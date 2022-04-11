(($) => {
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
        html += `<div class="title"></div>`;
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
              <div class="character_container"></div>
            </div>
          `;
        });
        html += "</div>";
      });

      $(".players_container").html(html);
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
            `
          );

          SetInnerHtml(
            $(`.slot${t + 1} .p${p + 1}.container .flagcountry`),
            player.country.asset
              ? `<div class='flag' style='background-image: url(../../${player.country.asset.toLowerCase()})'></div>`
              : ""
          );

          SetInnerHtml(
            $(`.slot${t + 1} .p${p + 1}.container .flagstate`),
            player.state.asset
              ? `<div class='flag' style='background-image: url(../../${player.state.asset})'></div>`
              : ""
          );

          let charactersHtml = "";

          if (
            !oldData.player_list ||
            JSON.stringify(player.character) !=
              JSON.stringify(
                oldData.player_list.slot[t + 1].player[p + 1].character
              )
          ) {
            Object.values(player.character).forEach((character, index) => {
              if (character.assets["portrait"]) {
                charactersHtml += `
                  <div class="icon stockicon">
                      <div style='background-image: url(../../${character.assets["portrait"].asset})'></div>
                  </div>
                  `;
              }
            });
            SetInnerHtml(
              $(`.slot${t + 1} .p${p + 1}.container .character_container`),
              charactersHtml,
              undefined,
              0.5,
              () => {
                $(
                  `.slot${t + 1} .p${
                    p + 1
                  }.container .character_container .icon.stockicon div`
                ).each((e, i) => {
                  if (player.character[e + 1].assets["portrait"] != null) {
                    CenterImage(
                      $(i),
                      player.character[e + 1].assets["portrait"].eyesight
                    );
                  }
                });
              }
            );
          }

          SetInnerHtml(
            $(`.slot${t + 1} .p${p + 1}.container .sponsor_icon`),
            player.sponsor_logo
              ? `<div style='background-image: url(../../${player.sponsor_logo})'></div>`
              : ""
          );

          SetInnerHtml(
            $(`.slot${t + 1} .p${p + 1}.container .avatar`),
            player.avatar
              ? `<div style="background-image: url('../../${player.avatar}')"></div>`
              : ""
          );

          SetInnerHtml(
            $(`.slot${t + 1} .p${p + 1}.container .online_avatar`),
            player.online_avatar
              ? `<div style="background-image: url('${player.online_avatar}')"></div>`
              : ""
          );

          SetInnerHtml(
            $(`.slot${t + 1} .p${p + 1}.container .twitter`),
            player.twitter
              ? `<span class="twitter_logo"></span>${String(player.twitter)}`
              : ""
          );

          SetInnerHtml(
            $(`.slot${t + 1} .p${p + 1}.container .sponsor-container`),
            `<div class='sponsor-logo' style='background-image: url(../../${player.sponsor_logo})'></div>`
          );
        }
      });
    });

    SetInnerHtml($(".info.container.top"), data.tournamentInfo.tournamentName);

    SetInnerHtml(
      $(".info.container.bottom"),
      `
        <div class="info container_inner">
            ${data.score.phase ? `<div>${data.score.phase}</div>` : ""}
            ${data.score.match ? `<div>${data.score.match}</div>` : ""}
            ${
              data.score.best_of
                ? `<div>Best of ${data.score.best_of}</div>`
                : ""
            }
        </div>
      `
    );

    $(".text").each(function (e) {
      FitText($($(this)[0].parentNode));
    });

    $(".container div:has(>.text:empty)").css("margin-right", "0");
    $(".container div:not(:has(>.text:empty))").css("margin-right", "");
    $(".container div:has(>.text:empty)").css("margin-left", "0");
    $(".container div:not(:has(>.text:empty))").css("margin-left", "");
  }

  $(window).on("load", () => {
    $("body").fadeTo(1, 1, async () => {
      Start();
      setInterval(Update, 2);
    });
  });
})(jQuery);
