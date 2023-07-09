LoadEverything().then(() => {
  Start = async (event) => {};

  var hideStagesTimeout = null;

  function GetBannedStages(ruleset, state) {
    let banList = [];

    if (ruleset.useDSR) {
      banList = state.stagesPicked ? state.stagesPicked : [];
    } else if (ruleset.useMDSR && state.lastWinner !== -1) {
      banList =
        state.stagesWon && state.stagesWon.length > 0
          ? state.stagesWon[(state.lastWinner + 1) % 2]
          : [];
    }

    return banList;
  }

  function IsStageBanned(ruleset, state, stage) {
    let banList = GetBannedStages(ruleset, state);

    console.log("banList", banList);

    let found = banList.findIndex((e) => e === stage);
    if (found !== -1) {
      return true;
    }
    return false;
  }

  function IsStageStriked(state, stage, previously = false) {
    for (let i = 0; i < Object.values(state.strikedStages).length; i += 1) {
      if (i === Object.values(state.strikedStages).length - 1 && previously) {
        continue;
      }
      let round = Object.values(state.strikedStages)[i];
      let found = round.findIndex((e) => e === stage);
      if (found !== -1) {
        return true;
      }
    }
    return false;
  }

  Update = async (event) => {
    let data = event.data;
    let oldData = event.oldData;

    if (
      !oldData.score ||
      JSON.stringify(data.score.stage_strike) !=
        JSON.stringify(oldData.score.stage_strike) ||
      JSON.stringify(oldData.score.team) != JSON.stringify(data.score.team)
    ) {
      html = "";

      try {
        let teamNames = [];

        [data.score.team["1"], data.score.team["2"]].forEach((team, t) => {
          let teamName = "";

          if (!team.teamName || team.teamName == "") {
            let names = [];
            Object.values(team.player).forEach((player, p) => {
              if (player) {
                names.push(player.name);
              }
            });
            teamName = names.join(" / ");
          } else {
            teamName = team.teamName;
          }

          if (teamName == "") {
            teamName = "P" + (t + 1);
          }

          teamNames.push(teamName);
        });

        console.log(data.score.teamsSwapped);

        if (data.score.teamsSwapped == true) {
          teamNames = teamNames.reverse();
        }

        console.log(teamNames);

        console.log(data.score.stage_strike);

        let allStages = data.score.ruleset.neutralStages;

        if (data.score.stage_strike.currGame > 0) {
          allStages = allStages.concat(data.score.ruleset.counterpickStages);
        }

        console.log(allStages);

        allStages.forEach((stage) => {
          let path = stage.path;
          html += `
              <div class="stage-container 
                ${
                  IsStageStriked(data.score.stage_strike, stage.codename) ||
                  IsStageBanned(
                    data.score.ruleset,
                    data.score.stage_strike,
                    stage.codename
                  )
                    ? "striked"
                    : ""
                }
                ${
                  data.score.stage_strike.selectedStage &&
                  data.score.stage_strike.selectedStage == stage.codename
                    ? "selected"
                    : ""
                }
                ">
                  <div class="stage-icon" style="background-image: url('../../${path}')">
                      ${
                        IsStageStriked(data.score.stage_strike, stage.codename)
                          ? `<div class="stage-striked stamp"></div>`
                          : ""
                      }
                      ${
                        IsStageBanned(
                          data.score.ruleset,
                          data.score.stage_strike,
                          stage.codename
                        )
                          ? `<div class="stage-dsr stamp"></div>`
                          : ""
                      }
                      ${
                        data.score.stage_strike.selectedStage &&
                        data.score.stage_strike.selectedStage == stage.codename
                          ? data.score.stage_strike.gentlemans
                            ? `<div class="stage-selected-gentlemans stamp"></div>`
                            : `<div class="stage-selected stamp"></div>`
                          : ""
                      }
                  </div>
                  <div class="stage-name">
                      <div class="text">
                          ${stage.name}
                      </div>
                  </div>
                  ${
                    IsStageStriked(data.score.stage_strike, stage.codename) &&
                    (data.score.stage_strike.strikedBy[0].includes(
                      stage.codename
                    ) ||
                      data.score.stage_strike.strikedBy[1].includes(
                        stage.codename
                      ))
                      ? `<div class="banned-by-name">
                        <div class="text">
                          ${
                            data.score.stage_strike.strikedBy[0].includes(
                              stage.codename
                            )
                              ? teamNames[0]
                              : teamNames[1]
                          }
                        </div>
                      </div>`
                      : ""
                  }
                  ${
                    data.score.stage_strike.selectedStage &&
                    data.score.stage_strike.selectedStage == stage.codename
                      ? `<div class="banned-by-name">
                        <div class="text">
                          ${
                            data.score.stage_strike.gentlemans
                              ? "Gentlemans"
                              : teamNames[data.score.stage_strike.currPlayer]
                          }
                        </div>
                      </div>`
                      : ""
                  }
              </div>
          `;
        });

        // Hide stage strike logic
        if (hideStagesTimeout != null) {
          clearTimeout(hideStagesTimeout);
        }

        if (
          window.AUTOHIDE &&
          !_.get(oldData, "score.stage_strike.selectedStage") &&
          _.get(data, "score.stage_strike.selectedStage")
        ) {
          hideStagesTimeout = setTimeout(() => {
            gsap.to(".container", { autoAlpha: "0" });
          }, 5000);
        }
      } catch (e) {
        console.log(e);
      }
      $(".container").html(html);

      // Fade stage strike back in
      if (!_.get(data, "score.stage_strike.selectedStage")) {
        gsap.to(".container", { autoAlpha: "1", overwrite: true });
      }

      $(".container")
        .find(".stage-name, .banned-by-name")
        .each(function () {
          FitText($(this));
        });
    }
  };
});
