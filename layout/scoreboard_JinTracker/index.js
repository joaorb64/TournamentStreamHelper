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
  let startingAnimation = gsap.timeline({ paused: true });

  Start = async () => {
    startingAnimation.restart();
  };

  Update = async (event) => {
    let data = event.data;

    let isTeams = Object.keys(data.score.team["1"].player).length > 1;

    if (!isTeams) {
      for (const [t, team] of [
        data.score.team["1"],
        data.score.team["2"],
      ].entries()) {
        for (const [p, player] of [team.player["1"]].entries()) {
          if (player) {
            SetInnerHtml(
              $(`.p${t + 1}.container .placeholder_container`),
              player.character[1].name ? `<div class='placeholder'></div>` : ""
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

            let score = [data.score.score_left, data.score.score_right];

            SetInnerHtml($(`.p${t + 1} .score`), String(team.score));

            SetInnerHtml(
              $(`.p${t + 1} .seed`),
              player.seed ? `SEED ${player.seed}` : ""
            );

            SetInnerHtml(
              $(`.p${t + 1} .pronoun`),
              player.pronoun ? player.pronoun : ""
            );

            // Get the name of the state instead of the flag and put it next to the location pin logo.
            SetInnerHtml(
              $(`.p${t + 1} .flagstate`),
              player.state.name
                ? `<span class="location_logo symbol"></span>${String(
                    player.state.name
                  )}`
                : ""
            );

            SetInnerHtml(
              $(`.p${t + 1} .twitter`),
              player.twitter
                ? `<span class="twitter_logo symbol"></span>${String(
                    player.twitter
                  )}`
                : ""
            );

            document
              .querySelector(`.p${t + 1}.character_container`)
              .classList.add("unhidden");

            document.querySelector(`.p${t + 1}.bg`).classList.add("unhidden");

            let teamMultiplyier = t == 0 ? 1 : -1;

            await CharacterDisplay(
              $(`.p${t + 1}.character_container`),
              {
                source: `score.team.${t + 1}`,
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
          }
        }
      }
      SetInnerHtml($(".match"), data.score.match ? data.score.match : "");

      SetInnerHtml($(".phase"), data.score.phase ? data.score.phase : "");
      document.querySelector(".tournament_logo").classList.add("unhidden");
      checkSwap(); // Check to see if a swap took place. If it did, then the colors of the boxes are flipped and swapDetected is set to true.
    } else {
      for (const [t, team] of [
        data.score.team["1"],
        data.score.team["2"],
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

          SetInnerHtml($(`.p${t + 1} .seed`), "");
          SetInnerHtml($(`.p${t + 1} .flagcountry`), "");
          SetInnerHtml($(`.p${t + 1} .flagstate`), "");
          SetInnerHtml($(`.p${t + 1} .twitter`), "");
          SetInnerHtml($(`.p${t + 1} .pronoun`), "");
          SetInnerHtml($(`.p${t + 1}.container .placeholder_container`), "");
          SetInnerHtml($(`.p${t + 1} .score`), String(team.score));
        }
      }
      SetInnerHtml($(".match"), data.score.match ? data.score.match : "");
      SetInnerHtml($(".phase"), data.score.phase ? data.score.phase : "");
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
    for (let i = 0; i < data.score.best_of; i++) {
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
    [data.score.team["1"], data.score.team["2"]].forEach((team, t) => {
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
    [data.score.team["1"], data.score.team["2"]].forEach((team, t) => {
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

  // Do a run-through to get P1 score and P2 score to see which game we are at.
  [data.score.team["1"], data.score.team["2"]].forEach((team, t) => {
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
        for (let j = 0; j < data.score.best_of; j++) {
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
        for (let j = 0; j < data.score.best_of; j++) {
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

  return { savedGameArray, newP1Score, newP2Score, p1Score, p2Score }; // Return all the updated variables
}

/**
 * Displays the box(es) when the Best Of is greater than 0.
 */
function scoreBoxDisplayToggle() {
  const scoreBoxes = document.querySelector(`.score_boxes`);

  if (data.score.best_of > 0) {
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
  if (data.score.best_of > 0 && data.score.best_of != savedBestOf) {
    // The number of boxes should equal Best Of
    for (let i = 1; i <= data.score.best_of; i++) {
      gameDivText += `<div class="game${i} box">GAME ${i}</div>\n`;
      redGameDivText += `<div class="game${i} box p1_won hidden"></div>\n`;
      blueGameDivText += `<div class="game${i} box p2_won hidden"></div>\n`;
      darkGameDivText += `<div class="game${i} box neither_won"></div>\n`;
    }
    SetInnerHtml($(".word.score_boxes"), gameDivText); // Create the game boxes with words
    SetInnerHtml($(".red.score_boxes"), redGameDivText); // Create the red game boxes
    SetInnerHtml($(".blue.score_boxes"), blueGameDivText); // Create the blue game boxes
    SetInnerHtml($(".dark.score_boxes"), darkGameDivText); // Create the dark game boxes
  } else if (data.score.best_of === 0) {
    SetInnerHtml($(".word.score_boxes"), ""); // The game boxes with words disappear
    SetInnerHtml($(".red.score_boxes"), ""); // The red game boxes disappear
    SetInnerHtml($(".blue.score_boxes"), ""); // The blue game boxes disappear
    SetInnerHtml($(".dark.score_boxes"), ""); // The dark game boxes disappear
  }
  savedBestOf = data.score.best_of; // The new Best Of is saved so it can be used to detect change later
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
    if (key !== "seed") {
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
