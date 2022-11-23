(($) => {
  var ASSET_TO_USE = "full";
  var ZOOM = 2;

  gsap.config({ nullTargetWarn: false, trialWarn: false });

  let startingAnimation = gsap.timeline({ paused: true });

  function Start() {
    startingAnimation.restart();
  }

  var data = {};
  var oldData = {};

  async function Update() {
    oldData = data;
    data = await getData();

    if (
      !oldData.bracket ||
      JSON.stringify(data.bracket.bracket) !=
        JSON.stringify(oldData.bracket.bracket)
    ) {
      let bracket = data.bracket.bracket.rounds;
      let players = data.player_list.slot;

      let html = "";

      Object.values(bracket).forEach((round, r) => {
        html += `<div class="round round_${r}">`;
        Object.values(round).forEach((slot, i) => {
          html += `<div class="slot slot_${i + 1}">`;
          Object.values(slot.playerId).forEach((playerId, p) => {
            html += `
              <div class="p_${playerId} slot_p_${p} player container">
                <div class="icon avatar"></div>
                <div class="icon online_avatar"></div>
                <div class="name_twitter">
                <div class="name"></div>
                </div>
                <div class="sponsor_icon"></div>
                <div class="flags">
                  <div class="flagcountry"></div>
                  <div class="flagstate"></div>
                </div>
                <div class="character_container"></div>
                <div class="score">0</div>
              </div>
            `;
          });
          html += "</div>";
        });
        html += "</div>";
      });

      $(".players_container").html(html);

      Object.values(bracket).forEach((round, r) => {
        Object.values(round).forEach((slot, i) => {
          Object.values(slot.score).forEach((score, p) => {
            console.log(p);
            SetInnerHtml(
              $(`.round_${r} .slot_${i + 1} .slot_p_${p}.container .score`),
              `
                ${score}
              `,
              undefined,
              0
            );
          });
        });
      });

      Object.values(players).forEach((slot, t) => {
        Object.values(slot.player).forEach((player, p) => {
          if (player) {
            SetInnerHtml(
              $(`.p_${t + 1}.container .name`),
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
              $(`.p_${t + 1}.container .flagcountry`),
              player.country.asset
                ? `<div class='flag' style='background-image: url(../../${player.country.asset.toLowerCase()})'></div>`
                : "",
              undefined,
              0
            );

            SetInnerHtml(
              $(`.p_${t + 1}.container .flagstate`),
              player.state.asset
                ? `<div class='flag' style='background-image: url(../../${player.state.asset})'></div>`
                : "",
              undefined,
              0
            );

            let charactersHtml = "";

            Object.values(player.character).forEach((character, index) => {
              if (character.assets[ASSET_TO_USE]) {
                charactersHtml += `
                  <div class="icon stockicon">
                      <div
                        style='background-image: url(../../${
                          character.assets[ASSET_TO_USE].asset
                        })'
                        data-asset='${JSON.stringify(
                          character.assets[ASSET_TO_USE]
                        )}'
                        data-zoom='${ZOOM}'
                      >
                      </div>
                  </div>
                  `;
              }
            });
            SetInnerHtml(
              $(`.p_${t + 1} .character_container`),
              charactersHtml,
              undefined,
              0,
              () => {
                $(
                  `.p_${
                    t + 1
                  }.container .character_container .icon.stockicon div`
                ).each((e, i) => {
                  if (
                    player.character[e + 1] &&
                    player.character[e + 1].assets[ASSET_TO_USE] != null
                  ) {
                    console.log(i);
                    CenterImage(
                      $(i),
                      $(i).attr("data-asset"),
                      $(i).attr("data-zoom"),
                      { x: 0.5, y: 0.5 },
                      $(i).parent().parent()
                    );
                  }
                });
              }
            );

            SetInnerHtml(
              $(`.p_${t + 1}.container .sponsor_icon`),
              player.sponsor_logo
                ? `<div style='background-image: url(../../${player.sponsor_logo})'></div>`
                : "<div></div>",
              undefined,
              0
            );

            SetInnerHtml(
              $(`.p_${t + 1} .avatar`),
              player.avatar
                ? `<div style="background-image: url('../../${player.avatar}')"></div>`
                : "",
              undefined,
              0
            );

            SetInnerHtml(
              $(`.p_${t + 1} .online_avatar`),
              player.online_avatar
                ? `<div style="background-image: url('${player.online_avatar}')"></div>`
                : '<div style="background: gray)"></div>',
              undefined,
              0
            );

            SetInnerHtml(
              $(`.p_${t + 1}.container .twitter`),
              player.twitter
                ? `<span class="twitter_logo"></span>${String(player.twitter)}`
                : "",
              undefined,
              0
            );

            SetInnerHtml(
              $(`.p_${t + 1}.container .sponsor-container`),
              `<div class='sponsor-logo' style='background-image: url(../../${player.sponsor_logo})'></div>`,
              undefined,
              0
            );
          }
        });

        gsap.from(
          $(`.round_${t + 1}`),
          { x: -100, autoAlpha: 0, duration: 0.4 },
          0.5 + 0.3 * t
        );
      });
    }

    $(".text").each(function (e) {
      FitText($($(this)[0].parentNode));
    });
  }

  Update();
  $(window).on("load", () => {
    $("body").fadeTo(1, 1, async () => {
      Start();
      setInterval(Update, 16);
    });
  });
})(jQuery);
