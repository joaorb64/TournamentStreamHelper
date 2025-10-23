import {Action, createSlice, PayloadAction, WritableDraft} from '@reduxjs/toolkit'
import {applyDeltas, combineDeltas} from "../stateDelta";
import websocketConnection from "../websocketConnection";
import {
    TSHCountryDb,
    TSHCharacterDb,
    TSHCharacterDbEntry,
    TSHPlayerDb,
    TSHState,
    TSHGamesDb, Delta
} from "../backendDataTypes";

export type ReceivedDeltas = {
    delta_index: number;
    delta: Delta[];
};

export type TSHStateMessage = {
    state: TSHState;
    delta_index: number;
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

export type TshStateReduxState = {
    tshState: TSHState;
    stateDeltas: ReceivedDeltas[];
    maxAppliedDeltaIdx: number;
    initializing: boolean;
};

export const tshStateSlice = createSlice({
    name: 'tshState',
    initialState: {
        tshState: {} as TSHState,
        stateDeltas: [],
        maxAppliedDeltaIdx: -1,
        initializing: true,
    } as TshStateReduxState,
    reducers: {
        applySavedDeltas(state: WritableDraft<TshStateReduxState>, action: Action) {
            let sortedDeltas = state.stateDeltas.toSorted((a, b) => a.delta_index - b.delta_index);
            const staleDeltas = sortedDeltas.filter((d) => d.delta_index < state.maxAppliedDeltaIdx);
            sortedDeltas = sortedDeltas.filter((d) => d.delta_index >= state.maxAppliedDeltaIdx);

            if (staleDeltas.length > 0) {
                console.warn("Skipping applying stale deltas...", staleDeltas);
            }

            if (sortedDeltas.length > 0) {
                for (let deltaSet of sortedDeltas) {
                    console.log("Applying deltas: ", combineDeltas(deltaSet.delta));
                    applyDeltas(state.tshState, deltaSet.delta);
                }
                state.maxAppliedDeltaIdx = sortedDeltas[sortedDeltas.length-1].delta_index;
            }

            state.initializing = false;
            state.stateDeltas = [];
        },

        addDeltas(state: TshStateReduxState, action: PayloadAction<ReceivedDeltas>){
            if (action.payload.delta_index < state.maxAppliedDeltaIdx) {
                console.warn("Received out of order delta! Requesting new full state.");
                websocketConnection.instance().emit("program_state", {});
            }

            state.stateDeltas.push(action.payload);
        },

        overwrite(state: TshStateReduxState, action: PayloadAction<TSHStateMessage>) {
            state.tshState = action.payload.state;
            state.maxAppliedDeltaIdx = Math.max(action.payload.delta_index, state.maxAppliedDeltaIdx);
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
            for (let k in state.players) {
                state.players[k].prefixed_tag = k;
            }
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
            Object.values(action.payload).forEach((char: TSHCharacterDbEntry) => {
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
    name: 'tshCountries',
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
});
