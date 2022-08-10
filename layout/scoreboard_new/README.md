# New Overlay (Inspired by Double Down Overlay of VGBC):
- Download the zip file and open it.
- Move the scoreboard_new file (probably named scoreboard_new-main) into the /layout folder of TSH where all the other scoreboard files are located.
- Go to OBS and add a new Browser.
- Select the /layout/scoreboard_new-main/ssbultimate.html as the local file and set its width and height to 1920 and 1080 respectively.
- Run TSH and enter the players' information.
  - The Browser in OBS may need to be refreshed for the information to appear properly.
  - Select "Shutdown source when not visible" in the Browser's properties so that it plays the overlay animation everytime it becomes visible.
  
# Player Cams:
- Included in the scoreboard_new file are the CameraBorders.png and CameraMask.png.
- Add /layout/scoreboard_new-main/CameraBorders.png as an Image in OBS to set the camera borders.
  - Change the color of the border by adding a color correction filter to the image.
- Add an Image Mask/Blend filter to the player cam (1280x720) and select CameraMask.png as its path to round the corners of the player cam.
- Adjust the size of the player cams and move them so they fit nicely within their borders.

# Enjoy!
- You can edit the CSS file to change the color and position of words and containers.
