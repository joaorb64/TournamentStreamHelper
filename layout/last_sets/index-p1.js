(($) => {
  gsap.config({ nullTargetWarn: false, trialWarn: false });

  let startingAnimation = gsap
    .timeline({ paused: true });

  function Start() {
    startingAnimation.restart();
  }

  var data = {};
  var oldData = {};

  async function Update() {
    oldData = data;
    data = await getData();
    if (!oldData.score ||
      JSON.stringify(data.score.last_sets) != JSON.stringify(oldData.score.last_sets)) {

      $('.player1_container').html('')

      sets_html = ""
      Object.values(data.score.last_sets["1"]).slice(0, 3).forEach((sets, s) => {
        sets_html += `<div class="set${s+1} set_container">
          <div class="info">
            <div class="phase"></div>
            <div class="match"></div>
          </div>
          <div class="winner">
            <div class="name">
            </div>
            <div class="score"></div>
          </div>
          <div class="loser">
            <div class="name">
            </div>
            <div class="score"></div>
          </div>
        </div>`
        });
        $('.player1_content').html(sets_html);

        Object.values(data.score.last_sets["1"]).slice(0, 3).forEach((sets, s) => {
          let phaseTexts = [];
          if (sets.phase_name) phaseTexts.push(sets.phase_name);
          if (sets.phase_id) phaseTexts.push(sets.phase_id);
          SetInnerHtml($(`.player1_content .set${s+1} .phase`), phaseTexts.join(" "));
          SetInnerHtml($(`.player1_content .set${s+1} .match`), sets.round_name);
          SetInnerHtml($(`.player1_content .set${s+1} .winner .name`), 
          `
            <span class="sponsor">
              ${sets.winner_team ? sets.winner_team : ""}
            </span>
            ${sets.winner_name}
          `
          );
          SetInnerHtml($(`.player1_content .set${s+1} .winner .score`), sets.winner_score);
          SetInnerHtml($(`.player1_content .set${s+1} .loser .name`), 
          `
            <span class="sponsor">
              ${sets.loser_team ? sets.loser_team : ""}
            </span>
            ${sets.loser_name}
          `
          );
          SetInnerHtml($(`.player1_content .set${s+1} .loser .score`), sets.loser_score);
          gsap.from($(`.set${s + 1}`), { y: +100, autoAlpha: 0, duration: 0.4 }, 0.5 + 0.3 * s);
      });
    }

    $(".text").each(function (e) {
      FitText($($(this)[0].parentNode));
    });

    $(".container div:has(>.text:empty)").css("margin-right", "0");
    $(".container div:not(:has(>.text:empty))").css("margin-right", "");
    $(".container div:has(>.text:empty)").css("margin-left", "0");
    $(".container div:not(:has(>.text:empty))").css("margin-left", "");
  }

  Update();
  $(window).on("load", () => {
    $("body").fadeTo(1, 1, async () => {
      Start();
      setInterval(Update, 500);
    });
  });
})(jQuery);
