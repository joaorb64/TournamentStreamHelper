LoadEverything().then(() => {
  gsap.config({ nullTargetWarn: false, trialWarn: false });

  let startingAnimation = gsap
    .timeline({ paused: true })
    .from(
      [".container"],
      { duration: 1, opacity: "0", x: "-40px", ease: "power2.inOut" },
      0
    )
    .from(
      [".twitter-container"],
      { duration: 1, opacity: "0", x: "+80px", ease: "power2.inOut" },
      0
    )
    .from(".mask", { width: 0, duration: 1, ease: "power2.inOut" }, 0)
    .from(
      ".doubles .info",
      { opacity: 0, duration: 0.5, ease: "power2.inOut" },
      0.8
    );

  Start = async () => {
    startingAnimation.restart();
  };

  Update = async (event) => {
    let data = event.data;
    let oldData = event.oldData;

    let isTeams = Object.keys(data.score.team["1"].player).length > 1;

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

    for (const [t, team] of [
      data.score.team["1"],
      data.score.team["2"],
    ].entries()) {
      let teamName = "";

      if (!team.teamName || team.teamName == "") {
        let names = [];
        for (const [p, player] of Object.values(team.player).entries()) {
          if (player) {
            names.push(await Transcript(player.name));
          }
        }
        teamName = names.join(" / ");
      } else {
        teamName = team.teamName;
      }

      SetInnerHtml(
        $(`.info.doubles.t${t + 1} .team_name`),
        `
          ${teamName}${team.losers ? " [L]" : ""}
        `
      );

      for (const [p, player] of Object.values(team.player).entries()) {
        if (player) {
          SetInnerHtml(
            $(`.t${t + 1}.p${p + 1} .name`),
            `
                <span>
                    <span class='sponsor'>
                        ${player.team ? player.team + "" : ""}
                    </span>
                    ${await Transcript(player.name)}
										${team.losers && !isTeams ? " [L]" : ""}
                </span>
            `
          );

          SetInnerHtml($(`.t${t + 1}.p${p + 1} .pronoun`), player.pronoun);

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
            player.twitter
              ? `<span class="twitter_logo"></span>${String(player.twitter)}`
              : ""
          );

          SetInnerHtml(
            $(`.t${t + 1}.p${p + 1} .score`),
            !isTeams ? String(team.score) : ""
          );

          SetInnerHtml($(`.t${t + 1} .doubles_score`), String(team.score));

          SetInnerHtml(
            $(`.t${t + 1}.p${p + 1} .sponsor-container`),
            `<div class='sponsor-logo' style='background-image: url(../../${player.sponsor_logo})'></div>`
          );
        }
      }
    }

    let phaseTexts = [];
    if (data.score.phase) phaseTexts.push(data.score.phase);
    if (data.score.best_of_text) phaseTexts.push(data.score.best_of_text);

    SetInnerHtml($(".info.material_container .phase"), phaseTexts.join(" - "));
    SetInnerHtml(
      $(".info.material_container .tournament_name"),
      data.tournamentInfo.tournamentName
    );
    SetInnerHtml($(".info.material_container .match"), data.score.match);
  };
});
