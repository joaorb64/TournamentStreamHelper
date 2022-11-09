(($) => {
  var ASSET_TO_USE = "full"
  var ZOOM = 1
  
  gsap.config({ nullTargetWarn: false, trialWarn: false });

  let startingAnimation = gsap
    .timeline({ paused: true })
    .from([".container"], { duration: 1, width: "0", ease: "power2.inOut" }, 0);

  function Start() {
    startingAnimation.restart();
  }

  var data = {};
  var oldData = {};

  async function Update() {
    oldData = data;
    data = await getData();

    if (
      !oldData.player_list ||
      JSON.stringify(data.player_list) != JSON.stringify(oldData.player_list)
    ) {
      let html = "";

      Object.values(data.player_list.slot).forEach((slot, i) => {
        html += `<div class="slot slot${i + 1}">`;
        html += `<div class="container title"></div>`;
        Object.values(slot.player).forEach((player, p) => {
          html += `
            <div class="p${p + 1} player container">
              <div class="icon avatar"></div>
              <div class="icon online_avatar"></div>
              <div class="flagcountry"></div>
              <div class="flagstate"></div>
              <div class="sponsor_icon"></div>
              <div class="name_twitter">
                <div class="name"></div>
                <div class="twitter"></div>
                </div>
              <div class="filler"></div>
              <div class="character_container"></div>
            </div>
          `;
        });
        html += "</div>";
      });

      $(".players_container").html(html);

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

            let charactersHtml = "";

            Object.values(player.character).forEach((character, index) => {
              if (character.assets[ASSET_TO_USE]) {
                charactersHtml += `
                  <div class="icon stockicon">
                      <div style='background-image: url(../../${character.assets[ASSET_TO_USE]})'></div>
                  </div>
                  `;
              }
            });
            SetInnerHtml(
              $(`.slot${t + 1} .p${p + 1}.container .character_container`),
              charactersHtml,
              undefined,
              0,
              () => {
                $(
                  `.slot${t + 1} .p${
                    p + 1
                  }.container .character_container .icon.stockicon div`
                ).each((e, i) => {
                  if (player.character[e + 1].assets[ASSET_TO_USE] != null) {
                    CenterImage(
                      $(i),
                      player.character[e + 1].assets[ASSET_TO_USE],
                      ZOOM
                    );
                  }
                });
              }
            );

            SetInnerHtml(
              $(`.slot${t + 1} .p${p + 1}.container .sponsor_icon`),
              player.sponsor_logo
                ? `<div style='background-image: url(../../${player.sponsor_logo})'></div>`
                : "",
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
                : "",
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
      });
    }

    $(".text").each(function (e) {
      FitText($($(this)[0].parentNode));
    });

    $(".container div:has(>.text:empty)").css("margin-right", "0");
    $(".container div:not(:has(>.text:empty))").css("margin-right", "");
    $(".container div:has(>.text:empty)").css("margin-left", "0");
    $(".container div:not(:has(>.text:empty))").css("margin-left", "");
  }

  Update();
  $(window).on("load", () => {
    $("body").fadeTo(1, 1, async () => {
      Start();
      setInterval(Update, 16);
    });
  });
})(jQuery);
