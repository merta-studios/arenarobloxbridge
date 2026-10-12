#!/usr/bin/env python3
"""Umlaut-Werkzeug der 7.9.2-Session: ae/oe/ue/s in echte Umlaute ueberfuehren.

Aufruf (ohne --write passiert nichts, es wird nur gezaehlt):
  .venv/bin/python developer/tools/german_umlauts.py app/ArenaBridge.ps1 --report /tmp/rep.txt
  .venv/bin/python developer/tools/german_umlauts.py README.md --all-text --no-bom --write
Geprueft wird nur Text und Kommentar; Code-Bezeichner und englische Begriffe
bleiben stehen (SKIP, camelCase-Regel, --code-words-from).

Regeln (bewusst streng, damit NICHTS Kaputtes entsteht):
  1. Nur Text- und Kommentarbereiche werden angefasst - niemals Code.
  2. Ein Wort wird nur ersetzt, wenn die Umlaut-/ss-Form belegbar richtig ist:
       a) die ganze Form steht im deutschen Woerterbuch, oder
       b) die Form ist ein Kompositum aus mindestens zwei Woerterbuchwoertern
          (>= 3 Zeichen je Teil, dazwischen nur einzelne Binde-Buchstaben), oder
       c) die Form ist Woerterbuchwort + deutsche Endung (schließend+e), oder
       d) das Wort steht in FORCE (einzeln geprueft).
  3. "ss" wird nur dort zu "ß", wo die ß-Form belegbar ist. "muss", "dass",
     "Prozess" und englische Woerter bleiben unveraendert.
  4. Woerter, die auch im Code vorkommen (Bezeichner, IDs) bleiben unangetastet.
"""
from __future__ import annotations

import argparse
import importlib.util
import itertools
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

_spec = importlib.util.spec_from_file_location('ps_text_tokens', str(HERE / 'ps_text_tokens.py'))
ps_text_tokens = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ps_text_tokens)
segments = ps_text_tokens.segments

WORD_RE = re.compile(r'[A-Za-zÄÖÜäöüß]{3,}')

UMLAUT_MAP = {'ae': 'ä', 'oe': 'ö', 'ue': 'ü'}

# Englische/Kunst-Woerter und Bezeichner, die nie angefasst werden.
SKIP = set("""
true value sessionid asset message query queue assetid request info note
does doesn unique guess guesses guessed guessing sequence sequential
issue issues due blue hue quest venue continues goes zeroes opaque
coerced consequential frequently portuguese rescue requests requested
requesting enqueued queued dequeue segoe aep nvalue nvalues nzeroes
upvalue upvalues ncontinue nrequesting nmaxvalue getvalue httpwebrequest
requestasync requestkey unguessable assets session progress pass passes
glass class cross press process unless plus status bonus access asset
assets mess messung messen misst messwerte gemessen gemessene gemessenen
bla bla bla
""".split())

# Einzeln geprueft: Woerter, die die Regeln nicht sicher ableiten koennen.
# Links steht die alte Schreibweise, rechts die gepruefte richtige Form.
FORCE_MAP = {
    'Fenstergroesse': 'Fenstergröße', 'Pixelgroessen': 'Pixelgrößen',
    'Bildgroesse': 'Bildgröße', 'Startgroesse': 'Startgröße', 'Zellgroesse': 'Zellgröße',
    'Wasserhoehe': 'Wasserhöhe', 'Fuehlhoehe': 'Fühlhöhe', 'Fuellgradient': 'Füllgradient',
    'Groessenbremse': 'Größenbremse', 'Groessenheuristiken': 'Größenheuristiken',
    'Schluesselpruefung': 'Schlüsselprüfung', 'Sitzungsschluessel': 'Sitzungsschlüssel',
    'Antwortschluessel': 'Antwortschlüssel', 'zugemuellt': 'zugemüllt',
    'entsaettigte': 'entsättigte', 'ausgeloesst': 'ausgelöst',
    'rueckgeben': 'rückgeben', 'rueckgibt': 'rückgibt',
    'Blockoutwuensche': 'Blockoutwünsche', 'RUECKKANAL': 'RÜCKKANAL',
    'Rueck': 'Rück', 'Loesch': 'Lösch', 'Gezaehle': 'Gezähle',
    'Umleitflaeche': 'Umleitfläche', 'ultraduennen': 'ultradünnen',
    'unitaeres': 'unitäres', 'Prueflauf': 'Prüflauf', 'Pruef': 'Prüf',
    'veroeffent': 'veröffent', 'Aufaeum': 'Aufräum', 'Laueft': 'Läuft',
    'ZURUECKgesetzt': 'ZURÜCKgesetzt', 'haert': 'härt', 'gepraeft': 'geprüft',
    'zouverlaessig': 'zuverlässig', 'aufwaechsen': 'aufwachsen',
    'Kaerten': 'Karten', 'Zusaetz': 'Zusatz', 'Flaeeche': 'Fläche',
    'EMPFoeHLEN': 'EMPFOHLEN',
}


SUFFIXES = ('ungen', 'endem', 'enden', 'ender', 'endes', 'ung', 'lich', 'liche',
            'lichen', 'licher', 'liches', 'keit', 'keiten', 'ung', 'em', 'en',
            'er', 'es', 'et', 'e', 'st', 'te', 'ten', 't', 's', 'n')


def umlaut_form(word: str):
    """ae/oe/ue -> ä/ö/ü (Gross-/Kleinschreibung erhalten) + Aenderungspositionen."""
    out = list(word)
    changed = set()
    i = 0
    while i < len(out) - 1:
        pair = out[i].lower() + out[i + 1].lower()
        if pair in UMLAUT_MAP and out[i].isalpha() and out[i + 1].isalpha():
            repl = UMLAUT_MAP[pair]
            if out[i].isupper():
                repl = repl.upper()
            out[i] = repl
            del out[i + 1]
            changed.add(i)
            i += 1
            continue
        i += 1
    return ''.join(out), changed


def ss_variants(word: str):
    """Alle Formen, in denen einzelne 'ss' durch 'ß' ersetzt sind (max. 3 Stellen)."""
    positions = [m.start() for m in re.finditer('ss', word.lower())]
    if not positions:
        return []
    positions = positions[:3]
    out = []
    for r in range(1, len(positions) + 1):
        for combo in itertools.combinations(positions, r):
            chars = list(word)
            for pos in sorted(combo, reverse=True):
                chars[pos:pos + 2] = ['ß']
            out.append(''.join(chars))
    return out


class Converter:
    def __init__(self, dictionary: set[str], code_words: set[str]):
        self.dict = dictionary
        self.code_words = code_words
        # Woerterbuch nach Laenge, fuer die Kompositum-Zerlegung.
        self.known = {w for w in dictionary if len(w) >= 3 and w.isalpha()}

    # ---- Zerlegung -----------------------------------------------------
    def compound(self, word: str) -> bool:
        """Wort = >=2 Woerterbuchwoerter; dazwischen hoechstens ein Binde-Buchstabe.

        Der Binde-Buchstabe muss zwischen zwei Woertern stehen - ein Wortrest,
        der nur uebersprungen wird (tex|t|uell+e), zaehlt nicht."""
        low = word.lower()
        n = len(low)
        seen: dict[tuple[int, int], bool] = {}

        def piece_at(start: int) -> list[int]:
            return [end for end in range(n, start + 2, -1) if low[start:end] in self.known]

        def solve(start: int, pieces: int) -> bool:
            if start == n:
                return pieces >= 2
            key = (start, pieces)
            if key in seen:
                return seen[key]
            seen[key] = False
            result = False
            for end in piece_at(start):
                if solve(end, pieces + 1):
                    result = True
                    break
            if not result and pieces >= 1 and start + 2 < n:
                # Binde-Buchstabe(n): genau ein Zeichen, danach ein echtes Wort.
                for end in piece_at(start + 1):
                    if solve(end, pieces + 1):
                        result = True
                        break
            seen[key] = result
            return result

        return solve(0, 0)

    def with_suffix(self, word: str) -> bool:
        low = word.lower()
        for suffix in SUFFIXES:
            if low.endswith(suffix) and len(low) - len(suffix) >= 4:
                stem = low[:len(low) - len(suffix)]
                if stem in self.dict:
                    return True
        return False

    # ---- Entscheidung --------------------------------------------------
    @staticmethod
    def is_identifier(word: str) -> bool:
        """camelCase/mixedCase = Programmname, API-Feld oder Pfad - nie anfassen."""
        if re.search(r'[a-z]', word) and re.search(r'[A-Z]', word[1:]):
            return True
        return False

    def variants(self, word: str):
        """(Form, Regel) - nur Formen, die nachweislich deutsches Deutsch sind."""
        if len(word) < 3 or not word.isalpha() or self.is_identifier(word):
            return []
        low = word.lower()
        if low in self.dict or low in SKIP or low in self.code_words:
            return []
        umlaut, changed = umlaut_form(word)
        result = []
        # 1) Belegbare Formen: ganze Form steht im Woerterbuch (auch ss -> ß).
        exact = []
        if umlaut != word:
            exact.append((umlaut, 'wort'))
        if not word.isupper():
            # In Woertern aus lauter Grossbuchstaben bleibt SS stehen
            # (AUSSCHLIESSLICH) - ß gehoert nicht in eine Grossschriftzeile.
            for candidate in [umlaut, word]:
                if candidate == word and 'ss' not in low:
                    continue
                for beta in ss_variants(candidate):
                    exact.append((beta, 'eszett'))
        for form, kind in exact:
            if form != word and form.lower() in self.dict:
                result.append((form, kind))
        if result:
            return result
        # 2) Kuratierte Einzelfaelle (FORCE).
        forced = FORCE_MAP.get(word) or FORCE_MAP.get(word.lower())
        if forced:
            result.append((forced, 'force'))
            return result
        # 3) Zusammengesetzte Woerter nur OHNE ss/ß - dort ist die Form sonst
        #    nicht sicher belegbar (Fenstergroesse bleibt lieber stehen).
        if 'ss' in low:
            return result
        if self.compound(umlaut):
            result.append((umlaut, 'kompositum'))
        elif self.with_suffix(umlaut):
            result.append((umlaut, 'endung'))
        return result

    def candidate(self, word: str):
        forms = self.variants(word)
        if not forms:
            return None, ''
        # Kuerzeste/konservativste Form zuerst: lieber ein sicheres Einzelwort
        # als eine lange Kette von Ersetzungen.
        forms.sort(key=lambda item: (len(item[0]), item[1] != 'wort'))
        return forms[0]


def convert_text(text: str, converter: Converter, all_text: bool = False):
    segs = segments(text) if not all_text else [('text', 0, len(text))]
    parts = []
    last = 0
    stats: dict[str, int] = {}
    reasons: dict[str, str] = {}
    rejected: dict[str, int] = {}
    for kind, start, end in segs:
        parts.append(text[last:start])
        chunk = text[start:end]
        if kind == 'code':
            parts.append(chunk)
        else:
            def repl(match):
                word = match.group(0)
                new, why = converter.candidate(word)
                if new and new != word:
                    stats[word] = stats.get(word, 0) + 1
                    reasons.setdefault(word, why)
                    return new
                if re.search(r'(ae|oe|ue|ss)', word.lower()) and word.isalpha() \
                        and not re.search(r'[a-z][A-Z]|[A-Z].*[A-Z]', word):
                    rejected[word] = rejected.get(word, 0) + 1
                return word
            parts.append(WORD_RE.sub(repl, chunk))
        last = end
    parts.append(text[last:])
    return ''.join(parts), stats, reasons, rejected


def code_word_set(text: str, only_code: bool = True) -> set[str]:
    """Bezeichner aus dem PowerShell-Code - als Schutzliste fuer Textdateien."""
    if not only_code:
        return set()
    return _code_words(text)


def _code_words(text: str) -> set[str]:
    words = set()
    for kind, start, end in segments(text):
        if kind != 'code':
            continue
        for match in WORD_RE.finditer(text[start:end]):
            words.add(match.group(0).lower())
    return words


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('path')
    ap.add_argument('--write', action='store_true')
    ap.add_argument('--report', default='')
    ap.add_argument('--code-words-from', default='',
                    help='PowerShell-Quelle, deren Code-Bezeichner nie ersetzt werden')
    ap.add_argument('--all-text', action='store_true',
                    help='Textdatei (Doku): es gibt keinen Code, alles wird geprueft')
    ap.add_argument('--no-bom', action='store_true',
                    help='ohne BOM schreiben (Standard fuer .py/.md/.txt)')
    args = ap.parse_args()

    from spellchecker import SpellChecker
    spell = SpellChecker(language='de')
    path = Path(args.path)
    raw = path.read_text(encoding='utf-8-sig')
    code_words = code_word_set(raw) if path.suffix.lower() == '.ps1' else set()
    if args.code_words_from:
        code_words |= code_word_set(Path(args.code_words_from).read_text(encoding='utf-8-sig'))
    converter = Converter(spell.word_frequency.dictionary, code_words)
    converted, stats, reasons, rejected = convert_text(raw, converter, args.all_text)
    print(f'Ersetzungen: {sum(stats.values())} in {len(stats)} Woertern')
    counts: dict[str, int] = {}
    for word in stats:
        counts[reasons[word]] = counts.get(reasons[word], 0) + 1
    print('Regeln:', counts)
    if args.report:
        base = Path(args.report)
        base.write_text('\n'.join(
            f'{w}\t{c}\t{reasons[w]}' for w, c in sorted(stats.items(), key=lambda kv: (-kv[1], kv[0]))) + '\n',
            encoding='utf-8')
        base.with_suffix(base.suffix + '.rejected').write_text('\n'.join(
            f'{w}\t{c}' for w, c in sorted(rejected.items(), key=lambda kv: (-kv[1], kv[0]))) + '\n',
            encoding='utf-8')
    if args.write:
        prefix = '' if args.no_bom else '\ufeff'
        path.write_text(prefix + converted, encoding='utf-8')
        print('geschrieben:', path)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
