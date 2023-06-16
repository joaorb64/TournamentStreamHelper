import re
import unicodedata
from typing import Union, Dict


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
    badWordList = []
    badWordTrie = Trie()
    pattern: str = ""

    def LoadBadWordList():
        TSHBadWordFilter.badWordList = open(
            "./assets/bad_word_list.txt", 'r', encoding="utf-8").read().splitlines()

        for index, word in enumerate(TSHBadWordFilter.badWordList):
            word = re.sub("a", "(a|4|\@)", word)
            word = re.sub("i", "(i|1|l)", word)
            word = re.sub("o", "(o|0|\@)", word)
            word = re.sub("l", "(l|i)", word)
            word = re.sub("e", "(e|3)", word)
            word = re.sub("s", "(s|\$|5)", word)
            word = re.sub("t", "(t|7)", word)
            TSHBadWordFilter.badWordList[index] = word

        for word in TSHBadWordFilter.badWordList:
            TSHBadWordFilter.badWordTrie.insert(word)

        TSHBadWordFilter.pattern = TSHBadWordFilter.badWordTrie.build_regex_pattern()

    def CensorString(value: str):
        oldValue = value
        testStrings = []

        # test whole string
        testStrings.append(remove_accents_lower(value))

        # ignore dividers
        dividers = [" ", "_", ",", ".", "/", "-", "\\", "*"]
        val = remove_accents_lower(value)
        for divider in dividers:
            val = val.replace(divider, "")
        testStrings.append(val)

        for testVal in testStrings:
            if len(testVal) <= 1:
                continue

            matches = TSHBadWordFilter.pattern.finditer(testVal)
            # matches = re.finditer(
            #     "|".join([f"({w})" for w in TSHBadWordFilter.badWordList]), testVal, flags=re.IGNORECASE)

            for match in matches:
                print(match.group())
                print(match.start())
                print(match.end())
                value = "***"
                break
            if value == "***":
                break

        if value != oldValue:
            print(oldValue, "->", value)

        return value

    def CensorDict(dictionary: dict):
        for key, value in dictionary.items():
            if isinstance(value, dict):
                TSHBadWordFilter.CensorDict(value)
            else:
                # Modify the leaf value
                if type(value) == str:
                    dictionary[key] = TSHBadWordFilter.CensorString(value)

    def Censor(value: Union[Dict, str, None]):
        if value == None:
            return value

        if type(value) == str:
            value = TSHBadWordFilter.CensorString(value)
        if isinstance(value, dict):
            TSHBadWordFilter.CensorDict(value)

        return value


TSHBadWordFilter.LoadBadWordList()
