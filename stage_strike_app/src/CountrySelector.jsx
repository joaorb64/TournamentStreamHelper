import TextField from "./ScoreboardPage/TextField";
import i18n from "./i18n/config";
import React, {useContext} from "react";
import {TSHCountriesContext} from "./ScoreboardPage/Contexts";
import {Autocomplete, AutocompleteValue, createFilterOptions} from "@mui/material";
import {BACKEND_PORT} from "./env";

/**
 * @param {?string} countryCode
 * @param {(val: AutocompleteValue<string, false, false, true>)=> any} onChange
 * @param props
 * @returns {Element}
 */
export function CountrySelector({
    countryCode,
    onChange,
    ...props
}) {
    const countries = useContext(TSHCountriesContext);

    return <Autocomplete
        freeSolo
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
            return (
                <li key={key} {...rest}>
                    <img alt="Country flag" loading={"lazy"} src={`http://${window.location.hostname}:${BACKEND_PORT}/assets/country_flag/${option?.toLowerCase()}.png`} width={32} />
                    <span style={{marginLeft: '16px'}}>
                        {countries[option]?.name ?? option}
                    </span>
                </li>
            )
        }}
        renderInput={(params) => {
            return <div>
                <TextField
                    {...params}
                    label={i18n.t("country")}
                />
            </div>
        }}
        value={countryCode}
        options={Object.keys(countries)}
        onChange={(ev, val) => onChange(val)}
        getOptionLabel={(opt) => (countries[opt]?.name ?? opt)}
        {...props}
    />
}
