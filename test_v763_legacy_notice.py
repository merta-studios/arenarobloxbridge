"""Offline-Test: letztes Update im alten Kanal (7.6.3).

Prueft, dass der Hauptkanal nur noch das Hinweisfenster "Neues Update System"
mit dem Knopf zur neuen Bridge anbietet, dass der alte Updater die Datei
annimmt (>= 50 KB, neuere Version, BOM) und dass der alte Code nicht mehr
ausgefuehrt wird. Kein Windows/WPF noetig.
"""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCRIPT = ROOT / 'ArenaBridge.ps1'
URL = 'https://arena-rblx-bridge.netlify.app/'


class LegacyNotice763(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = SCRIPT.read_bytes()
        cls.text = cls.raw.decode('utf-8-sig')

    def test_version_is_newer_than_old_channel(self):
        data = json.loads((ROOT / 'version.json').read_text(encoding='utf-8'))
        self.assertEqual(data['version'], '7.6.3')
        self.assertIn(URL, data['notes'][0])
        self.assertGreater(tuple(map(int, data['version'].split('.'))), (7, 6, 2))

    def test_header_reports_763_within_first_lines(self):
        head = self.text.splitlines()[:5]
        m = [re.search(r'Version\s+([0-9]+(?:\.[0-9]+)+)', l) for l in head]
        found = [x.group(1) for x in m if x]
        self.assertEqual(found[0], '7.6.3')

    def test_old_updater_accepts_file(self):
        # Der alte Updater lehnt Dateien unter 50000 Zeichen ab.
        self.assertGreaterEqual(len(self.text), 50000)
        self.assertTrue(self.raw.startswith(b'\xef\xbb\xbf'))

    def test_notice_texts_and_url(self):
        self.assertIn('Neues Update System', self.text)
        self.assertIn('Neue Arena AI Bridge installieren', self.text)
        self.assertIn(f"'{URL}'", self.text)

    def test_notice_runs_before_old_code_and_exits(self):
        call = self.text.index('\nShow-ArenaLegacyNotice\nexit 0\n')
        old_code = self.text.index('PROOF_OF_LIFE')
        self.assertLess(call, old_code)
        self.assertLess(self.text.index('\nparam(\n    [string]$UpdateStatus'), call)

    def test_notice_block_parses_without_errors(self):
        try:
            from tree_sitter import Language, Parser
            import tree_sitter_powershell as tsp
        except ImportError:
            self.skipTest('tree_sitter_powershell nicht installiert')
        parser = Parser(Language(tsp.language()))
        end = self.text.index('\nexit 0\n') + len('\nexit 0\n')
        start = self.text.index('# LETZTES UPDATE IM ALTEN UPDATE-KANAL')
        region = self.text[start:end].encode('utf-8')
        tree = parser.parse(region)
        errors = []

        def walk(node):
            if node.type == 'ERROR' or node.is_missing:
                errors.append(node.start_point)
            for child in node.children:
                walk(child)

        walk(tree.root_node)
        self.assertEqual(errors, [])


if __name__ == '__main__':
    unittest.main(verbosity=2)
