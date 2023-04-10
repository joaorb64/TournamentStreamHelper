# VGBC Style Waiting Screen Overlay:

- Go to OBS and add a new Browser.
- Select the /layout/scoreboard_vgbootcampy_waiting/index.html as the local file and set its width and height to 1920 and 1080 respectively.
- Run TSH and enter the players' information.

# Setup Instructions:

- Included in the scoreboard_vgbootcampy_waiting file are the Border.png, Divider.png, and GameScreenMask.png.
- Add /layout/scoreboard_vgbootcampy_waiting/Border.png and Divider.png as Images in OBS.
  - Change the color of the border and divider by adding a Color Correction filter and changing the Color Multiply to your color of choice.
- Add an Image Mask/Blend filter to the game screen and select /layout/scoreboard_vgbootcampy_waiting/GameScreenMask.png as its path to round the corners of the game screen.
- Adjust the size of the game screen and move it so it fit nicely within the border.

# Enjoy!

- You can edit the HTML, CSS, and JavaScript files to change the color of words and containers, etc.
