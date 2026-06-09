import { useState } from "react";
import {
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Box,
} from "@mui/material";
import { Language as LanguageIcon } from "@mui/icons-material";
import i18n, { SUPPORTED_LANGUAGES } from "../i18n/config";
import { languageSettings, saveLanguageSettings } from "./languageSettings";

function resolveCode(lang) {
  if (SUPPORTED_LANGUAGES.find(l => l.code === lang)) return lang;
  const short = lang.split(/[-_]/)[0];
  return SUPPORTED_LANGUAGES.find(l => l.code === short)?.code ?? 'en';
}

export function LanguageSelector({ playerLanguages, currPlayer, selectedStage }) {
  const [settings, setSettings] = useState(() => ({ ...languageSettings }));

  const isSharedStep = selectedStage !== null || currPlayer === -1;
  const autoLang = (!isSharedStep && currPlayer >= 0)
    ? resolveCode(playerLanguages?.[currPlayer] ?? settings.language)
    : resolveCode(settings.language);

  const displayLang = settings.usePlayerLanguage ? autoLang : resolveCode(settings.language);

  const applyLang = (lang) => {
    i18n.changeLanguage(lang);
  };

  const handleLangChange = (e) => {
    const lang = e.target.value;
    const next = { ...settings, language: lang };
    setSettings(next);
    saveLanguageSettings({ language: lang });
    if (!settings.usePlayerLanguage) applyLang(lang);
  };

  const handleAutoToggle = (e) => {
    const usePlayer = e.target.checked;
    const next = { ...settings, usePlayerLanguage: usePlayer };
    setSettings(next);
    saveLanguageSettings({ usePlayerLanguage: usePlayer });
    applyLang(usePlayer ? autoLang : resolveCode(settings.language));
  };

  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        gap: 0.5,
        bgcolor: 'background.paper',
        borderRadius: 1,
        px: 1,
        py: 0.5,
        opacity: 0.9,
      }}
    >
      <LanguageIcon fontSize="small" sx={{ color: 'text.secondary' }} />
      <Select
        value={displayLang}
        onChange={handleLangChange}
        disabled={settings.usePlayerLanguage}
        size="small"
        variant="standard"
        disableUnderline
        sx={{ minWidth: 48, fontSize: '0.85rem' }}
      >
        {SUPPORTED_LANGUAGES.map(l => (
          <MenuItem key={l.code} value={l.code}>{l.label}</MenuItem>
        ))}
      </Select>
      <FormControlLabel
        control={
          <Switch
            size="small"
            checked={settings.usePlayerLanguage}
            onChange={handleAutoToggle}
          />
        }
        label="Auto"
        labelPlacement="start"
        sx={{ ml: 0.5, mr: 0, '& .MuiFormControlLabel-label': { fontSize: '0.75rem' } }}
      />
    </Box>
  );
}
