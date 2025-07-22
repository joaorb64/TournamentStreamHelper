

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
 * @prop {Object.<number, TSHCharacterSelection>} character
 */
/**
 * @typedef {object} TSHTeamInfo
 * @prop {int} score
 * @prop {string} teamName
 * @prop {Object.<int, TSHPlayerInfo>} player
 */

/** @typedef {object} TSHState very incomplete definition
 * @prop {{
 *   [scoreboard: number]: TSHScoreInfo
 *   ruleset: object
 * }} score
 * @prop {?{
 *     codename?: string
 * }} game
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
 * @typedef {object} TSHCharacterBase
 * @prop {string} codename
 * @prop {string} display_name
 * @prop {string} en_name
 * @prop {string} name
 */

/**
 * @typedef {object} TSHCharacterSelection
 * @extends {TSHCharacterBase}
 * @prop {number} skin This is -1 if unset.
 */

/** @typedef {Object.<string, TSHCharacterDbEntry>} TSHCharacterDb */
/**
 * @typedef {object} TSHCharacterDbEntry
 * @extends {TSHCharacterBase}
 * @prop {TSHCharacterSkin[]} skins
 */

/**
 * @typedef {object} TSHCharacterSkin
 * @property {TSHCharacterSkinAsset[]} assets
 */

/**
 * @typedef {object} TSHCharacterSkinAssets
 * @prop {?TSHCharacterSkinAsset} art
 * @prop {?TSHCharacterSkinAsset} base_files/icon
 * @prop {?TSHCharacterSkinAsset} costume
 * @prop {?TSHCharacterSkinAsset} css
 * @prop {?TSHCharacterSkinAsset} full
 * @prop {?TSHCharacterSkinAsset} profile
 */

/** @typedef Point2D
 *  @prop {number} x
 *  @prop {number} y
 */

/**
 * @typedef {object} TSHCharacterSkinAsset
 * @prop {string} asset Path to the asset
 * @prop {?Point2D} average_size
 * @prop {?Point2D} image_size
 * @prop {?number} rescaling_factor
 * @prop {?string[]} type
 * @prop {?string[]} uncropped_edge
 */

/**
 * @typedef {Object.<string, TSHCharacterSelection>} TSHCharacters
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

/** @typedef {Object.<string, TSHPlayerDbEntry>} TSHPlayerDb */
/**
 * @typedef TSHPlayerDbEntry
 * @property {string} controller
 * @property {string} country_code
 * @property {string} custom_textbox
 * @property {string} gamerTag
 * @property {?TSHMainsMap} mains
 * @property {string} name
 * @property {string} prefix
 * @property {string} pronoun
 * @property {string} twitter
 */

/**
 * @typedef {Object.<string, TSHMain[]>} TSHMainsMap
 */

/**
 * @typedef {[string, number, string]} TSHMain
 */

/**
 * @typedef {Object.<string, TSHPlayerDbEntry>} TSHPlayerDb
 */

export const BackendTypes = {};
