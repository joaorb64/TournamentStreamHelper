import { Component } from "react";
import ReactDOMServer from "react-dom/server";
import "../NoSleep";
import {
  Button,
  Card,
  CardActionArea,
  CardMedia,
  Container,
  GridLegacy as Grid,
  Typography,
  Dialog,
  DialogTitle,
  DialogContent,
  Fab,
} from "@mui/material";
import { Box } from "@mui/system";
import i18n from "../i18n/config";
import { Check, Handshake, Redo, RestartAlt, Undo } from "@mui/icons-material";
import i18next from "i18next";
import {darkTheme} from "../themes";
import {BACKEND_PORT, BASE_URL} from "../env";
import {NoRulesetError} from "./NoRulesetError";
import {StageCard} from "./StageCard";
import {
  ConfirmClicked,
  MatchWinner,
  ReportRpsWin,
  RestartStageStrike,
  SetGentlemans,
  StageClicked
} from "./postActions";
import {RpsDialog} from "./RpsDialog";

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
    if (this.state.strikedStages[this.state.currStep]) {
      if (this.state.currGame === 0) {
        if (
          this.state.strikedStages[this.state.currStep].length ===
            this.state.ruleset.strikeOrder[this.state.currStep] &&
          !this.state.selectedStage
        ) {
          return true;
        }
      } else {
        if (
          this.state.strikedStages[this.state.currStep].length ===
          this.GetStrikeNumber()
        ) {
          return true;
        }
      }
    }

    return false;
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

  componentDidMount() {
    window.setInterval(() => this.FetchRuleset(), 100);
  }

  FetchRuleset = () => {
    fetch("http://" + window.location.hostname + `:${BACKEND_PORT}/ruleset`)
      .then((res) => res.json())
      .then((data) => {
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
      })
      .catch(console.log);
  }
  render() {
    return (
        <>
          {this.state.ruleset && this.state.ruleset.neutralStages.length > 0
            ? <>
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
                        {this.state.phase ? this.state.phase + " / " : ""}
                        {this.state.match ? this.state.match + " / " : ""}
                        {i18n.t("game", { value: this.state.currGame + 1 })}
                        {this.state.bestOf
                          ? " (" +
                          i18n.t("best_of", { value: this.state.bestOf }) +
                          ")"
                          : ""}
                      </Typography>
                    </Grid>
                    <Grid item xs={12}>
                      <Typography
                        variant={"h4"}
                        component="div"
                      >
                        {this.state.stagesWon && this.state.stagesWon.length > 0
                          ? this.state.stagesWon[0].length
                          : 0}{" "}
                        -{" "}
                        {this.state.stagesWon && this.state.stagesWon.length > 0
                          ? this.state.stagesWon[1].length
                          : 0}
                      </Typography>
                    </Grid>
                    {this.state.currPlayer !== -1 ? (
                      <Grid item xs={12}>
                        <Typography
                          sx={{ typography: { xs: "h6", sm: "h4" } }}
                          component="div"
                        >
                          {this.state.selectedStage ? (
                            <>{i18n.t("report_results")}</>
                          ) : (
                            <>
                              {this.state.gentlemans ? (
                                <>
                                  {i18n.t("gentlemans_prompt", {
                                    gentlemans_pick: i18n.t("gentlemans_pick"),
                                  })}
                                </>
                              ) : this.state.currGame > 0 &&
                              this.state.currStep > 0 ? (
                                <div
                                  dangerouslySetInnerHTML={{
                                    __html: i18n.t("select_a_stage_prompt", {
                                      player: ReactDOMServer.renderToStaticMarkup(
                                        <span
                                          style={{
                                            color:
                                            darkTheme.palette[
                                              `p${
                                                this.state.currPlayer + 1
                                              }color`
                                              ].main,
                                          }}
                                        >
                                        {
                                          this.state.playerNames[
                                            this.state.currPlayer
                                            ]
                                        }
                                      </span>
                                      ),
                                      val: this.GetStrikeNumber(),
                                      interpolation: { escapeValue: false },
                                    }),
                                  }}
                                ></div>
                              ) : (
                                <div
                                  dangerouslySetInnerHTML={{
                                    __html: i18n.t("ban_prompt", {
                                      player: ReactDOMServer.renderToStaticMarkup(
                                        <span
                                          style={{
                                            color:
                                            darkTheme.palette[
                                              `p${
                                                this.state.currPlayer + 1
                                              }color`
                                              ].main,
                                          }}
                                        >
                                        {
                                          this.state.playerNames[
                                            this.state.currPlayer
                                            ]
                                        }
                                      </span>
                                      ),
                                      val: this.GetStrikeNumber(),
                                      interpolation: { escapeValue: false },
                                    }),
                                  }}
                                ></div>
                              )}
                            </>
                          )}
                        </Typography>
                      </Grid>
                    ) : null}
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
                      {(this.state.currGame > 0
                          ? this.state.ruleset.neutralStages.concat(
                            this.state.ruleset.counterpickStages
                          )
                          : this.state.ruleset.neutralStages
                      ).map((stage) =>
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
                          strikedBy={
                            this.state.strikedBy[0].findIndex(
                              (s) => s === stage.codename
                            ) !== -1
                              ? this.state.playerNames[0]
                              : this.state.playerNames[1]
                          }
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
                      {this.state.selectedStage && (
                        <Fab
                          size={
                            darkTheme.breakpoints.up("md") ? "large" : "small"
                          }
                          fontSize={darkTheme.breakpoints.up("md") ? 8 : ""}
                          fullWidth
                          color="p1color"
                          variant="extended"
                          onClick={() => MatchWinner(0)}
                          style={{
                            top: -16,
                            left: 16,
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
                            player: this.state.playerNames[0],
                          })}
                        </Fab>
                      )}

                      {this.state.selectedStage && (
                        <Fab
                          size={
                            darkTheme.breakpoints.up("md") ? "large" : "small"
                          }
                          fontSize={darkTheme.breakpoints.up("md") ? 8 : ""}
                          fullWidth
                          color="p2color"
                          variant="extended"
                          onClick={() => MatchWinner(1)}
                          style={{
                            top: -16,
                            right: 16,
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
                            player: this.state.playerNames[1],
                          })}
                        </Fab>
                      )}
                    </Box>
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
                          disabled={!this.state.canUndo}
                          variant="outlined"
                          sx={{
                            flexDirection: { xs: "column", lg: "unset" },
                            fontSize: { xs: 10, lg: "unset" },
                          }}
                          onClick={() => {
                            this.Undo();
                          }}
                          startIcon={<Undo />}
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
                          disabled={!this.state.canRedo}
                          variant="outlined"
                          sx={{
                            flexDirection: { xs: "column", lg: "unset" },
                            fontSize: { xs: 10, lg: "unset" },
                          }}
                          onClick={() => {
                            this.Redo();
                          }}
                          startIcon={<Redo />}
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
                            this.state.gentlemans ? "contained" : "outlined"
                          }
                          startIcon={<Handshake />}
                          onClick={() => {
                            SetGentlemans(!this.state.gentlemans);
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
                  </Grid>
                </Box>
              </Container>

              { this.state.currPlayer === -1 &&
                <RpsDialog
                  playerNames={this.state.playerNames}
                />
              }
            </>
            : <NoRulesetError currPlayer={this.state.currPlayer} />
          }
        </>
    );
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
