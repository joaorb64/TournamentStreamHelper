LoadEverything().then(() => {
  // Change this to the name of the assets pack you want to use
  // It's basically the folder name: user_data/games/game/ASSETPACK
  var ASSET_TO_USE = "full";

  // Change this to select wether to flip P2 character asset or not
  // Set it to true or false
  var FLIP_P2_ASSET = true;

  // Amount of zoom to use on the assets. Use 1 for 100%, 1.5 for 150%, etc.
  var zoom = 1.2;

  // Where to center character eyesights. [ 0.0 - 1.0 ]
  var EYESIGHT_CENTERING = { x: 0.5, y: 0.4 };

  let startingAnimation = gsap
    .timeline({ paused: true })
    .to([".logo"], { duration: 0.8, top: 160 }, 0)
    .to([".logo"], { duration: 0.8, scale: 0.4 }, 0)
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
    .from([".vs1"], { duration: 0.1, opacity: "0", scale: 10, ease: "in" }, 1.2)
    .from([".vs2"], { duration: 0.01, opacity: "0" }, 1.3)
    .to([".vs2"], { opacity: 0, scale: 2, ease: "power2.out" }, 1.31)
    .from([".p1.container"], { duration: 1, x: "-200px", ease: "out" }, 0)
    .from([".p2.container"], { duration: 1, x: "200px", ease: "out" }, 0);

  Start = async (event) => {
    startingAnimation.restart();
  };

  Update = async (event) => {
    let data = event.data;
    let oldData = event.oldData;

    let isDoubles = Object.keys(data.score.team["1"].player).length == 2;

    if (!isDoubles) {
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
            $(`.p${t + 1} > .sponsor_logo`),
            player.sponsor_logo
              ? `
                <div class='sponsor_logo' style='background-image: url(../../${player.sponsor_logo})'></div>
                `
              : ""
          );

          SetInnerHtml($(`.p${t + 1} .real_name`), `${player.real_name}`);

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

          let zIndexMultiplyier = 1;
          if (t == 1) zIndexMultiplyier = -1;

          await CharacterDisplay(
            $(`.p${t + 1}.character`),
            {
              source: `score.team.${t + 1}`,
              custom_center: [0.5, 0.4],
              custom_element: -2,
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
        }
      }
    } else {
      const teams = Object.values(data.score.team);
      for (const [t, team] of teams.entries()) {
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
          $(`.p${t + 1} .name`),
          `
            <span>
                <div>
                  ${teamName}
                </div>
                ${team.losers ? "<span class='losers'>L</span>" : ""}
            </span>
          `
        );

        SetInnerHtml($(`.p${t + 1} > .sponsor_logo`), "");

        SetInnerHtml($(`.p${t + 1} .real_name`), ``);

        SetInnerHtml($(`.p${t + 1} .twitter`), ``);

        SetInnerHtml($(`.p${t + 1} .flagcountry`), "");

        SetInnerHtml($(`.p${t + 1} .flagstate`), "");

        let zIndexMultiplyier = 1;
        if (t == 1) zIndexMultiplyier = -1;

        await CharacterDisplay(
          $(`.p${t + 1}.character`),
          {
            source: `score.team.${t + 1}`,
            custom_center: [0.5, 0.4],
            custom_element: -2,
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
