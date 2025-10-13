import "../App.css";
import {darkTheme} from "../themes";
import i18n from "../i18n/config";
import {
    Paper, Stack
} from "@mui/material";
import React from "react";
import {Box} from "@mui/system";
import { io } from 'socket.io-client';

import '../backendDataTypes.ts';
import CurrentSet from "./CurrentSet";
import UpcomingSets from "./UpcomingSets";
import {Header} from "./Header";
import {tshStore, ReduxState} from "../redux/store"
import {useDispatch, useSelector} from "react-redux";
import {tshStateSlice} from "../redux/tshState";
import websocketInit from "./websocketInit";

/**
 * Main page for the scoreboard. This whole contraption is powered by TSH's python-side
 * program state. In order to do that, we subscribe to updates that get sent out and update
 * our state piecemeal. Each update has a number so that we can tell if our updates are stale
 * or out of order and request a full state send-over.
 */
export default function ScoreboardPage(props: any) {
    const dispatch = useDispatch();
    const {loading, errored} = useSelector((state: ReduxState) => ({
        loading: (state.tshState.initializing
            || state.tshCharacters.initializing
            || state.tshPlayers.initializing),
        errored: state.websocketInfo.status === "errored",
    }));

    React.useEffect(() => {
        (window as any).title = `TSH ${i18n.t("scoreboard")}`;
        websocketInit();
        const intervalId = setInterval(() => {
            tshStore.dispatch(tshStateSlice.actions.applySavedDeltas())
        }, 1000);
        return () => clearInterval(intervalId);
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

    const onSelectedSetChanged = React.useCallback(() => {
        dispatch(tshStateSlice.actions.loadingNewData({}));
    }, []);

    if (errored) {
        body = connectionError;
    } else if (loading) {
        body = loadingEl;
    } else {
        body = (
            // Extra margin at the bottom allows for mobile users to see the bottom of the page better.
            <>
                <Header/>
                <Box
                    paddingX={2}
                    paddingY={2}
                >
                    <Stack gap={4} marginBottom={24}>
                        <CurrentSet/>
                        <UpcomingSets onSelectedSetChanged={onSelectedSetChanged}/>
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
