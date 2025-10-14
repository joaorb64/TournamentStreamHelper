import {configureStore, combineReducers, Action} from '@reduxjs/toolkit'
import {
    tshCharactersSlice,
    tshCountriesSlice,
    tshGamesSlice,
    tshPlayersSlice,
    tshStateSlice,
    websocketInfoSlice
} from './tshState';
import {selectedScoreboardSlice} from "./uiState";
import {produce} from "immer";

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
    devTools: {
        // Helps keep the devtools crispy.
        stateSanitizer: function<S>(state: S, index) {
            return produce(state, (ds: any) => {
                try {
                    ds.tshPlayers = `<${objLen(ds.tshPlayers.players)} players>`;
                    ds.tshCountries = `<${objLen(ds.tshCountries.value)} countries>`;
                    for (let k in ds.tshCharacters.characters) {
                        ds.tshCharacters.characters[k].skins = `<${objLen(ds.tshCharacters.characters[k].skins)} skins>`
                    }
                    ds.tshState.tshState.bracket = "omitted";
                    ds.tshState.tshState.notes = "omitted";
                    ds.tshState.tshState.player_list = "omitted";
                } catch {}
            });
        },
        predicate: function<S, A extends Action>(state: S, action: A) {
            return action.type !== 'tshState/maybeApplySavedDeltas';
        }
    },
});

const objLen = (o: any) => Object.keys(o).length;

export type TshStore = typeof tshStore;
export type ReduxState = ReturnType<TshStore['getState']>
export type ReduxDispatch = TshStore['dispatch'];
