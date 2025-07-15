import React from "react";
import {
    Avatar,
    Card,
    CardContent,
    CardHeader,
    Collapse,
    FormControl, IconButton,
    InputLabel, Paper,
    Select,
    Stack
} from "@mui/material";
import TextField from './TextField';
import i18n from "../i18n/config";
import {ExpandMore} from "@mui/icons-material";
import {TSHCharacterContext, TSHPlayerDBContext, TSHStateContext} from "./Contexts";

/**
 * @param {string} teamId
 * @param {TSHPlayerInfo} player
 */
export default React.forwardRef(function Player({teamId, player}, ref) {
    const [state, setState] = React.useState({
        _countryCode: player.country?.code,
        _stateCode: player.state?.code,
        _team: player.team,
        _name: player.name,
        _realName: player.real_name,
        _twitter: player.twitter,
        _pronoun: player.pronoun,
        _charCode: player.character[1].codename ?? "",

        countryCode: player.country?.code,
        stateCode: player.state?.code,
        team: player.team,
        name: player.name,
        realName: player.real_name,
        twitter: player.twitter,
        pronoun: player.pronoun,
        charCode: player.character[1].codename ?? "",
        expanded: true
    });

    const tshState = React.useContext(TSHStateContext);
    const gameCodename = tshState?.game?.codename;
    const playerDb = React.useContext(TSHPlayerDBContext);

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

    const characters = React.useContext(TSHCharacterContext);
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
            if (Object.keys(playerDb).includes(player.name)) {
                rval.mains = {
                    ...playerDb[player.name].mains,
                }
            } else {
                rval.mains = {};
            }

            rval.mains[gameCodename] = [[characters[state.charCode].en_name, 0, ""]];
        }

        rval.overwrite = true;

        console.log("Update payload:",  rval)
        return rval;
    }

    const idBase = `team-${teamId}-player-${playerId}-`;
    const rowProps = {direction: 'row', spacing: 2};

    React.useImperativeHandle(ref, () => ({
        getModifiedPlayerData: getModifiedPlayerData
    }) );

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
                                       value={state.team}
                                       onChange={changeHandlerFor('team')}
                            />
                            <TextField label={i18n.t("tag")}
                                       key={idBase + "tag"}
                                       id={idBase + "tag"}
                                       value={state.name}
                                       onChange={changeHandlerFor('name')}
                            />
                        </Stack>

                        <TextField label={i18n.t("real_name")}
                                   key={idBase + "realName"}
                                   id={idBase + "realName"}
                                   value={state.realName}
                                   onChange={changeHandlerFor('realName')}
                        />

                        <Stack {...rowProps}>
                            <TextField label={i18n.t("twitter")}
                                       key={idBase + "twitter"}
                                       id={idBase + "twitter"}
                                       value={state.twitter}
                                       onChange={changeHandlerFor('twitter')}
                            />
                            <TextField label={i18n.t("pronouns")}
                                       key={idBase + "pronoun"}
                                       id={idBase + "pronoun"}
                                       value={state.pronoun}
                                       onChange={changeHandlerFor('pronoun')}
                            />
                        </Stack>

                        <Stack {...rowProps}>
                            <TextField label={i18n.t("country")}
                                       key={idBase + "country"}
                                       id={idBase + "country"}
                                       value={state.countryCode}
                                       onChange={changeHandlerFor('countryCode')}
                            />
                            <TextField label={i18n.t("state")}
                                       key={idBase + "state"}
                                       id={idBase + "state"}
                                       value={state.stateCode}
                                       onChange={changeHandlerFor('stateCode')}
                            />
                        </Stack>

                        <FormControl>
                            <InputLabel
                                id={idBase + "char-label"}
                                sx={t => ({'&[data-shrink="false"]': {color: t.palette.text.disabled}})}
                                htmlFor={idBase + "char-select"}
                            >
                                Character
                            </InputLabel>
                            <Select
                                key={idBase + "char-select"}
                                id={idBase + "char-select"}
                                labelId={idBase + "char-label"}
                                label={i18n.t("character")}
                                value={state.charCode ?? ""}
                                onChange={changeHandlerFor('charCode')}
                                native={true}
                            >
                                <option value={""}></option>
                                {
                                    Object.values(characters).sort().map((character) => (
                                        <option key={character.codename} value={character.codename}>
                                            {character.display_name}
                                        </option>
                                    ))
                                }
                            </Select>
                        </FormControl>
                    </Stack>
                </CardContent>
            </Collapse>
        </Card>
    )
});
