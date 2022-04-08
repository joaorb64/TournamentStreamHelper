(($) => {
  let startingAnimation = gsap
    .timeline({ paused: true })
    .from(
      [".left .container:not(.cameras)"],
      { duration: 1, x: "-100%", ease: "power2.inOut" },
      0
    )
    .from(
      [".right .container:not(.cameras)"],
      { duration: 1, x: "+100%", ease: "power2.inOut" },
      0
    )
    .from([".score"], { duration: 1, autoAlpha: "0", ease: "power2.inOut" }, 0)
    .from(
      [".left .character_container:not(.cameras)"],
      { duration: 1, x: "+50%", ease: "power2.inOut" },
      0
    )
    .from(
      [".right .character_container:not(.cameras)"],
      { duration: 1, x: "-50%", ease: "power2.inOut" },
      0
    )
    .from(
      [".container.top"],
      { duration: 1, y: "-100%", ease: "power2.inOut" },
      0
    )
    .from(
      [".container.bottom"],
      { duration: 1, y: "+100%", ease: "power2.inOut" },
      0
    );

  function Start() {
    startingAnimation.restart();
  }

  var data = {};
  var oldData = {};

  async function Update() {
    oldData = data;
    data = await getData();

    Object.values(data.score.team).forEach((team, t) => {
      console.log(team);

      let team_id = ["left", "right"][t];

      SetInnerHtml($(`.${team_id} .score`), String(team.score));

      let team_size = Object.values(team.player).length;

      let firstRun = Object.keys(oldData).length == 0;
      let time = firstRun ? 0 : 1;

      if (team_size == 1) {
        gsap.timeline().to($(`.${team_id} .p${2}.container`), {
          height: 0,
          duration: time,
        });
      } else {
        gsap.timeline().to($(`.${team_id} .p${2}.container`), {
          height: "420px",
          duration: time,
        });
      }

      Object.values(team.player).forEach((player, p) => {
        if (player) {
          SetInnerHtml(
            $(`.${team_id} .p${p + 1} .name`),
            `
              <span class="sponsor">${
                player.team ? player.team + "&nbsp;" : ""
              }</span>${String(player.name)}
            `
          );

          SetInnerHtml(
            $(`.${team_id} .p${p + 1} .flagcountry`),
            player.country.asset
              ? `
              <div class='flag' style='background-image: url(../../${String(
                player.country.asset
              ).toLowerCase()})'></div>
            `
              : ""
          );

          SetInnerHtml(
            $(`.${team_id} .p${p + 1} .flagstate`),
            player.state.asset
              ? `
              <div class='flag' style='background-image: url(../../${player.state.asset})'></div>
            `
              : ""
          );

          let charactersHtml = "";

          if (
            $(".cameras").length == 0 &&
            (!oldData.score ||
              JSON.stringify(
                oldData.score.team[`${t + 1}`].player[`${p + 1}`].character
              ) != JSON.stringify(player.character))
          ) {
            Object.values(player.character).forEach((character) => {
              if (character.assets["full"]) {
                charactersHtml += `
                <div class='character' style='background-image: url(../../${character.assets["full"].asset})'></div>
              `;
              }
            });

            SetInnerHtml(
              $(`.${team_id} .p${p + 1} .character_container`),
              charactersHtml,
              undefined,
              0.5,
              () => {
                $(
                  `.${team_id} .p${p + 1} .character_container .character`
                ).each((i, e) => {
                  CenterImage(
                    $(e),
                    Object.values(player.character)[i].assets["full"].eyesight
                  );
                });
              }
            );
          }

          SetInnerHtml(
            $(`.${team_id} .p${p + 1} .twitter`),
            player.twitter
              ? `<span class="twitter_logo"></span>${String(player.twitter)}`
              : ""
          );

          SetInnerHtml(
            $(`.${team_id} .p${p + 1} .sponsor_logo`),
            `<div class='sponsor_logo' style='background-image: url(../../${String(
              player.sponsor_logo
            )})'></div>`
          );
        }
      });
    });

    SetInnerHtml($(".info.container.top"), data.tournamentInfo.tournamentName);

    SetInnerHtml($(".match"), data.score.match);

    let phaseTexts = [];
    if (data.score.phase) phaseTexts.push(data.score.phase);
    if (data.score.best_of) phaseTexts.push(`Best of ${data.score.best_of}`);

    SetInnerHtml($(".phase"), phaseTexts.join(" - "));

    $(".text").each(function (e) {
      FitText($($(this)[0].parentNode));
    });
  }

  Update();
  $(window).on("load", () => {
    $("body").fadeTo(500, 1, async () => {
      Start();
      setInterval(Update, 500);
    });
  });
})(jQuery);
