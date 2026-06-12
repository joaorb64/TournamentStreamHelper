import i18n from "i18next";
import LanguageDetector from "i18next-browser-languagedetector";
import en from "./locales/en.json";
import ptBR from "./locales/pt-BR.json";
import es from "./locales/es.json";
import ja from "./locales/ja.json";
import fr from "./locales/fr.json";
import it from "./locales/it.json";
import zhCN from "./locales/zh-CN.json";
import zhTW from "./locales/zh-TW.json";

i18n.use(LanguageDetector).init({
  fallbackLng: ["en"],
  resources: {
    en:      { translations: en },
    "pt-BR": { translations: ptBR },
    es:      { translations: es },
    ja:      { translations: ja },
    fr:      { translations: fr },
    it:      { translations: it },
    "zh-CN": { translations: zhCN },
    "zh-TW": { translations: zhTW },
  },
  detection: {
    order: ["querystring", "navigator"],
    lookupQuerystring: "lng",
  },
  ns: ["translations"],
  defaultNS: "translations",
  debug: false,
  interpolation: { escapeValue: false },
});

export const SUPPORTED_LANGUAGES = [
  { code: "en",    label: "EN" },
  { code: "pt-BR", label: "PT" },
  { code: "es",    label: "ES" },
  { code: "ja",    label: "JA" },
  { code: "fr",    label: "FR" },
  { code: "it",    label: "IT" },
  { code: "zh-CN", label: "简中" },
  { code: "zh-TW", label: "繁中" },
];

export default i18n;
