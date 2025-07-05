import {createTheme, responsiveFontSizes} from "@mui/material/styles";

export const defaultTheme = createTheme({
    palette: {
        mode: "dark",
    },
});

export const darkTheme = responsiveFontSizes(createTheme({
    palette: {
        mode: "dark",
        text: {
            disabled: 'rgba(255,255,255, 0.3)'
        },
        p1color: defaultTheme.palette.augmentColor({
            color: { main: "#ff7a6d" },
            name: "p1color",
        }),
        p2color: defaultTheme.palette.augmentColor({
            color: { main: "#29b6f6" },
            name: "p2color",
        }),
    },
}));

