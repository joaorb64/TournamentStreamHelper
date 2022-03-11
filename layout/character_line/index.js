(($) => {
  function Start() {}

  var data = {};
  var oldData = {};

  let oldCharacters = {};

  async function Update() {
    oldData = data;
    data = await getData();

    let team = window.team ? window.team : 1;
    let player = window.player ? window.player : 1;

    let characters = data.score.team[team].player[player].character;

    if (JSON.stringify(characters) != JSON.stringify(oldCharacters)) {
      console.log(oldCharacters);
      console.log(characters);
      oldCharacters = characters;

      assetToUse = "full";
      characterAssets = [];

      Object.values(characters).forEach((character) => {
        if (character.assets) {
          if (character.assets.hasOwnProperty(assetToUse)) {
            let asset = character.assets[assetToUse];
            asset.img = new Image();
            asset.img.src = "../../" + asset.asset;
            characterAssets.push(asset);
          } else {
            characterAssets.push({});
          }
        }
      });

      let elements = "";

      characterAssets.forEach((asset, i) => {
        elements += `
          <div
            class="icon"
            id="character${i}"
            style="background-image: url('../../${asset.asset}')"
          ></div>
        `;
      });

      elements += `<div class="index_display"></div>`;

      $(".container").html(elements);

      characterAssets.forEach((a, i) => {
        let img = a.img;

        let reposition = () => {
          let proportion = img.naturalWidth / img.naturalHeight;
          $(`#character${i}`).css(
            "background-position",
            `${
              ((characterAssets[i].eyesight.x * 1) /
                proportion /
                img.naturalWidth) *
              100
            }% ${
              ((characterAssets[i].eyesight.y * proportion) /
                img.naturalHeight) *
              100
            }%`
          );
        };

        $(window).resize(() => {
          reposition();
        });

        $(img).on("load", () => {
          reposition();
        });
      });
    }
  }

  Update();
  $(window).on("load", () => {
    $("body").fadeTo(500, 1, async () => {
      Start();
      setInterval(Update, 1000);
    });
  });
})(jQuery);
