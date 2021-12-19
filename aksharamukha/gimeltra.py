#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright © 2021 Adam Twardoch, MIT license
# Adapted from : https://github.com/twardoch/gimeltra

# Modified by Vinodh Rajan

import os
import regex as re
from pathlib import Path
import logging
import json
import langcodes
from fontTools import unicodedata as ucd
from collections import Counter

cwd = Path(Path(__file__).parent)

class Transliterator(object):
    def __init__(self):
        with open(Path(cwd, "gimeltra_data.json"), "r", encoding="utf-8") as f:
            data = json.load(f)
        self.db = data['ssub']
        self.db_ccmp = data['ccmp']
        self.db_simplify = data['simp']
        self.db_fina = data['fina']
        self.db_liga = data['liga']

    def auto_script(self, text):
        sc_count = Counter([ucd.script(c) for c in text])
        sc = sc_count.most_common(1)[0][0]
        if not sc:
            sc = 'Zyyy'
        return sc

    def _tr(self, text, sc, to_sc):
        t = text
        if sc != 'Latn':
            t = self._preprocess(t, sc)
        t = self._convert(t, sc, to_sc)
        t = self._postprocess(t, to_sc)
        return t

    def _preprocess(self, text, sc):
        t = text
        for rule_i, rule_o in self.db_ccmp.get(sc, {}).items():
            t = t.replace(rule_i, rule_o)
        t = ucd.normalize('NFD', t)

        t = re.sub(r"(?![\u05C4\u0308])\p{M}","", t)

        logging.debug(f"Pre: {list(t)}")
        return t

    def _postprocess(self, text, sc):
        t = text
        for rule_i, rule_o in self.db_fina.get(sc, {}).items():
            t = re.subf(fr"(\p{{L}})({rule_i})([^\p{{L}}])", f"{{1}}{rule_o}{{3}}", t)
            t = re.subf(fr"(\p{{L}})({rule_i})$", f"{{1}}{rule_o}", t)
        for rule_i, rule_o in self.db_liga.get(sc, {}).items():
            t = t.replace(rule_i, rule_o)
        logging.debug(f"Post: {list(t)}")

        return t

    def _to_latin(self, text, sc, to_sc):
        chars = list(self.db[sc]["Latn"])
        chars.sort(key=len, reverse=True)
        for char in chars:
            text = text.replace(char, self.db[sc]["Latn"][char])

        return text

    def _from_latin(self, text, sc, to_sc):
        chars = list(self.db["Latn"][to_sc])
        chars.sort(key=len, reverse=True)

        if sc != 'Latn':
            chars_missing = set(list(self.db[sc]["Latn"].values())) - set(chars)
            # print("Missing chars ")
            # print(chars_missing)

        if sc == 'Latn':
            chars_missing = set(self.db_simplify) - set(list(self.db[to_sc]["Latn"].values()))
            # print("Missing chars ")
            # print(chars_missing)

        for char in chars_missing:

            if char in self.db_simplify:
                text = text.replace(char, self.db_simplify[char])

        for char in chars:
            text = text.replace(char, self.db["Latn"][to_sc][char])

        return text

    def _convert(self, text, sc, to_sc):
        if to_sc == 'Latn':
            return self._to_latin(text, sc, to_sc)
        elif sc == 'Latn':
            return self._from_latin(text, sc, to_sc)
        else:
            txt_latn = self._to_latin(text, sc, to_sc)
            return self._from_latin(txt_latn, sc, to_sc)

    def tr(self, text, sc=None, to_sc='Latn'):
        if not sc:
            sc = self.auto_script(text)
        logging.debug({
            'script': sc, 'to_script': to_sc,
        })
        logging.debug(f"Text: {list(text)}")
        if sc != to_sc:
            res = self._tr(text, sc, to_sc)
        else:
            res = text
        return res

def tr(text, sc=None, to_sc='Latn'):
    tr = Transliterator()
    print(sc +' ' + to_sc)
    if sc != to_sc:
        return tr.tr(text, sc, to_sc)
    else:
        return text

