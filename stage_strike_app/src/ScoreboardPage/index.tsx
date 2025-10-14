import "../App.css";
import {darkTheme} from "../themes";
import i18n from "../i18n/config";
import {
    Paper, Stack,
    Tab,
    Tabs
} from "@mui/material";
import React from "react";
import {Box} from "@mui/system";

import CurrentSet from "./CurrentSet";
import UpcomingSets from "./UpcomingSets";
import {Header} from "./Header";
import {tshStore, ReduxState} from "../redux/store"
import {shallowEqual, useDispatch, useSelector} from "react-redux";
import {tshStateSlice} from "../redux/tshState";
import websocketInit from "./websocketInit";
import websocketConnection from "../websocketConnection";
import {selectedScoreboardSlice} from "../redux/uiState";
import {TSHState} from "../backendDataTypes";

/**
 * Main page for the scoreboard. This whole contraption is powered by TSH's python-side
 * program state. In order to do that, we subscribe to updates that get sent out and update
 * our state piecemeal. Each update has a number so that we can tell if our updates are stale
 * or out of order and request a full state send-over.
 */
export default function ScoreboardPage(props: any) {
    const dispatch = useDispatch();
    const {loading, errored, selectedScoreboard, scoreboards} = useSelector((state: ReduxState) => ({
        loading: (
            state.tshState.initializing
            || state.tshCharacters.initializing
            || state.tshPlayers.initializing
            || state.tshGames.initializing
            || state.tshCountries.initializing
        ),
        errored: state.websocketInfo.status === "errored",
        scoreboards: state.tshState.tshState.score,
        selectedScoreboard: state.selectedScoreboard.value
    }), shallowEqual);

    React.useEffect(() => {
        document.title = `TSH ${i18n.t("scoreboard")}`;
        websocketInit();
    }, []);

    let body;
    const connectionError = (
        <Paper key="connection_error" elevation={2} sx={{padding: '8px'}}>
            <div>{i18n.t("failed_to_connect")}</div>
        </Paper>
    );
    const loadingEl = (
        <Paper key="loading" elevation={2} sx={{padding: '8px'}}>
            <div>{i18n.t("loading")}</div>
        </Paper>
    );

    const onSelectedSetChanged = () => {
        dispatch(tshStateSlice.actions.loadingNewData({}));
    };

    const onSelectedGameChanged= (newGame: string) => {
        websocketConnection.instance().emit('update_game', {codename: newGame});
    };

    if (errored) {
        body = connectionError;
    } else if (loading) {
        body = loadingEl;
    } else {
        body = (
            // Extra margin at the bottom allows for mobile users to see the bottom of the page better.
            <>
                <Header onSelectedGameChange={onSelectedGameChanged}/>
                <Box
                    paddingX={2}
                    paddingTop={1}
                    paddingBottom={2}
                >
                    <Stack gap={4} marginBottom={24}>
                        <Box>
                            <Box sx={{borderBottom: 1, borderColor: 'divider'}}>
                                <Tabs
                                    sx={{width: '100%'}}
                                    variant={"scrollable"}
                                    onChange={(event, newValue) => {
                                        tshStore.dispatch(selectedScoreboardSlice.actions.setSelectedScoreboard(newValue))
                                    }}
                                    value={selectedScoreboard}
                                >
                                    {
                                        scoreboardKeys(scoreboards).map(sbName =>
                                            <Tab key={sbName} value={sbName} label={`Scoreboard ${sbName}`} />)
                                    }
                                </Tabs>
                            </Box>
                            <div
                                role={"tabpanel"}
                                id={`scoreboards-tabpanel-${selectedScoreboard}`}
                                aria-labelledby={`scoreboards-tabpanel-${selectedScoreboard}`}
                            >
                                <CurrentSet scoreboardNumber={selectedScoreboard} />
                            </div>
                        </Box>
                        <UpcomingSets onSelectedSetChanged={onSelectedSetChanged} scoreboardNumber={selectedScoreboard}/>
                    </Stack>
                </Box>
            </>
        );
    }

    return (
        <Box
            style={{
                display: "flex",
                flexDirection: "column",
                height: "100vh",
                gap: darkTheme.spacing(2),
            }}
            sx={{overflow: "auto !important"}}
        >
            {body}
        </Box>
    )
}

const scoreboardKeys = (scoreboards: TSHState['score']) => {
    if (scoreboards) {
        return Object.keys(scoreboards)
            .filter(k => k.match(/^\d+$/))
            .map(k => Number.parseInt(k));
    } else {
        return [];
    }
}
