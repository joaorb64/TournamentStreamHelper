(($) => { 
    function Start(){
        
    }

    var data = {}
    var oldData = {}

    let oldCharacters = {}

    async function Update(){
        oldData = data;
        data = await getData();

        let characters = data.score.team1.players["1"].character;

        if(JSON.stringify(characters) != JSON.stringify(oldCharacters)){
            oldCharacters = characters;

            assetToUse = "portrait";
            characterAssets = []
    
            Object.values(characters).forEach((character)=>{
                if(character.assets){
                    if(character.assets.hasOwnProperty(assetToUse)){
                        characterAssets.push(character.assets[assetToUse])
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

    let cycleIndex = 0;
    let imgs = [];

    function crossfade(){
        TweenMax.to(imgs[(cycleIndex+imgs.length-1)%imgs.length], 1, {autoAlpha:0})
        TweenMax.to(imgs[cycleIndex], 1, {autoAlpha:1})
        $(".index_display").html(`${cycleIndex+1}/${imgs.length}`)
        cycleIndex = (cycleIndex+1)%imgs.length;
    }
    
    var cycle = setInterval(crossfade, 2000)

    Update();
    $(window).on("load", () => {
        $('body').fadeTo(500, 1, async () => {
            Start();
            setInterval(Update, 1000);
        });
    });
})(jQuery);