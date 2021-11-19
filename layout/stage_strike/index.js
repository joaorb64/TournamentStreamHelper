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
            Object.keys(data.stage_strike.stages).forEach((stage)=>{
                let filename = data.stage_strike.stages[stage].filename;
                html += `
                    <div class="stage-container">
                        <div class="stage-icon" style="background-image: url('../../${data.asset_path}/stage_icon/${filename}.png')">
                            ${data.stage_strike.striked.includes(stage) &&
                            !data.stage_strike.dsr.includes(stage)?
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
                            <div class="stage-name">
                                <div class="text">
                                    ${stage}
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