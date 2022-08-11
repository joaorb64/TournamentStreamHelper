(($) => {
  gsap.config({ nullTargetWarn: false, trialWarn: false });

  let startingAnimation = gsap
    .timeline({ paused: true })
    .from([".logo"], { duration: 0.5, autoAlpha: 0, ease: "power2.inOut" }, 0.5)
    .from(
      [".anim_container_outer"],
      {
        duration: 1,
        width: "0",
        ease: "power2.inOut",
      },
      1
    )
    .from(
      [".p1.twitter"],
      {
        duration: 0.75,
        x: "-373px",
        opacity: 0,
        ease: "power2.inOut",
      },
      "<"
    )
    .from(
      [".p2.twitter"],
      {
        duration: 0.75,
        x: "373px",
        opacity: 0,
        ease: "power2.inOut",
      },
      "<"
    );

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
              <span class="sponsor">${
                player.team.toUpperCase() ? player.team.toUpperCase() : ""
              }</span>${player.name.toUpperCase()}`
          );

          SetInnerHtml(
            $(`.p${t + 1} .losers_container`),
            `${team.losers ? "<span class='losers'>L</span>" : ""}`
          );

          SetInnerHtml(
            $(`.p${t + 1}.container .flagcountry`),
            player.country.asset
              ? `<div class='flag' style='background-image: url(../../${player.country.asset.toLowerCase()})'></div>`
              : ""
          );

          SetInnerHtml(
            $(`.p${t + 1}.twitter`),
            player.twitter
              ? `<span class="twitter_logo"></span>${
                  "@" + String(player.twitter).toUpperCase()
                }`
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

    SetInnerHtml($(".match"), data.score.match.toUpperCase());

    let phaseTexts = [];
    if (data.score.phase) phaseTexts.push(data.score.phase.toUpperCase());
    if (data.score.best_of) phaseTexts.push(`BEST OF ${data.score.best_of}`);

    SetInnerHtml($(".phase"), phaseTexts.join(" - "));

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
      setInterval(Update, 500);
    });
  });
})(jQuery);
