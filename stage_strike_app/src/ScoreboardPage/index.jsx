import "../App.css";
import i18n from "../i18n/config";
import {
    Paper, Stack, Tabs, Tab
} from "@mui/material";
import React from "react";
import {Box} from "@mui/system";
import { io } from 'socket.io-client';

import './backendDataTypes';
import CurrentSet from "./CurrentSet";
import UpcomingSets from "./UpcomingSets";
import {TSHStateContext, TSHCharacterContext, TSHPlayerDBContext, TSHCountriesContext} from "./Contexts";
import {Header} from "./Header";
import {produce as immer_produce} from "immer";
import {applyDeltas, combineDeltas} from "../stateDelta";
import {BACKEND_PORT} from "../env";


/**
 * Main page for the scoreboard. This whole contraption is powered by TSH's python-side
 * program state. In order to do that, we subscribe to updates that get sent out and update
 * our state piecemeal. Each update has a number so that we can tell if our updates are stale
 * or out of order and request a full state send-over.
 */
export default function ScoreboardPage(props) {
    const [tshState, setTshState] = React.useState(null);
    const [receivedDeltas, setReceivedDeltas] = React.useState([]);
    const [maxAppliedDeltaIdx, setMaxAppliedDeltaIdx] = React.useState(-1);
    const [loadingStatus, setLoadingStatus] = React.useState({
        connectionError: false,
        isLoading: true,
    });
    const [characters, setCharacters] = React.useState(null);
    const [playerDb, setPlayerDb] = React.useState(null);
    const [countriesData, setCountriesData] = React.useState({
        countries: {},
        isLoaded: false,
    });

    const [selectedScoreboard, setSelectedScoreboard] = React.useState(-1);

    let socket;

    function connectToSocketIO() {
        socket = io(`ws://${window.location.hostname}:${BACKEND_PORT}/`, {
            transports: ['websocket', 'webtransport'],
            timeout: 5000,
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
            setMaxAppliedDeltaIdx(data['delta_index'])
            setReceivedDeltas(receivedDeltas.filter(d => d.deltaIdx <= data['delta_index']))
            setTshState(data['state']);

            if (selectedScoreboard === -1) {
                setSelectedScoreboard(scoreboardKeys(data['state'])?.[0] ?? 1)
            }
        });

        socket.on("program_state_update", deltaMessage => {
            console.log("TSH state update received", deltaMessage);
            const deltaIdx = deltaMessage['delta_index'];
            const delta = deltaMessage['delta'];
            if (deltaIdx < maxAppliedDeltaIdx) {
                console.warn("Received out of order delta! Requesting new full state.");
                socket.emit("program_state", {});
            } else {
                setReceivedDeltas((prevState) => immer_produce(prevState, (draft) => {
                    // Each delta that we receive is an array of delta objects.
                    for (let subdelta of delta) {
                        draft.push({deltaIdx, delta: subdelta});
                    }
                }));
            }
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

    const loadCountriesFile = () => {
        fetch(
            `http://${window.location.hostname}:${BACKEND_PORT}/assets/data_countries.json`
        ).then(
            (resp) => resp.json()
        ).then((json) => {
             for (let key in json) {
                 json[key].code = key;
             }

            console.log("Loaded countries json file", json);
             setCountriesData({
                 countries: json,
                 isLoaded: true
             });
        }).catch((e) => {
            console.error("Failed to request countries file", e);
            setCountriesData({
                countries: {},
                isLoaded: true
            });
        });
    }

    React.useEffect(() => {
        const intervalId = setInterval(() => {
            let sortedDeltas = receivedDeltas.toSorted((a, b) => a.deltaIdx - b.deltaIdx);
            const staleDeltas = sortedDeltas.filter((d) => d.deltaIdx < maxAppliedDeltaIdx);
            sortedDeltas = sortedDeltas.filter((d) => d.deltaIdx >= maxAppliedDeltaIdx);
            if (staleDeltas.length > 0) {
                console.warn("Skipping applying stale deltas...", staleDeltas);
            }
            if (sortedDeltas.length > 0) {
                console.log("Applying deltas: ", combineDeltas(sortedDeltas.map(d => d.delta)));
                setTshState((prevState) => {
                    const newState = immer_produce(prevState, (draftState) => {
                        try {
                            applyDeltas(draftState, sortedDeltas.map((d) => d.delta));
                        } catch (e) {
                            console.warn("Could not apply deltas.", e);
                        }
                    });

                    return newState;
                });

                setMaxAppliedDeltaIdx(sortedDeltas[sortedDeltas.length-1].deltaIdx);
                setReceivedDeltas([]);
            }
        }, 1000);

        return () => clearInterval(intervalId);
    }, [receivedDeltas, maxAppliedDeltaIdx]);


    React.useEffect(() => {
        window.title = `TSH ${i18n.t("scoreboard")}`;
        connectToSocketIO();
        loadCountriesFile();
        return () => {
           socket.close();
        };
    }, []); // eslint-disable-line react-hooks/exhaustive-deps
    // Adding the deps suggested above will actually break things... we
    // want this to only run once when the component is loaded.

    let body;
    const connectionError = (
        <Paper key="connection_error" elevation={2} sx={{padding: '8px'}}>
            <div>{i18n.t("failed_to_connect")}</div>
        </Paper>
    );
    const loading = (
        <Paper key="loading" elevation={2} sx={{padding: '8px'}}>
            <div>{i18n.t("loading")}</div>
        </Paper>
    );

    const onSelectedSetChanged = React.useCallback(() => {
        setLoadingStatus({isLoading: true, connectionError: false})
    }, []);

    if (!!loadingStatus.connectionError) {
        body = connectionError;
    } else if (!tshState || !characters || !playerDb || !countriesData.isLoaded) {
        body = loading;
    } else {

        body = (
            // Extra margin at the bottom allows for mobile users to see the bottom of the page better.
            <>
                <Header/>
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
                                    onChange={(event, newValue) => setSelectedScoreboard(newValue)}
                                    value={selectedScoreboard}
                                >
                                    {
                                        scoreboardKeys(tshState).map(sbName =>
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
            }}
            sx={{overflow: "auto !important"}}
        >
            <TSHStateContext.Provider value={tshState}>
                <TSHCharacterContext.Provider value={characters}>
                    <TSHPlayerDBContext.Provider value={playerDb}>
                        <TSHCountriesContext.Provider value={countriesData.countries}>
                            {body}
                        </TSHCountriesContext.Provider>
                    </TSHPlayerDBContext.Provider>
                </TSHCharacterContext.Provider>
            </TSHStateContext.Provider>
        </Box>
    )
}

/** @returns {number[]} */
const scoreboardKeys = (tshState) => {
    if (tshState.score) {
        return Object.keys(tshState.score)
            .filter(k => k.match(/^\d+$/))
            .map(k => Number.parseInt(k));
    } else {
        return [];
    }
}
