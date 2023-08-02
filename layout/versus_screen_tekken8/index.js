LoadEverything().then(() => {
  let startingAnimation = gsap
    .timeline({ paused: true })
    .to([".logo"], { duration: 0.8, top: 160 }, 0)
    .to([".logo"], { duration: 0.8, scale: 0.4 }, 0)
    .from(
      ".p1.character_name",
      {
        duration: 2.3,
        x: "-100px",
        autoAlpha: 0,
      },
      0
    )
    .from(
      ".p2.character_name",
      {
        duration: 2.3,
        x: "+100px",
        autoAlpha: 0,
      },
      0
    )
    .from(
      ".p1.character",
      {
        duration: 0.13,
        x: "-800px",
        autoAlpha: 0,
        ease: "power2.out",
      },
      2
    )
    .from(
      ".p2.character",
      {
        duration: 0.13,
        x: "+800px",
        autoAlpha: 0,
        ease: "power2.out",
      },
      2
    )
    .from(
      [".tournament"],
      { duration: 0.6, opacity: "0", ease: "power2.inOut" },
      0.2
    )
    .from(
      [".match"],
      { duration: 0.6, opacity: "0", ease: "power2.inOut" },
      0.4
    )
    .from(
      [".phase_best_of"],
      { duration: 0.6, opacity: "0", ease: "power2.inOut" },
      0.6
    )
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
    .fromTo(
      [".vs1"],
      { opacity: 0, scale: 1.2 },
      { opacity: 0.8, ease: "in", duration: 2.1 },
      0
    )
    .to([".vs1"], { duration: 0.03, opacity: "1", scale: 1 }, 2.1)
    .from([".vs2"], { duration: 0.01, opacity: "0" }, 2.13)
    .to(
      [".vs2"],
      {
        opacity: 0,
        scale: 1.2,
        ease: "power2.out",
        duration: 1,
      },
      2.4
    )
    .to("body", { x: "+20", y: "-10", duration: 0.1 }, 2.2)
    .to("body", { x: "-5", y: "+2", duration: 0.1 }, 2.3)
    .to("body", { x: 0, y: 0, duration: 0.1 }, 2.4);

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
                  ${team.losers ? "<span class='losers'>L</span>" : ""}
              </span>
            `
          );

          SetInnerHtml($(`.p${t + 1} .pronoun`), player.pronoun);

          SetInnerHtml(
            $(`.p${t + 1} .sponsor_logo`),
            player.sponsor_logo
              ? `
                <div class='sponsor-logo' style='background-image: url(../../${player.sponsor_logo})'></div>
                `
              : ""
          );

          SetInnerHtml($(`.p${t + 1} .seed`), player.seed ? `Seed ${player.seed}` : "");

          SetInnerHtml($(`.p${t + 1} .real_name`), player.real_name);

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
                <div class='flag'>
                  <div class='flagimage' style='background-image: url(../../${player.country.asset});'></div>
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
                <div class='flag'>
                  <div class='flagimage' style='background-image: url(../../${player.state.asset});'></div>
                  <div class="flagname">${player.state.code}</div>
                </div>
              </div>`
              : ""
          );

          let characterNames = [];

          if(window.ONLINE_AVATAR || window.PLAYER_AVATAR){
            characterNames = [player.name]
          } else {
            let characters = _.get(player, "character");
            for (const c of Object.values(characters)) {
              if (c.name) characterNames.push(c.name);
            }
          }

          SetInnerHtml(
            $(`.p${t + 1}.character_name`),
            `
              ${characterNames.join("<br/>")}
          `
          );

          $(`.p${t + 1}.character_name`).css({"font-size": 500/characterNames.length})

          let zIndexMultiplyier = 1;
          if (t == 1) zIndexMultiplyier = -1;

          if (!window.ONLINE_AVATAR && !window.PLAYER_AVATAR) {
            await CharacterDisplay(
              $(`.p${t + 1}.character > div`),
              {
                source: `score.team.${t + 1}`,
                scale_based_on_parent: true,
                anim_out: {
                  x: -zIndexMultiplyier * 100 + "%",
                  stagger: 0.1,
                },
                anim_in: {
                  x: 0,
                  duration: 1,
                  ease: "expo.out",
                  autoAlpha: 1,
                  stagger: 0.2,
                },
              },
              event
            );
          } else if (window.ONLINE_AVATAR) {
            SetInnerHtml(
              $(`.p${t + 1}.character > div`),
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
                  x: -zIndexMultiplyier * 100 + "%",
                  stagger: 0.1,
                },
                anim_in: {
                  x: 0,
                  duration: 1,
                  ease: "expo.out",
                  autoAlpha: 1,
                  stagger: 0.2,
                },
              }
            );
          } else {
            SetInnerHtml(
              $(`.p${t + 1}.character > div`),
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
                  x: -zIndexMultiplyier * 100 + "%",
                  stagger: 0.1,
                },
                anim_in: {
                  x: 0,
                  duration: 1,
                  ease: "expo.out",
                  autoAlpha: 1,
                  stagger: 0.2,
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
                  ${team.losers ? "<span class='losers'>L</span>" : ""}
              </span>
            `
          );
          SetInnerHtml($(`.p${t + 1} .real_name`), ``);
        }

        SetInnerHtml($(`.p${t + 1} > .sponsor_logo`), "");

        SetInnerHtml($(`.p${t + 1} .twitter`), ``);

        SetInnerHtml($(`.p${t + 1} .flagcountry`), "");

        SetInnerHtml($(`.p${t + 1} .flagstate`), "");

        SetInnerHtml($(`.p${t + 1} .pronoun`), "");

        SetInnerHtml($(`.p${t + 1} .seed`), team.seed ? `Seed ${team.seed}` : "");

        let characterNames = [];

        if(window.ONLINE_AVATAR || window.PLAYER_AVATAR){
          for (const [p, player] of Object.values(team.player).entries()) {
            if (player.name) characterNames.push(player.name);
          }
        } else {
          for (const [p, player] of Object.values(team.player).entries()) {
            let characters = _.get(player, "character");
            for (const c of Object.values(characters)) {
              if (c.name) characterNames.push(c.name);
            }
          }
        }

        SetInnerHtml(
          $(`.p${t + 1}.character_name`),
          `
            ${characterNames.join("<br/>")}
        `
        );

        $(`.p${t + 1}.character_name`).css({"font-size": 500/characterNames.length})

        let zIndexMultiplyier = 1;
        if (t == 1) zIndexMultiplyier = -1;

        if (!window.ONLINE_AVATAR && !window.PLAYER_AVATAR) {
          await CharacterDisplay(
            $(`.p${t + 1}.character > div`),
            {
              source: `score.team.${t + 1}`,
              scale_based_on_parent: true,
              anim_out: {
                x: -zIndexMultiplyier * 100 + "%",
                stagger: 0.1,
              },
              anim_in: {
                x: 0,
                duration: 1,
                ease: "expo.out",
                autoAlpha: 1,
                stagger: 0.2,
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
            $(`.p${t + 1}.character > div`),
            `
              <div class="player_avatar">
                ${avatars_html}
              </div>
            `,
            {
              anim_out: {
                x: -zIndexMultiplyier * 100 + "%",
                stagger: 0.1,
              },
              anim_in: {
                x: 0,
                duration: 1,
                ease: "expo.out",
                autoAlpha: 1,
                stagger: 0.2,
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
            $(`.p${t + 1}.character > div`),
            `
              <div class="player_avatar">
                ${avatars_html}
              </div>
            `,
            {
              anim_out: {
                x: -zIndexMultiplyier * 100 + "%",
                stagger: 0.1,
              },
              anim_in: {
                x: 0,
                duration: 1,
                ease: "expo.out",
                autoAlpha: 1,
                stagger: 0.2,
              },
            }
          );
        }
      }
    }

    SetInnerHtml($(`.p1 .score`), String(data.score.team["1"].score));
    SetInnerHtml($(`.p2 .score`), String(data.score.team["2"].score));

    SetInnerHtml($(".tournament"), data.tournamentInfo.tournamentName);
    SetInnerHtml($(".match"), data.score.match);

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
        { scale: 2 },
        { scale: 1.2, duration: 0.8, ease: "power2.out" }
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

    SetInnerHtml(
      $(".phase_best_of"),
      data.score.phase +
        (data.score.best_of_text ? ` | ${data.score.best_of_text}` : "")
    );
  };
});
