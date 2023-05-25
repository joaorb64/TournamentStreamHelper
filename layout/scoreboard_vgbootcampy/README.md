# VGBC Style Overlay Properties:
- The top left container displays the name of the tournament and the bottom containers each display the player's Twitter handle.
- The match is shown at the bottom of the left player container.
- The phase and best of x is shown at the bottom of the right player container in "phase - best of x" format.
  - If only best of x is available, then only best of x is shown.
  - If it is best of 0 and the phase is available, then only the phase is shown.
- No information alternation takes place in this overlay. 
- Select "Shutdown source when not visible" in the Browser's properties so that it plays the overlay animation every time it becomes visible.

# Player Cams:

- Included in the scoreboard_vgbootcampy file are the CameraBorders.png and CameraMask.png.
- Add /layout/scoreboard_vgbootcampy/CameraBorders.png as an Image in OBS to set the camera borders.
  - Change the color of the border by adding a Color Correction filter and changing the Color Multiply to your color of choice.
- Add an Image Mask/Blend filter to the player cam (1280x720) and select /layout/scoreboard_vgbootcampy/CameraMask.png as its path to round the corners of the player cam.
- Adjust the size of the player cams and move them so they fit nicely within their borders.

# Enjoy!

- You can edit the HTML, CSS, and JavaScript files to change the color and position of words and containers, add your own logo, change animation speed, etc.
