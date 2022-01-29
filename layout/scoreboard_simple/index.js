(($) => {
    let startingAnimation = gsap.timeline({ paused: true })
        .from(['.phase'], { duration: .8, opacity: '0', y: "-20px", ease: "power2.inOut" }, 0)
        .from(['.container'], { duration: .8, opacity: '0', x: "-20px", ease: "power2.inOut" }, 0)
        .from(['.twitter-container'], { duration: .8, opacity: '0', x: "+40px", ease: "power2.inOut" }, 0)
            
    function Start(){
        startingAnimation.restart();
    }

    var data = {}
    var oldData = {}

    async function Update(){
        oldData = data;
        data = await getData();

        if(oldData.score == null || Object.keys(oldData.score.team1.players).length != Object.keys(data.score.team1.players).length) {
            if(Object.keys(data.score.team1.players).length == 1){
                gsap.timeline().from(['.singles'], { duration: .8, opacity: '1', ease: "power2.inOut" }, 0)
                gsap.timeline().to(['.doubles'], { duration: .8, opacity: '0', ease: "power2.inOut" }, 0)
            } else {
                gsap.timeline().to(['.singles'], { duration: .8, opacity: '0', ease: "power2.inOut" }, 0)
                gsap.timeline().from(['.doubles'], { duration: .8, opacity: '1', ease: "power2.inOut" }, 0)
            }
        }

        [data.score.team1, data.score.team2].forEach((team, t) => {
            Object.values(team.players).forEach((player, p) => {
                if(p){
                    SetInnerHtml($(`.t${t+1}.p${p+1} .name`), `
                        <span>
                            <span class='sponsor'>
                                ${player.team ? (player.team+"") : ""}
                            </span>
                            ${player.name}
                            ${team.losers ? " [L]" : ""}
                        </span>
                    `);
            
                    SetInnerHtml($(`.t${t+1}.p${p+1} .flagcountry`), `
                        <div class='flag' style='background-image: url(../../${player.country.asset.toLowerCase()})'></div>
                    `);
            
                    SetInnerHtml($(`.t${t+1}.p${p+1} .flagstate`), `
                        <div class='flag' style='background-image: url(../../${player.state.asset})'></div>
                    `);
            
                    SetInnerHtml($(`.t${t+1}.p${p+1} .twitter`), String(player.twitter));
            
                    let score = [data.score.score_left, data.score.score_right]
    
                    SetInnerHtml($(`.t${t+1}.p${p+1} .score`), String(score[t]));
    
                    SetInnerHtml($(`.t${t+1}.p${p+1} .sponsor-container`),
                        `<div class='sponsor-logo' style='background-image: url(../../${player.sponsor_logo})'></div>`);
                }
            });
        });


        //SetInnerHtml($(".phase"), data.tournament_phase + (data.best_of != 0 ? " - Best of " + data.best_of : ""));
    }

    $(window).on("load", () => {
        Update();
        $('body').fadeTo(500, 1, async () => {
            Start();
            setInterval(Update, 1000);
        });
    });
})(jQuery);