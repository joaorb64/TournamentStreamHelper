import {Autocomplete, MenuItem, Stack} from "@mui/material";
import {TSHCharacterContext} from "./Contexts";
import TextField from "./TextField";
import {useContext} from "react";
import i18n from "i18next";

/**
 * @typedef {{
 *  id: string
 *  charName: string
 *  charSkin: string|number
 *  onCharNameChanged: () => void
 *  onCharSkinChanged: () => void
 *  stackProps: any
 * }} CharSelectorProps
 */

/**
 *
 * @param {CharSelectorProps} props
 * @returns {JSX.Element}
 * @constructor
 */

export function CharSelector({
    id,
    charName,
    charSkin,
    onCharNameChanged,
    onCharSkinChanged,
    stackProps,
 }) {
    const /** @type {TSHCharacterDb} */ characters = useContext(TSHCharacterContext);
    const hasCharName = charName && charName !== '';

    return (
    <Stack {...stackProps} alignItems={"stretch"} justifyContent={"space-evenly"} sx={{height: 56}}>
        <Autocomplete
            id={id + "-name"}
            options={Object.values(characters)}
            value={characters?.[charName] ?? ""}
            freeSolo={true}
            sx={{width: '50%'}}
            onChange={onCharNameChanged}
            getOptionLabel={(char) => char?.display_name ?? char}
            renderOption={(props, option, _) => {
                let skimage = option?.skins?.[0]?.assets?.['base_files/icon']?.['asset']
                if (!!skimage) {
                    skimage = skimage.replace("./", "");
                }

                return <li {...props}>
                    {skimage
                        ? <img height="32" width="32" alt={`Image for skin ${charSkin}`}
                               src={`http://${window.location.hostname}:5000/${skimage}`}/>
                        : <div style={{height: '32px', width: '32px'}}/>
                    }
                    <span style={{marginLeft: '16px'}}>
                                            {option?.display_name ?? option}
                                        </span>
                </li>
            }}
            renderInput={(params) => {
                return (
                    <div>
                        <TextField
                            {...params}
                            label={i18n.t("character")}
                        />
                    </div>)
            }
            }
        />

        <TextField
            id={id + "-skin"}
            /* MUI doesn't propagate the input id properly for some reason */
            inputProps={{
                id: id + "-skin"
            }}
            label={"Skin"}
            select
            value={hasCharName ? charSkin : ''}
            disabled={!hasCharName}
            onChange={onCharSkinChanged}
            sx={{
                display: 'block',
                width: '50%',
                height: '100%',

                padding: 0,
                '& .MuiPopover-paper': {
                    minWidth: 'initial'
                },
                '& .MuiInputBase-root': {
                    height: '100%',
                    width: '100%'
                },
                '& .MuiSelect-select': {
                    paddingTop: 0,
                    paddingBottom: 0
                },
            }}
        >
            {
                Object.entries(characters[charName]?.skins ?? {}).map(([idx, skin]) => (
                    <MenuItem
                        key={charName + idx}
                        value={idx}
                    >
                        <div style={{height: 56, width: 56, overflow: 'hidden', margin: 'auto'}}>
                            <img
                                alt={`Skin ${idx}`}
                                style={{
                                    height: '100%',
                                    width: '100%',
                                    verticalAlign: 'middle',
                                    objectFit: 'cover'
                                }}
                                src={getSkinAssetUrl(skin)}
                            />
                        </div>
                    </MenuItem>
                ))
            }
        </TextField>
    </Stack>
    )
}

/**
 * @param {TSHCharacterSkin} skin
 * @return string
 */
function getSkinAssetUrl(skin) {
    if (!skin) {
        return "about:_blank";
    }

    const assets = skin.assets;
    let asset = null;

    if (assets?.costume) {
        asset = assets.costume;
    } else if (assets?.full) {
        asset = assets.full;
    } else if (assets?.['base_files/icon']) {
        asset = assets['base_files/icon'];
    } else {
        return "about:_blank";
    }

    return `http://${window.location.hostname}:5000/${asset.asset.slice(2)}`;
}

