const STORAGE_KEY = 'tsh_lang_settings';

function load() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
  } catch {
    return {};
  }
}

const stored = load();

export const languageSettings = {
  language: stored.language || 'en',
  usePlayerLanguage: stored.usePlayerLanguage ?? true,
};

export function saveLanguageSettings(updates) {
  Object.assign(languageSettings, updates);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(languageSettings));
}
