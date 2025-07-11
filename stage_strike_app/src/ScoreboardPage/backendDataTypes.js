

/**
 * @typedef {object} TSHCountryInfo
 * @prop {string} code
 * @prop {string} display_name
 * @prop {string} en_name
 */
/**
 * @typedef {object} TSHPlayerInfo
 * @prop {?[int, int]} id
 * @prop {?string} city
 * @prop {?TSHCountryInfo} state
 * @prop {?TSHCountryInfo} country
 * @prop {?string} online_avatar
 * @prop {string} name
 * @prop {string} mergedName
 * @prop {string} mergedOnlyName
 * @prop {string} real_name
 * @prop {int} seed
 * @prop {string=} pronoun
 * @prop {?string} sponsor_logo
 * @prop {?string} team
 * @prop {?string} twitter
 * @prop {Object.<number, TSHCharacter>} character
 */
/**
 * @typedef {object} TSHTeamInfo
 * @prop {int} score
 * @prop {string} teamName
 * @prop {Object.<int, TSHPlayerInfo>} player
 */
/**
 * @typedef {object} TSHScoreInfo
 * @prop {int} best_of
 * @prop {string} best_of_text
 * @prop {string} match
 * @prop {string} phase
 * @prop {int} set_id
 * @prop {?string} station
 * @prop {?string} stream_url
 * @prop {Object.<int, TSHTeamInfo>} team
 */
/**
 * @typedef {object} TSHCharacter
 * @prop {string} codename
 * @prop {string} display_name
 * @prop {string} en_name
 * @prop {string} name
 */

/**
 * @typedef {Object.<string, TSHCharacter>} TSHCharacters
 */

/**
 * @typedef {object} TSHSetEntrant
 * @property {string} gamerTag
 * @property {?string} prefix
 * @property {?string} name
 * @property {int[]} id
 */

/**
 * @typedef {object} TSHSet
 * @property {string} bracket_type
 * @property {[TSHSetEntrant, TSHSetEntrant]} entrants
 * @property {int} id
 * @property {?boolean} isOnline
 * @property {boolean} isPools
 * @property {string} p1_name
 * @property {?int} p1_seed
 * @property {string} p2_name
 * @property {?int} p2_seed
 * @property {string} round
 * @property {string} round_name
 * @property {?string} station
 * @property {?string} stream
 * @property {int} team1score
 * @property {int} team2score
 * @property {?string} tournament_phase
 */

export const BackendTypes = {};
