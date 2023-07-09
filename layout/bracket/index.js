LoadEverything().then(() => {
  gsap.config({ nullTargetWarn: false, trialWarn: false });

  let startingAnimation = gsap.timeline({ paused: true });

  Start = async (event) => {
    startingAnimation.restart();
  };

  var entryAnim = gsap.timeline();
  var animations = {};

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

  function AnimateElement(roundKey, setIndex, set, bracket, progressionsOut) {
    let isGf = false;
    let isGfR = false;
    let GfResetRoundNum = 0;

    if (progressionsOut == 0) {
      GfResetRoundNum = Math.max.apply(
        null,
        Object.keys(bracket).map((r) => parseInt(r))
      );

      isGf = parseInt(roundKey) == GfResetRoundNum - 1;
      isGfR = parseInt(roundKey) == GfResetRoundNum;
    }

    if (animations[roundKey][setIndex]) {
      if (window.ALWAYS_EXPAND) {
        // Hide incomplete sets (-1), but not pending (-2)
        if (
          (set.playerId[0] == -1 && set.playerId[1] != -1) ||
          (set.playerId[0] != -1 && set.playerId[1] == -1)
        ) {
          return animations[roundKey][setIndex].tweenTo("hidden");
        }

        if (!isGf && !isGfR)
          return animations[roundKey][setIndex].tweenTo("done");

        if (isGf) {
          if (set.score[0] >= set.score[1] || !set.completed) {
            return animations[roundKey][setIndex].tweenTo("displayed");
          } else {
            return animations[roundKey][setIndex].tweenTo("done");
          }
        }

        if (
          progressionsOut == 0 &&
          isGfR &&
          bracket[GfResetRoundNum - 1].sets[0].score[0] <
            bracket[GfResetRoundNum - 1].sets[0].score[1] &&
          bracket[GfResetRoundNum - 1].sets[0].completed
        ) {
          return animations[roundKey][setIndex].tweenTo("displayed");
        } else {
          return animations[roundKey][setIndex].tweenTo("hidden");
        }
      } else {
        if (
          (set.playerId[0] == -2 && set.playerId[1] == -2) ||
          (set.playerId[0] == -1 && set.playerId[1] != -1) ||
          (set.playerId[0] != -1 && set.playerId[1] == -1) ||
          (progressionsOut == 0 &&
            isGfR &&
            bracket[GfResetRoundNum - 1].sets[0].score[0] >
              bracket[GfResetRoundNum - 1].sets[0].score[1])
        ) {
          return animations[roundKey][setIndex].tweenTo("hidden");
        } else if (!set.completed || (isGf && set.score[0] >= set.score[1])) {
          return animations[roundKey][setIndex].tweenTo("displayed");
        } else {
          return animations[roundKey][setIndex].tweenTo("done");
        }
      }
    }
    return null;
  }

  Update = async (event) => {
    let data = event.data;
    let oldData = event.oldData;

    if (
      !oldData.bracket ||
      JSON.stringify(data.bracket.bracket) !=
        JSON.stringify(oldData.bracket.bracket)
    ) {
      let bracket = data.bracket.bracket.rounds;
      let players = data.bracket.players.slot;

      let progressionsOut = data.bracket.bracket.progressionsOut;
      let progressionsIn = data.bracket.bracket.progressionsIn;
      let winnersOnlyProgressions =
        data.bracket.bracket.winnersOnlyProgressions;

      let biggestRound = Math.max.apply(
        null,
        Object.values(bracket).map((r) => {
          const setMap = Object.values(r.sets).map((s) => {
            return s.playerId[0] == -1 || s.playerId[1] == -1 ? 0 : 1;
          });
          return setMap.reduce(function (result, item) {
            return result + item;
          }, 0);
        })
      );

      let size = 32;
      $(":root").css("--player-height", size);

      let containerSize = $(".winners_container").height();
      if (window.LOSERS_ONLY) containerSize = $(".losers_container").height();

      while (
        biggestRound * (2 * parseInt($(":root").css("--player-height")) + 4) >
        containerSize - 20
      ) {
        size -= 1;
        $(":root").css("--player-height", size);
      }
      $(":root").css("--name-size", Math.min(size - size * 0.3, 24));
      $(":root").css("--score-size", size - size * 0.25);
      $(":root").css("--flag-height", size - size * 0.4);

      if (
        !oldData.bracket ||
        Object.keys(oldData.bracket.players).length !=
          Object.keys(data.bracket.players).length ||
        progressionsIn != _.get(oldData, "bracket.bracket.progressionsIn") ||
        progressionsOut != _.get(oldData, "bracket.bracket.progressionsOut") ||
        Object.keys(oldData.bracket.bracket.rounds).length !=
          Object.keys(data.bracket.bracket.rounds).length ||
        _.get(oldData, "bracket.phase") != _.get(data, "bracket.phase") ||
        _.get(oldData, "bracket.phaseGroup") !=
          _.get(data, "bracket.phaseGroup")
      ) {
        // WINNERS SIDE
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

        let losersRounds = Object.fromEntries(
          Object.entries(bracket).filter(([round]) => parseInt(round) < 0)
        );

        // LOSERS SIDE
        if (!window.WINNERS_ONLY) {
          html = "";

          Object.entries(losersRounds).forEach(([roundKey, round], r) => {
            html += `<div class="round round_${roundKey}">`;
            html += `<div class="round_name"></div>`;
            Object.values(round.sets).forEach((slot, i) => {
              html += `<div class="slot slot_${i + 1}">`;
              Object.values(slot.playerId).forEach((playerId, p) => {
                html += `
                  <div class="slot_p_${p} player container">
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
        }

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
                if (window.WINNERS_ONLY && parseInt(roundKey) < 0) return;
                if (window.LOSERS_ONLY && parseInt(roundKey) > 0) return;

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
                  slotLines += `<path class="${
                    this.baseClass
                  } line_r_${roundKey} s_${i + 1}" d="
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
                      winElement.offset().top + winElement.outerHeight() / 2,
                    ],
                    [
                      winElement.offset().left,
                      winElement.offset().top + winElement.outerHeight() / 2,
                    ],
                  ]
                    .map((point) => point.join(" "))
                    .map((point) => "L" + point)
                    .join(" ")}"
                  stroke="black" fill="none" stroke-width="5" />`;
                }

                // Lines for progressions in
                if (
                  progressionsIn > 0 &&
                  ((parseInt(roundKey) > 0 && parseInt(roundKey) == 1) ||
                    (parseInt(roundKey) < 0 &&
                      Math.abs(parseInt(roundKey)) == 1 &&
                      !winnersOnlyProgressions))
                ) {
                  slotLines += `<path class="${this.baseClass} line_in_r_${
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
                  stroke="black" fill="none" stroke-width="5" />`;
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
                  slotLines += `<path class="${
                    this.baseClass
                  } line_out_r_${roundKey} s_${i + 1}" d="
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
                    slotElement.offset().left + slotElement.outerWidth() + 35,
                    slotElement.offset().top +
                      slotElement.outerHeight() / 2 -
                      8,
                  ].join(" ")}
                  ${[
                    [
                      slotElement.offset().left + slotElement.outerWidth() + 45,
                      slotElement.offset().top + slotElement.outerHeight() / 2,
                    ],
                    [
                      slotElement.offset().left + slotElement.outerWidth() + 35,
                      slotElement.offset().top +
                        slotElement.outerHeight() / 2 +
                        8,
                    ],
                  ]
                    .map((point) => point.join(" "))
                    .map((point) => "L" + point)
                    .join(" ")}"
                  stroke="black" fill="none" stroke-width="5"  />`;
                }
              }
            },
            { baseClass: baseClass }
          );
        });

        $(".lines").html(slotLines);

        // ANIMATIONS
        animations = {};

        entryAnim = gsap.timeline();

        let GfResetRoundNum = Math.max.apply(
          null,
          Object.keys(bracket).map((r) => parseInt(r))
        );

        Object.entries(bracket).forEach(function ([roundKey, round], r) {
          animations[roundKey] = {};
          Object.values(round.sets).forEach((set, setIndex) => {
            let isGfR = parseInt(roundKey) == GfResetRoundNum;

            let anim = gsap.timeline();

            anim.addLabel("hidden");

            anim.add(
              AnimateLine($(`.line_in_r_${roundKey}.s_${setIndex + 1}`)),
              0
            );

            if (isGfR && progressionsOut == 0) {
              anim.from(
                $(`.round_${roundKey} .round_name`),
                { autoAlpha: 0, duration: 0.4 },
                0.5
              );
            }

            anim.from(
              $(`.round_${roundKey} .slot_${setIndex + 1}`),
              { x: -50, autoAlpha: 0, duration: 0.4 },
              0.5
            );

            anim.addLabel("displayed");

            anim.add(
              AnimateLine($(`.line_r_${roundKey}.s_${setIndex + 1}`)),
              0.9
            );
            anim.add(
              AnimateLine($(`.line_out_r_${roundKey}.s_${setIndex + 1}`)),
              1.4
            );

            anim.addLabel("over");

            animations[roundKey][setIndex] = anim;
            anim.pause();

            entryAnim.add(
              AnimateElement(roundKey, setIndex, set, bracket, progressionsOut),
              Math.abs(parseInt(roundKey)) * 0.6
            );
          });
        });

        entryAnim.play(0);
      }

      // TRIGGER ANIMATIONS
      if (entryAnim && entryAnim.progress() >= 1) {
        Object.entries(bracket).forEach(function ([roundKey, round], r) {
          Object.values(round.sets).forEach((set, setIndex) => {
            AnimateElement(roundKey, setIndex, set, bracket, progressionsOut);
          });
        });
      }

      // UPDATE SCORES
      Object.entries(bracket).forEach(function ([roundKey, round], r) {
        if (parseInt(roundKey) < 0) {
          baseClass = "losers_container";
        } else {
          baseClass = "winners_container";
        }

        SetInnerHtml(
          $(`.${baseClass} .round_${parseInt(roundKey)} .round_name`),
          round.name
        );

        Object.values(round.sets).forEach(function (slot, i) {
          Object.values(slot.score).forEach(
            function (score, p) {
              SetInnerHtml(
                $(
                  `.${this.baseClass} .round_${parseInt(roundKey)} .slot_${
                    i + 1
                  } .slot_p_${p}.container .score`
                ),
                `
                  ${slot.completed ? (score == -1 ? "DQ" : score) : ""}
                `
              );
            },
            { baseClass: baseClass }
          );
          if (slot.score[0] > slot.score[1] && slot.completed) {
            $(
              `.${this.baseClass} .round_${parseInt(roundKey)} .slot_${
                i + 1
              } .slot_p_${0}.container`
            ).css("filter", "brightness(1)");
            $(
              `.${this.baseClass} .round_${parseInt(roundKey)} .slot_${
                i + 1
              } .slot_p_${1}.container`
            ).css("filter", "brightness(0.6)");
          } else if (slot.score[1] > slot.score[0] && slot.completed) {
            $(
              `.${this.baseClass} .round_${parseInt(roundKey)} .slot_${
                i + 1
              } .slot_p_${0}.container`
            ).css("filter", "brightness(0.6)");
            $(
              `.${this.baseClass} .round_${parseInt(roundKey)} .slot_${
                i + 1
              } .slot_p_${1}.container`
            ).css("filter", "brightness(1)");
          } else {
            $(
              `.${this.baseClass} .round_${parseInt(roundKey)} .slot_${
                i + 1
              } .slot_p_${0}.container`
            ).css("filter", "brightness(1)");
            $(
              `.${this.baseClass} .round_${parseInt(roundKey)} .slot_${
                i + 1
              } .slot_p_${1}.container`
            ).css("filter", "brightness(1)");
          }
        });
      });

      // UPDATE PLAYER DATA
      for (const [roundKey, round] of Object.entries(bracket)) {
        for (const [setIndex, set] of Object.entries(round.sets)) {
          for (const [index, pid] of set.playerId.entries()) {
            let element = $(
              `.round_${roundKey} .slot_${
                parseInt(setIndex) + 1
              } .slot_p_${index}`
            ).get(0);

            if (!element) continue;

            let team = players[pid];

            if (!team) {
              SetInnerHtml($(element).find(`.name`), "");
              SetInnerHtml($(element).find(`.flagcountry`), "");
              SetInnerHtml($(element).find(`.flagstate`), "");
              SetInnerHtml($(element).find(`.character_container`), "");
              SetInnerHtml($(element).find(`.sponsor_icon`), "");
              SetInnerHtml($(element).find(`.avatar`), "");
              SetInnerHtml($(element).find(`.online_avatar`), "");
              SetInnerHtml($(element).find(`.twitter`), "");
              SetInnerHtml($(element).find(`.sponsor-container`), "");

              continue;
            }

            if (Object.values(team.player).length == 1) {
              // Singles
              let player = null;

              if (players[pid]) player = players[pid].player["1"];

              SetInnerHtml(
                $(element).find(`.name`),
                `
                  <span>
                    <span class="sponsor">
                      ${player && player.team ? player.team : ""}
                    </span>
                    ${player ? await Transcript(player.name) : ""}
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

              await CharacterDisplay(
                $(element).find(`.character_container`),
                {
                  source: `bracket.players.slot.${pid}`,
                },
                event
              );

              SetInnerHtml(
                $(element).find(`.sponsor_icon`),
                player && player.sponsor_logo
                  ? `<div style='background-image: url(../../${player.sponsor_logo})'></div>`
                  : ""
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
                  ? `<span class="twitter_logo"></span>${String(
                      player.twitter
                    )}`
                  : ""
              );

              SetInnerHtml(
                $(element).find(`.sponsor-container`),
                `<div class='sponsor-logo' style='background-image: url(../../${
                  player ? player.sponsor_logo : ""
                })'></div>`
              );
            } else {
              // Doubles/Teams
              let teamName = team.name;

              if (!teamName || teamName == "") {
                let names = [];
                for (const [p, player] of Object.values(
                  team.player
                ).entries()) {
                  if (player) {
                    names.push(await Transcript(player.name));
                  }
                }
                teamName = names.join(" / ");
              }

              SetInnerHtml(
                $(element).find(`.name`),
                `
                  <span>
                    ${teamName}
                  </span>
                `
              );

              SetInnerHtml($(element).find(`.flagcountry`), "");
              SetInnerHtml($(element).find(`.flagstate`), "");

              await CharacterDisplay(
                $(element).find(`.character_container`),
                {
                  slice_character: [0, 1],
                  source: `bracket.players.slot.${pid}`,
                },
                event
              );

              SetInnerHtml($(element).find(`.sponsor_icon`), "");
              SetInnerHtml($(element).find(`.avatar`), "");
              SetInnerHtml($(element).find(`.online_avatar`), "");
              SetInnerHtml($(element).find(`.twitter`), "");
              SetInnerHtml($(element).find(`.sponsor-container`), "");
            }
          }
        }
      }

      SetInnerHtml($(`.tournament_name`), data.tournamentInfo.tournamentName);
      SetInnerHtml($(`.event_name`), data.tournamentInfo.eventName);
      SetInnerHtml($(`.bracket_name`), data.bracket.phase);
      SetInnerHtml($(`.pool_name`), data.bracket.phaseGroup);
    }
  };
});
