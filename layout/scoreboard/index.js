(($) => {
    function getData() {
        return $.ajax({
            dataType: 'json',
            url: '../../out/program_state.json',
            cache: false,
        });
    }

    function FitText(target) {
        let fontSize = parseInt(target.css("font-size").split('px')[0]);
        let textElement = target.find(".text");

        while(textElement.width() > parseInt(target.css("width").split('px')[0]) && fontSize > 0) {
            fontSize--
            textElement.css("font-size", fontSize+"px");
        }
    }

    function SetInnerHtml(element, html){
        let fadeOutTime = 0.5;
        let fadeInTime = 0.5;

        if(html == null) html = "";

        // First run, no need of smooth fade out
        if(element.find(".text").length == 0){
            element.html("<div class='text'></div>");
            fadeOutTime = 0;
        };

        html = html.replaceAll("'", '"');

        if(element.find(".text").html() != html){
            gsap.to(element.find(".text"), { autoAlpha: 0, duration: fadeOutTime, onComplete: ()=>{
                element.find(".text").html(html);
                FitText(element);
                gsap.to(element.find(".text"), { autoAlpha: 1, duration: fadeInTime });
            } });
        }
    }
    
    let startingAnimation = gsap.timeline({ paused: true })
        .from(['.container'], { duration: 1, width: '0', ease: "power2.inOut" }, 0)
        .from(['.phase'], { duration: 1, opacity: '0', ease: "power2.inOut" }, 0)
    startingAnimation.eventCallback("onComplete", Update)
            
    function Start(){
        startingAnimation.restart();
    }

    async function Update(){
        let data = await getData();

        SetInnerHtml($(".p1 .name"), `
            <span>
                <span class='sponsor'>
                    ${data.p1_org ? (data.p1_org+"&nbsp;") : ""}
                </span>
                ${data.p1_name}
            </span>
        `);

        SetInnerHtml($(".p2 .name"), `
            <span>
                <span class='sponsor'>
                    ${data.p2_org ? (data.p2_org+"&nbsp;") : ""}
                </span>
                ${data.p2_name}
            </span>
        `);
        
        SetInnerHtml($(".p1 .twitter"), data.p1_twitter);
        SetInnerHtml($(".p2 .twitter"), data.p2_twitter);

        SetInnerHtml($(".p1 .flagcountry"), `
            <div class='flag' style='background-image: url(../../country_icon/${data.p1_country.toLowerCase()}.png)'></div>
        `);

        SetInnerHtml($(".p1 .flagstate"), `
            <div class='flag' style='background-image: url(../../out/p1_state_flag.png)'></div>
        `);

        SetInnerHtml($(".p2 .flagcountry"), `
            <div class='flag' style='background-image: url(../../country_icon/${data.p2_country.toLowerCase()}.png)'></div>
        `);

        SetInnerHtml($(".p2 .flagstate"), `
            <div class='flag' style='background-image: url(../../out/p2_state_flag.png)'></div>
        `);

        SetInnerHtml($(".p1 .stockicon"), `
            <div class="icon" style='background-image: url(../../character_icon/chara_2_${data.p1_character_codename}_0${data.p1_character_color}.png)'></div>
        `);

        SetInnerHtml($(".p2 .stockicon"), `
            <div class="icon" style='background-image: url(../../character_icon/chara_2_${data.p2_character_codename}_0${data.p2_character_color}.png)'></div>
        `);

        SetInnerHtml($(".p1 .score"), String(data.score_left));
        SetInnerHtml($(".p2 .score"), String(data.score_right));

        SetInnerHtml($(".phase"), data.tournament_phase);
    }

    $(document).ready(() => {
        $('body').fadeIn(500, async () => {
            Start();
            setInterval(Update, 1000);
        });
    });
})(jQuery);