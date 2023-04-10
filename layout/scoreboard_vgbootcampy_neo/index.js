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
    setInterval(UpdateMatch, 9000);
    setInterval(UpdateTwitter, 9000);
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
          SetInnerHtml(
            $(`.p${t + 1}.container .name`),
            `
              <span class="sponsor">
                ${player.team ? player.team.toUpperCase() : ""}
              </span>
              ${player.name ? await Transcript(player.name.toUpperCase()) : ""}
              ${team.losers ? "(L)" : ""}
            `
          );

          SetInnerHtml(
            $(`.p${t + 1}.container .flagcountry`),
            player.country.asset
              ? `<div class='flag' style='background-image: url(../../${player.country.asset.toLowerCase()})'></div>`
              : ""
          );

          let score = [data.score.score_left, data.score.score_right];

          SetInnerHtml($(`.p${t + 1}.container .score`), String(team.score));
        }
      }
    }

    // Only on first update
    if (Object.keys(oldData).length == 0) {
      UpdateMatch();
      UpdateTwitter();
    }
  };

  const delay = (ms) => new Promise((res) => setTimeout(res, ms));

  async function UpdateMatch() {
    oldData = data;
    data = await getData();

    const tournamentContainer = document.querySelector(".tournament_container");

    if (
      data.score.best_of == 0 &&
      (data.score.match == undefined || String(data.score.match) == "")
    ) {
      tournamentContainer.classList.add("hidden");
      tournamentContainer.classList.remove("unhidden");
    } else {
      tournamentContainer.classList.add("unhidden");
      tournamentContainer.classList.remove("hidden");

      if (
        data.score.best_of == 0 &&
        !(data.score.match == undefined || String(data.score.match) == "")
      ) {
        SetInnerHtml($(".match"), data.score.match.toUpperCase());
      } else if (
        data.score.best_of > 0 &&
        (data.score.match == undefined || String(data.score.match) == "")
      ) {
        SetInnerHtml($(".match"), "BEST OF " + data.score.best_of);
      } else {
        SetInnerHtml($(".match"), "BEST OF " + data.score.best_of);
        SetInnerHtml($(".match"), data.score.match.toUpperCase());
      }
    }
  }

  async function UpdateTwitter() {
    oldData = data;
    data = await getData();

    [data.score.team["1"], data.score.team["2"]].forEach((team, t) => {
      [team.player["1"]].forEach((player, p) => {
        if (player) {
          const playerTwitter = document.querySelector(`.p${t + 1}.twitter`);
          if (
            (player.twitter == undefined || String(player.twitter) == "") &&
            (player.pronoun == undefined || String(player.pronoun) == "")
          ) {
            playerTwitter.classList.add("hidden");
            playerTwitter.classList.remove("unhidden");
          } else {
            playerTwitter.classList.add("unhidden");
            playerTwitter.classList.remove("hidden");

            if (
              (player.twitter == undefined || String(player.twitter) == "") &&
              !(player.pronoun == undefined || String(player.pronoun) == "")
            ) {
              SetInnerHtml(
                $(`.p${t + 1}.twitter`),
                player.pronoun.toUpperCase()
              );
            } else if (
              !(player.twitter == undefined || String(player.twitter) == "") &&
              (player.pronoun == undefined || String(player.pronoun) == "")
            ) {
              SetInnerHtml(
                $(`.p${t + 1}.twitter`),
                player.twitter
                  ? `<span class="twitter_logo"></span>${
                      "@" + String(player.twitter).toUpperCase()
                    }`
                  : ""
              );
            } else {
              SetInnerHtml(
                $(`.p${t + 1}.twitter`),
                player.pronoun.toUpperCase()
              );
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
      });
    });
  }
});
