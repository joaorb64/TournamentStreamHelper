## Stream Queue Layout

This layout displays the next matches in the stream queue, for a specific stream, which means you need to choose a stream (i.e. a twitch username). You can do that in TournamentStreamHelper's interface (gear icon to the right of the "Load Current Stream Set" button on the "Scoreboard" tab). You can also use the settings.json file located in the same folder as this layout : 
- The "stream" property overrides the stream selected in TSH, if you enter a stream name between the quotes next to `"stream" : `, this stream will always be used.
- The "default_stream" property can be used to specify a default stream (duh) : if *there is no stream set in TSH*, the stream name between the quotes next to `"default_stream" : ` will be used instead if there is one.