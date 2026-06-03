import i18n from "i18next";
import LanguageDetector from "i18next-browser-languagedetector";

i18n.use(LanguageDetector).init({
  fallbackLng: ["en"],
  resources: {
    en: {
      translations: require("./locales/en.json"),
    },
    pt: {
      translations: require("./locales/pt.json"),
    },
    es: {
      translations: require("./locales/es.json"),
    },
    ja: {
      translations: require("./locales/ja.json"),
    },
    fr: {
      translations: require("./locales/fr.json"),
    },
    "zh-CN": {
      translations: require("./locales/zh-CN.json"),
    },
    "zh-TW": {
      translations: require("./locales/zh-TW.json"),
    },
  },
  detection: {
    order: ["querystring", "navigator"],
    lookupQuerystring: "lng",
  },
  ns: ["translations"],
  defaultNS: "translations",
  debug: true,
  interpolation: { escapeValue: false },
});

i18n.languages = ["en", "pt", "es", "ja", "fr", "zh-CN", "zh-TW"];

export default i18n;
