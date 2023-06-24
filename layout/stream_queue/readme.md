## Stream Queue Layout

This layout displays the next matches in the stream queue for the current tournament, either for one specific stream or all streams. Here's how it works.

### Select a stream, or all of them
But first, what do i mean by "stream" ? Well, a stream is what you define on the top of the "Streams & Stations" page in start.gg. Basically, it's a twitch/youtube/whatever channel that can be assigned to some matches (a stream is assigned to a match = this match will be streamed on that channel). TSH currently only supports twitch channels, so we refer to streams with just the channel name.

The layout can either display all the sets in the stream queue (multi-stream mode), or a single stream (single-stream mode). By default, the layout enters single-stream mode as long as a stream name is specified somewhere : 
- If you enter a stream name in TSH directly (using the gear icon next to "Load current set from stream"), this stream will be used
- You can also use the options (either in settings.json or `window.config`, see below) : 
  - The "stream" option will override the stream selected in TSH : if there is a name between the quotes next to "stream", it will be used no matter what.
  - the "default_stream" option does the opposite : a stream name specified here will be used only if there is no stream selected in TSH.

If you do this, the layout will only display sets assigned to the stream you gave, if you don't give a stream anywhere (or use the "force_multistream" option, see below), all sets in the stream queue will be displayed.

Note that in multistream mode, the names of the streams will be displayed : this can be changed using [options](#options)

### Options
Options can be defined in two places : 
- In settings.json, you will find all the options that can change the behavior or this layout. Remember that everything between the `:` next to an option name, and the next `,` (or `}` at the end) will be the value of that option. Values can be numbers (written normally), text (between quotes) and the two special values `true` and `false`, options that are basically a yes/no question. 
- You can makes copies of the .html file, while overriding some options for each file. If you want an overlay that displays all the stream queue, and an overlay that focuses on a specific stream, that's what you want. To override an option only for a specific .html file, open it, and add a `"option name" : value,` line (same syntax as in settings.json) between the brackets after `window.config`. 
  ```html
    window.config = {
        "OPTION" : VALUE,
    };
  ```

Basically settings.json contains the global options, and if you want to use multiple instances of the layout with different behaviors you copy index.html and use window.config to override the relevant options.

So, now that you understand options, here are all the possible options and what they do

| Option | Effect
| - | -
| stream | see above
| default_stream | see above
| force_multistream | If `true`, the layout will always be in multi-stream mode.
| display_stream_name | If the value is "multistream", the name of the streams will be displayed but only in multi-stream mode. If `true`, it will be here even in single-stream mode. If `false`, never.
| sets_displayed | How many sets are displayed. If -1, no limit, all sets in the queue are displayed, if 0 or more only the first x sets will be listed. 
| display_first_set | if `false`, the first set in the queue will be skipped. Why would you want that ? Well, when a set is started, it stays in the queue, so you may want to only have future sets. 
| station | Remember the start.gg "streams & stations" page ? On this page, you can also defines "station", which are just the console/pc + screen setups where matches are played (which we usually just refer to as "setups"). A station can be assigned to a match so players can see where they are playing/gonna play, but you can also assign a stream to a station, meaning that matches on this station are also streamed on that stream. And you can assign multiple stations to a single stream (if you want to stream multiple matches at the same time). So, this options allows you to limit the display to one specific station. If the value is 2, and stations 1, 2 and 3 are assigned to a stream, the matches assigned to stations 1 and 3 will not show up, even if they are also in the stream queue (and on the same stream). God that was a long explanation.
| display | This one is special, it's not actually a property, but rather a group of properties. So, you don't change it's value directly (what comes after the : next to "display"), you change the sub-properties inside the brackets next to "display". All these sub-properties are true or false and control whether something is displayed. 
| display.avatar | The player's start.gg avatar.
| display.country_flag | The flag of each player's countries
| display.state_flag | The flag of each player's state/region
| display.station | The station assigned to this set. 

Is there something you don't understand ? A problem with the layout ? Message @TwilCynder on twitter.