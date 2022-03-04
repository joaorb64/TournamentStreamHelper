function getData() {
  return $.ajax({
    dataType: "json",
    url: "../../out/program_state.json",
    cache: false,
  });
}

function FitText(target) {
  if (target == null) return;
  if (target.css("font-size") == null) return;
  if (target.css("width") == null) return;

  let textElement = target.find(".text");

  if (textElement.text().trim().toLowerCase() == "undefined") {
    textElement.html("");
  }

  textElement.css("font-size", "");
  let fontSize = parseInt(target.css("font-size").split("px")[0]);

  while (textElement[0].scrollWidth > target.width() && fontSize > 0) {
    fontSize--;
    textElement.css("font-size", fontSize + "px");
  }
}

function SetInnerHtml(element, html, force = undefined, fadeTime = 0.5) {
  if (element == null) return;
  if (force == false) return;

  let fadeOutTime = fadeTime;
  let fadeInTime = fadeTime;

  if (html == null) html = "";

  html = String(html);

  // First run, no need of smooth fade out
  if (element.find(".text").length == 0) {
    // Put any text inside the div just so the font loading is triggered
    element.html("<div class='text'>&nbsp;</div>");
    fadeOutTime = 0;
  }

  // Wait for font to load before calculating sizes
  document.fonts.ready.then(() => {
    if (
      force == true ||
      he.decode(element.find(".text").html().replace(/'/g, '"')) !=
        he.decode(html.replace(/'/g, '"'))
    ) {
      gsap.to(element.find(".text"), {
        autoAlpha: 0,
        duration: fadeOutTime,
        onComplete: () => {
          element.find(".text").html(html);
          FitText(element);
          gsap.to(element.find(".text"), {
            autoAlpha: 1,
            duration: fadeInTime,
          });
        },
      });
    }
  });
}
