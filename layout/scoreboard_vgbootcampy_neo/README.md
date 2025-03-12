# Neo VGBC Style Overlay:
- Download the zip file and open it.
- Move the scoreboard_vgbootcampy_neo file into the /layout folder of TSH where all the other scoreboard files are located.
- Go to OBS and add a new Browser.
- Select the /layout/scoreboard_vgbootcampy_neo/index.html as the local file and set its width and height to 1920 and 1080 respectively.
- Run TSH and enter the players' information.
  - Select "Shutdown source when not visible" in the Browser's properties so that it plays the overlay animation everytime it becomes visible.
  
# Player Cams:
- Included in the scoreboard_vgbootcampy_neo file are the CameraWhiteBorders.png and CameraMask.png.
- Add /layout/scoreboard_vgbootcampy_neo/CameraWhiteBorders.png as an Image in OBS to set the camera borders.
  - Change the color of the border by adding a color correction filter to the image.
- Add an Image Mask/Blend filter to the player cam (1280x720) and select /layout/scoreboard_vgbootcampy_neo/CameraMask.png as its path to round the corners of the player cam.
- Adjust the size of the player cams and move them so they fit nicely within their borders.

# Enjoy!
- You can edit the HTML, CSS, and JavaScript files to change the color and position of words and containers, add your own logo, change animation speed, etc.
