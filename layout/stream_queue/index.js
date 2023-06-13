LoadEverything().then(() => {
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

        console.log(`.set${s} .p${t} .tag`)

        resolver.add(`.set${s} .p${t} .tag`, 
            isTeams ? team.name :
                `
                <span class="sponsor">
                    ${player.team ? player.team : ""}
                </span>
                ${await Transcript(player.name)}
                ${team.losers ? "<span class='losers'>L</span>" : ""}
                `
        )

        resolver.add(`.set${s} .p${t} .twitter`, 
            (!isTeams) ?  `<span class="twitter_logo"></span>${String(player.twitter)}` : ""  
        )

        return `
            <div class = "p${t} team">
                ${isTeams ? "" : online_avatar_html(player, t)}
                <div class = "flags">
                    ${ isTeams ? "" : 
                        (player.country.asset ? `<div class='flag' style='background-image: url(../../${player.country.asset.toLowerCase()})'></div>` : "") + 
                        (player.state.asset ? `<div class='flag' style='background-image: url(../../${player.state.asset.toLowerCase()})'></div>` : "")
                    }
                </div>
                <div class = "name">
                    <div class = "tag"></div>
                    <div class = "extra">
                        <div class = "twitter">  </div> 
                        <div class = "pronoun"> ${ wrap_text((!isTeams && true) ?  String(player.pronoun) : "") } </div>
                        <div class = "seed"> ${wrap_text("Seed " + team.seed)} </div>
                    </div>
                </div>
            </div>
        `
    }

    Update = async (event) => {
        let data = event.data;
        let oldData = event.oldData;

        if (
            !oldData.streamQueue ||
            JSON.stringify(data.streamQueue) !=
            JSON.stringify(oldData.score.streamQueue)
        ) {
            let resolver = new ContentResolver();

            let stream = data.currentStream || tsh_settings.default_stream;
            let queue = data.streamQueue[stream];
            let html = ""
            for (const [s, set] of Object.values(queue).entries()){
                let isTeams = Object.keys(set.team["1"].player).length > 1;
                html += `
                    <div class="set${s + 1} set">
                        ${ await team_html(set, 1, s + 1, isTeams, resolver) }
                        <div class = "vs_container">
                            <div class = "vs">VS</div>
                            <div class = "phase"> </div>
                            <div class = "match"> </div>
                        </div>
                        ${ await team_html(set, 2, s + 1, isTeams, resolver) }
                    </div>
                `;

                console.log(set.match)

            }
            //console.log(html);
            $(".stream_queue_content").html(html);

            resolver.resolve()

            for (const [s, set] of Object.values(queue).entries()){
                SetInnerHtml($(`.set${s + 1} .match`), set.match);
                SetInnerHtml($(`.set${s + 1} .phase`), set.phase);

                gsap.from(
                    $(`.set${s + 1}`),
                    { x: -100, autoAlpha: 0, duration: 0.3 },
                    0.2 + 0.2 * s
                );
            }
        }

    }
})