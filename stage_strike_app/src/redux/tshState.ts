import {Action, createSlice, PayloadAction} from '@reduxjs/toolkit'
import {applyDeltas, combineDeltas} from "../stateDelta";
import {TSHCharacterDb, TSHCountryDb, TSHCountryInfo, TSHGamesDb, TSHPlayerDb, TSHState} from "../backendDataTypes";
import websocketConnection from "../websocketConnection";

export type Delta = any;
export type ReceivedDeltas = {
    deltaIdx: number;
    delta: Delta[];
};

export type TSHStateMessage = {
    state: TSHState;
    deltaIdx: number;
}

export type WebsocketStatus =
    'initial'
    | 'connected'
    | 'errored'
    | 'disconnected';

export const websocketInfoSlice = createSlice({
    name: 'websocketInfo',
    initialState: {
        status: 'initial' as WebsocketStatus,
        errorMessage: null as (null | string)
    },
    reducers: {
        setStatus(state, action: PayloadAction<WebsocketStatus>) {
            state.status = action.payload;
        }
    }
});

export const tshStateSlice = createSlice({
    name: 'tshState',
    initialState: {
        tshState: {} as TSHState,
        stateDeltas: [] as any[],
        maxAppliedDeltaIdx: -1,
        initializing: true,
    },
    reducers: {
        applySavedDeltas(state, action: Action) {
            let sortedDeltas = state.stateDeltas.toSorted((a, b) => a.deltaIdx - b.deltaIdx);
            const staleDeltas = sortedDeltas.filter((d) => d.deltaIdx < state.maxAppliedDeltaIdx);
            sortedDeltas = sortedDeltas.filter((d) => d.deltaIdx >= state.maxAppliedDeltaIdx);

            if (staleDeltas.length > 0) {
                console.warn("Skipping applying stale deltas...", staleDeltas);
            }

            if (sortedDeltas.length > 0) {
                console.log("Applying deltas: ", combineDeltas(sortedDeltas.map(d => d.delta)));
                applyDeltas(state, sortedDeltas.map((d) => d.delta));
                state.maxAppliedDeltaIdx = sortedDeltas[sortedDeltas.length-1].deltaIdx;
                state.stateDeltas = [];
                state.initializing = false;
            }
        },

        addDeltas(state, action: PayloadAction<ReceivedDeltas>){
            if (action.payload.deltaIdx < state.maxAppliedDeltaIdx) {
                console.warn("Received out of order delta! Requesting new full state.");
                websocketConnection.instance().emit("program_state", {});
            }

            state.maxAppliedDeltaIdx = Math.max(action.payload.deltaIdx, state.maxAppliedDeltaIdx);

            for (let d of action.payload.delta) {
                state.stateDeltas.push(d);
            }
        },

        overwrite(state, action: PayloadAction<TSHStateMessage>) {
            state.tshState = action.payload.state;
            state.maxAppliedDeltaIdx = Math.max(action.payload.deltaIdx, state.maxAppliedDeltaIdx);
            state.stateDeltas = [];
            state.initializing = false;
        },

        loadingNewData(state, action) {
            state.initializing = true;
        }
    }
})

export const tshPlayersSlice = createSlice({
    name: 'tshPlayers',
    initialState: {
        players: {} as TSHPlayerDb,
        initializing: true,
    },
    reducers: {
        overwrite(state, action: PayloadAction<TSHPlayerDb>) {
            state.players = action.payload;
            state.initializing = false;
        }
    }
});

export const tshCharactersSlice = createSlice({
    name: 'tshCharacters',
    initialState: {
        characters: {} as TSHCharacterDb,
        initializing: true,
    },
    reducers: {
        overwrite(state, action: PayloadAction<TSHCharacterDb>) {
            // We need our character list to be keyed by the en_name, because things like player mains are set
            // to the english name instead the localized name. We won't be able to do lookups if we don't
            // rearrange it like this.
            const enChars: TSHCharacterDb = {};
            Object.values(action.payload).forEach((/** TSHCharacterBase */ char) => {
                enChars[char.en_name] = char;
            });
            console.log("Character data set", enChars);
            state.characters = enChars;
            state.initializing = false;
        }
    }
});

export const tshGamesSlice = createSlice({
    name: 'tshGames',
    initialState: {
        value: {} as TSHGamesDb,
        initializing: true
    },
    reducers: {
        overwrite(state, action: PayloadAction<TSHGamesDb>) {
            state.value = action.payload;
            for (let k in state.value) {
                state.value[k].codename = k;
            }
            state.initializing = false;
        }
    }
});

export const tshCountriesSlice = createSlice({
    name: 'tshCountires',
    initialState: {
        value: {} as TSHCountryDb,
        initializing: true,
    },
    reducers: {
        overwrite(state, action: PayloadAction<TSHCountryDb>) {
            state.value = action.payload;
            state.initializing = false;
        }
    }
})
