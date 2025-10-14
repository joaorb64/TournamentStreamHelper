import {BASE_URL} from "./env";
import {useState} from "react";

/** @param {{game: TSHGameInfo, fixedWidth: boolean}} props */
export function GameIcon({game, fixedWidth=false, ...rest}) {
  const {errored, setErrored} = useState(false);

  const logoUrl = `${BASE_URL}/user_data/games/${game.codename}/base_files/logo.png`;
  return <div {...rest}>
    {errored
      ? <span>{game.codename}</span>
      : <img
        alt="Game logo"
        src={logoUrl}
        {...(fixedWidth ? {width: 48} : {height: 48})}
        onError={(e) => setErrored(true)}
      />
    }
  </div>
}
