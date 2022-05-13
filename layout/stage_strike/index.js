(($) => {
  function Start() {}

  var data = {};
  var oldData = {};

  async function Update() {
    oldData = data;
    data = await getData();

    if (
      !oldData.score ||
      JSON.stringify(data.score.stage_strike) !=
        JSON.stringify(oldData.score.stage_strike)
    ) {
      console.log(data.score.stage_strike);
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

          teamNames.push(teamName);
        });

        Object.keys(data.score.stage_strike.stages).forEach((stage) => {
          let path = data.score.stage_strike.stages[stage].path;
          html += `
              <div class="stage-container">
                  <div class="stage-icon" style="background-image: url('../../${path}')">
                      ${
                        data.score.stage_strike.striked.includes(stage) &&
                        !data.score.stage_strike.dsr.includes(stage)
                          ? `<div class="stage-striked stamp"></div>`
                          : ""
                      }
                      ${
                        data.score.stage_strike.dsr.includes(stage)
                          ? `<div class="stage-dsr stamp"></div>`
                          : ""
                      }
                      ${
                        data.score.stage_strike.selected &&
                        data.score.stage_strike.selected.codename == stage
                          ? `<div class="stage-selected stamp"></div>`
                          : ""
                      }
                  </div>
                  <div class="stage-name">
                      <div class="text">
                          ${data.score.stage_strike.stages[stage].name}
                      </div>
                  </div>
                  ${
                    data.score.stage_strike.striked.includes(stage) &&
                    (data.score.stage_strike.strikedBy[0].includes(stage) ||
                      data.score.stage_strike.strikedBy[1].includes(stage))
                      ? `<div class="banned-by-name">
                        <div class="text">
                          ${
                            data.score.stage_strike.strikedBy[0].includes(stage)
                              ? teamNames[0]
                              : teamNames[1]
                          }
                        </div>
                      </div>`
                      : ""
                  }
                  ${
                    data.score.stage_strike.selected &&
                    data.score.stage_strike.selected.codename == stage
                      ? `<div class="banned-by-name">
                        <div class="text">
                          ${teamNames[data.score.stage_strike.currPlayer]}
                        </div>
                      </div>`
                      : ""
                  }
              </div>
          `;
        });
      } catch (e) {
        console.log(e);
      }
      $(".container").html(html);
      $(".container")
        .find(".stage-name, .banned-by-name")
        .each(function () {
          FitText($(this));
        });
    }
  }

  Update();
  $(window).on("load", () => {
    $("body").fadeTo(1000, 1, async () => {
      Start();
      setInterval(Update, 32);
    });
  });
})(jQuery);
