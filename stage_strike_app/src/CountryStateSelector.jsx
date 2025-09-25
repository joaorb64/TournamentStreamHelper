import TextField from "./ScoreboardPage/TextField";
import i18n from "./i18n/config";
import React, {useContext, useEffect, useState} from "react";
import {TSHCountriesContext} from "./ScoreboardPage/Contexts";
import {Autocomplete, AutocompleteValue, createFilterOptions} from "@mui/material";
import {BACKEND_PORT} from "./env";

/**
 * @param {?string} countryCode
 * @param {?string} stateCode
 * @param {(val: AutocompleteValue<string, false, false, true>)=> any} onChange
 * @param props
 * @returns {Element}
 */
export function CountryStateSelector({
                                    countryCode,
                                    onChange,
                                    ...props
                                }) {
    const isValidCountryCode = (countryCode !== "" && !!countryCode);
    const [stateData, setStateData] = useState({
        states: {},
        isLoading: true
    });

    useEffect(() => {
        if (isValidCountryCode) {
            fetch(`http://${window.location.hostname}:${BACKEND_PORT}/states?countryCode=${countryCode}`)
                .then(d => d.json())
                .then(j => setStateData({
                    states: Object.entries(j).reduce((acc, st) => {acc[st.name] = st; return acc}, {}),
                    isLoading: false
                }))
                .catch(e => {
                    console.warn(`Failed to load autocomplete state data for country code ${countryCode}`, e);
                    setStateData({states: {}, isLoading: false})
                });
        }

    }, [countryCode, isValidCountryCode]);

    return <Autocomplete
        freeSolo
        disabled={countryCode === "" || !countryCode || stateData.isLoading}
        filterOptions={(options, state) => {
            if (state.inputValue.length < 2) {
                return [];
            }

            return createFilterOptions({
                limit: 8,
            })(options, state);
        }}
        renderOption={(_props, option, _) => {
            const {key, ...rest} = _props;
            let stateAsset = stateData[option]?.asset;
            if (stateAsset[0] === ".") {
                stateAsset = stateAsset.slice(1);
            }

            return (
                <li key={key} {...rest}>
                    <img alt="State flag" loading={"lazy"} src={`http://${window.location.hostname}:${BACKEND_PORT}${stateAsset}`} width={32} />
                    <span style={{marginLeft: '16px'}}>
                        {[option]?.name ?? option}
                    </span>
                </li>
            )
        }}
        renderInput={(params) => {
            return <div>
                <TextField
                    {...params}
                    label={i18n.t("state")}
                />
            </div>
        }}
        value={countryCode}
        options={Object.keys(stateData.states)}
        onChange={(ev, val) => onChange(val)}
        getOptionLabel={(opt) => (stateData[opt]?.name ?? opt)}
        {...props}
    />
}
