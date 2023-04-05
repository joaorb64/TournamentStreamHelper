LoadEverything().then(() => {
  // Change this to the name of the assets pack you want to use
  // It's basically the folder name: user_data/games/game/ASSETPACK
  var ASSET_TO_USE = "full";

  // Amount of zoom to use on the assets. Use 1 for 100%, 1.5 for 150%, etc.
  var CUSTOM_ZOOM = 1;

  // Where to center character eyesights. [ 0.0 - 1.0 ]
  var EYESIGHT_CENTERING = [0.5, 0.4];

  Start = async () => {
    $(".tsh_character > div").each((i, e) => $(e).css("opacity", "0"));
  };

  Update = async (event) => {
    let data = event.data;
    let oldData = event.oldData;

    let src = "";

    if (window.team != undefined && window.player != undefined) {
      src = `score.team.${window.team}.player.${window.player}`;
    } else {
      src = `score.team.${window.team}`;
    }

    await CharacterDisplay(
      $(`.container`),
      {
        custom_zoom: CUSTOM_ZOOM,
        asset_key: ASSET_TO_USE,
        custom_center: EYESIGHT_CENTERING,
        source: src,
      },
      event
    );

    imgs = $.makeArray($(".tsh_character > div"));

    if (imgs.length < 2) {
      gsap.to($(".index_display"), { autoAlpha: 0 });
    } else {
      gsap.to($(".index_display"), { autoAlpha: 1 });
    }
  };

  let cycleIndex = 0;
  let imgs = [];

  function crossfade() {
    if (imgs.length > 1) {
      gsap.to(imgs[(cycleIndex + imgs.length - 1) % imgs.length], 1, {
        autoAlpha: 0,
      });
      gsap.to(imgs[cycleIndex], 1, { autoAlpha: 1 });
      $(".index_display").html(`${cycleIndex + 1}/${imgs.length}`);
      cycleIndex = (cycleIndex + 1) % imgs.length;
    } else if (imgs.length == 1) {
      gsap.to(imgs[0], 1, { autoAlpha: 1 });
      $(".index_display").html(`1/1`);
      cycleIndex = 0;
    }
  }

  var cycle = setInterval(crossfade, 3000);
});
