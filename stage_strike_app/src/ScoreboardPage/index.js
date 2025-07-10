import "../App.css";
import {darkTheme} from "../themes";
import i18n from "../i18n/config";
import {
    Paper, Stack
} from "@mui/material";
import React from "react";
import {Box} from "@mui/system";
import './backendDataTypes';
import CurrentSet from "./CurrentSet";
import UpcomingSets from "./UpcomingSets";


export default class ScoreboardPage extends React.Component {
    constructor(props) {
        super(props);
        this.currentSetDisplayRef = React.createRef();
        this.state = {
            connectionError: false,
            isLoading: true,
            currentSetExpanded: true,
            characters: {}
        }
    }

    componentDidMount = () => {
        window.title = `TSH ${i18n.t("scoreboard")}`;

        fetch("http://" + window.location.hostname + `:5000/characters`)
            .then((res) => res.json())
            .then((data) => {
                this.setState({
                    isLoading: false,
                    connectionError: false,
                    characters: data
                });
            })
            .catch((e) => {
                console.error(e);
                this.setState({
                    ...this.state,
                    isLoading: false,
                    connectionError: true
                });
            });
    }

    onSelectedSetChanged = (setId) => {
        const fetchScore = this.currentSetDisplayRef.current?.FetchScore;
        if (fetchScore !== null && fetchScore !== undefined) {
            setTimeout(fetchScore, 500, setId)
        }
    }

    render = () => {
        let body;
        if (!!this.state.connectionError) {
            body = (
                <Paper elevation={2} sx={{padding: '8px'}}>
                    <div>{i18n.t("failed_to_connect")}</div>
                </Paper>
            );
        } else if (!!this.state.isLoading) {
            body = (
                <Paper elevation={2} sx={{padding: '8px'}}>
                    <div>{i18n.t("loading")}</div>
                </Paper>
            );
        } else {
            body = (
                // Extra margin at the bottom allows for mobile users to see the bottom of the page better.
                <Stack gap={4} marginBottom={24}>
                    <CurrentSet ref={this.currentSetDisplayRef} characters={this.state.characters} />
                    <UpcomingSets onSelectedSetChanged={this.onSelectedSetChanged}/>
                </Stack>
            )
        }

        return (
            <Box
                style={{
                    display: "flex",
                    flexDirection: "column",
                    height: "100vh",
                    gap: darkTheme.spacing(2),
                }}
                paddingY={2}
                paddingX={2}
                sx={{overflow: "auto !important"}}
            >
                {body}
            </Box>
        )
    }
}
