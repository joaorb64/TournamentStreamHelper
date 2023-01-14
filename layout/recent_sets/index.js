(($) => {
  let startingAnimation = gsap
    .timeline({ paused: true })
    .from($(".recent_sets"), { autoAlpha: 0 });

  var playersRecentSets = null;

  async function Start() {
    startingAnimation.restart();
  }

  var data = {};
  var oldData = {};

  async function Update() {
    oldData = data;
    data = await getData();

    if (
      !oldData.score ||
      JSON.stringify(oldData.score.recent_sets) !=
        JSON.stringify(data.score.recent_sets)
    ) {
      playersRecentSets = data.score.recent_sets;
      console.log(playersRecentSets);
    }

    recentSetsHtml = "";

    if (
      playersRecentSets == null ||
      (playersRecentSets.state == "done" && playersRecentSets.sets.length == 0)
    ) {
      recentSetsHtml = `No sets found`;
    } else if (playersRecentSets.state != "done") {
      recentSetsHtml += `<div class="lds-ring"><div></div><div></div><div></div><div></div></div>`;
    } else {
      playersRecentSets.sets.slice(0, 5).forEach((_set) => {
        recentSetsHtml += `
            <div class="set_container">
              <div class="${_set.winner == 0 ? "set_winner" : "set_loser"}">
                ${_set.score[0]}
              </div>
              <div class="set_info">
                <div class="set_title">
                  ${_set.online ? `<div class="wifi_icon"></div>` : ""}
                  ${_set.tournament}
                </div>
                <div class="set_date">
                  ${new Date(_set.timestamp * 1000).toLocaleDateString(
                    "en-US",
                    {
                      month: "short",
                      day: "2-digit",
                      year: "numeric",
                    }
                  )}
                </div>
              </div>
              <div class="${_set.winner == 1 ? "set_winner" : "set_loser"}">
                ${_set.score[1]}
              </div>
            </div>
          `;
      });
    }

    SetInnerHtml($(`.recent_sets_content`), recentSetsHtml);
  }

  // Using update here to set images as soon as possible
  // so that on window.load they are already preloaded
  Update();
  $(window).on("load", () => {
    $("body").fadeTo(0, 1, async () => {
      Start();
      setInterval(Update, 500);
    });
  });
})(jQuery);
