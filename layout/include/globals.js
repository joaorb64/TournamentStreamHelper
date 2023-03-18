var data = {};
var oldData = {};

async function UpdateData() {
  oldData = data;
  data = await getData();
  let event = new CustomEvent("tsh_update");
  event.data = data;
  event.oldData = oldData;
  document.dispatchEvent(event);
}

async function LoadEverything() {
  let libPath = "../include/";
  let scripts = [
    "kuroshiro.min.js",
    "kuroshiro-analyzer-kuromoji.min.js",
    "jquery-3.6.0.min.js",
    "gsap.min.js",
    "he.js",
    "lodash.min.js",
    "assetUtils.js",
  ];

  let loadPromises = [];

  for (let i = 0; i < scripts.length; i += 1) {
    let script = document.createElement("script");
    script.src = libPath + scripts[i];
    document.head.appendChild(script);
    loadPromises.push(
      new Promise((resolve, reject) => {
        script.onload = () => {
          console.log(`Loaded script: ${libPath + scripts[i]}`);
          resolve();
        };
        script.onerror = () => {
          console.log(`Error loading script: ${libPath + scripts[i]}`);
          reject();
        };
      })
    );
  }

  return Promise.all(loadPromises).then(async (values) => {
    console.log("== Loading complete ==");
    await InitAll();
  });
}

async function InitAll() {
  await LoadKuroshiro();

  setInterval(async () => {
    await UpdateData();
  }, 200);

  console.log("== Init complete ==");
  document.dispatchEvent(new CustomEvent("tsh_init"));
}

function getData() {
  return $.ajax({
    dataType: "json",
    url: "../../out/program_state.json",
    cache: false,
  });
}

function RegisterFit(element) {
  if (!$(element).hasClass("tsh-fit-content")) {
    $(element).addClass("tsh-fit-content");
    divResizeObserver.observe($(element).get(0));
  }
}

function FitText(target) {
  document.fonts.ready.then(() => {
    if (target == null) return;
    if (target.css("font-size") == null) return;
    if (target.css("width") == null) return;

    let textElement = target.find(".text");
    RegisterFit(target);

    if (textElement.text().trim().toLowerCase() == "undefined") {
      textElement.html("");
    }

    textElement.css("transform", "");
    let scaleX = 1;

    if (textElement[0].scrollWidth * scaleX > target.width()) {
      scaleX = target.width() / textElement[0].scrollWidth;
      textElement.css("transform", "scaleX(" + scaleX + ")");
    }
  });
}

async function LoadKuroshiro() {
  window.kuroshiro = new Kuroshiro.default();
  await window.kuroshiro.init(
    new KuromojiAnalyzer({
      dictPath: "../include/kuromoji",
    })
  );
}

async function Transcript(text) {
  if (text == null || text.length == 0) return text;

  try {
    if (window.Kuroshiro.default.Util.hasJapanese(text)) {
      return window.kuroshiro
        .convert(text, {
          mode: "furigana",
          to: "romaji",
          romajiSystem: "nippon",
        })
        .then((res) => {
          return res;
        });
    } else {
      return text;
    }
  } catch {
    return text;
  }
}

async function SetInnerHtml(
  element,
  html,
  force = undefined,
  fadeTime = 0.5,
  middleFunction = undefined,
  options = {}
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
          $(element).ready((e) => {
            gsap.to(element.find(".text"), {
              autoAlpha: 1,
              duration: fadeInTime,
            });
          });
        },
      });
    }
  });
}

const degrees_to_radians = (deg) => (deg * Math.PI) / 180.0;

function GenerateMulticharacterPositions(
  character_number,
  center = [0.5, 0.5],
  radius = 0.3
) {
  let positions = [];

  // For 1 character, just center it
  if (character_number == 1) radius = 0;

  let angle_rad = degrees_to_radians(90);

  if (character_number == 2) angle_rad = degrees_to_radians(45);

  let pendulum = 1;

  for (let i = 0; i < character_number; i += 1) {
    let j = i;
    if (i > 1) {
      if (i % 2 == 0) {
        pendulum *= -1;
      } else {
        pendulum *= -1;
        pendulum += 1;
      }
      j = pendulum;
    }
    angle = angle_rad + degrees_to_radians(360 / character_number) * j;
    pos = [
      center[0] + Math.cos(angle) * radius,
      center[1] + Math.sin(angle) * radius,
    ];
    positions.push(pos);
  }

  return positions;
}

function resizeInCanvas(image, width, height) {
  // Initialize the canvas and it's size
  const canvas = document.createElement("canvas");
  const ctx = canvas.getContext("2d");

  // Set width and height
  canvas.width = width;
  canvas.height = height;

  ctx.imageSmoothingQuality = "high";
  ctx.imageSmoothingEnabled = true;

  // Draw image and export to a data-uri
  ctx.drawImage(image, 0, 0, canvas.width, canvas.height);
  const dataURI = canvas.toDataURL();

  canvas.remove();

  // Do something with the result, like overwrite original
  return dataURI;
}

var imageResizeObserver = new ResizeObserver((entries) => {
  for (const entry of entries) {
    console.log("Resized");
    CenterImageDo(entry.target);
  }
});

var divResizeObserver = new ResizeObserver((entries) => {
  for (const entry of entries) {
    FitText($(entry.target));
  }
});

async function CenterImage(element, assetData, options = {}) {
  return new Promise((accept, reject) => {
    try {
      options = _.defaults(options, {
        customZoom: 1,
        customCenter: null,
        customElement: null,
        scale_fill_x: false,
        scale_fill_y: false,
      });

      if (!assetData) {
        reject();
      }

      $(element).attr("data-assetData", JSON.stringify(assetData));
      $(element).attr("data-customZoom", JSON.stringify(options.customZoom));
      $(element).attr(
        "data-customCenter",
        JSON.stringify(options.customCenter)
      );
      $(element).attr(
        "data-customElement",
        JSON.stringify(options.customElement)
      );
      $(element).attr(
        "data-scale_fill_x",
        JSON.stringify(options.scale_fill_x)
      );
      $(element).attr(
        "data-scale_fill_y",
        JSON.stringify(options.scale_fill_y)
      );

      CenterImageDo($(element)).then(() => {
        if (!$(element).hasClass("tsh-center-image")) {
          $(element).addClass("tsh-center-image");
          $(element).ready(() => {
            imageResizeObserver.observe($(element).get(0));
          });
        }
        accept();
      });
    } catch (e) {
      console.log(e);
      reject();
    }
  });
}

async function CenterImageDo(element) {
  return new Promise((accept, reject) => {
    try {
      let assetData = JSON.parse($(element).attr("data-assetData"));
      let customZoom = JSON.parse($(element).attr("data-customZoom"));
      let customCenter = JSON.parse($(element).attr("data-customCenter"));
      let customElement = JSON.parse($(element).attr("data-customElement"));
      let scale_fill_x = JSON.parse($(element).attr("data-scale_fill_x"));
      let scale_fill_y = JSON.parse($(element).attr("data-scale_fill_y"));

      if (typeof assetData == "string") {
        assetData = JSON.parse(assetData);
      }
      if (!assetData) return;

      let image = 'url("../../' + assetData.asset + '")';

      if (image != undefined && image.includes("url(")) {
        let img = new Image();
        img.src = "../../" + assetData.asset;

        $(img).on("load", () => {
          let eyesight = assetData.eyesight;

          if (!eyesight) {
            eyesight = {
              x: img.naturalWidth / 2,
              y: img.naturalHeight / 2,
            };
          }

          if (!customElement) customElement = element;

          let proportional_zoom = 1;
          if (assetData.average_size) {
            proportional_zoom = 0;
            proportional_zoom = Math.max(
              proportional_zoom,
              ($(customElement).innerWidth() / assetData.average_size.x) * 1.2
            );
            proportional_zoom = Math.max(
              proportional_zoom,
              ($(customElement).innerHeight() / assetData.average_size.y) * 1.2
            );
          }

          // For cropped assets, zoom to fill
          // Calculate max zoom
          zoom_x = $(customElement).innerWidth() / img.naturalWidth;
          zoom_y = $(customElement).innerHeight() / img.naturalHeight;

          let minZoom = 1;

          let rescalingFactor = 1;

          if (assetData.rescaling_factor)
            rescalingFactor = assetData.rescaling_factor;

          let uncropped_edge = assetData.uncropped_edge;

          if (
            !uncropped_edge ||
            uncropped_edge == "undefined" ||
            uncropped_edge.length == 0
          ) {
            if (zoom_x > zoom_y) {
              minZoom = zoom_x;
            } else {
              minZoom = zoom_y;
            }
          } else {
            if (
              uncropped_edge.includes("u") &&
              uncropped_edge.includes("d") &&
              uncropped_edge.includes("l") &&
              uncropped_edge.includes("r")
            ) {
              minZoom = customZoom * proportional_zoom * rescalingFactor;
            } else if (
              !uncropped_edge.includes("l") &&
              !uncropped_edge.includes("r")
            ) {
              minZoom = zoom_x;
            } else if (
              !uncropped_edge.includes("u") &&
              !uncropped_edge.includes("d")
            ) {
              minZoom = zoom_y;
            } else {
              minZoom = customZoom * proportional_zoom * rescalingFactor;
            }
          }

          if (scale_fill_x && !scale_fill_y) {
            minZoom = zoom_x;
          } else if (scale_fill_y && !scale_fill_x) {
            minZoom = zoom_y;
          } else if (scale_fill_x && scale_fill_y) {
            minZoom = Math.max(zoom_x, zoom_y);
          }

          zoom = Math.max(minZoom, customZoom * minZoom);

          // Cetering
          let xx = 0;
          let yy = 0;

          if (!customCenter) {
            xx = -eyesight.x * zoom + $(element).innerWidth() / 2;
          } else {
            xx = -eyesight.x * zoom + $(element).innerWidth() * customCenter.x;
          }

          let maxMoveX = $(element).innerWidth() - img.naturalWidth * zoom;

          if (!uncropped_edge || !uncropped_edge.includes("l")) {
            if (xx > 0) xx = 0;
          }
          if (!uncropped_edge || !uncropped_edge.includes("r")) {
            if (xx < maxMoveX) xx = maxMoveX;
          }

          if (!customCenter) {
            yy = -eyesight.y * zoom + $(element).innerHeight() / 2;
          } else {
            yy = -eyesight.y * zoom + $(element).innerHeight() * customCenter.y;
          }

          let maxMoveY = $(element).innerHeight() - img.naturalHeight * zoom;

          if (!uncropped_edge || !uncropped_edge.includes("u")) {
            if (yy > 0) yy = 0;
          }
          if (!uncropped_edge || !uncropped_edge.includes("d")) {
            if (yy < maxMoveY) yy = maxMoveY;
          }

          $(element).css(
            "background-position",
            `
              ${xx}px
              ${yy}px
            `
          );

          $(element).css(
            "background-size",
            `
              ${img.naturalWidth * zoom}px
              ${img.naturalHeight * zoom}px
            `
          );
          $(element).css("background-repeat", "no-repeat");

          $(element)
            .css(
              "background-image",
              "url(" +
                resizeInCanvas(
                  img,
                  img.naturalWidth * zoom,
                  img.naturalHeight * zoom
                ) +
                ")"
            )
            .promise()
            .done(() => {
              accept();
            });

          //element.css("background-position", "initial");
          //element.css("position", "fixed");
          //element.css("width", img.naturalWidth * zoom);
          //element.css("height", img.naturalHeight * zoom);
        });
      }
    } catch (e) {
      console.log(e);
      reject();
    }
  });
}

async function FindImages(folder = "") {
  let flag = true;
  let counter = 1;
  const files = [];

  while (flag) {
    const filename = `${folder}/${counter}.png`;
    try {
      await $.get(filename);
      files.push(filename);
      counter += 1;
    } catch (e) {
      flag = false;
    }
  }

  return files;
}

function powerOf2(v) {
  return v && !(v & (v - 1));
}

function nextPow2(v) {
  var p = 2;
  while ((v >>= 1)) {
    p <<= 1;
  }
  return p;
}
