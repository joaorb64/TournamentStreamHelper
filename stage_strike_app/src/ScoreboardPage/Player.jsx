import React from "react";
import {
    Avatar,
    Autocomplete,
    Card,
    CardContent,
    CardHeader,
    Collapse,
    IconButton,
    MenuItem,
    Stack
} from "@mui/material";
import TextField from './TextField';
import i18n from "../i18n/config";
import {ExpandMore} from "@mui/icons-material";
import {TSHCharacterContext, TSHPlayerDBContext, TSHStateContext} from "./Contexts";
/** @typedef {{
 *     _countryCode?: string,
 *     _stateCode?: string,
 *     _team: string,
 *     _name: string,
 *     _realName: string,
 *     _twitter: string,
 *     _pronoun: string,
 *     _charCode: string,
 *     _charSkin: string | number,
 *
 *     countryCode?: string,
 *     stateCode?: string,
 *     team: string,
 *     name: string,
 *     realName: string,
 *     twitter: string,
 *     pronoun: string,
 *     charCode: string,
 *     charSkin: string,
 *     expanded: boolean
 * }} PlayerState
 */

/**
 * @param {TSHPlayerDbEntry} player
 * @param {string} gameCodename
 * @return {{charCode?: string, charSkin: string}}
 */
function getMain(player, gameCodename) {
    let charCode = "";
    let charSkin = "";

    if (player.mains?.hasOwnProperty(gameCodename)) {
        const main = player.mains?.[gameCodename]?.[0];
        if (main) {
            charCode = main?.[0] ?? "";
            charSkin = main?.[1] ?? "";
        }
    }

    return {
        charCode, charSkin
    };
}

/**
 * @param {string} teamId
 * @param {TSHPlayerInfo} player
 */
export default React.forwardRef(function Player({teamId, player}, ref) {
    const [
        /** @type {PlayerState} */ state,
        setState
    ] = React.useState({
        _countryCode: player.country?.code,
        _stateCode: player.state?.code,
        _team: player.team,
        _name: player.name,
        _realName: player.real_name,
        _twitter: player.twitter,
        _pronoun: player.pronoun,
        _charCode: player.character[1].codename ?? "",
        _charSkin: "",

        countryCode: player.country?.code,
        stateCode: player.state?.code,
        team: player.team,
        name: player.name,
        realName: player.real_name,
        twitter: player.twitter,
        pronoun: player.pronoun,
        charCode: player.character[1].codename ?? "",
        charSkin: "",
        expanded: true
    });

    const /** @type {TSHState} */ tshState = React.useContext(TSHStateContext);
    const gameCodename = tshState?.game?.codename;
    /** @type TSHPlayerDb */ const playerDb = React.useContext(TSHPlayerDBContext);

    React.useEffect(() => {
        const newProps = {
            countryCode: player.country?.code,
            stateCode: player.state?.code,
            team: player.team,
            name: player.name,
            realName: player.real_name,
            twitter: player.twitter,
            pronoun: player.pronoun,
            charCode: player?.character?.[1]?.codename ?? "",
            charSkin: player?.character?.[1]?.skin ?? "",
        }

        const stateUpdates = {};
        for (const prop in newProps) {
            if (state[`_${prop}`] !== newProps[prop]) {
                stateUpdates[prop] = newProps[prop];
                stateUpdates[`_${prop}`] = newProps[prop];
            }
        }

        if (Object.keys(stateUpdates).length > 0) {
            console.log("Updating player data: ", stateUpdates);
            setState({...state, ...stateUpdates});
        }
    }, [player])

    const /** @type {TSHCharacterDb} */ characters = React.useContext(TSHCharacterContext);
    const playerId = player?.id?.at(0) || player?.id?.at(1) || -1;

    const changeHandlerFor = (fieldName) => {
        return (/** React.ChangeEvent<HTMLInputElement> */ e) => {
            const newState = {
                ...state,
                [fieldName]: e.target.value,
            };

            setState(newState);
        }
    }

    /** @returns {TSHPlayerInfo} */
    const getModifiedPlayerData = () => {
        /*
         * The fields here are slightly off... The API sends the scoreboard out with the real name in the
         * player's "real_name" field and the tag in the "name" field. But on save it uses a slightly different
         * format where "name" is where the real name is stored and "gamerTag" holds the tag.
         *
         * In general the field names just... don't line up.
         */
        const rval = {};
        rval.country_code = state.countryCode;
        rval.state_code = state.stateCode;
        rval.prefix = state.team
        rval.gamerTag = state.name
        rval.name = state.realName
        rval.twitter = state.twitter
        rval.pronoun = state.pronoun
        if (!!state.charCode) {
            const lookupName = !!player.prefix ? `${player.prefix} ${player.name}` : player.name;
            if (Object.keys(playerDb).includes(lookupName)) {
                rval.mains = {
                    ...playerDb[player.name].mains,
                }
            } else {
                rval.mains = {};
            }


            rval.mains[gameCodename] = [
                [
                    state.charCode ? characters[state.charCode].en_name : "",
                    state.charSkin || 0,
                    ""
                ]
            ];
        }

        // Don't persist player info to DB if they have no tag.
        rval.savePlayerToDb = (!!state.name);

        console.log("Update payload:",  rval)
        return rval;
    }

    /**
     *
     * @param {React.SyntheticEvent} event
     * @param {TSHPlayerDbEntry|string} newPlayer
     * @param {string} reason
     */
    const onTagChanged = (event, newPlayer,  reason) => {
        if (newPlayer instanceof Object && newPlayer.hasOwnProperty("gamerTag")) {
            // newPlayer is a TSHPlayerDbEntry
            setState({
                ...state,
                countryCode: newPlayer.country_code ?? "",
                name: newPlayer.gamerTag,
                team: newPlayer.prefix ?? "",
                realName: newPlayer.name ?? "",
                twitter: newPlayer.twitter ?? "",
                pronoun: newPlayer.pronoun ?? "",
                stateCode: newPlayer.state_code ?? "",
                ...getMain(newPlayer, gameCodename),
            });
        } else {
            // value is an ad-hoc string of a player tag.
            setState({...state, name: newPlayer})
        }
        console.log(event, newPlayer, reason);
    };

    const onCharCodeChanged = (event, value, _) => {
        const charEntry = characters?.[value?.codename];
        let charSkin = "";
        if (charEntry) {
            const charSkins = charEntry?.skins?.length;
            if (charSkins && charSkins > 0) {
                charSkin = 0;
            }
        }
        setState({...state, charCode: value?.codename ?? value, charSkin: charSkin})
    }

    const idBase = `team-${teamId}-player-${playerId}-`;
    const rowProps = {direction: 'row', spacing: 2};

    React.useImperativeHandle(ref, () => ({
        getModifiedPlayerData: getModifiedPlayerData
    }), [state, getModifiedPlayerData]);

    return (
        <Card raised={true}>
            <CardHeader
                avatar={<Avatar
                    src={player?.online_avatar}
                    width={96}
                    height={96}
                    sx={{objectFit: "contain"}}
                    alt={i18n.t("avatar_for", {player: state.name})}
                >{state.name?.at(0) ?? "?"}</Avatar>}
                action={<IconButton onClick={() => setState({...state, expanded: !state.expanded})}>
                    <ExpandMore sx={{
                        transform: state.expanded ? 'rotate(0deg)' : 'rotate(270deg)'
                    }}/>
                </IconButton>}
                title={state.name}
                height={96}
            />
            <Collapse in={state.expanded} timeout={"auto"}>
                <CardContent>
                    <Stack spacing={4}>
                        <Stack {...rowProps}>
                            <TextField label={i18n.t("sponsor")}
                                       key={idBase + "sponsor"}
                                       id={idBase + "sponsor"}
                                       value={state.team ?? ''}
                                       onChange={changeHandlerFor('team')}
                            />

                            <Autocomplete
                                key={idBase + "tag"}
                                id={idBase + "tag"}
                                options={Object.values(playerDb)}
                                value={state.name ?? ''}
                                getOptionLabel={(/** TSHPlayerDbEntry|string */ player) => {
                                    return player?.gamerTag ?? player;
                                }}
                                freeSolo={true}
                                sx={{width: '100%'}}
                                onChange={onTagChanged}
                                renderInput={(params) =>
                                    <TextField
                                        {...params}
                                        label={i18n.t("tag")}
                                    />}
                            />


                            {/*
                            <TextField label={i18n.t("tag")}
                                       key={idBase + "tag"}
                                       id={idBase + "tag"}
                                       value={state.name}
                                       onChange={changeHandlerFor('name')}
                            />
                            */}
                        </Stack>

                        <TextField label={i18n.t("real_name")}
                                   key={idBase + "realName"}
                                   id={idBase + "realName"}
                                   value={state.realName ?? ''}
                                   onChange={changeHandlerFor('realName')}
                        />

                        <Stack {...rowProps}>
                            <TextField label={i18n.t("twitter")}
                                       key={idBase + "twitter"}
                                       id={idBase + "twitter"}
                                       value={state.twitter ?? ''}
                                       onChange={changeHandlerFor('twitter')}
                            />
                            <TextField label={i18n.t("pronouns")}
                                       key={idBase + "pronoun"}
                                       id={idBase + "pronoun"}
                                       value={state.pronoun ?? ''}
                                       onChange={changeHandlerFor('pronoun')}
                            />
                        </Stack>

                        <Stack {...rowProps}>
                            <TextField label={i18n.t("country")}
                                       key={idBase + "country"}
                                       id={idBase + "country"}
                                       value={state.countryCode ?? ''}
                                       onChange={changeHandlerFor('countryCode')}
                            />
                            <TextField label={i18n.t("state")}
                                       key={idBase + "state"}
                                       id={idBase + "state"}
                                       value={state.stateCode ?? ''}
                                       onChange={changeHandlerFor('stateCode')}
                            />
                        </Stack>

                            <Stack {...rowProps} alignItems={"stretch"} justifyContent={"space-evenly"} sx={{height: 56}}>
                                <Autocomplete
                                    key={idBase + "char-select"}
                                    id={idBase + "char-select"}
                                    options={Object.values(characters)}
                                    value={characters?.[state.charCode] ?? ""}
                                    freeSolo={true}
                                    sx={{width: '50%'}}
                                    onChange={onCharCodeChanged}
                                    getOptionLabel={(char) => char?.display_name ?? char}
                                    renderOption={(props, option, _) => {
                                        let skimage = option?.skins?.[0]?.assets?.['base_files/icon']?.['asset']
                                        if (!!skimage) {
                                            skimage = skimage.replace("./", "");
                                        }

                                        return <li {...props}>
                                            {skimage
                                                ? <img height="32" width="32" alt={`Profile icon for ${state.name}`} src={`http://${window.location.hostname}:5000/${skimage}`}/>
                                                : <div style={{height:'32px', width:'32px'}}/>
                                            }
                                            <span style={{marginLeft: '16px'}}>
                                            {option?.display_name ?? option}
                                        </span>
                                        </li>
                                    }}
                                    renderInput={(params) => {
                                        return(
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
                                    label={"Skin"}
                                    select
                                    value={(!state.charCode || state.charCode === '') ? '' : state.charSkin }
                                    disabled={(!state.charCode || state.charCode === '')}
                                    onChange={changeHandlerFor('charSkin')}
                                    sx={{
                                        display: 'block',
                                        width: '50%',
                                        height: '100%',

                                        padding:0,
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
                                        Object.entries(characters[state.charCode]?.skins ?? {}).map(([idx, skin]) => (
                                            <MenuItem
                                                key={state.charCode + idx}
                                                value={idx}
                                            >
                                                <div style={{height: 56, width: 56, overflow: 'hidden', margin: 'auto'}}>
                                                    <img
                                                        alt={`Skin number ${idx} for ${state.charCode}`}
                                                        style={{
                                                            height: '100%',
                                                            width: '100%',
                                                            verticalAlign: 'middle',
                                                            objectFit: 'cover'
                                                        }}
                                                        src={`http://${window.location.hostname}:5000/${skin?.assets?.costume?.asset?.slice(2)}`}
                                                    />
                                                </div>
                                            </MenuItem>
                                        ))
                                    }
                                </TextField>
                            </Stack>
                    </Stack>
                </CardContent>
            </Collapse>
        </Card>
    )
});
