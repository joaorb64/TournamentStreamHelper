# Jin's Game Result Tracker Overlay:

- Disclaimer: The boxes do not work when both players have the exact same information (name, sponsor, Twitter handle, pronouns, etc.)!
  - This is because player info is used to detect a swap. When both players' info are the same, the program thinks a swap has occurred whenever there is an update.
  - Therefore, it is best to set the players' info before changing the score, match, or phase.
  - Hopefully, this is not an issue since players have different sponsors, Twitter handles, etc. even if they have the same name. Also identical player info should not be a problem in a tournament singles setting due to different seedings.
  - For doubles, seeding is not checked to detect a swap.
- Reset the score to 0-0 to have the boxes be colored from the game 1 box.
- Change Best Of to either increase or decrease the number of boxes.
- The topleft container that holds match info disappears when match info is not available. This works the same for the small phase container just below it.
- There are five types of player info chip displayed on top of the player container: seed, twitter, pronoun, the state the player is from, and the country flag the player is from.
- You can change the type of character image by going to settings.json and changing the asset key.
- The camera borders, character images, and player chips disappear for doubles.

How the automatic font and shadow color switching works:

- When the player's color is dark, the texts in the chips become white and have a dark shadow beneath it, the shadow surrounding the player's container becomes white, the color of the inner container becomes white, and the color of the player's name becomes black.
- When the player's color has medium brightness, the texts in the chips become white and have dark shadow beneath it, the color of the inner container becomes black, and the color of the player's name becomes white.
- When the player's color is bright, the texts in the chips become black and have no shadow beneath it, the color of the inner container becomes black, and the color of the player's name becomes white.


# Setup Guide:

- Download the zip file and open it.
- Move the scoreboard_JinTracker file into the /layout folder of TSH where all the other scoreboard files are located.
- Go to OBS and add a new Browser source.
- Select the /layout/scoreboard_JinTracker/index.html as the local file and set its width and height to 1920 and 1080 respectively.
- To use the one without the character images, select the /layout/scoreboard_JinTracker/noCharacter.html as the local file and set its width and height to 1920 and 1080 respectively.
- Run TSH and enter the players' information.

# Player Cams:

- The color of the P1 camera border is the same as the color of the P1 score background and the color used to fill in the boxes when P1 wins, which is --p1-score-bg-color.
- The color of the P2 camera border is the same as the color of the P2 score background and the color used to fill in the boxes when P2 wins, which is --p2-score-bg-color.
- A 1920x1080 dimension player cam should fit inside a border.

# Customize:

- You can change the color of P1 and P2 by going to layout/main.css and changing --p1-score-bg-color and --p2-score-bg-color.
- You can rename an image tournament_logo.png and put it in this file to have it be displayed at the bottom center.
- You can edit the HTML, CSS, and JavaScript files to change the color and position of words and containers, etc.

# Inspirations

- Got the idea of having boxes keep track of who won which game from Wii Sports Resort Swordplay.
- Got the idea of putting the player info chips on top of the player container, displaying which state the player is from in one of the chips, and displaying player characters from @SevenThomsen's Sweet Spot 7 overlay.
