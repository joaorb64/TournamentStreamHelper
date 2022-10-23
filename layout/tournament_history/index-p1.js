(($) => {
  gsap.config({ nullTargetWarn: false, trialWarn: false });

  let startingAnimation = gsap
    .timeline({ paused: true });

  function Start() {
    startingAnimation.restart();
  }

  function getNumberWithOrdinal(n) {
    var s = ["th", "st", "nd", "rd"], v = n %100;
    return n+(s[(v - 20) % 10] || s[v] || s[0]);
  }

  var data = {};
  var oldData = {};

  async function Update() {
    oldData = data;
    data = await getData();
    if (!oldData.score ||
      JSON.stringify(data.score.history_sets) != JSON.stringify(oldData.score.history_sets)) {

      sets_html = ""
      Object.values(data.score.history_sets["1"]).slice(0, 6).forEach((sets, s) => {
        sets_html += `
        <div class="set${s+1} set_container">
          <div class="info">
            <div class="tournament_logo"></div>
            <div class="placement"></div>
            <div class="tournament_info">
              <div class="tournament_name"></div>
              <div class="event_name"></div>
            </div>
          </div>
        </div>`
        });
        $('.player1_content').html(sets_html);

        Object.values(data.score.history_sets["1"]).slice(0, 6).forEach((sets, s) => {
          SetInnerHtml($(`.player1_content .set${s+1} .info .tournament_info .tournament_name`), sets.tournament_name);
          SetInnerHtml($(`.player1_content .set${s+1} .info .tournament_info .event_name`), sets.event_name);
          SetInnerHtml($(`.player1_content .set${s+1} .info .tournament_logo`), 
          `
            <span class="logo" style="background-image: url('${sets.tournament_picture}')"></span>
          `
          );
          SetInnerHtml($(`.player1_content .set${s+1} .info .placement`), getNumberWithOrdinal(sets.placement));
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
