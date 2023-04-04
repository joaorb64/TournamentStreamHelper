LoadEverything().then(() => {
  // Change this to the name of the assets pack you want to use
  // It's basically the folder name: user_data/games/game/ASSETPACK
  var ASSET_TO_USE = "full";

  // Amount of zoom to use on the assets. Use 1 for 100%, 1.5 for 150%, etc.
  var CUSTOM_ZOOM = 1;

  // Where to center character eyesights. [ 0.0 - 1.0 ]
  var EYESIGHT_CENTERING = [0.5, 0.4];

  Start = async () => {};

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
  };
});
