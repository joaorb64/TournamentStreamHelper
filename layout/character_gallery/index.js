LoadEverything().then(() => {
  Start = async () => {
    $(".tsh_character > div").each((i, e) => $(e).css("opacity", "0"));
  };

  Update = async (event) => {
    let data = event.data;
    let oldData = event.oldData;

    let scoreboardNumber = 1;

    let src = "";

    if (window.team != undefined && window.player != undefined) {
      src = `score.${scoreboardNumber}.team.${window.team}.player.${window.player}`;
    } else {
      src = `score.${scoreboardNumber}.team.${window.team}`;
    }

    await CharacterDisplay(
      $(`.container`),
      {
        source: src,
      },
      event
    );

    imgs = $.makeArray($(".tsh_character > div"));

    if (imgs.length < 2) {
      gsap.to($(".index_display"), { autoAlpha: 0 });
    } else {
      gsap.to($(".index_display"), { autoAlpha: 1 });
    }
  };

  let cycleIndex = 0;
  let imgs = [];

  function crossfade() {
    if (imgs.length > 1) {
      gsap.to(imgs[(cycleIndex + imgs.length - 1) % imgs.length], 1, {
        autoAlpha: 0,
      });
      gsap.to(imgs[cycleIndex], 1, { autoAlpha: 1 });
      $(".index_display").html(`${cycleIndex + 1}/${imgs.length}`);
      cycleIndex = (cycleIndex + 1) % imgs.length;
    } else if (imgs.length == 1) {
      gsap.to(imgs[0], 1, { autoAlpha: 1 });
      $(".index_display").html(`1/1`);
      cycleIndex = 0;
    }
  }

  var cycle = setInterval(crossfade, 3000);
});
