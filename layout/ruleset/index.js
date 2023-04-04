LoadEverything().then(() => {
  Start = async (event) => {};

  Update = async (event) => {
    let data = event.data;
    let oldData = event.oldData;

    if (
      !oldData.score ||
      JSON.stringify(data.score.ruleset) !=
        JSON.stringify(oldData.score.ruleset)
    ) {
      html = "";
      data.score.ruleset.neutralStages.forEach((stage) => {
        html += `
            <div class="stage-container">
                <div class="stage-icon" style="background-image: url('../../${stage.path}')">
                </div>
                <div class="stage-name">
                    <div class="text">
                        ${stage.name}
                    </div>
                </div>
            </div>
        `;
      });
      $(".neutral").html(html);
      $(".neutral")
        .find(".stage-name")
        .each(function () {
          FitText($(this));
        });

      html = "";
      data.score.ruleset.counterpickStages.forEach((stage) => {
        html += `
            <div class="stage-container">
                <div class="stage-icon" style="background-image: url('../../${stage.path}')">
                </div>
                <div class="stage-name">
                    <div class="text">
                        ${stage.name}
                    </div>
                </div>
            </div>
        `;
      });
      $(".counterpick").html(html);
      $(".counterpick")
        .find(".stage-name")
        .each(function () {
          FitText($(this));
        });

      if (Object.values(data.score.ruleset.counterpickStages).length == 0) {
        $(".counterpick_stages").css("display", "none");
      } else {
        $(".counterpick_stages").css("display", "");
      }

      let rules = [];

      if (data.score.ruleset.useDSR) {
        rules.push("DSR: Each stage can only be picked once during the set");
      }
      if (data.score.ruleset.useMDSR) {
        rules.push("MDSR: You cannot pick a stage where you won a game");
      }

      if (data.score.ruleset.strikeOrder) {
        rules.push(
          "First match strike order: " +
            data.score.ruleset.strikeOrder.map((a) => "P" + a).join(", ")
        );
      }

      if (data.score.ruleset.banCount) {
        rules.push(
          "After each match, winner bans " +
            data.score.ruleset.banCount +
            " stages"
        );
      }

      $(".rules").html(rules.join("<br/>"));

      $(".title.ruleset").html(data.score.ruleset.name);
    }
  };
});
