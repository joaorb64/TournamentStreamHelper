(($) => {
  // Change this to the name of the assets pack you want to use
  // It's basically the folder name: user_data/games/game/ASSETPACK
  var ASSET_TO_USE = "full";

  // Change this to select wether to flip P2 character asset or not
  // Set it to true or false
  var FLIP_P2_ASSET = true;

  // Amount of zoom to use on the assets. Use 1 for 100%, 1.5 for 150%, etc.
  var zoom = 1;

  let startingAnimation = gsap
    .timeline({ paused: true })
    .from([".phase"], { duration: 0.8, opacity: "0", ease: "power2.inOut" }, 0)
    .from([".match"], { duration: 0.8, opacity: "0", ease: "power2.inOut" }, 0)
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
    .from([".p1.container"], { duration: 1, x: "-100px", ease: "out" }, 0)
    .from([".p2.container"], { duration: 1, x: "100px", ease: "out" }, 0);

  async function Start() {
    startingAnimation.restart();
  }

  var data = {};
  var oldData = {};

  async function Update() {
    oldData = data;
    data = await getData();

    Object.values(data.score.team).forEach((team, t) => {
      Object.values(team.player).forEach((player, p) => {
        SetInnerHtml(
          $(`.p${t + 1} .name`),
          `
            <span>
                <div>
                  <span class='sponsor'>
                      ${player.team ? player.team : ""}
                  </span>
                  ${player.name}
                </div>
                ${team.losers ? "<span class='losers'>L</span>" : ""}
            </span>
          `
        );

        SetInnerHtml(
          $(`.p${t + 1} > .sponsor_logo`),
          player.sponsor_logo
            ? `
              <div class='sponsor_logo' style='background-image: url(../../${player.sponsor_logo})'></div>
              `
            : ""
        );

        SetInnerHtml($(`.p${t + 1} .real_name`), `${player.real_name}`);

        SetInnerHtml(
          $(`.p${t + 1} .twitter`),
          `
            ${
              player.twitter
                ? `
                <div class="twitter_logo"></div>
                ${player.twitter}
                `
                : ""
            }
        `
        );

        SetInnerHtml(
          $(`.p${t + 1} .flagcountry`),
          player.country.asset
            ? `
            <div>
                <div class='flag' style='background-image: url(../../${player.country.asset});'>
                    <div class="flagname">${player.country.code}</div>
                </div>
            </div>`
            : ""
        );

        SetInnerHtml(
          $(`.p${t + 1} .flagstate`),
          player.state.asset
            ? `
            <div>
                <div class='flag' style='background-image: url(../../${player.state.asset});'>
                    <div class="flagname">${player.state.code}</div>
                </div>
            </div>`
            : ""
        );

        if (
          !oldData.score ||
          JSON.stringify(player.character) !=
            JSON.stringify(
              oldData.score.team[String(t + 1)].player[String(p + 1)].character
            )
        ) {
          let html = "";
          let characters = Object.values(player.character);
          if (t == 0) characters = characters.reverse();
          let zIndexMultiplyier = 1;
          if (t == 1) zIndexMultiplyier = -1;
          characters.forEach((character, c) => {
            if (
              character &&
              character.assets &&
              character.assets[ASSET_TO_USE]
            ) {
              if (!character.assets[ASSET_TO_USE].asset.endsWith(".webm")) {
                // if asset is a image, add a image element
                html += `
                <div class="bg char${
                  t == 1 ? c : characters.length - 1 - c
                }" style="z-index: ${c * zIndexMultiplyier};">
                  <div class="portrait_container">
                    <div
                      class="portrait ${
                        !FLIP_P2_ASSET && t == 1 ? "invert_shadow" : ""
                      }"
                      style='
                          background-image: url(../../${
                            character.assets[ASSET_TO_USE].asset
                          });
                          ${
                            t == 1 && FLIP_P2_ASSET
                              ? "transform: scaleX(-1)"
                              : ""
                          }
                      '>
                      </div>
                    </div>
                </div>
                  `;
              } else {
                // if asset is a video, add a video element
                html += `
                <div class="bg char${
                  t == 1 ? c : characters.length - 1 - c
                }" style="z-index: ${c * zIndexMultiplyier};">
                  <video id="video_${p}" class="video" width="auto" height="100%" autoplay muted>
                    <source src="../../${character.assets[ASSET_TO_USE].asset}">
                  </video>
                </div>
                  `;
              }
            }
          });

          $(`.p${t + 1}.character`).html(html);

          if (t == 0) characters = characters.reverse();
          characters.forEach((character, c) => {
            if (character.assets[ASSET_TO_USE]) {
              CenterImage(
                $(`.p${t + 1}.character .char${c} .portrait`),
                character.assets[ASSET_TO_USE].eyesight,
                zoom
              );
            }
          });

          characters.forEach((character, c) => {
            if (character) {
              gsap.timeline().fromTo(
                [`.p${t + 1}.character .char${c}`],
                {
                  duration: 1,
                  x: zIndexMultiplyier * -800 + "px",
                  z: 0,
                  rotationY: zIndexMultiplyier * 15 * (c + 1),
                  ease: "out",
                },
                {
                  duration: 1,
                  x: 0,
                  z: -c * 50 + "px",
                  rotationY: zIndexMultiplyier * 15 * (c + 1),
                  ease: "out",
                },
                c / 6
              );

              gsap
                .timeline()
                .from(
                  `.p${t + 1}.character .char${c} .portrait_container`,
                  {
                    duration: 0.5,
                    opacity: 0,
                  },
                  c / 6
                )
                .from(`.p${t + 1}.character .char${c} .portrait_container`, {
                  duration: 0.4,
                  filter: "brightness(0%)",
                  onUpdate: function (tl) {
                    var tlp = (this.progress() * 100) >> 0;
                    TweenMax.set(
                      `.p${t + 1}.character .char${c} .portrait_container`,
                      {
                        filter: "brightness(" + tlp + "%)",
                      }
                    );
                  },
                  onUpdateParams: ["{self}"],
                });
            }
          });
        }
      });
    });

    SetInnerHtml($(`.p1 .score`), String(data.score.team["1"].score));
    SetInnerHtml($(`.p2 .score`), String(data.score.team["2"].score));

    SetInnerHtml($(".tournament"), data.tournamentInfo.tournamentName);
    SetInnerHtml($(".match"), data.score.match);

    SetInnerHtml(
      $(".phase"),
      data.score.phase ? `<div class="container">${data.score.phase}</div>` : ""
    );

    SetInnerHtml(
      $(".best_of"),
      data.score.best_of
        ? `<div class="container">Best of ${data.score.best_of}</div>`
        : ""
    );
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
