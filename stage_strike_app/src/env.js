// In production, the app is served by TSH itself so same-origin is correct.
// In dev, the Vite proxy forwards backend requests to TSH_PORT, so same-origin works there too.
export const BACKEND_PORT = window.location.port;

export const BASE_URL = `http://${window.location.hostname}:${BACKEND_PORT}`


export const inlineFlagWidth = 24;
