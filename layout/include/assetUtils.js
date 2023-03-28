function GetBiggestAsset(character) {
  let biggest = null;
  if (Object.entries(character.assets).length > 0) {
    biggest = Object.entries(character.assets)[0];

    if (Object.entries(character.assets).length > 1) {
      for (let i = 1; i < Object.keys(character.assets).length; i += 1) {
        try {
          let currSum = biggest[1].average_size.x + biggest[1].average_size.y;

          let newSum =
            Object.entries(character.assets)[i][1].average_size.x +
            Object.entries(character.assets)[i][1].average_size.y;

          if (newSum > currSum) {
            biggest = Object.entries(character.assets)[i];
          }
        } catch {}
      }
    }
  }
  if (biggest) return biggest[1];
  else return null;
}

function GetCharacterAsset(asset, character) {
  if (character.assets.hasOwnProperty(asset)) {
    return character.assets[asset];
  } else return GetBiggestAsset(character);
}

function GetRecommendedZoom(asset) {
  if (asset.uncropped_edge) {
    if (
      asset.uncropped_edge.includes("u") &&
      asset.uncropped_edge.includes("d") &&
      asset.uncropped_edge.includes("l") &&
      asset.uncropped_edge.includes("r")
    )
      return 1.2;
  }
  return 1;
}

document.addEventListener("tsh_update", (event) => {
  $(".tsh_fade").each((i, e) => {
    let path = $(e).attr("data-source");
    let data = _.get(event.data, path + ".1.assets");

    if (!data) {
      gsap.timeline().to($(e), { autoAlpha: 0 });
    } else {
      gsap.timeline().to($(e), { autoAlpha: 1 });
    }
  });
});

function CharacterDisplay(element, settings) {
  $(element).data(settings);
  $(element).addClass("tsh_character_container");
}

document.addEventListener("tsh_update", async (event) => {
  $(".tsh_character_container").each(async (i, e) => {
    let settings = _.defaults($(e).data(), {
      custom_zoom: 1,
      custom_center: null,
      custom_element: null,
      scale_fill_x: false,
      scale_fill_y: false,
    });

    let path = settings.source;

    let slice_player = [0, Infinity];

    try {
      if (settings.slice_player) {
        slice_player = settings.slice_player;
      }
    } catch (e) {
      console.log(e);
    }

    let slice_character = [0, Infinity];

    try {
      if (settings.slice_character) {
        slice_character = settings.slice_character;
      }
    } catch (e) {
      console.log(e);
    }

    let team = _.get(event.data, path);

    let characters = Object.values(_.get(team, "player"))
      .slice(slice_player)
      .map((p, index) => {
        return Object.values(_.get(p, "character"))
          .map((c, index) => {
            return c;
          })
          .slice(slice_character[0], slice_character[1]);
      });

    let oldTeam = _.get(event.oldData, path);

    let oldCharacters = Object.values(_.get(oldTeam, "player", []))
      .slice(slice_player)
      .map((p, index) => {
        return Object.values(_.get(p, "character"))
          .map((c, index) => {
            return c;
          })
          .slice(slice_character[0], slice_character[1]);
      });

    let anim_in = { autoAlpha: 1, duration: 1 };

    if (settings.anim_in) {
      anim_in = anim_in;
    }

    let anim_out = { autoAlpha: 0, duration: 1 };

    if (settings.anim_out) {
      anim_out = settings.anim_out;
    }

    let changed = JSON.stringify(characters) != JSON.stringify(oldCharacters);

    if (changed || !$(e).hasClass("tsh_character_container_active")) {
      $(e).addClass("tsh_character_container_active");

      await gsap
        .to($(e).children(".tsh_character"), anim_out)
        .then(async () => {
          let loads = [];

          $(e).html("");

          if (characters) {
            for (let player of Object.values(characters)) {
              for (let character of player) {
                if (!_.get(character, "codename")) continue;
                console.log(character);
                let _div = $("<div class='tsh_character'><div></div></div>");
                e.appendChild($(_div).get(0));

                window.requestAnimationFrame(() => {
                  let asset = settings.asset_key
                    ? GetCharacterAsset(settings.asset_key, character)
                    : GetBiggestAsset(character);

                  let zoom = settings.zoom
                    ? settings.zoom
                    : GetRecommendedZoom(asset);

                  loads.push(CenterImage($(_div).children(0), asset, settings));
                });
              }
            }
          }

          Promise.all(loads).then((values) => {
            console.log("animate", $(e));
            gsap.fromTo(
              $(e).children(".tsh_character").children(),
              anim_out,
              anim_in
            );
          });
        });
    }
  });
});

document.addEventListener("tsh_update", (event) => {
  $(".tsh_text").each((i, e) => {
    let path = $(e).attr("data-source");
    let data = _.get(event.data, path);

    if (!data) {
      gsap.timeline().to($(e), { autoAlpha: 0 });
    } else {
      gsap.timeline().to($(e), { autoAlpha: 1 });
      SetInnerHtml($(e), data);
    }
  });
});
