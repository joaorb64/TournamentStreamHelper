import {createSlice, configureStore, combineReducers} from '@reduxjs/toolkit'
import {tshCharactersSlice, tshPlayersSlice, tshStateSlice, websocketInfoSlice} from './tshState';

export const tshStore = configureStore({
    reducer: combineReducers({
        tshState: tshStateSlice.reducer,
        tshPlayers: tshPlayersSlice.reducer,
        tshCharacters: tshCharactersSlice.reducer,
        websocketInfo: websocketInfoSlice.reducer,
    }),
});

export type TshStore = typeof tshStore;
export type ReduxState = ReturnType<TshStore['getState']>
export type ReduxDispatch = TshStore['dispatch'];
