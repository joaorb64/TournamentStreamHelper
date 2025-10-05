export type TSHCountryInfo = {
    code: string;
    display_name: string;
    en_name: string;
};

export type TSHPlayerInfo = {
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
};

export type TSHTeamInfo = {
    score: number;
    teamName: string;
    player: Record<number, TSHPlayerInfo>;
    losers: boolean;
    color: string;
};

export type TSHScoreInfo = {
    best_of: number;
    best_of_text: string;
    match: string;
    phase: string;
    set_id: number;
    station?: string;
    stream_url?: string;
    team: Record<number, TSHTeamInfo>;
};

export type TSHCharacterBase = {
    codename: string;
    display_name: string;
    en_name: string;
    name: string;
};

export type TSHCharacterSelection = TSHCharacterBase & {
    skin: number; // This is -1 if unset.
};

export type TSHCharacterSelections = Record<number, TSHCharacterSelection>;

export type TSHCharacterDbEntry = TSHCharacterBase & {
    skins: TSHCharacterSkin[];
};

export type TSHCharacterSkin = {
    assets: TSHCharacterSkinAssets;
};

export type TSHCharacterSkinAssets = {
    art?: TSHCharacterSkinAsset;
    "base_files/icon"?: TSHCharacterSkinAsset;
    costume?: TSHCharacterSkinAsset;
    css?: TSHCharacterSkinAsset;
    full?: TSHCharacterSkinAsset;
    profile?: TSHCharacterSkinAsset;
};

export type TSHCharacterSkinAsset = {
    asset: string; // Path to the asset
    average_size?: Point2D;
    image_size?: Point2D;
    rescaling_factor?: number;
    type?: string[];
    uncropped_edge?: string[];
};

export type Point2D = {
    x: number;
    y: number;
};

export type TSHCharacters = Record<string, TSHCharacterSelection>;

export type TSHSetEntrant = {
    gamerTag: string;
    prefix?: string;
    name?: string;
    id: number[];
};

export type TSHSet = {
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
};

export type TSHPlayerDbEntry = {
    controller: string;
    country_code: string;
    custom_textbox: string;
    gamerTag: string;
    mains?: TSHMainsMap;
    name: string;
    prefix: string;
    pronoun: string;
    twitter: string;
};

export type TSHMainsMap = Record<string, TSHMain[]>;

export type TSHMain = [string, number, string];

export type TSHPlayerDb = Record<string, TSHPlayerDbEntry>;

export type TSHState = {
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
};

export const BackendTypes = {};
