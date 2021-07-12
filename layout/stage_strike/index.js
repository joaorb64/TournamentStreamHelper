(($) => { 
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

    Update();
    $(window).on("load", () => {
        $('body').fadeTo(500, 1, async () => {
            Start();
            setInterval(Update, 1000);
        });
    });
})(jQuery);