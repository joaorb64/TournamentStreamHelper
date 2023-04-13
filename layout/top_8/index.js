LoadEverything().then(() => {
  gsap.config({ nullTargetWarn: false, trialWarn: false });

  let startingAnimation = gsap
    .timeline({ paused: true })
    .from([".container"], { duration: 1, width: "0", ease: "power2.inOut" }, 0);

  Start = async (event) => {
    startingAnimation.restart();
  };

  Update = async (event) => {
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
              <div class="footer">
                <!-- <div class="icon avatar"></div> -->
                <!-- <div class="icon online_avatar"></div> -->
                <div class="name_twitter">
                  <div class="name"></div>
                  <div class="twitter"></div>
                </div>
                <div class="sponsor_icon"></div>
              </div>
              <div class="flags">
                <div class="flagcountry"></div>
                ${player.state.asset ? `<div class="flagstate"></div>` : ""}
              </div>
              <div class="character_container"></div>
            </div>
          `;
        });

        html += "</div>";

        htmls.push(html);
      });

      $(".top1_container").html("");
      $(".top4_container").html("");
      $(".top8_container").html("");

      for (let i = 0; i < htmls.length; i++) {
        let html = htmls[i];

        if (window.SAME_SIZE) {
          $(".top8_container").html($(".top8_container").html() + html);
        } else {
          if (i == 0) {
            $(".top1_container").html($(".top1_container").html() + html);
          } else if (i < 4) {
            $(".top4_container").html($(".top4_container").html() + html);
          } else {
            $(".top8_container").html($(".top8_container").html() + html);
          }
        }
      }

      for (const [t, slot] of Object.entries(data.player_list.slot)) {
        for (const [p, player] of Object.entries(slot.player)) {
          if (player) {
            SetInnerHtml(
              $(`.slot${parseInt(t)} .p${parseInt(p)}.container .name`),
              `
            <span>
              <span class="sponsor">
                ${player.team ? player.team : ""}
              </span>
              ${await Transcript(player.name)}
            </span>
            `,
              undefined,
              0
            );

            SetInnerHtml(
              $(`.slot${parseInt(t)} .p${parseInt(p)}.container .flagcountry`),
              player.country.asset
                ? `<div class='flag' style='background-image: url(../../${player.country.asset.toLowerCase()})'></div>`
                : "",
              undefined,
              0
            );

            SetInnerHtml(
              $(`.slot${parseInt(t)} .p${parseInt(p)}.container .flagstate`),
              player.state.asset
                ? `<div class='flag' style='background-image: url(../../${player.state.asset})'></div>`
                : "",
              undefined,
              0
            );

            let load_settings_path = "top_1";

            if (t == 1) load_settings_path = "top_1";
            else if (t <= 4) load_settings_path = "top_4";
            else if (t <= 8) load_settings_path = "top_8";

            if (window.SAME_SIZE) load_settings_path = "same_size";

            await CharacterDisplay(
              $(
                `.slot${parseInt(t)} .p${parseInt(
                  p
                )}.container .character_container`
              ),
              {
                source: `player_list.slot.${parseInt(t)}`,
                load_settings_path: load_settings_path,
              },
              event
            );

            SetInnerHtml(
              $(`.slot${parseInt(t)} .p${parseInt(p)}.container .sponsor_icon`),
              player.sponsor_logo
                ? `<div style='background-image: url(../../${player.sponsor_logo})'></div>`
                : "<div></div>",
              undefined,
              0
            );

            SetInnerHtml(
              $(`.slot${parseInt(t)} .p${parseInt(p)}.container .avatar`),
              player.avatar
                ? `<div style="background-image: url('../../${player.avatar}')"></div>`
                : "",
              undefined,
              0
            );

            SetInnerHtml(
              $(
                `.slot${parseInt(t)} .p${parseInt(p)}.container .online_avatar`
              ),
              player.online_avatar
                ? `<div style="background-image: url('${player.online_avatar}')"></div>`
                : "",
              undefined,
              0
            );

            SetInnerHtml(
              $(`.slot${parseInt(t)} .p${parseInt(p)}.container .twitter`),
              player.twitter
                ? `<span class="twitter_logo"></span>${String(player.twitter)}`
                : "",
              undefined,
              0
            );

            SetInnerHtml(
              $(
                `.slot${parseInt(t)} .p${parseInt(
                  p
                )}.container .sponsor-container`
              ),
              `<div class='sponsor-logo' style='background-image: url(../../${player.sponsor_logo})'></div>`,
              undefined,
              0
            );
          }
        }
      }
    }
  };
});
