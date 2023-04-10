LoadEverything().then(() => {
  gsap.config({ nullTargetWarn: false, trialWarn: false });

  let startingAnimation = gsap
    .timeline({ paused: true })
    .from(
      [".anim_container_outer"],
      {
        duration: 0.5,
        y: "-130px",
        ease: "power2.Out",
      },
      1
    )
    .from(
      [".p1 .inner_container"],
      {
        duration: 0.75,
        x: "255px",
        ease: "power2.Out",
      },
      "<50%"
    )
    .from(
      [".p2 .inner_container"],
      {
        duration: 0.75,
        x: "-255px",
        ease: "power2.Out",
      },
      "<"
    )
    .from(
      [".p1 .sponsor_container"],
      {
        duration: 0.75,
        x: "-255px",
        ease: "power2.Out",
      },
      "<"
    )

    .from(
      [".p2 .sponsor_container"],
      {
        duration: 0.75,
        x: "255px",
        ease: "power2.Out",
      },
      "<"
    )
    .from(
      [".p1 .name_container"],
      {
        duration: 0.75,
        x: "200px",
        ease: "power2.Out",
      },
      "<50%"
    )
    .from(
      [".p2 .name_container"],
      {
        duration: 0.75,
        x: "-200px",
        ease: "power2.Out",
      },
      "<"
    )
    .from(
      [".p1 .flags_container"],
      {
        duration: 0.75,
        x: "200px",
        ease: "power2.Out",
      },
      "<"
    )
    .from(
      [".p2 .flags_container"],
      {
        duration: 0.75,
        x: "-200px",
        ease: "power2.Out",
      },
      "<"
    )
    .from(
      [".p1 .losers_container"],
      {
        duration: 0.75,
        x: "270px",
        ease: "power2.Out",
      },
      "<"
    )
    .from(
      [".p2 .losers_container"],
      {
        duration: 0.75,
        x: "-270px",
        ease: "power2.Out",
      },
      "<"
    );

  Start = async () => {
    setInterval(UpdateMatch, 10000);
    setInterval(UpdateFlagSponsor, 10000);
    startingAnimation.restart();
  };

  Update = async (event) => {
    let data = event.data;
    let oldData = event.oldData;

    for (const [t, team] of [
      data.score.team["1"],
      data.score.team["2"],
    ].entries()) {
      for (const [p, player] of [team.player["1"]].entries()) {
        if (player) {
          const playerLosers = document.querySelector(
            `.p${t + 1} .losers_container`
          );

          if (team.losers) {
            playerLosers.classList.add("unhidden");
            playerLosers.classList.remove("hidden");
          } else {
            playerLosers.classList.add("hidden");
            playerLosers.classList.remove("unhidden");
          }

          SetInnerHtml(
            $(`.p${t + 1}.container .name`),
            `
              ${player.name ? await Transcript(player.name.toUpperCase()) : ""}
            `
          );

          SetInnerHtml(
            $(`.p${t + 1} .losers_container`),
            `${team.losers ? "<span class='losers'>[L]</span>" : ""}`
          );

          let score = [data.score.score_left, data.score.score_right];

          SetInnerHtml($(`.p${t + 1} .score`), String(team.score));

          SetInnerHtml(
            $(`.p${t + 1} .sponsor_container`),
            `<div class='sponsor_logo' style='background-image: url(../../${player.sponsor_logo})'></div>`
          );
        }
      }
    }

    // Only on first update
    if (Object.keys(oldData).length == 0) {
      UpdateMatch();
      UpdateFlagSponsor();
    }
  };

  async function UpdateFlagSponsor() {
    [data.score.team["1"], data.score.team["2"]].forEach((team, t) => {
      [team.player["1"]].forEach((player, p) => {
        if (player) {
          if (!player.country.asset && !player.sponsor_logo) {
            SetInnerHtml($(`.p${t + 1}.container .flagcountry`), "");
          } else if (player.country.asset && player.sponsor_logo) {
            SetInnerHtml(
              $(`.p${t + 1}.container .flagcountry`),
              `<div class='flag' style='background-image: url(../../${player.country.asset.toLowerCase()})'></div>`
            );
            SetInnerHtml(
              $(`.p${t + 1}.container .flagcountry`),
              `<div class='flag' style='background-image: url(../../${player.sponsor_logo})'></div>`
            );
          } else if (player.country.asset && !player.sponsor_logo) {
            SetInnerHtml(
              $(`.p${t + 1}.container .flagcountry`),
              `<div class='flag' style='background-image: url(../../${player.country.asset.toLowerCase()})'></div>`
            );
          } else if (!player.country.asset && player.sponsor_logo) {
            SetInnerHtml(
              $(`.p${t + 1}.container .flagcountry`),
              `<div class='flag' style='background-image: url(../../${player.sponsor_logo})'></div>`
            );
          }
        }
      });
    });
  }

  async function UpdateMatch() {
    const tournamentContainer = document.querySelector(".tournament_container");

    if (!(data.score.best_of || data.score.match)) {
      tournamentContainer.classList.add("hidden");
      tournamentContainer.classList.remove("unhidden");
    } else {
      tournamentContainer.classList.add("unhidden");
      tournamentContainer.classList.remove("hidden");

      if (!data.score.best_of && data.score.match) {
        SetInnerHtml($(".match"), data.score.match.toUpperCase());
      } else if (data.score.best_of && !data.score.match) {
        SetInnerHtml($(".match"), data.score.best_of_text.toUpperCase());
      } else {
        SetInnerHtml($(".match"), data.score.best_of_text.toUpperCase());
        SetInnerHtml($(".match"), data.score.match.toUpperCase());
      }
    }
  }
});
