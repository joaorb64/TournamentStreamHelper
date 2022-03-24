(($) => {
  let startingAnimation = gsap
    .timeline({ paused: true })
    .from($(".recent_sets"), { autoAlpha: 0 });

  var playersRecentSets = null;

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
            userId: data.score.team["1"].player["1"].id,
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
            userId: data.score.team["2"].player["1"].id,
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

      if (ids[0] == null || ids[1] == null) {
        playersRecentSets = [];
        return;
      }

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
                  userId: data.score.team["1"].player["1"].id,
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

    if (
      !oldData.score ||
      data.score.team["1"].player["1"].id !=
        oldData.score.team["1"].player["1"].id ||
      data.score.team["2"].player["1"].id !=
        oldData.score.team["2"].player["1"].id
    ) {
      playersRecentSets = null;
      GetPlayersRecentSets();
    }

    recentSetsHtml = "";

    if (playersRecentSets != null) {
      if (playersRecentSets && playersRecentSets.length > 0) {
        playersRecentSets.slice(0, 5).forEach((_set) => {
          recentSetsHtml += `
            <div class="set_container">
              <div class="${_set.winner == 0 ? "set_winner" : "set_loser"}">${
            _set.score[0]
          }</div>
              <div class="set_info">
                <div class="set_title">${
                  _set.online ? `<div class="wifi_icon"></div>` : ""
                }${_set.tournament}</div>
                <div>${_set.date}</div>
              </div>
              <div class="${_set.winner == 1 ? "set_winner" : "set_loser"}">${
            _set.score[1]
          }</div>
            </div>
          `;
        });
      } else {
        recentSetsHtml += `No sets found`;
      }
    } else {
      recentSetsHtml += `<div class="lds-ring"><div></div><div></div><div></div><div></div></div>`;
    }

    SetInnerHtml($(`.recent_sets_content`), recentSetsHtml);
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
