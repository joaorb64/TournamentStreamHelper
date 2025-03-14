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

# Country Flags + Additional Flags PNG Files

- Country flags used in this overlay are stored in scoreboard_vgbootcampy_neo/assets/country_flag as PNG images.
- Additional flags used in this overlay are stored in scoreboard_vgbootcampy_neo/user_data/additional_flag as PNG images.
- Most of the country flags and all additional flags were created by editing the flags in base TSH that are in TournamentStreamHelper/assets/country_flag and TournamentStreamHelper/user_data/additional_flag.
- Some of the country flags were created by editing the Twemoji Flags Icons Pack designed by Twitter on:
  - https://www.iconarchive.com/show/twemoji-flags-icons-by-twitter.1.html
  - https://www.iconarchive.com/show/twemoji-flags-icons-by-twitter.2.html
  - https://www.iconarchive.com/show/twemoji-flags-icons-by-twitter.3.html
- These flag icons are licensed under CC Attribution 4.0 that allows copying, redistributing, remixing, transforming, and building upon the material for any purpose, even commercially.
- Link to the CC Attribution 4.0 License: https://creativecommons.org/licenses/by/4.0/.
- The corners of the flags from the Twemoji Flags Icons Pack were drawn using Procreate.
- Flags were resized to 92px x 66px, centered in a 92 x 92 canvas, overlaid with a transparent PNG image called shiny.png on top of them, and exported as new PNG images.
- These are the country code of the flags that were made using the flags from the Twemoji Flags Icon Pack:
  - ai, aq, au, ba, bm, by, ca, cc, ch, ck, cn, cu, cx, eh, er, fj, fk, gb-eng, gb-nir, gb, gd, gq, gs, gw, hm, hn, io, jp, km, kp, ky, kz, lc, lr, me, mh, ms, my, nc, nf, ng, np, nr, nu, nz, ph, pn, ps, qa, sb, sd, sh, si, ss, st, tc, tg, tk, tl, to, tv, uz, vg, vu, ws, zw.
- shiny.png can be found in this directory for those who are interested.

# Enjoy!

- You can edit the HTML, CSS, and JavaScript files to change the color and position of words and containers, add your own logo, change animation speed, etc.
