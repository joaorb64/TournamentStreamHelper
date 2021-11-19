# TournamentStreamHelper

A Stream helper for fighting game tournaments!

## Program itself

![screenshot](../media/media/screenshot1.png)

## Usage

All data is updated in one click!

![screenshot](../media/media/usage.gif)

## Scoreboard samples -- included in the program

### Animated scoreboards!

![screenshot](../media/media/scoreboard.gif)

#### Simpler scoreboard

![screenshot](../media/media/scoreboard2.png)

#### "FGC-style" scoreboard

![screenshot](../media/media/scoreboard_fgc.png)

#### Demo with automatic transcription of Kana to Romaji

![screenshot](../media/media/scoreboard_jp.png)

### VS screen

![screenshot](../media/media/vs_screen.gif)

![screenshot](../media/media/vs2.gif)

### Download multiple asset packs from within the program!

![screenshot](../media/media/multi.gif)

Features:

- Update stream information without messing up your OBS setup
- For TOs: select set from SmashGG to have player information automatically filled, update current info from set in StreamQueue, with 100% automatic data input
- For Competitors: turn on Competitor Mode to get your current set info in one click or automatically, so you can play the tournament without needing to manually update the overlay data
- Comes with demo animated overlays for a quick start

# How to install

Windows:

- Download the latest release zip and extract it: https://github.com/joaorb64/SmashStreamHelper/releases/latest
- Install Python 3.X and be sure to have it added to "Path" when installing (Windows x64: https://www.python.org/ftp/python/3.9.2/python-3.9.2-amd64.exe)
- Only for the first run, double click `install_requirements.bat` (a command prompt window should open, load some bars, then wait for you to press any key)
- From now on you may open the program using `TournamentStreamHelper.bat`

Linux:

- Download the latest release zip and extract it: https://github.com/joaorb64/SmashStreamHelper/releases/latest
- `pip3 install -r requirements.txt`
- Double click `TournamentStreamHelper.sh` or run `./TournamentStreamHelper.sh` from a terminal. Make sure the script has executable permissions.

# Getting started

## I'm streaming online tournaments (not playing)

- Click on the SmashGG button's arrow, configure your SmashGG Key as prompted (only needs to be done once)
- Click again on the SmashGG button's arrow, configure the tournament link as prompted
- Now clicking the SmashGG button will open a list of matches for you to pick from. Pick a set
- Auto update should start -- it will update all data in the program and also the files in /out/. It also updates selected characters and the stage striking sequence

- If you're configuring the StreamQueue in SmashGG, there is an auto mode in the Twitch button, which will also get the next set automatically. Use this for full automation.

- Remember to turn on autosave on the save button's arrow if you want it
- Notice that the auto-update will overwrite your edits, so cancel it if you want to edit data manually

## I'm streaming my own run in an online tournament

- Activate **Settings** > **Competitor Mode**

- Click on the SmashGG button's arrow, configure your SmashGG Key as prompted (only needs to be done once)
- Click on the SmashGG button's arrow, configure your SmashGG user id as prompted (only needs to be done once)

- You'll be always the player on the left, and all match data will be updated automatically
- When a new set starts, the data will automatically update

- Remember to turn on autosave on the save button's arrow if you want it
- Notice that the auto-update will overwrite your edits, so cancel it if you want to edit data manually

## I'm streaming an offline tournament

- You can download autocomplete data from either SmashGG (using a tournament link) or PowerRankings.gg
- When you start entering a name, autocomplete should show options that will auto-fill player's data

- Remember to turn on autosave on the save button's arrow if you want it

# Usage with OBS

## Sample overlays

There are sample overlays located in the `/layout/` directory. In OBS, add a Browser element, select local file, then select one of the `.html` in the subdirectories.

- Make sure to set the window size to 1920x1080 for the overlay samples.
- Make sure to set the browser element to hide when inactive and reload on scene change, or else you will get a quick flicker when the scene is changed.

### VS Screens

- For the VS screens, check out their `index.js` to select which asset pack you want to use. There you can also define if P2's character asset will be mirrored or not.
- There are 2 versions of the vs screen: `tall` and `square`. Tall has stage strike output and is made based mainly on Smash Ultimate, but assets for some games can look weird in a taller crop. Square has no stage output and doesn't crop the character assets.

### Stage strike

- For the stage striking sample, experiment with different window sizes as the elements will adapt to it (i.e. 2000x2000, 1000x1000, 500x500, ...)

There's also instructions for editing those layouts in the `/layout/` directory.

## Using OBS Elements

When you click save (or edit anything when auto save is on) a directory named `out` is created in the program's directory, containing the players' data. In OBS, when you create a `Text` element, in its `properties`, there is an option to load the text from a text file. Redirect Text elements to the text files and the images from `out` to have your overlay synced with the program's output.

It's not possible to animate these elements unless there's an OBS plugin for that (I'm not aware of one).

### Tips

- In OBS you can select any element and use `Edit > Transform > Edit Transform (Ctrl+E)`. There you can set up the absolute position and size for your elements. There are alignment options and bounding box options so that when a player's name would overflow your layout the font gets smaller instead. Also works for images, where you can reserve a space and the image will fit that space independent of image size or proportion

# Extra configs

## Sponsor logos

You can find a directory called `/sponsor_logos/` in the program's directory. If you put an image, say, `google.png` (has to be a lowercase png), and a player has its prefix set as `GOOGLE`, `google` (or any casing variations) this file will also get copied to the output.

## Donations

[![ko-fi](https://www.ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/W7W22YK26)
