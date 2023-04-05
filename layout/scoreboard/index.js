LoadEverything().then(() => {
  let ASSET_TO_USE = "base_files/icon";
  let ZOOM = 1;

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
      [".bottom"],
      {
        duration: 1,
        autoAlpha: 0,
        ease: "power2.inOut",
      },
      1
    )
    .from(
      [".fgc .top", ".fgc .player"],
      {
        duration: 1,
        y: "-100px",
        ease: "power2.inOut",
      },
      0
    )
    .from(
      [".fgc:not(.bblue) .bottom"],
      {
        duration: 1,
        y: "+100px",
        ease: "power2.inOut",
      },
      0
    )
    .from(
      [".fgc.bblue .bottom"],
      {
        duration: 1,
        autoAlpha: 0,
        ease: "power2.inOut",
      },
      0.2
    );

  Start = async () => {
    startingAnimation.restart();
  };

  Update = async (event) => {
    let data = event.data;
    let oldData = event.oldData;

    let isDoubles = Object.keys(data.score.team["1"].player).length == 2;

    if (!isDoubles) {
      for (const [t, team] of [
        data.score.team["1"],
        data.score.team["2"],
      ].entries()) {
        for (const [p, player] of [team.player["1"]].entries()) {
          if (player) {
            SetInnerHtml(
              $(`.p${t + 1}.container .name`),
              `
                <span class="sponsor">
                  ${player.team ? player.team : ""}
                </span>
                ${await Transcript(player.name)}
                ${team.losers ? "<span class='losers'>L</span>" : ""}
              `
            );

            SetInnerHtml(
              $(`.p${t + 1} .flagcountry`),
              player.country.asset
                ? `<div class='flag' style='background-image: url(../../${player.country.asset.toLowerCase()})'></div>`
                : ""
            );

            SetInnerHtml(
              $(`.p${t + 1} .flagstate`),
              player.state.asset
                ? `<div class='flag' style='background-image: url(../../${player.state.asset})'></div>`
                : ""
            );

            await CharacterDisplay(
              $(`.p${t + 1}.container .character_container`),
              {
                asset_key: "base_files/icon",
                source: `score.team.${t + 1}`,
              },
              event
            );

            SetInnerHtml(
              $(`.p${t + 1}.container .sponsor_icon`),
              player.sponsor_logo
                ? `<div style='background-image: url(../../${player.sponsor_logo})'></div>`
                : ""
            );

            SetInnerHtml(
              $(`.p${t + 1}.container .avatar`),
              player.avatar
                ? `<div style="background-image: url('../../${player.avatar}')"></div>`
                : ""
            );

            SetInnerHtml(
              $(`.p${t + 1}.container .online_avatar`),
              player.online_avatar
                ? `<div style="background-image: url('${player.online_avatar}')"></div>`
                : ""
            );

            SetInnerHtml(
              $(`.p${t + 1} .twitter`),
              player.twitter
                ? `<span class="twitter_logo"></span>${String(player.twitter)}`
                : ""
            );

            SetInnerHtml(
              $(`.p${t + 1} .pronoun`),
              player.pronoun ? player.pronoun : ""
            );

            SetInnerHtml(
              $(`.p${t + 1} .seed`),
              player.seed ? `Seed ${player.seed}` : ""
            );

            let score = [data.score.score_left, data.score.score_right];

            SetInnerHtml($(`.p${t + 1}.container .score`), String(team.score));

            SetInnerHtml(
              $(`.p${t + 1}.container .sponsor-container`),
              `<div class='sponsor-logo' style='background-image: url(../../${player.sponsor_logo})'></div>`
            );
          }
        }
      }
    } else {
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

        SetInnerHtml(
          $(`.p${t + 1}.container .name`),
          `
            ${teamName}
            ${team.losers ? "<span class='losers'>L</span>" : ""}
          `
        );

        SetInnerHtml($(`.p${t + 1} .flagcountry`), "");

        SetInnerHtml($(`.p${t + 1} .flagstate`), "");

        let charactersHtml = "";

        let charactersChanged = false;

        if (!oldData) {
          charactersChanged = true;
        } else {
          Object.values(team.player).forEach((player, p) => {
            Object.values(player.character).forEach((character, index) => {
              try {
                if (
                  JSON.stringify(player.character) !=
                  JSON.stringify(
                    oldData.score.team[`${t + 1}`].player[`${p + 1}`].character
                  )
                ) {
                  charactersChanged = true;
                }
              } catch {
                charactersChanged = true;
              }
            });
          });
        }

        if (charactersChanged) {
          Object.values(team.player).forEach((player, p) => {
            Object.values(player.character).forEach((character, index) => {
              if (character.assets[ASSET_TO_USE]) {
                charactersHtml += `
                  <div class="icon stockicon">
                    <div data-asset='${JSON.stringify(
                      character.assets[ASSET_TO_USE]
                    )}'></div>
                  </div>
                  `;
              }
            });
          });

          SetInnerHtml(
            $(`.p${t + 1}.container .character_container`),
            charactersHtml,
            undefined,
            0.5,
            () => {
              $(
                `.p${t + 1}.container .character_container .stockicon div`
              ).each((i, e) => {
                CenterImage($(e), JSON.parse($(e).attr("data-asset")), ZOOM);
              });
            }
          );
        }

        SetInnerHtml($(`.p${t + 1}.container .sponsor_icon`), "");

        SetInnerHtml($(`.p${t + 1}.container .avatar`), "");

        SetInnerHtml($(`.p${t + 1}.container .online_avatar`), "");

        SetInnerHtml($(`.p${t + 1} .twitter`), "");

        let score = [data.score.score_left, data.score.score_right];

        SetInnerHtml($(`.p${t + 1}.container .score`), String(team.score));

        SetInnerHtml($(`.p${t + 1}.container .sponsor-container`), "");
      });
    }

    SetInnerHtml($(".tournament_name"), data.tournamentInfo.tournamentName);

    SetInnerHtml($(".match"), data.score.match);

    let phaseTexts = [];
    if (data.score.phase) phaseTexts.push(data.score.phase);
    if (data.score.best_of_text) phaseTexts.push(data.score.best_of_text);

    SetInnerHtml($(".phase"), phaseTexts.join(" - "));
  };
});
