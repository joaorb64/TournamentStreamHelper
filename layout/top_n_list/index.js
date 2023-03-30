LoadEverything().then(() => {
  var ASSET_TO_USE = "full";
  var ZOOM = 1;

  gsap.config({ nullTargetWarn: false, trialWarn: false });

  let startingAnimation = gsap
    .timeline({ paused: true })
    .from([".container"], { duration: 1, ease: "power2.inOut" }, 0);

  function Start() {
    startingAnimation.restart();
  }

  var data = {};
  var oldData = {};

  async function Update(event) {
    let data = event.data;
    let oldData = event.oldData;

    if (
      !oldData.player_list ||
      JSON.stringify(data.player_list) != JSON.stringify(oldData.player_list)
    ) {
      let htmls = [];

      Object.values(data.player_list.slot).forEach((slot, i) => {
        let html = `<div class="slot slot${i + 1}">`;

        Object.values(slot.player).forEach((player, p) => {
          html += `
            <div class="p${p + 1} player container">
              <div class="score">${
                // TODO: Standings formula
                Array(1, 2, 3, 4, 5, 5, 7, 7, 17, 17, 17, 17, 21, 21, 21, 21)[i]
              }</div>
              <div class="icon avatar"></div>
              <div class="icon online_avatar"></div>
              <div class="name_twitter">
              <div class="name"></div>
              <div class="twitter"></div>
              </div>
              <div class="sponsor_icon"></div>
              <div class="flags">
                <div class="flagcountry"></div>
                ${player.state.asset ? `<div class="flagstate"></div>` : ""}
              </div>
              <div class="filler"></div>
              <div class="character_container"></div>
            </div>
          `;
        });

        html += "</div>";

        htmls.push(html);
      });

      $(".players_container").html("");

      for (let i = 0; i < htmls.length; i++) {
        let html = htmls[i];
        $(".players_container").html($(".players_container").html() + html);
      }

      Object.values(data.player_list.slot).forEach((slot, t) => {
        SetInnerHtml($(`.slot${t + 1} .title`), slot.name);
        Object.values(slot.player).forEach((player, p) => {
          if (player) {
            SetInnerHtml(
              $(`.slot${t + 1} .p${p + 1}.container .name`),
              `
            <span>
              <span class="sponsor">
                ${player.team ? player.team : ""}
              </span>
              ${player.name}
            </span>
            `,
              undefined,
              0
            );

            SetInnerHtml(
              $(`.slot${t + 1} .p${p + 1}.container .flagcountry`),
              player.country.asset
                ? `<div class='flag' style='background-image: url(../../${player.country.asset.toLowerCase()})'></div>`
                : "",
              undefined,
              0
            );

            SetInnerHtml(
              $(`.slot${t + 1} .p${p + 1}.container .flagstate`),
              player.state.asset
                ? `<div class='flag' style='background-image: url(../../${player.state.asset})'></div>`
                : "",
              undefined,
              0
            );

            CharacterDisplay(
              $(`.slot${t + 1} .p${p + 1}.container .character_container`),
              {
                source: `player_list.slot.${t + 1}`,
                custom_center: [0.5, 0.4],
                custom_element: -2,
              }
            );

            SetInnerHtml(
              $(`.slot${t + 1} .p${p + 1}.container .sponsor_icon`),
              player.sponsor_logo
                ? `<div style='background-image: url(../../${player.sponsor_logo})'></div>`
                : "<div></div>",
              undefined,
              0
            );

            SetInnerHtml(
              $(`.slot${t + 1} .p${p + 1}.container .avatar`),
              player.avatar
                ? `<div style="background-image: url('../../${player.avatar}')"></div>`
                : "",
              undefined,
              0
            );

            SetInnerHtml(
              $(`.slot${t + 1} .p${p + 1}.container .online_avatar`),
              player.online_avatar
                ? `<div style="background-image: url('${player.online_avatar}')"></div>`
                : '<div style="background: gray)"></div>',
              undefined,
              0
            );

            SetInnerHtml(
              $(`.slot${t + 1} .p${p + 1}.container .twitter`),
              player.twitter
                ? `<span class="twitter_logo"></span>${String(player.twitter)}`
                : "",
              undefined,
              0
            );

            SetInnerHtml(
              $(`.slot${t + 1} .p${p + 1}.container .sponsor-container`),
              `<div class='sponsor-logo' style='background-image: url(../../${player.sponsor_logo})'></div>`,
              undefined,
              0
            );
          }
        });

        gsap.from(
          $(`.slot${t + 1}`),
          { x: -100, autoAlpha: 0, duration: 0.4, delay: 0 },
          0.5 + 0.3 * t
        );
      });
    }
  }

  $("body").fadeTo(1, 1, async () => {
    Start();
  });
  document.addEventListener("tsh_update", Update);
});
