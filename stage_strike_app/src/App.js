import logo from "./logo.svg";
import "./App.css";
import { Component } from "react";
import {
  useTheme,
  ThemeProvider,
  createTheme,
  responsiveFontSizes,
} from "@mui/material/styles";
import {
  Button,
  Card,
  CardActionArea,
  CardContent,
  CardMedia,
  Container,
  CssBaseline,
  Grid,
  Typography,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
} from "@mui/material";
import { Box } from "@mui/system";

const defaultTheme = createTheme({
  palette: {
    mode: "dark",
  },
});

let darkTheme = createTheme({
  palette: {
    mode: "dark",
    p1color: defaultTheme.palette.augmentColor({
      color: { main: "#ff3837ff" },
      name: "p1color",
    }),
    p2color: defaultTheme.palette.augmentColor({
      color: { main: "#1255a3ff" },
      name: "p2color",
    }),
  },
});

darkTheme = responsiveFontSizes(darkTheme);

class App extends Component {
  state = {
    ruleset: null,
    currGame: 0,
    currPlayer: -1,
    currStep: 0,
    strikedStages: [],
    stagesWon: [[], []],
    stagesPicked: [],
    selectedStage: null,
    lastWinner: -1,
    playerNames: [],
    phase: null,
    match: null,
    bestOf: null,
  };

  Initialize() {
    this.setState({
      currGame: 0,
      currPlayer: -1,
      currStep: 0,
      strikedStages: [[]],
      stagesWon: [[], []],
      stagesPicked: [],
      selectedStage: null,
      lastWinner: -1,
    });
  }

  GetStage(stage) {
    let found = this.state.ruleset.neutralStages.find((s) => s.name === stage);
    if (found) return found;
    found = this.state.ruleset.counterpickStages.find((s) => s.name === stage);
    if (found) return found;
    return null;
  }

  IsStageStriked(stage, previously = false) {
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
      banList = this.state.stagesWon[(this.state.lastWinner + 1) % 2];
    }

    return banList;
  }

  IsStageBanned(stage) {
    let banList = this.GetBannedStages();

    let found = banList.findIndex((e) => e === stage);
    if (found !== -1) {
      return true;
    }
    return false;
  }

  StageClicked(stage) {
    if (this.state.currGame > 0 && this.state.currStep > 0) {
      // pick
      if (!this.IsStageBanned(stage.name) && !this.IsStageStriked(stage.name)) {
        this.state.selectedStage = stage.name;
        this.setState(this.state);
      }
    } else if (
      !this.IsStageStriked(stage.name, true) &&
      !this.IsStageBanned(stage.name)
    ) {
      // ban
      let foundIndex = this.state.strikedStages[this.state.currStep].findIndex(
        (e) => e === stage.name
      );
      if (foundIndex === -1) {
        if (
          this.state.strikedStages[this.state.currStep].length <
          this.GetStrikeNumber()
        ) {
          this.state.strikedStages[this.state.currStep].push(stage.name);
        }
      } else {
        this.state.strikedStages[this.state.currStep].splice(foundIndex, 1);
      }
      this.setState(this.state);
    }
  }

  CanConfirm() {
    if (this.state.strikedStages[this.state.currStep]) {
      if (this.state.currGame === 0) {
        if (
          this.state.strikedStages[this.state.currStep].length ===
          this.state.ruleset.strikeOrder[this.state.currStep]
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

  ConfirmClicked() {
    if (this.state.currGame === 0) {
      if (
        this.state.strikedStages[this.state.currStep].length ===
        this.state.ruleset.strikeOrder[this.state.currStep]
      ) {
        this.state.currStep += 1;
        this.state.currPlayer = (this.state.currPlayer + 1) % 2;
        this.state.strikedStages.push([]);
      }
    } else {
      if (
        this.state.strikedStages[this.state.currStep].length ===
        this.state.ruleset.banCount
      ) {
        this.state.currStep += 1;
        this.state.currPlayer = (this.state.currPlayer + 1) % 2;
        this.state.strikedStages.push([]);
      }
    }

    if (
      this.state.currGame === 0 &&
      this.state.currStep >= this.state.ruleset.strikeOrder.length
    ) {
      let selectedStage = this.state.ruleset.neutralStages.find(
        (stage) => !this.IsStageStriked(stage.name)
      );
      this.state.selectedStage = selectedStage.name;
      this.state.stagesPicked.push(selectedStage.name);
    }

    this.setState(this.state);
    console.log(this.state);
  }

  MatchWinner(id) {
    this.state.currGame += 1;
    this.state.currStep = 0;

    this.state.stagesWon[id].push(this.state.selectedStage);
    this.state.stagesPicked.push(this.state.selectedStage);

    this.state.currPlayer = id;
    this.state.strikedStages = [[]];
    this.state.selectedStage = null;

    this.state.lastWinner = id;

    // If next step has no bans, skip it
    if (this.GetStrikeNumber() == 0) {
      this.ConfirmClicked();
    }

    this.setState(this.state);
    this.UpdateStreamScore();
  }

  GetStrikeNumber() {
    if (this.state.currGame == 0) {
      return this.state.ruleset.strikeOrder[this.state.currStep];
    } else {
      if (this.state.ruleset.banCount != 0) {
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
  }

  componentDidMount() {
    window.setInterval(() => this.FetchRuleset(), 1000);
    window.setInterval(() => this.UpdateStream(), 1000);
  }

  FetchRuleset() {
    fetch("http://" + window.location.hostname + ":5000/ruleset")
      .then((res) => res.json())
      .then((data) => {
        let oldRuleset = this.state.ruleset;

        this.setState({
          playerNames: [data.p1 ? data.p1 : "P1", data.p2 ? data.p2 : "P2"],
          ruleset: data.ruleset,
          phase: data.phase,
          match: data.match,
          bestOf: data.best_of,
        });

        // Reset only if ruleset changed
        if (JSON.stringify(oldRuleset) !== JSON.stringify(this.state.ruleset)) {
          this.Initialize();
        }
      })
      .catch(console.log);
  }

  UpdateStream() {
    let allStages =
      this.state.currGame === 0
        ? this.state.ruleset.neutralStages
        : this.state.ruleset.neutralStages.concat(
            this.state.ruleset.counterpickStages
          );
    let stageMap = {};

    allStages.forEach((stage) => {
      stageMap[stage.codename] = stage;
    });

    let data = {
      dsr: this.GetBannedStages().map((stage) => this.GetStage(stage).codename),
      playerTurn: null,
      selected: this.GetStage(this.state.selectedStage),
      stages: stageMap,
      striked: this.state.ruleset.neutralStages
        .concat(this.state.ruleset.counterpickStages)
        .filter((stage) => this.IsStageStriked(stage.name))
        .map((stage) => stage.codename),
    };

    fetch("http://" + window.location.hostname + ":5000/post", {
      method: "POST",
      body: JSON.stringify(data),
      contentType: "application/json",
    });
  }

  UpdateStreamScore() {
    let data = {
      team1score: this.state.stagesWon[0].length,
      team2score: this.state.stagesWon[1].length,
    };

    fetch("http://" + window.location.hostname + ":5000/score", {
      method: "POST",
      body: JSON.stringify(data),
      contentType: "application/json",
    });
  }

  render() {
    return (
      <ThemeProvider theme={darkTheme}>
        <CssBaseline />
        {this.state.ruleset && this.state.ruleset.neutralStages.length > 0 ? (
          <>
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
                      sx={{ typography: { xs: "h7", sm: "h5" } }}
                      component="div"
                    >
                      {this.state.phase ? this.state.phase + " / " : ""}
                      {this.state.match ? this.state.match + " / " : ""}
                      Game {this.state.currGame + 1}
                      {this.state.bestOf
                        ? " (Best of " + this.state.bestOf + ")"
                        : ""}
                    </Typography>
                  </Grid>
                  <Grid item xs={12}>
                    <Typography
                      sx={{ typography: { xs: "h7", sm: "h4" } }}
                      component="div"
                    >
                      {this.state.stagesWon[0].length} -{" "}
                      {this.state.stagesWon[1].length}
                    </Typography>
                  </Grid>
                  {this.state.currPlayer != -1 ? (
                    <Grid item xs={12}>
                      <Typography
                        sx={{ typography: { xs: "h6", sm: "h4" } }}
                        component="div"
                      >
                        {this.state.selectedStage ? (
                          <>Report Results</>
                        ) : this.state.currGame > 0 &&
                          this.state.currStep > 0 ? (
                          <>
                            <span
                              style={{
                                color:
                                  darkTheme.palette[
                                    `p${this.state.currPlayer + 1}color`
                                  ].main,
                              }}
                            >
                              {this.state.playerNames[this.state.currPlayer]}
                            </span>
                            , pick a stage
                          </>
                        ) : (
                          <>
                            <span
                              style={{
                                color:
                                  darkTheme.palette[
                                    `p${this.state.currPlayer + 1}color`
                                  ].main,
                              }}
                            >
                              {this.state.playerNames[this.state.currPlayer]}
                            </span>
                            , ban {this.GetStrikeNumber()} stage(s)
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
                  alignContent={"center"}
                  alignItems="center"
                  sx={{
                    overflow: { xs: "scroll", lg: "hidden" },
                    "flex-wrap": { xs: "nowrap", lg: "wrap" },
                  }}
                >
                  <Grid
                    item
                    container
                    xs={12}
                    spacing={2}
                    justifyContent="center"
                    alignContent={"center"}
                    style={{ height: "100%" }}
                  >
                    <>
                      {(this.state.currGame > 0
                        ? this.state.ruleset.neutralStages.concat(
                            this.state.ruleset.counterpickStages
                          )
                        : this.state.ruleset.neutralStages
                      ).map((stage) => (
                        <Grid item xs={4} sm={3} md={2}>
                          <Card>
                            <CardActionArea
                              onClick={() => this.StageClicked(stage)}
                            >
                              {this.IsStageStriked(stage.name) ? (
                                <div className="stamp stage-striked"></div>
                              ) : null}
                              {this.IsStageBanned(stage.name) ? (
                                <div className="stamp stage-dsr"></div>
                              ) : null}
                              {this.state.selectedStage === stage.name ? (
                                <div className="stamp stage-selected"></div>
                              ) : null}
                              <CardMedia
                                component="img"
                                height={{ sm: "50", md: "100" }}
                                image={`http://${window.location.hostname}:5000/${stage.path}`}
                              />
                              <CardContent
                                style={{ padding: darkTheme.spacing(1) }}
                              >
                                <Typography
                                  variant="button"
                                  component="div"
                                  noWrap
                                  fontSize={{ xs: 8, md: "" }}
                                >
                                  {stage.name}
                                </Typography>
                              </CardContent>
                            </CardActionArea>
                          </Card>
                        </Grid>
                      ))}
                    </>
                  </Grid>
                </Grid>
                <Grid
                  container
                  xs
                  textAlign={"center"}
                  spacing={1}
                  justifyItems="center"
                  style={{ flexGrow: 0 }}
                >
                  <Grid
                    container
                    item
                    xs={12}
                    spacing={2}
                    justifyContent="center"
                  >
                    <Grid item xs={4}>
                      <Button
                        size={
                          darkTheme.breakpoints.up("md") ? "large" : "small"
                        }
                        fontSize={darkTheme.breakpoints.up("md") ? 8 : ""}
                        fullWidth
                        color="success"
                        variant={this.CanConfirm() ? "contained" : "outlined"}
                        onClick={() => this.ConfirmClicked()}
                      >
                        Confirm
                      </Button>
                    </Grid>
                    <Grid item xs={4}>
                      <Button
                        size={
                          darkTheme.breakpoints.up("md") ? "large" : "small"
                        }
                        fontSize={darkTheme.breakpoints.up("md") ? 8 : ""}
                        fullWidth
                        variant="outlined"
                        onClick={() => this.Initialize()}
                      >
                        Reset
                      </Button>
                    </Grid>
                  </Grid>
                  {this.state.selectedStage ? (
                    <Grid
                      container
                      item
                      xs={12}
                      spacing={2}
                      justifyContent="center"
                    >
                      <Grid item xs={4}>
                        <Button
                          size={
                            darkTheme.breakpoints.up("md") ? "large" : "small"
                          }
                          fontSize={darkTheme.breakpoints.up("md") ? 8 : ""}
                          fullWidth
                          color="p1color"
                          variant="contained"
                          onClick={() => this.MatchWinner(0)}
                        >
                          {this.state.playerNames[0]} won
                        </Button>
                      </Grid>
                      <Grid item xs={4}>
                        <Button
                          size={
                            darkTheme.breakpoints.up("md") ? "large" : "small"
                          }
                          fontSize={darkTheme.breakpoints.up("md") ? 8 : ""}
                          fullWidth
                          color="p2color"
                          variant="contained"
                          onClick={() => this.MatchWinner(1)}
                        >
                          {this.state.playerNames[1]} won
                        </Button>
                      </Grid>
                    </Grid>
                  ) : null}
                </Grid>
              </Box>
            </Container>
            <Dialog
              open={this.state.currPlayer == -1}
              onClose={() => {}}
              aria-labelledby="modal-modal-title"
              aria-describedby="modal-modal-description"
            >
              <DialogTitle id="responsive-dialog-title">
                {"Stage Strike"}
              </DialogTitle>
              <DialogContent>
                <Box
                  component="div"
                  gap={2}
                  display="flex"
                  flexDirection={"column"}
                >
                  <Typography>
                    Play rock-paper-scissors to decide who starts the stage
                    strike process, or use the randomize button.
                  </Typography>

                  <Typography
                    sx={{ typography: { xs: "h6", sm: "h5" } }}
                    align="center"
                  >
                    Rock-Paper-Scissors
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
                        onClick={() => this.setState({ currPlayer: 0 })}
                      >
                        {this.state.playerNames[0]} won
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
                        onClick={() => this.setState({ currPlayer: 1 })}
                      >
                        {this.state.playerNames[1]} won
                      </Button>
                    </Grid>
                  </Grid>
                  <Typography
                    sx={{ typography: { xs: "h6", sm: "h5" } }}
                    align="center"
                  >
                    Randomize
                  </Typography>
                  <Button
                    size={darkTheme.breakpoints.up("md") ? "large" : "small"}
                    fontSize={darkTheme.breakpoints.up("md") ? 8 : ""}
                    fullWidth
                    color="success"
                    variant="outlined"
                    onClick={() =>
                      this.setState({ currPlayer: Math.random() > 0.5 ? 1 : 0 })
                    }
                  >
                    Randomize
                  </Button>
                </Box>
              </DialogContent>
            </Dialog>
          </>
        ) : null}

        {this.state.ruleset != null &&
        this.state.ruleset.neutralStages.length == 0 ? (
          <>
            <Dialog
              open={this.state.currPlayer == -1}
              onClose={() => {}}
              aria-labelledby="modal-modal-title"
              aria-describedby="modal-modal-description"
            >
              <DialogTitle id="responsive-dialog-title">
                {"Stage Strike"}
              </DialogTitle>
              <DialogContent>
                <Box
                  component="div"
                  gap={2}
                  display="flex"
                  flexDirection={"column"}
                >
                  <Typography>
                    No ruleset is selected. Please notify production/TO to
                    select a ruleset.
                  </Typography>
                </Box>
              </DialogContent>
            </Dialog>
          </>
        ) : null}
      </ThemeProvider>
    );
  }
}

export default App;
