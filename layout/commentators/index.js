(($) => {
  if (!window.config) {
    window.config = {
      size: "normal",
    };
  }

  function Start() {}

  var data = {};
  var oldData = {};

  let oldCharacters = {};

  async function Update() {
    oldData = data;
    data = await getData();

    if (
      Object.keys(oldData).length == 0 ||
      Object.keys(oldData.commentary).length !=
        Object.keys(data.commentary).length
    ) {
      let html = "";
      Object.values(data.commentary).forEach((commentator, index) => {
        html += `
              <div class="commentator_container commentator${index}">
                  <div class="name"></div>
                  <div class="pronoun"></div>
                  ${
                    window.config.size == "normal"
                      ? `<div class="real_name"></div>`
                      : ""
                  }
                  ${
                    window.config.size == "normal" ||
                    window.config.size == "mini"
                      ? `<div class="twitter"></div>`
                      : ""
                  }
              </div>
          `;
      });
      $(".container").html(html);
    }

    Object.values(data.commentary).forEach((commentator, index) => {
      if (commentator.name) {
        $(`.commentator${index}`).css("display", "");
        SetInnerHtml(
          $(`.commentator${index} .name`),
          `
            <span class="mic_icon"></span>
            <span class="team">
              ${commentator.team ? commentator.team + "&nbsp;" : ""}
            </span>
            ${commentator.name}
          `
        );
        SetInnerHtml(
          $(`.commentator${index} .pronoun`),
          commentator.pronoun
        );
        SetInnerHtml(
          $(`.commentator${index} .real_name`),
          commentator.real_name
        );
        SetInnerHtml(
          $(`.commentator${index} .twitter`),
          commentator.twitter ? "@" + commentator.twitter : ""
        );
      } else {
        $(`.commentator${index}`).css("display", "none");
      }
    });
  }

  Update();
  $(window).on("load", () => {
    $("body").fadeTo(800, 1, async () => {
      Start();
      setInterval(Update, 1000);
    });
  });
})(jQuery);
