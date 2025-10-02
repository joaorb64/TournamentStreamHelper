import {BASE_URL} from "./env";
import ReactDOMServer from "react-dom/server";

/** @param {{game: TSHGameInfo, fixedWidth: boolean}} props */
export function GameIcon({game, fixedWidth=false, ...rest}) {
  const logoUrl = `${BASE_URL}/user_data/games/${game.codename}/base_files/logo.png`;
  return <div {...rest}>
    <img
      alt="Game logo"
      src={logoUrl}
      {...(fixedWidth ? {width: 48} : {height: 48})}
      onError={(e) => e.nativeEvent.target.replace(ReactDOMServer.renderToStaticMarkup(<span>game.name</span>))}
    />
  </div>
}
