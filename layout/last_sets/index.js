LoadEverything().then(() => {
  if (!window.PLAYER) {
    window.PLAYER = 1;
  }

  let scoreboardNumber = 1;

  gsap.config({ nullTargetWarn: false, trialWarn: false });

  let startingAnimation = gsap.timeline({ paused: true });

  Start = async (event) => {
    startingAnimation.restart();
  };

  Update = async (event) => {
    let data = event.data;
    let oldData = event.oldData;

    if (
      !oldData.score ||
      JSON.stringify(data.score.last_sets) !=
        JSON.stringify(oldData.score.last_sets)
    ) {
      sets_html = "";
      Object.values(data.score[scoreboardNumber].last_sets[window.PLAYER])
        .slice(0, 3)
        .reverse()
        .forEach((sets, s) => {
          sets_html += `<div class="set${s + 1} set_container">
          <div class="info">
            <div class="phase"></div>
            <div class="match"></div>
          </div>
          <div class="p1 color${window.PLAYER == 1 ? 1 : 2} ${
            sets.player_score > sets.oponent_score ? "winner" : "loser"
          }">
            <div class="name">
            </div>
            <div class="score"></div>
          </div>
          <div class="p2 color${window.PLAYER == 1 ? 2 : 1} ${
            sets.player_score > sets.oponent_score ? "loser" : "winner"
          }">
            <div class="name">
            </div>
            <div class="score"></div>
          </div>
        </div>`;
        });
      if (Object.values(data.score[scoreboardNumber].last_sets[window.PLAYER]).length > 0) {
        sets_html +=
          '<div class="bracket_line"><div class="line_arrow"></div></div>';
      }
      $(".player1_content").html(sets_html);

      for (const [s, sets] of Object.values(data.score[scoreboardNumber].last_sets[window.PLAYER])
        .slice(0, 3)
        .reverse()
        .entries()) {
        let phaseTexts = [];
        if (sets.phase_name) phaseTexts.push(sets.phase_name);
        if (sets.phase_id) phaseTexts.push(sets.phase_id);
        SetInnerHtml(
          $(`.player1_content .set${s + 1} .phase`),
          phaseTexts.join(" ")
        );
        SetInnerHtml(
          $(`.player1_content .set${s + 1} .match`),
          sets.round_name
        );
        SetInnerHtml(
          $(`.player1_content .set${s + 1} .p1 .name`),
          `
            <span class="sponsor">
              ${sets.player_team ? sets.player_team : ""}
            </span>
            ${await Transcript(sets.player_name)}
          `
        );
        SetInnerHtml(
          $(`.player1_content .set${s + 1} .p1 .score`),
          sets.player_score
        );
        SetInnerHtml(
          $(`.player1_content .set${s + 1} .p2 .name`),
          `
            <span class="sponsor">
              ${sets.oponent_team ? sets.oponent_team : ""}
            </span>
            ${await Transcript(sets.oponent_name)}
          `
        );
        SetInnerHtml(
          $(`.player1_content .set${s + 1} .p2 .score`),
          sets.oponent_score
        );
        gsap.from(
          $(`.set${s + 1}`),
          { x: -100, autoAlpha: 0, duration: 0.4 },
          0.2 + 0.2 * s
        );
      }

      gsap.fromTo(
        $(".bracket_line"),
        { width: 0 },
        { width: "calc(100% + 240px)", duration: 1, ease: "Power2.easeOut" }
      );
    }
  };
});
