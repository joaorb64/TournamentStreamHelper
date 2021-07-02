(($) => {
    let startingAnimation = gsap.timeline({ paused: true })
            
    function Start(){
        startingAnimation.restart();
    }

    var data = {}
    var oldData = {}

    async function Update(){
        oldData = data;
        data = await getData();

        if(oldData.p1_smashgg_id != data.p1_smashgg_id){
            $('.main').attr("src", "https://powerrankings.gg/ssbu/headtohead?p1="+data.p1_smashgg_id+"&p2="+data.p2_smashgg_id+"&fullscreen=true")
        }
    }

    $(document).ready(() => {
        $('body').fadeIn(500, async () => {
            Start();
            setInterval(Update, 1000);
        });
    });
})(jQuery);