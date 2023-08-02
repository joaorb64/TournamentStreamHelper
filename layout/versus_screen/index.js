LoadEverything().then(() => {
  let startingAnimation = gsap
    .timeline({ paused: true })
    .from(
      [".phase.container"],
      { duration: 0.8, opacity: "0", ease: "power2.inOut" },
      0
    )
    .from([".match"], { duration: 0.8, opacity: "0", ease: "power2.inOut" }, 0)
    .from(
      [".score_container"],
      { duration: 0.8, opacity: "0", ease: "power2.inOut" },
      0
    )
    .from(
      [".best_of.container"],
      { duration: 0.8, opacity: "0", ease: "power2.inOut" },
      0
    )
    .from([".vs"], { duration: 0.4, opacity: "0", scale: 4, ease: "out" }, 0.5)
    .from([".p1.container"], { duration: 1, x: "-100px", ease: "out" }, 0)
    .from([".p2.container"], { duration: 1, x: "100px", ease: "out" }, 0);

  Start = async (event) => {
    startingAnimation.restart();
  };

  Update = async (event) => {
    let data = event.data;
    let oldData = event.oldData;

    let isTeams = Object.keys(data.score.team["1"].player).length > 1;

    if (!isTeams) {
      const teams = Object.values(data.score.team);
      for (const [t, team] of teams.entries()) {
        const players = Object.values(team.player);
        for (const [p, player] of players.entries()) {
          SetInnerHtml(
            $(`.p${t + 1} .name`),
            `
              <span>
                  <div>
                    <span class='sponsor'>
                        ${player.team ? player.team : ""}
                    </span>
                    ${await Transcript(player.name)}
                  </div>
              </span>
            `
          );

          SetInnerHtml($(`.p${t + 1} .pronoun`), player.pronoun);

          SetInnerHtml(
            $(`.p${t + 1} > .sponsor_logo`),
            player.sponsor_logo
              ? `
                <div class='sponsor_logo' style='background-image: url(../../${player.sponsor_logo})'></div>
                `
              : ""
          );

          SetInnerHtml($(`.p${t + 1} .real_name`), player.real_name);

          SetInnerHtml($(`.p${t + 1} .seed`), player.seed ? `Seed ${player.seed}` : "");

          SetInnerHtml(
            $(`.p${t + 1} .twitter`),
            `
              ${
                player.twitter
                  ? `
                  <div class="twitter_logo"></div>
                  ${player.twitter}
                  `
                  : ""
              }
          `
          );

          SetInnerHtml(
            $(`.p${t + 1} .flagcountry`),
            player.country.asset
              ? `
              <div>
                  <div class='flag' style='background-image: url(../../${player.country.asset});'>
                      <div class="flagname">${player.country.code}</div>
                  </div>
              </div>`
              : ""
          );

          SetInnerHtml(
            $(`.p${t + 1} .flagstate`),
            player.state.asset
              ? `
              <div>
                  <div class='flag' style='background-image: url(../../${player.state.asset});'>
                      <div class="flagname">${player.state.code}</div>
                  </div>
              </div>`
              : ""
          );

          let characterNames = [];

          if(!window.ONLINE_AVATAR && !window.PLAYER_AVATAR){
            for (const [p, player] of Object.values(team.player).entries()) {
              let characters = _.get(player, "character");
              for (const c of Object.values(characters)) {
                if (c.name) characterNames.push(c.name);
              }
            }
          }

          SetInnerHtml(
            $(`.p${t + 1} .character_name`),
            `
                ${characterNames.join(" / ")}
            `
          );

          gsap.to($(`.p${t + 1} .losers_badge`), {
            autoAlpha: team.losers ? 1 : 0,
            overwrite: true,
            duration: 0.8,
          });

          let zIndexMultiplyier = 1;
          if (t == 1) zIndexMultiplyier = -1;

          if (!window.ONLINE_AVATAR && !window.PLAYER_AVATAR) {
            await CharacterDisplay(
              $(`.p${t + 1}.character`),
              {
                source: `score.team.${t + 1}`,
                scale_based_on_parent: true,
                anim_out: {
                  x: zIndexMultiplyier * -800 + "px",
                  z: 0 + "px",
                  stagger: 0.1,
                },
                anim_in: {
                  duration: 0.4,
                  x: zIndexMultiplyier * 0 + "px",
                  z: -30 + "px",
                  ease: "in",
                  autoAlpha: 1,
                  stagger: 0.1,
                },
              },
              event
            );
          } else if (window.ONLINE_AVATAR) {
            SetInnerHtml(
              $(`.p${t + 1}.character`),
              `
                <div class="player_avatar">
                  <div style="background-image: url('${
                    player.online_avatar ? player.online_avatar : "./person.svg"
                  }');">
                  </div>
                </div>
              `,
              {
                anim_out: {
                  x: zIndexMultiplyier * -800 + "px",
                  z: 0 + "px",
                  stagger: 0.1,
                },
                anim_in: {
                  duration: 0.4,
                  x: zIndexMultiplyier * 0 + "px",
                  z: -30 + "px",
                  ease: "in",
                  autoAlpha: 1,
                  stagger: 0.1,
                },
              }
            );
          } else {
            SetInnerHtml(
              $(`.p${t + 1}.character`),
              `
                <div class="player_avatar">
                  <div style="background-image: url('${
                    player.avatar ? '../../'+player.avatar : "./person.svg"
                  }');">
                  </div>
                </div>
              `,
              {
                anim_out: {
                  x: zIndexMultiplyier * -800 + "px",
                  z: 0 + "px",
                  stagger: 0.1,
                },
                anim_in: {
                  duration: 0.4,
                  x: zIndexMultiplyier * 0 + "px",
                  z: -30 + "px",
                  ease: "in",
                  autoAlpha: 1,
                  stagger: 0.1,
                },
              }
            );
          }
        }
      }
    } else {
      const teams = Object.values(data.score.team);
      for (const [t, team] of teams.entries()) {
        let hasTeamName = team.teamName != null && team.teamName != ""

        let playerNames = "";

        let names = [];
        for (const [p, player] of Object.values(team.player).entries()) {
          if (player && player.name) {
            names.push(await Transcript(player.name));
          }
        }
        playerNames = names.join(" / ");

        if(hasTeamName){
          SetInnerHtml(
            $(`.p${t + 1} .name`),
            `
              <span>
                  <div>
                    ${team.teamName}
                  </div>
              </span>
            `
          );
          SetInnerHtml($(`.p${t + 1} .real_name`), playerNames);
        } else {
          SetInnerHtml(
            $(`.p${t + 1} .name`),
            `
              <span>
                  <div>
                    ${playerNames}
                  </div>
              </span>
            `
          );
          SetInnerHtml($(`.p${t + 1} .real_name`), ``);
        }

        gsap.to($(`.p${t + 1} .losers_badge`), {
          autoAlpha: team.losers ? 1 : 0,
          overwrite: true,
          duration: 0.8,
        });

        SetInnerHtml($(`.p${t + 1} > .sponsor_logo`), "");
        SetInnerHtml($(`.p${t + 1} .twitter`), ``);
        SetInnerHtml($(`.p${t + 1} .flagcountry`), "");
        SetInnerHtml($(`.p${t + 1} .flagstate`), "");
        SetInnerHtml($(`.p${t + 1} .pronoun`), "");
        SetInnerHtml($(`.p${t + 1} .seed`), team.seed ? `Seed ${team.seed}` : "");

        let characterNames = [];

        if(!window.ONLINE_AVATAR && !window.PLAYER_AVATAR){
          for (const [p, player] of Object.values(team.player).entries()) {
            let characters = _.get(player, "character");
            for (const c of Object.values(characters)) {
              if (c.name) characterNames.push(c.name);
            }
          }
        }

        SetInnerHtml(
          $(`.p${t + 1} .character_name`),
          `
              ${characterNames.join(" / ")}
          `
        );

        let zIndexMultiplyier = 1;
        if (t == 1) zIndexMultiplyier = -1;

        if (!window.ONLINE_AVATAR && !window.PLAYER_AVATAR) {
          await CharacterDisplay(
            $(`.p${t + 1}.character`),
            {
              source: `score.team.${t + 1}`,
              scale_based_on_parent: true,
              anim_out: {
                x: zIndexMultiplyier * -800 + "px",
                z: 0 + "px",
                stagger: 0.1,
              },
              anim_in: {
                duration: 0.4,
                x: zIndexMultiplyier * 0 + "px",
                z: -30 + "px",
                ease: "in",
                autoAlpha: 1,
                stagger: 0.1,
              },
            },
            event
          );
        } else if (window.ONLINE_AVATAR) {
          let avatars_html = "";
          for (const [p, player] of Object.values(team.player).entries()) {
            if (player)
              avatars_html += `<div style="background-image: url('${
                player.online_avatar ? player.online_avatar : "./person.svg"
              }');"></div>`;
          }
          SetInnerHtml(
            $(`.p${t + 1}.character`),
            `
              <div class="player_avatar">
                ${avatars_html}
              </div>
            `,
            {
              anim_out: {
                x: zIndexMultiplyier * -800 + "px",
                z: 0 + "px",
                stagger: 0.1,
              },
              anim_in: {
                duration: 0.4,
                x: zIndexMultiplyier * 0 + "px",
                z: -30 + "px",
                ease: "in",
                autoAlpha: 1,
                stagger: 0.1,
              },
            }
          );
        } else {
          let avatars_html = "";
          for (const [p, player] of Object.values(team.player).entries()) {
            if (player)
              avatars_html += `<div style="background-image: url('${
                player.avatar ? '../../'+player.avatar : "./person.svg"
              }');"></div>`;
          }
          SetInnerHtml(
            $(`.p${t + 1}.character`),
            `
              <div class="player_avatar">
                ${avatars_html}
              </div>
            `,
            {
              anim_out: {
                x: zIndexMultiplyier * -800 + "px",
                z: 0 + "px",
                stagger: 0.1,
              },
              anim_in: {
                duration: 0.4,
                x: zIndexMultiplyier * 0 + "px",
                z: -30 + "px",
                ease: "in",
                autoAlpha: 1,
                stagger: 0.1,
              },
            }
          );
        }
      }
    }

    SetInnerHtml($(`.p1 .score`), String(data.score.team["1"].score));
    SetInnerHtml($(`.p2 .score`), String(data.score.team["2"].score));

    SetInnerHtml($(".tournament"), data.tournamentInfo.tournamentName);
    SetInnerHtml($(".event"), data.tournamentInfo.eventName);
    SetInnerHtml($(".match"), data.score.match);

    SetInnerHtml(
      $(".phase:not(.container)"),
      data.score.phase ? data.score.phase : ""
    );
  
    SetInnerHtml(
      $(".container .best_of"),
      data.score.best_of_text ? data.score.best_of_text : ""
    );

    let stage = null;

    if (_.get(data, "score.stage_strike.selectedStage")) {
      let stageId = _.get(data, "score.stage_strike.selectedStage");

      let allStages = _.get(data, "score.ruleset.neutralStages", []).concat(
        _.get(data, "score.ruleset.counterpickStages", [])
      );

      stage = allStages.find((s) => s.codename == stageId);
    }

    if (
      stage &&
      _.get(data, "score.stage_strike.selectedStage") !=
        _.get(oldData, "score.stage_strike.selectedStage")
    ) {
      gsap.fromTo(
        $(`.stage`),
        { scale: 1.6 },
        { scale: 1.2, duration: 0.6, ease: "power2.out" }
      );
    }

    SetInnerHtml(
      $(`.stage`),
      stage
        ? `
        <div>
            <div class='' style='background-image: url(../../${stage.path});'>
            </div>
        </div>`
        : ""
    );
  };
});
