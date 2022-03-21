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
  let fontSize = parseFloat(target.css("font-size").split("px")[0]);

  while (textElement[0].scrollWidth > target.width() && fontSize > 0) {
    fontSize -= 0.1;
    textElement.css("font-size", fontSize + "px");
  }
}

function SetInnerHtml(
  element,
  html,
  force = undefined,
  fadeTime = 0.5,
  middleFunction = undefined
) {
  if (element == null) return;
  if (force == false) return;

  let fadeOutTime = fadeTime;
  let fadeInTime = fadeTime;

  if (html == null || html == undefined) html = "";

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
      he.decode(String(element.find(".text").html()).replace(/'/g, '"')) !=
        he.decode(String(html).replace(/'/g, '"'))
    ) {
      gsap.to(element.find(".text"), {
        autoAlpha: 0,
        duration: fadeOutTime,
        onComplete: () => {
          element.find(".text").html(html);
          FitText(element);
          if (middleFunction != undefined) {
            middleFunction();
          }
          gsap.to(element.find(".text"), {
            autoAlpha: 1,
            duration: fadeInTime,
          });
        },
      });
    }
  });
}

function CenterImage(element, eyesight) {
  let image = element.css("background-image");

  console.log("CenterImage", image);

  if (image != undefined && image.includes("url(")) {
    let img = new Image();
    img.src = image.split('url("')[1].split('")')[0];

    $(img).on("load", () => {
      console.log(element);
      console.log(eyesight.x, img.naturalWidth);
      console.log(eyesight.x / img.naturalWidth);
      element.css(
        "background-position",
        `${(eyesight.x / img.naturalWidth) * 100}% ${
          (eyesight.y / img.naturalHeight) * 100
        }%`
      );
    });
  }
}
