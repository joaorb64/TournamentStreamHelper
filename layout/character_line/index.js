(($) => { 
    function Start(){
        
    }

    var data = {}
    var oldData = {}

    let oldCharacters = {}

    async function Update(){
        oldData = data;
        data = await getData();

        let characters = data.score.team["1"].players["1"].character;

        if(JSON.stringify(characters) != JSON.stringify(oldCharacters)){
            oldCharacters = characters;

            assetToUse = "base_files/icon";
            characterAssets = []
    
            Object.values(characters).forEach((character)=>{
                if(character.assets){
                    if(character.assets.hasOwnProperty(assetToUse)){
                        characterAssets.push(character.assets[assetToUse])
                    } else {
                        characterAssets.push({})
                    }
                }
            })

            let elements = "";

            characterAssets.forEach((asset, i)=>{
                elements += `<div class="icon" id="character${i}" style='background-image: url(../../${asset.asset})'></div>`;
            })

            elements += `<div class="index_display"></div>`
    
            $(".container").html(elements);

            imgs = $.makeArray($('.icon'));
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