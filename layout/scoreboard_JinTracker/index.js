LoadEverything().then(() => {
  gsap.config({ nullTargetWarn: false, trialWarn: false });

  let p1Score = 100; // Variable to hold the P1 score before an update
  let p2Score = 100; // Variable to hold the P2 score before an update
  let newP1Score = 0; // Variable to hold the P1 score after an update
  let newP2Score = 0; // Variable to hold the P2 score after an update
  let savedBestOf = 0; // Variable to hold Best Of info
  let savedGameArray = new Array(); // Array to save which player won which game
  let player1; // P1 object before an update takes place
  let player2; // P2 object before an update takes place
  let newPlayer1; // P1 object after an update takes place
  let newPlayer2; // P2 object after an update takes place
  let swapDetected = false; // Variable that holds a boolean of whether a swap took place, initially set to false
  let startingAnimation = gsap.timeline({ paused: true })
    .from(
      [".fade"],
      {
        duration: 0.2,
        autoAlpha: 0,
        ease: "power2.out",
      },
      0
    )
    .from(
      [".p1.under_chips .fade_stagger_reverse:not(.text_empty)"],
      {
        autoAlpha: 0,
        stagger: {
          each: 0.05,
          from: 'start',
          opacity: 0,
        },
        duration: 0.2,
      },
      0
    )
    .from(
      [".p1.chips .fade_stagger_reverse:not(.text_empty)"],
      {
        autoAlpha: 0,
        stagger: {
          each: 0.05,
          from: 'start',
          opacity: 0,
        },
        duration: 0.2,
      },
      0
    )
    .from(
      [".p2.under_chips .fade_stagger_reverse:not(.text_empty)"],
      {
        autoAlpha: 0,
        stagger: {
          each: 0.05,
          from: 'start',
          opacity: 0,
        },
        duration: 0.2,
      },
      0
    )
    .from(
      [".p2.chips .fade_stagger_reverse:not(.text_empty)"],
      {
        autoAlpha: 0,
        stagger: {
          each: 0.05,
          from: 'start',
          opacity: 0,
        },
        duration: 0.2,
      },
      0
    )
    .from(
      [".fade_down"],
      {
        duration: 0.2,
        y: "-20px",
        ease: "power2.out",
        autoAlpha: 0,
      },
      0
    )
    .from(
      [".fade_right"],
      {
        duration: 0.2,
        x: "-20px",
        ease: "power2.out",
        autoAlpha: 0,
      },
      0
    )
    .from(
      [".fade_left"],
      {
        duration: 0.2,
        x: "+20px",
        ease: "power2.out",
        autoAlpha: 0,
      },
      0
    )
    .from(
      [".fade_up"],
      {
        duration: 0.2,
        y: "+20px",
        ease: "power2.out",
        autoAlpha: 0,
      },
      0
    );

  Start = async () => {
    startingAnimation.restart();
  };

  Update = async (event) => {
    let data = event.data;

    let isTeams =
      Object.keys(data.score[window.scoreboardNumber].team["1"].player).length >
      1;

    if (!isTeams) {
      for (const [t, team] of [
        data.score[window.scoreboardNumber].team["1"],
        data.score[window.scoreboardNumber].team["2"],
      ].entries()) {
        for (const [p, player] of [team.player["1"]].entries()) {
          if (player) {
            if (
              Object.keys(player.character).length > 0 &&
              player.character[1].name
            ) {
              SetInnerHtml(
                $(`.p${t + 1}.container .placeholder_container`),
                `<div class='placeholder'></div>`
              );
            } else {
              SetInnerHtml($(`.p${t + 1} .placeholder`), "");
              SetInnerHtml(
                $(`.p${t + 1}.container .placeholder_container`),
                ""
              );
            }

            SetInnerHtml(
              $(`.p${t + 1}.container .sponsor_icon`),
              player.sponsor_logo
                ? `<div style='background-image: url(../../${player.sponsor_logo})'></div>`
                : ""
            );

            SetInnerHtml(
              $(`.p${t + 1}.container .name`),
              `
            <span>
              <span class="sponsor">
                ${player.team ? player.team : ""}
              </span>
              ${player.name ? await Transcript(player.name) : ""}
              ${team.losers ? "(L)" : ""}
            </span>
            `
            );

            SetInnerHtml(
              $(`.p${t + 1} .flagcountry`),
              player.country.asset
                ? `<div class='flag' style='background-image: url(../../${player.country.asset.toLowerCase()})'></div>`
                : ""
            );

            let score = [
              data.score[window.scoreboardNumber].score_left,
              data.score[window.scoreboardNumber].score_right,
            ];

            SetInnerHtml($(`.p${t + 1} .score`), String(team.score));

            SetInnerHtml(
              $(`.p${t + 1} .seed`),
              player.seed ? `SEED ${player.seed}` : ""
            );

            SetInnerHtml(
              $(`.p${t + 1} .pronoun`),
              player.pronoun ? player.pronoun : ""
            );

            document
              .querySelector(`.p${t + 1}.character_container`)
              .classList.add("unhidden");

            document.querySelector(`.p${t + 1}.bg`).classList.add("unhidden");

            let teamMultiplyier = t == 0 ? 1 : -1;

            await CharacterDisplay(
              $(`.p${t + 1}.character_container`),
              {
                source: `score.${window.scoreboardNumber}.team.${t + 1}`,
                anim_out: {
                  autoAlpha: 0,
                  x: -20 * teamMultiplyier + "px",
                  stagger: teamMultiplyier * 0.2,
                  duration: 0.4,
                },
                anim_in: {
                  autoAlpha: 1,
                  x: "0px",
                  stagger: teamMultiplyier * 0.2,
                  duration: 0.4,
                },
              },
              event
            );
            UpdateColor(player, t);
          }
          if (team.color && !tsh_settings["forceDefaultScoreColors"]) {
            document
              .querySelector(":root")
              .style.setProperty(`--p${t + 1}-score-bg-color`, team.color);
          }
        }
      }
      SetInnerHtml(
        $(".match"),
        data.score[window.scoreboardNumber].match
          ? data.score[window.scoreboardNumber].match
          : ""
      );

      SetInnerHtml(
        $(".phase"),
        data.score[window.scoreboardNumber].phase
          ? data.score[window.scoreboardNumber].phase
          : ""
      );
      document.querySelector(".tournament_logo").classList.add("unhidden");
      checkSwap(); // Check to see if a swap took place. If it did, then the colors of the boxes are flipped and swapDetected is set to true.
    } else {
      for (const [t, team] of [
        data.score[window.scoreboardNumber].team["1"],
        data.score[window.scoreboardNumber].team["2"],
      ].entries()) {
        let teamName = "";
        let names = [];
        for (const [p, player] of Object.values(team.player).entries()) {
          if (player && player.name) {
            names.push(await Transcript(player.name));
          }
        }
        teamName = names.join(" / ");
        SetInnerHtml(
          $(`.p${t + 1}.container .name`),
          `
        <span>
          ${teamName}
          ${team.losers ? "(L)" : ""}
        </span>
        `
        );
        for (const [p, player] of [team.player["1"]].entries()) {
          document
            .querySelector(`.p${t + 1}.character_container`)
            .classList.remove("unhidden");

          document.querySelector(`.p${t + 1}.bg`).classList.remove("unhidden");
          document
            .querySelector(`.p${t + 1}.light`)
            .classList.remove("unhidden");

          SetInnerHtml($(`.p${t + 1} .seed`), "");
          SetInnerHtml($(`.p${t + 1} .flagcountry`), "");
          SetInnerHtml($(`.p${t + 1} .pronoun`), "");
          SetInnerHtml($(`.p${t + 1}.container .placeholder_container`), "");
          SetInnerHtml($(`.p${t + 1}.container .sponsor_icon`), "");
          SetInnerHtml($(`.p${t + 1} .score`), String(team.score));
          UpdateColorAlternate(player, t);
          if (team.color && !tsh_settings["forceDefaultScoreColors"]) {
            document
              .querySelector(":root")
              .style.setProperty(`--p${t + 1}-score-bg-color`, team.color);
          }
        }
      }
      SetInnerHtml(
        $(".match"),
        data.score[window.scoreboardNumber].match
          ? data.score[window.scoreboardNumber].match
          : ""
      );
      SetInnerHtml(
        $(".phase"),
        data.score[window.scoreboardNumber].phase
          ? data.score[window.scoreboardNumber].phase
          : ""
      );
      document.querySelector(".tournament_logo").classList.remove("unhidden");
      checkSwapForTeam(); // Check to see if a swap took place. If it did, then the colors of the boxes are flipped and swapDetected is set to true.
    }

    scoreBoxDisplayToggle(); // Display the boxes when Best Of is greater than 0
    savedBestOf = createGameBoxes(savedBestOf); // Create the boxes

    if (!swapDetected) {
      // If a swap was not detected, then just update the savedGameArray without flipping the colors of the boxes.
      ({ savedGameArray, newP1Score, newP2Score, p1Score, p2Score } =
        updateGameArray(
          savedGameArray,
          newP1Score,
          newP2Score,
          p1Score,
          p2Score
        ));
    }
    swapDetected = false; // Set swapDetected back to false if it was set to true inside the checkSwap function.

    // Here is where we color in the boxes.
    // I do not want the colorInBoxes function to be running forever, but it does not seem to update
    // the color of the boxes by executing once or multiple times using a for loop for some reason.
    // setInterval works, so I am using it to repeat the colorInBoxes function 10 times.
    let counter = 0;
    const i = setInterval(function () {
      colorInBoxes();
      counter++;
      if (counter == 10) {
        clearInterval(i);
      }
    }, 100);
  };

  /**
   * This function colors in the boxes based on the data saved in the savedGameArray.
   * The array holds 1 for player 1's win and 2 for player 2's win.
   * The result of game 1 is held in index 0, game 2 in index 1, and so on.
   */
  function colorInBoxes() {
    for (let i = 0; i < data.score[window.scoreboardNumber].best_of; i++) {
      const redGameBox = document.querySelector(`.game${i + 1}.p1_won`);
      const blueGameBox = document.querySelector(`.game${i + 1}.p2_won`);
      const darkGameBox = document.querySelector(`.game${i + 1}.neither_won`);

      if (blueGameBox) {
        if (savedGameArray[i] == 1) {
          redGameBox.classList.add("unhidden");
          blueGameBox.classList.remove("unhidden");
        } else if (savedGameArray[i] == 2) {
          redGameBox.classList.remove("unhidden");
          blueGameBox.classList.add("unhidden");
        } else {
          redGameBox.classList.remove("unhidden");
          blueGameBox.classList.remove("unhidden");
        }
      }
    }
  }

  /**
   * Checks to see if a swap took place. If it did, then the colors of the boxes are flipped.
   */
  function checkSwap() {
    [
      data.score[window.scoreboardNumber].team["1"],
      data.score[window.scoreboardNumber].team["2"],
    ].forEach((team, t) => {
      [team.player["1"]].forEach((player, p) => {
        if (player) {
          if (t == 0) {
            newPlayer1 = player;
          }
          if (t == 1) {
            newPlayer2 = player;
          }
        }
      });
    });

    // If a swap was detected
    if (
      player1 !== undefined &&
      player2 !== undefined &&
      compareObjects(player2, newPlayer1) &&
      compareObjects(player1, newPlayer2)
    ) {
      swapDetected = true;
      // Change player 1's win to player 2's win and vice versa
      for (let i = 0; i < savedGameArray.length; i++) {
        if (savedGameArray[i] == 1) {
          savedGameArray[i] = 2;
        } else if (savedGameArray[i] == 2) {
          savedGameArray[i] = 1;
        }
      }

      // Convert the array to a JSON string
      const jsonString = JSON.stringify(savedGameArray);

      // Store the JSON string in local storage
      localStorage.setItem("output", jsonString);

      // Swap score history as well
      [p1Score, p2Score] = [p2Score, p1Score];
    }

    // After a swap, player data are saved to detect the next swap
    player1 = newPlayer1;
    player2 = newPlayer2;
  }

  /**
   * Checks to see if a swap took place. If it did, then the colors of the boxes are flipped.
   */
  function checkSwapForTeam() {
    [
      data.score[window.scoreboardNumber].team["1"],
      data.score[window.scoreboardNumber].team["2"],
    ].forEach((team, t) => {
      [team.player["1"]].forEach((player, p) => {
        if (player) {
          if (t == 0) {
            newPlayer1 = player;
          }
          if (t == 1) {
            newPlayer2 = player;
          }
        }
      });
    });

    // If a swap was detected
    if (
      player1 !== undefined &&
      player2 !== undefined &&
      compareObjectsForTeam(player2, newPlayer1) &&
      compareObjectsForTeam(player1, newPlayer2)
    ) {
      swapDetected = true;
      // Change player 1's win to player 2's win and vice versa
      for (let i = 0; i < savedGameArray.length; i++) {
        if (savedGameArray[i] == 1) {
          savedGameArray[i] = 2;
        } else if (savedGameArray[i] == 2) {
          savedGameArray[i] = 1;
        }
      }

      // Convert the array to a JSON string
      const jsonString = JSON.stringify(savedGameArray);

      // Store the JSON string in local storage
      localStorage.setItem("output", jsonString);

      // Swap score history as well
      [p1Score, p2Score] = [p2Score, p1Score];
    }

    // After a swap, player data are saved to detect the next swap
    player1 = newPlayer1;
    player2 = newPlayer2;
  }
});

/**
 * Updates the savedGameArray based on the update on the players' scores.
 * @param savedGameArray an array holding the results of the games, 1 for P1's win, 2 for P2's win
 * @param newP1Score a variable to hold the current P1 score
 * @param newP2Score a variable to hold the current P2 score
 * @param p1Score a variable that holds the previous P1 score
 * @param p2Score a variable that holds the previous P2 score
 * @returns all the updated variables
 */
function updateGameArray(
  savedGameArray,
  newP1Score,
  newP2Score,
  p1Score,
  p2Score
) {
  let gameNum = 0; // Variable to store which game we are at
  let gameArray = savedGameArray; // Array to hold game winner data

  // Retrieve the JSON string from local storage
  const retrievedJsonString = localStorage.getItem("output");

  // Parse the JSON string back to an array
  const retrievedArray = JSON.parse(retrievedJsonString);

  if (retrievedArray) {
    gameArray = retrievedArray;
  }

  // Do a run-through to get P1 score and P2 score to see which game we are at.
  [
    data.score[window.scoreboardNumber].team["1"],
    data.score[window.scoreboardNumber].team["2"],
  ].forEach((team, t) => {
    [team.player["1"]].forEach((player, p) => {
      if (player) {
        // If we are looking at P1
        if (t == 0) {
          newP1Score = team.score; // Get P1 score
        }
        // If we are looking at P2
        if (t == 1) {
          newP2Score = team.score; // Get P2 score
        }
      }
    });
    gameNum = newP1Score + newP2Score; // Add P1 score and P2 score to see which game we are at
  });

  // Clear all the boxes when P1 score + P2 score is 0.
  if (gameNum == 0) {
    gameArray = new Array(); // Clear the array
  }

  // If the score of P1 increased, fill in the array with 1's equal to the increase amount.
  if (newP1Score > p1Score) {
    for (let i = 0; i < newP1Score - p1Score; i++) {
      gameArray[gameNum - (newP1Score - p1Score) + i] = 1;
    }
  }

  // If the score of P2 increased, fill in the array with 2's equal to the increase amount.
  if (newP2Score > p2Score) {
    for (let i = 0; i < newP2Score - p2Score; i++) {
      gameArray[gameNum - (newP2Score - p2Score) + i] = 2;
    }
  }

  // If the score of P1 decreased, locate the index of the most recent win and remove it from the array using splice.
  // Repeat as many times as the decrease amount.
  if (newP1Score < p1Score) {
    // p1Score was initially set to 100 so this does not execute on the first run-through
    if (p1Score < 100) {
      for (let i = 0; i < p1Score - newP1Score; i++) {
        let index = -1;
        for (let j = 0; j < data.score[window.scoreboardNumber].best_of; j++) {
          if (gameArray[j] == 1) {
            index = j; // Locate the index of the most recent win
          }
        }
        gameArray.splice(index, 1); // Remove one game at a time
      }
    }
  }

  // If the score of P2 decreased, locate the index of the most recent win and remove it from the array using splice.
  // Repeat as many times as the decrease amount.
  if (newP2Score < p2Score) {
    // p2Score was initially set to 100 so this does not execute on the first run-through
    if (p2Score < 100) {
      for (let i = 0; i < p2Score - newP2Score; i++) {
        let index = -1;
        for (let j = 0; j < data.score[window.scoreboardNumber].best_of; j++) {
          if (gameArray[j] == 2) {
            index = j; // Locate the index of the most recent win
          }
        }
        gameArray.splice(index, 1); // Remove one game at a time
      }
    }
  }
  p1Score = newP1Score; // Update p1Score to detect change later
  p2Score = newP2Score; // Update p2Score to detect change later

  savedGameArray = gameArray; // Update the savedGameArray to hold the current results

  // Convert the array to a JSON string
  const jsonString = JSON.stringify(savedGameArray);

  // Store the JSON string in local storage
  localStorage.setItem("output", jsonString);

  return { savedGameArray, newP1Score, newP2Score, p1Score, p2Score }; // Return all the updated variables
}

/**
 * Displays the box(es) when the Best Of is greater than 0.
 */
function scoreBoxDisplayToggle() {
  const scoreBoxes = document.querySelector(`.score_boxes`);

  if (data.score[window.scoreboardNumber].best_of > 0) {
    // Show the box(es) when Best Of is greater than 0
    scoreBoxes.classList.add("unhidden");
  } else {
    // Hide when Best Of is not greater than 0
    scoreBoxes.classList.remove("unhidden");
  }
}

/**
 * Creates the boxes by adding divs inside the score_boxes class
 * @param savedBestOf Best Of info that is saved before an update takes place
 * @returns the new savedBestOf after the boxes are created
 */
function createGameBoxes(savedBestOf) {
  let gameDivText = "";
  let redGameDivText = "";
  let blueGameDivText = "";
  let darkGameDivText = "";

  // If Best Of is not 0 and Best Of has been updated
  if (
    data.score[window.scoreboardNumber].best_of > 0 &&
    data.score[window.scoreboardNumber].best_of != savedBestOf
  ) {
    // The number of boxes should equal Best Of
    for (let i = 1; i <= data.score[window.scoreboardNumber].best_of; i++) {
      gameDivText += `<div class="game${i} box">GAME ${i}</div>\n`;
      redGameDivText += `<div class="game${i} box p1_won hidden"></div>\n`;
      blueGameDivText += `<div class="game${i} box p2_won hidden"></div>\n`;
      darkGameDivText += `<div class="game${i} box neither_won"></div>\n`;
    }
    SetInnerHtml($(".word.score_boxes"), gameDivText); // Create the game boxes with words
    SetInnerHtml($(".red.score_boxes"), redGameDivText); // Create the red game boxes
    SetInnerHtml($(".blue.score_boxes"), blueGameDivText); // Create the blue game boxes
    SetInnerHtml($(".dark.score_boxes"), darkGameDivText); // Create the dark game boxes
  } else if (data.score[window.scoreboardNumber].best_of === 0) {
    SetInnerHtml($(".word.score_boxes"), ""); // The game boxes with words disappear
    SetInnerHtml($(".red.score_boxes"), ""); // The red game boxes disappear
    SetInnerHtml($(".blue.score_boxes"), ""); // The blue game boxes disappear
    SetInnerHtml($(".dark.score_boxes"), ""); // The dark game boxes disappear
  }
  savedBestOf = data.score[window.scoreboardNumber].best_of; // The new Best Of is saved so it can be used to detect change later
  return savedBestOf;
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
    if (key !== "character" && key !== "mains" && key !== "id" && key !== "") {
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

/**
 * This function is for teams.
 * Checks to see whether the properties and their values of obj1 are the same as those of obj2.
 * Does not compare seeding.
 * Created this function with the help of ChatGPT, modified to make it recursive and fit the need of the overlay.
 * @param obj1 Object 1 to compare
 * @param obj2 Object 2 to compare
 * @returns boolean of whether the properties and their values of obj1 are the same as those of obj2
 */
function compareObjectsForTeam(obj1, obj2) {
  // Get the property names of obj1
  const obj1Keys = Object.keys(obj1).sort();

  // Loop through the properties of obj1
  for (let key of obj1Keys) {
    // Seedings can change for a player/team so do not check it
    if (
      key !== "seed" &&
      key !== "character" &&
      key !== "mains" &&
      key !== "id" &&
      key !== ""
    ) {
      // Check if the property exists in obj2
      if (!obj2.hasOwnProperty(key)) {
        return false;
      }
      // Check if the values of the properties are the same
      // Check to see if there is an object inside the object
      if (typeof obj1[key] == "object" && obj1[key] && obj2[key]) {
        // If an inner object of obj1 is not equal to the inner object of obj2, then we return false to avoid any more comparisons
        if (!compareObjectsForTeam(obj1[key], obj2[key])) return false;
        // If the primitive types are not equal to each other, then we return false here as well
      } else if (obj1[key] !== obj2[key]) {
        return false;
      }
    }
  }
  // If all properties and their values are the same, return true
  return true;
}

async function firstFunction(player, t) {
  SetInnerHtml(
    $(`.p${t + 1} .flagstate`),
    player.state.name
      ? `<div class="location_logo symbol"></div>${String(player.state.name)}`
      : ""
  );
}

async function firstAlternateFunction(player, t) {
  SetInnerHtml($(`.p${t + 1} .flagstate`), "");
}

async function secondFunction(player, t) {
  SetInnerHtml(
    $(`.p${t + 1} .twitter`),
    player.twitter
      ? `<div class="twitter_logo symbol"></div>${String(player.twitter)}`
      : ""
  );
}

async function secondAlternateFunction(player, t) {
  SetInnerHtml($(`.p${t + 1} .twitter`), "");
}

async function UpdateColor(player, t) {
  await firstFunction(player, t);
  await secondFunction(player, t);
  await thirdFunction(t);
}

async function UpdateColorAlternate(player, t) {
  await firstAlternateFunction(player, t);
  await secondAlternateFunction(player, t);
  await thirdAlternateFunction(t);
}

async function thirdFunction(t) {
  let stylesheet = document.styleSheets[1];

  console.log("Stylesheet:");
  console.log(stylesheet);

  var divs = document.getElementsByClassName(`p${t + 1} container`);

  var chips = document.getElementsByClassName(`p${t + 1} chips`);

  var camera_border_light = document.querySelector(`.p${t + 1}.light`);

  // Assuming there's only one div with the class "myDiv", you can directly access it
  var div = divs[0];

  var chip = chips[0];

  var score_container_element = div.querySelector(".score_container");
  var score_element = score_container_element.querySelector(".score");
  var name_element = div.querySelector(".name");

  var symbol_elements = chip.getElementsByClassName("symbol");

  var twitter = chip.querySelector(".twitter");

  var twitter_text = twitter.querySelector(".text");

  var twitter_logo = twitter_text.querySelector(".twitter_logo");

  var location = chip.querySelector(".flagstate");

  var location_text = location.querySelector(".text");

  var location_logo = location_text.querySelector(".location_logo");

  var chip_elements = chip.getElementsByClassName("chip");

  // Get the background color of the div
  var color = window
    .getComputedStyle(score_container_element, null)
    .getPropertyValue("background-color");

  var components = color.match(/^rgb\((\d+),\s*(\d+),\s*(\d+)\)$/);

  if (components) {
    // Extract the individual RGB components
    var red = parseInt(components[1]);
    var green = parseInt(components[2]);
    var blue = parseInt(components[3]);

    // Display the color
    console.log("The background color of the div is: " + color);
    console.log("Red: " + red);
    console.log("Green: " + green);
    console.log("Blue: " + blue);

    var intensity = red * 0.299 + green * 0.587 + blue * 0.114;
    console.log("The intensity is: " + intensity);

    if (intensity > 142) {
      console.log("Word should be black");

      // Change the text color
      score_element.style.color = "rgb(24, 24, 27)";
      name_element.style.color = "white";
      div.style.backgroundColor = "rgb(24, 24, 27)";

      changeStylesheetRule(
        stylesheet,
        `.p${t + 1} .twitter_logo`,
        "background-image",
        "url(./X_twitter_black.png)"
      );

      changeStylesheetRule(
        stylesheet,
        `.p${t + 1} .location_logo`,
        "background-image",
        "url(./map_pin_black.png)"
      );

      changeStylesheetRule(
        stylesheet,
        `.p${t + 1} .chip .text:not(.text_empty)`,
        "text-shadow",
        "none"
      );

      changeStylesheetRule(
        stylesheet,
        `.p${t + 1} .score`,
        "text-shadow",
        "none"
      );

      changeStylesheetRule(
        stylesheet,
        `.p${t + 1}.container`,
        "filter",
        "none"
      );

      changeStylesheetRule(
        stylesheet,
        `.p${t + 1}.under_chips`,
        "filter",
        "none"
      );

      camera_border_light.classList.remove("unhidden");

      for (key in chip_elements) {
        chip_elements.item(key).style.color = "rgb(24, 24, 27)";
      }
    } else if (intensity > 75) {
      console.log("In the middle");

      // Change the text color
      score_element.style.color = "white";
      name_element.style.color = "white";
      div.style.backgroundColor = "rgb(24, 24, 27)";

      changeStylesheetRule(
        stylesheet,
        `.p${t + 1} .twitter_logo`,
        "background-image",
        "url(./X_twitter_white.png)"
      );

      changeStylesheetRule(
        stylesheet,
        `.p${t + 1} .location_logo`,
        "background-image",
        "url(./map_pin_white.png)"
      );

      changeStylesheetRule(
        stylesheet,
        `.p${t + 1} .chip .text:not(.text_empty)`,
        "text-shadow",
        "0em 0em 0.2em #000"
      );

      changeStylesheetRule(
        stylesheet,
        `.p${t + 1} .score`,
        "text-shadow",
        "0em 0em 0.2em #000"
      );

      changeStylesheetRule(
        stylesheet,
        `.p${t + 1}.container`,
        "filter",
        "none"
      );

      changeStylesheetRule(
        stylesheet,
        `.p${t + 1}.under_chips`,
        "filter",
        "none"
      );

      camera_border_light.classList.remove("unhidden");

      for (key in chip_elements) {
        chip_elements.item(key).style.color = "white";
      }
    } else if (intensity <= 75) {
      // Change the text color
      score_element.style.color = "white";
      name_element.style.color = "rgb(24, 24, 27)";
      div.style.backgroundColor = "rgba(255, 255, 255)";

      changeStylesheetRule(
        stylesheet,
        `.p${t + 1} .twitter_logo`,
        "background-image",
        "url(./X_twitter_white.png)"
      );

      changeStylesheetRule(
        stylesheet,
        `.p${t + 1} .location_logo`,
        "background-image",
        "url(./map_pin_white.png)"
      );

      changeStylesheetRule(
        stylesheet,
        `.p${t + 1} .chip .text:not(.text_empty)`,
        "text-shadow",
        "0em 0em 0.2em #000"
      );

      changeStylesheetRule(
        stylesheet,
        `.p${t + 1} .score`,
        "text-shadow",
        "0em 0em 0.2em #000"
      );

      changeStylesheetRule(
        stylesheet,
        `.p${t + 1}.container`,
        "filter",
        "drop-shadow(0 0px 2px rgba(255, 255, 255, 0.85))"
      );

      changeStylesheetRule(
        stylesheet,
        `.p${t + 1}.under_chips`,
        "filter",
        "drop-shadow(0 0px 2px rgba(255, 255, 255, 0.85))"
      );

      camera_border_light.classList.add("unhidden");

      for (key in chip_elements) {
        chip_elements.item(key).style.color = "white";
      }
    }
  }
}

async function thirdAlternateFunction(t) {
  let stylesheet = document.styleSheets[1];

  var divs = document.getElementsByClassName(`p${t + 1} container`);

  var chips = document.getElementsByClassName(`p${t + 1} chips`);

  var camera_border_light = document.querySelector(`.p${t + 1}.light`);

  // Assuming there's only one div with the class "myDiv", you can directly access it
  var div = divs[0];

  var chip = chips[0];

  var score_container_element = div.querySelector(".score_container");
  var score_element = score_container_element.querySelector(".score");
  var name_element = div.querySelector(".name");

  var symbol_elements = chip.getElementsByClassName("symbol");

  var twitter = chip.querySelector(".twitter");

  var twitter_text = twitter.querySelector(".text");

  var twitter_logo = twitter_text.querySelector(".twitter_logo");

  var location = chip.querySelector(".flagstate");

  var location_text = location.querySelector(".text");

  var location_logo = location_text.querySelector(".location_logo");

  var chip_elements = chip.getElementsByClassName("chip");

  // Get the background color of the div
  var color = window
    .getComputedStyle(score_container_element, null)
    .getPropertyValue("background-color");

  var components = color.match(/^rgb\((\d+),\s*(\d+),\s*(\d+)\)$/);

  if (components) {
    // Extract the individual RGB components
    var red = parseInt(components[1]);
    var green = parseInt(components[2]);
    var blue = parseInt(components[3]);

    // Display the color
    console.log("The background color of the div is: " + color);
    console.log("Red: " + red);
    console.log("Green: " + green);
    console.log("Blue: " + blue);

    var intensity = red * 0.299 + green * 0.587 + blue * 0.114;
    console.log("The intensity is: " + intensity);

    if (intensity > 142) {
      console.log("Word should be black");

      // Change the text color
      score_element.style.color = "rgb(24, 24, 27)";
      name_element.style.color = "white";
      div.style.backgroundColor = "rgb(24, 24, 27)";

      changeStylesheetRule(
        stylesheet,
        `.p${t + 1} .twitter_logo`,
        "background-image",
        "url(./X_twitter_black.png)"
      );

      changeStylesheetRule(
        stylesheet,
        `.p${t + 1} .location_logo`,
        "background-image",
        "url(./map_pin_black.png)"
      );

      changeStylesheetRule(
        stylesheet,
        `.p${t + 1} .chip .text:not(.text_empty)`,
        "text-shadow",
        "none"
      );

      changeStylesheetRule(
        stylesheet,
        `.p${t + 1} .score`,
        "text-shadow",
        "none"
      );

      changeStylesheetRule(
        stylesheet,
        `.p${t + 1}.container`,
        "filter",
        "none"
      );

      changeStylesheetRule(
        stylesheet,
        `.p${t + 1}.under_chips`,
        "filter",
        "none"
      );

      for (key in chip_elements) {
        chip_elements.item(key).style.color = "rgb(24, 24, 27)";
      }
    } else if (intensity > 75) {
      console.log("In the middle");

      // Change the text color
      score_element.style.color = "white";
      name_element.style.color = "white";
      div.style.backgroundColor = "rgb(24, 24, 27)";

      changeStylesheetRule(
        stylesheet,
        `.p${t + 1} .twitter_logo`,
        "background-image",
        "url(./X_twitter_white.png)"
      );

      changeStylesheetRule(
        stylesheet,
        `.p${t + 1} .location_logo`,
        "background-image",
        "url(./map_pin_white.png)"
      );

      changeStylesheetRule(
        stylesheet,
        `.p${t + 1} .chip .text:not(.text_empty)`,
        "text-shadow",
        "0em 0em 0.2em #000"
      );

      changeStylesheetRule(
        stylesheet,
        `.p${t + 1} .score`,
        "text-shadow",
        "0em 0em 0.2em #000"
      );

      changeStylesheetRule(
        stylesheet,
        `.p${t + 1}.container`,
        "filter",
        "none"
      );

      changeStylesheetRule(
        stylesheet,
        `.p${t + 1}.under_chips`,
        "filter",
        "none"
      );

      camera_border_light.classList.remove("unhidden");

      for (key in chip_elements) {
        chip_elements.item(key).style.color = "white";
      }
    } else if (intensity <= 75) {
      console.log("Word should be white.");

      // Change the text color
      score_element.style.color = "white";
      name_element.style.color = "rgb(24, 24, 27)";
      div.style.backgroundColor = "rgba(255, 255, 255)";

      changeStylesheetRule(
        stylesheet,
        `.p${t + 1} .twitter_logo`,
        "background-image",
        "url(./X_twitter_white.png)"
      );

      changeStylesheetRule(
        stylesheet,
        `.p${t + 1} .location_logo`,
        "background-image",
        "url(./map_pin_white.png)"
      );

      changeStylesheetRule(
        stylesheet,
        `.p${t + 1} .chip .text:not(.text_empty)`,
        "text-shadow",
        "0em 0em 0.2em #000"
      );

      changeStylesheetRule(
        stylesheet,
        `.p${t + 1} .score`,
        "text-shadow",
        "0em 0em 0.2em #000"
      );

      changeStylesheetRule(
        stylesheet,
        `.p${t + 1}.container`,
        "filter",
        "drop-shadow(0 0px 2px rgba(255, 255, 255, 0.85))"
      );

      changeStylesheetRule(
        stylesheet,
        `.p${t + 1}.under_chips`,
        "filter",
        "drop-shadow(0 0px 2px rgba(255, 255, 255, 0.85))"
      );

      for (key in chip_elements) {
        chip_elements.item(key).style.color = "white";
      }
    }
  }
}

function changeStylesheetRule(stylesheet, selector, property, value) {
  // Make the strings lowercase
  selector = selector.toLowerCase();
  property = property.toLowerCase();
  value = value.toLowerCase();

  // Change it if it exists
  for (var i = 0; i < stylesheet.cssRules.length; i++) {
    var rule = stylesheet.cssRules[i];
    if (rule.selectorText === selector) {
      rule.style[property] = value;
      return;
    }
  }

  // Add it if it does not
  stylesheet.insertRule(selector + " { " + property + ": " + value + "; }", 0);
}
// Used like so:
// changeStylesheetRule(s, "body", "color", "rebeccapurple");
