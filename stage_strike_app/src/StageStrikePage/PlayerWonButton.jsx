import {Fab} from "@mui/material";
import {darkTheme} from "../themes";
import {MatchWinner} from "./postActions";
import i18n from "../i18n/config";

export function PlayerWonButton({playerName, color, leftSide}) {
  const hPosition = leftSide ? {left: 16} : {right: 16};
  return <Fab
    size={
      darkTheme.breakpoints.up("md") ? "large" : "small"
    }
    fontSize={darkTheme.breakpoints.up("md") ? 8 : ""}
    color={color}
    variant="extended"
    onClick={() => MatchWinner(leftSide ? 0 : 1)}
    style={{
      top: -16,
      ...hPosition,
      transform: "translateY(-100%)",
      position: "absolute",
    }}
    sx={{
      width: {
        xs: "45%",
        md: "33%",
      },
    }}
  >
    {i18n.t("player_won", {
      player: playerName
    })}
  </Fab>
}
