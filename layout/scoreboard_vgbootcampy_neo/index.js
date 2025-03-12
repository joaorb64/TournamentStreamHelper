LoadEverything().then(() => {

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
  let player1 = "";
  let player2 = "";
  let team1Name = "";
  let team2Name = "";
  let teamNameInWinners = localStorage.getItem("teamNameInWinners");
  if (!teamNameInWinners) teamNameInWinners = "";
  let team1Losers = false;
  let team2Losers = false;

  let startingAnimation = gsap
    .timeline({ paused: true })
    .from([".logo"], { duration: 0.5, autoAlpha: 0, ease: "power2.inOut" }, 0.5)
    .from(
      [".anim_container_outer"],
      {
        duration: 1,
        width: "168px",
        ease: "power2.inOut",
      },
      1
    )
    .from(
      [".p1.twitter_container"],
      {
        duration: 0.75,
        x: "-373px",
        ease: "power4.Out",
      },
      "<25%"
    )
    .from(
      [".p2.twitter_container"],
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
      data.score[window.scoreboardNumber].team["1"],
      data.score[window.scoreboardNumber].team["2"],
    ].entries()) {
      for (const [p, player] of [team.player["1"]].entries()) {
        if (player) {

          if (Object.keys(team.player).length == 1) {
            DisplayName(t, team, player)
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
            DisplayTeamName(t, team, teamName);
          }

          SetInnerHtml($(`.p${t + 1} .score`), String(team.score));

          SetInnerHtml(
            $(`.p${t + 1}.container .flagcountry`),
            player.country.asset && Object.keys(team.player).length == 1
              ? `<div class='flag' style="background-image: url('${player.country.asset.toLowerCase()}')"></div>`
              : ""
          );

          DisplaySponsorLogo(t, player, team);
          
        }
        if (team.color) {
          document
            .querySelector(":root")
            .style.setProperty(`--p${t + 1}-score-bg-color`, team.color);
        }
        UpdateColor(t);
      }
    }

    // Only on first update
    if (Object.keys(oldData).length == 0) {
      UpdateMatch();
      UpdateTwitter();
      firstTime = false;
    }
  };

  async function DisplaySponsorLogo(t, player, team) {
    await SetInnerHtml(
      $(`.p${t + 1} .sponsor_container`),
      player.sponsor_logo && Object.keys(team.player).length == 1
        ? `<div class='sponsor_logo' style="background-image: url('../../${player.sponsor_logo}')"></div>`
        : ``
    );
    let element = document.querySelector(`.p${t + 1} .sponsor_container`);
    let width = parseFloat(window.getComputedStyle(element).width);
    let styleSheet = document.styleSheets[1];
    if (!width) {
      if (t == 0) {
        styleSheet.insertRule(`.p${t+ 1} .sponsor_logo { margin-left: 0px; !important}`, styleSheet.cssRules.length);
      }
      if (t == 1) {
        styleSheet.insertRule(`.p${t+ 1} .sponsor_logo { margin-right: 0px; !important}`, styleSheet.cssRules.length);
      }
    } else {
      if (t == 0) {
        styleSheet.insertRule(`.p${t+ 1} .sponsor_logo { margin-left: 12px; !important}`, styleSheet.cssRules.length);
      }
      if (t == 1) {
        styleSheet.insertRule(`.p${t+ 1} .sponsor_logo { margin-right: 12px; !important}`, styleSheet.cssRules.length);
      }
    }
  }

  async function UpdateTwitterMatch() {
    UpdateTwitter();
    UpdateMatch();
  }

  async function UpdateMatch() {
    const tournamentContainer = document.querySelector(".tournament_container");

    if (!(data.score[window.scoreboardNumber].best_of
      || data.score[window.scoreboardNumber].match)) {
      tournamentContainer.classList.add("hidden");
      tournamentContainer.classList.remove("unhidden");
    } else {
      tournamentContainer.classList.add("unhidden");
      tournamentContainer.classList.remove("hidden");

      if (!data.score[window.scoreboardNumber].best_of
        && data.score[window.scoreboardNumber].match) {
        SetInnerHtml($(".match"), data.score[window.scoreboardNumber].match.toUpperCase());
      } else if (data.score[window.scoreboardNumber].best_of
        && !data.score[window.scoreboardNumber].match) {
        SetInnerHtml($(".match"), data.score[window.scoreboardNumber].best_of_text.toUpperCase());
      } else if (savedMatch != data.score[window.scoreboardNumber].match) {
        SetInnerHtml($(".match"), data.score[window.scoreboardNumber].match.toUpperCase());
      } else if (savedBestOf != data.score[window.scoreboardNumber].best_of) {
        SetInnerHtml($(".match"), data.score[window.scoreboardNumber].match.toUpperCase());
      } else {
        SetInnerHtml($(".match"), data.score[window.scoreboardNumber].best_of_text.toUpperCase());
        SetInnerHtml($(".match"), data.score[window.scoreboardNumber].match.toUpperCase());
      }
    }
    savedBestOf = data.score[window.scoreboardNumber].best_of;
    savedMatch = data.score[window.scoreboardNumber].match;
  }

  async function UpdateTwitter() {
    changeInP1 = false;
    changeInP2 = false;

    [data.score[window.scoreboardNumber].team["1"], data.score[window.scoreboardNumber].team["2"]].forEach((team, t) => {
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

    [data.score[window.scoreboardNumber].team["1"]
    , data.score[window.scoreboardNumber].team["2"]].forEach((team, t) => {
      [team.player["1"]].forEach((player, p) => {
        if (player) {
          const playerTwitter = document.querySelector(`.p${t + 1}.twitter_container`);

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
                $(`.p${t + 1} .twitter`),
                player.pronoun.toUpperCase()
              );
            }

            if (player.twitter && !player.pronoun) {
              SetInnerHtml(
                $(`.p${t + 1} .twitter`),
                player.twitter
                  ? `<span class="twitter_logo"></span>${
                      "@" + String(player.twitter)
                    }`
                  : ""
              );
            }

            if (changeInP1 || changeInP2) {
              if (player.twitter) {
                SetInnerHtml(
                  $(`.p${t + 1} .twitter`),
                  player.twitter
                    ? `<span class="twitter_logo"></span>${
                        "@" + String(player.twitter)
                      }`
                    : ""
                );
              }
            } else {
              if (player.pronoun) {
                SetInnerHtml(
                  $(`.p${t + 1} .twitter`),
                  player.pronoun.toUpperCase()
                );
              }
              if (player.twitter) {
                SetInnerHtml(
                  $(`.p${t + 1} .twitter`),
                  player.twitter
                    ? `<span class="twitter_logo"></span>${
                        "@" + String(player.twitter)
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
    [data.score[window.scoreboardNumber].team["1"]
    , data.score[window.scoreboardNumber].team["2"]].forEach((team, t) => {
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
      !(savedBestOf == data.score[window.scoreboardNumber].best_of
        && savedMatch == data.score[window.scoreboardNumber].match)
    ) {
      refreshNeeded = true;
    }

    if (refreshNeeded && !firstTime) {
      UpdateMatch();
      resetIntervals();
    }
    refreshNeeded = false;
  }

  async function UpdateColor(t) {
    let styleSheet = document.styleSheets[1];

    var divs = document.getElementsByClassName(`p${t + 1} container`);

    var div = divs[0];

    var inner_container = div.querySelector(".inner_container");

    var score_container = div.querySelector(".score_container");
    var score_element = score_container.querySelector(".score");

    var name_container = inner_container.querySelector(".name_container");
    var name_element = name_container.querySelector(".name");

    var twitter_element = document.querySelector(`.p${t + 1} .twitter`);

    // Get the background color of the div
    var color = window
      .getComputedStyle(div, null)
      .getPropertyValue("background-color");

    var components = color.match(/^rgb\((\d+),\s*(\d+),\s*(\d+)\)$/);

    if (components) {
      // Extract the individual RGB components
      var red = parseInt(components[1]);
      var green = parseInt(components[2]);
      var blue = parseInt(components[3]);

      const intensity = red * 0.299 + green * 0.587 + blue * 0.114;

      if (intensity > 142) {

        // Change the text color
        score_element.style.color = "rgb(18, 18, 18, 0.8)";
        twitter_element.style.color = "rgb(18, 18, 18, 0.8)";
        styleSheet.insertRule(`.p${t+ 1} .twitter_logo { background:rgba(18, 18, 18, 0.8) !important}`, styleSheet.cssRules.length);
        name_element.style.color = "white";
        inner_container.style.backgroundColor = "rgba(18, 18, 18, 0.8)";

      } else if (intensity > 95) {

        // Change the text color
        score_element.style.color = "white";
        twitter_element.style.color = "white";
        styleSheet.insertRule(`.p${t+ 1} .twitter_logo { background: white!important}`, styleSheet.cssRules.length);
        name_element.style.color = "white";
        inner_container.style.backgroundColor = "rgba(18, 18, 18, 0.8)";

      } else if (intensity <= 80) {

        // Change the text color
        score_element.style.color = "white";
        twitter_element.style.color = "white";
        styleSheet.insertRule(`.p${t+ 1} .twitter_logo { background: white !important}`, styleSheet.cssRules.length);
        name_element.style.color = "rgb(18, 18, 18, 0.8)";
        inner_container.style.backgroundColor = "rgba(255, 255, 255, 0.8)";
      }
    }
  }

  /**
   * Checks to see whether the properties and their values of obj1 are the same as those of obj2
   * Created this function with the help of ChatGPT, modified to make it recursive and fit the need of the overlay.
   * @param obj1 Object 1 to compare
   * @param obj2 Object 2 to compare
   * @returns boolean of whether the properties and their values of obj1 are the same as those of obj2
   */
  function compareObjects(obj1, obj2) {
    // Get the property names of obj1
    const obj1Keys = Object.keys(obj1).sort();

    // Loop through the properties of obj1
    for (let key of obj1Keys) {
      if (key !== "character" && key !== "mains" && key !== "id" && key !== "mergedName" && key !== "mergedOnlyName" && key != "seed" && key != "") {
        // Check if the property exists in obj2
        if (!obj2.hasOwnProperty(key)) {
          return false;
        }
        // Check if the values of the properties are the same
        // Check to see if there is an object inside the object
        if (typeof obj1[key] == "object" && obj1[key] && obj2[key]) {
          // If an inner object of obj1 is not equal to the inner object of obj2, then we return false to avoid any more comparisons
          if (!compareObjects(obj1[key], obj2[key])) return false;
          // If the primitive types are not equal to each other, then we return false here as well
        } else if (obj1[key] !== obj2[key]) {
          return false;
        }
      }
    }
    // If all properties and their values are the same, return true
    return true;
  }

  async function DisplayName(t, team, player) {

    const retrievedJsonString = localStorage.getItem("playerInWinners");
    const playerInWinners = JSON.parse(retrievedJsonString);

    if (t == 0) {
      player1 = player
      team1Losers = team.losers
    }

    if (t == 1) {
      player2 = player
      team2Losers = team.losers
    }

      // If the player and the opponent are both in losers
    if (team1Losers && team2Losers) {

      // If P1 was in winners
      if (compareObjects(playerInWinners, player1)) {

        // P1 has (WL)
        SetInnerHtml(
          $(`.p1.container .name`),
          `
          <span>
            <span class="sponsor">
              ${player1.team ? player1.team.replace(/\s*[\|\/\\]\s*/g, ' '): ""}
            </span>
            ${
              player1.name ? await Transcript(player1.name) : ""
            }
            ${"(WL)"}
          </span>
          `
        );

        // P2 has (L)
        SetInnerHtml(
          $(`.p2.container .name`),
          `
          <span>
            <span class="sponsor">
              ${player2.team ? player2.team.replace(/\s*[\|\/\\]\s*/g, ' '): ""}
            </span>
            ${
              player2.name ? await Transcript(player2.name) : ""
            }
            ${"(L)"}
          </span>
          `
        );

      // If P2 was in winners
      } else if (compareObjects(playerInWinners, player2)) { 

        // P1 has (L)
        SetInnerHtml(
          $(`.p1.container .name`),
          `
          <span>
            <span class="sponsor">
              ${player1.team ? player1.team.replace(/\s*[\|\/\\]\s*/g, ' '): ""}
            </span>
            ${
              player1.name ? await Transcript(player1.name) : ""
            }
            ${"(L)"}
          </span>
          `
        );

        // P2 has (WL)
        SetInnerHtml(
          $(`.p2.container .name`),
          `
          <span>
            <span class="sponsor">
              ${player2.team ? player2.team.replace(/\s*[\|\/\\]\s*/g, ' '): ""}
            </span>
            ${
              player2.name ? await Transcript(player2.name) : ""
            }
            ${"(WL)"}
          </span>
          `
        );

      // If neither of them were in winners (which is unlikely but possible)
      } else {

        // P1 has (L)
        SetInnerHtml(
          $(`.p1.container .name`),
          `
          <span>
            <span class="sponsor">
              ${player1.team ? player1.team.replace(/\s*[\|\/\\]\s*/g, ' '): ""}
            </span>
            ${
              player1.name ? await Transcript(player1.name) : ""
            }
            ${"(L)"}
          </span>
          `
        );

        // P2 has (L)
        SetInnerHtml(
          $(`.p2.container .name`),
          `
          <span>
            <span class="sponsor">
              ${player2.team ? player2.team.replace(/\s*[\|\/\\]\s*/g, ' '): ""}
            </span>
            ${
              player2.name ? await Transcript(player2.name) : ""
            }
            ${"(L)"}
          </span>
          `
        );
      }

    } else if (team1Losers) { // P1 in losers, P2 in winners

      // P1 has (L)
      SetInnerHtml(
        $('.p1.container .name'),
        `
        <span>
          <span class="sponsor">
            ${player1.team ? player1.team.replace(/\s*[\|\/\\]\s*/g, ' '): ""}
          </span>
          ${
            player1.name ? await Transcript(player1.name) : ""
          }
          ${"(L)"}
        </span>
        `
      );
      
      // P2 has (W)
      SetInnerHtml(
        $('.p2.container .name'),
        `
        <span>
          <span class="sponsor">
            ${player2.team ? player2.team.replace(/\s*[\|\/\\]\s*/g, ' '): ""}
          </span>
          ${
            player2.name ? await Transcript(player2.name) : ""
          }
          ${"(W)"}
        </span>
        `
      );

      if (t == 1) {
        const jsonString = JSON.stringify(player2);
        localStorage.setItem("playerInWinners", jsonString);
      }

    } else if (team2Losers) {

      // P1 has (W)
      SetInnerHtml(
        $('.p1.container .name'),
        `
        <span>
          <span class="sponsor">
            ${player1.team ? player1.team.replace(/\s*[\|\/\\]\s*/g, ' '): ""}
          </span>
          ${
            player1.name ? await Transcript(player1.name) : ""
          }
          ${"(W)"}
        </span>
        `
      );
      
      // P2 to has (L)
      SetInnerHtml(
        $('.p2.container .name'),
        `
        <span>
          <span class="sponsor">
            ${player2.team ? player2.team.replace(/\s*[\|\/\\]\s*/g, ' '): ""}
          </span>
          ${
            player2.name ? await Transcript(player2.name) : ""
          }
          ${"(L)"}
        </span>
        `
      );

      if (t == 1) {
        const jsonString = JSON.stringify(player1);
        localStorage.setItem("playerInWinners", jsonString);
      }

    // Neither P1 nor P2 is in losers
    } else {

      SetInnerHtml(
        $('.p1.container .name'),
        `
        <span>
          <span class="sponsor">
            ${player1.team ? player1.team.replace(/\s*[\|\/\\]\s*/g, ' '): ""}
          </span>
          ${
            player1.name ? await Transcript(player1.name) : ""
          }
        </span>
        `
      );

      SetInnerHtml(
        $('.p2.container .name'),
        `
        <span>
          <span class="sponsor">
            ${player2.team ? player2.team.replace(/\s*[\|\/\\]\s*/g, ' '): ""}
          </span>
          ${
            player2.name ? await Transcript(player2.name) : ""
          }
        </span>
        `
      );

    }
  }

  async function DisplayTeamName(t, team, teamName) {

    const teamNameInWinners = localStorage.getItem("teamNameInWinners");

    if (t == 0) {
      team1Name = teamName;
      team1Losers = team.losers
    }

    if (t == 1) {
      team2Name = teamName;
      team2Losers = team.losers
    }

      // If the player and the opponent are both in losers
    if (team1Losers && team2Losers) {

      // If Team 1 was in winners
      if (team1Name == teamNameInWinners) {

        // Team 1 has (WL)
        SetInnerHtml(
          $(`.p1.container .name`),
          `
          <span>
            ${team1Name}
            ${"(WL)"}
          </span>
          `
        );

        // Team 2 has (L)
        SetInnerHtml(
          $(`.p2.container .name`),
          `
          <span>
            ${team2Name}
            ${"(L)"}
          </span>
          `
        );

      // If Team 2 was in winners
      } else if (team2Name == teamNameInWinners) { 

        // Team 1 has (L)
        SetInnerHtml(
          $(`.p1.container .name`),
          `
          <span>
            ${team1Name}
            ${"(L)"}
          </span>
          `
        );

        // Team 2 has (WL)
        SetInnerHtml(
          $(`.p2.container .name`),
          `
          <span>
            ${team2Name}
            ${"(WL)"}
          </span>
          `
        );

      // If neither of them were in winners (which is unlikely but possible)
      } else {

        // Team 1 has (L)
        SetInnerHtml(
          $(`.p1.container .name`),
          `
          <span>
            ${team1Name}
            ${"(L)"}
          </span>
          `
        );

        // Team 2 has (L)
        SetInnerHtml(
          $(`.p2.container .name`),
          `
          <span>
            ${team2Name}
            ${"(L)"}
          </span>
          `
        );
      }

    } else if (team1Losers) { // Team 1 in losers, Team 2 in winners

      // Team 1 has (L)
      SetInnerHtml(
        $(`.p1.container .name`),
        `
        <span>
          ${team1Name}
          ${"(L)"}
        </span>
        `
      );

      // Team 2 has (W)
      SetInnerHtml(
        $(`.p2.container .name`),
        `
        <span>
          ${team2Name}
          ${"(W)"}
        </span>
        `
      );

      if (t == 1) {
        localStorage.setItem("teamNameInWinners", team2Name);
      }

    } else if (team2Losers) {

      // Team 1 has (W)
      SetInnerHtml(
        $(`.p1.container .name`),
        `
        <span>
          ${team1Name}
          ${"(W)"}
        </span>
        `
      );

      // Team 2 has (L)
      SetInnerHtml(
        $(`.p2.container .name`),
        `
        <span>
          ${team2Name}
          ${"(L)"}
        </span>
        `
      );

      if (t == 1) {
        localStorage.setItem("teamNameInWinners", team1Name);
      }

    // Neither P1 nor P2 is in losers
    } else {

      SetInnerHtml(
        $(`.p1.container .name`),
        `
        <span>
          ${team1Name}
        </span>
        `
      );

      SetInnerHtml(
        $(`.p2.container .name`),
        `
        <span>
          ${team2Name}
        </span>
        `
      );

    }
  }
});
