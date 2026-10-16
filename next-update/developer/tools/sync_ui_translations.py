#!/usr/bin/env python3
"""Embed the UI catalog into the single-file EXE source; --check never writes."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / 'app/ArenaBridge.ps1'
CATALOG = ROOT / 'app/localization/en.json'
START = '# >>> UI-TRANSLATIONS-803 (generated from app/localization/en.json) >>>'
END = '# <<< UI-TRANSLATIONS-803 <<<'

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    catalog = json.loads(CATALOG.read_text(encoding='utf-8'))
    assert len({key.casefold() for key in catalog}) == len(catalog), 'PowerShell keys must be case-insensitively unique'
    assert all(isinstance(key, str) and isinstance(value, str) and key and value for key, value in catalog.items())
    data = json.dumps(catalog, ensure_ascii=False, indent=2)
    assert "\n'@" not in data
    block = (START + "\n$script:UiTranslationsDeEn = @{}\n$uiTranslationJson = @'\n" + data +
             "\n'@\nforeach ($property in ($uiTranslationJson | ConvertFrom-Json).PSObject.Properties) { $script:UiTranslationsDeEn[$property.Name] = [string]$property.Value }\n" + END)
    text = APP.read_text(encoding='utf-8-sig')
    a = text.index(START)
    b = text.index(END, a) + len(END)
    if args.check:
        assert text[a:b] == block, 'Run developer/tools/sync_ui_translations.py before building'
    else:
        APP.write_text(text[:a] + block + text[b:], encoding='utf-8-sig')
    print(f'UI catalog: {len(catalog)} entries; embedded copy matches')

if __name__ == '__main__':
    main()
