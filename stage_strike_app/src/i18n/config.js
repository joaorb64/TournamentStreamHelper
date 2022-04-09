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
  },
  detection: {
    order: ["querystring", "navigator"],
    lookupQuerystring: "lng",
  },
  ns: ["translations"],
  defaultNS: "translations",
});

i18n.languages = ["en", "pt", "es", "ja"];

export default i18n;
