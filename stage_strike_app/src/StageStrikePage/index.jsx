import { Component } from "react";
import "../NoSleep";
import {
  Container,
  GridLegacy as Grid,
  Typography,
  Fab,
} from "@mui/material";
import { Box } from "@mui/system";
import i18n from "../i18n/config";
import { Check } from "@mui/icons-material";
import i18next from "i18next";
import {darkTheme} from "../themes";
import {BASE_URL} from "../env";
import {NoRulesetError} from "./NoRulesetError";
import {StageCard} from "./StageCard";
import {
  ConfirmClicked,
  StageClicked
} from "./postActions";
import {RpsDialog} from "./RpsDialog";
import {FooterControls} from "./FooterControls";
import {PlayerWonButton} from "./PlayerWonButton";
import {StagePromptText} from "./StagePromptText";
import websocketConnection from "../websocketConnection";

class StageStrikePage extends Component {
  state = {
    ruleset: null,
    currGame: 0,
    currPlayer: -1,
    currStep: 0,
    strikedStages: [],
    strikedBy: [[], []],
    stagesWon: [[], []],
    stagesPicked: [],
    selectedStage: null,
    lastWinner: -1,
    playerNames: [],
    phase: null,
    match: null,
    bestOf: null,
    gentlemans: false,
    canUndo: false,
    canRedo: false,
  };

  socket = websocketConnection.instance();

  GetStage(/** string */ stage) {
    let found = this.state.ruleset.neutralStages.find(
      (s) => s.codename === stage
    );
    if (found) return found;
    found = this.state.ruleset.counterpickStages.find(
      (s) => s.codename === stage
    );
    if (found) return found;
    return null;
  }

  IsStageStriked(/** string */ stage, previously = false) {
    for (
      let i = 0;
      i < Object.values(this.state.strikedStages).length;
      i += 1
    ) {
      if (
        i === Object.values(this.state.strikedStages).length - 1 &&
        previously
      ) {
        continue;
      }
      let round = Object.values(this.state.strikedStages)[i];
      let found = round.findIndex((e) => e === stage);
      if (found !== -1) {
        return true;
      }
    }
    return false;
  }

  GetBannedStages() {
    let banList = [];

    if (this.state.ruleset.useDSR) {
      banList = this.state.stagesPicked;
    } else if (this.state.ruleset.useMDSR && this.state.lastWinner !== -1) {
      banList =
        this.state.stagesWon && this.state.stagesWon.length > 0
          ? this.state.stagesWon[(this.state.lastWinner + 1) % 2]
          : [];
    }

    return banList;
  };

  IsStageBanned(/** string */ stage) {
    let banList = this.GetBannedStages();

    let found = banList.findIndex((e) => e === stage);
    if (found !== -1) {
      return true;
    }
    return false;
  }

  CanConfirm() {
    const strikedStages = this.state.strikedStages[this.state.currStep];
    const strikeOrder = this.state.ruleset.strikeOrder[this.state.currStep];
    if (this.state.selectedStage || !strikedStages) {
      return false;
    }

    if (this.state.currGame === 0) {
      return strikedStages.length === strikeOrder;
    } else {
      return strikedStages.length === this.GetStrikeNumber();
    }
  }

  GetStrikeNumber = () => {
    if (this.state.currGame === 0) {
      return this.state.ruleset.strikeOrder[this.state.currStep];
    } else {
      if (this.state.ruleset.banCount !== 0) {
        // Fixed ban count
        return this.state.ruleset.banCount;
      } else if (
        this.state.ruleset.banByMaxGames &&
        Object.keys(this.state.ruleset.banByMaxGames).includes(
          String(this.state.bestOf)
        )
      ) {
        console.log(this.state.bestOf);
        // Ban by max games
        return this.state.ruleset.banByMaxGames[String(this.state.bestOf)];
      } else {
        return 0;
      }
    }
  };

  /** @param {string} stageCodename */
  PlayerWhoStrikedStage = (stageCodename) => {
    return this.state.strikedBy[0].findIndex(
      (s) => s === stageCodename
    ) !== -1
      ? this.state.playerNames[0]
      : this.state.playerNames[1]
  }

  PlayerWinCount = (playerNum) => {
    return this.state?.stagesWon?.[0]?.length ?? 0;
  }

  componentDidMount() {
    this.socket.on("connect", () => {
      console.log("SocketIO connection established.");
      this.socket.emit("ruleset", {}, () => {console.log("TSH acked ruleset request")});
    });

    this.socket.on("ruleset", data => {
      console.log("TSH ruleset data received ", data);
      this.ProcessRulesetData(data);
    });

    this.socket.on("disconnect", () => {
      console.log("SocketIO disconnected.")
      this.socket.connect();
    });

    this.socket.on('error', (err) => {
      console.log(err);
    })
  }

  componentWillUnmount() {
    this.socket.close();
  }

  ProcessRulesetData = (data) => {
    this.setState({
      playerNames: [
        data.p1 ? data.p1 : i18n.t("p1"),
        data.p2 ? data.p2 : i18n.t("p2"),
      ],
      ruleset: data.ruleset,
      phase: data.phase,
      match: data.match,
      bestOf: data.best_of,
    });

    if (data.state && Object.keys(data.state).length > 0) {
      this.setState({
        currGame: data.state.currGame,
        currPlayer: data.state.currPlayer,
        currStep: data.state.currStep,
        strikedStages: data.state.strikedStages,
        strikedBy: data.state.strikedBy,
        stagesWon: data.state.stagesWon,
        stagesPicked: data.state.stagesPicked,
        selectedStage: data.state.selectedStage,
        lastWinner: data.state.lastWinner,
        gentlemans: data.state.gentlemans,
        canUndo: data.state.canUndo,
        canRedo: data.state.canRedo,
      });
    }
  }

  render() {
    if (!this.state.ruleset || this.state.ruleset.neutralStages.length === 0) {
      return <NoRulesetError currPlayer={this.state.currPlayer} />
    }

    const currentPlayerColor = darkTheme.palette[`p${this.state.currPlayer + 1}color`];
    const currentPlayerName = this.state.playerNames[this.state.currPlayer]
    const ruleset = this.state.ruleset;
    const activeStages = this.state.currGame > 0
      ? ruleset.neutralStages.concat(ruleset.counterpickStages)
      : ruleset.neutralStages;

    return <>
      <Container>
        <Box
          style={{
            display: "flex",
            flexDirection: "column",
            height: "100vh",
            gap: darkTheme.spacing(2),
          }}
          paddingY={2}
        >
          <Grid
            container
            xs
            textAlign={"center"}
            spacing={{ xs: 0, sm: 1 }}
            justifyItems="center"
            style={{ flexGrow: 0 }}
          >
            <Grid item xs={12}>
              <Typography
                variant={"h4"}
                component="div"
              >
                {this.state.phase && `${this.state.phase} / `}
                {this.state.match && `${this.state.match} / `}
                {i18n.t("game", { value: this.state.currGame + 1 })}
                {this.state.bestOf &&
                  ` (${i18n.t("best_of", { value: this.state.bestOf })})`
                }
              </Typography>
            </Grid>
            <Grid item xs={12}>
              <Typography
                variant={"h4"}
                component="div"
              >
                {`${this.PlayerWinCount(0)} - ${this.PlayerWinCount(1)}`}
              </Typography>
            </Grid>
            { this.state.currPlayer !== -1 &&
              <StagePromptText
                selectedStage={this.state.selectedStage}
                isGentlemans={this.state.gentlemans}
                currGame={this.state.currGame}
                currStep={this.state.currStep}
                strikeNumber={this.GetStrikeNumber()}
                currentPlayerColor={currentPlayerColor}
                currentPlayerName={currentPlayerName}
              />
            }
          </Grid>
          <Grid
            container
            xs
            textAlign={"center"}
            spacing={1}
            justifyItems="center"
            style={{ overflow: "auto", height: "100%" }}
          >
            <Grid
              item
              container
              xs={12}
              spacing={2}
              justifyContent="center"
              alignContent={"center"}
            >
              {activeStages.map((stage) =>
                <StageCard
                  key={stage.en_name}
                  stageName={StageName(stage)}
                  stageImage={`${BASE_URL}/${stage.path}`}
                  isSelected={this.state.selectedStage === stage.codename}
                  onClick={() => StageClicked(stage)}
                  isStriked={this.IsStageStriked(stage.codename)}
                  isBanned={this.IsStageBanned(stage.codename)}
                  isGentlemanEnabled={this.state.gentlemans}
                  currentPlayerName={this.state.playerNames[this.state.currPlayer]}
                  strikedBy={this.PlayerWhoStrikedStage(stage.codename)}
                />
              )}

            </Grid>
          </Grid>
          <Grid
            container
            xs
            textAlign={"center"}
            spacing={1}
            justifyItems="center"
            style={{ flexGrow: 0, zIndex: 9999 }}
          >
            { /* Has Confirm and p1/p2 win buttons */ }
            <Box style={{ position: "relative", width: "100%" }}>
              {this.CanConfirm() && (
                <Fab
                  size={
                    darkTheme.breakpoints.up("md") ? "large" : "small"
                  }
                  color="success"
                  variant="extended"
                  onClick={() => ConfirmClicked()}
                  style={{
                    top: -16,
                    left: "50%",
                    transform: "translateX(-50%) translateY(-100%)",
                    position: "absolute",
                  }}
                  sx={{
                    minWidth: {
                      xs: "100%",
                      md: "33%",
                    },
                  }}
                >
                  <Check sx={{ mr: 1 }} />
                  {i18n.t("confirm")}
                </Fab>
              )}

              { this.state.selectedStage &&
                [0, 1].map(playerNum =>
                  <PlayerWonButton
                    key={this.state.playerNames[playerNum]}
                    playerName={this.state.playerNames[playerNum]}
                    color={`p${playerNum+1}color`}
                    leftSide={playerNum === 0}
                  />
                )
              }
            </Box>
            <FooterControls
              canUndo={this.state.canUndo}
              canRedo={this.state.canRedo}
              isGentlemans={this.state.gentlemans}
            />
          </Grid>
        </Box>
      </Container>

      { this.state.currPlayer === -1 &&
        <RpsDialog
          playerNames={this.state.playerNames}
        />
      }
    </>
  }
}

function StageName(stage) {
  if (stage.locale) {
    if (stage.locale.hasOwnProperty(i18next.language)) {
      return stage.locale[i18next.language.replace("-", "_")];
    }
    const shortLang = i18next.language.split("-")[0];
    if (stage.locale.hasOwnProperty(shortLang)) {
      return stage.locale[shortLang];
    }
  }
  return stage.en_name; // fallback
}

export default StageStrikePage;
