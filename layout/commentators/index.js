(($) => {
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
        if (commentator.name) {
          html += `
                <div class="commentator_container commentator${index}">
                    <div class="name"></div>
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
        }
      });
      $(".container").html(html);
    }

    Object.values(data.commentary).forEach((commentator, index) => {
      if (commentator.name) {
        SetInnerHtml(
          $(`.commentator${index} .name`),
          `
            <div class="mic_icon"></div>
            <span class="team">
              ${commentator.team ? commentator.team + "&nbsp;" : ""}
            </span>
            ${commentator.name}
          `
        );
        SetInnerHtml(
          $(`.commentator${index} .real_name`),
          commentator.real_name
        );
        SetInnerHtml($(`.commentator${index} .twitter`), commentator.twitter);
      }
    });
  }

  Update();
  $(window).on("load", () => {
    $("body").fadeTo(500, 1, async () => {
      Start();
      setInterval(Update, 1000);
    });
  });
})(jQuery);
