import "../App.css";
import {darkTheme} from "../themes";
import i18n from "../i18n/config";
import {
    Paper, Stack
} from "@mui/material";
import React from "react";
import {Box} from "@mui/system";
import { io } from 'socket.io-client';
import imm_update from 'immutability-helper';

import './backendDataTypes';
import CurrentSet from "./CurrentSet";
import UpcomingSets from "./UpcomingSets";
import {TSHStateContext, TSHCharacterContext, TSHPlayerDBContext} from "./Contexts";
import {Header} from "./Header";


/**
 *
 * @param inputStr
 * @returns {string[]}
 */
function getKeysFromPyDeepDiffStr(inputStr) {
    const r = new RegExp(/\[([^[\]]*)]/g)
    const m = inputStr.matchAll(r)
    const vals = m
        .toArray()
        .map(
            o => o[1]
                .replaceAll(/['"]/g, "")
        );
    return vals;
}

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
            console.log("TSH state received ", data);
            setTshState(data);
        });

        socket.on("program_state_update", data => {
            console.log("TSH state update received", data);
            setTshState((prevState) => {
                const query = {};
                for (
                    let diffOperation of
                        [
                        'values_changed',
                        'dictionary_item_added',
                        'dictionary_item_removed'
                        ]
                    )
                {
                    if (!data[diffOperation]) {
                        continue;
                    }

                    for (let dataKeyStr in data[diffOperation]) {
                        const pathPieces = getKeysFromPyDeepDiffStr(dataKeyStr);
                        const lp = pathPieces[pathPieces.length-1];
                        let queryInner = {};
                        switch(diffOperation) {
                            case 'values_changed':
                                // _.set(newState, pathPieces, data[diffOperation][dataKeyStr]['new_value'])
                                queryInner = {"$set": data[diffOperation][dataKeyStr]['new_value']}
                                break;
                            case 'dictionary_item_added':
                                // _.set(newState, pathPieces, data[diffOperation][dataKeyStr])
                                queryInner = {"$set": data[diffOperation][dataKeyStr]}
                                break;
                            case 'dictionary_item_removed':
                                queryInner = {"$unset": [lp]}
                                // _.unset(newState, pathPieces)
                                break;
                        }

                        let currentQueryObj = query;
                        for (let i = 0; i < pathPieces.length; i += 1) {
                            if (!currentQueryObj[pathPieces[i]]) {
                                currentQueryObj[pathPieces[i]] = {};
                            }

                            if (i === pathPieces.length-1 && diffOperation === 'dictionary_item_removed') {
                                if (currentQueryObj.hasOwnProperty("$unset")) {
                                    currentQueryObj['$unset'].push(lp)
                                } else {
                                    currentQueryObj['$unset'] = queryInner['$unset'];
                                }
                                break;
                            }

                            currentQueryObj = currentQueryObj[pathPieces[i]];
                        }
                        if (diffOperation !== 'dictionary_item_removed') {
                            currentQueryObj['$set'] = queryInner['$set'];
                        }
                    }
                }
                console.log("Updating TSH state with query: ", query);
                return imm_update(prevState, query)
            });
        });

        socket.on("playerdb", data => {
            console.log("Player data received", data);
            setPlayerDb(data);
        })

        socket.on("characters", data => {
            console.log("Character data received", data);

            // We need our character list to be keyed by the en_name, because things like player mains are set
            // to the english name instead the localized name. We won't be able to do lookups if we don't
            // rearrange it like this.
            const enChars = {};
            Object.values(data).forEach((/** TSHCharacterBase */ char) => {
                enChars[char.en_name] = char;
            });
            console.log("Character data set", enChars);
            setCharacters(enChars);
        })

        socket.on("disconnect", () => {
            console.log("SocketIO disconnected.")
            socket.connect();
        });

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
    }, []); // eslint-disable-line react-hooks/exhaustive-deps
    // Adding the deps suggested above will actually break things... we
    // want this to only run once when the component is loaded.

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
            <>
                <Header/>
                <Box
                    paddingX={2}
                    paddingY={2}
                >
                    <Stack gap={4} marginBottom={24}>
                        <CurrentSet/>
                        <UpcomingSets onSelectedSetChanged={() => {setLoadingStatus({isLoading: true, connectionError: false})}}/>
                    </Stack>
                </Box>
            </>
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
