import { createContext } from 'react';
import './backendDataTypes';

export const /** @type {Context<TSHState>} */ TSHStateContext = createContext(null);
export const /** @type {Context<TSHCharacterDb>} */ TSHCharacterContext = createContext(null);
export const /** @type {Context<TSHPlayerDb>} */ TSHPlayerDBContext =  createContext(null);
export const /** @type {Context<TSHCountries>} */ TSHCountriesContext =  createContext({});

