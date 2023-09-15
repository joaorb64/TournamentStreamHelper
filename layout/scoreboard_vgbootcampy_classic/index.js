LoadEverything().then(() => {
  gsap.config({ nullTargetWarn: false, trialWarn: false });

  let p1Twitter = "";
  let p2Twitter = "";
  let p1Pronoun = "";
  let p2Pronoun = "";
  let newP1Twitter = "";
  let newP2Twitter = "";
  let newP1Pronoun = "";
  let newP2Pronoun = "";
  let savedBestOf = 0;
  let savedMatch = "";
  let firstTime = true;

  let intervalID = "";

  let scoreboardNumber = 1;

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
    intervalID = setInterval(UpdateTwitterMatch, 9000);
    setInterval(TwitterPronounChecker, 100);
    setInterval(matchChecker, 100);
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
              <span>
                <span class="sponsor">
                  ${player.team ? player.team.toUpperCase() : ""}
                </span>
                ${
                  player.name ? await Transcript(player.name.toUpperCase()) : ""
                }
                ${team.losers ? "(L)" : ""}
              </span>
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
            $(`.p${t + 1}.container .flagcountry`),
            player.country.asset && Object.keys(team.player).length == 1
              ? `<div class='flag' style='background-image: url(../../${player.country.asset.toLowerCase()})'></div>`
              : ""
          );

          SetInnerHtml(
            $(`.p${t + 1} .sponsor-container`),
            player.sponsor_logo && Object.keys(team.player).length == 1
              ? `<div class='sponsor-logo' style='background-image: url(../../${player.sponsor_logo})'></div>`
              : ``
          );

          let score = [data.score[scoreboardNumber].score_left, data.score[scoreboardNumber].score_right];

          SetInnerHtml($(`.p${t + 1}.score`), String(team.score));

          if (!TwitterPronounChecker()) {
            SetInnerHtml($(`.p${t + 1}.twitter`), player.pronoun.toUpperCase());
          }
        }
      }
    }

    // Only on first update
    if (Object.keys(oldData).length == 0) {
      UpdateMatch();
      UpdateTwitter();
      firstTime = false;
    }
  };

  async function UpdateTwitterMatch() {
    UpdateTwitter();
    UpdateMatch();
  }

  async function UpdateMatch() {
    const tournamentContainer = document.querySelector(".tournament_container");

    if (!(data.score[scoreboardNumber].best_of || data.score[scoreboardNumber].match)) {
      tournamentContainer.classList.add("hidden");
      tournamentContainer.classList.remove("unhidden");
    } else {
      tournamentContainer.classList.add("unhidden");
      tournamentContainer.classList.remove("hidden");

      if (!data.score[scoreboardNumber].best_of && data.score[scoreboardNumber].match) {
        SetInnerHtml($(".match"), data.score[scoreboardNumber].match.toUpperCase());
      } else if (data.score.best_of && !data.score[scoreboardNumber].match) {
        SetInnerHtml($(".match"), data.score[scoreboardNumber].best_of_text.toUpperCase());
      } else if (savedMatch != data.score[scoreboardNumber].match) {
        SetInnerHtml($(".match"), data.score[scoreboardNumber].match.toUpperCase());
      } else if (savedBestOf != data.score[scoreboardNumber].best_of) {
        SetInnerHtml($(".match"), data.score[scoreboardNumber].match.toUpperCase());
      } else {
        SetInnerHtml($(".match"), data.score[scoreboardNumber].best_of_text.toUpperCase());
        SetInnerHtml($(".match"), data.score[scoreboardNumber].match.toUpperCase());
      }
    }
    savedBestOf = data.score[scoreboardNumber].best_of;
    savedMatch = data.score[scoreboardNumber].match;
  }

  async function UpdateTwitter() {
    changeInP1 = false;
    changeInP2 = false;

    [data.score[scoreboardNumber].team["1"], data.score[scoreboardNumber].team["2"]].forEach((team, t) => {
      [team.player["1"]].forEach((player, p) => {
        if (player) {
          if (t == 0) {
            newP1Twitter = player.twitter;
            newP1Pronoun = player.pronoun;
          }

          if (t == 1) {
            newP2Twitter = player.twitter;
            newP2Pronoun = player.pronoun;
          }
        }
      });
      if (newP1Twitter != p1Twitter || newP1Pronoun != p1Pronoun) {
        changeInP1 = true;
      }

      if (newP2Twitter != p2Twitter || newP2Pronoun != p2Pronoun) {
        changeInP2 = true;
      }
    });

    [data.score[scoreboardNumber].team["1"], data.score[scoreboardNumber].team["2"]].forEach((team, t) => {
      [team.player["1"]].forEach((player, p) => {
        if (player) {
          const playerTwitter = document.querySelector(`.p${t + 1}.twitter`);

          if (
            !(player.twitter || player.pronoun) ||
            Object.values(team.player).length != 1
          ) {
            playerTwitter.classList.add("hidden");
            playerTwitter.classList.remove("unhidden");
          } else {
            playerTwitter.classList.add("unhidden");
            playerTwitter.classList.remove("hidden");

            if (!player.twitter && player.pronoun) {
              SetInnerHtml(
                $(`.p${t + 1}.twitter`),
                player.pronoun.toUpperCase()
              );
            }

            if (player.twitter && !player.pronoun) {
              SetInnerHtml(
                $(`.p${t + 1}.twitter`),
                player.twitter
                  ? `<span class="twitter_logo"></span>${
                      "@" + String(player.twitter).toUpperCase()
                    }`
                  : ""
              );
            }

            if (changeInP1 || changeInP2) {
              if (player.twitter) {
                SetInnerHtml(
                  $(`.p${t + 1}.twitter`),
                  player.twitter
                    ? `<span class="twitter_logo"></span>${
                        "@" + String(player.twitter).toUpperCase()
                      }`
                    : ""
                );
              }
            } else {
              if (player.pronoun) {
                SetInnerHtml(
                  $(`.p${t + 1}.twitter`),
                  player.pronoun.toUpperCase()
                );
              }
              if (player.twitter) {
                SetInnerHtml(
                  $(`.p${t + 1}.twitter`),
                  player.twitter
                    ? `<span class="twitter_logo"></span>${
                        "@" + String(player.twitter).toUpperCase()
                      }`
                    : ""
                );
              }
            }
          }
          if (t == 0) {
            p1Twitter = player.twitter;
            p1Pronoun = player.pronoun;
          }

          if (t == 1) {
            p2Twitter = player.twitter;
            p2Pronoun = player.pronoun;
          }
        }
      });
    });
  }

  async function TwitterPronounChecker() {
    let refreshNeeded = false;
    [data.score[scoreboardNumber].team["1"], data.score[scoreboardNumber].team["2"]].forEach((team, t) => {
      [team.player["1"]].forEach((player, p) => {
        if (
          t == 0 &&
          !(p1Twitter == player.twitter && p1Pronoun == player.pronoun)
        ) {
          refreshNeeded = true;
        } else if (
          t == 1 &&
          !(p2Twitter == player.twitter && p2Pronoun == player.pronoun)
        ) {
          refreshNeeded = true;
        }
      });
    });
    if (refreshNeeded && !firstTime) {
      UpdateTwitter();
      resetIntervals();
    }
    refreshNeeded = false;
  }

  function resetIntervals() {
    clearInterval(intervalID);
    intervalID = setInterval(UpdateTwitterMatch, 9000);
  }

  async function matchChecker() {
    let refreshNeeded = false;

    if (
      !(savedBestOf == data.score[scoreboardNumber].best_of
        && savedMatch == data.score[scoreboardNumber].match)
    ) {
      refreshNeeded = true;
    }

    if (refreshNeeded && !firstTime) {
      UpdateMatch();
      resetIntervals();
    }
    refreshNeeded = false;
  }
});
