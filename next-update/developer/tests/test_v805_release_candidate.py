#!/usr/bin/env python3
"""8.0.5: The automatic CI build is a 1:1 release candidate.

The workflow must build with the exact release version (no -beta suffix), verify
that the EXE's file version matches app/version.json, and keep release/ and
latest.json untouched until the candidate is explicitly promoted.
"""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]          # next-update/
REPO = ROOT.parent
BUILDER = (ROOT / 'builder/Build-EXE.ps1').read_text(encoding='utf-8-sig')
EXE_BUILDER = (REPO / '.github/workflows/exe-builder.yml').read_text(encoding='utf-8')
PROMOTE = (REPO / '.github/workflows/promote-candidate.yml').read_text(encoding='utf-8')
PUBLISH_WORKFLOW = (REPO / '.github/workflows/publish-bridge.yml').read_text(encoding='utf-8')
PUBLISH_TOOL = (ROOT / 'developer/tools/publish_latest.py').read_text(encoding='utf-8')
VERSION = json.loads((ROOT / 'app/version.json').read_text(encoding='utf-8'))


class BuilderChannels(unittest.TestCase):
    def test_rc_channel_exists(self):
        self.assertIn("[ValidateSet('beta','stable','rc')]", BUILDER)

    def test_rc_uses_the_exact_release_version(self):
        branch = BUILD_VERSION_BRANCH()
        self.assertIn("if ($Channel -eq 'beta') { $BuildVersion = $sourceVersion + '-beta.1' }", branch)
        self.assertIn('else { $BuildVersion = $sourceVersion }', branch)

    def test_rc_rejects_a_prerelease_suffix(self):
        self.assertIn("if ($Channel -eq 'rc') {", BUILDER)
        self.assertIn('A release candidate must use exactly the version from app/version.json (no prerelease suffix)', BUILDER)

    def test_rc_never_writes_into_release_by_default(self):
        self.assertIn("if ([string]::IsNullOrWhiteSpace($OutputDirectory) -and $Channel -eq 'rc') {", BUILDER)
        self.assertIn('$buildOutputDirectory = $betaReleaseDirectory', BUILDER)
        self.assertIn('A release candidate is never written into release\\.', BUILDER)

    def test_metadata_marks_the_candidate_as_publishable(self):
        self.assertIn("releaseCandidate = ($Channel -eq 'rc')", BUILDER)
        self.assertIn("publishable = ($Channel -eq 'rc' -and -not $TestFixtureBuild)", BUILDER)

    def test_version_placeholder_is_still_replaced(self):
        self.assertIn("$preparedSource = $preparedSource.Replace($versionMarker, $BuildVersion)", BUILDER)


class CandidateWorkflow(unittest.TestCase):
    def test_builds_with_rc(self):
        self.assertIn('Build-EXE.ps1" -Channel rc', EXE_BUILDER)
        self.assertNotIn('-Channel beta', EXE_BUILDER)

    def test_verifies_the_file_version_of_the_candidate(self):
        self.assertIn('FileVersionInfo]::GetVersionInfo($exe.FullName).FileVersion', EXE_BUILDER)
        self.assertIn('if ($fileVersion -ne ($version + ".0"))', EXE_BUILDER)

    def test_refuses_a_version_that_is_not_newer(self):
        self.assertIn('nicht neuer als die veroeffentlichte Version', EXE_BUILDER)
        self.assertIn("latest.json", EXE_BUILDER)

    def test_publishes_nothing_by_itself(self):
        self.assertNotIn('git add next-update/release/', EXE_BUILDER)
        self.assertNotIn('cp next-update/beta-release/ArenaRobloxBridge.exe', EXE_BUILDER)
        self.assertNotIn('publish_latest.py', EXE_BUILDER)
        self.assertIn('git add next-update/beta-release/ArenaRobloxBridge.exe', EXE_BUILDER)

    def test_commit_message_names_the_candidate_version(self):
        self.assertIn('Auto-Build: Release-Kandidat ${VERSION} in beta-release bereitgestellt', EXE_BUILDER)


class PromotionWorkflow(unittest.TestCase):
    def test_only_manual_dispatch(self):
        self.assertIn('workflow_dispatch:', PROMOTE)
        self.assertNotIn('  push:', PROMOTE)
        self.assertIn('if [ "${{ inputs.confirm }}" != "RELEASE" ]; then', PROMOTE)

    def test_validates_the_candidate_before_copying(self):
        dry_run = PROMOTE.index('publish_latest.py')
        copy = PROMOTE.index('cp next-update/beta-release/ArenaRobloxBridge.exe next-update/release/ArenaRobloxBridge.exe')
        self.assertLess(dry_run, copy)
        self.assertIn('--dry-run', PROMOTE)

    def test_starts_the_publish_run_explicitly(self):
        self.assertIn('gh workflow run publish-bridge.yml --ref main', PROMOTE)
        self.assertIn('actions: write', PROMOTE)

    def test_waits_for_green_tests_by_default(self):
        self.assertIn('run_offline_tests.py', PROMOTE)
        self.assertIn('${{ !inputs.skip_tests }}', PROMOTE)


class PublishSafety(unittest.TestCase):
    def test_publish_workflow_only_watches_the_release_folder(self):
        self.assertIn("'next-update/release/ArenaRobloxBridge.exe'", PUBLISH_WORKFLOW)
        self.assertNotIn('beta-release', PUBLISH_WORKFLOW)

    def test_publish_tool_requires_the_exact_source_version(self):
        self.assertIn('fv != version + ".0"', PUBLISH_TOOL)
        self.assertIn('Die EXE wurde mit einer anderen Version gebaut.', PUBLISH_TOOL)

    def test_publish_tool_rejects_a_new_file_for_an_old_version(self):
        self.assertIn('bereits veroeffentlicht, aber mit einer anderen Datei', PUBLISH_TOOL)

    def test_version_manifest_is_still_behind_the_candidate(self):
        latest = json.loads((ROOT / 'release/latest.json').read_text(encoding='utf-8'))
        self.assertLess(tuple(map(int, latest['version'].split('.'))),
                        tuple(map(int, VERSION['version'].split('.'))))


def BUILD_VERSION_BRANCH() -> str:
    start = BUILDER.index("if ([string]::IsNullOrWhiteSpace($BuildVersion)) {")
    end = BUILDER.index('if ($BuildVersion -notmatch', start)
    return BUILDER[start:end]


if __name__ == '__main__':
    unittest.main()
