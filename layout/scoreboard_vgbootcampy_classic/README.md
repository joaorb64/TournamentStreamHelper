# Early 2022 VGBC Style Overlay Properties:
- The top left container alternates between match and best of x every 9 seconds. 
- The bottom containers alternate between Twitter handle and pronouns every 9 seconds.
- When one of the above information (match, best of x, Twitter handle, or pronouns) is edited, then the 9-second cycle is refreshed starting with match for the top left container and Twitter handle for the bottom containers.
- For a container, if one of the information is missing, then the alternation does not happen. If both are missing, then the container disappears.
- Select "Shutdown source when not visible" in the Browser's properties so the overlay animation is played everytime it becomes visible.

# Player Cams:
- Included in the scoreboard_vgbootcampy_classic file are the CameraWhiteBorders.png and CameraMask.png.
- Add /layout/scoreboard_vgbootcampy_classic/CameraWhiteBorders.png as an Image in OBS to set the camera borders.
  - Change the color of the border by adding a color correction filter to the image.
- Add an Image Mask/Blend filter to the player cam (1280x720) and select /layout/scoreboard_vgbootcampy_classic/CameraMask.png as its path to round the corners of the player cam.
- Adjust the size of the player cams and move them so they fit nicely within their borders.

# Enjoy!
- You can edit the HTML, CSS, and JavaScript files to change the color and position of words and containers, add your own logo, change animation speed, etc.
