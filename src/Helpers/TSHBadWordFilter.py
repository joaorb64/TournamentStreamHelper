import re
import unicodedata
from typing import Union, Dict
from ..SettingsManager import SettingsManager
import json
from .TSHLocaleHelper import TSHLocaleHelper
import traceback
import os
from collections import defaultdict
from typing import List, Set, Tuple
from loguru import logger


def remove_accents_lower(input_str):
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return u"".join([c for c in nfkd_form if not unicodedata.combining(c)]).lower()


class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end_of_word = False


class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word):
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end_of_word = True

    def build_regex_pattern(self):
        regex_strings = []
        self._build_regex_strings(self.root, '', regex_strings)
        pattern = '|'.join(regex_strings)
        return re.compile(pattern)

    def _build_regex_strings(self, node, prefix, regex_strings):
        if node.is_end_of_word:
            regex_strings.append(prefix)
        for char, child_node in node.children.items():
            self._build_regex_strings(child_node, prefix + char, regex_strings)


class TSHBadWordFilter():
    badWordTries = defaultdict(Trie)
    patterns = defaultdict(re.Pattern)
    whiteList = []
    blackList = []

    # Pre-compiled at class level — compiled once, reused forever
    _LEET_PATTERN = re.compile(r'[ailuvoest]')
    _LEET_MAP = {
        'a': r'(a|4|@)',
        'i': r'(i|1|l|!)',
        'l': r'(l|1|i|!)',
        'u': r'(u|v)',
        'v': r'(v|u)',
        'o': r'(o|0|@)',
        'e': r'(e|3)',
        's': r'(s|\$|5)',
        't': r'(t|7)',
    }

    def _apply_leet(word: str) -> str:
        return TSHBadWordFilter._LEET_PATTERN.sub(lambda m: TSHBadWordFilter._LEET_MAP[m.group()], word)

    def LoadBadWordList():
        import threading

        def _worker():
            langs = defaultdict(set)
            try:
                for f in os.listdir("./assets/ngword/"):
                    if not f.endswith(".txt"):
                        continue
                    words = open(f"./assets/ngword/{f}", 'r', encoding="utf-16").read().splitlines()
                    langs[f.split(".")[0]] = {TSHBadWordFilter._apply_leet(w) for w in words}
            except:
                logger.error(traceback.format_exc())

            for langkey, lang in langs.items():
                for word in lang:
                    TSHBadWordFilter.badWordTries[langkey].insert(word)
                TSHBadWordFilter.patterns[langkey] = \
                    TSHBadWordFilter.badWordTries[langkey].build_regex_pattern()

        threading.Thread(target=_worker, daemon=True).start()

    def CensorString(value: str, playerCountry: str = None):
        langTests = set(["common"])

        # Saving extra languages as [language, country]
        extraLanguages: Set[Tuple[str]] = set()

        userLocale = TSHLocaleHelper.programLocale.lower()

        # Add program language
        if "-" in userLocale:
            extraLanguages.add(
                (userLocale.split("-")[0], userLocale.split("-")[-1]))
        else:
            extraLanguages.add((userLocale, None))

        # Add languages spoken in player's country
        if playerCountry is not None:
            langs = TSHLocaleHelper.GetCountrySpokenLanguages(
                playerCountry.upper())
            for lang in langs:
                extraLanguages.add((lang, playerCountry))

        # Process extra languages
        for lang, country in extraLanguages:
            lang = lang.lower()

            if country is not None:
                country = country.lower()

                # Test language-country
                canonical = f"{lang}-{country}"
                if canonical in TSHBadWordFilter.patterns:
                    langTests.add(canonical)
                    continue

                # Test language-continent
                if country:
                    regionalLang = None
                    continent = TSHLocaleHelper.GetCountryContinent(country)

                    if continent in ["NA", "SA"]:
                        regionalLang = f"{lang}-americas"

                    if regionalLang and regionalLang in TSHBadWordFilter.patterns:
                        langTests.add(regionalLang)
                        continue

            # Test language only
            if lang in TSHBadWordFilter.patterns:
                langTests.add(lang)
                continue

        logger.info(f"TSHBadWordFilter: using filters [{', '.join(langTests)}]")

        dividers = [" ", "_", ",", ".", "/", "-", "\\", "*"]
        testString = remove_accents_lower(value)
        stringStart = 0

        newString = ""

        for characterPos, character in enumerate(testString):
            if character in dividers:
                substring = testString[stringStart:characterPos]

                if len(substring) > 0:
                    matched = False

                    if substring in TSHBadWordFilter.blackList:
                        newString += "***"
                        matched = True
                    elif substring in TSHBadWordFilter.whiteList:
                        pass
                    else:
                        for lang in langTests:
                            if lang not in TSHBadWordFilter.patterns:
                                continue

                            match = TSHBadWordFilter.patterns[lang].match(
                                substring)

                            if match:
                                newString += "***"
                                matched = True
                                break
                    if not matched:
                        newString += value[stringStart:characterPos]

                newString += character
                stringStart = characterPos+1

        substring = testString[stringStart:]

        if len(substring) > 0:
            matched = False

            if substring in TSHBadWordFilter.blackList:
                newString += "***"
                matched = True
            elif substring in TSHBadWordFilter.whiteList:
                pass
            else:
                for lang in langTests:
                    if lang not in TSHBadWordFilter.patterns:
                        continue

                    match = TSHBadWordFilter.patterns[lang].match(
                        substring)

                    if match:
                        newString += "***"
                        matched = True
                        break
            if not matched:
                newString += value[stringStart:]

        if value != newString:
            logger.info(f"{value} -> {newString}")

        return newString

    def CensorDict(dictionary: dict):
        for key, value in dictionary.items():
            if isinstance(value, dict):
                TSHBadWordFilter.CensorDict(value)
            else:
                # Modify the leaf value
                if type(value) == str:
                    dictionary[key] = TSHBadWordFilter.CensorString(value)

    def Censor(value: Union[Dict, str, None], countryCode2: str = None):
        if SettingsManager.Get("general.profanity_filter", True) != True:
            return value

        if value == None:
            return value

        if type(value) == str:
            value = TSHBadWordFilter.CensorString(value, countryCode2)
        if isinstance(value, dict):
            TSHBadWordFilter.CensorDict(value)

        return value

    def LoadWordList(file):
        try:
            if not os.path.exists(f"./user_data/{file}"):
                with open(f"./user_data/{file}", 'w', encoding="utf-8") as f:
                    f.write("")
            words = open(f"./user_data/{file}", 'r',
                         encoding="utf-8").read().splitlines()
            return set([remove_accents_lower(w) for w in words if len(w) > 0])
        except:
            logger.error(traceback.format_exc())


TSHBadWordFilter.LoadBadWordList()
TSHBadWordFilter.whiteList = TSHBadWordFilter.LoadWordList(
    "badword_whitelist.txt")
TSHBadWordFilter.blackList = TSHBadWordFilter.LoadWordList(
    "badword_blacklist.txt")
