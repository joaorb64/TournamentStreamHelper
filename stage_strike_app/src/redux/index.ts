import { createSlice, configureStore } from '@reduxjs/toolkit'
import {tshStateSlice} from './tshState';

export const tshStore = configureStore({
    reducer: tshStateSlice.reducer
});



/*
export const { incremented, decremented } = counterSlice.actions

// Can still subscribe to the store
store.subscribe(() => console.log(store.getState()))

// Still pass action objects to `dispatch`, but they're created for us
store.dispatch(incremented())
// {value: 1}
store.dispatch(incremented())
// {value: 2}
store.dispatch(decremented())
// {value: 1}
 */