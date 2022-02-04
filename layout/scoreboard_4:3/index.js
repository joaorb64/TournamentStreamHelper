(($) => {
    let startingAnimation = gsap.timeline({ paused: true })
        .from(['.p1.container'], { duration: 1, x: '-100%', ease: "power2.inOut" }, 0)
        .from(['.p2.container'], { duration: 1, x: '+100%', ease: "power2.inOut" }, 0)
        .from(['.p1 .character_container'], { duration: 1, x: '+50%', ease: "power2.inOut" }, 0)
        .from(['.p2 .character_container'], { duration: 1, x: '-50%', ease: "power2.inOut" }, 0)
        .from(['.container_top'], { duration: 1, y: "-100%", ease: "power2.inOut" }, 0)
        .from(['.container_bottom'], { duration: 1, y: '+100%', ease: "power2.inOut" }, 0)
            
    function Start(){
        startingAnimation.restart();
    }

    var data = {}
    var oldData = {}

    async function Update(){
        oldData = data;
        data = await getData();

        Object.values(data.score.team).forEach((team, t) => {
            console.log(team)
            player = team.players["1"]

            if(player){
                SetInnerHtml($(`.p${t+1} .name`), `
                    <span class="sponsor">${player.team ? player.team+"&nbsp;" : ""}</span>${player.name}
                `);

                SetInnerHtml($(`.p${t+1} .flagcountry`), `
                    <div class='flag' style='background-image: url(../../${player.country.asset.toLowerCase()})'></div>
                `);
        
                SetInnerHtml($(`.p${t+1} .flagstate`), `
                    <div class='flag' style='background-image: url(../../${player.state.asset})'></div>
                `);

                SetInnerHtml($(`.p${t+1} .character_container`), `
                    <div class='character' style='background-image: url(../../${player.character["1"].assets.portrait.asset})'></div>
                `);
        
                SetInnerHtml($(`.p${t+1} .twitter`), player.twitter);

                SetInnerHtml($(`.p${t+1} .score`), String(team.score));

                SetInnerHtml($(`.p${t+1} .sponsor_logo`),
                    `<div class='sponsor_logo' style='background-image: url(../../${String(player.sponsor_logo)})'></div>`);
            }
        });

        SetInnerHtml($(`.container_top`), data.tournamentInfo.tournamentName);

        let bottomtexts = [];
        if(data.score.phase) bottomtexts.push(data.score.phase);
        if(data.score.match) bottomtexts.push(data.score.match);
        if(data.score.best_of) bottomtexts.push("BO"+data.score.best_of);

        SetInnerHtml($(`.container_bottom`), bottomtexts.join(" - "));
    }

    Update();
    $(window).on("load", () => {
        $('body').fadeTo(500, 1, async () => {
            Start();
            setInterval(Update, 1000);
        });
    });
})(jQuery);