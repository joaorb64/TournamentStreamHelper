import {Action, createSlice, PayloadAction} from '@reduxjs/toolkit'
import {applyDeltas} from "../stateDelta";
import {TSHState} from "../backendDataTypes";

type Delta = any;

export const tshStateSlice = createSlice({
    name: 'tshState',
    initialState: {
        tshState: {} as TSHState,
        deltas: [] as any[],
    },
    reducers: {
        applyDiff(state, action: Action) {
            let sortedDeltas = state.deltas.toSorted((a, b) => a.deltaIdx - b.deltaIdx);
            // const staleDeltas = sortedDeltas.filter((d) => d.deltaIdx < maxAppliedDeltaIdx);
            // sortedDeltas = sortedDeltas.filter((d) => d.deltaIdx >= maxAppliedDeltaIdx);

            applyDeltas(state.tshState, sortedDeltas);
            state.deltas = [];
        },

        addDeltas(state, action: PayloadAction<Delta[]>){
            for (let d of action.payload) {
                state.deltas.push(d);
            }
        },

        overwrite(state, action: PayloadAction<TSHState>) {
            state.tshState = action.payload;
        }
    }
})


export const {applyDiff, addDeltas, overwrite} = tshStateSlice.actions;
export default tshStateSlice.reducer;