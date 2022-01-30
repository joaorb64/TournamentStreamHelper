// See https://github.com/xtk93x/Leaflet.TileLayer.ColorFilter to colorize your map
let myFilter = [
]

var baseMap = L.tileLayer.colorFilter(
    "http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    {
        maxZoom: 6,
        zoomSnap: 0,
        zoomControl: false,
        id: "osm.streets",
        filter: myFilter
    }
);

var map = L.map('map', {
    maxZoom: 6,
    zoomControl: false
}).setView([0, 0], 2);

baseMap.addTo(map);

(($) => { 
    function Start(){
        pingData = getPings().then((pingData)=>{
            console.log(pingData)

            Object.values(data.score.team).forEach((team)=>{
                Object.values(team.players).forEach((player)=>{
                    let pos = [
                        player.state.latitude? player.state.latitude : player.country.latitude,
                        player.state.longitude? player.state.longitude : player.country.latitude,
                    ]

                    let server = findClosestServer(pingData, pos[0], pos[1])

                    L.marker(pos, { icon: L.icon({
                        iconUrl: "./marker.svg",
                        iconSize: [12, 12],
                        iconAnchor: [6, 6],
                    }) }).addTo(map)
                        .bindTooltip(player.name, { direction: "top", className: 'leaflet-tooltip-own', offset: [0, -12] })
                        .openTooltip();
                })
            })

            // let ping = pingBetweenServers(server1, server2);
            // let distance = distanceInKm(pos1, pos2);

            // console.log("Ping: "+ping);
            // console.log("Distance: "+distance);

            // $("#distance").html("Distance: "+distance.toFixed(2)+" Km"+" / "+(distance*0.621371).toFixed(2)+" mi")
            // $("#ping").html("Estimated ping: "+ping.toFixed(2)+" ms")

            // gsap.timeline()
            //     .to(['.overlay-element'], { duration: 1, autoAlpha: 1 }, 0)

            // L.marker(pos2, { icon: L.icon({
            //     iconUrl: "../../icons/update_circle.svg",
            //     iconSize: [12, 12],
            //     iconAnchor: [6, 6],
            // }) }).addTo(map)
            //     .bindTooltip(data.score.team2.players["1"].name, { direction: "top", className: 'leaflet-tooltip-own', offset: [0, -12] })
            //     .openTooltip();
            
            // map.on("zoomend", ()=>{
            //     var polyline = L.polyline([pos1, pos2], {color: 'blue', dashArray: '5,10'}).addTo(map);
            // })

            // map.flyToBounds(L.latLngBounds(pos1, pos2), {
            //     paddingTopLeft: [80 + $(".overlay").outerHeight(), 80],
            //     paddingBottomRight: [80, 80],
            //     duration: 2,
            //     easeLinearity: 0.000001
            // })
        })
    }

    function findClosestServer(pingData, lat, lng){
        let closest = pingData[0]
        let closestVal = Math.getDistance(lat, lng, parseFloat(pingData[0].latitude), parseFloat(pingData[0].longitude))

        pingData.forEach((server)=>{
            let distance = Math.getDistance(lat, lng, parseFloat(server.latitude), parseFloat(server.longitude));
            if(distance < closestVal){
                closestVal = distance;
                closest = server;
            }
        })

        return closest;
    }

    function pingBetweenServers(server1, server2){
        return server1.pings[server2.id]
    }

    function distanceInKm(origin, destination) {
        var lon1 = toRadian(origin[1]),
            lat1 = toRadian(origin[0]),
            lon2 = toRadian(destination[1]),
            lat2 = toRadian(destination[0]);
    
        var deltaLat = lat2 - lat1;
        var deltaLon = lon2 - lon1;
    
        var a = Math.pow(Math.sin(deltaLat/2), 2) + Math.cos(lat1) * Math.cos(lat2) * Math.pow(Math.sin(deltaLon/2), 2);
        var c = 2 * Math.asin(Math.sqrt(a));
        var EARTH_RADIUS = 6371;
        return c * EARTH_RADIUS;
    }
    function toRadian(degree) {
        return degree*Math.PI/180;
    }

    var data = {}
    var oldData = {}

    async function Update(){
        oldData = data;
        data = await getData();

        if(oldData == {}){
            
        }
    }

    Math.getDistance = function( x1, y1, x2, y2 ) {
        var xs = x2 - x1, ys = y2 - y1;		
        xs *= xs;
        ys *= ys;
        return Math.sqrt( xs + ys );
    };

    function getPings() {
        return $.ajax({
            dataType: 'json',
            url: './pings.json',
            cache: false,
        });
    }

    Update();
    $(window).on("load", () => {
        $('body').fadeTo(500, 1, async () => {
            Start();
            setInterval(Update, 1000);
        });
    });
})(jQuery);