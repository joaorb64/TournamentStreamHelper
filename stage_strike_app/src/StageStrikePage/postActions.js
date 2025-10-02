import {BACKEND_PORT, BASE_URL} from "../env";

export function ConfirmClicked() {
    fetch(
        `${BASE_URL}/stage_strike_confirm_clicked`,
        {
            method: "POST",
            contentType: "application/json",
        }
    );
}

export function MatchWinner(id) {
    fetch(
        `${BASE_URL}/stage_strike_match_win`,
        {
            method: "POST",
            contentType: "application/json",
            body: JSON.stringify({
                winner: id,
            }),
        }
    );
}

export function SetGentlemans(value) {
    fetch(
        `${BASE_URL}/stage_strike_set_gentlemans`,
        {
            method: "POST",
            contentType: "application/json",
            body: JSON.stringify({ value: value }),
        }
    );
}

export function RestartStageStrike() {
    fetch(`${BASE_URL}/stage_strike_reset`, {
        method: "POST",
        contentType: "application/json",
    });
}

export function StageClicked(/** object */ stage) {
    fetch(
        `${BASE_URL}/stage_strike_stage_clicked`,
        {
            method: "POST",
            body: JSON.stringify(stage),
            contentType: "application/json",
        }
    );
}

export function Undo() {
    fetch(`${BASE_URL}/stage_strike_undo`, {
        method: "POST",
        contentType: "application/json",
    });
}

export function Redo() {
    fetch(`${BASE_URL}/stage_strike_redo`, {
        method: "POST",
        contentType: "application/json",
    });
}

export function ReportRpsWin(/** number */ winner) {
  fetch(
    "http://" +
    window.location.hostname +
    `:${BACKEND_PORT}/stage_strike_rps_win`,
    {
      method: "POST",
      contentType: "application/json",
      body: JSON.stringify({
        winner: winner
      }),
    }
  )
}

