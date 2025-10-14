import {
    tshCharactersSlice,
    tshCountriesSlice,
    tshGamesSlice,
    tshPlayersSlice,
    tshStateSlice,
    websocketInfoSlice
} from "../redux/tshState";
import { tshStore } from "../redux/store";
import socketConnection from "../websocketConnection";
import {BACKEND_PORT} from "../env";

let initialized = false;

export default function websocketInit() {
    if (initialized) {
        return;
    }

    initialized = true;
    const socket = socketConnection.instance();

    socket.on("connect", () => {
        console.log("SocketIO connection established.");
        tshStore.dispatch(websocketInfoSlice.actions.setStatus("connected"));
        socket.emit("playerdb", {}, () => {
            console.log("TSH acked player db request")
        });
        socket.emit("characters", {}, () => {
            console.log("TSH acked characters request")
        });
        socket.emit("games", {}, () => {
            console.log("TSH acked games request")
        });

        loadCountriesFile();
    });

    socket.on("program_state", data => {
        console.log("TSH state received ", data);
        tshStore.dispatch(tshStateSlice.actions.overwrite(data));
    });

    socket.on("games", data => {
        console.log("TSH game info received ", data);
        tshStore.dispatch(tshGamesSlice.actions.overwrite(data));
    })

    socket.on("countries", data => {
        console.log("TSH countries info received.")
        tshStore.dispatch(tshCountriesSlice.actions.overwrite(data));

    });

    socket.on("program_state_update", deltaMessage => {
        console.log("TSH state update received", deltaMessage);
        tshStore.dispatch(tshStateSlice.actions.addDeltas(deltaMessage));
    });

    socket.on("playerdb", data => {
        console.log("Player data received", data);
        tshStore.dispatch(tshPlayersSlice.actions.overwrite(data));
    })

    socket.on("characters", data => {
        console.log("Character data received", data);
        tshStore.dispatch(tshCharactersSlice.actions.overwrite(data));
    })

    socket.on("disconnect", () => {
        console.log("SocketIO disconnected.")
        tshStore.dispatch(websocketInfoSlice.actions.setStatus("disconnected"));
        socket.connect();
    });

    socket.on('error', (err) => {
        console.log(err);
        tshStore.dispatch(websocketInfoSlice.actions.setStatus("errored"));
    });

    // This can't be set up twice because of the initialization guard at the top of the function.
    setInterval(() => {
        const state = tshStore.getState();
        if (state.websocketInfo.status === "connected" && state.tshState?.stateDeltas.length > 0) {
            tshStore.dispatch(tshStateSlice.actions.applySavedDeltas());
        }
    }, 1000);
}

// Todo, maybe move this to a thunk or something.
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
        tshStore.dispatch(tshCountriesSlice.actions.overwrite(json));
    }).catch((e) => {
        console.error("Failed to request countries file", e);
        tshStore.dispatch(tshCountriesSlice.actions.overwrite({}));
    });
}

