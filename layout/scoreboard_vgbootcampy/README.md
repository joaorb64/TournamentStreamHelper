# VGBC Style Overlay:

- Go to OBS and add a new Browser.
- Select the /layout/scoreboard_vgbootcampy/index.html as the local file and set its width and height to 1920 and 1080 respectively.
- Run TSH and enter the players' information.
  - Select "Shutdown source when not visible" in the Browser's properties so that it plays the overlay animation every time it becomes visible.

# Player Cams:

- Included in the scoreboard_vgbootcampy file are the CameraBorders.png and CameraMask.png.
- Add /layout/scoreboard_vgbootcampy/CameraBorders.png as an Image in OBS to set the camera borders.
  - Change the color of the border by adding a Color Correction filter and changing the Color Multiply to your color of choice.
- Add an Image Mask/Blend filter to the player cam (1280x720) and select /layout/scoreboard_vgbootcampy/CameraMask.png as its path to round the corners of the player cam.
- Adjust the size of the player cams and move them so they fit nicely within their borders.

# Enjoy!

- You can edit the HTML, CSS, and JavaScript files to change the color and position of words and containers, add your own logo, change animation speed, etc.
