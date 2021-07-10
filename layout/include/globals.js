function getData() {
    return $.ajax({
        dataType: 'json',
        url: '../../out/program_state.json',
        cache: false,
    });
}

function FitText(target) {
    if (target == null) return;
    if (target.css("font-size") == null) return;
    if (target.css("width") == null) return;

    let textElement = target.find(".text");
    textElement.css("font-size", "");
    let fontSize = parseInt(target.css("font-size").split('px')[0]);

    while(textElement.width() > parseInt(target.css("width").split('px')[0]) && fontSize > 0) {
        fontSize--
        textElement.css("font-size", fontSize+"px");
    }
}

function SetInnerHtml(element, html, force=undefined){
    if(element == null) return;
    if(force == false) return;

    let fadeOutTime = 0.5;
    let fadeInTime = 0.5;

    if(html == null) html = "";

    // First run, no need of smooth fade out
    if(element.find(".text").length == 0){
        element.html("<div class='text'></div>");
        fadeOutTime = 0;
    };

    html = html.replace(/'/g, '"');

    if(force == true || element.find(".text").html() != html){
        gsap.to(element.find(".text"), { autoAlpha: 0, duration: fadeOutTime, onComplete: ()=>{
            element.find(".text").html(html);
            FitText(element);
            gsap.to(element.find(".text"), { autoAlpha: 1, duration: fadeInTime });
        } });
    }
}