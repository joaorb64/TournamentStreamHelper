import {createSlice, PayloadAction} from "@reduxjs/toolkit";


export const selectedScoreboardSlice = createSlice({
    name: 'uiState',
    initialState: {
        value: 1
    },
    reducers: {
        setSelectedScoreboard(state, action: PayloadAction<number>) {
            state.value = action.payload;
        }
    },
});
