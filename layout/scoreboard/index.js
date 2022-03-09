(($) => {
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

    [data.score.team["1"], data.score.team["2"]].forEach((team, t) => {
      [team.player["1"]].forEach((player, p) => {
        if (player) {
          SetInnerHtml(
            $(`.p${t + 1}.container .name`),
            `
            <span>
              <span class="sponsor">
                ${player.team ? player.team : ""}
              </span>
              ${player.name}
              ${team.losers ? " [L]" : ""}
            </span>
            `
          );

          SetInnerHtml(
            $(`.p${t + 1}.container .flagcountry`),
            player.country.asset
              ? `<div class='flag' style='background-image: url(../../${player.country.asset.toLowerCase()})'></div>`
              : ""
          );

          SetInnerHtml(
            $(`.p${t + 1}.container .flagstate`),
            player.state.asset
              ? `<div class='flag' style='background-image: url(../../${player.state.asset})'></div>`
              : ""
          );

          let charactersHtml = "";
          Object.values(player.character).forEach((character, index) => {
            if (character.assets["base_files/icon"]) {
              charactersHtml += `
                <div class="icon stockicon">
                    <div style='background-image: url(../../${character.assets["base_files/icon"].asset})'></div>
                </div>
                `;
            }
          });
          SetInnerHtml(
            $(`.p${t + 1}.container .character_container`),
            charactersHtml
          );

          SetInnerHtml(
            $(`.p${t + 1}.container .sponsor`),
            player.sponsor_logo
              ? `<div style='background-image: url(../../${player.sponsor_logo})'></div>`
              : ""
          );

          SetInnerHtml(
            $(`.p${t + 1}.container .avatar`),
            player.avatar
              ? `<div style="background-image: url('../../${player.avatar}')"></div>`
              : ""
          );

          SetInnerHtml(
            $(`.p${t + 1}.container .online_avatar`),
            player.online_avatar
              ? `<div style="background-image: url('${player.online_avatar}')"></div>`
              : ""
          );

          SetInnerHtml(
            $(`.p${t + 1}.container .twitter`),
            player.twitter
              ? `<span class="twitter_logo"></span>${String(player.twitter)}`
              : ""
          );

          let score = [data.score.score_left, data.score.score_right];

          SetInnerHtml($(`.p${t + 1}.container .score`), String(team.score));

          SetInnerHtml(
            $(`.p${t + 1}.container .sponsor-container`),
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

    $(".icon:has(>.text:empty)").css("margin-right", "0");
    $(".icon:has(>.text:empty)").css("margin-left", "0");
  }

  $(window).on("load", () => {
    $("body").fadeTo(1, 1, async () => {
      Start();
      setInterval(Update, 2);
    });
  });
})(jQuery);
