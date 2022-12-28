(($) => {
  var ASSET_TO_USE = "full";
  var ZOOM = 2;
  var ICON_TO_USE = "base_files/icon";
  var ICON_ZOOM = 1;

  var USE_ONLINE_PICTURE = false;

  gsap.config({ nullTargetWarn: false, trialWarn: false });

  let startingAnimation = gsap.timeline({ paused: true });

  function Start() {
    startingAnimation.restart();
  }

  var data = {};
  var oldData = {};

  var entryAnim = gsap.timeline();
  var animations = {};

  var iconAnimations = [];

  var players = [];
  var bracket = {};

  function AnimateLine(element) {
    let anim = null;

    if (element && element.get(0)) {
      element = element.get(0);
      let length = element.getTotalLength();
      anim = gsap.from(
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
        0
      );
    }

    return anim;
  }

  function AnimateElement(roundKey, setIndex, set) {
    if (animations[roundKey][setIndex]) {
      if (set.playerId[0] == -2 && set.playerId[1] == -2) {
        return animations[roundKey][setIndex].tweenTo("hidden");
      } else if (
        set.score[0] == set.score[1] ||
        set.playerId[0] == -2 ||
        set.playerId[1] == -2
      ) {
        return animations[roundKey][setIndex].tweenTo("displayed");
      } else {
        return animations[roundKey][setIndex].tweenTo("done");
      }
    }
    return null;
  }

  async function Update() {
    oldData = data;
    data = await getData();

    if (
      !oldData.bracket ||
      JSON.stringify(data.bracket.bracket) !=
        JSON.stringify(oldData.bracket.bracket)
    ) {
      bracket = data.bracket.bracket.rounds;
      players = data.bracket.players.slot;

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
        size -= 1;
        $(":root").css("--player-height", size);
      }
      $(":root").css("--name-size", Math.min(size - size * 0.3, 16));
      $(":root").css("--score-size", size - size * 0.3);
      $(":root").css("--flag-height", size - size * 0.4);

      if (
        !oldData.bracket ||
        oldData.bracket.bracket.length != data.bracket.bracket.length
      ) {
        // WINNERS SIDE
        let html = "";

        let winnersRounds = Object.fromEntries(
          Object.entries(bracket).filter(([round]) => parseInt(round) > 0)
        );

        // First row has only the player slots
        Object.entries(winnersRounds)
          .slice(0, 1)
          .forEach(([roundKey, round], r) => {
            html += `<div class="round round_base_w">`;
            Object.values(round.sets).forEach((slot, i) => {
              Object.values(slot.playerId).forEach((playerId, p) => {
                html += `
                  <div class="slot_full slot_${
                    i + 1
                  } p_${playerId} slot_p_${p} player container">
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
                  </div>
                `;
              });
            });
            html += "</div>";
          });

        Object.entries(winnersRounds)
          .slice(0, -2)
          .forEach(([roundKey, round], r) => {
            html += `<div class="round round_${roundKey}">`;
            html += `<div class="round_name"></div>`;
            Object.values(round.sets).forEach((slot, i) => {
              html += `<div class="slot_${
                i + 1
              }" style="width: 32px; height: 32px; align-self: center;"></div>`;
            });
            html += "</div>";
          });

        $(".winners_container").html(html);

        html = "";

        Object.entries(winnersRounds)
          .slice(-2, -1)
          .forEach(([roundKey, round], r) => {
            html += `<div class="round round_${roundKey}">`;
            html += `<div class="round_name"></div>`;
            Object.values(round.sets).forEach((slot, i) => {
              html += `<div class="slot_${
                i + 1
              }" style="width: 32px; height: 32px; align-self: center;"></div>`;
            });
            html += "</div>";
          });

        $(".center_container").html(html);

        // LOSERS SIDE
        html = "";

        let losersRounds = Object.fromEntries(
          Object.entries(bracket).filter(([round]) => parseInt(round) < 0)
        );

        Object.entries(losersRounds)
          .reverse()
          .forEach(([roundKey, round], r) => {
            html += `<div class="round round_${roundKey}">`;
            html += `<div class="round_name"></div>`;
            Object.values(round.sets).forEach((slot, i) => {
              if (r % 2 == 1) {
                html += `
                  <div class="slot_hanging slot_hanging_${
                    i + 1
                  } p_${0} slot_p_${0} player container">
                    <div class="character_container"></div>
                    <div class="name"></div>
                  </div>
                `;
                html += `<div class="slot_sibling_${
                  i + 1
                }" style="width: 32px; height: 32px; align-self: center;"></div>`;
              } else {
                // if (Object.keys(round.sets).length == 2) {
                //   html += `<div class="slot_sibling_${
                //     i + 1
                //   }" style="width: 32px; height: 32px; align-self: center;"></div>`;
                // }
              }
              html += `<div class="slot_${
                i + 1
              }" style="width: 32px; height: 32px; align-self: center;"></div>`;

              if (r % 2 == 1) {
                html += `<div class="slot_sibling_${
                  i + 1
                }" style="width: 32px; height: 32px; align-self: center;"></div>`;
              }
            });
            html += "</div>";
          });

        // Last row has all players
        Object.entries(losersRounds)
          .slice(0, 1)
          .forEach(([roundKey, round], r) => {
            html += `<div class="round round_base_l">`;
            Object.values(round.sets).forEach((slot, i) => {
              Object.values(slot.playerId).forEach((playerId, p) => {
                html += `<div class="slot_sibling_${
                  i + 1
                }" style="width: 32px; height: 32px; align-self: center;"></div>`;

                html += `
                  <div class="slot_hanging slot_${
                    i + 1
                  } p_${playerId} slot_p_${p} player container">
                    <div class="character_container"></div>
                    <div class="name"></div>
                  </div>
                `;
              });
            });
            html += "</div>";
          });

        $(".losers_container").html(html);

        // ICONS
        html = "";

        Object.entries(players).forEach(([teamId, team], t) => {
          Object.entries(team.player).forEach(([playerId, player], p) => {
            html += `
            <div class="bracket_icon bracket_icon_p${teamId}">
              <div class="icon_name_arrow">
                <div class="icon_name"></div>
                <div class="icon_arrow_border"></div>
                <div class="icon_arrow"></div>
              </div>
              <div class="icon_image"></div>
            </div>`;
            return;
          });
        });

        $(".winners_icons").html(html);
        $(".losers_icons").html(html);

        // BRACKET LINES
        // .line_r_(round) = Line going from (round) set to the next set
        let slotLines = "";

        let baseClass = "winners_container";

        Object.entries(bracket).forEach(function ([roundKey, round], r) {
          if (parseInt(roundKey) < 0) {
            baseClass = "losers_container";
          } else {
            baseClass = "winners_container";
          }

          Object.values(round.sets).forEach(
            function (slot, i) {
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

                // Initial line from base
                if (roundKey == "1" || roundKey == "-1") {
                  [0, 1].forEach((index) => {
                    let className =
                      roundKey == "1" ? "round_base_w" : "round_base_l";

                    let baseElement = $(
                      `.${this.baseClass} .${className} .slot_${
                        i + 1
                      }.slot_p_${index}`
                    );

                    slotLines += `<path class="${
                      this.baseClass
                    } line_base_r_${roundKey} s_${i + 1} p_${index}" d="
                    M${[
                      baseElement.offset().left + baseElement.outerWidth() / 2,
                      baseElement.offset().top + baseElement.outerHeight() / 2,
                    ].join(" ")}
                    ${[
                      [
                        baseElement.offset().left +
                          baseElement.outerWidth() / 2 +
                          (slotElement.offset().left -
                            (baseElement.offset().left +
                              baseElement.outerWidth() / 2)) /
                            2,
                        baseElement.offset().top +
                          baseElement.outerHeight() / 2,
                      ],
                      [
                        slotElement.offset().left +
                          slotElement.outerWidth() / 2,
                        baseElement.offset().top +
                          baseElement.outerHeight() / 2,
                      ],
                      [
                        slotElement.offset().left +
                          slotElement.outerWidth() / 2,
                        slotElement.offset().top +
                          slotElement.outerHeight() / 2,
                      ],
                    ]
                      .map((point) => point.join(" "))
                      .map((point) => "L" + point)
                      .join(" ")}"
                    stroke="gray" fill="none" stroke-width="8" />`;
                  });
                }

                if (
                  winElement &&
                  winElement.offset() &&
                  parseInt(roundKey) > 0
                ) {
                  slotLines += `<path class="${
                    this.baseClass
                  } line_r_${roundKey} s_${i + 1}" d="
                  M${[
                    slotElement.offset().left + slotElement.outerWidth() / 2,
                    slotElement.offset().top + slotElement.outerHeight() / 2,
                  ].join(" ")}
                  ${[
                    [
                      slotElement.offset().left +
                        slotElement.outerWidth() / 2 +
                        (winElement.offset().left -
                          (slotElement.offset().left +
                            slotElement.outerWidth() / 2)) /
                          2,
                      slotElement.offset().top + slotElement.outerHeight() / 2,
                    ],
                    [
                      winElement.offset().left + winElement.outerWidth() / 2,
                      slotElement.offset().top + slotElement.outerHeight() / 2,
                    ],
                    [
                      winElement.offset().left + winElement.outerWidth() / 2,
                      winElement.offset().top + winElement.outerHeight() / 2,
                    ],
                  ]
                    .map((point) => point.join(" "))
                    .map((point) => "L" + point)
                    .join(" ")}"
                  stroke="gray" fill="none" stroke-width="8" />`;
                }

                if (parseInt(roundKey) < 0) {
                  if (parseInt(roundKey) % 2 == -1) {
                    let hangingElement = $(
                      `.${this.baseClass} .round_${roundKey} .slot_hanging_${
                        i + 1
                      }`
                    );

                    if (
                      winElement &&
                      winElement.offset() &&
                      hangingElement &&
                      hangingElement.offset()
                    ) {
                      slotLines += `<path class="${
                        this.baseClass
                      } line_r_${roundKey} s_${i * 2 + 1}" d="
                        M${[
                          hangingElement.offset().left +
                            hangingElement.outerWidth() / 2,
                          hangingElement.offset().top +
                            hangingElement.outerHeight() / 2,
                        ].join(" ")}
                        ${[
                          [
                            hangingElement.offset().left +
                              hangingElement.outerWidth() / 2 +
                              (winElement.offset().left -
                                (hangingElement.offset().left +
                                  hangingElement.outerWidth() / 2)) /
                                2,
                            hangingElement.offset().top +
                              hangingElement.outerHeight() / 2,
                          ],
                          [
                            winElement.offset().left +
                              winElement.outerWidth() / 2,
                            hangingElement.offset().top +
                              hangingElement.outerHeight() / 2,
                          ],
                          [
                            winElement.offset().left +
                              winElement.outerWidth() / 2,
                            winElement.offset().top +
                              winElement.outerHeight() / 2,
                          ],
                        ]
                          .map((point) => point.join(" "))
                          .map((point) => "L" + point)
                          .join(" ")}"
                        stroke="gray" fill="none" stroke-width="8" />`;
                    }
                  }
                  if (winElement && winElement.offset()) {
                    slotLines += `<path class="${
                      this.baseClass
                    } line_r_${roundKey} s_${(i + 1) * 2}" d="
                      M${[
                        slotElement.offset().left +
                          slotElement.outerWidth() / 2,
                        slotElement.offset().top +
                          slotElement.outerHeight() / 2,
                      ].join(" ")}
                      ${[
                        [
                          slotElement.offset().left +
                            slotElement.outerWidth() / 2 +
                            (winElement.offset().left -
                              (slotElement.offset().left +
                                slotElement.outerWidth() / 2)) /
                              2,
                          slotElement.offset().top +
                            slotElement.outerHeight() / 2,
                        ],
                        [
                          winElement.offset().left +
                            winElement.outerWidth() / 2,
                          slotElement.offset().top +
                            slotElement.outerHeight() / 2,
                        ],
                        [
                          winElement.offset().left +
                            winElement.outerWidth() / 2,
                          winElement.offset().top +
                            winElement.outerHeight() / 2,
                        ],
                      ]
                        .map((point) => point.join(" "))
                        .map((point) => "L" + point)
                        .join(" ")}"
                      stroke="gray" fill="none" stroke-width="8" />`;
                  }
                }
              }
            },
            { baseClass: baseClass }
          );
        });

        $(".lines").html(slotLines);

        // ICON ANIMATIONS
        Object.entries(players).forEach(([teamId, team], t) => {
          Object.entries(team.player).forEach(([playerId, player], p) => {
            // Winners path
            let icon_element = $(
              `.winners_icons .bracket_icon.bracket_icon_p${teamId}`
            );
            if (!icon_element) return;

            let icon_anim = gsap.timeline();

            Object.entries(winnersRounds)
              .slice(0, -2)
              .forEach(([roundKey, round], r) => {
                Object.values(round.sets).forEach((slot, i) => {
                  Object.values(slot.playerId).forEach(
                    (slotPlayerId, slotIndex) => {
                      if (slotPlayerId == teamId) {
                        if (roundKey == "1") {
                          let setElement = $(
                            `.round_base_w .slot_${i + 1}.slot_p_${slotIndex}`
                          );

                          if (setElement && setElement.offset()) {
                            icon_anim.set($(icon_element), {
                              x:
                                setElement.offset().left +
                                setElement.outerWidth() -
                                $(icon_element).outerWidth() / 4,
                              y:
                                setElement.offset().top +
                                setElement.outerHeight() / 2 -
                                $(icon_element).outerHeight() / 2,
                            });
                          }
                        }

                        let setElement = $(`.round_${roundKey} .slot_${i + 1}`);

                        if (setElement && setElement.offset()) {
                          icon_anim.to($(icon_element), {
                            x: setElement.offset().left,
                            duration: 1,
                          });

                          // Only continue if won
                          if (
                            slot.score[slotIndex] >
                            slot.score[(slotIndex + 1) % 2]
                          ) {
                            icon_anim.to($(icon_element), {
                              x: setElement.offset().left,
                              y: setElement.offset().top,
                              duration: 1,
                            });
                          } else {
                            // TODO: remove
                            icon_anim.fromTo(
                              $(icon_element).find(".icon_image"),
                              { filter: "brightness(1)" },
                              {
                                filter: "brightness(.5)",
                                duration: 0.4,
                              }
                            );
                          }
                        }
                      }
                    }
                  );
                });
              });

            // Losers path
            icon_element = $(
              `.losers_icons .bracket_icon.bracket_icon_p${teamId}`
            );
            if (!icon_element) return;

            icon_anim = gsap.timeline();

            let found = false;

            Object.entries(losersRounds).forEach(([roundKey, round], r) => {
              Object.values(round.sets).forEach((slot, i) => {
                Object.values(slot.playerId).forEach(
                  (slotPlayerId, slotIndex) => {
                    if (slotPlayerId == teamId) {
                      if (roundKey == "-1") {
                        let setElement = $(
                          `.round_base_l .slot_${i + 1}.slot_p_${slotIndex}`
                        );

                        if (setElement && setElement.offset()) {
                          icon_anim.set($(icon_element), {
                            x:
                              setElement.offset().left -
                              ($(icon_element).outerWidth() * 3) / 4,
                            y:
                              setElement.offset().top +
                              setElement.outerHeight() / 2 -
                              $(icon_element).outerHeight() / 2,
                          });
                        }
                      } else if (!found) {
                        let setElement = $(
                          `.round_${parseInt(roundKey) + 1} .slot_hanging_${
                            i + 1
                          }`
                        );

                        if (setElement && setElement.offset()) {
                          icon_anim.set($(icon_element), {
                            x:
                              setElement.offset().left -
                              ($(icon_element).outerWidth() * 3) / 4,
                            y:
                              setElement.offset().top +
                              setElement.outerHeight() / 2 -
                              $(icon_element).outerHeight() / 2,
                          });
                        }
                      }

                      let setElement = $(`.round_${roundKey} .slot_${i + 1}`);

                      if (setElement && setElement.offset()) {
                        icon_anim.to($(icon_element), {
                          x: setElement.offset().left,
                          duration: 1,
                        });
                        // Only continue if won
                        if (
                          slot.score[slotIndex] >
                          slot.score[(slotIndex + 1) % 2]
                        ) {
                          icon_anim.to($(icon_element), {
                            x: setElement.offset().left,
                            y: setElement.offset().top,
                            duration: 1,
                          });
                        } else {
                          // TODO: remove
                          icon_anim.fromTo(
                            $(icon_element).find(".icon_image"),
                            { filter: "brightness(1)" },
                            {
                              filter: "brightness(.5)",
                              duration: 0.4,
                            }
                          );
                        }
                      }

                      found = true;
                    }
                  }
                );
              });
            });
            return;
          });
        });
      }

      let GfResetRoundNum = Math.max.apply(
        null,
        Object.keys(bracket).map((r) => parseInt(r))
      );

      let gf = bracket[GfResetRoundNum - 1].sets[0];
      let isReset = gf.score[0] < gf.score[1];

      // COLORIZE LINES
      Object.entries(bracket).forEach(function ([roundKey, round], r) {
        Object.values(round.sets).forEach((set, setIndex) => {
          let won = false;

          if (
            set.nextWin &&
            bracket[set.nextWin[0]] &&
            bracket[set.nextWin[0]].sets
          ) {
            let nextSet = bracket[set.nextWin[0]].sets[set.nextWin[1]];

            let wonSet =
              set.score[0] > set.score[1] ? set.playerId[0] : set.playerId[1];

            if (nextSet) {
              let wonNextSet =
                nextSet.score[0] > nextSet.score[1]
                  ? nextSet.playerId[0]
                  : nextSet.playerId[1];

              if (wonNextSet == wonSet) {
                won = true;
              }
            }
          }

          // if (roundKey == "1" || roundKey == "-1") {
          //   let wonIndex = set.score[0] > set.score[1] ? 0 : 1;

          //   $(`.line_base_r_${roundKey}.s_${setIndex + 1}.p_${wonIndex}`).attr(
          //     "stroke",
          //     "yellow"
          //   );
          // }

          // $(`.line_r_${roundKey}.s_${setIndex + 1}`).attr(
          //   "stroke",
          //   won ? "yellow" : "gray"
          // );
        });
      });

      // TRIGGER ANIMATIONS
      if (entryAnim && entryAnim.progress() >= 1) {
        Object.entries(bracket).forEach(function ([roundKey, round], r) {
          Object.values(round.sets).forEach((set, setIndex) => {
            AnimateElement(roundKey, setIndex, set);
          });
        });
      }

      // UPDATE SCORES
      Object.entries(bracket).forEach(function ([roundKey, round], r) {
        SetInnerHtml($(`.round_${parseInt(roundKey)} .round_name`), round.name);

        Object.values(round.sets).forEach(function (slot, i) {
          Object.values(slot.score).forEach(function (score, p) {
            SetInnerHtml(
              $(
                `.round_${parseInt(roundKey)} .slot_${
                  i + 1
                }.slot_p_${p}.container .score`
              ),
              `
                  ${score == -1 ? "DQ" : score}
                `
            );
          });
          if (slot.score[0] > slot.score[1]) {
            $(
              `.round_${parseInt(roundKey)} .slot_${
                i + 1
              }.slot_p_${0}.container`
            ).css("filter", "brightness(1)");
            $(
              `.round_${parseInt(roundKey)} .slot_${
                i + 1
              }.slot_p_${1}.container`
            ).css("filter", "brightness(0.6)");
          } else if (slot.score[1] > slot.score[0]) {
            $(
              `.round_${parseInt(roundKey)} .slot_${
                i + 1
              }.slot_p_${0}.container`
            ).css("filter", "brightness(0.6)");
            $(
              `.round_${parseInt(roundKey)} .slot_${
                i + 1
              }.slot_p_${1}.container`
            ).css("filter", "brightness(1)");
          } else {
            $(
              `.round_${parseInt(roundKey)} .slot_${
                i + 1
              }.slot_p_${0}.container`
            ).css("filter", "brightness(1)");
            $(
              `.round_${parseInt(roundKey)} .slot_${
                i + 1
              }.slot_p_${1}.container`
            ).css("filter", "brightness(1)");
          }
        });
      });

      // UPDATE PLAYER DATA
      Object.entries(bracket).forEach(function ([roundKey, round], r) {
        Object.values(round.sets).forEach((set, setIndex) => {
          set.playerId.forEach((pid, index) => {
            if (parseInt(roundKey) > 0 && roundKey != "1") return;

            let element = null;

            if (parseInt(roundKey) > 0) {
              element = $(
                `.round_base_w .slot_${setIndex + 1}.slot_p_${index}`
              ).get(0);
            } else {
              if (roundKey == "-1") {
                element = $(
                  `.round_base_l .slot_${setIndex + 1}.slot_p_${index}`
                ).get(0);
              } else {
                element = $(
                  `.round_${parseInt(roundKey) + 1} .slot_hanging_${
                    setIndex + 1
                  }.slot_p_${index}`
                ).get(0);
              }
            }

            if (!element) return;

            let player = null;

            if (players[pid]) player = players[pid].player["1"];

            SetInnerHtml(
              $(element).find(`.name`),
              `
                <span>
                  <span class="sponsor">
                    ${player && player.team ? player.team : ""}
                  </span>
                  ${player ? player.name : ""}
                </span>
              `
            );

            SetInnerHtml(
              $(element).find(`.flagcountry`),
              player && player.country.asset
                ? `<div class='flag' style='background-image: url(../../${player.country.asset.toLowerCase()})'></div>`
                : ""
            );

            SetInnerHtml(
              $(element).find(`.flagstate`),
              player && player.state.asset
                ? `<div class='flag' style='background-image: url(../../${player.state.asset})'></div>`
                : ""
            );

            let charactersHtml = "";

            if (player && player.character) {
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
            }
            SetInnerHtml(
              $(element).find(`.character_container`),
              charactersHtml,
              undefined,
              0.5,
              () => {
                $(element)
                  .find(`.character_container .icon.stockicon div`)
                  .each((e, i) => {
                    if (
                      player &&
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
              $(element).find(`.sponsor_icon`),
              player && player.sponsor_logo
                ? `<div style='background-image: url(../../${player.sponsor_logo})'></div>`
                : "<div></div>"
            );

            SetInnerHtml(
              $(element).find(`.avatar`),
              player && player.avatar
                ? `<div style="background-image: url('../../${player.avatar}')"></div>`
                : ""
            );

            SetInnerHtml(
              $(element).find(`.online_avatar`),
              player && player.online_avatar
                ? `<div style="background-image: url('${player.online_avatar}')"></div>`
                : '<div style="background: gray)"></div>'
            );

            SetInnerHtml(
              $(element).find(`.twitter`),
              player && player.twitter
                ? `<span class="twitter_logo"></span>${String(player.twitter)}`
                : ""
            );

            SetInnerHtml(
              $(element).find(`.sponsor-container`),
              `<div class='sponsor-logo' style='background-image: url(../../${
                player ? player.sponsor_logo : ""
              })'></div>`
            );
          });
        });
      });
    }

    // UPDATE ICONS
    Object.entries(players).forEach(([teamId, team], t) => {
      Object.entries(team.player).forEach(([playerId, player], p) => {
        let element = $(`.bracket_icon.bracket_icon_p${teamId}`);
        if (!element) return;
        let charactersHtml = "";

        SetInnerHtml(
          $(element).find(`.icon_name`),
          `
            <span>
              ${player ? player.name : ""}
            </span>
          `
        );

        if (!USE_ONLINE_PICTURE) {
          if (
            player &&
            (!oldData.bracket ||
              JSON.stringify(oldData.bracket.players.slot[teamId]) !=
                JSON.stringify(data.bracket.players.slot[teamId]))
          ) {
            if (player && player.character) {
              Object.values(player.character).forEach((character, index) => {
                if (character.assets[ICON_TO_USE]) {
                  charactersHtml += `
                    <div class="floating_icon stockicon">
                        <div
                          style='background-image: url(../../${
                            character.assets[ICON_TO_USE].asset
                          })'
                          data-asset='${JSON.stringify(
                            character.assets[ICON_TO_USE]
                          )}'
                          data-zoom='${ICON_ZOOM}'
                        >
                        </div>
                    </div>
                    `;
                }
              });
            }
            SetInnerHtml(
              $(element).find(".icon_image"),
              charactersHtml,
              undefined,
              0,
              () => {
                $(element)
                  .find(`.icon_image .floating_icon.stockicon div`)
                  .each((e, i) => {
                    if (
                      player &&
                      player.character[1] &&
                      player.character[1].assets[ICON_TO_USE] != null
                    ) {
                      CenterImage(
                        $(i),
                        $(i).attr("data-asset"),
                        $(i).attr("data-zoom"),
                        { x: 0.5, y: 0.5 },
                        $(i),
                        true,
                        true
                      );
                    }
                  });
              }
            );
          }
        } else {
          SetInnerHtml(
            $(element).find(".icon_image"),
            player && player.online_avatar
              ? `<div style="background-image: url('${player.online_avatar}')"></div>`
              : '<div style="background: gray; width: 100%; height: 100%; border-radius: 8px;"></div>'
          );
        }

        // SET ICON POSITION
        // ["winners", "losers"].forEach((side) => {
        //   let element = $(
        //     `.${side}_icons .bracket_icon.bracket_icon_p${teamId}`
        //   );
        //   if (!element) return;

        //   let lastFoundRound = 0;
        //   let lastFoundSetIndex = 0;
        //   let prevLastFoundRound = 0;
        //   let prevLastFoundSetIndex = 0;

        //   let GfResetRoundNum = Math.max.apply(
        //     null,
        //     Object.keys(bracket).map((r) => parseInt(r))
        //   );

        //   Object.entries(bracket).forEach(function ([roundKey, round], r) {
        //     if (side == "winners" && parseInt(roundKey) < 0) return;
        //     if (side == "losers" && parseInt(roundKey) > 0) return;
        //     Object.values(round.sets).forEach(function (set, setIndex) {
        //       if (
        //         ((side == "losers" &&
        //           parseInt(roundKey) < parseInt(lastFoundRound)) ||
        //           (side == "winners" &&
        //             parseInt(roundKey) > parseInt(lastFoundRound))) &&
        //         (set.playerId[0] == teamId || set.playerId[1] == teamId) &&
        //         roundKey != GfResetRoundNum
        //       ) {
        //         prevLastFoundRound = lastFoundRound;
        //         prevLastFoundSetIndex = lastFoundSetIndex;
        //         lastFoundRound = roundKey;
        //         lastFoundSetIndex = setIndex;
        //       }
        //     });
        //   });

        //   let index = 0;

        //   if (lastFoundRound != 0) {
        //     index =
        //       bracket[lastFoundRound].sets[lastFoundSetIndex].playerId[0] ==
        //       teamId
        //         ? 0
        //         : 1;
        //   }
        //   if (lastFoundRound == "1") {
        //     let setElement = $(
        //       `.round_base_w .slot_${lastFoundSetIndex + 1}.slot_p_${index}`
        //     );

        //     if (setElement && setElement.offset()) {
        //       $(element).css(
        //         "left",
        //         setElement.offset().left +
        //           setElement.outerWidth() -
        //           $(element).outerWidth() / 4
        //       );
        //       $(element).css(
        //         "top",
        //         setElement.offset().top +
        //           setElement.outerHeight() / 2 -
        //           $(element).outerHeight() / 2
        //       );

        //       $(element).find(".icon_name_arrow").css("opacity", 0);
        //     }
        //   } else if (
        //     lastFoundRound == "-1" ||
        //     (parseInt(lastFoundRound) < 0 &&
        //       parseInt(lastFoundRound) % 2 == 0 &&
        //       index == 0)
        //   ) {
        //     let setElement = null;

        //     if (lastFoundRound == "-1") {
        //       setElement = $(
        //         `.round_base_l .slot_${lastFoundSetIndex + 1}.slot_p_${index}`
        //       );
        //       $(element).find(".icon_name_arrow").css("opacity", 0);
        //     } else if (index == 0) {
        //       setElement = $(
        //         `.round_${parseInt(lastFoundRound) + 1} .slot_hanging_${
        //           lastFoundSetIndex + 1
        //         }`
        //       );
        //       $(element).find(".icon_name_arrow").css("opacity", 0);
        //     }

        //     if (setElement && setElement.offset()) {
        //       $(element).css(
        //         "left",
        //         setElement.offset().left - ($(element).outerWidth() * 3) / 4
        //       );
        //       $(element).css(
        //         "top",
        //         setElement.offset().top +
        //           setElement.outerHeight() / 2 -
        //           $(element).outerHeight() / 2
        //       );
        //     }
        //   } else {
        //     let setElement = $(
        //       `.round_${prevLastFoundRound} .slot_${prevLastFoundSetIndex + 1}`
        //     );

        //     if (setElement && setElement.offset()) {
        //       $(element).css("left", setElement.offset().left);
        //       $(element).css("top", setElement.offset().top);
        //     }
        //   }
        // });

        return;
      });
    });

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
