import React from "react";
import {
    Avatar,
    Autocomplete,
    Card,
    CardContent,
    CardHeader,
    Collapse,
    IconButton,
    Stack
} from "@mui/material";
import TextField from './TextField';
import i18n from "../i18n/config";
import {ExpandMore} from "@mui/icons-material";
import {CharSelector} from "./CharSelector";
import {useSelector} from "react-redux";
import {CountrySelector} from "../CountrySelector";
import {CountryStateSelector} from "../CountryStateSelector";

/**
 * @typedef {{
 *    charIdx: string,
 *    charName: string,
 *    charSkin: string | number
 * }} CharacterSelection
 */

/**
 * @typedef {Record.<number, CharacterSelection>} CharacterSelections
 */

/** @typedef {{
 *     _countryCode?: string,
 *     _stateCode?: string,
 *     _team: string,
 *     _name: string,
 *     _realName: string,
 *     _twitter: string,
 *     _pronoun: string,
 *     _characterSelections: CharacterSelections
 *
 *     countryCode?: string,
 *     stateCode?: string,
 *     team: string,
 *     name: string,
 *     realName: string,
 *     twitter: string,
 *     pronoun: string,
 *     characterSelections: CharacterSelections
 *     expanded: boolean
 * }} PlayerState
 */

/**
 * @param {TSHPlayerDbEntry} player
 * @param {string} gameCodename
 * @param {number} count
 * @return {CharacterSelections}
 */
function getMains(player, gameCodename, count) {
    const /** @type CharacterSelections */ rval = {};
    // Yeah, we do 1-based counting here.
    for (let i = 1; i < count+1; i += 1) {
        rval[i] = {
            charName: "",
            charSkin: "",
            charIdx: i
        };
    }

    if (player.mains?.hasOwnProperty(gameCodename)) {
        const mains = player.mains?.[gameCodename];
        if (mains) {
            for (let i = 0; i < count && i < mains.length; i += 1) {
                const main = mains[i]
                rval[i+1] = {
                    charName: main?.[0] ?? "",
                    charSkin: main?.[1] ?? "",
                    charIdx: i+1
                }
            }
        }
    }

    return rval;
}

/**
 * @param {string} teamId
 * @param {string} teamKey
 * @param {TSHPlayerInfo} player
 */
export default React.forwardRef(function Player({teamId, teamKey, player}, ref) {
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
        _charSelections: charsFromTsh(player.character),

        countryCode: player.country?.code,
        stateCode: player.state?.code,
        team: player.team,
        name: player.name,
        realName: player.real_name,
        twitter: player.twitter,
        pronoun: player.pronoun,
        charSelections: charsFromTsh(player.character),
        expanded: true
    });

    // console.log(`Rendering player widget: `, player)

    const playerId = `${teamId}-p-${teamKey}`;
    const tshState = useSelector((s) => s.tshState.tshState);
    const gameCodename = tshState?.game?.codename;
    /** @type TSHPlayerDb */ const playerDb = useSelector(state => state.tshPlayers.players);

    React.useEffect(() => {
        const newProps = {
            countryCode: player.country?.code,
            stateCode: player.state?.code,
            team: player.team,
            name: player.name,
            realName: player.real_name,
            twitter: player.twitter,
            pronoun: player.pronoun,
            charSelections: charsFromTsh(player.character),
        }

        const stateUpdates = {};
        for (const prop in newProps) {
            stateUpdates[prop] = newProps[prop];
            stateUpdates[`_${prop}`] = newProps[prop];
        }

        if (Object.keys(stateUpdates).length > 0) {
            console.log(`Received new data for [${playerId}, DB: ${tshPlayerDbId}]`, stateUpdates);
            setState({
                ...state,
                ...stateUpdates,
            });
        }
    }, [player]) // eslint-disable-line react-hooks/exhaustive-deps
    // We don't want our dependencies to be exhaustive above because we want to specifically only

    const /** @type {TSHCharacterDb} */ characters = useSelector(state => state.tshCharacters.characters);
    const tshPlayerDbId = player?.id?.at(0) || player?.id?.at(1) || -1;

    const changeHandlerFor = (fieldName) => {
        return (/** React.ChangeEvent<HTMLInputElement> | string */ e) => {
            const newVal = (
                typeof e === 'string' ? e
                    : e === null || e === undefined ? ''
                    : e?.target?.value
            );

            console.log(`React-State: Setting (${playerId}).${fieldName} to ${newVal}`);

            const newState = {
                ...state,
                [fieldName]: newVal
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
        rval.mains = {[gameCodename]: []}

        /*
         * When we submit character selection, it also updates the player's mains in the player DB. To prevent
         * overriding them when we haven't selected a character, we do this song-and-dance to submit the selected
         * characters and fall back
         */
        const lookupName = !!player.prefix ? `${player.prefix} ${player.name}` : player.name;
        const existingMains = Object.values(playerDb[lookupName]?.mains?.[gameCodename] ?? [])
        const charsFromForm = Object.values(state.charSelections)
        // The number of characters from the original TSH state.
        const maxChars = Object.values(state._charSelections).length;
        const mainsToSubmit = [];
        for (let i = 0; i < maxChars; i += 1) {
            if (i < charsFromForm.length && !!charsFromForm[i].charName) {
                mainsToSubmit.push([
                    (charsFromForm[i].charName ? characters[charsFromForm[i].charName]?.en_name : ""),
                    charsFromForm[i].charSkin || 0,
                    ""
                ])
            } else if (i < existingMains.length) {
                mainsToSubmit.push(existingMains[i]);
            } else {
                mainsToSubmit.push(["", 0, ""])
            }
        }
        rval.mains[gameCodename] = mainsToSubmit;

        // Don't persist player info to DB if they have no tag.
        rval.savePlayerToDb = (!!state.name);

        console.log("Player update payload:",  rval)
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
                charSelections: getMains(newPlayer, gameCodename, Object.keys(state._charSelections).length),
            });
        } else {
            // value is an ad-hoc string of a player tag.
            setState({...state, name: newPlayer})
        }
    };

    /**
     *
     * @param charIdx
     * @param {TSHCharacterBase|string} newChar
     */
    const onCharNameChanged = (charIdx, newChar) => {
        const charEntry = characters?.[newChar?.en_name];
        let charSkin = "";
        if (charEntry) {
            const charSkins = charEntry?.skins?.length;
            if (charSkins && charSkins > 0) {
                charSkin = 0;
            }
        }

        setState({
            ...state,
            charSelections: {
                ...state.charSelections,
                [charIdx]: {
                    charIdx,
                    charName: newChar?.en_name ?? newChar,
                    charSkin: charSkin
                }
            }
        });
    }

    const onCharSkinChanged = (charIdx, newSkinIdx) => {
        setState({
            ...state,
            charSelections: {
                ...state.charSelections,
                [charIdx]: {
                    ...(state.charSelections?.[charIdx] ?? {}),
                    charSkin: newSkinIdx
                }
            }
        })
    }

    const idBase = `team-${teamId}-player-${playerId}-`;
    const rowProps = {direction: 'row', spacing: 2};

    React.useImperativeHandle(ref, () => ({
        getModifiedPlayerData: getModifiedPlayerData
    }), [state, getModifiedPlayerData]); // eslint-disable-line react-hooks/exhaustive-deps
    // ignoring changes in state cause getModifiedPlayerData to return bad values for some reason.

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
                                    return player?.prefixed_tag ?? player;
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
                        </Stack>

                        <TextField label={i18n.t("real_name")}
                                   key={idBase + "realName"}
                                   id={idBase + "realName"}
                                   value={state.realName ?? ''}
                                   onChange={changeHandlerFor('realName')}
                        />

                        <Stack {...rowProps} alignItems={"stretch"}>
                            <TextField label={i18n.t("twitter")}
                                       sx={{width: '50%', maxWidth: '50%'}}
                                       key={idBase + "twitter"}
                                       id={idBase + "twitter"}
                                       value={state.twitter ?? ''}
                                       onChange={changeHandlerFor('twitter')}
                            />
                            <TextField label={i18n.t("pronouns")}
                                       sx={{width: '50%', maxWidth: '50%'}}
                                       key={idBase + "pronoun"}
                                       id={idBase + "pronoun"}
                                       value={state.pronoun ?? ''}
                                       onChange={changeHandlerFor('pronoun')}
                            />
                        </Stack>

                        <Stack {...rowProps}>

                            <CountrySelector
                                sx={{width: '50%', maxWidth: '50%'}}
                                label={i18n.t("country")}
                                value={state.countryCode ?? ''}
                                onChange={changeHandlerFor('countryCode')}
                            />

                            <CountryStateSelector
                                countryCode={state.countryCode}
                                sx={{width: '50%', maxWidth: '50%'}}
                                label={i18n.t("state")}
                                value={state.stateCode ?? ''}
                                onChange={changeHandlerFor('stateCode')}
                            />
                        </Stack>


                        {
                            Object.values(state.charSelections).map( (cs) =>
                                <CharSelector
                                    key={`${playerId}-cs-${cs.charIdx}`}
                                    id={`${playerId}-cs-${cs.charIdx}`}
                                    charName={cs.charName}
                                    charSkin={cs.charSkin}
                                    onCharNameChanged={(ev, val, _) => onCharNameChanged(cs.charIdx, val)}
                                    onCharSkinChanged={(ev, val, _) => onCharSkinChanged(cs.charIdx, ev.target.value)}
                                    stackProps={rowProps}
                                />
                            )
                        }
                    </Stack>
                </CardContent>
            </Collapse>
        </Card>
    )
});

/**
 *
 * @param {TSHCharacterSelections} tshChars
 * @returns {CharacterSelections}
 */
function charsFromTsh(tshChars) {
    const res = {};
    for (const i in tshChars) {
        res[i] = {
            charIdx: i,
            charName: tshChars[i].en_name,
            charSkin: tshChars[i].skin,
        }

    }
    return res;
}

