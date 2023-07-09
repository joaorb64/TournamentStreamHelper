LoadEverything().then(() => {
  Start = async () => {};

  Update = async (event) => {
    let data = event.data;
    let oldData = event.oldData;

    let src = "";

    if (window.team != undefined && window.player != undefined) {
      src = `score.team.${window.team}.player.${window.player}`;
    } else {
      src = `score.team.${window.team}`;
    }

    await CharacterDisplay(
      $(`.container`),
      {
        source: src,
      },
      event
    );
  };
});
