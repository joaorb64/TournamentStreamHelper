(($) => {
  function Start() {}

  var data = {};
  var oldData = {};

  let oldCharacters = {};

  async function Update() {
    oldData = data;
    data = await getData();

    let characters =
      data.score.team[window.team].player[window.player].character;

    if (JSON.stringify(characters) != JSON.stringify(oldCharacters)) {
      TweenMax.to(".container", 0.1, { autoAlpha: 0 }).then(() => {
        oldCharacters = characters;

        assetToUse = "full";
        characterAssets = [];

        Object.values(characters).forEach((character) => {
          if (character.assets) {
            if (character.assets.hasOwnProperty(assetToUse)) {
              characterAssets.push(character.assets[assetToUse]);
            }
          }
        });

        let elements = "";

        characterAssets.forEach((asset, i) => {
          elements += `<div class="icon" id="character${i}" style='background-image: url(../../${asset.asset})'></div>`;
        });

        elements += `<div class="index_display"></div>`;

        $(".container").html(elements);

        characterAssets.forEach((a, i) => {
          CenterImage($(`#character${i}`), a.eyesight);
        });

        imgs = $.makeArray($(".icon"));

        cycleIndex = 0;

        TweenMax.to(".container", 0.1, { autoAlpha: 1 });
        crossfade();
      });
    }
  }

  let cycleIndex = 0;
  let imgs = [];

  function crossfade() {
    if (imgs.length > 1) {
      TweenMax.to(imgs[(cycleIndex + imgs.length - 1) % imgs.length], 1, {
        autoAlpha: 0,
      });
      TweenMax.to(imgs[cycleIndex], 1, { autoAlpha: 1 });
      $(".index_display").html(`${cycleIndex + 1}/${imgs.length}`);
      cycleIndex = (cycleIndex + 1) % imgs.length;
    } else if (imgs.length == 1) {
      TweenMax.to(imgs[0], 1, { autoAlpha: 1 });
      $(".index_display").html(`1/1`);
      cycleIndex = 0;
    }
  }

  var cycle = setInterval(crossfade, 3000);

  Update();
  $(window).on("load", () => {
    $("body").fadeTo(1, 1, async () => {
      Start();
      setInterval(Update, 100);
    });
  });
})(jQuery);
