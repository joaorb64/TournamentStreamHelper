import {Autocomplete, MenuItem, Stack} from "@mui/material";
import TextField from "./TextField";
import i18n from "i18next";
import {BACKEND_PORT} from "../env";
import {useSelector} from "react-redux";

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
    const /** @type {TSHCharacterDb} */ characters = useSelector((state) => state.tshCharacters.characters);
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
            renderOption={(_allProps, option, _) => {
                const {key, ..._props} = _allProps;
                let skimage = option?.skins?.[0]?.assets?.['base_files/icon']?.['asset']
                if (!!skimage) {
                    skimage = skimage.replace("./", "");
                }

                return <li key={key} {..._props}>
                    {skimage
                        ? <img height="32" alt={`Skin ${charSkin}`}
                               src={`http://${window.location.hostname}:${BACKEND_PORT}/${skimage}`}/>
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

    return `http://${window.location.hostname}:${BACKEND_PORT}/${asset.asset.slice(2)}`;
}

