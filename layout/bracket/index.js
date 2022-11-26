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
      let players = data.bracket.players.slot;

      let html = "";

      let winnersRounds = Object.fromEntries(
        Object.entries(bracket).filter(([round]) => parseInt(round) > 0)
      );

      console.log(winnersRounds);

      Object.values(winnersRounds).forEach((round, r) => {
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

      let slotLines = "";

      Object.values(bracket).forEach((round, r) => {
        Object.values(round).forEach((slot, i) => {
          if (
            slot.playerId[0] > Object.keys(players).length ||
            slot.playerId[1] > Object.keys(players).length
          ) {
            $(`.round_${r} .slot_${i + 1} .slot_p_0.container`).css(
              "opacity",
              "0"
            );
            $(`.round_${r} .slot_${i + 1} .slot_p_1.container`).css(
              "opacity",
              "0"
            );
          }
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
          if (slot.score[0] > slot.score[1]) {
            $(`.round_${r} .slot_${i + 1} .slot_p_${1}.container`).css(
              "filter",
              "brightness(0.6)"
            );
          } else if (slot.score[1] > slot.score[0]) {
            $(`.round_${r} .slot_${i + 1} .slot_p_${0}.container`).css(
              "filter",
              "brightness(0.6)"
            );
          }

          let slotElement = $(`.round_${r} .slot_${i + 1}`);

          if (slotElement && slotElement.position()) {
            console.log(slotElement.position());
            slotLines += `<line
              x1=${slotElement.position().left + slotElement.width()}
              y1=${slotElement.position().top + slotElement.height() / 2}
              x2=${slotElement.position().left + slotElement.width() + 10}
              y2=${slotElement.position().top + slotElement.height() / 2} 
              stroke="black" width="5" />`;
          }
        });
      });

      $(".lines").html(slotLines);

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
                    player.character[1] &&
                    player.character[1].assets[ASSET_TO_USE] != null
                  ) {
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
    $("body").fadeTo(1000, 1000, async () => {
      Start();
      setInterval(Update, 16);
    });
  });
})(jQuery);
