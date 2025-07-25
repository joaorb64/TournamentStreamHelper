import React from "react";
import {Paper, Stack} from "@mui/material";
import Player from "./Player";

export default React.forwardRef(function Team({teamId, team}, ref) {
    /**
     * @typedef {Object} TeamProps
     * @prop {any} teamId
     * @prop {TSHTeamInfo} team
     */

    /**
     * @typedef {Object} TeamState
     * @prop {TSHTeamInfo} team
     */


    const playerRefs = [];

    React.useImperativeHandle(ref, () => {
        return {
            submitTeamData: submitTeamData,
            getTeamDataFromForm: getTeamDataFromForm
        }
    },);

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

    const submitTeamData = () => {
        const teamData = getTeamDataFromForm();

        return Promise.all(
            Object.entries(teamData.player).map(([teamKey, playerData]) => {
                return fetch(
                    `http://${window.location.hostname}:5000`
                    + `/scoreboard1-update-team-${teamId}-${teamKey}`,
                    {
                        method: 'POST',
                        headers: {'content-type': 'application/json'},
                        body: JSON.stringify(playerData)
                    }
                )
                    .then((resp) => resp.text())
                    .then((d) => console.info(`Submitting team ${teamId} data: `, d))
                    .catch(console.error);
            })
        );
    }

    const idBase = `team-${teamId}`;

    const playerWidgets = playersInTeam().map(([teamKey, player]) => {
        if (!(teamKey in playerRefs)) {
            playerRefs[teamKey] = React.createRef();
        }

        return (
            <Player
                key={`${idBase}${String(player.id)}${player.name}`}
                ref={playerRefs[teamKey]}
                teamId={teamId}
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
        <Stack gap={2} padding={1}>
            {playerWidgets}
        </Stack>
    </Paper>
});

