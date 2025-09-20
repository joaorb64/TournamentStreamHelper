import React from "react";
import {
    Button, Card, CardContent, CardHeader,
    Checkbox, Collapse,
    FormControlLabel,
    FormGroup, IconButton,
    Stack,
    Table, TableBody, TableCell,
    TableContainer,
    TableHead, TableRow,
} from "@mui/material";
import i18n from "../i18n/config";
import TextField from "./TextField";
import {alpha} from "@mui/material/styles";
import {ExpandMore} from "@mui/icons-material";
import {BACKEND_PORT} from "../env";


/**
 * @typedef {object} UpcomingSetsState
 * @property {?string} setFilter
 * @property {?TSHSet} selectedSet
 * @property {boolean} showFinished
 * @property {boolean} expanded
 * @property {Array.<TSHSet>} sets
 */
export default class UpcomingSets extends React.Component {
    /** @type UpcomingSetsState */ state;

    constructor(props) {
        super(props);

        this.state = {
            isLoading: true,
            setFilter: null,
            selectedSet: null,
            showFinished: false,
            expanded: true,
            sets: []
        };
    }

    componentDidMount = () => {
        this.FetchSets();
    }

    FetchSets = () => {
        this.setState({
            ...this.state,
            isLoading: true,
        });

        fetch("http://" + window.location.hostname + `:${BACKEND_PORT}/get-sets?_foo=${this.state.showFinished ? "&getFinished=true" : ""}&`)
            .then((res) => res.json())
            .then(( /** {Array.<tourney_set>} */ data) => {
                this.setState({
                    ...this.state,
                    isLoading: false,
                    sets: data
                });
            })
            .catch(console.log);
    }

    SubmitNewSet = () => {
        this.setState({
            ...this.state,
            isLoading: true
        });

        fetch(
            "http://" + window.location.hostname + `:${BACKEND_PORT}/scoreboard1-load-set?set=${this.state.selectedSet?.id}`,
        )
            .then((resp) => {resp.text()})
            .then((respText) => {
                this.setState({
                    ...this.state,
                    isLoading: false
                });

                this.props.onSelectedSetChanged && this.props.onSelectedSetChanged(this.state.selectedSet.id);
            });
    }

    showFinishedSetsChanged = (e) => {
        this.setState({
            showFinished: e.target.checked ?? false
        }, () => {
            this.FetchSets();
        });
    }

    filterFieldChanged = (e) => {
        const newVal = e.target.value === "" ? null : e.target.value;
        this.setState({
            setFilter: newVal
        });
    }

    /**
     * @returns {TSHSet[]}
     */
    filteredSets = () => {
        if (this.state.setFilter === null) {
            return this.state.sets;
        }

        const fs = this.state.setFilter.toLocaleLowerCase();

        return this.state.sets.filter((set) => (
            set.p1_name.toLocaleLowerCase().includes(fs)
            || set.p2_name.toLocaleLowerCase().includes(fs)
            || set.round_name.toLocaleLowerCase().includes(fs)
            || set.stream?.toLocaleLowerCase().includes(fs)
        ));
    }

    onSetClicked = ( /** @type {TSHSet} */ set) => {
        this.setState({
            selectedSet: set
        });
    }

    render = () => {
        return (
            <Card>
                <CardHeader
                    title={`Upcoming Sets`}
                    action={
                        <IconButton onClick={() => this.setState({...this.state, expanded: !this.state.expanded})}>
                            <ExpandMore sx={{
                                transform: this.state.expanded ? 'rotate(0deg)' : 'rotate(270deg)'
                            }} />
                        </IconButton>
                    }
                />
                <Collapse in={this.state.expanded} timeout={"auto"}>
                    <CardContent>
                        <Stack xs={12} spacing={2}>
                            <Stack direction={"row"} gap={2}>
                                <Button
                                    variant={"outlined"}
                                    onClick={() => this.FetchSets()}
                                >
                                    {i18n.t("refresh_sets")}
                                </Button>

                                <Button
                                    variant={"outlined"}
                                    onClick={() => this.SubmitNewSet()}
                                    disabled={!this.state.selectedSet}
                                >
                                    {i18n.t("load_selected_set")}
                                </Button>
                            </Stack>

                            <FormGroup>
                                <FormControlLabel
                                    control={
                                        <Checkbox id={"show-finished-sets"} label="Show finished sets" onChange={this.showFinishedSetsChanged}  />
                                    }
                                    label={i18n.t("show_finished_sets")}
                                />
                                <TextField label={i18n.t("filter")}
                                           onChange={this.filterFieldChanged}
                                           variant="outlined"
                                           sx={(theme) => ({
                                               '& label[data-shrink="false"]': {color: theme.palette.text.disabled}
                                           })}
                                />
                            </FormGroup>

                            <TableContainer>
                                <Table stickyHeader>
                                    <TableHead>
                                        <TableRow>
                                            <TableCell>{i18n.t("p1")}</TableCell>
                                            <TableCell>{i18n.t("p2")}</TableCell>
                                            <TableCell>{i18n.t("phase")}</TableCell>
                                            <TableCell>{i18n.t("match")}</TableCell>
                                            <TableCell>{i18n.t("stream")}</TableCell>
                                            <TableCell>{i18n.t("station")}</TableCell>
                                        </TableRow>
                                    </TableHead>
                                    <TableBody>
                                        {
                                            this.filteredSets().map((/** TSHSet */ set) => (
                                                <TableRow
                                                    hover
                                                    onClick={() => {this.onSetClicked(set)}}
                                                    key={set.id}
                                                    sx={(theme) => ({
                                                        '&:last-child td, &:last-child th': {
                                                            border: 0
                                                        },
                                                        'td': (this.state.selectedSet?.id !== set.id ? {} : {
                                                            backgroundColor: theme.vars
                                                                ? `rgba(${theme.vars.palette.primary.mainChannel} / calc(${theme.vars.palette.action.selectedOpacity} + ${theme.vars.palette.action.hoverOpacity}))`
                                                                : alpha(
                                                                    theme.palette.primary.main,
                                                                    theme.palette.action.selectedOpacity,
                                                                ),
                                                        })
                                                    })}
                                                >
                                                    {/*
                                          * It's unclear if the backend will translate things like
                                          * "Losers Round 5" for us. Stuff exists to support it in the
                                          * python side of things, but using it browser-side is definitely
                                          * a yak that needs shaving.
                                          */}
                                                    <TableCell>{set.p1_name}</TableCell>
                                                    <TableCell>{set.p2_name}</TableCell>
                                                    <TableCell>{set.tournament_phase}</TableCell>
                                                    <TableCell>{set.round_name}</TableCell>
                                                    <TableCell>{set.stream}</TableCell>
                                                    <TableCell>{set.station}</TableCell>
                                                </TableRow>
                                            ))
                                        }
                                    </TableBody>
                                </Table>
                            </TableContainer>
                        </Stack>
                    </CardContent>
                </Collapse>
            </Card>
        )
    }
}
