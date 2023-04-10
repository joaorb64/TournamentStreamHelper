var data = {};
var oldData = {};
var tsh_settings = {};

var Start = async () => {
  console.log("Start(): Implement me");
};

var Update = async (event) => {
  console.log("Update(): Implement me");
};

async function UpdateWrapper(event) {
  await Update(event);

  window.requestAnimationFrame(() => {
    if (gsap.globalTimeline.timeScale() == 0) {
      $(document).waitForImages(function () {
        $("body").fadeTo(1, 1, () => {
          Start();
          gsap.globalTimeline.timeScale(1);
        });
      });
    }
  });
}

async function UpdateData() {
  oldData = data;
  data = await getData();
  let event = new CustomEvent("tsh_update");
  event.data = data;
  event.oldData = oldData;

  if (JSON.stringify(data) != JSON.stringify(oldData)) {
    document.dispatchEvent(event);
  }
}

async function LoadEverything() {
  let libPath = "../include/";
  let scripts = [
    "jquery-3.6.0.min.js",
    "gsap.min.js",
    "he.js",
    "lodash.min.js",
    "kuroshiro.min.js",
    "kuroshiro-analyzer-kuromoji.min.js",
    "jquery.waitforimages.min.js",
    "color-thief.min.js",
    "assetUtils.js",
  ];

  for (let i = 0; i < scripts.length; i += 1) {
    const script = scripts[i];
    const src = libPath + script;
    try {
      await new Promise((resolve, reject) => {
        const scriptElement = document.createElement("script");
        scriptElement.src = src;
        scriptElement.onload = resolve;
        scriptElement.onerror = reject;
        document.head.appendChild(scriptElement);
      });
      console.log(`Loaded script: ${src}`);
    } catch (error) {
      console.error(`Error loading script: ${src}`, error);
      throw error;
    }
  }

  console.log("== Loading complete ==");

  await InitAll();
}

async function InitAll() {
  await LoadSettings();
  await LoadKuroshiro();

  setInterval(async () => {
    await UpdateData();
  }, 32);

  console.log("== Init complete ==");
  document.dispatchEvent(new CustomEvent("tsh_init"));

  document.addEventListener("tsh_update", UpdateWrapper);
  gsap.globalTimeline.timeScale(0);
}

function getData() {
  return $.ajax({
    dataType: "json",
    url: "../../out/program_state.json",
    cache: false,
  });
}

async function LoadSettings() {
  try {
    let global_settings = await $.ajax({
      dataType: "json",
      url: "../settings.json",
      cache: false,
    });
    let file_settings = await $.ajax({
      dataType: "json",
      url: "./settings.json",
      cache: false,
    });
    tsh_settings = _.defaultsDeep(file_settings, global_settings);
  } catch (e) {
    console.log("Could not load settings.json");
    console.log(e);
  }
}

function RegisterFit(element) {
  if (!$(element).hasClass("tsh-fit-content")) {
    if ($(element).get(0)) {
      $(element).addClass("tsh-fit-content");
      divResizeObserver.observe($(element).get(0));
    }
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
  let settings = _.defaultsDeep(tsh_settings.japanese_transcription, {
    enabled: true,
    to: "romaji",
    mode: "normal",
    romajiSystem: "nippon",
  });

  if (text == null || text.length == 0 || !settings.enabled) return text;

  try {
    if (window.Kuroshiro.default.Util.hasJapanese(text)) {
      return window.kuroshiro
        .convert(text, {
          mode: settings.mode,
          to: settings.to,
          romajiSystem: settings.romajiSystem,
        })
        .then((res) => {
          return `${text}<span class="tsh_transcript">&nbsp;${res}</span>`;
        });
    } else {
      return text;
    }
  } catch (e) {
    console.log(e);
    return text;
  }
}

async function SetInnerHtml(element, html, settings = {}) {
  let force = undefined;
  let fadeTime = 0.5;
  let middleFunction = undefined;

  if (element == null) return;
  if (force == false) return;

  // Fade out/in animations
  let anim_in = { autoAlpha: 1, duration: fadeTime, stagger: 0.1 };

  if (settings.anim_in) {
    anim_in = settings.anim_in;
  }

  let anim_out = { autoAlpha: 0, duration: fadeTime, stagger: 0.1 };

  if (settings.anim_out) {
    anim_out = settings.anim_out;
  }

  anim_out.overwrite = true;

  if (html == null || html == undefined) html = "";

  html = String(html);

  let firstRun = false;

  // First run, no need of smooth fade out
  if (element.find(".text").length == 0) {
    // Put any text inside the div just so the font loading is triggered
    element.html("<div class='text' style='opacity: 0;'>&nbsp;</div>");
    firstRun = true;
  }

  // Wait for font to load before calculating sizes
  document.fonts.ready.then(() => {
    if (
      force == true ||
      he.decode(String(element.find(".text").html()).replace(/'/g, '"')) !=
        he.decode(String(html).replace(/'/g, '"'))
    ) {
      const callback = () => {
        element.find(".text").html(html);
        if (html.length == 0) {
          element.find(".text").addClass("text_empty");
        } else {
          element.find(".text").removeClass("text_empty");
        }
        FitText(element);
        if (middleFunction != undefined) {
          middleFunction();
        }
        $(element).ready((e) => {
          gsap.fromTo(element.find(".text"), anim_out, anim_in);
        });
      };

      if (!firstRun) {
        gsap.to(element.find(".text"), anim_out).then(() => callback());
      } else {
        gsap.set(element.find(".text"), anim_out).then(() => callback());
      }
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
  if (width > image.width || height > image.height) {
    return image.src;
  }

  // Initialize the canvas and it's size
  const canvas = document.createElement("canvas");
  const ctx = canvas.getContext("2d");

  // Set width and height
  canvas.width = width;
  canvas.height = height;

  ctx.imageSmoothingQuality = "medium";
  ctx.imageSmoothingEnabled = true;

  // Draw image and export to a data-uri
  ctx.drawImage(image, 0, 0, canvas.width, canvas.height);
  const dataURI = canvas.toDataURL("image/webp");

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
  try {
    options = _.defaultsDeep(options, {
      custom_zoom: 1,
      custom_center: [0.5, 0.5],
      scale_based_on_parent: false,
      scale_fill_x: false,
      scale_fill_y: false,
    });

    if (!assetData) {
      reject();
    }

    options.asset_data = assetData;

    $(element).data(options);

    await CenterImageDo($(element)).then(() => {
      if (!$(element).hasClass("tsh-center-image")) {
        $(element).addClass("tsh-center-image");
        imageResizeObserver.observe($(element).get(0));
      }
    });
  } catch (e) {
    console.log(e);
  }
}

async function CenterVideo(element, assetData, options = {}) {
  function loadImage() {
    return new Promise((resolve) => {
      var video = $("<video />", {
        src: "../../" + assetData.asset,
        muted: true,
        autoplay: true,
      });

      $(element).css({
        position: "relative",
      });

      video.css({
        height: "100%",
        "min-width": 0,
        "min-height": 0,
        position: "absolute",
      });

      video.muted = true;
      video.autoplay = true;

      video.appendTo($(element)).unwrap();

      video.on("loadedmetadata", async () => {
        $(video)[0].muted = true;
        await $(video)[0].play();
        resolve();
      });

      video[0].load();
    });
  }

  await loadImage();
}

async function CenterImageDo(element) {
  try {
    let data = $(element).data();

    let assetData = data.asset_data;
    let customZoom = data.custom_zoom;
    let customCenter = data.custom_center;
    let scale_based_on_parent = data.scale_based_on_parent;
    let scale_fill_x = data.scale_fill_x;
    let scale_fill_y = data.scale_fill_y;

    let customElement = null;

    if (scale_based_on_parent) {
      customElement = element.parent().parent();
    }

    if (typeof assetData == "string") {
      assetData = JSON.parse(assetData);
    }
    if (!assetData) return;

    let image = 'url("../../' + assetData.asset + '")';

    if (image != undefined && image.includes("url(")) {
      function loadImage() {
        return new Promise((resolve) => {
          const img = new Image();
          img.src = "../../" + assetData.asset;
          img.onload = async () => {
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
                ($(customElement).innerHeight() / assetData.average_size.y) *
                  1.2
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
              xx =
                -eyesight.x * zoom + $(element).innerWidth() * customCenter[0];
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
              yy =
                -eyesight.y * zoom + $(element).innerHeight() * customCenter[1];
            }

            let maxMoveY = $(element).innerHeight() - img.naturalHeight * zoom;

            if (!uncropped_edge || !uncropped_edge.includes("u")) {
              if (yy > 0) yy = 0;
            }
            if (!uncropped_edge || !uncropped_edge.includes("d")) {
              if (yy < maxMoveY) yy = maxMoveY;
            }

            if (data.use_dividers === false) {
              $(element).parent().css("position", "absolute");
            }

            if (data.z_index) {
              $(element).parent().css("z-index", data.z_index);
            } else {
              $(element).parent().css("z-index", 0);
            }

            $(element)
              .css({
                "background-position": `
              ${xx}px
              ${yy}px
            `,
                "background-size": `
              ${img.naturalWidth * zoom}px
              ${img.naturalHeight * zoom}px
            `,
                "background-repeat": "no-repeat",
                "background-image":
                  "url(" +
                  resizeInCanvas(
                    img,
                    img.naturalWidth * zoom,
                    img.naturalHeight * zoom
                  ) +
                  ")",
              })
              .promise();

            //element.css("background-position", "initial");
            //element.css("position", "fixed");
            //element.css("width", img.naturalWidth * zoom);
            //element.css("height", img.naturalHeight * zoom);
            resolve();
          };
        });
      }

      await loadImage();
    }
  } catch (e) {
    console.log(e);
  }
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
