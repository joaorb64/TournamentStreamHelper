import React from "react";
import {
    Button,
    Card,
    CardContent,
    Collapse, Container, IconButton,
    Paper,
    Stack,
    Typography, useMediaQuery
} from "@mui/material";
import i18n from "../i18n/config";

import SetScore from "./SetScore";
import Team from "./Team";
import {ExpandMore} from "@mui/icons-material";
import {useTheme} from "@mui/material/styles";
import {BACKEND_PORT} from "../env";
import {useSelector} from "react-redux";
import {Grid} from "@mui/system";

export default function CurrentSet({scoreboardNumber}) {
    /**
     * @typedef CurrentSetState
     * @prop {?TSHScoreInfo} score
     * @prop {boolean} expanded
     */

    /** @type {CurrentSetState} */
    const [expanded, setExpanded] = React.useState(true);

    const tshState = useSelector(state => state.tshState.tshState);
    const tshChars = useSelector(state => state.tshPlayers.players);
    const theme = useTheme();
    const isSmall = useMediaQuery(theme.breakpoints.down('lg'));


    /** @type {TSHScoreInfo} */
    const score = tshState?.score[scoreboardNumber];
    const team1Ref = React.createRef();
    const team2Ref = React.createRef();
    const scoreRef = React.createRef();

    const submitChanges = () => {
        Promise.all([
            team1Ref.current.submitTeamData(scoreboardNumber).catch(console.error),
            team2Ref.current.submitTeamData(scoreboardNumber).catch(console.error),
            scoreRef.current.submitScore(scoreboardNumber).catch(console.error),
            scoreRef.current.submitSetInfo(scoreboardNumber).catch(console.error)
        ]).catch((e) => console.log("Error submitting data: ", e.text()));
    }

    const clearScoreboard = () => {
        fetch(`http://${window.location.hostname}:${BACKEND_PORT}/scoreboard${scoreboardNumber}-clear-all`)
            .catch(console.error);
    }

    const swapTeams = () => {
        fetch(`http://${window.location.hostname}:${BACKEND_PORT}/scoreboard${scoreboardNumber}-swap-teams`)
            .catch(console.error)
    }

    const hasSuitableTeamCount =
        !!score
        && !!score.team
        && Object.keys(score.team).length >= 2;

    if (!hasSuitableTeamCount) {
        return <Typography sx={{typography: isSmall ? "h7": "h5"}}>
            {i18n.t("no_set")}
        </Typography>
    }

    const teamKeys = Object.keys(score.team).sort()
    const teams = [score.team[teamKeys[0]], score.team[teamKeys[1]]];

    return (<>
        <span style={{position: 'relative', float: 'right'}}>
                <IconButton
                    title={i18n.t("expand_scoreboard")}
                    sx={{
                        position: 'absolute',
                        top: "-48px",
                        right: "0px",
                    }}
                    onClick={() => setExpanded(!expanded)}
                >
                    <ExpandMore sx={{
                        transform: expanded ? 'rotate(0deg)' : 'rotate(270deg)'
                    }} />
                </IconButton>
            </span>
        <Card>
            <Collapse in={expanded} timeout={"auto"}>
                <CardContent>
                    {
                        hasSuitableTeamCount && (
                            <Grid
                                container
                                direction={"row"}
                                spacing={2}
                                alignItems={"stretch"}
                                justifyContent={"space-evenly"}
                            >
                                <Grid
                                    size={isSmall ? 12 : 4.5}
                                >
                                    <Container disableGutters maxWidth={'sm'}>
                                        <Team
                                            key={`s-${scoreboardNumber}-t-${teamKeys[0]}`}
                                            teamId={`s-${scoreboardNumber}-t-${teamKeys[0]}`}
                                            tshTeamId={teamKeys[0]}
                                            ref={team1Ref}
                                            team={teams[0]}
                                            characters={tshChars}
                                        />
                                    </Container>
                                </Grid>


                                <Grid size={isSmall ? 12 : 3}>
                                    <Container disableGutters maxWidth={'xs'}>
                                        <Stack gap={4}>
                                            <Paper sx={{padding:2}} elevation={3}>
                                                <SetScore
                                                    key={score.set_id + "score"}
                                                    leftTeam={teams[0]}
                                                    rightTeam={teams[1]}
                                                    best_of={score.best_of}
                                                    match={score.match ?? ""}
                                                    phase={score.phase ?? ""}
                                                    ref={scoreRef}
                                                />
                                            </Paper>

                                            <Stack gap={2}>
                                                <Button variant={"outlined"} onClick={submitChanges}>Submit Changes</Button>
                                                <Button variant={"outlined"} onClick={clearScoreboard}>Clear Scoreboard</Button>
                                                <Button variant={"outlined"} onClick={swapTeams}>Swap Teams</Button>
                                            </Stack>
                                        </Stack>
                                    </Container>
                                </Grid>

                                    <Grid size={isSmall ? 12 : 4.5}>
                                        <Container disableGutters maxWidth={'sm'}>
                                            <Team key={`s-${scoreboardNumber}-t-${teamKeys[1]}`}
                                                  teamId={`s-${scoreboardNumber}-t-${teamKeys[1]}`}
                                                  tshTeamId={teamKeys[1]}
                                                  ref={team2Ref}
                                                  team={teams[1]}
                                            />
                                        </Container>
                                    </Grid>
                            </Grid>
                        )
                    }
                </CardContent>
            </Collapse>
        </Card>
    </>)
}
