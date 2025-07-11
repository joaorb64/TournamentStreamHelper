import React from 'react';
import TextField from "./TextField";
import {Stack} from "@mui/material";
import i18n from "i18next";

/**
 * @typedef {object} SetScoreState
 * @prop {number} scoreLeft
 * @prop {number} scoreRight
 * @prop {boolean} isLoading
 * @prop {?number} bestOf
 * @prop {string} match
 * @prop {string} phase
 */

export default class SetScore extends React.Component {
    /** @type {SetScoreState} */
    state;

    /**
     * @param {TSHTeamInfo} props.leftTeam
     * @param {TSHTeamInfo} props.rightTeam
     * @param {number=} props.best_of
     * @param {string=} props.match
     * @param {string=} props.phase
     */
    constructor(props) {
        super(props);

        this.best_of = (
            (props.best_of !== undefined)
                ? props.best_of
                : null
        );

        this.leftTeam = props.leftTeam;
        this.rightTeam = props.rightTeam;
        this.state = {
            scoreLeft: props.leftTeam.score,
            scoreRight: props.rightTeam.score,
            match: props.match ?? "",
            phase: props.phase ?? "",
            bestOf: this.best_of
        };
    }

    /** @return {?number} */
    maxWins = () => {
        let bestOf = parseInt(this.state.bestOf);
        if (isNaN(bestOf) || isNaN(bestOf - 0)) {
            bestOf = null;
        }

        return bestOf
            ? (Math.floor(bestOf / 2) + 1)
            : null;
    }

    submitScore = () => {
        return (
            fetch(`http://${window.location.hostname}:5000/score`,
                {
                    method: 'POST',
                    headers: {'content-type': 'application/json'},
                    body: JSON.stringify({
                        team1score: Number.parseInt(this.state.scoreLeft),
                        team2score: Number.parseInt(this.state.scoreRight)
                    })
                })
                .then(resp => resp.text())
                .then((d) => console.log("Submit Score: ", d))
        );
    }

    submitSetInfo = () => {
        return (
            fetch(`http://${window.location.hostname}:5000/scoreboard1-set?` + new URLSearchParams({
                "best-of": this.state.bestOf,
                "phase": this.props.phase,
                "match": this.state.match,
            }).toString())
                .then(resp => resp.text())
                .then((d) => console.log("Submit set info: ", d))
        )
    }

    render = () => {
        const numInputStyles = {
            '& input': {
                width: 50,
                paddingX: '5px',
                textAlign: "center"
            }
        };

        return (
            <Stack gap={4} direction={"column"} alignItems={"center"}>
                <TextField
                    label={i18n.t("phase")}
                    value={this.state.phase}
                    variant={"outlined"}
                    onChange={(e) => {this.setState({...this.state, phase: e.target.value})}}
                />
                <TextField
                    label={i18n.t("match")}
                    value={this.state.match}
                    variant={"outlined"}
                    onChange={(e) => {this.setState({...this.state, match: e.target.value})}}
                />
                <TextField
                    type={"number"}
                    label={i18n.t("best_of", {value: ""})}
                    variant="outlined"
                    value={this.state.bestOf}
                    onChange={((e) => {this.setState({...this.state, bestOf: e.target.value})})}
                    inputProps={{
                        min: 0
                    }}
                />
                <Stack gap={2} direction={"row"} alignItems={"baseline"}>
                    <TextField
                        type={"number"}
                        variant="outlined"
                        value={this.state.scoreLeft}
                        onChange={((e) => {this.setState({...this.state, scoreLeft: e.target.value})})}
                        sx={numInputStyles}
                        inputProps={{
                            max: this.maxWins(),
                            min: 0
                        }}
                    />
                    <span>&nbsp;-&nbsp;</span>
                    <TextField
                        type={"number"}
                        variant="outlined"
                        value={this.state.scoreRight}
                        onChange={((e) => {this.setState({...this.state, scoreRight: e.target.value})})}
                        sx={numInputStyles}
                        inputProps={{
                            max: this.maxWins(),
                            min: 0
                        }}
                    />
                </Stack>
            </Stack>
        )
    }
}
