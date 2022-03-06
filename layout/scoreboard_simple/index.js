(($) => {
  let startingAnimation = gsap
    .timeline({ paused: true })
    .from(
      [".phase"],
      { duration: 0.8, opacity: "0", y: "-20px", ease: "power2.inOut" },
      0
    )
    .from(
      [".container"],
      { duration: 0.8, opacity: "0", x: "-20px", ease: "power2.inOut" },
      0
    )
    .from(
      [".twitter-container"],
      { duration: 0.8, opacity: "0", x: "+40px", ease: "power2.inOut" },
      0
    );

  function Start() {
    startingAnimation.restart();
  }

  var data = {};
  var oldData = {};

  async function Update() {
    oldData = data;
    data = await getData();

    let isDoubles = Object.keys(data.score.team["1"].player).length == 2;

    if (
      oldData.score == null ||
      Object.keys(oldData.score.team["1"].player).length !=
        Object.keys(data.score.team["1"].player).length
    ) {
      if (Object.keys(data.score.team["1"].player).length == 1) {
        gsap
          .timeline()
          .fromTo(
            ["body > .doubles"],
            { duration: 0.2, opacity: "1", ease: "power2.inOut" },
            { duration: 0.2, opacity: "0", ease: "power2.inOut" }
          )
          .fromTo(
            ["body > .singles"],
            { duration: 0.2, opacity: "0", ease: "power2.inOut" },
            { duration: 0.2, opacity: "1", ease: "power2.inOut" }
          );
      } else {
        gsap
          .timeline()
          .fromTo(
            ["body > .singles"],
            { duration: 0.2, opacity: "1", ease: "power2.inOut" },
            { duration: 0.2, opacity: "0", ease: "power2.inOut" }
          )
          .fromTo(
            ["body > .doubles"],
            { duration: 0.2, opacity: "0", ease: "power2.inOut" },
            { duration: 0.2, opacity: "1", ease: "power2.inOut" }
          );
      }
    }

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
      console.log(teamName);

      SetInnerHtml(
        $(`.info.doubles.t${t + 1}`),
        `
          ${teamName}${team.losers ? " [L]" : ""}
        `
      );

      Object.values(team.player).forEach((player, p) => {
        if (player) {
          SetInnerHtml(
            $(`.t${t + 1}.p${p + 1} .name`),
            `
                <span>
                    <span class='sponsor'>
                        ${player.team ? player.team + "" : ""}
                    </span>
                    ${player.name}
										${team.losers && !isDoubles ? " [L]" : ""}
                </span>
            `
          );

          SetInnerHtml(
            $(`.t${t + 1}.p${p + 1} .flagcountry`),
            player.country.asset
              ? `
                <div class='flag' style='background-image: url(../../${player.country.asset.toLowerCase()})'></div>
            `
              : ""
          );

          SetInnerHtml(
            $(`.t${t + 1}.p${p + 1} .flagstate`),
            player.state.asset
              ? `
                <div class='flag' style='background-image: url(../../${player.state.asset})'></div>
            `
              : ""
          );

          SetInnerHtml(
            $(`.t${t + 1}.p${p + 1} .twitter`),
            String(player.twitter)
          );

          SetInnerHtml(
            $(`.t${t + 1}.p${p + 1} .score`),
            !isDoubles ? String(team.score) : ""
          );

          SetInnerHtml(
            $(`.t${t + 1}.p${p + 1} .sponsor-container`),
            `<div class='sponsor-logo' style='background-image: url(../../${player.sponsor_logo})'></div>`
          );
        }
      });
    });

    SetInnerHtml(
      $(".info.material_container.top"),
      data.tournamentInfo.tournamentName
    );
    SetInnerHtml(
      $(".info.material_container.bottom"),
      `
            <div class="info material_container_inner">
                ${data.score.phase ? `<div>${data.score.phase}</div>` : ""}
                ${data.score.match ? `<div>${data.score.match}</div>` : ""}
                ${
                  data.score.best_of
                    ? `<div>Best of ${data.score.best_of}</div>`
                    : ""
                }
            </div>
        `
    );
  }

  $(window).on("load", () => {
    Update();
    $("body").fadeTo(500, 1, async () => {
      Start();
      setInterval(Update, 1000);
    });
  });
})(jQuery);
