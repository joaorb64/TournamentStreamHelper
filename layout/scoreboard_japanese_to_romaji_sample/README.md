## scoreboard_japanese_to_romaji_sample

Player names that are exclusively Kana characters are "translated" to Romaji. This could be used so that international viewers can read player names in japanese tournament streams.

**Example**: If a player's name is `はらせん`, it will be displayed as `はらせん / HARASEN`.

**How I did it**
- Added `wanakana` library
- Imported wanakana in the HTML
- Red the documentation available online
- Added simple rules in `index.js > Update()`