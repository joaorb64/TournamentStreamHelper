import {darkTheme} from "../themes";
import i18n from "i18next";
import {RestartStageStrike, SetGentlemans, Undo, Redo} from "./postActions";
import {GridLegacy as Grid, Button} from "@mui/material";
import {Handshake, RestartAlt, Undo as UndoIcon, Redo as RedoIcon} from "@mui/icons-material";

export function FooterControls({
  isGentlemans,
  canUndo,
  canRedo
}) {
  return <Grid
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
        disabled={!canUndo}
        variant="outlined"
        sx={{
          flexDirection: { xs: "column", lg: "unset" },
          fontSize: { xs: 10, lg: "unset" },
        }}
        onClick={() => {
          Undo();
        }}
        startIcon={<UndoIcon />}
      >
        {i18n.t("undo")}
      </Button>
    </Grid>
    <Grid item xs>
      <Button
        size={
          darkTheme.breakpoints.up("md") ? "large" : "small"
        }
        fontSize={darkTheme.breakpoints.up("md") ? 8 : ""}
        fullWidth
        disabled={!canRedo}
        variant="outlined"
        sx={{
          flexDirection: { xs: "column", lg: "unset" },
          fontSize: { xs: 10, lg: "unset" },
        }}
        onClick={() => {
          Redo();
        }}
        startIcon={<RedoIcon />}
      >
        {i18n.t("redo")}
      </Button>
    </Grid>
    <Grid item xs>
      <Button
        sx={{
          flexDirection: { xs: "column", lg: "unset" },
          fontSize: { xs: 10, lg: "unset" },
        }}
        size={
          darkTheme.breakpoints.up("md") ? "large" : "small"
        }
        fontSize={darkTheme.breakpoints.up("md") ? 8 : ""}
        fullWidth
        variant={
          isGentlemans ? "contained" : "outlined"
        }
        startIcon={<Handshake />}
        onClick={() => {
          SetGentlemans(!isGentlemans);
        }}
      >
        {i18n.t("gentlemans_pick")}
      </Button>
    </Grid>
    <Grid item xs>
      <Button
        size={
          darkTheme.breakpoints.up("md") ? "large" : "small"
        }
        fontSize={darkTheme.breakpoints.up("md") ? 8 : ""}
        fullWidth
        variant="outlined"
        sx={{
          flexDirection: { xs: "column", lg: "unset" },
          fontSize: { xs: 10, lg: "unset" },
        }}
        onClick={() => {
          RestartStageStrike(true);
        }}
        startIcon={<RestartAlt />}
      >
        {i18n.t("restart_all")}
      </Button>
    </Grid>
  </Grid>
}
