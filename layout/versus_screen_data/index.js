(($) => {
  // Change this to the name of the assets pack you want to use
  // It's basically the folder name: assets/games/game/ASSETPACK
  var ASSET_TO_USE = "full";

  // Change this to select wether to flip P2 character asset or not
  // Set it to true or false
  var FLIP_P2_ASSET = true;

  let startingAnimation = gsap
    .timeline({ paused: true })
    .from([".phase"], { duration: 0.8, opacity: "0", ease: "power2.inOut" }, 0)
    .from([".match"], { duration: 0.8, opacity: "0", ease: "power2.inOut" }, 0)
    .from(
      [".score_container"],
      { duration: 0.8, opacity: "0", ease: "power2.inOut" },
      0
    )
    .from(
      [".best_of"],
      { duration: 0.8, opacity: "0", ease: "power2.inOut" },
      0
    )
    .from([".vs"], { duration: 0.4, opacity: "0", scale: 4, ease: "out" }, 0.5)
    .from([".p1.container"], { duration: 1, x: "-100px", ease: "out" }, 0)
    .from([".p2.container"], { duration: 1, x: "100px", ease: "out" }, 0);

  var playersRecentSets = [];

  async function GetPlayersRecentSets() {
    let playerFetches = [];

    playerFetches.push(
      fetch("https://corsanywhere.herokuapp.com/https://smash.gg/api/-/gql", {
        method: "POST",
        headers: {
          "client-version": "19",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          operationName: "UserSetQuery",
          variables: {
            userId: data.score.team["1"].players["1"].id,
          },
          query: `
            query UserSetQuery($userId: ID!) {
                user(id: $userId) {
                    player {
                        id
                    }
                }
            }
          `,
        }),
      })
        .then((resp) => resp.json())
        .then(function (data) {
          return data.data.user.player.id;
        })
        .catch(function (error) {
          console.log(error);
        })
    );

    playerFetches.push(
      fetch("https://corsanywhere.herokuapp.com/https://smash.gg/api/-/gql", {
        method: "POST",
        headers: {
          "client-version": "19",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          operationName: "UserSetQuery",
          variables: {
            userId: data.score.team["2"].players["1"].id,
          },
          query: `
            query UserSetQuery($userId: ID!) {
                user(id: $userId) {
                    player {
                        id
                    }
                }
            }
          `,
        }),
      })
        .then((resp) => resp.json())
        .then(function (data) {
          return data.data.user.player.id;
        })
        .catch(function (error) {
          console.log(error);
        })
    );

    Promise.all(playerFetches).then((ids) => {
      console.log("Players: ", ids);

      let setsFetches = [];

      for (let i = 0; i < 30; i += 1) {
        setsFetches.push(
          fetch(
            "https://corsanywhere.herokuapp.com/https://smash.gg/api/-/gql",
            {
              method: "POST",
              headers: {
                "client-version": "19",
                "Content-Type": "application/json",
              },
              body: JSON.stringify({
                operationName: "UserSetQuery",
                variables: {
                  userId: data.score.team["1"].players["1"].id,
                },
                query: `
            query UserSetQuery($userId: ID!) {
                user(id: $userId) {
                    events(query: {page: ${
                      i + 1
                    }, perPage: 10, filter: {videogameId: [${
                  data.game.smashgg_id
                }]}}) {
                      nodes {
                        isOnline
                        name
                        tournament {
                          name
                        }
                        startAt
                        sets(page: 1, perPage: 100, filters: {playerIds: [${
                          ids[1]
                        }], hideEmpty: true, showByes: false}) {
                          nodes {
                              id
                              slots {
                                  entrant {
                                      id
                                      participants {
                                          id
                                          player {
                                              id
                                          }
                                      }
                                  }
                              }
                              entrant1Score
                              entrant2Score
                              displayScore
                              winnerId
                          }
                        }
                      }
                    }
                }
            }
          `,
              }),
            }
          )
            .then((resp) => resp.json())
            .then(function (sggdata) {
              return sggdata;
            })
            .catch(function (error) {
              console.log(error);
            })
        );
      }

      Promise.all(setsFetches).then((results) => {
        let recentSets = [];

        results.forEach((sggdata) => {
          let events = sggdata.data.user.events.nodes;

          events.forEach((event) => {
            if (!event) return;
            if (!event.sets) return;

            let sets = event.sets.nodes;

            sets.forEach((_set) => {
              let p1Id = _set.slots[0].entrant.participants[0].player.id;
              let p2Id = _set.slots[1].entrant.participants[0].player.id;

              if (!ids.includes(p1Id)) return;
              if (!ids.includes(p2Id)) return;

              if (_set.entrant1Score == -1 || _set.entrant2Score == -1) return;

              let playerToEntrant = {};
              playerToEntrant[p1Id] = _set.slots[0].entrant.id;
              playerToEntrant[p2Id] = _set.slots[1].entrant.id;

              let winner = 0;
              if (p1Id == ids[0]) {
                winner = _set.winnerId == playerToEntrant[p1Id] ? 0 : 1;
              } else {
                winner = _set.winnerId == playerToEntrant[p1Id] ? 1 : 0;
              }

              let score = [0, 0];

              if (_set.entrant1Score != null && _set.entrant2Score != null) {
                if (p1Id == ids[0]) {
                  score = [_set.entrant1Score, _set.entrant2Score];
                } else {
                  score = [_set.entrant2Score, _set.entrant1Score];
                }
              } else {
                if (p1Id == ids[0]) {
                  score = ["W", "L"];
                } else {
                  score = ["L", "W"];
                }
              }

              let entry = {
                tournament: event.tournament.name,
                event: event.name,
                online: event.isOnline,
                score: score,
                date: new Date(event.startAt * 1000).toLocaleDateString(
                  "en-US",
                  {
                    month: "2-digit",
                    day: "2-digit",
                    year: "numeric",
                  }
                ),
                winner: winner,
              };

              console.log(entry);
              recentSets.push(entry);
            });
          });
        });

        playersRecentSets = recentSets;
      });
    });
  }

  async function Start() {
    startingAnimation.restart();
  }

  var data = {};
  var oldData = {};

  async function Update() {
    oldData = data;
    data = await getData();

    Object.values(data.score.team).forEach((team, t) => {
      Object.values(team.players).forEach((player, p) => {
        SetInnerHtml(
          $(`.p${t + 1} .name`),
          `
            <span>
                <span class='sponsor'>
                    ${player.team ? player.team + "&nbsp;" : ""}
                </span>
                ${player.name}
                ${team.losers ? " [L]" : ""}
            </span>
          `
        );

        SetInnerHtml(
          $(`.p${t + 1} > .sponsor_logo`),
          player.sponsor_logo
            ? `
              <div class='sponsor_logo' style='background-image: url(../../${player.sponsor_logo})'></div>
              `
            : ""
        );

        SetInnerHtml($(`.p${t + 1} .real_name`), `${player.real_name}`);

        SetInnerHtml(
          $(`.p${t + 1} .twitter`),
          `
            ${
              player.twitter
                ? `
                <div class="twitter_logo"></div>
                ${player.twitter}
                `
                : ""
            }
        `
        );

        SetInnerHtml(
          $(`.p${t + 1} .flagcountry`),
          player.country.asset
            ? `
            <div>
                <div class='flag' style='background-image: url(../../${player.country.asset});'>
                    <div class="flagname">${player.country.code}</div>
                </div>
            </div>`
            : ""
        );

        SetInnerHtml(
          $(`.p${t + 1} .flagstate`),
          player.state.asset
            ? `
            <div>
                <div class='flag' style='background-image: url(../../${player.state.asset});'>
                    <div class="flagname">${player.state.code}</div>
                </div>
            </div>`
            : ""
        );

        if (
          !oldData.score ||
          JSON.stringify(player.character) !=
            JSON.stringify(
              oldData.score.team[String(t + 1)].players[String(p + 1)].character
            )
        ) {
          let html = "";
          let characters = Object.values(player.character);
          if (t == 0) characters = characters.reverse();
          let zIndexMultiplyier = 1;
          if (t == 1) zIndexMultiplyier = -1;
          characters.forEach((character, c) => {
            if (
              character &&
              character.assets &&
              character.assets[ASSET_TO_USE]
            ) {
              if (!character.assets[ASSET_TO_USE].asset.endsWith(".webm")) {
                // if asset is a image, add a image element
                html += `
                <div class="bg char${
                  t == 1 ? c : characters.length - 1 - c
                }" style="z-index: ${c * zIndexMultiplyier};">
                  <div class="portrait_container">
                    <div
                      class="portrait ${
                        !FLIP_P2_ASSET && t == 1 ? "invert_shadow" : ""
                      }"
                      style='
                          background-image: url(../../${
                            character.assets[ASSET_TO_USE].asset
                          });
                          ${
                            t == 1 && FLIP_P2_ASSET
                              ? "transform: scaleX(-1)"
                              : ""
                          }
                      '>
                      </div>
                    </div>
                </div>
                  `;
              } else {
                // if asset is a video, add a video element
                html += `
                <div class="bg char${
                  t == 1 ? c : characters.length - 1 - c
                }" style="z-index: ${c * zIndexMultiplyier};">
                  <video id="video_${p}" class="video" width="auto" height="100%" autoplay muted>
                    <source src="../../${character.assets[ASSET_TO_USE].asset}">
                  </video>
                </div>
                  `;
              }
            }
          });

          $(`.p${t + 1}.character`).html(html);

          characters.forEach((character, c) => {
            if (character) {
              gsap.timeline().fromTo(
                [`.p${t + 1}.character .char${c}`],
                {
                  duration: 0.8,
                  x: zIndexMultiplyier * -800 + "px",
                  z: 0,
                  rotationY: zIndexMultiplyier * -270,
                  ease: "out",
                },
                {
                  duration: 0.8,
                  x: 0,
                  z: -c * 50 + "px",
                  rotationY: zIndexMultiplyier * 15 * (c + 1),
                  ease: "out",
                },
                c / 6
              );

              gsap
                .timeline()
                .from(
                  `.p${t + 1}.character .char${c} .portrait_container`,
                  {
                    duration: 0.5,
                    opacity: 0,
                  },
                  c / 6
                )
                .from(`.p${t + 1}.character .char${c} .portrait_container`, {
                  duration: 0.4,
                  filter: "brightness(0%)",
                  onUpdate: function (tl) {
                    var tlp = (this.progress() * 100) >> 0;
                    TweenMax.set(
                      `.p${t + 1}.character .char${c} .portrait_container`,
                      {
                        filter: "brightness(" + tlp + "%)",
                      }
                    );
                  },
                  onUpdateParams: ["{self}"],
                });
            }
          });
        }
      });
    });

    SetInnerHtml($(`.p1 .score`), String(data.score.team["1"].score));
    SetInnerHtml($(`.p2 .score`), String(data.score.team["2"].score));

    SetInnerHtml($(".phase"), data.score.phase);
    SetInnerHtml($(".match"), data.score.match);
    SetInnerHtml(
      $(".best_of"),
      data.score.best_of ? "Best of " + data.score.best_of : ""
    );

    if (
      !oldData.score ||
      data.score.team["1"].players["1"].id !=
        oldData.score.team["1"].players["1"].id ||
      data.score.team["2"].players["1"].id !=
        oldData.score.team["2"].players["1"].id
    ) {
      playersRecentSets = [];
      GetPlayersRecentSets();
    }

    recentSetsHtml = "";

    if (playersRecentSets && playersRecentSets.length > 0) {
      recentSetsHtml += `<div class="recent_sets_title">Recent Sets</div>`;
      playersRecentSets.slice(0, 3).forEach((_set) => {
        recentSetsHtml += `
          <div class="set_container">
            <div class="${_set.winner == 0 ? "set_winner" : "set_loser"}">${
          _set.score[0]
        }</div>
            <div class="set_info">
              <div class="set_title">${_set.tournament}</div>
              <div>${_set.date}</div>
            </div>
            <div class="${_set.winner == 1 ? "set_winner" : "set_loser"}">${
          _set.score[1]
        }</div>
          </div>
        `;
      });
    }

    SetInnerHtml($(`.recent_sets`), recentSetsHtml);
  }

  // Using update here to set images as soon as possible
  // so that on window.load they are already preloaded
  Update();
  $(window).on("load", () => {
    $("body").fadeTo(0, 1, async () => {
      Start();
      setInterval(Update, 1000);
    });
  });
})(jQuery);
