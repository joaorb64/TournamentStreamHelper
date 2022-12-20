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

      let progressionsOut = data.bracket.bracket.progressionsOut;
      let progressionsIn = data.bracket.bracket.progressionsIn;

      let biggestRound = Math.max.apply(
        null,
        Object.values(bracket).map((r) => Object.keys(r.sets).length)
      );
      console.log(biggestRound);

      let size = 32;
      $(":root").css("--player-height", size);

      while (
        biggestRound * (2 * parseInt($(":root").css("--player-height")) + 4) >
        $(".winners_container").height() - 20
      ) {
        console.log("repeat");
        size -= 1;
        $(":root").css("--player-height", size);
      }
      $(":root").css("--name-size", Math.min(size - size * 0.3, 16));
      $(":root").css("--score-size", size - size * 0.3);
      $(":root").css("--flag-height", size - size * 0.4);

      let html = "";

      let winnersRounds = Object.fromEntries(
        Object.entries(bracket).filter(([round]) => parseInt(round) > 0)
      );

      Object.entries(winnersRounds).forEach(([roundKey, round], r) => {
        html += `<div class="round round_${roundKey}">`;
        html += `<div class="round_name"></div>`;
        Object.values(round.sets).forEach((slot, i) => {
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

      $(".winners_container").html(html);

      html = "";

      let losersRounds = Object.fromEntries(
        Object.entries(bracket).filter(([round]) => parseInt(round) < 0)
      );

      Object.entries(losersRounds).forEach(([roundKey, round], r) => {
        html += `<div class="round round_${roundKey}">`;
        html += `<div class="round_name"></div>`;
        Object.values(round.sets).forEach((slot, i) => {
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

      $(".losers_container").html(html);

      let slotLines = "";

      let baseClass = "winners_container";

      Object.entries(bracket).forEach(function ([roundKey, round], r) {
        if (parseInt(roundKey) < 0) {
          baseClass = "losers_container";
        } else {
          baseClass = "winners_container";
        }

        console.log(round.name);

        SetInnerHtml(
          $(`.${baseClass} .round_${parseInt(roundKey)} .round_name`),
          round.name
        );

        Object.values(round.sets).forEach(
          function (slot, i) {
            Object.values(slot.score).forEach(
              function (score, p) {
                SetInnerHtml(
                  $(
                    `.${this.baseClass} .round_${parseInt(roundKey)} .slot_${
                      i + 1
                    } .slot_p_${p}.container .score`
                  ),
                  `
                ${score == -1 ? "DQ" : score}
              `,
                  undefined,
                  0
                );
              },
              { baseClass: baseClass }
            );
            if (slot.score[0] > slot.score[1]) {
              $(
                `.${this.baseClass} .round_${parseInt(roundKey)} .slot_${
                  i + 1
                } .slot_p_${1}.container`
              ).css("filter", "brightness(0.6)");
            } else if (slot.score[1] > slot.score[0]) {
              $(
                `.${this.baseClass} .round_${parseInt(roundKey)} .slot_${
                  i + 1
                } .slot_p_${0}.container`
              ).css("filter", "brightness(0.6)");
            }

            let lastLosers =
              parseInt(roundKey) ==
              Math.min.apply(
                null,
                Object.keys(bracket).map((r) => parseInt(r))
              );

            if (
              slot.nextWin &&
              !(
                slot.playerId[0] > Object.keys(players).length ||
                slot.playerId[1] > Object.keys(players).length ||
                slot.playerId[0] == -1 ||
                slot.playerId[1] == -1
              )
            ) {
              let slotElement = $(
                `.${this.baseClass} .round_${roundKey} .slot_${i + 1}`
              );

              if (!slotElement || !slotElement.offset()) return;

              let winElement = $(
                `.${this.baseClass} .round_${slot.nextWin[0]} .slot_${
                  slot.nextWin[1] + 1
                }`
              );

              if (winElement && winElement.offset()) {
                slotLines += `<path class="${this.baseClass} r_${roundKey} s_${
                  i + 1
                }" d="
                M${[
                  slotElement.offset().left + slotElement.outerWidth(),
                  slotElement.offset().top + slotElement.outerHeight() / 2,
                ].join(" ")}
                ${[
                  [
                    slotElement.offset().left +
                      slotElement.outerWidth() +
                      (winElement.offset().left -
                        (slotElement.offset().left +
                          slotElement.outerWidth())) /
                        2,
                    slotElement.offset().top + slotElement.outerHeight() / 2,
                  ],
                  [
                    slotElement.offset().left +
                      slotElement.outerWidth() +
                      (winElement.offset().left -
                        (slotElement.offset().left +
                          slotElement.outerWidth())) /
                        2,
                    winElement.offset().top + slotElement.outerHeight() / 2,
                  ],
                  [
                    winElement.offset().left,
                    winElement.offset().top + winElement.outerHeight() / 2,
                  ],
                ]
                  .map((point) => point.join(" "))
                  .map((point) => "L" + point)
                  .join(" ")}"
                stroke="black" fill="none" stroke-width="3" />`;
              }

              // Lines for progressions in
              if (
                progressionsIn > 0 &&
                ((parseInt(roundKey) > 0 && parseInt(roundKey) == 1) ||
                  (parseInt(roundKey) < 0 && Math.abs(parseInt(roundKey)) == 1))
              ) {
                slotLines += `<path class="${this.baseClass} in_r_${
                  Math.sign(parseInt(roundKey)) * Math.abs(parseInt(roundKey))
                } s_${i + 1}" d="
                M${[
                  slotElement.offset().left - 50,
                  slotElement.offset().top + slotElement.outerHeight() / 2,
                ].join(" ")}
                ${[
                  [
                    slotElement.offset().left,
                    slotElement.offset().top + slotElement.outerHeight() / 2,
                  ],
                ]
                  .map((point) => point.join(" "))
                  .map((point) => "L" + point)
                  .join(" ")}"
                stroke="black" fill="none" stroke-width="3" />`;
              }

              // Lines for progressions out
              if (
                progressionsOut > 0 &&
                ((parseInt(roundKey) > 0 &&
                  parseInt(roundKey) == Object.keys(winnersRounds).length) ||
                  (parseInt(roundKey) < 0 &&
                    Math.abs(parseInt(roundKey)) ==
                      Object.keys(losersRounds).length))
              ) {
                slotLines += `<path class="${this.baseClass} r_${roundKey} s_${
                  i + 1
                }" d="
                M${[
                  slotElement.offset().left + slotElement.outerWidth(),
                  slotElement.offset().top + slotElement.outerHeight() / 2,
                ].join(" ")}
                ${[
                  [
                    slotElement.offset().left + slotElement.outerWidth() + 45,
                    slotElement.offset().top + slotElement.outerHeight() / 2,
                  ],
                ]
                  .map((point) => point.join(" "))
                  .map((point) => "L" + point)
                  .join(" ")}
                M${[
                  slotElement.offset().left + slotElement.outerWidth() + 40,
                  slotElement.offset().top + slotElement.outerHeight() / 2 - 5,
                ].join(" ")}
                ${[
                  [
                    slotElement.offset().left + slotElement.outerWidth() + 45,
                    slotElement.offset().top + slotElement.outerHeight() / 2,
                  ],
                  [
                    slotElement.offset().left + slotElement.outerWidth() + 40,
                    slotElement.offset().top +
                      slotElement.outerHeight() / 2 +
                      5,
                  ],
                ]
                  .map((point) => point.join(" "))
                  .map((point) => "L" + point)
                  .join(" ")}"
                stroke="black" fill="none" stroke-width="3" />`;
              }
            }
          },
          { baseClass: baseClass }
        );
      });

      $(".lines").html(slotLines);

      let GfResetRoundNum = Math.max.apply(
        null,
        Object.keys(bracket).map((r) => parseInt(r))
      );

      let gf = bracket[GfResetRoundNum - 1].sets[0];
      let isReset = gf.score[0] < gf.score[1];

      Object.entries(bracket).forEach(function ([roundKey, round], r) {
        Object.values(round.sets).forEach((set, setIndex) => {
          let anim = gsap.from(
            $(`.round_${roundKey} .slot_${setIndex + 1}`),
            { x: -50, autoAlpha: 0, duration: 0.4 },
            0.5 + 0.8 * Math.abs(parseInt(roundKey))
          );

          if (parseInt(roundKey) == GfResetRoundNum && !isReset) {
            anim.pause();
          }
          if (set.playerId[0] == -1 || set.playerId[1] == -1) {
            anim.pause();
          }
        });

        let roundLines = $(`.r_${roundKey}, .in_r_${roundKey}`);

        roundLines.each((index, element) => {
          if (element) {
            let length = element.getTotalLength();
            let anim = gsap.from(
              element,
              {
                duration: 0.4,
                "stroke-dashoffset": length,
                "stroke-dasharray": length,
                opacity: 0,
                onUpdate: function (tl) {
                  let tlp = (this.progress() * 100) >> 0;
                  if (element) {
                    let length = element.getTotalLength();
                    TweenMax.set(element, {
                      "stroke-dashoffset": (length / 100) * (100 - tlp),
                      "stroke-dasharray": length,
                      opacity: 1,
                    });
                  }
                },
                onUpdateParams: ["{self}"],
              },
              0.9 +
                0.8 * Math.abs(parseInt(roundKey)) -
                ($(element).is(`.in_r_${roundKey}`) ? 0.8 : 0)
            );

            if (parseInt(roundKey) == GfResetRoundNum - 1 && !isReset) {
              anim.pause();
            }
          }
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
