LoadEverything().then(() => {
  var MIDDLE_SPACE = 100;
  if (!window.USE_ONLINE_PICTURE) {
    window.USE_ONLINE_PICTURE = false;
  }
  var firstUpdate = true;

  gsap.config({ nullTargetWarn: false, trialWarn: false });

  let startingAnimation = gsap.timeline({ paused: true });

  Start = async (event) => {
    startingAnimation.restart();
  };

  var entryAnim = gsap.timeline({ paused: true });
  var animations = {};

  // Animations for the icons and lines
  // All animations include the whole path as if the player won
  // But we add labels as checkpoints for each round
  // So we get where the player is last seen in bracket and animate to that point
  var iconAnimationsW = [];
  var iconAnimationsL = [];

  // Animation for when a player loses
  // (makes slot, lines, and icon darker)
  var playerLoseAnimW = [];
  var playerLoseAnimL = [];

  var players = [];
  var bracket = {};

  var allWinners = false;

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
          "stroke-linecap": "butt",
          opacity: 0,
          onUpdate: function (tl) {
            let tlp = (this.progress() * 100) >> 0;
            if (element) {
              let length = element.getTotalLength();
              TweenMax.set(element, {
                "stroke-dashoffset": (length / 100) * (100 - tlp),
                "stroke-dasharray": length,
                "stroke-linecap": tlp == 0 ? "butt" : "square",
                opacity: tlp == 0 ? 0 : 1,
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

  /**
   * @param {string} _class
   * @param {Array} points
   */
  function GetBracketLineHtml(_class, points, color, hidden = false) {
    let newPoints = [];

    newPoints.push(points[0]);
    newPoints.push([points[1][0], points[0][1]]);
    newPoints.push(points[1]);

    let line = `<path class="${_class}" d="
    M${[newPoints[0][0], newPoints[0][1]].join(" ")}
    ${newPoints
      .slice(1)
      .map((point) => point.join(" "))
      .map((point) => "L" + point)
      .join(" ")}"
    stroke="${color}" fill="none" stroke-width="8" stroke-linecap="square" ${
      hidden ? 'style="opacity: 0"' : ""
    } />`;

    return line;
  }

  /**
   * @param {string} _class
   * @param {Array} points
   */
  function GetLineHtml(_class, points, color, hidden = false) {
    let line = `<path class="${_class}" d="
    M${points[0].join(" ")}
    ${points
      .slice(1)
      .map((point) => point.join(" "))
      .map((point) => "L" + point)
      .join(" ")}"
    stroke="${color}" fill="none" stroke-width="8" stroke-linecap="square" ${
      hidden ? 'style="opacity: 0"' : ""
    } />`;

    return line;
  }

  Update = async (event) => {
    let data = event.data;
    let oldData = event.oldData;

    if (
      !oldData.bracket ||
      JSON.stringify(data.bracket.bracket) !=
        JSON.stringify(oldData.bracket.bracket)
    ) {
      bracket = data.bracket.bracket.rounds;
      players = data.bracket.players.slot;

      let progressionsOut = data.bracket.bracket.progressionsOut;
      let progressionsIn = data.bracket.bracket.progressionsIn;
      let winnersOnlyProgressions =
        data.bracket.bracket.winnersOnlyProgressions;

      if (winnersOnlyProgressions === undefined) winnersOnlyProgressions = true;

      let biggestRound = Math.max.apply(
        null,
        Object.values(bracket).map((r) => Object.keys(r.sets).length)
      );

      let size = 32;
      $(":root").css("--player-height", size);

      while (
        biggestRound * (2 * parseInt($(":root").css("--player-height")) + 2) >
        $(".winners_container").height() - 92
      ) {
        size -= 1;
        $(":root").css("--player-height", size);
      }
      $(":root").css("--name-size", Math.min(size - size * 0.3, 16));
      $(":root").css("--score-size", size - size * 0.3);
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

        // LOSERS SIDE
        html = "";

        let losersRounds = Object.fromEntries(
          Object.entries(bracket).filter(([round]) => parseInt(round) < 0)
        );

        allWinners =
          Object.keys(Object.values(winnersRounds)[0].sets).length >=
          Object.values(players).length / 2;

        if (winnersOnlyProgressions) allWinners = true;

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
            html += `<div class="round round_base_l ${
              !allWinners ? "complete" : ""
            }">`;
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
                    ${
                      !allWinners
                        ? `
                      <div class="sponsor_icon"></div>
                      <div class="flags">
                        <div class="flagcountry"></div>
                        <div class="flagstate"></div>
                      </div>
                      <div class="icon avatar"></div>
                      <div class="icon online_avatar"></div>
                    `
                        : ""
                    }
                  </div>
                `;
              });
            });
            html += "</div>";
          });

        $(".losers_container").html(html);

        // Center area
        html = "";

        html += `<div class="round round_${
          Object.keys(winnersRounds).reverse()[1]
        }">`;
        html += `<div class="round_name"></div>`;
        html += `<div class="slot_1" style="width: 32px; height: 32px; align-self: center;"></div>`;
        html += "</div>";

        $(".center_container").html(html);

        // ICONS
        // Winners side: one icon per player
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

        // Losers side: one icon per slot considering a power2 sized bracket
        html = "";

        let size = nextPow2(Object.entries(players).length);

        for (let t = 0; t < size; t += 1) {
          html += `
            <div class="bracket_icon bracket_icon_p${t + 1}">
              <div class="icon_name_arrow">
                <div class="icon_name"></div>
                <div class="icon_arrow_border"></div>
                <div class="icon_arrow"></div>
              </div>
              <div class="icon_image"></div>
            </div>`;
        }

        $(".losers_icons").html(html);

        // BRACKET LINES
        // .line_r_(round) = Line going from (round) set to the next set
        let slotLines = "";
        let slotLinesW = "";

        let baseClass = "winners_container";

        Object.entries(bracket).forEach(function ([roundKey, round], r) {
          if (parseInt(roundKey) < 0) {
            baseClass = "losers_container";
          } else {
            baseClass = "winners_container";
          }

          Object.values(round.sets).forEach(
            function (set, setIndex) {
              let lastLosers =
                parseInt(roundKey) ==
                Math.min.apply(
                  null,
                  Object.keys(bracket).map((r) => parseInt(r))
                );

              if (
                set.nextWin &&
                !(
                  set.playerId[0] > Object.keys(players).length ||
                  set.playerId[1] > Object.keys(players).length
                )
              ) {
                let slotElement = $(
                  `.${this.baseClass} .round_${roundKey} .slot_${setIndex + 1}`
                );

                if (!slotElement || !slotElement.offset()) return;

                let winElement = $(
                  `.${this.baseClass} .round_${set.nextWin[0]} .slot_${
                    set.nextWin[1] + 1
                  }`
                );

                if (!winElement.get(0)) {
                  winElement = $(`.center_container .slot_${1}`);
                }

                // Initial line from base
                if (roundKey == "1" || roundKey == "-1") {
                  [0, 1].forEach((index) => {
                    let className =
                      roundKey == "1" ? "round_base_w" : "round_base_l";

                    let baseElement = $(
                      `.${this.baseClass} .${className} .slot_${
                        setIndex + 1
                      }.slot_p_${index}`
                    );

                    let points = [
                      [
                        baseElement.offset().left +
                          baseElement.outerWidth() / 2,
                        baseElement.offset().top +
                          baseElement.outerHeight() / 2,
                      ],
                      [
                        slotElement.offset().left +
                          slotElement.outerWidth() / 2,
                        slotElement.offset().top +
                          slotElement.outerHeight() / 2,
                      ],
                    ];

                    slotLines += GetBracketLineHtml(
                      `${this.baseClass} line_base_r_${roundKey} s_${
                        setIndex + 1
                      } p_${index}`,
                      points,
                      "gray"
                    );

                    slotLinesW += GetLineHtml(
                      `${this.baseClass} line_base_r_${roundKey} s_${
                        setIndex + 1
                      } p_${index} base`,
                      [points[0], [points[1][0], points[0][1]]],
                      "yellow",
                      true
                    );

                    slotLinesW += GetLineHtml(
                      `${this.baseClass} line_base_r_${roundKey} s_${
                        setIndex + 1
                      } p_${index} win`,
                      [[points[1][0], points[0][1]], points[1]],
                      "yellow",
                      true
                    );
                  });
                }

                // Winners side lines
                if (
                  winElement &&
                  winElement.offset() &&
                  parseInt(roundKey) > 0
                ) {
                  let points = [
                    [
                      slotElement.offset().left + slotElement.outerWidth() / 2,
                      slotElement.offset().top + slotElement.outerHeight() / 2,
                    ],
                    [
                      winElement.offset().left + winElement.outerWidth() / 2,
                      winElement.offset().top + winElement.outerHeight() / 2,
                    ],
                  ];

                  // For last round, we don't want the lines to merge so we add a spacing
                  if (
                    parseInt(roundKey) ==
                    parseInt(Object.keys(winnersRounds).reverse()[2])
                  ) {
                    points[1][0] -= MIDDLE_SPACE;
                  }

                  slotLines += GetBracketLineHtml(
                    `${this.baseClass} line_r_${roundKey} s_${setIndex + 1}`,
                    points,
                    "gray"
                  );

                  slotLinesW += GetBracketLineHtml(
                    `${this.baseClass} line_r_${parseInt(roundKey) + 1} s_${
                      setIndex + 1
                    } base`,
                    [points[0], [points[1][0], points[0][1]]],
                    "yellow",
                    true
                  );

                  slotLinesW += GetBracketLineHtml(
                    `${this.baseClass} line_r_${parseInt(roundKey) + 1} s_${
                      setIndex + 1
                    } win`,
                    [[points[1][0], points[0][1]], points[1]],
                    "yellow",
                    true
                  );
                }

                // Losers side lines
                if (parseInt(roundKey) < 0) {
                  if (
                    (parseInt(roundKey) % 2 == -1 &&
                      Object.keys(losersRounds).length % 2 == 0) ||
                    (parseInt(roundKey) % 2 == 0 &&
                      Object.keys(losersRounds).length % 2 == 1)
                  ) {
                    let hangingElement = $(
                      `.${this.baseClass} .round_${roundKey} .slot_hanging_${
                        setIndex + 1
                      }`
                    );

                    if (
                      winElement &&
                      winElement.offset() &&
                      hangingElement &&
                      hangingElement.offset()
                    ) {
                      let points = [
                        [
                          hangingElement.offset().left +
                            hangingElement.outerWidth() / 2,
                          hangingElement.offset().top +
                            hangingElement.outerHeight() / 2,
                        ],
                        [
                          winElement.offset().left +
                            winElement.outerWidth() / 2,
                          winElement.offset().top +
                            winElement.outerHeight() / 2,
                        ],
                      ];

                      slotLines += GetBracketLineHtml(
                        `${this.baseClass} line_r_${roundKey} s_${
                          setIndex + 1
                        }`,
                        points,
                        "gray"
                      );

                      slotLinesW += GetBracketLineHtml(
                        `${this.baseClass} line_r_${parseInt(roundKey) - 1} s_${
                          setIndex + 1
                        } p_${0} base`,
                        [points[0], [points[1][0], points[0][1]]],
                        "yellow",
                        true
                      );

                      slotLinesW += GetBracketLineHtml(
                        `${this.baseClass} line_r_${parseInt(roundKey) - 1} s_${
                          setIndex + 1
                        } p_${0} win`,
                        [[points[1][0], points[0][1]], points[1]],
                        "yellow",
                        true
                      );
                    }
                  }
                  if (winElement && winElement.offset()) {
                    let points = [
                      [
                        slotElement.offset().left +
                          slotElement.outerWidth() / 2,
                        slotElement.offset().top +
                          slotElement.outerHeight() / 2,
                      ],
                      [
                        winElement.offset().left + winElement.outerWidth() / 2,
                        winElement.offset().top + winElement.outerHeight() / 2,
                      ],
                    ];

                    // For last round, we don't want the lines to merge so we add a spacing
                    if (
                      parseInt(roundKey) ==
                      parseInt(Object.keys(losersRounds).reverse()[0])
                    ) {
                      points[1][0] += MIDDLE_SPACE;
                    }

                    slotLines += GetBracketLineHtml(
                      `${this.baseClass} line_r_${roundKey} s_${setIndex + 1}`,
                      points,
                      "gray"
                    );

                    // Which set index to assign?
                    let s = 0;
                    if (
                      (parseInt(roundKey) % 2 == -1 &&
                        Object.keys(losersRounds).length % 2 == 0) ||
                      (parseInt(roundKey) % 2 == 0 &&
                        Object.keys(losersRounds).length % 2 == 1)
                    ) {
                      // Next round has the same amount of sets, so just use the current index
                      s = setIndex + 1;
                    } else {
                      // Next round has half the number of sets, so we divide setIndex by 2
                      s = Math.floor(setIndex / 2) + 1;
                    }

                    // Which player slot to assign?
                    let p = 0;
                    if (
                      (parseInt(roundKey) % 2 == -1 &&
                        Object.keys(losersRounds).length % 2 == 0) ||
                      (parseInt(roundKey) % 2 == 0 &&
                        Object.keys(losersRounds).length % 2 == 1)
                    ) {
                      // If in an odd round, it's always 1 because slot 0 is a hanging slot
                      // (a player that came from winners as slot 0 vs this one as slot 1)
                      p = 1;
                    } else {
                      // Just alternate between 0 and 1
                      p = parseInt(setIndex) % 2 == 0 ? 0 : 1;
                    }

                    slotLinesW += GetBracketLineHtml(
                      `${this.baseClass} line_r_${
                        parseInt(roundKey) - 1
                      } s_${s} p_${p} base`,
                      [points[0], [points[1][0], points[0][1]]],
                      "yellow",
                      true
                    );

                    slotLinesW += GetBracketLineHtml(
                      `${this.baseClass} line_r_${
                        parseInt(roundKey) - 1
                      } s_${s} p_${p} win`,
                      [[points[1][0], points[0][1]], points[1]],
                      "yellow",
                      true
                    );
                  }
                }
              }
            },
            { baseClass: baseClass }
          );
        });

        $(".lines.base").html(slotLines);
        $(".lines.win").html(slotLinesW);

        // ICON ANIMATIONS
        // For each player
        Object.entries(players).forEach(([teamId, team], t) => {
          Object.entries(team.player).forEach(([playerId, player], p) => {
            // Winners path
            let icon_element = $(
              `.winners_icons .bracket_icon.bracket_icon_p${teamId}`
            );
            if (!icon_element) return;

            let icon_anim = gsap.timeline({ paused: true });
            let icon_lose_anim = gsap.timeline({ paused: true });
            let prevSlot = null;

            icon_lose_anim.fromTo(
              $(icon_element),
              { filter: "brightness(1)" },
              {
                duration: 0.5,
                filter: "brightness(0.7)",
              },
              0
            );

            // We follow the bracket and add the positions the player appeared
            // to the animation
            Object.entries(winnersRounds)
              .slice(0, -1)
              .forEach(([roundKey, round], r) => {
                Object.values(round.sets).forEach((slot, i) => {
                  Object.values(slot.playerId).forEach(
                    (slotPlayerId, slotIndex) => {
                      if (
                        (roundKey == "1" && slotPlayerId == teamId) ||
                        (prevSlot &&
                          prevSlot.nextWin &&
                          prevSlot.nextWin[0] == parseInt(roundKey) &&
                          prevSlot.nextWin[1] == i &&
                          slotIndex == prevSlot.winSlot)
                      ) {
                        prevSlot = slot;

                        if (roundKey == "1") {
                          let setElement = $(
                            `.round_base_w .slot_${i + 1}.slot_p_${slotIndex}`
                          );

                          icon_lose_anim.fromTo(
                            $(setElement),
                            { filter: "brightness(1)" },
                            {
                              duration: 0.5,
                              filter: "brightness(0.7)",
                            },
                            0
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
                            icon_anim.addLabel("start");
                          }

                          icon_anim.add(
                            AnimateLine(
                              $(
                                `.lines.win .winners_container.line_base_r_${roundKey}.s_${
                                  i + 1
                                }.p_${slotIndex}.base`
                              )
                            ),
                            ">"
                          );
                        }

                        let setElement = $(`.round_${roundKey} .slot_${i + 1}`);

                        icon_anim.add(
                          AnimateLine(
                            $(
                              `.lines.win .winners_container.line_r_${roundKey}.s_${
                                2 * i + 1 + slotIndex
                              }.base`
                            )
                          ),
                          ">"
                        );

                        if (setElement && setElement.offset()) {
                          icon_anim.to(
                            $(icon_element),
                            {
                              x:
                                roundKey !=
                                Object.keys(winnersRounds).reverse()[1]
                                  ? setElement.offset().left
                                  : setElement.offset().left - MIDDLE_SPACE,
                              duration: 0.4,
                            },
                            "<"
                          );

                          icon_anim.addLabel(`round_${roundKey}`, "<+=0.4");

                          // Animation if won
                          if (roundKey == "1") {
                            icon_anim.add(
                              AnimateLine(
                                $(
                                  `.lines.win .winners_container.line_base_r_${roundKey}.s_${
                                    i + 1
                                  }.p_${slotIndex}.win`
                                )
                              ),
                              ">"
                            );
                          } else {
                            icon_anim.add(
                              AnimateLine(
                                $(
                                  `.lines.win .winners_container.line_r_${roundKey}.s_${
                                    2 * i + 1 + slotIndex
                                  }.win`
                                )
                              ),
                              ">"
                            );
                          }
                          icon_anim.to(
                            $(icon_element),
                            {
                              x:
                                roundKey !=
                                Object.keys(winnersRounds).reverse()[1]
                                  ? setElement.offset().left
                                  : setElement.offset().left - MIDDLE_SPACE,
                              y: setElement.offset().top,
                              duration: 0.4,
                            },
                            "<"
                          );
                        }
                      }
                    }
                  );
                });
              });

            iconAnimationsW.push(icon_anim);
            playerLoseAnimW.push(icon_lose_anim);
          });
        });
        for (let t = 0; t < size; t += 1) {
          // Losers path
          icon_element = $(
            `.losers_icons .bracket_icon.bracket_icon_p${t + 1}`
          );
          if (!icon_element) continue;

          icon_anim = gsap.timeline({ paused: true });
          icon_lose_anim = gsap.timeline({ paused: true });
          prevSlot = null;

          icon_lose_anim.fromTo(
            $(icon_element),
            { filter: "brightness(1)" },
            {
              duration: 0.5,
              filter: "brightness(0.7)",
            },
            0
          );

          let appearRounds = [];

          if (Object.keys(losersRounds).length % 2 == 0 && !allWinners) {
            Object.values(bracket["-1"].sets).forEach((set, index) => {
              appearRounds.push([-1, index, 0]);
              appearRounds.push([-1, index, 1]);
            });
          }

          Object.entries(winnersRounds).forEach(([roundKey, round], r) => {
            Object.values(round.sets).forEach((set, s) => {
              if (set.nextLose) {
                appearRounds.push([
                  set.nextLose[0],
                  set.nextLose[1],
                  set.loseSlot,
                ]);
              }
            });
          });

          let found = false;

          Object.entries(losersRounds).forEach(([roundKey, round], r) => {
            Object.values(round.sets).forEach((slot, i) => {
              Object.values(slot.playerId).forEach(
                (slotPlayerId, slotIndex) => {
                  if (
                    (prevSlot &&
                      prevSlot.nextWin &&
                      prevSlot.nextWin[0] == parseInt(roundKey) &&
                      prevSlot.nextWin[1] == i &&
                      slotIndex == prevSlot.winSlot) ||
                    (appearRounds[t] &&
                      parseInt(roundKey) == appearRounds[t][0] &&
                      i == appearRounds[t][1] &&
                      slotIndex == appearRounds[t][2] &&
                      !found)
                  ) {
                    prevSlot = slot;

                    if (roundKey == "-1") {
                      let setElement = $(
                        `.round_base_l .slot_${i + 1}.slot_p_${slotIndex}`
                      );

                      if (setElement && setElement.offset()) {
                        gsap.set($(icon_element), {
                          x:
                            setElement.offset().left -
                            ($(icon_element).outerWidth() * 3) / 4,
                          y:
                            setElement.offset().top +
                            setElement.outerHeight() / 2 -
                            $(icon_element).outerHeight() / 2,
                        });

                        icon_lose_anim.fromTo(
                          $(setElement),
                          { filter: "brightness(1)" },
                          {
                            duration: 0.5,
                            filter: "brightness(0.7)",
                          },
                          0
                        );
                      }

                      icon_anim.add(
                        AnimateLine(
                          $(
                            `.lines.win .losers_container.line_base_r_${roundKey}.s_${
                              i + 1
                            }.p_${slotIndex}.base`
                          )
                        ),
                        "<"
                      );

                      // icon_anim.addLabel(`round_${roundKey}`);
                    } else if (!found) {
                      let setElement = $(
                        `.round_${parseInt(roundKey) + 1} .slot_hanging_${
                          i + 1
                        }`
                      );

                      if (setElement && setElement.offset()) {
                        gsap.set($(icon_element), {
                          x:
                            setElement.offset().left -
                            ($(icon_element).outerWidth() * 3) / 4,
                          y:
                            setElement.offset().top +
                            setElement.outerHeight() / 2 -
                            $(icon_element).outerHeight() / 2,
                        });

                        icon_lose_anim.fromTo(
                          $(setElement),
                          { filter: "brightness(1)" },
                          {
                            duration: 0.5,
                            filter: "brightness(0.7)",
                          },
                          0
                        );
                      }
                      icon_anim.addLabel(`start`);

                      icon_anim.add(
                        AnimateLine(
                          $(
                            `.lines.win .losers_container.line_r_${parseInt(
                              roundKey
                            )}.s_${i + 1}.p_${slotIndex}.base`
                          ),
                          "<"
                        )
                      );

                      // icon_anim.addLabel(`round_${parseInt(roundKey)}`);
                    }

                    let setElement = $(`.round_${roundKey} .slot_${i + 1}`);

                    icon_anim.add(
                      AnimateLine(
                        $(
                          `.lines.win .losers_container.line_r_${roundKey}.s_${
                            i + 1
                          }.p_${slotIndex}.base`
                        )
                      ),
                      ">"
                    );

                    if (setElement && setElement.offset()) {
                      icon_anim.to(
                        $(icon_element),
                        {
                          x: setElement.offset().left,
                          duration: 0.4,
                        },
                        "<"
                      );

                      icon_anim.addLabel(`round_${roundKey}`);

                      // Animation if won
                      if (roundKey == "-1") {
                        icon_anim.add(
                          AnimateLine(
                            $(
                              `.lines.win .losers_container.line_base_r_${-1}.s_${
                                i + 1
                              }.p_${slotIndex}.win`
                            )
                          ),
                          ">"
                        );
                      } else {
                        icon_anim.add(
                          AnimateLine(
                            $(
                              `.lines.win .losers_container.line_r_${roundKey}.s_${
                                i + 1
                              }.p_${slotIndex}.win`
                            )
                          ),
                          ">"
                        );
                      }
                      icon_anim.to(
                        $(icon_element),
                        {
                          x: setElement.offset().left,
                          y: setElement.offset().top,
                          duration: 0.4,
                        },
                        "<"
                      );
                    }

                    found = true;
                  }
                }
              );
            });
          });

          // Add animations for GF and GF Reset
          let GfResetRoundNum = Math.max.apply(
            null,
            Object.keys(bracket).map((r) => parseInt(r))
          );

          let lastLosersRoundNum = Math.min.apply(
            null,
            Object.keys(bracket).map((r) => parseInt(r))
          );

          [GfResetRoundNum - 1].forEach((roundNum, index) => {
            icon_anim.add(
              AnimateLine(
                $(
                  `.lines.win .losers_container.line_r_${
                    lastLosersRoundNum - index - 1
                  }.s_${1}.base`
                )
              ),
              ">"
            );

            let setElement = $(`.round_${roundNum} .slot_${1}`);

            if (setElement.get(0)) {
              icon_anim.to(
                $(icon_element),
                {
                  x: setElement.offset().left + MIDDLE_SPACE,
                  duration: 0.4,
                },
                "<"
              );
            }

            icon_anim.addLabel(`round_${lastLosersRoundNum - index - 1}`);

            // Animation if won
            icon_anim.add(
              AnimateLine(
                $(
                  `.lines.win .losers_container.line_r_${
                    lastLosersRoundNum - index - 1
                  }.s_${1}.win`
                )
              ),
              ">"
            );

            if (setElement.get(0)) {
              icon_anim.to(
                $(icon_element),
                {
                  x: setElement.offset().left + MIDDLE_SPACE,
                  y: setElement.offset().top,
                  duration: 0.4,
                },
                "<"
              );
            }
          });

          iconAnimationsL.push(icon_anim);
          playerLoseAnimL.push(icon_lose_anim);
        }
      }

      let GfResetRoundNum = Math.max.apply(
        null,
        Object.keys(bracket).map((r) => parseInt(r))
      );

      let gf = bracket[GfResetRoundNum - 1].sets[0];
      let isReset = gf.score[0] < gf.score[1];

      // UPDATE ROUND NAMES
      Object.entries(bracket).forEach(function ([roundKey, round], r) {
        let roundName = round.name;

        if (parseInt(roundKey) < 0) {
          roundName = roundName
            .split(/ |-/)
            .map((n) => n[0])
            .join("");
        }

        SetInnerHtml($(`.round_${parseInt(roundKey)} .round_name`), roundName);
      });

      // UPDATE PLAYER DATA
      for (const [roundKey, round] of Object.entries(bracket)) {
        for (const [setIndex, set] of Object.entries(round.sets)) {
          for (const [index, pid] of set.playerId.entries()) {
            if (parseInt(roundKey) > 0 && roundKey != "1") continue;

            let element = null;

            if (parseInt(roundKey) > 0) {
              element = $(
                `.round_base_w .slot_${parseInt(setIndex) + 1}.slot_p_${index}`
              ).get(0);
            } else {
              if (roundKey == "-1") {
                element = $(
                  `.round_base_l .slot_${
                    parseInt(setIndex) + 1
                  }.slot_p_${index}`
                ).get(0);
              } else {
                element = $(
                  `.round_${parseInt(roundKey) + 1} .slot_hanging_${
                    parseInt(setIndex) + 1
                  }.slot_p_${index}`
                ).get(0);
              }
            }

            if (!element) continue;

            let player = null;

            if (players[pid]) player = players[pid].player["1"];

            SetInnerHtml(
              $(element).find(`.name`),
              `
                <span>
                  <span class="sponsor">
                    ${
                      player &&
                      player.team &&
                      (parseInt(roundKey) > 0 ||
                        (!allWinners && roundKey == "-1"))
                        ? player.team
                        : ""
                    }
                  </span>
                  ${player ? await Transcript(player.name) : "---"}
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
          }
        }
      }

      // UPDATE ICONS
      for (const [teamId, team] of Object.entries(players)) {
        for (const [playerId, player] of Object.entries(team.player)) {
          let element = $(
            `.winners_icons .bracket_icon.bracket_icon_p${teamId}`
          );
          if (!element) continue;

          SetInnerHtml(
            $(element).find(`.icon_name`),
            `
            <span>
              ${player ? await Transcript(player.name) : ""}
            </span>
          `
          );

          if (!USE_ONLINE_PICTURE) {
            await CharacterDisplay(
              $(element).find(`.icon_image`),
              {
                load_settings_path: "icon",
                slice_character: [0, 1],
                source: `bracket.players.slot.${teamId}`,
              },
              event
            );
          } else {
            SetInnerHtml(
              $(element).find(".icon_image"),
              player && player.online_avatar
                ? `<div class="floating_online_avatar" style="background-image: url('${player.online_avatar}')"></div>`
                : '<div style="background: gray; width: 100%; height: 100%; border-radius: 8px;"></div>'
            );
          }

          // TRIGGER ANIMATIONS
          let GfResetRoundNum = Math.max.apply(
            null,
            Object.keys(bracket).map((r) => parseInt(r))
          );

          let lastLosersRoundNum = Math.min.apply(
            null,
            Object.keys(bracket).map((r) => parseInt(r))
          );

          // Winners side - just detect if a player keeps showing up in the following round until they don't
          Object.entries(players).forEach(([teamId, team], t) => {
            let lastFoundRound = 0;

            let lost = false;

            Object.entries(bracket).forEach(function ([roundKey, round], r) {
              // Skip losers rounds
              if (parseInt(roundKey) < 0) return;

              // If we don't find the player in a round, lost = true
              // using this to avoid detecting a player that got into grand finals
              // through losers
              if (lost) return;
              let foundInRound = false;
              Object.values(round.sets).forEach(function (set, setIndex) {
                if (
                  parseInt(roundKey) > parseInt(lastFoundRound) &&
                  (set.playerId[0] == parseInt(teamId) ||
                    set.playerId[1] == parseInt(teamId))
                ) {
                  lastFoundRound = roundKey;
                  foundInRound = true;

                  if (set.completed) {
                    if (
                      set.playerId[0] == parseInt(teamId) &&
                      set.score[0] < set.score[1]
                    ) {
                      lost = true;
                    }
                    if (
                      set.playerId[1] == parseInt(teamId) &&
                      set.score[1] < set.score[0]
                    ) {
                      lost = true;
                    }
                  }
                }
              });
            });

            if (lost) playerLoseAnimW[t].play();
            else playerLoseAnimW[t].reverse();

            if (lastFoundRound >= 1) {
              iconAnimationsW[t].tweenTo(`round_${lastFoundRound}`, {
                delay: firstUpdate ? 0.6 : 0,
              });
            } else {
              iconAnimationsW[t].tweenTo(`start`);
            }
          });

          // Losers side
          let appearRounds = [];

          let losersRounds = Object.fromEntries(
            Object.entries(bracket).filter(([round]) => parseInt(round) < 0)
          );

          if (Object.keys(losersRounds).length % 2 == 0 && !allWinners) {
            Object.values(bracket["-1"].sets).forEach((set, index) => {
              appearRounds.push([-1, index, 0]);
              appearRounds.push([-1, index, 1]);
            });
          }

          Object.entries(bracket).forEach(([roundKey, round], r) => {
            if (
              parseInt(roundKey) < 0 &&
              parseInt(roundKey) != GfResetRoundNum - 1
            )
              return;
            Object.values(round.sets).forEach((set, s) => {
              if (set.nextLose) {
                appearRounds.push([
                  set.nextLose[0],
                  set.nextLose[1],
                  set.loseSlot,
                ]);
              }
            });
          });

          // Keep track of which icons were animated
          // Because we have to deactivate the rest
          let managedIcons = [];

          // First, we assign players to the "losers slots"
          // Since they appear in losers in an unpredictable order
          // So we assign the player so we can later set their name, icon, etc
          for (const [teamId, team] of Object.entries(players)) {
            let lastFoundRound = 0;
            let firstFoundRound = 0;
            let lastFoundSet = null;
            let losersIconId = null;
            let lost = false;

            for (const [roundKey, round] of Object.entries(bracket)) {
              if (
                parseInt(roundKey) > 0 &&
                parseInt(roundKey) < GfResetRoundNum - 1
              )
                continue;
              Object.values(Object.values(round.sets)).forEach(function (
                set,
                setIndex
              ) {
                if (
                  parseInt(roundKey) < parseInt(lastFoundRound) &&
                  (set.playerId[0] == teamId || set.playerId[1] == teamId)
                ) {
                  lastFoundRound = roundKey;
                  lastFoundSet = set;

                  if (!firstFoundRound) firstFoundRound = roundKey;

                  if (losersIconId == null) {
                    appearRounds.forEach((appearRound, i) => {
                      if (
                        parseInt(roundKey) == appearRound[0] &&
                        setIndex == appearRound[1] &&
                        ((set.playerId[0] == teamId && appearRound[2] == 0) ||
                          (set.playerId[1] == teamId && appearRound[2] == 1))
                      ) {
                        if (roundKey == "-1" && allWinners) {
                          if (set.playerId[0] == teamId) {
                            losersIconId = i;
                            return;
                          }
                          if (set.playerId[1] == teamId) {
                            losersIconId = i;
                            return;
                          }
                        } else {
                          losersIconId = i;
                          return;
                        }
                      }
                    });
                  }
                }
              });
            }

            if (lastFoundRound == 0 || losersIconId === null) {
              //if (iconAnimationsL != null && t < iconAnimationsL.length)
              //  iconAnimationsL[t].tweenTo(`start`);
            } else {
              managedIcons.push(losersIconId);

              if (lastFoundSet && lastFoundSet.completed) {
                if (
                  lastFoundSet.playerId[0] == teamId &&
                  lastFoundSet.score[0] <= lastFoundSet.score[1]
                ) {
                  lost = true;
                }
                if (
                  lastFoundSet.playerId[1] == teamId &&
                  lastFoundSet.score[1] <= lastFoundSet.score[0]
                ) {
                  lost = true;
                }
              }

              if (playerLoseAnimL.length > losersIconId) {
                if (lost) playerLoseAnimL[losersIconId].play();
                else playerLoseAnimL[losersIconId].reverse();
              }

              // Get GF and GF Reset
              if (lastFoundRound == lastLosersRoundNum) {
                let gfSet = bracket[GfResetRoundNum - 1].sets[0];

                if (gfSet.playerId[1] == teamId) {
                  lastFoundRound = lastLosersRoundNum - 1;
                }
              }

              if (playerLoseAnimL.length > losersIconId) {
                if (
                  iconAnimationsL[losersIconId].labels.hasOwnProperty(
                    `round_${lastFoundRound}`
                  )
                ) {
                  iconAnimationsL[losersIconId].tweenTo(
                    `round_${lastFoundRound}`,
                    {
                      delay: firstUpdate ? 0.6 * -firstFoundRound : 0,
                    }
                  );
                } else {
                  iconAnimationsL[losersIconId].tweenTo(`start`);
                }
              }

              let element = $(
                `.losers_icons .bracket_icon.bracket_icon_p${losersIconId + 1}`
              );
              if (element.get(0)) {
                let player = team.player["1"];

                SetInnerHtml(
                  $(element).find(`.icon_name`),
                  `
                  <span>
                    ${player ? await Transcript(player.name) : ""}
                  </span>
                `
                );

                gsap.to($(element), { autoAlpha: 1 });

                let charactersHtml = "";

                if (!USE_ONLINE_PICTURE) {
                  await CharacterDisplay(
                    $(element).find(`.icon_image`),
                    {
                      load_settings_path: "icon",
                      slice_character: [0, 1],
                      source: `bracket.players.slot.${teamId}`,
                    },
                    event
                  );
                } else {
                  SetInnerHtml(
                    $(element).find(".icon_image"),
                    player && player.online_avatar
                      ? `<div class="floating_online_avatar" style="background-image: url('${player.online_avatar}')"></div>`
                      : '<div style="background: gray; width: 100%; height: 100%; border-radius: 8px;"></div>'
                  );
                }
              }
            }
          }

          // Return unmanaged icons to start
          for (const [index, anim] of iconAnimationsL.entries()) {
            if (!managedIcons.includes(index)) {
              anim.tweenTo(0, { duration: firstUpdate ? 0 : undefined });

              let element = $(
                `.losers_icons .bracket_icon.bracket_icon_p${index + 1}`
              );
              if (element.get(0)) {
                SetInnerHtml($(element).find(`.icon_name`), `---`);
                gsap.to($(element), {
                  autoAlpha: 0,
                  duration: firstUpdate ? 0 : undefined,
                });
              }
            }
          }

          SetInnerHtml($(".header .title"), data.tournamentInfo.tournamentName);

          let infos = [];

          if (data.bracket.phase) infos.push(data.bracket.phase);
          if (data.bracket.phaseGroup) infos.push(data.bracket.phaseGroup);
          if (data.tournamentInfo.numEntrants)
            infos.push(data.tournamentInfo.numEntrants + " Players");

          SetInnerHtml($(".info_content"), infos.join(" / "));

          continue;
        }
      }

      firstUpdate = false;
    }
  };
});
