import React from "react";
import {
    Button,
    Card,
    CardContent,
    CardHeader,
    Collapse, IconButton,
    Paper,
    Stack,
    Typography, useMediaQuery
} from "@mui/material";
import i18n from "../i18n/config";

import SetScore from "./SetScore";
import Team from "./Team";
import {ExpandMore} from "@mui/icons-material";
import {TSHCharacterContext, TSHStateContext} from "./Contexts";
import {useTheme} from "@mui/material/styles";

export default function CurrentSet() {
    /**
     * @typedef CurrentSetState
     * @prop {?TSHScoreInfo} score
     * @prop {boolean} expanded
     */

    /** @type {CurrentSetState} */
    const [expanded, setExpanded] = React.useState(true);

    const tshState = React.useContext(TSHStateContext);
    const tshChars = React.useContext(TSHCharacterContext);
    const theme = useTheme();
    const isSmall = useMediaQuery(theme.breakpoints.down('md'));


    /** @type {TSHScoreInfo} */
    const score = tshState?.score[1];
    const team1Ref = React.createRef();
    const team2Ref = React.createRef();
    const scoreRef = React.createRef();

    const submitChanges = () => {
        Promise.all([
            team1Ref.current.submitTeamData().catch(console.error),
            team2Ref.current.submitTeamData().catch(console.error),
            scoreRef.current.submitScore().catch(console.error),
            scoreRef.current.submitSetInfo().catch(console.error)
        ]).catch((e) => console.log("Error submitting data: ", e.text()));
    }

    const clearScoreboard = () => {
        fetch(`http://${window.location.hostname}:5000/scoreboard1-clear-all`)
            .catch(console.error);
    }

    const swapTeams = () => {
        fetch(`http://${window.location.hostname}:5000/scoreboard1-swap-teams`)
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
    const setId = score.set_id ?? 'unk';
    const teams = [score.team[teamKeys[0]], score.team[teamKeys[1]]];

    let setTitle;
    const {phase, match} = score;
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
                    <IconButton onClick={() => setExpanded(!expanded)}>
                        <ExpandMore sx={{
                            transform: expanded ? 'rotate(0deg)' : 'rotate(270deg)'
                        }} />
                    </IconButton>
                }
            />
            <Collapse in={expanded} timeout={"auto"}>
                <CardContent>
                    {
                        hasSuitableTeamCount && (
                            <Stack direction={isSmall ? "column" : "row"}
                                   spacing={2}
                                   alignItems={"center"}
                                   justifyContent={"space-evenly"}
                            >
                                <Team
                                      key={`s-${setId}-t-${teamKeys[0]}`}
                                      teamId={`s-${setId}-t-${teamKeys[0]}`}
                                      tshTeamId={teamKeys[0]}
                                      ref={team1Ref}
                                      team={teams[0]}
                                      characters={tshChars}
                                />

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

                                <Team key={`s-${setId}-t-${teamKeys[1]}`}
                                      teamId={`s-${setId}-t-${teamKeys[1]}`}
                                      tshTeamId={teamKeys[1]}
                                      ref={team2Ref}
                                      team={teams[1]}
                                />
                            </Stack>
                        )
                    }
                </CardContent>
            </Collapse>
        </Card>
    )
}
