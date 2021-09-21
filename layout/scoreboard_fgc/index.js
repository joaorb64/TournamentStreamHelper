(($) => {
    let startingAnimation = gsap.timeline({ paused: true })
        .from(['.overlay'], { duration: 1, y: "-63px", ease: "power2.out" }, 0)
            
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
            <div class='flag' style='background-image: url(${data.p1_state_flag_url})'></div>
        `, oldData.p1_state != data.p1_state);

        SetInnerHtml($(".p2 .flagcountry"), `
            <div class='flag' style='background-image: url(../../assets/country_flag/${data.p2_country.toLowerCase()}.png)'></div>
        `);

        SetInnerHtml($(".p2 .flagstate"), `
            <div class='flag' style='background-image: url(${data.p2_state_flag_url})'></div>
        `, oldData.p2_state != data.p2_state);

        SetInnerHtml($(".p1 .score"), String(data.score_left));
        SetInnerHtml($(".p2 .score"), String(data.score_right));

        SetInnerHtml($(".phase"), data.tournament_phase + (data.best_of != 0 ? " - Best of " + data.best_of : ""));
    }

    $(window).on("load", () => {
        Update();
        $('body').fadeTo(10, 1, async () => {
            Start();
            setInterval(Update, 1000);
        });
    });
})(jQuery);