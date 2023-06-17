LoadEverything().then(() => {
  gsap.config({ nullTargetWarn: false, trialWarn: false });

  let startingAnimation = gsap
    .timeline({ paused: true })
    .from([".logo"], { duration: 0.5, autoAlpha: 0, ease: "power2.inOut" }, 0.5)
    .from(
      [".anim_container_outer"],
      {
        duration: 1,
        width: "0",
        ease: "power2.inOut",
      },
      1
    )
    .from(
      [".p1.twitter"],
      {
        duration: 0.75,
        x: "-373px",
        ease: "power4.Out",
      },
      "<25%"
    )
    .from(
      [".p2.twitter"],
      {
        duration: 0.75,
        x: "373px",
        ease: "power4.Out",
      },
      "<"
    )
    .from(
      ".tournament_container",
      { opacity: 0, duration: 0.5, ease: "power4.Out" },
      "<80%"
    )
    .from(
      ".tournament_logo",
      { opacity: 0, duration: 0.5, ease: "power4.Out" },
      "<"
    );

  Start = async () => {
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
          if (Object.keys(team.player).length == 1) {
            SetInnerHtml(
              $(`.p${t + 1}.container .name`),
              `
                <span class="sponsor">
                  ${player.team ? player.team.toUpperCase() : ""}
                </span>
                ${
                  player.name ? await Transcript(player.name.toUpperCase()) : ""
                }
              `
            );
          } else {
            let teamName = "";

            if (!team.teamName || team.teamName == "") {
              let names = [];
              for (const [p, player] of Object.values(team.player).entries()) {
                if (player && player.name) {
                  names.push(await Transcript(player.name));
                }
              }
              teamName = names.join(" / ");
            } else {
              teamName = team.teamName;
            }

            SetInnerHtml(
              $(`.p${t + 1}.container .name`),
              `
              <span>
                ${teamName.toUpperCase()}
                ${team.losers ? "(L)" : ""}
              </span>
              `
            );
          }

          SetInnerHtml(
            $(`.p${t + 1} .losers_container`),
            `${team.losers ? "<span class='losers'>L</span>" : ""}`
          );

          SetInnerHtml(
            $(`.p${t + 1}.container .flagcountry`),
            player.country.asset && Object.keys(team.player).length == 1
              ? `<div class='flag' style='background-image: url(../../${player.country.asset.toLowerCase()})'></div>`
              : `<div class='flag' style=''></div>`
          );

          const playerTwitter = document.querySelector(`.p${t + 1}.twitter`);

          if (
            player.twitter == undefined ||
            String(player.twitter) == "" ||
            Object.values(team.player).length != 1
          ) {
            playerTwitter.classList.add("hidden");
            playerTwitter.classList.remove("unhidden");
          } else {
            playerTwitter.classList.add("unhidden");
            playerTwitter.classList.remove("hidden");
          }

          SetInnerHtml(
            $(`.p${t + 1}.twitter`),
            player.twitter
              ? `<span class="twitter_logo"></span>${
                  "@" + String(player.twitter).toUpperCase()
                }`
              : ""
          );

          let score = [data.score.score_left, data.score.score_right];

          SetInnerHtml($(`.p${t + 1}.container .score`), String(team.score));

          SetInnerHtml(
            $(`.p${t + 1} .sponsor-container`),
            player.sponsor_logo && Object.keys(team.player).length == 1
              ? `<div class='sponsor-logo' style='background-image: url(../../${player.sponsor_logo})'></div>`
              : `<div class='sponsor-logo' style=''></div>`
          );
        }
      }
    }

    SetInnerHtml(
      $(".tournament_name"),
      data.tournamentInfo.tournamentName.toUpperCase()
    );

    SetInnerHtml($(".match"), data.score.match.toUpperCase());

    let phaseTexts = [];
    if (data.score.phase) phaseTexts.push(data.score.phase.toUpperCase());
    if (data.score.best_of_text)
      phaseTexts.push(`${data.score.best_of_text}`.toUpperCase());

    SetInnerHtml($(".phase"), phaseTexts.join(" - "));
  };
});
