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

  function getNumberOrdinal(n) {
    var s = ["th", "st", "nd", "rd"],
      v = n % 100;
    return s[(v - 20) % 10] || s[v] || s[0];
  }

  Update = async (event) => {
    let data = event.data;
    let oldData = event.oldData;

    if (
      !oldData.score ||
      JSON.stringify(data.score[scoreboardNumber].history_sets) !=
        JSON.stringify(oldData.score[scoreboardNumber].history_sets)
    ) {
      tournament_html = "";
      Object.values(data.score[scoreboardNumber].history_sets[window.PLAYER])
        .slice(0, 6)
        .forEach((sets, s) => {
          tournament_html += `
          <div class="tournament${s + 1} tournament_container">
            <div class="info">
              <div class="tournament_logo"></div>
              <div class="placement"></div>
              <div class="tournament_info">
                <div class="tournament_name"></div>
                <div class="event_name"></div>
              </div>
            </div>
          </div>`;
        });
      $(".player1_content").html(tournament_html);

      for (const [s, tournament] of Object.values(
        data.score[scoreboardNumber].history_sets[window.PLAYER]
      )
        .slice(0, 6)
        .entries()) {
        SetInnerHtml(
          $(
            `.player1_content .tournament${
              s + 1
            } .info .tournament_info .tournament_name`
          ),
          tournament.tournament_name
        );
        SetInnerHtml(
          $(
            `.player1_content .tournament${
              s + 1
            } .info .tournament_info .event_name`
          ),
          tournament.event_name
        );
        SetInnerHtml(
          $(`.player1_content .tournament${s + 1} .info .tournament_logo`),
          `
              <span class="logo" style="background-image: url('${tournament.tournament_picture}')"></span>
            `
        );
        SetInnerHtml(
          $(`.player1_content .tournament${s + 1} .info .placement`),
          tournament.placement +
            `<span class="ordinal">${getNumberOrdinal(
              tournament.placement
            )}</span><span class="num_entrants">/${tournament.entrants}</span>`
        );
        gsap.from(
          $(`.tournament${s + 1}`),
          { x: -100, autoAlpha: 0, duration: 0.3 },
          0.2 + 0.2 * s
        );
      }
    }
  };
});
