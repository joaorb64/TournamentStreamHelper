import {Button, Dialog, DialogContent, DialogTitle, GridLegacy as Grid, Typography} from "@mui/material";
import i18n from "../i18n/config";
import {Box} from "@mui/system";
import {darkTheme} from "../themes";
import {ReportRpsWin} from "./postActions";

export function RpsDialog({playerNames}) {
  return <Dialog
    open={true}
    onClose={() => {}}
    aria-labelledby="modal-modal-title"
    aria-describedby="modal-modal-description"
  >
    <DialogTitle id="responsive-dialog-title">
      {i18n.t("title")}
    </DialogTitle>
    <DialogContent>
      <Box
        component="div"
        gap={2}
        display="flex"
        flexDirection={"column"}
      >
        <Typography>{i18n.t("initial_explanation")}</Typography>

        <Typography
          sx={{ typography: { xs: "h6", sm: "h5" } }}
          align="center"
        >
          {i18n.t("rock_paper_scissors")}
        </Typography>
        <Grid
          container
          item
          xs={12}
          spacing={2}
          justifyContent="center"
        >
          <Grid item xs>
            <Button
              size={
                darkTheme.breakpoints.up("md") ? "large" : "small"
              }
              fontSize={darkTheme.breakpoints.up("md") ? 8 : ""}
              fullWidth
              color="p1color"
              variant="contained"
              onClick={() => ReportRpsWin(0)}
            >
              {i18n.t("player_won", {
                player: playerNames[0],
              })}
            </Button>
          </Grid>
          <Grid item xs>
            <Button
              size={
                darkTheme.breakpoints.up("md") ? "large" : "small"
              }
              fontSize={darkTheme.breakpoints.up("md") ? 8 : ""}
              fullWidth
              color="p2color"
              variant="contained"
              onClick={() => ReportRpsWin(1)}
            >
              {i18n.t("player_won", {
                player: playerNames[1],
              })}
            </Button>
          </Grid>
        </Grid>
        <Typography
          sx={{ typography: { xs: "h6", sm: "h5" } }}
          align="center"
        >
          {i18n.t("randomize")}
        </Typography>
        <Button
          size={darkTheme.breakpoints.up("md") ? "large" : "small"}
          fontSize={darkTheme.breakpoints.up("md") ? 8 : ""}
          fullWidth
          color="success"
          variant="outlined"
          onClick={() => ReportRpsWin(Math.random() > 0.5 ? 1 : 0)}
        >
          {i18n.t("randomize")}
        </Button>
      </Box>
    </DialogContent>
  </Dialog>
}
