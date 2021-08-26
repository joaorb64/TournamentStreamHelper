(($) => {
    let startingAnimation = gsap.timeline({ paused: true })
        .from(['.phase'], { duration: .8, opacity: '0', ease: "power2.inOut" }, 0)
        .from(['.score_container'], { duration: .8, opacity: '0', ease: "power2.inOut" }, 0)
        .from(['.best_of'], { duration: .8, opacity: '0', ease: "power2.inOut" }, 0)
        .from(['.vs'], { duration: .4, opacity: '0', scale: 4, ease: "out" }, 0.5)
        .from(['.p1.character'], { duration: 1, x: "-200px", ease: "out" }, 0)
        .from(['.p1.container'], { duration: 1, x: "-100px", ease: "out" }, 0)
        .from(['.p2.character'], { duration: 1, x: "200px", ease: "out" }, 0)
        .from(['.p2.container'], { duration: 1, x: "100px", ease: "out" }, 0)
            
    function Start(){
        startingAnimation.restart();
    }

    var data = {}
    var oldData = {}

    async function Update(){
        oldData = data;
        data = await getData();

        ["p1", "p2"].forEach((p)=>{
            SetInnerHtml($(`.${p} .name`), `
                <span>
                    <span class='sponsor'>
                        ${data[p+"_org"] ? (data[p+"_org"]+"&nbsp;") : ""}
                    </span>
                    ${data[p+"_name"]}
                    ${data[p+"_losers"] ? " [L]" : ""}
                </span>
            `);

            SetInnerHtml($(`.${p} .sponsor_logo`),
                data[p+"_org"] ? `
                    <div>
                        <div class='sponsor_logo' style='background-image: url(../../sponsor_logos/${data[p+"_org"].toUpperCase()}.png)'></div>
                    </div>`
                    :
                    ""
            , oldData[p+"_state_flag_url"] != data[p+"_state_flag_url"]);
    
            SetInnerHtml($(`.${p} .real_name`), `${data[p+"_real_name"]}`);
    
            SetInnerHtml($(`.${p} .twitter`), `
                ${data[p+"_twitter"] ? `
                    <div class="twitter_logo"></div>
                    ${data[p+"_twitter"]}
                    `
                    :
                    ""
                }
            `);
    
            SetInnerHtml($(`.${p} .flagcountry`),
                data[p+"_country"] ? `
                    <div>
                        <div class='flag' style='background-image: url(../../assets/country_flag/${data[p+"_country"].toLowerCase()}.png)'></div>
                        <div class="flagname">${data[p+"_country"].toUpperCase()}</div>
                    </div>`
                    :
                    ""
            );
    
            SetInnerHtml($(`.${p} .flagstate`),
                data[p+"_state_flag_url"] ? `
                    <div>
                        <div class='flag' style='background-image: url(${data[p+"_state_flag_url"]})'></div>
                        <div class="flagname">${data[p+"_state"].toUpperCase()}</div>
                    </div>`
                    :
                    ""
            , oldData[p+"_state_flag_url"] != data[p+"_state_flag_url"]);
    
            if(oldData[p+"_character_codename"] != data[p+"_character_codename"] ||
            oldData[p+"_character_color"] != data[p+"_character_color"]){
                $(`.${p}.character`).html(`
                    <div class="bg">
                        <!--<div class="portrait" style='background-image: url(../../out/${p}_character_portrait.png)'></div>-->
                        <video id="video_${p}" class="video" width="auto" height="100%" autoplay muted>
                            <source src="../../${data[p+"_assets_path"]["webm"]}">
                        </video>
                    </div>
                `)
                gsap.timeline()
                    .from(
                        `.${p}.character .portrait`,
                        {duration: .5, opacity: 0}
                    )
                    .from(
                        `.${p}.character .portrait`,
                        { duration: .4, filter: 'brightness(0%)', onUpdate: function(tl) {
                            var tlp = (this.progress() * 100) >> 0;
                            TweenMax.set(`.${p}.character .portrait`, {'filter': 'brightness(' + tlp + '%)'});
                        },
                        onUpdateParams: ["{self}"] }
                    )
                
                    let vid = document.getElementById(`video_${p}`);
                    if(vid){
                        vid.addEventListener("timeupdate", function(){
                            // Check you time here and
                            if(this.currentTime >= 5) //Where t = CurrentTime
                            {
                                this.pause();// Stop the Video
                                this.currentTime = 5;
                            }
                        })
                    }
            }
    
        })

        SetInnerHtml($(`.p1 .score`), String(data.score_left));
        SetInnerHtml($(`.p2 .score`), String(data.score_right));

        SetInnerHtml($(".phase"), data.tournament_phase);
        SetInnerHtml($(".best_of"), data.best_of ? "Best of "+data.best_of : "");
    }

    // Using update here to set images as soon as possible
    // so that on window.load they are already preloaded
    Update();
    $(window).on("load", () => {
        $('body').fadeTo(0, 1, async () => {
            Start();
            setInterval(Update, 1000);
        });
    });
})(jQuery);
