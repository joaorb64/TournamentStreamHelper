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

    function SetInnerHtml(element, html, force=false){
        let fadeOutTime = 0.5;
        let fadeInTime = 0.5;

        if(html == null) html = "";

        // First run, no need of smooth fade out
        if(element.find(".text").length == 0){
            element.html("<div class='text'></div>");
            fadeOutTime = 0;
        };

        html = html.replaceAll("'", '"');

        if(force || element.find(".text").html() != html){
            gsap.to(element.find(".text"), { autoAlpha: 0, duration: fadeOutTime, onComplete: ()=>{
                element.find(".text").html(html);
                FitText(element);
                gsap.to(element.find(".text"), { autoAlpha: 1, duration: fadeInTime });
            } });
        }
    }
            
    function Start(){
        
    }

    var data = {}
    var oldData = {}

    async function Update(){
        oldData = data;
        data = await getData();

        if(JSON.stringify(data.stage_strike) != JSON.stringify(oldData.stage_strike)){
            html = "";
            data.stage_strike.stages.forEach((stage)=>{
                html += `
                    <div class="stage-container">
                        <div class="stage-icon" style="background-image: url('../../stage_icon/stage_2_${stage}.png')">
                            ${data.stage_strike.striked.includes(stage) ?
                                `<div class="stage-striked stamp"></div>`
                                :
                                ""
                            }
                            ${data.stage_strike.dsr.includes(stage) ?
                                `<div class="stage-dsr stamp"></div>`
                                :
                                ""
                            }
                            ${data.stage_strike.selected == stage ?
                                `<div class="stage-selected stamp"></div>`
                                :
                                ""
                            }
                        </div>
                    </div>
                `
            })
            $('.container').html(html);
        }
    }

    $(document).ready(() => {
        $('body').fadeIn(500, async () => {
            Start();
            setInterval(Update, 1000);
        });
    });
})(jQuery);