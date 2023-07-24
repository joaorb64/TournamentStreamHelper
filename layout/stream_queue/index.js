LoadEverything().then(() => {
    let config = {
        "assets": {
          "default": {}
        },
        "stream": "",
        "default_stream" : "",
        "force_multistream" : false,
        "display_stream_name" : "multistream",
        "sets_displayed" : -1,
        "display_first_set": true,
        "station" : -1,
        "currentEventOnly": false,
        "display" : {
            "station" : false,
            "country_flag" : true,
            "state_flag" : true,
            "avatar" : true
        }
    }
    
    function isDefault(value){
        return value === "" || value === -1 || value === undefined || value === null
    }

    let window_config = window.config || {}
    for (k in config){
        if (!isDefault(window_config[k])){
            config[k] = window_config[k]
        } else if (!isDefault(tsh_settings[k])) {
            config[k] = tsh_settings[k]
        }
    }

    if (!config.display){
        config.display = {};
    }

    console.log(config)

    let first_index = config.display_first_set ? 0 : 1    
    let sets_nb = config.sets_displayed;
    if (sets_nb < 0) sets_nb = undefined;

    gsap.config({ nullTargetWarn: false, trialWarn: false });

    let startingAnimation = gsap.timeline({ paused: true });

    Start = async (event) => {
        startingAnimation.restart();
    };

    /**
     * Wraps content in a .text element to emulate SetInnerHtml's behavior.
     */
    function wrap_text(txt){
        return `
            <div class = "text">${txt}</div>
        `
    }
    
    current_set_nb = 0; // ooooo dirty ass global var
    function resetSetsCount(){
        current_set_nb = 0;
    }


    function online_avatar_html(player, t){
        return `
            <div class = "p${t}_avatar avatar_container"> 
                <span class="avatar" style="background-image: url('${player.online_avatar}')"></span>
            </div>
        `
    }

    async function team_html(set, t, s, isTeams, resolver){
        let team = set.team[""+t];
        let player = team.player["1"];

        resolver.add(`.set${current_set_nb} .p${t} .tag`, 
            isTeams ? team.name :
                `
                <span class="sponsor">
                    ${player.team ? player.team : ""}
                </span>
                ${await Transcript(player.name)}
                ${team.losers ? "<span class='losers'>L</span>" : ""}
                `
        )

        resolver.add(`.set${s - 1} .p${t} .twitter`, 
            (!isTeams) ?  `<span class="twitter_logo"></span>${String(player.twitter)}` : ""  
        )

        return `
            <div class = "p${t} team">
                ${isTeams && !config.display.avatar ? "" : online_avatar_html(player, t)}
                <div class = "flags">
                    ${ isTeams ? "" : 
                        (player.country.asset && config.display.country_flag ? `<div class='flag' style='background-image: url(../../${player.country.asset.toLowerCase()})'></div>` : "") + 
                        (player.state.asset && config.display.state_flag? `<div class='flag' style='background-image: url(../../${player.state.asset.toLowerCase()})'></div>` : "")
                    }
                </div>
                <div class = "name">
                    <div class = "tag"></div>
                    <div class = "extra">
                        ${ player.twitter ?
                            ` <div class = "twitter">  </div> ` : ''
                        }
                        ${ player.pronoun ?
                            ` <div class = "pronoun"> ${ wrap_text((!isTeams && true) ?  String(player.pronoun) : "") } </div>` : ''
                        }
                        ${ team.seed ?
                            `<div class = "seed"> ${wrap_text("Seed " + team.seed)} </div> ` : ''
                        }
                       
                        
                    </div>
                </div>
            </div>
        `
    }

    async function queue_html(queue, resolver){
        let html = "";

        for (const [s, set] of Object.values(queue).slice(first_index).entries()){
            if (sets_nb && (current_set_nb >= sets_nb)) break;

            if (config.currentEventOnly && !set.isCurrentEvent) continue;
            if (config.station != -1 && config.station != set.station) continue;

            let isTeams = Object.keys(set.team["1"].player).length > 1;
            html += `
                <div class="set${current_set_nb} set">
                    ${ await team_html(set, 1, s + 1 , isTeams, resolver) }
                    <div class = "vs_container">
                        <div class = "vs vs_${config.display.station ? 'small' : 'big'}">VS</div>
                        ${config.display.station && set.station && set.station != -1 ? '<div class = "station"></div>' : ''}
                        <div class = "phase"> </div>
                        <div class = "match"> </div>

                    </div>
                    ${ await team_html(set, 2, s + 1, isTeams, resolver) }
                </div>
            `;

            resolver.add(`.set${current_set_nb} .match`, set.match);
            resolver.add(`.set${current_set_nb} .phase`, set.phase);
            resolver.add(`.set${current_set_nb} .station`, "Station " + set.station);

            current_set_nb++;
        }

        return html;
    }

    function stream_name_html(stream){
        return `<div class = "message"><img class = "twitch_logo" src = "./twitch.svg"></img>/${stream}</div>`
    }

    Update = async (event) => {
        let data = event.data;
        let oldData = event.oldData;

        let stream = config.stream || data.currentStream || config.default_stream

        if (
            !oldData.streamQueue ||
            JSON.stringify(data.streamQueue) !=
            JSON.stringify(oldData.score.streamQueue) || 
            ( !tsh_settings.stream && oldData.currentStream != data.currentStream)
        ) {

            /*
            if (!stream){
                $(".stream_queue_content").html('<div class = "message">No stream (twitch username) selected. Enter one in TSH or set the "stream" or "default_stream" value in this layout\'s settings.json</div>');
                return;
            }*/
    
            let html = ""
            let resolver = new ContentResolver();

            if (stream){ //single-stream
                let queue = data.streamQueue[stream];
                if (!queue) return;
                
                if (config.display_stream_name == true){
                    html += stream_name_html(stream)
                }

                resetSetsCount();
                html += await queue_html(queue, resolver);
            } else { //multistream
                resetSetsCount();

                for (stream in data.streamQueue){
                    if (config.display_stream_name){
                        html += stream_name_html(stream)
                    }
                    html += await queue_html(data.streamQueue[stream], resolver)
                }
            }

            //console.log(html);
            $(".stream_queue_content").html(html);

            resolver.resolve()

            for (let i = 0; i <= current_set_nb; i++){
                gsap.from(
                    $(`.set${i}`),
                    { x: -100, autoAlpha: 0, duration: 0.3 },
                    0.2 + 0.2 * i
                );
            }
            gsap.from(
                $(`.message`),
                {autoAlpha: 0, duration : 0.3},
                0.3 + 0.2 * current_set_nb
            );
        }

    }
})