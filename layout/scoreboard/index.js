(($) => {
    let startingAnimation = gsap.timeline({ paused: true })
        .from(['.container'], { duration: 1, width: '0', ease: "power2.inOut" }, 0)
        .from(['.phase'], { duration: 1, opacity: '0', ease: "power2.inOut" }, 0)
            
    function Start(){
        startingAnimation.restart();
    }

    var data = {}
    var oldData = {}

    async function Update(){
        oldData = data;
        data = await getData();

        SetInnerHtml($(".p1 .name"), `
            <span>
                <span class='sponsor'>
                    ${data.p1_org ? (data.p1_org+"&nbsp;") : ""}
                </span>
                ${data.p1_name}
                ${data.p1_losers ? " [L]" : ""}
            </span>
        `);

        SetInnerHtml($(".p2 .name"), `
            <span>
                <span class='sponsor'>
                    ${data.p2_org ? (data.p2_org+"&nbsp;") : ""}
                </span>
                ${data.p2_name}
                ${data.p2_losers ? " [L]" : ""}
            </span>
        `);
        
        SetInnerHtml($(".p1 .twitter"), data.p1_twitter);
        SetInnerHtml($(".p2 .twitter"), data.p2_twitter);

        SetInnerHtml($(".p1 .flagcountry"), `
            <div class='flag' style='background-image: url(../../assets/country_flag/${data.p1_country.toLowerCase()}.png)'></div>
        `);

        SetInnerHtml($(".p1 .flagstate"), `
            <div class='flag' style='background-image: url(../../assets/state_flag/${data.p1_country.toUpperCase()}/${data.p1_state.toUpperCase()}.png)'></div>
        `);

        SetInnerHtml($(".p2 .flagcountry"), `
            <div class='flag' style='background-image: url(../../assets/country_flag/${data.p2_country.toLowerCase()}.png)'></div>
        `);

        SetInnerHtml($(".p1 .flagstate"), `
            <div class='flag' style='background-image: url(../../assets/state_flag/${data.p2_country.toUpperCase()}/${data.p2_state.toUpperCase()}.png)'></div>
        `);

        SetInnerHtml($(".p1 .stockicon"), `
            <div class="icon" style='background-image: url(../../${data.p1_assets_path["base_files/icon"]})'></div>
        `);

        SetInnerHtml($(".p2 .stockicon"), `
            <div class="icon" style='background-image: url(../../${data.p2_assets_path["base_files/icon"]})'></div>
        `);

        SetInnerHtml($(".p1 .score"), String(data.score_left));
        SetInnerHtml($(".p2 .score"), String(data.score_right));

        SetInnerHtml($(".phase"), data.tournament_phase + (data.best_of != 0 ? " - Best of " + data.best_of : ""));
    }

    $(window).on("load", () => {
        $('body').fadeTo(500, 1, async () => {
            Start();
            setInterval(Update, 1000);
        });
    });
})(jQuery);