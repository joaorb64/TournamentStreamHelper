import {GridLegacy as Grid, Typography} from "@mui/material";
import i18n from "../i18n/config";
import ReactDOMServer from "react-dom/server";

export function StagePromptText({
  selectedStage,
  isGentlemans,
  currGame,
  currStep,
  strikeNumber,
  currentPlayerColor,
  currentPlayerName,
}) {
  let body;

  if (selectedStage) {
    body = i18n.t("report_results");
  } else if (isGentlemans) {
    body = <>
      {
        i18n.t("gentlemans_prompt", {
          gentlemans_pick: i18n.t("gentlemans_pick"),
        })
      }
    </>
  } else if (currGame > 0 && currStep > 0) {
    body = embedHtml(
      i18n.t("select_a_stage_prompt", {
        player: ReactDOMServer.renderToStaticMarkup(
          <span
            style={{
              color: currentPlayerColor?.main
            }}
          >
            { currentPlayerName }
          </span>
        ),
        val: strikeNumber,
        interpolation: { escapeValue: false },
      })
    );
  } else {
    body = embedHtml(
      i18n.t("ban_prompt", {
        player: ReactDOMServer.renderToStaticMarkup(
          <span
            style={{
              color: currentPlayerColor.main,
            }}
          >
            { currentPlayerName }
          </span>
        ),
        val: strikeNumber,
        interpolation: { escapeValue: false },
      })
    );
  }

  return <Grid item xs={12}>
      <Typography
        sx={{ typography: { xs: "h6", sm: "h4" } }}
        component="div"
      >
        { body }
      </Typography>
    </Grid>
}

function embedHtml(data, props) {
  if (!props) {
    props = {}
  }

  return <div
    {...props}
    dangerouslySetInnerHTML={{
      __html: data
    }} />

}
