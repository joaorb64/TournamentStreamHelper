export const BACKEND_PORT = process.env.NODE_ENV === 'production'
    ? window.location.port
    : 5000;

export const BASE_URL = `http://${window.location.hostname}:${BACKEND_PORT}`


export const inlineFlagWidth = 24;
