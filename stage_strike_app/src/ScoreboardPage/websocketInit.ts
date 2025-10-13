import {tshCharactersSlice, tshPlayersSlice, tshStateSlice, websocketInfoSlice} from "../redux/tshState";
import { tshStore } from "../redux/store";
import socketConnection from "../websocketConnection";

export default function websocketInit() {
    const socket = socketConnection.instance();

    socket.on("connect", () => {
        console.log("SocketIO connection established.");
        socket.emit("playerdb", {}, () => {
            console.log("TSH acked player db request")
        });
        socket.emit("characters", {}, () => {
            console.log("TSH acked characters request")
        });
    });

    socket.on("program_state", data => {
        console.log("TSH state received ", data);
        tshStore.dispatch(tshStateSlice.actions.overwrite(data));
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
    })
}