export interface TSHCountryInfo {
    code: string;
    display_name: string;
    en_name: string;
}

export interface TSHPlayerInfo {
    id?: [number, number];
    city?: string;
    state?: TSHCountryInfo;
    country?: TSHCountryInfo;
    online_avatar?: string;
    name: string;
    mergedName: string;
    mergedOnlyName: string;
    real_name: string;
    seed: number;
    pronoun?: string;
    sponsor_logo?: string;
    team?: string;
    twitter?: string;
    character: TSHCharacterSelections;
}

export interface TSHTeamInfo {
    score: number;
    teamName: string;
    player: Record<number, TSHPlayerInfo>;
    losers: boolean;
    color: string;
}

export interface TSHScoreInfo {
    best_of: number;
    best_of_text: string;
    match: string;
    phase: string;
    set_id: number;
    station?: string;
    stream_url?: string;
    team: Record<number, TSHTeamInfo>;
}

export interface TSHCharacterBase {
    codename: string;
    display_name: string;
    en_name: string;
    name: string;
}

export interface TSHCharacterSelection extends TSHCharacterBase {
    skin: number; // This is -1 if unset.
}

export type TSHCharacterSelections = Record<number, TSHCharacterSelection>;

export interface TSHCharacterDb {
    [codename: string]: TSHCharacterDbEntry;
}

export interface TSHCharacterDbEntry extends TSHCharacterBase {
    skins: TSHCharacterSkin[];
}

export interface TSHCharacterSkin {
    assets: TSHCharacterSkinAssets;
}

export interface TSHCharacterSkinAssets {
    art?: TSHCharacterSkinAsset;
    "base_files/icon"?: TSHCharacterSkinAsset;
    costume?: TSHCharacterSkinAsset;
    css?: TSHCharacterSkinAsset;
    full?: TSHCharacterSkinAsset;
    profile?: TSHCharacterSkinAsset;
}

export interface TSHCharacterSkinAsset {
    asset: string; // Path to the asset
    average_size?: Point2D;
    image_size?: Point2D;
    rescaling_factor?: number;
    type?: string[];
    uncropped_edge?: string[];
}

export interface Point2D {
    x: number;
    y: number;
}

export type TSHCharacters = Record<string, TSHCharacterSelection>;

export interface TSHSetEntrant {
    gamerTag: string;
    prefix?: string;
    name?: string;
    id: number[];
}

export interface TSHSet {
    bracket_type: string;
    entrants: [TSHSetEntrant, TSHSetEntrant];
    id: number;
    isOnline?: boolean;
    isPools: boolean;
    p1_name: string;
    p1_seed?: number;
    p2_name: string;
    p2_seed?: number;
    round: string;
    round_name: string;
    station?: string;
    stream?: string;
    team1score: number;
    team2score: number;
    tournament_phase?: string;
}

export interface TSHPlayerDbEntry {
    controller: string;
    country_code: string;
    custom_textbox: string;
    prefixed_tag: string;
    gamerTag: string;
    mains?: TSHMainsMap;
    name: string;
    prefix: string;
    pronoun: string;
    twitter: string;
}

export type TSHCountryCode = string;

export interface TSHCountryDb {
    [country_code: TSHCountryCode]: TSHCountryInfo
}

export type TSHMainsMap = Record<string, TSHMain[]>;

export type TSHMain = [string, number, string];

export type TSHPlayerDb = Record<string, TSHPlayerDbEntry>;

export interface TSHState {
    score: {
        [scoreboard: number]: TSHScoreInfo;
        ruleset: object;
    };
    game?: {
        name: string;
        smashgg_id: number;
        logo?: string;
        codename?: string;
    };
    tournamentInfo: {
        tournamentName?: string;
        address?: string;
        eventName?: string;
        shortLink?: string;
        endAt?: string;
        startAt?: string;
        eventEndAt?: string;
        eventStartAt?: string;
        initial_load?: boolean;
        numEntrants?: number;
    };
}

export interface TSHGamesDb {
    [codename: string]: TSHGameInfo
}

export interface TSHGameInfo{
    challonge_game_id: number,
    has_stages: boolean
    has_variants: boolean
    locale: null | object
    name: string
    smashgg_game_id: number
    codename: string // This one isn't in the backend responses, I add it from the key.
}

export interface Delta {
    action: DeltaOpType;
    path: (string | number)[];
    type: string;
    value: any;
}

export type DeltaOpType =
     "type_changes"
   | "values_changed"
   | "dictionary_item_added"
   | "dictionary_item_removed"
   | "iterable_item_added"
   | "iterable_item_removed"
   | "attribute_added"
   | "attribute_removed"
   | "set_item_added"
   | "set_item_removed"
   | "repetition_change";
