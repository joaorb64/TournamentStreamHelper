import "../App.css";
import {darkTheme} from "../themes";
import i18n from "../i18n/config";
import {
    Paper, Stack
} from "@mui/material";
import React from "react";
import {Box} from "@mui/system";
import { io } from 'socket.io-client';

import './backendDataTypes';
import CurrentSet from "./CurrentSet";
import UpcomingSets from "./UpcomingSets";
import {TSHStateContext, TSHCharacterContext, TSHPlayerDBContext} from "./Contexts";


export default function ScoreboardPage(props) {
    const [tshState, setTshState] = React.useState(null);
    const [loadingStatus, setLoadingStatus] = React.useState({
        connectionError: false,
        isLoading: true,
    });
    const [characters, setCharacters] = React.useState(null);
    const [playerDb, setPlayerDb] = React.useState(null);

    let socket;

    function connectToSocketIO() {
        socket = io(`ws://${window.location.hostname}:5000/`, {
            transports: ['websocket', 'webtransport'],
            timeout: 500,
            reconnectionDelay: 500,
            reconnectionDelayMax: 1500
        });

        socket.on("connect", () => {
            console.log("SocketIO connection established.");
            socket.emit("playerdb", {}, () => {console.log("TSH acked player db request")});
            socket.emit("characters", {}, () => {console.log("TSH acked characters request")});
        });

        socket.on("program_state", data => {
            console.log("TSH state update received ", data);
            setTshState(data);
        })

        socket.on("playerdb", data => {
            console.log("Player data received", data);
            setPlayerDb(data);
        })

        socket.on("characters", data => {
            console.log("Character data received", data);
            setCharacters(data);
        })

        socket.on("disconnect", () => {console.log("SocketIO disconnected.")});
        socket.on('error', (err) => {
            console.log(err);
            setLoadingStatus({connectionError: true})
        })
    }

    React.useEffect(() => {
        window.title = `TSH ${i18n.t("scoreboard")}`;
        connectToSocketIO();
        return () => {
           socket.close();
        };
    }, []);

    let body;
    if (!!loadingStatus.connectionError) {
        body = (
            <Paper elevation={2} sx={{padding: '8px'}}>
                <div>{i18n.t("failed_to_connect")}</div>
            </Paper>
        );
    } else if (tshState === null || characters === null || playerDb === null) {
        body = (
            <Paper elevation={2} sx={{padding: '8px'}}>
                <div>{i18n.t("loading")}</div>
            </Paper>
        );
    } else {
        body = (
            // Extra margin at the bottom allows for mobile users to see the bottom of the page better.
            <Stack gap={4} marginBottom={24}>
                    <CurrentSet/>
                    <UpcomingSets onSelectedSetChanged={() => {setLoadingStatus({isLoading: true, connectionError: false})}}/>
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
            <TSHStateContext.Provider value={tshState}>
                <TSHCharacterContext.Provider value={characters}>
                    <TSHPlayerDBContext.Provider value={playerDb}>
                        {body}
                    </TSHPlayerDBContext.Provider>
                </TSHCharacterContext.Provider>
            </TSHStateContext.Provider>
        </Box>
    );
}
