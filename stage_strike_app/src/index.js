import React from 'react';
import ReactDOM from 'react-dom';
import './index.css';
import StageStrikePage from './StageStrikePage';
import reportWebVitals from './reportWebVitals';

import {BrowserRouter, Navigate, Route, Routes} from "react-router-dom";
import ScoreboardPage from "./ScoreboardPage";
import {darkTheme} from "./themes";
import {ThemeProvider} from "@mui/material/styles";
import {CssBaseline} from "@mui/material";

ReactDOM.render(
  <React.StrictMode>
      <ThemeProvider theme={darkTheme}>
          <CssBaseline />
          <BrowserRouter>
              <Routes>
                  <Route
                      path="/stage-strike-app"
                      element={<StageStrikePage />}
                  />
                  <Route
                      path="/scoreboard"
                      element={<ScoreboardPage />}
                  />
                  <Route
                      path="*"
                      element={<Navigate to={"/stage-strike-app"} replace={true}/>}
                  />
              </Routes>
          </BrowserRouter>
      </ThemeProvider>
  </React.StrictMode>,
  document.getElementById('root')
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
