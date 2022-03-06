(($) => {
  // Change this to the name of the assets pack you want to use
  // It's basically the folder name: user_data/games/game/ASSETPACK
  var ASSET_TO_USE = "full";

  // Change this to select wether to flip P2 character asset or not
  // Set it to true or false
  var FLIP_P2_ASSET = false;

  let startingAnimation = gsap
    .timeline({ paused: true })
    .from([".phase"], { duration: 0.8, opacity: "0", ease: "power2.inOut" }, 0)
    .from(
      [".score_container"],
      { duration: 0.8, opacity: "0", ease: "power2.inOut" },
      0
    )
    .from(
      [".best_of"],
      { duration: 0.8, opacity: "0", ease: "power2.inOut" },
      0
    )
    .from([".vs"], { duration: 0.4, opacity: "0", scale: 4, ease: "out" }, 0.5)
    .from([".p1.character"], { duration: 1, x: "-200px", ease: "out" }, 0)
    .from([".p1.container"], { duration: 1, x: "-100px", ease: "out" }, 0)
    .from([".p2.character"], { duration: 1, x: "200px", ease: "out" }, 0)
    .from([".p2.container"], { duration: 1, x: "100px", ease: "out" }, 0);

  function Start() {
    startingAnimation.restart();
  }

  var data = {};
  var oldData = {};

  async function Update() {
    oldData = data;
    data = await getData();

    ["p1", "p2"].forEach((p) => {
      SetInnerHtml(
        $(`.${p} .name`),
        `
                <span>
                    <span class='sponsor'>
                        ${data[p + "_org"] ? data[p + "_org"] + "&nbsp;" : ""}
                    </span>
                    ${data[p + "_name"]}
                    ${data[p + "_losers"] ? " [L]" : ""}
                </span>
            `
      );

      SetInnerHtml(
        $(`.${p} .sponsor_logo`),
        data[p + "_org"]
          ? `
                    <div>
                        <div class='sponsor_logo' style='background-image: url(../../sponsor_logos/${data[
                          p + "_org"
                        ].toUpperCase()}.png)'></div>
                    </div>`
          : "",
        oldData[p + "_org"] != data[p + "_org"]
      );

      SetInnerHtml($(`.${p} .real_name`), `${data[p + "_real_name"]}`);

      SetInnerHtml(
        $(`.${p} .twitter`),
        `
                ${
                  data[p + "_twitter"]
                    ? `
                    <div class="twitter_logo"></div>
                    ${data[p + "_twitter"]}
                    `
                    : ""
                }
            `
      );

      SetInnerHtml(
        $(`.${p} .flagcountry`),
        data[p + "_country"]
          ? `
                    <div>
                        <div class='flag' style='background-image: url(../../assets/country_flag/${data[
                          p + "_country"
                        ].toLowerCase()}.png)'>
                            <div class="flagname">${data[
                              p + "_country"
                            ].toUpperCase()}</div>
                        </div>
                    </div>`
          : ""
      );

      SetInnerHtml(
        $(`.${p} .flagstate`),
        data[p + "_state"]
          ? `
                    <div>
                        <div class='flag' style='background-image: url(../../assets/state_flag/${data[
                          p + "_country"
                        ].toUpperCase()}/${data[
              p + "_state"
            ].toUpperCase()}.png)'>
                            <div class="flagname">${data[
                              p + "_state"
                            ].toUpperCase()}</div>
                        </div>
                    </div>`
          : ""
      );

      if (
        oldData[p + "_character_codename"] != data[p + "_character_codename"] ||
        oldData[p + "_character_color"] != data[p + "_character_color"]
      ) {
        if (!data[p + "_assets_path"][ASSET_TO_USE].endsWith(".webm")) {
          // if asset is a image, add a image element
          $(`.${p}.character`).html(`
                        <div class="bg">
                            <div
                                class="portrait"
                                style='
                                    background-image: url(../../${
                                      data[p + "_assets_path"][ASSET_TO_USE]
                                    });
                                    ${
                                      p == "p2" && FLIP_P2_ASSET
                                        ? "transform: scaleX(-1)"
                                        : ""
                                    }
                                '>
                            </div>
                        </div>
                    `);
        } else {
          // if asset is a video, add a video element
          $(`.${p}.character`).html(`
                        <div class="bg">
                            <video id="video_${p}" class="video" width="auto" height="100%" autoplay muted>
                                <source src="../../${
                                  data[p + "_assets_path"][ASSET_TO_USE]
                                }">
                            </video>
                        </div>
                    `);
        }

        gsap
          .timeline()
          .from(`.${p}.character .portrait`, { duration: 0.5, opacity: 0 })
          .from(`.${p}.character .portrait`, {
            duration: 0.4,
            filter: "brightness(0%)",
            onUpdate: function (tl) {
              var tlp = (this.progress() * 100) >> 0;
              TweenMax.set(`.${p}.character .portrait`, {
                filter: "brightness(" + tlp + "%)",
              });
            },
            onUpdateParams: ["{self}"],
          });
      }
    });

    SetInnerHtml($(`.p1 .score`), String(data.score_left));
    SetInnerHtml($(`.p2 .score`), String(data.score_right));

    SetInnerHtml($(".phase"), data.tournament_phase);
    SetInnerHtml($(".best_of"), data.best_of ? "Best of " + data.best_of : "");
  }

  // Using update here to set images as soon as possible
  // so that on window.load they are already preloaded
  Update();
  $(window).on("load", () => {
    $("body").fadeTo(0, 1, async () => {
      Start();
      setInterval(Update, 1000);
    });
  });
})(jQuery);
