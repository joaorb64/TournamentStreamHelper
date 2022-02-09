(($) => { 
    function Start(){
        
    }

    var data = {}
    var oldData = {}

    async function Update(){
        oldData = data;
        data = await getData();

        if(JSON.stringify(data.score.stage_strike) != JSON.stringify(oldData.score.stage_strike)){
            html = "";
            Object.keys(data.score.stage_strike.stages).forEach((stage)=>{
                let path = data.score.stage_strike.stages[stage].path;
                html += `
                    <div class="stage-container">
                        <div class="stage-icon" style="background-image: url('../../${path}')">
                            ${data.score.stage_strike.striked.includes(stage) &&
                            !data.score.stage_strike.dsr.includes(stage)?
                                `<div class="stage-striked stamp"></div>`
                                :
                                ""
                            }
                            ${data.score.stage_strike.dsr.includes(stage) ?
                                `<div class="stage-dsr stamp"></div>`
                                :
                                ""
                            }
                            ${data.score.stage_strike.selected && data.score.stage_strike.selected.codename == stage ?
                                `<div class="stage-selected stamp"></div>`
                                :
                                ""
                            }
                            <div class="stage-name">
                                <div class="text">
                                    ${data.score.stage_strike.stages[stage].name}
                                </div>
                            </div>
                        </div>
                    </div>
                `
            })
            $('.container').html(html);
            $('.container').find('.stage-name').each(function(){FitText($(this))});
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