import TextField from "./ScoreboardPage/TextField";
import React from "react";
import {Button, InputAdornment, Stack, SxProps} from "@mui/material";
import {Grid} from "@mui/system";

export interface NumberInputProps {
    value: number;
    label?: string;
    min?: number;
    max?: number;
    onChange: (oldVal: number, newVal: number) => void;
    wingWidth?: number;
    width?: number;
    sx?: SxProps;
}

export function NumberInput(props: NumberInputProps) {
    const inputProps = {min: 0};
    if (props.max) {
        inputProps['max'] = props.max;
    }

    const wingButtonWidth = props.wingWidth ?? 32;
    let sx = props.sx ?? {};
    const min = props.min ?? Number.MIN_SAFE_INTEGER;
    const max = props.max ?? Number.MAX_SAFE_INTEGER;

    return (
        <Grid container sx={{...sx, width: props.width}}>
            <Stack direction={"row"} sx={{position: 'relative'}}>
                <TextField
                    type={"number"}
                    variant="outlined"
                    value={props.value}
                    onChange={(e) => props.onChange(props.value, Number.parseInt(e.target.value))}
                    label={props.label}
                    sx={{
                        width: props.width ? `${props.width - wingButtonWidth*2}px` : undefined,
                        marginX: `${wingButtonWidth}px`,

                        '& .MuiInputBase-root': {
                            paddingX: 0,
                            marginX: 0,
                            borderRadius: 0,
                            justifyContent: 'space-between',
                        },
                        '& .MuiOutlinedInput-notchedOutline': {
                            borderLeft: 0,
                            borderRight: 0,
                        },
                        '& input': {
                            width: '50px',
                            textAlign: "center",
                            MozAppearance: 'textfield',
                        },
                        '& input::-webkit-outer-spin-button, & input::-webkit-inner-spin-button': {
                            WebkitAppearance: 'none',
                            margin: 0,
                        }
                    }}
                    slotProps={{
                        htmlInput: inputProps,
                        input: {
                            startAdornment:
                                <InputAdornment
                                    position={"start"}
                                    sx={{
                                        position: 'absolute',
                                        left: `-${wingButtonWidth}px`,
                                        maxHeight: '100%',
                                        height: '100%',
                                        margin: 0,
                                        padding: 0,
                                    }}
                                >
                                    <Button
                                        variant={"outlined"}
                                        disabled={props.value <= min}
                                        onClick={() => props.onChange && props.onChange(props.value, Math.max(min, props.value - 1))}
                                        sx={{
                                            borderBottomRightRadius: 0,
                                            borderTopRightRadius: 0,
                                            height: '100%',
                                            minWidth: wingButtonWidth,
                                            width: wingButtonWidth,
                                            padding:0,
                                            margin:0,
                                        }}
                                    >
                                        -
                                    </Button>
                                </InputAdornment>,
                            endAdornment:
                                <InputAdornment
                                    position={"end"}
                                    sx={{
                                        position: 'absolute',
                                        right: `-${wingButtonWidth}px`,
                                        maxHeight: '100%',
                                        height: '100%'
                                    }}
                                >
                                    <Button
                                        variant={"outlined"}
                                        disabled={props.value >= max}
                                        onClick={() => props.onChange && props.onChange(props.value, Math.min(max, props.value + 1))}
                                        sx={{
                                            borderTopLeftRadius: 0,
                                            borderBottomLeftRadius: 0,
                                            height: '100%',
                                            minWidth: wingButtonWidth,
                                            width: wingButtonWidth,
                                            padding:0,
                                            margin:0,
                                        }}
                                    >
                                        +
                                    </Button>
                                </InputAdornment>
                        }
                    }}
                />
            </Stack>
        </Grid>
    )
}
