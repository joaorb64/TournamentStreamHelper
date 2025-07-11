import React from "react";
import {Paper, Stack} from "@mui/material";
import Player from "./Player";

export default class Team extends React.Component {
    /**
     * @typedef {Object} TeamProps
     * @prop {any} teamId
     * @prop {TSHTeamInfo} team
     * @prop {TSHCharacters} characters
     */

    /**
     * @typedef {Object} TeamState
     * @prop {TSHTeamInfo} team
     */

    /** @type {TeamProps} */ props;
    constructor(/** TeamProps */ props) {
        super(props);

        this.playerRefs = [];
        this.props = props;
    }

    /** @returns {[any, TSHPlayerInfo]} */
    playersInTeam = () => {
        return Object.keys(this.props.team.player).sort().map(k => [k, this.props.team.player[k]]);
    }

    getTeamDataFromForm = () => {
        /** @type TSHTeamInfo */ const rval = JSON.parse(JSON.stringify(this.props.team));
        for (const teamKey in this.playerRefs) {
            /** @type Player */ const widget = this.playerRefs[teamKey].current;
            rval.player[teamKey] = widget.getModifiedPlayerData();
        }
        return rval;
    }

    submitTeamData = () => {
        const teamData = this.getTeamDataFromForm();

        return Promise.all(
            Object.entries(teamData.player).map(([teamKey, playerData]) => {
                return fetch(
                    `http://${window.location.hostname}:5000`
                    + `/scoreboard1-update-team-${this.props.teamId}-${teamKey}`,
                    {
                        method: 'POST',
                        headers: {'content-type': 'application/json'},
                        body: JSON.stringify(playerData)
                    }
                )
                    .then((resp) => resp.text())
                    .then((d) => console.info(`Submitting team ${this.props.teamId} data: `, d))
                    .catch(console.error);
            })
        );
    }

    render = () => {
        const idBase = `team-${this.props.teamId}`;

        const playerWidgets = this.playersInTeam().map(([teamKey, player]) => {
            if (!(teamKey in this.playerRefs)) {
                this.playerRefs[teamKey] = React.createRef();
            }

            return (
                <Player
                    key={`${idBase}${String(player.id)}`}
                    ref={this.playerRefs[teamKey]}
                    teamId={this.props.teamId}
                    player={player}
                    characters={this.props.characters}/>
            );
        });

        let borderStyle = {};
        if (this.props.team.color) {
            borderStyle = {
                borderTop: `solid 4px ${this.props.team.color}`
            };
        }

        return <Paper padding={2} elevation={3} sx={borderStyle}>
            <Stack gap={2} padding={1}>
                {playerWidgets}
            </Stack>
        </Paper>
    }
}

