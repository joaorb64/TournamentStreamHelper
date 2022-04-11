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
      translations: require("./locales/jp.json"),
    },
    fr: {
      translations: require("./locales/fr.json"),
    },
  },
  detection: {
    order: ["querystring", "navigator"],
    lookupQuerystring: "lng",
  },
  ns: ["translations"],
  defaultNS: "translations",
  debug: true,
});

i18n.languages = ["en", "pt", "es", "ja", "fr"];

export default i18n;
