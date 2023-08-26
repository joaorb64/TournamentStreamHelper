LoadEverything().then(() => {

  let scoreboardNumber = 1;
  
  let startingAnimation = gsap
    .timeline({ paused: true })
    .from(
      [".left .container:not(.cameras)"],
      { duration: 1, x: "-100%", ease: "power2.inOut" },
      0
    )
    .from(
      [".right .container:not(.cameras)"],
      { duration: 1, x: "+100%", ease: "power2.inOut" },
      0
    )
    .from([".score"], { duration: 1, autoAlpha: "0", ease: "power2.inOut" }, 0)
    .from(
      [".left .character_container:not(.cameras)"],
      { duration: 1, x: "+50%", ease: "power2.inOut" },
      0
    )
    .from(
      [".right .character_container:not(.cameras)"],
      { duration: 1, x: "-50%", ease: "power2.inOut" },
      0
    )
    .from(
      [".container.top"],
      { duration: 1, y: "-100%", ease: "power2.inOut" },
      0
    )
    .from(
      [".container.bottom"],
      { duration: 1, y: "+100%", ease: "power2.inOut" },
      0
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
      console.log(team);

      let team_id = ["left", "right"][t];

      SetInnerHtml($(`.${team_id} .score`), String(team.score));

      let team_size = Object.values(team.player).length;

      let firstRun = Object.keys(oldData).length == 0;
      let time = firstRun ? 0 : 1;

      if (team_size == 1) {
        gsap.timeline().to($(`.${team_id} .p${2}.container`), {
          height: 0,
          duration: time,
        });
      } else {
        gsap.timeline().to($(`.${team_id} .p${2}.container`), {
          height: "420px",
          duration: time,
        });
      }

      for (const [p, player] of Object.values(team.player).entries()) {
        if (player) {
          SetInnerHtml(
            $(`.${team_id} .p${p + 1} .name`),
            `
              <span class="sponsor">${
                player.team ? player.team + "&nbsp;" : ""
              }</span>${await Transcript(player.name)}
            `
          );

          SetInnerHtml(
            $(`.${team_id} .p${p + 1} .pronoun`),
            `
              ${player.pronoun}
            `
          );

          SetInnerHtml(
            $(`.${team_id} .p${p + 1} .seed`),
            `Seed ${player.seed}`
          );

          SetInnerHtml(
            $(`.${team_id} .p${p + 1} .flagcountry`),
            player.country.asset
              ? `
              <div class='flag' style='background-image: url(../../${String(
                player.country.asset
              ).toLowerCase()})'></div>
            `
              : ""
          );

          SetInnerHtml(
            $(`.${team_id} .p${p + 1} .flagstate`),
            player.state.asset
              ? `
              <div class='flag' style='background-image: url(../../${player.state.asset})'></div>
            `
              : ""
          );

          if ($(".cameras").length == 0) {
            await CharacterDisplay(
              $(`.${team_id} .p${p + 1}.container .character_container`),
              {
                source: `score.${scoreboardNumber}.team.${t + 1}.player.${p + 1}`,
              },
              event
            );
          }

          SetInnerHtml(
            $(`.${team_id} .p${p + 1} .twitter`),
            player.twitter
              ? `<span class="twitter_logo"></span>${String(player.twitter)}`
              : ""
          );

          SetInnerHtml(
            $(`.${team_id} .p${p + 1} .sponsor_logo`),
            `<div class='sponsor_logo' style='background-image: url(../../${String(
              player.sponsor_logo
            )})'></div>`
          );
        }
      }
    }

    SetInnerHtml($(".info.container.top"), data.tournamentInfo.tournamentName);

    SetInnerHtml($(".match"), data.score[scoreboardNumber].match);

    let phaseTexts = [];
    if (data.score[scoreboardNumber].phase) phaseTexts.push(data.score[scoreboardNumber].phase);
    if (data.score[scoreboardNumber].best_of_text) phaseTexts.push(data.score[scoreboardNumber].best_of_text);

    SetInnerHtml($(".phase"), phaseTexts.join(" - "));
  };
});
