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

export default class Player extends React.Component {
    /**
     * @typedef {object} PlayerWidgetProps
     * @prop {string} teamId
     * @prop {TSHPlayerInfo} player
     * @prop {TSHCharacters} characters
     */
    /** @type {PlayerWidgetProps} */ props;

    constructor(/** PlayerWidgetProps */ props) {
        super(props);
        this.props = props;

        console.log("Player: ", props.player)
        this.player = props.player;
        this.state = {
            countryCode: props.player.country?.code,
            stateCode: props.player.state?.code,
            team: props.player.team,
            name: props.player.name,
            realName: props.player.real_name,
            twitter: props.player.twitter,
            pronoun: props.player.pronoun,
            charCode: props.player.character[1].codename ?? "",
            expanded: true
        }

        this.teamId = props.teamId;
        this.playerId = this.player?.id?.at(0) || this.player?.id?.at(1) || -1;
    }

    changeHandlerFor = (fieldName) => {
        return function changeHandler(/** React.ChangeEvent<HTMLInputElement> */ e) {
            const newState = {
                ...this.state,
                [fieldName]: e.target.value,
            };

            this.setState(newState);
        }.bind(this);
    }

    /** @returns {TSHPlayerInfo} */
    getModifiedPlayerData = () => {
        /*
         * The fields here are slightly off... The API sends the scoreboard out with the real name in the
         * player's "real_name" field and the tag in the "name" field. But on save it uses a slightly different
         * format where "name" is where the real name is stored and "gamerTag" holds the tag.
         *
         * In general the field names just... don't line up.
         */
        const rval = {};
        rval.country_code = this.state.countryCode;
        rval.state_code = this.state.stateCode;
        rval.prefix = this.state.team
        rval.gamerTag = this.state.name
        rval.name = this.state.realName
        rval.twitter = this.state.twitter
        rval.pronoun = this.state.pronoun
        if (!!this.state.charCode) {
            rval.mains = [this.props.characters[this.state.charCode].en_name]
        }

        return rval;
    }

    render = () => {
        const player = this.player;
        const idBase = `team-${this.teamId}-player-${this.playerId}-`;
        const rowProps = {direction: 'row', spacing: 2};

        return (
            <Card raised={true}>
                <CardHeader
                    avatar={<Avatar
                        src={player?.online_avatar}
                        width={96}
                        height={96}
                        sx={{objectFit: "contain"}}
                        alt={i18n.t("avatar_for", {player: this.state.name})}
                    >{this.state.name?.at(0) ?? "?"}</Avatar>}
                    action={<IconButton onClick={() => this.setState({...this.state, expanded: !this.state.expanded})}>
                        <ExpandMore sx={{
                            transform: this.state.expanded ? 'rotate(0deg)' : 'rotate(270deg)'
                        }}/>
                    </IconButton>}
                    title={this.state.name}
                    height={96}
                />
                <Collapse in={this.state.expanded} timeout={"auto"}>
                    <CardContent>
                        <Stack spacing={4}>
                            <Stack {...rowProps}>
                                <TextField label={i18n.t("sponsor")}
                                           key={idBase + "sponsor"}
                                           id={idBase + "sponsor"}
                                           value={this.state.team}
                                           onChange={this.changeHandlerFor('team')}
                                />
                                <TextField label={i18n.t("tag")}
                                           key={idBase + "tag"}
                                           id={idBase + "tag"}
                                           value={this.state.name}
                                           onChange={this.changeHandlerFor('name')}
                                />
                            </Stack>

                            <TextField label={i18n.t("real_name")}
                                       key={idBase + "realName"}
                                       id={idBase + "realName"}
                                       value={this.state.realName}
                                       onChange={this.changeHandlerFor('realName')}
                            />

                            <Stack {...rowProps}>
                                <TextField label={i18n.t("twitter")}
                                           key={idBase + "twitter"}
                                           id={idBase + "twitter"}
                                           value={this.state.twitter}
                                           onChange={this.changeHandlerFor('twitter')}
                                />
                                <TextField label={i18n.t("pronouns")}
                                           key={idBase + "pronoun"}
                                           id={idBase + "pronoun"}
                                           value={this.state.pronoun}
                                           onChange={this.changeHandlerFor('pronoun')}
                                />
                            </Stack>

                            <Stack {...rowProps}>
                                <TextField label={i18n.t("country")}
                                           key={idBase + "country"}
                                           id={idBase + "country"}
                                           value={this.state.countryCode}
                                           onChange={this.changeHandlerFor('countryCode')}
                                />
                                <TextField label={i18n.t("state")}
                                           key={idBase + "state"}
                                           id={idBase + "state"}
                                           value={this.state.stateCode}
                                           onChange={this.changeHandlerFor('stateCode')}
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
                                    defaultValue={""}
                                    value={this.state.charCode ?? ""}
                                    onChange={this.changeHandlerFor('charCode')}
                                    native={true}
                                >
                                    <option value={""}></option>
                                    {
                                        Object.values(this.props.characters).sort().map((character) => (
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
    }
}
