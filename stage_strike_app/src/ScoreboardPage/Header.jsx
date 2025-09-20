import {useContext} from "react";
import {TSHStateContext} from "./Contexts";
import {AppBar, Toolbar, Typography} from "@mui/material";
import {Box} from "@mui/system";
import {useTheme} from "@mui/material/styles";
import {BACKEND_PORT} from "../env";


export const Header = (props) => {
    const /** @type {TSHState} */ tshState = useContext(TSHStateContext);
    const theme = useTheme();

    return (
        <AppBar sx={{
            position: 'unset',
            px: '2em',
        }}>
            <Toolbar disableGutters sx={{
                whiteSpace: "nowrap",
                textOverflow: "ellipsis",
                display: 'flex',

                [theme.breakpoints.down('sm')]: {
                    flexDirection: 'column',
                    gap: 1,
                    paddingY: 2,
                },
            }}>

                <Typography
                    variant="h6"
                    gap={2}
                    sx={{
                        display: 'flex',
                        alignItems: "center",
                        mr: 4,
                    }}
                >
                    <img alt="TSH logo" src={`http://${window.location.hostname}:${BACKEND_PORT}/assets/icons/icon.png`} height={48} width={48} sx={{mr: 2}} />
                    Web Scoreboard
                </Typography>

                <Box
                    sx={{
                        display: 'flex',
                        alignItems: 'center',
                        mr: 2
                    }}
                >
                    <span>Game:&nbsp;</span>
                    {tshState.game?.logo
                        ? <img
                            alt={"Game logo"}
                            src={`http://${window.location.hostname}:${BACKEND_PORT}/${tshState.game.logo.replace("./", "/")}`}
                            height={48}
                        />
                        : <span>{tshState.game?.name ?? "Unknown"}</span>
                    }
                </Box>

                <Box sx={{
                    overflowX: "hidden",
                    textOverflow: "ellipsis",
                    maxWidth: '100%',
                }}>
                    <span>Event:&nbsp;</span>
                    <span>{tshState.tournamentInfo.tournamentName}:</span>
                    <span>{tshState.tournamentInfo.eventName}</span>
                </Box>
            </Toolbar>
        </AppBar>
    )
}
