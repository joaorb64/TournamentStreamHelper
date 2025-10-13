import {createSlice, configureStore, combineReducers} from '@reduxjs/toolkit'
import {
    tshCharactersSlice,
    tshCountriesSlice,
    tshGamesSlice,
    tshPlayersSlice,
    tshStateSlice,
    websocketInfoSlice
} from './tshState';
import {selectedScoreboardSlice} from "./uiState";

export const tshStore = configureStore({
    reducer: combineReducers({
        tshState: tshStateSlice.reducer,
        tshPlayers: tshPlayersSlice.reducer,
        tshCharacters: tshCharactersSlice.reducer,
        tshGames: tshGamesSlice.reducer,
        tshCountries: tshCountriesSlice.reducer,
        websocketInfo: websocketInfoSlice.reducer,
        selectedScoreboard: selectedScoreboardSlice.reducer,
    }),
});

export type TshStore = typeof tshStore;
export type ReduxState = ReturnType<TshStore['getState']>
export type ReduxDispatch = TshStore['dispatch'];
