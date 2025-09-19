import React from 'react';

export const BACKEND_PORT = process.env.NODE_ENV === 'production'
    ? window.location.port
    : 5000;
