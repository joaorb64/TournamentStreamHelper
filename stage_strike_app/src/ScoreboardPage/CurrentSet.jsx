import React from "react";
import {
    Backdrop,
    Button,
    Card,
    CardContent,
    CardHeader,
    CircularProgress, Collapse, IconButton,
    Paper,
    Stack,
    Typography
} from "@mui/material";
import i18n from "../i18n/config";

import SetScore from "./SetScore";
import Team from "./Team";
import {ExpandMore} from "@mui/icons-material";

export default class CurrentSet extends React.Component {
    /**
     * @typedef CurrentSetState
     * @prop {?TSHScoreInfo} score
     * @prop {boolean} isLoading
     * @prop {boolean} expanded
     */

    /** @type {CurrentSetState} */
    state;

    /** @param {TSHCharacters} props.characters */
    constructor(props) {
        super(props);

        this.team1Ref = React.createRef();
        this.team2Ref = React.createRef();
        this.scoreRef = React.createRef();

        this.props = props;
        this.state = {
            score: null,
            isLoading: false,
            expanded: true
        }
    }

    componentDidMount = () => {
        this.FetchScore();
    }

    FetchScore = (/** number | string | null */ targetSetId = null) => {
        const retries = 10;
        const timeout = 1000;
        let currentRetry = 0;

        if (targetSetId !== null) {
            targetSetId = String(targetSetId);
        }

        this.setState({...this.state, isLoading: true});

        const retry = () => {
            if (currentRetry++ > retries) {
                console.error(`Couldn't load target set after ${retries} retries)`);
            } else {
                setTimeout(do_it, timeout);
            }
        }

        const do_it = () => {
            console.log("Loading current set...");

            fetch("http://" + window.location.hostname + `:5000/scoreboard1-get`)
                .then((res) => res.json())
                .then(( /** TSHScoreInfo */ data) => {
                    if (!!(targetSetId) && data.set_id !== targetSetId) {
                        console.log(`Fetched set_id ${data.set_id} but looking for ${targetSetId}. Retrying...`);
                        retry();
                    } else if ((!!targetSetId) && (data.match === "" || data.phase === "")) {
                        console.log(`Set appears to be only partially loaded. Retrying...`);
                        retry();
                    } else {
                        console.log("Set loaded successfully", data);
                        this.setState({
                            isLoading: false,
                            score: data
                        });
                    }
                })
                .catch((e) => {
                    console.error(e);
                    if (currentRetry++ > retries) {
                        console.error(`Couldn't load target set after ${retries} retries)`);
                        retry();
                    }
                });
        }

        do_it();
    }

    submitChanges = () => {
        Promise.all([
            this.team1Ref.current.submitTeamData().catch(console.error),
            this.team2Ref.current.submitTeamData().catch(console.error),
            this.scoreRef.current.submitScore().catch(console.error),
            this.scoreRef.current.submitSetInfo().catch(console.error)
        ]).catch((e) => console.log("Error submitting data: ", e.text()));
    }

    clearScoreboard = () => {
        this.setState({
            ...this.state,
            isLoading: true
        });

        fetch(`http://${window.location.hostname}:5000/scoreboard1-clear-all`)
            .then(resp => resp.text())
            .then(() => {setTimeout(this.FetchScore, 1000);})
            .catch(console.error);
    }

    render = () => {
        const hasSuitableTeamCount =
            this.state.score !== null
            && this.state.score.team !== null
            && Object.keys(this.state.score.team).length >= 2;

        if (!hasSuitableTeamCount) {
            return <Typography sx={{ typography: {xs: "h7", sm: "h5"}}}>
                {i18n.t("no_set")}
            </Typography>
        }

        const teamKeys = Object.keys(this.state.score.team).sort()
        const teams = [this.state.score.team[teamKeys[0]], this.state.score.team[teamKeys[1]]];

        if (this.state.isLoading) {
            return (
                <div style={{position: "relative", height: "200px"}}>
                    <Backdrop open={true} sx={{position: "absolute"}}>
                        <CircularProgress>{i18n.t("Loading...")}</CircularProgress>
                    </Backdrop>
                </div>
            )
        }

        let setTitle;
        const {phase, match} = this.state.score;
        if (!!phase) {
            if (!!match) {
                setTitle = `${match}`;
            } else {
                setTitle = phase;
            }
        } else {
            if (!!match) {
                setTitle = match;
            } else {
                setTitle = i18n.t("unknown");
            }
        }

        return (
                <Card>
                    <CardHeader
                        title={`Current Set: ${setTitle}`}
                        action={
                            <IconButton onClick={() => this.setState({...this.state, expanded: !this.state.expanded})}>
                                <ExpandMore sx={{
                                    transform: this.state.expanded ? 'rotate(0deg)' : 'rotate(270deg)'
                                }} />
                            </IconButton>
                        }
                    />
                    <Collapse in={this.state.expanded} timeout={"auto"}>
                        <CardContent>
                            {
                                hasSuitableTeamCount && (
                                    <Stack direction={{xs: "column", sm: "row"}} spacing={2} alignItems={"center"} justifyContent={"space-evenly"}>
                                        <Team ref={this.team1Ref}
                                              key={this.state.score.set_id + "1"}
                                              teamId={teamKeys[0]}
                                              team={teams[0]}
                                              characters={this.props.characters}
                                        />

                                        <Stack gap={4}>
                                            <Paper sx={{padding:2}} elevation={3}>
                                                <SetScore
                                                    key={this.state.score.set_id + "score"}
                                                    leftTeam={teams[0]}
                                                    rightTeam={teams[1]}
                                                    best_of={this.state.score.best_of}
                                                    match={this.state.score.match ?? ""}
                                                    phase={this.state.score.phase ?? ""}
                                                    ref={this.scoreRef}
                                                />
                                            </Paper>

                                            <Stack gap={2}>
                                                <Button variant={"outlined"} onClick={this.submitChanges}>Submit Changes</Button>
                                                <Button variant={"outlined"} onClick={this.clearScoreboard}>Clear Scoreboard</Button>
                                            </Stack>
                                        </Stack>

                                        <Team key={this.state.score.set_id + "2"}
                                              ref={this.team2Ref}
                                              teamId={teamKeys[1]}
                                              team={teams[1]}
                                              characters={this.props.characters}
                                        />
                                    </Stack>
                                )
                            }
                        </CardContent>
                    </Collapse>
                </Card>
        )

    }
}
