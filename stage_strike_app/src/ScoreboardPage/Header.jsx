import {AppBar, MenuItem, Select, Toolbar, Typography} from "@mui/material";
import {Box} from "@mui/system";
import {useTheme} from "@mui/material/styles";
import {shallowEqual, useSelector} from "react-redux";
import {BASE_URL} from "../env";
import {GameIcon} from "../GameIcon";


export const Header = ({onSelectedGameChange, ...rest}) => {
    const {tshState, games} = useSelector(state => ({
      tshState: state.tshState.tshState,
      games: state.tshGames.value
    }), shallowEqual);

    const theme = useTheme();

    return (
        <AppBar
          sx={{
              position: 'unset',
              px: '2em',
          }}
          {...rest}
        >
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
                    <img alt="TSH logo" src={`${BASE_URL}/assets/icons/icon.png`} height={48} width={48} sx={{mr: 2}} />
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
                    <Select
                      sx={{
                          '.MuiSelect-select': {
                              paddingY: 0,
                              marginY: 0
                          },
                      }}
                      value={tshState.game.codename}
                      renderValue={(codename) =>
                        <GameIcon game={games[codename]} />
                      }
                      id={"header-game-select"}
                      onChange={(e) => onSelectedGameChange(e.target.value)}
                    >
                        {
                            Object.values(games).map(game =>
                              <MenuItem key={game.codename} value={game.codename}>
                                  <GameIcon fixedWidth={true} game={game} />
                                  <Typography>{game.name}</Typography>
                              </MenuItem>
                            )
                        }
                    </Select>
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
