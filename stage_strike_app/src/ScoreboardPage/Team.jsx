import React from "react";
import {Checkbox, FormControlLabel, FormGroup, Paper, Stack} from "@mui/material";
import Player from "./Player";
import {Box} from "@mui/system";
import {BACKEND_PORT} from "../env";

export default React.forwardRef(
    /**
     * @param {Object} props
     * @param {string} props.teamId
     * @param {string|int} props.tshTeamId
     * @param {TSHTeamInfo} props.team
     * @param {React.ForwardedRef<unknown>} ref
     */
    function Team({teamId, tshTeamId, team}, ref) {

    /**
     * @typedef {Object} TeamState
     * @prop {boolean} inLosers
     */
    const [state, setState] = React.useState( {inLosers: team.losers});

        React.useEffect(() => {
            setState(s => ({
                ...s,
                inLosers: team.losers
            }))
        }, [team.losers]);

    React.useImperativeHandle(ref, () => {
        return {
            submitTeamData: submitTeamData,
            getTeamDataFromForm: getTeamDataFromForm
        }
    },);

    const playerRefs = [];

    /** @returns {[any, TSHPlayerInfo]} */
    const playersInTeam = () => {
        return Object.keys(team.player).sort().map(k => [k, team.player[k]]);
    }

    const getTeamDataFromForm = () => {
        /** @type TSHTeamInfo */ const rval = JSON.parse(JSON.stringify(team));
        for (const teamKey in playerRefs) {
            /** @type Player */ const widget = playerRefs[teamKey].current;
            rval.player[teamKey] = widget.getModifiedPlayerData();
        }
        return rval;
    }

    const submitTeamData = (scoreboardNumber) => {
        const teamData = getTeamDataFromForm();

        return Promise.all(
            [
                (
                    fetch(`http://${window.location.hostname}:${BACKEND_PORT}/scoreboard${scoreboardNumber}-set?` + new URLSearchParams({
                        losers: state.inLosers,
                        team: tshTeamId
                    }).toString())
                        .then(resp => resp.text())
                        .then((d) => console.log("Submit set info: ", d))
                ),
                ...Object.entries(teamData.player).map(([teamKey, playerData]) => {
                    const body = {...playerData};
                    console.log("team update payload", body);

                    return fetch(
                        `http://${window.location.hostname}:${BACKEND_PORT}`
                        + `/scoreboard${scoreboardNumber}-update-team-${tshTeamId}-${teamKey}`,
                        {
                            method: 'POST',
                            headers: {'content-type': 'application/json'},
                            body: JSON.stringify(body)
                        }
                    )
                        .then((resp) => resp.text())
                        .then((d) => console.info(`Submitted team ${tshTeamId} data: `, d))
                        .catch(console.error);
                })
            ]
        );
    };

    const playerWidgets = playersInTeam().map(([teamKey, player]) => {
        if (!(teamKey in playerRefs)) {
            playerRefs[teamKey] = React.createRef();
        }

        return (
            <Player
                key={`${teamId}-p-${teamKey}`}
                ref={playerRefs[teamKey]}
                teamId={teamId}
                teamKey={teamKey}
                player={player}
            />
        );
    });

    let borderStyle = {};
    if (team.color) {
        borderStyle = {
            borderTop: `solid 4px ${team.color}`
        };
    }

    return <Paper padding={2} elevation={3} sx={borderStyle}>
        <Box paddingX={1}>
            <FormGroup>
                <FormControlLabel
                    control={
                        <Checkbox
                            id={teamId + "-losers"}
                            checked={state.inLosers}
                            onChange={
                                (e) => {
                                    setState(s => ({...s, inLosers: e.target.checked}))
                                }
                            }
                        />
                    }
                    label={"Losers Bracket"}
                />
            </FormGroup>
        </Box>

        <Stack gap={2} padding={1}>
            {playerWidgets}
        </Stack>
    </Paper>
});

