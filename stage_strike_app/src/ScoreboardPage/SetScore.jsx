import React from 'react';
import TextField from "./TextField";
import {Stack} from "@mui/material";

/**
 * @typedef {object} SetScoreState
 * @prop {?TSHScoreInfo} score
 * @prop {boolean} isLoading
 */

export default class SetScore extends React.Component {
    /**
     * @param {TSHTeamInfo} props.leftTeam
     * @param {TSHTeamInfo} props.rightTeam
     * @param {number=} props.best_of
     */
    constructor(props) {
        super(props);

        this.best_of = (
            (props.best_of !== undefined)
                ? props.best_of
                : null
        );

        this.max_wins = this.best_of ?? (Math.floor(this.best_of / 2) + 1);

        this.leftTeam = props.leftTeam;
        this.rightTeam = props.rightTeam;
        this.state = {
            scoreLeft: props.leftTeam.score,
            scoreRight: props.rightTeam.score
        };
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
                .catch(console.error)
        );
    }

    render = () => {
        const numInputStyles = {
            '& input': {
                width: 50,
                paddingX: '5px',
                paddingY: '5px',
                textAlign: "center"
            }
        };

        return <Stack gap={2} direction={"row"} alignItems={"baseline"}>
            <TextField
                type={"number"}
                variant="outlined"
                value={this.state.scoreLeft}
                onChange={((e) => {this.setState({scoreLeft: e.target.value})})}
                sx={numInputStyles}
                max={this.max_wins}
            />
            <span>&nbsp;-&nbsp;</span>
            <TextField
                type={"number"}
                variant="outlined"
                value={this.state.scoreRight}
                onChange={((e) => {this.setState({scoreRight: e.target.value})})}
                sx={numInputStyles}
                max={this.max_wins}
            />
        </Stack>
    }
}
