// See https://github.com/xtk93x/Leaflet.TileLayer.ColorFilter to colorize your map
let myFilter = [];

var baseMap = L.tileLayer.colorFilter(
  "http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
  {
    maxZoom: 4,
    zoomSnap: 0,
    zoomControl: false,
    id: "osm.streets",
    filter: myFilter,
  }
);

var map = L.map("map", {
  zoomControl: false,
}).setView([0, 0], 3);

baseMap.addTo(map);

LoadEverything().then(() => {
  var markers = [];
  var polylines = [];
  var positions = [];
  // I use this to know if I added a icon for a state or a country latlng
  // for country latlng the icon pulses and there's more zoom out
  var isPrecise = [];

  Start = async (event) => {};

  function UpdateMap() {
    console.log(pingData);

    markers.forEach((marker) => {
      map.removeLayer(marker);
    });
    markers = [];

    polylines.forEach((poly) => {
      poly.removeFrom(map);
    });
    polylines = [];

    positions = [];
    isPrecise = [];
    isValid = [];

    let servers = [];

    Object.values(data.score.team).forEach((team) => {
      Object.values(team.player).forEach((player) => {
        if(!player.name){
          return
        }

        let pos = [
          player.state.latitude != null && !window.COUNTRY_ONLY
            ? parseFloat(player.state.latitude)
            : parseFloat(player.country.latitude),
          player.state.longitude != null && !window.COUNTRY_ONLY
            ? parseFloat(player.state.longitude)
            : parseFloat(player.country.longitude),
        ];

        let validPos = !Number.isNaN(pos[0]) && !Number.isNaN(pos[1]);
        if(!validPos) pos = [0, 0]
        isValid.push(validPos);

        positions.push(pos);

        let server = findClosestServer(pingData, pos[0], pos[1]);
        servers.push(server);

        let directions = ["top", "bottom", "left", "right"];
        let direction = 0;

        positions.forEach((position) => {
          if (position != pos) {
            if (position[0] == pos[0] && position[1] == pos[1]) {
              direction = (direction + 1) % directions.length;
            }
          }
        });

        let offsetDistance = validPos ? 8 : 16

        let offsets = {
          "top": [0, -offsetDistance],
          "bottom": [0, offsetDistance],
          "left":[-offsetDistance, 0],
          "right": [offsetDistance, 0]
        }

        let marker = L.marker(pos, {
          icon: L.icon({
            iconUrl: validPos ? "./marker.svg" : "./questionmark.svg",
            iconSize: validPos ? [12, 12] : [32, 32],
            iconAnchor: validPos ? [6, 6] : [16, 16],
          }),
        })
          .addTo(map)
          .bindTooltip(player.name, {
            direction: directions[direction],
            className: "leaflet-tooltip-own",
            offset: offsets[directions[direction]],
          })
          .openTooltip();

        markers.push(marker);

        if (!player.state.latitude || window.COUNTRY_ONLY || !validPos) {
          let marker = L.marker(pos, {
            icon: L.divIcon({
              html: `<div class="gps_ring ${!validPos ? "gps_ring_big": ""}"></div>`,
              className: "css-icon",
              iconAnchor: [64, 64],
            }),
          }).addTo(map);

          markers.push(marker);
          isPrecise.push(validPos);
        } else {
          isPrecise.push(true);
        }
      });
    });

    if (!window.NOHUD) {
      // Calculate max ping
      if (isPrecise.some((e) => e == false)) {
        $("#ping").html("ESTIMATED PING: ???");
        $("#distance").html("DISTANCE: ???");
      } else {
        let maxPing = 0;

        servers.forEach((server1) => {
          servers.forEach((server2) => {
            if (server1 != server2) {
              let ping = pingBetweenServers(server1, server2);
              if (ping > maxPing) {
                maxPing = ping;
              }
            }
          });
        });

        console.log("Max Ping: " + maxPing);

        let pingByDistance = 0;

        positions.forEach((pos1) => {
          positions.forEach((pos2) => {
            if (pos1 != pos2) {
              pingByDistance += distanceInKm(pos1, pos2) * 0.0067;
            }
          });
        });

        console.log("Ping by distance: " + pingByDistance);

        let pingString = maxPing < 20 ? "< 20" : maxPing.toFixed(2);
        $("#ping").html("ESTIMATED PING: " + pingString + " ms");

        let maxDistance = 0;

        positions.forEach((pos1) => {
          positions.forEach((pos2) => {
            if (pos1 != pos2) {
              let distance = distanceInKm(pos1, pos2);
              if (distance > maxDistance) {
                maxDistance = distance;
              }
            }
          });
        });

        console.log("Distance: " + maxDistance);

        let distanceString = "";

        if (maxDistance < 100) {
          distanceString = "< 100 Km / < 62 mi";
        } else {
          distanceString =
            maxDistance.toFixed(2) +
            " Km" +
            " / " +
            (maxDistance * 0.621371).toFixed(2) +
            " mi";
        }

        if (positions.length == 2) {
          $("#distance").html("DISTANCE: " + distanceString);
        } else {
          $("#distance").html("MAX DISTANCE: " + distanceString);
        }
      }
      gsap
        .timeline()
        .to([".overlay-element"], { duration: 1, autoAlpha: 1 }, 0);
    } else {
      $(".overlay").css("height", 0);
    }

    map.on("zoomend", () => {
      let validPositions = positions.filter((pos, i) => {
        return isPrecise[i];
      });
      var polyline = L.polyline(getPairs(validPositions), {
        color: "blue",
        dashArray: "5,10",
      }).addTo(map);
      polylines.push(polyline);
    });

    let bounds = L.latLngBounds(positions);

    isPrecise.forEach((precise, i) => {
      if (!precise) {
        bounds = bounds.extend(
          L.latLng(positions[i][0], positions[i][1]).toBounds(2000000)
        );
      }
    });

    map.flyToBounds(bounds, {
      paddingTopLeft: [30, 30 + $(".overlay").outerHeight()],
      paddingBottomRight: [30, 30],
      duration: 1.2,
      easeLinearity: 0.000001,
    });
  }

  function findClosestServer(pingData, lat, lng) {
    let closest = pingData[0];
    let closestVal = Math.getDistance(
      lat,
      lng,
      parseFloat(pingData[0].latitude),
      parseFloat(pingData[0].longitude)
    );

    pingData.forEach((server) => {
      let distance = Math.getDistance(
        lat,
        lng,
        parseFloat(server.latitude),
        parseFloat(server.longitude)
      );
      if (distance < closestVal) {
        closestVal = distance;
        closest = server;
      }
    });

    return closest;
  }

  function pingBetweenServers(server1, server2) {
    return server1.pings[server2.id];
  }

  function distanceInKm(origin, destination) {
    var lon1 = toRadian(origin[1]),
      lat1 = toRadian(origin[0]),
      lon2 = toRadian(destination[1]),
      lat2 = toRadian(destination[0]);

    var deltaLat = lat2 - lat1;
    var deltaLon = lon2 - lon1;

    var a =
      Math.pow(Math.sin(deltaLat / 2), 2) +
      Math.cos(lat1) * Math.cos(lat2) * Math.pow(Math.sin(deltaLon / 2), 2);
    var c = 2 * Math.asin(Math.sqrt(a));
    var EARTH_RADIUS = 6371;
    return c * EARTH_RADIUS;
  }
  function toRadian(degree) {
    return (degree * Math.PI) / 180;
  }

  var pingData = null;

  Update = async (event) => {
    let data = event.data;
    let oldData = event.oldData;

    if (!pingData) pingData = await getPings();

    if (
      Object.keys(oldData).length == 0 ||
      JSON.stringify(oldData.score.team["1"].player) !=
        JSON.stringify(data.score.team["1"].player) ||
      JSON.stringify(oldData.score.team["2"].player) !=
        JSON.stringify(data.score.team["2"].player)
    ) {
      UpdateMap();
    }
  };

  Math.getDistance = function (x1, y1, x2, y2) {
    var xs = x2 - x1,
      ys = y2 - y1;
    xs *= xs;
    ys *= ys;
    return Math.sqrt(xs + ys);
  };

  function getPairs(arr) {
    var res = [],
      l = arr.length;
    for (var i = 0; i < l; ++i)
      for (var j = i + 1; j < l; ++j) res.push([arr[i], arr[j]]);
    return res;
  }

  function getPings() {
    return $.ajax({
      dataType: "json",
      url: "./pings.json",
      cache: false,
    });
  }
});
