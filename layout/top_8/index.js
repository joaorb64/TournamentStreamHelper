LoadEverything().then(() => {
  gsap.config({ nullTargetWarn: false, trialWarn: false });

  let startingAnimation = gsap
    .timeline({ paused: true })
    .from([".container"], { duration: 1, width: "0", ease: "power2.inOut" }, 0);

  function Start() {
    startingAnimation.restart();
  }

  var data = {};
  var oldData = {};

  async function Update() {
    oldData = data;
    data = await getData();

    if (data.game) {
      var DIVIDERS = false;

      if (data.game.codename == "ssbu") {
        var ASSET_TO_USE_1ST = "vs_renders";
        var ZOOM_1ST = 1;

        var ASSET_TO_USE_2_to_4 = "vs_renders";
        var ZOOM_2_to_4 = 1;

        var ASSET_TO_USE_5_to_7 = "vs_renders";
        var ZOOM_5_to_7 = 1;

        DIVIDERS = false;
      } else if (data.game.codename == "ssbm") {
        var ASSET_TO_USE_1ST = "portrait_hd";
        var ZOOM_1ST = 1.2;

        var ASSET_TO_USE_2_to_4 = "portrait_hd";
        var ZOOM_2_to_4 = 1.2;

        var ASSET_TO_USE_5_to_7 = "portrait_hd";
        var ZOOM_5_to_7 = 1.2;
      } else if (data.game.codename == "ssb64") {
        var ASSET_TO_USE_1ST = "artwork";
        var ZOOM_1ST = 1.2;

        var ASSET_TO_USE_2_to_4 = "artwork";
        var ZOOM_2_to_4 = 1.2;

        var ASSET_TO_USE_5_to_7 = "artwork";
        var ZOOM_5_to_7 = 1.2;
      } else {
        var ASSET_TO_USE_1ST = "full";
        var ZOOM_1ST = 1.2;

        var ASSET_TO_USE_2_to_4 = "full";
        var ZOOM_2_to_4 = 1.2;

        var ASSET_TO_USE_5_to_7 = "full";
        var ZOOM_5_to_7 = 1.2;
      }
    }

    if (
      !oldData.player_list ||
      JSON.stringify(data.player_list) != JSON.stringify(oldData.player_list)
    ) {
      let htmls = [];

      Object.values(data.player_list.slot).forEach((slot, i) => {
        let html = `<div class="slot slot${i + 1}">`;

        Object.values(slot.player).forEach((player, p) => {
          html += `
            <div class="p${p + 1} player container">
              <div class="score">${
                // TODO: Standings formula
                Array(1, 2, 3, 4, 5, 5, 7, 7, 17, 17, 17, 17, 21, 21, 21, 21)[i]
              }</div>
              <div class="footer">
                <!-- <div class="icon avatar"></div> -->
                <!-- <div class="icon online_avatar"></div> -->
                <div class="name_twitter">
                  <div class="name"></div>
                  <div class="twitter"></div>
                </div>
                <div class="sponsor_icon"></div>
              </div>
              <div class="flags">
                <div class="flagcountry"></div>
                ${player.state.asset ? `<div class="flagstate"></div>` : ""}
              </div>
              <div class="character_container"></div>
            </div>
          `;
        });

        html += "</div>";

        htmls.push(html);
      });

      $(".top1_container").html("");
      $(".top4_container").html("");
      $(".top8_container").html("");

      for (let i = 0; i < htmls.length; i++) {
        let html = htmls[i];

        if (window.SAME_SIZE) {
          $(".top8_container").html($(".top8_container").html() + html);
        } else {
          if (i == 0) {
            $(".top1_container").html($(".top1_container").html() + html);
          } else if (i < 4) {
            $(".top4_container").html($(".top4_container").html() + html);
          } else {
            $(".top8_container").html($(".top8_container").html() + html);
          }
        }
      }

      Object.values(data.player_list.slot).forEach((slot, t) => {
        SetInnerHtml($(`.slot${t + 1} .title`), slot.name);
        Object.values(slot.player).forEach((player, p) => {
          if (player) {
            SetInnerHtml(
              $(`.slot${t + 1} .p${p + 1}.container .name`),
              `
            <span>
              <span class="sponsor">
                ${player.team ? player.team : ""}
              </span>
              ${player.name}
            </span>
            `,
              undefined,
              0
            );

            SetInnerHtml(
              $(`.slot${t + 1} .p${p + 1}.container .flagcountry`),
              player.country.asset
                ? `<div class='flag' style='background-image: url(../../${player.country.asset.toLowerCase()})'></div>`
                : "",
              undefined,
              0
            );

            SetInnerHtml(
              $(`.slot${t + 1} .p${p + 1}.container .flagstate`),
              player.state.asset
                ? `<div class='flag' style='background-image: url(../../${player.state.asset})'></div>`
                : "",
              undefined,
              0
            );

            if (t == 0) {
              ASSET_TO_USE = ASSET_TO_USE_1ST;
              ZOOM = ZOOM_1ST;
            } else if (t < 4) {
              ASSET_TO_USE = ASSET_TO_USE_2_to_4;
              ZOOM = ZOOM_2_to_4;
            } else {
              ASSET_TO_USE = ASSET_TO_USE_5_to_7;
              ZOOM = ZOOM_5_to_7;
            }

            CharacterDisplay(
              $(`.slot${t + 1} .p${p + 1}.container .character_container`),
              {
                custom_zoom: ZOOM,
                asset_key: ASSET_TO_USE,
                source: `player_list.slot.${t + 1}`,
                use_dividers: false,
                custom_center: [0.5, 0.4],
              }
            );

            SetInnerHtml(
              $(`.slot${t + 1} .p${p + 1}.container .sponsor_icon`),
              player.sponsor_logo
                ? `<div style='background-image: url(../../${player.sponsor_logo})'></div>`
                : "<div></div>",
              undefined,
              0
            );

            SetInnerHtml(
              $(`.slot${t + 1} .p${p + 1}.container .avatar`),
              player.avatar
                ? `<div style="background-image: url('../../${player.avatar}')"></div>`
                : "",
              undefined,
              0
            );

            SetInnerHtml(
              $(`.slot${t + 1} .p${p + 1}.container .online_avatar`),
              player.online_avatar
                ? `<div style="background-image: url('${player.online_avatar}')"></div>`
                : "",
              undefined,
              0
            );

            SetInnerHtml(
              $(`.slot${t + 1} .p${p + 1}.container .twitter`),
              player.twitter
                ? `<span class="twitter_logo"></span>${String(player.twitter)}`
                : "",
              undefined,
              0
            );

            SetInnerHtml(
              $(`.slot${t + 1} .p${p + 1}.container .sponsor-container`),
              `<div class='sponsor-logo' style='background-image: url(../../${player.sponsor_logo})'></div>`,
              undefined,
              0
            );
          }
        });
      });
    }
  }

  document.addEventListener("tsh_update", Update);
  gsap.globalTimeline.timeScale(0);

  window.setTimeout(() => {
    $("body").fadeTo(1, 1, async () => {
      gsap.globalTimeline.timeScale(1);
      Start();
    });
  }, 64);
});
