LoadEverything().then(() => {
  
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
      data.score[window.scoreboardNumber].team["1"],
      data.score[window.scoreboardNumber].team["2"],
    ].entries()) {
      console.log(team);

      let team_id = ["left", "right"][t];

      SetInnerHtml($(`.${team_id} .score`), String(team.score));

      if(team.color) {
        document.querySelector(':root').style.setProperty(`--p${t + 1}-score-bg-color`, team.color);
      }

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
            player.pronoun ? `${player.pronoun}` : ""
          );

          SetInnerHtml(
            $(`.${team_id} .p${p + 1} .seed`),
            player.seed ? `Seed ${player.seed}` : ""
          );

          SetInnerHtml(
            $(`.${team_id} .p${p + 1} .flagcountry`),
            player.country.asset
              ? `
              <div class='flag' style='background-image: url(../../${String(
                player.country.asset
              ).toLowerCase()})'></div>
              <div class='flagname'>${player.country.code}</div>
            `
              : ""
          );

          SetInnerHtml(
            $(`.${team_id} .p${p + 1} .flagstate`),
            player.state.asset
              ? `
              <div class='flag' style='background-image: url(../../${player.state.asset})'></div>
              <div class='flagname'>${player.state.code}</div>
            `
              : ""
          );

          if ($(".cameras").length == 0) {
            await CharacterDisplay(
              $(`.${team_id} .p${p + 1}.container .character_container`),
              {
                source: `score.${window.scoreboardNumber}.team.${t + 1}.player.${p + 1}`,
              },
              event
            );
          } else {
            await CharacterDisplay(
              $(`.${team_id} .p${p + 1}.container .character_container`),
              {
                source: `score.${window.scoreboardNumber}.team.${t + 1}.player.${p + 1}`,
                asset_key: "base_files/icon"
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

    let topInfo = []
    topInfo.push(data.tournamentInfo.tournamentName)
    topInfo.push(data.score[window.scoreboardNumber].phase)
    SetInnerHtml($(".info.container.top"), topInfo.join(" | "));

    let phaseTexts = [];
    if (data.score[window.scoreboardNumber].phase) phaseTexts.push(data.score[window.scoreboardNumber].match);
    if (data.score[window.scoreboardNumber].best_of_text) phaseTexts.push(data.score[window.scoreboardNumber].best_of_text);

    SetInnerHtml($(".match"), phaseTexts.join(" | "));
  };
});
