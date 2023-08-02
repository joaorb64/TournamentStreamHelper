// Gets biggest character asset available
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

// Gets character asset using key "asset". If not found, return biggest asset
function GetCharacterAsset(asset, character) {
  if (character.assets.hasOwnProperty(asset)) {
    return character.assets[asset];
  } else return GetBiggestAsset(character);
}

// Gets recommended zoom
// For uncropped assets, we add some zoom since they're usually full body arts
// and most times we want some focus on the characters' faces
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

// Set up character display for a div
async function CharacterDisplay(element, settings, event) {
  $(element).data(settings);

  if (!$(element).hasClass("tsh_character_container")) {
    $(element).addClass("tsh_character_container");
    if ($(element).get(0)) {
      await updateCharacterContainer($(element).get(0), event);
    }
  }
}

// When a tsh_update event is fired, we update the containers with tsh_character_container class
document.addEventListener("tsh_update", async (event) => {
  $(".tsh_character_container").each(async (i, e) => {
    updateCharacterContainer(e, event);
  });
});

// Given the path to a key in the settings which has asset settings,
// resolve current game and global/local/default settings and return the config.
function ResolveAssetSetting(key) {
  let current_game = _.get(data, "game.codename", "default");

  let global_default_settings = _.get(tsh_settings, key + ".default", {});
  let global_settings = _.get(tsh_settings, key + "." + current_game, {});

  let settings = _.defaultsDeep(global_settings, global_default_settings);

  return settings;
}

// Handle data for each character container
// Here we confirm some of the settings, check for data changes, etc
async function updateCharacterContainer(e, event) {
  // Load json file-based settings. If the key isn't specified, we default to the "assets" key in the json
  let asset_settings = ResolveAssetSetting(
    _.get($(e).data(), "load_settings_path", "assets")
  );

  if(_.get($(e).data(), "load_settings_path")){
    let defaultAssetSettings = ResolveAssetSetting("assets");

    asset_settings = _.defaultsDeep(
      Object.assign({}, defaultAssetSettings),
      Object.assign({}, asset_settings)
    )
  }

  // Use settings passed via script, default to settings got via json files
  let settings = _.defaultsDeep(
    Object.assign({}, $(e).data()),
    Object.assign({}, asset_settings)
  );

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

  let players = [];
  let oldPlayers = [];

  let team = _.get(event.data, path + ".player");

  if (team) {
    players = Object.values(_.get(event.data, path + ".player", {}));
    oldPlayers = Object.values(_.get(event.oldData, path + ".player", {}));
  } else {
    players = [_.get(event.data, path, {})];
    oldPlayers = [_.get(event.oldData, path, {})];
  }

  let characters = players.slice(slice_player).map((p, index) => {
    return Object.values(_.get(p, "character", {}))
      .map((c, index) => {
        return c;
      })
      .filter((c) => Object.values(c.assets).length > 0)
      .slice(slice_character[0], slice_character[1]);
  });

  let oldCharacters = oldPlayers.slice(slice_player).map((p, index) => {
    return Object.values(_.get(p, "character", {}))
      .map((c, index) => {
        return c;
      })
      .filter((c) => Object.values(c.assets).length > 0)
      .slice(slice_character[0], slice_character[1]);
  });

  let anim_in = { autoAlpha: 1, duration: 0.5, stagger: 0.1 };

  if (settings.anim_in) {
    anim_in = settings.anim_in;
  }

  let anim_out = { autoAlpha: 0, duration: 0.5, stagger: 0.1 };

  if (settings.anim_out) {
    anim_out = settings.anim_out;
  }

  // Forces latest call to overwrite any ongoing animation
  anim_out.overwrite = true;

  let changed = JSON.stringify(characters) != JSON.stringify(oldCharacters);

  let firstRun = !$(e).hasClass("tsh_character_container_active");

  if (firstRun) {
    anim_out.duration = 0;
  }

  if (changed || firstRun) {
    // Class used to detct if it's the first run
    $(e).addClass("tsh_character_container_active");

    const callback = async () => {
      let loads = [];

      $(e).html("");

      let index = 0;

      if (characters) {
        for (let i = 0; i < Object.values(characters).length; i += 1) {
          let player = Object.values(characters)[i];
          for (let j = 0; j < player.length; j += 1) {
            let character = player[j];
            if (!_.get(character, "codename")) continue;
            let _div = $(
              "<div class='tsh_character' style='opacity: 0;'><div></div></div>"
            );
            e.appendChild($(_div).get(0));

            let settingsClone = Object.assign({}, settings);

            settingsClone.z_index = Object.values(player).length - index;

            // If not using dividers, calculate proper placement for each character
            if (settings.use_dividers === false) {
              settingsClone.custom_center = GenerateMulticharacterPositions(
                Object.values(player).length,
                settings.custom_center
              )[index];
              console.log(settingsClone.custom_center);
            }

            let asset = settingsClone.asset_key
              ? GetCharacterAsset(settingsClone.asset_key, character)
              : GetBiggestAsset(character);

            console.log(settingsClone);
            if (!settingsClone.custom_zoom)
              settingsClone.custom_zoom = GetRecommendedZoom(asset);

            if (asset.asset.endsWith(".webm")) {
              loads.push(
                CenterVideo($(_div).children(0), asset, settingsClone)
              );
            } else {
              loads.push(
                CenterImage($(_div).children(0), asset, settingsClone)
              );
            }

            index += 1;
          }
        }
      }

      await Promise.allSettled(loads);
      gsap.fromTo($(e).children(".tsh_character"), anim_out, anim_in);
    };

    if (firstRun) {
      // No need to fade out
      await callback();
    } else {
      // Fade out, then change data and fade in
      gsap.to($(e).children(".tsh_character"), anim_out).then(callback);
    }
  }
}

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

// Sets colors for the css variables based on the tournament logo
function GetLogoColors() {
  let img = new Image();
  img.src = "../logo.png";

  img.onload = () => {
    const colorThief = new ColorThief();

    let palette = colorThief.getPalette(img, 2);

    let text = setContrast(palette[0]);

    $(`:root`).css({
      "--text-color": `rgb(${text.join(",")})`,
      "--bg-color": `rgb(${palette[0].join(",")})`,
      "--p1-score-bg-color": `rgb(${palette[1].join(",")})`,
      "--p2-score-bg-color": `rgb(${palette[1].join(",")})`,
      "--p1-sponsor-color": `rgb(${palette[1].join(",")})`,
      "--p2-sponsor-color": `rgb(${palette[1].join(",")})`,
      "--p1-score-color": `rgb(${setContrast(palette[1]).join(",")})`,
      "--p2-score-color": `rgb(${setContrast(palette[1]).join(",")})`,
    });
  };
}

// Gets contrasting color between black and white for a [r, g, b] background
const setContrast = (rgb) =>
  (rgb[0] * 299 + rgb[1] * 587 + rgb[2] * 114) / 1000 > 125
    ? [0, 0, 0]
    : [255, 255, 255];

/* $(`.p${t + 1}.character .tsh-center-image`).each((i, e) => {
  let img = new Image();

  img.src = $(e)
    .css("background-image")
    .split('url("')[1]
    .split('")')[0];

  img.onload = () => {
    const colorThief = new ColorThief();

    let palette = colorThief.getPalette(img, 2);

    console.log(
      `linear-gradient(90deg, rgb(${palette[0].join(
        ","
      )}), rgb(${palette[1].join(",")}))`
    );

    $(`.p${t + 1}.player.container`).css({
      background: `linear-gradient(90deg, rgb(${palette[0].join(
        ","
      )}), rgb(${palette[1].join(",")}))`,
      //"background-color": `rgb(${palette[1].join(",")})`,
      //color: `rgb(${palette[0].join(",")})`,
    });
  };
}); */
