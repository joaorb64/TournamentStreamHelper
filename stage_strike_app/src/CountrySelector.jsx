import TextField from "./ScoreboardPage/TextField";
import i18n from "./i18n/config";
import React from "react";
import {Autocomplete, createFilterOptions, InputAdornment} from "@mui/material";
import {BACKEND_PORT, inlineFlagWidth} from "./env";
import {useSelector} from "react-redux";

/**
 * @param {?string} countryCode
 * @param {(val: string)=> any} onChange
 * @param props
 * @returns {Element}
 */
export function CountrySelector({
    value,
    onChange,
    ...props
}) {
    const countries = useSelector(state => state.tshCountries.value);

    const country = countries[value];
    const getCountryFlagAsset = (inp) => {
        let c = typeof inp === 'string'
            ? countries[inp]
            : inp;

        if (!c.code || !c.code.toLowerCase) {
            return null;
        }

        return `http://${window.location.hostname}:${BACKEND_PORT}/assets/country_flag/${c.code.toLowerCase()}.png`
    };

    const countryDisplayName = (/** TSHCountry */ country) => {
        return country?.name ? `${country.name} (${country.code})` : country;
    };

    return <Autocomplete
        autoHighlight
        autoComplete
        autoSelect
        forcePopupIcon={false}
        clearIcon={null}
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
            const flagAsset = getCountryFlagAsset(option);
            return (
                <li key={key} {...rest}>
                    { flagAsset &&
                        <img alt="Country flag" loading={"lazy"} src={flagAsset} width={inlineFlagWidth} />
                    }
                    <span style={{marginLeft: '16px'}}>
                        {countryDisplayName(option)}
                    </span>
                </li>
            )
        }}
        renderInput={(params) => {
            const slotProps = params.slotProps ?? {};

            if (country?.name) {
                const flagAsset = getCountryFlagAsset(country);
                if (flagAsset) {
                    slotProps['input'] = {
                        startAdornment: <InputAdornment position="start">
                            <img
                                alt="Country flag"
                                loading={"lazy"}
                                src={flagAsset}
                                onError={(e) => e.nativeEvent.target.remove()}
                                width={inlineFlagWidth}
                            />
                        </InputAdornment>
                    }
                }
            }

            return <TextField
                {...params}
                slotProps={slotProps}
                label={i18n.t("country")}
            />
        }}

        value={country ?? null}
        options={Object.values(countries)}
        onChange={(ev, val) => onChange(val?.code ?? "")}
        getOptionLabel={(opt) => (opt?.name ?? "")}
        {...props}
        sx={{
            ...(props.sx ?? {}),
            '& .MuiAutocomplete-popupIndicator': {
                display: 'none'
            },
        }}
    />
}
