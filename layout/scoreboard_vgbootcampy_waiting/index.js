LoadEverything().then(() => {

  let scoreboardNumber = 1;

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
    // .from(
    //   ".tournament_container",
    //   { opacity: 0, duration: 0.5, ease: "power4.Out" },
    //   "<80%"
    // )
    .from(
      ".tournament_container",
      {
        duration: 0.75,
        x: "-373px",
        ease: "power4.Out",
      },
      "<"
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
      data.score[scoreboardNumber].team["1"],
      data.score[scoreboardNumber].team["2"],
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
                ${team.losers ? "(L)" : ""}
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

          let score = [data.score[scoreboardNumber].score_left, data.score[scoreboardNumber].score_right];

          SetInnerHtml($(`.p${t + 1}.score`), String(team.score));
        }
      }
    }
  };
});
