import {io, Socket} from "socket.io-client";
import {BACKEND_PORT} from "./env";

export class SocketSingleton {
    _instance: null | Socket = null;

    instance(): Socket {
        if (this._instance == null) {
            this._instance = io(`ws://${window.location.hostname}:${BACKEND_PORT}/`, {
                transports: ['websocket', 'webtransport'],
                timeout: 5000,
                reconnectionDelay: 500,
                reconnectionDelayMax: 1500
            });
        }
        return this._instance;
    }
}

const socketHolder =  new SocketSingleton();

export default socketHolder;