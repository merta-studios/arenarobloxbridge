#!/usr/bin/env python3
"""8.1.0: session builds stay on their branch and promotion verifies provenance."""
import hashlib
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT.parent
EXE_BUILDER = (REPO / '.github/workflows/exe-builder.yml').read_text()
PROMOTE = (REPO / '.github/workflows/promote-candidate.yml').read_text()
PUBLISH = (REPO / '.github/workflows/publish-bridge.yml').read_text()
MERGE = (REPO / '.github/workflows/auto-pr-merge.yml').read_text()
TOOL = ROOT / 'developer/tools/candidate_manifest.py'


def load_tool():
    spec = importlib.util.spec_from_file_location('candidate_manifest', TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class BranchSafeCandidateBuild(unittest.TestCase):
    def test_builder_can_run_on_session_branch_but_pushes_only_to_its_own_ref(self):
        self.assertIn("startsWith(github.ref, 'refs/heads/arena/')", EXE_BUILDER)
        self.assertIn('git push origin "HEAD:refs/heads/$GITHUB_REF_NAME"', EXE_BUILDER)
        self.assertNotIn('git push origin main', EXE_BUILDER)
        self.assertIn('group: exe-builder-${{ github.ref }}', EXE_BUILDER)

    def test_builder_runs_tests_and_parse_gate_before_build(self):
        tests = EXE_BUILDER.index('run_offline_tests.py')
        parse = EXE_BUILDER.index('parse-gate.ps1')
        build = EXE_BUILDER.index('-Channel rc')
        self.assertLess(tests, build)
        self.assertLess(parse, build)

    def test_builder_writes_provenance_manifest(self):
        self.assertIn('candidate_manifest.py write', EXE_BUILDER)
        self.assertIn('--source-commit "$GITHUB_SHA"', EXE_BUILDER)
        self.assertIn('next-update/beta-release/candidate.json', EXE_BUILDER)

    def test_session_push_does_not_auto_merge(self):
        self.assertNotIn('  push:', MERGE)
        self.assertIn('workflow_dispatch:', MERGE)
        self.assertIn("inputs.confirm == 'MERGE'", MERGE)
        self.assertNotIn('--admin', MERGE)

    def test_promotion_is_main_only_and_verifies_before_copy(self):
        self.assertIn("github.ref == 'refs/heads/main'", PROMOTE)
        verify = PROMOTE.index('candidate_manifest.py verify')
        copy = PROMOTE.index('cp next-update/beta-release/ArenaRobloxBridge.exe')
        self.assertLess(verify, copy)

    def test_publish_workflow_is_main_only(self):
        self.assertIn("github.ref == 'refs/heads/main'", PUBLISH)


class CandidateManifest(unittest.TestCase):
    def test_source_fingerprint_is_deterministic_and_covers_app_and_builder(self):
        mod = load_tool()
        a = mod.source_fingerprint()
        b = mod.source_fingerprint()
        self.assertEqual(a, b)
        self.assertEqual(len(a), 64)
        # Changing a relevant source file must change the fingerprint.
        app_file = ROOT / 'app/version.json'
        original = app_file.read_bytes()
        try:
            app_file.write_bytes(original + b'\n')
            self.assertNotEqual(mod.source_fingerprint(), a)
        finally:
            app_file.write_bytes(original)
        self.assertEqual(mod.source_fingerprint(), a)

    def test_verify_rejects_missing_or_stale_manifest(self):
        mod = load_tool()
        with self.assertRaises(Exception):
            mod.validate({'schema': 1, 'published': True, 'channel': 'rc'})
        with self.assertRaises(Exception):
            mod.validate({'schema': 1, 'published': False, 'channel': 'rc', 'version': '0.0.0'})

    def test_published_release_manifest_is_untouched_by_this_candidate(self):
        latest = json.loads((ROOT / 'release/latest.json').read_text())
        exe = ROOT / 'release/ArenaRobloxBridge.exe'
        self.assertEqual(latest['sha256'], hashlib.sha256(exe.read_bytes()).hexdigest())
        self.assertEqual(latest['sizeBytes'], exe.stat().st_size)
        self.assertLess(tuple(map(int, latest['version'].split('.'))),
                        tuple(map(int, json.loads((ROOT / 'app/version.json').read_text())['version'].split('.'))))


if __name__ == '__main__':
    unittest.main()
