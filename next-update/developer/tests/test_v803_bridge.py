#!/usr/bin/env python3
"""8.0.3 contracts: privacy, ownership, UI, persistence and agent documentation."""
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = (ROOT / 'app/ArenaBridge.ps1').read_text(encoding='utf-8-sig')
CATALOG = json.loads((ROOT / 'app/localization/en.json').read_text())

def region(start, end):
    a = SOURCE.index(start)
    return SOURCE[a:SOURCE.index(end, a)]

class Bridge803(unittest.TestCase):
    def test_release_is_prepared_not_published(self):
        data = json.loads((ROOT / 'app/version.json').read_text())
        self.assertEqual(data['version'], '8.0.3')
        self.assertTrue(data['notes'][0].startswith('• 8.0.3 — '))
        self.assertLess(len(data['notes'][0]), 600)
        self.assertGreaterEqual(data['notes'][0].count('•'), 5)
        self.assertEqual(len(data['notes']), len(data['notesEn']))
        for de, en in zip(data['notes'], data['notesEn']):
            self.assertEqual(CATALOG[de], en)
        # The checked-in EXE/manifest is the last published binary, not this candidate.
        latest = json.loads((ROOT / 'release/latest.json').read_text())
        self.assertLessEqual(tuple(map(int, latest['version'].split('.'))), (8, 0, 3))

    def test_no_desktop_capture_path(self):
        self.assertNotRegex(SOURCE, r'\.CopyFromScreen\s*\(')
        self.assertNotIn('private static Bitmap TryCopyFromScreen', SOURCE)
        self.assertNotIn('private static Bitmap TryWindowDcBitBlt', SOURCE)
        shot = region('    function Invoke-Screenshot(', '    # BEFEHL AN DAS STUDIO-PLUGIN')
        for marker in ('StudioCaptureTargets.TryGetValue', 'Get-DeliverySession', 'Get-Process -Id',
                       'MainWindowHandle.ToInt64()', 'STUDIO_WINDOW_UNRESOLVED',
                       '[Arena.PreviewCapture]::Capture', 'STUDIO_CAPTURE_UNAVAILABLE'):
            self.assertIn(marker, shot)
        self.assertNotIn('Select-Object -First 1', shot)
        self.assertIn('GetWindowThreadProcessId', SOURCE)

    def test_no_guessing_place_windows_or_stale_images(self):
        resolver = region('function Resolve-PlaceWindowIdentity {', 'function Test-PreviewHandleClaimed {')
        self.assertIn('$matches.Count -eq 1', resolver)
        self.assertIn('$sameNameSessions.Count -eq 1', resolver)
        self.assertIn('$_.ProcessId -eq $identity.ProcessId', resolver)
        self.assertIn('StudioCaptureTargets.TryRemove', resolver)
        self.assertNotIn('erstesFreiesFenster', resolver)
        preview = region('function Resolve-PlacePreviewHandle {', 'function Set-PlacePreviewImage {')
        self.assertIn('ambiguousWindowNoCapture', preview)
        self.assertNotIn('$infos[0]', preview)
        self.assertIn('$job.IdentityKey -ne (Get-PlaceIdentityKey', SOURCE)
        self.assertIn('GetProductInfo(id, Enum.InfoType.Asset)', SOURCE)
        self.assertIn('publishedPlaceName.id ~= id', SOURCE)
        self.assertIn("if ($Source -eq 'plugin') { return 3 }", SOURCE)

    def test_group_upload_does_not_fall_back_to_account(self):
        owner = region('    function Resolve-OpenCloudCreatorForUpload', '    function Invoke-OpenCloudUpload')
        self.assertLess(owner.index("creatorType -eq 'Group'"), owner.index('Get-OpenCloudStudioDeveloper'))
        self.assertIn("creatorKind='group'", owner)
        self.assertIn('GROUP_OWNER_UNKNOWN', owner)
        self.assertIn("$creator['groupId']", SOURCE)

    def test_asset_permission_repair_is_scoped_and_bounded(self):
        grant = region('    function Grant-SessionAssetUse', '    function Get-OpenCloudStudioDeveloper')
        self.assertIn('Invoke-OpenCloudCatalogTool', grant)
        self.assertIn('patch__asset_permissions_api_v1_assets_permissions', grant)
        self.assertIn("subjectType='Universe'", grant)
        self.assertIn("subjectId=[string]$entry.gameId", grant)
        self.assertIn("action='Use'", grant)
        self.assertNotIn("subjectType='All'", grant)
        invoke = region('    function Invoke-PluginTool(', '    # TOOL-DOKUMENTATION:')
        self.assertIn("$failed.code -eq 'ASSET_PERMISSION_DENIED'", invoke)
        self.assertIn('$timeoutSeconds $activityId $false', invoke)
        self.assertLess(invoke.index('if (-not $got) { return $null }'), invoke.index('Grant-SessionAssetUse'))
        catalog = region('    function Invoke-OpenCloudCatalogTool', '    function Get-OpenCloudAssetSpec')
        self.assertIn("$accessMode -ne 'readwrite'", catalog)
        self.assertIn('Assert-OpenCloudToolAccess', catalog)

    def test_place_row_only_status_and_real_or_indeterminate_progress(self):
        visual = region('function Update-PlaceProgressVisual', 'function Get-ProgressDiagnoseLines')
        self.assertIn('$Row.ProgressBar.IsIndeterminate', visual)
        self.assertIn('$silent -lt 60', visual)
        self.assertIn("$Row.ProgressBar.Visibility = 'Visible'", visual)
        self.assertIn("$Row.ProgressPercent.Visibility = 'Collapsed'", visual)
        self.assertNotIn("$label += ' · Letzte Aktion:", visual)
        self.assertNotIn('$label = $message', visual)
        self.assertNotIn("$label = 'Fortschritt nicht anwendbar", visual)
        self.assertIn('Seit über einer Minute kein Bridge-Aufruf', visual)

    def test_history_meter_uses_card_and_detailed_translations(self):
        history = region('function Update-ArenaHistoryProgressCard {', 'function Update-ArenaHistoryProgress {')
        self.assertNotIn('$Row.', history)
        self.assertIn('$Card.Bar.IsIndeterminate', history)
        self.assertIn("if ($progressMode -eq 'hidden') { 'Collapsed' }", history)
        self.assertFalse(any(v.startswith('Completed:') for v in CATALOG.values()))
        self.assertEqual(CATALOG['Explorer-Struktur'], 'Explorer hierarchy')
        self.assertIn('owner', CATALOG['Hat Place-Name, ID, Eigentümer und Studio-Zustand geprüft.'])

    def test_language_vectors_catalog_and_persistence(self):
        for name in ('LanguageMenuButton', 'LanguageChoices', 'SelectedLanguageText',
                     'SelectedEnglishFlag', 'SelectedGermanFlag'):
            self.assertIn(f'x:Name="{name}"', SOURCE)
        self.assertIn('Fill="#FFCE00"', SOURCE)
        self.assertIn('Fill="#012169"', SOURCE)
        self.assertNotIn('Text="🇩🇪"', SOURCE)
        self.assertNotIn('Text="🇬🇧"', SOURCE)
        self.assertEqual(len(CATALOG), len({k.casefold() for k in CATALOG}))
        self.assertGreater(len(CATALOG), 700)
        permissions = json.loads((ROOT / 'app/opencloud/catalog.json').read_text())['permissions']
        self.assertTrue(all(v in CATALOG for v in permissions.values()))
        self.assertIn('ConditionalWeakTable[object,object]', SOURCE)
        self.assertIn('$node.OwnedWindows', SOURCE)
        self.assertIn("$node -is [System.Windows.Controls.TextBox] -and $property -eq 'Text'", SOURCE)
        self.assertIn("$Element.Tag -ne 'ArenaUserContent'", SOURCE)
        self.assertIn("$script:AppDataRoot = Join-Path $env:LOCALAPPDATA 'ArenaRobloxBridge'", SOURCE)
        save = region('function Save-BridgeSettingsFile', '$script:SettingsCache = Get-BridgeSettingsFile')
        self.assertIn('uiLanguage', save)
        self.assertIn('[IO.File]::Replace($temp, $script:SettingsFile, $null)', save)
        subprocess.run([sys.executable, str(ROOT / 'developer/tools/sync_ui_translations.py'), '--check'], check=True)

    def test_all_static_german_xaml_is_in_catalog(self):
        ui = SOURCE[SOURCE.index('function Get-UiLanguage'):]
        attrs = set(re.findall(r'(?:Text|Content|Title|ToolTip)="([^"{}]+)"', ui))
        german = re.compile(r'[äöüÄÖÜß]|\b(?:nicht|und|die|für|wird|Bitte|Schlüssel|Einstellungen)\b')
        missing = [text for text in attrs if german.search(text) and text not in CATALOG and '$' not in text]
        self.assertEqual(missing, [])

    def test_startup_migration_happens_before_duplicate_exit(self):
        resolve = region('function Resolve-BridgeUpdaterExePath', 'function Save-BridgeUpdaterExePath')
        self.assertLess(resolve.index('$script:IsExeMode'), resolve.index('$PreferredPath))'))
        self.assertLess(SOURCE.index('try { [void](Get-StartupEnabled) }'), SOURCE.index('$mutexName ='))
        self.assertIn("(?: ?\\(\\d+\\))?", SOURCE)
        self.assertIn('Remove-BridgeStartupEntries', SOURCE)

    def test_multiple_accounts_and_agent_shape_documentation(self):
        profiles = region('function Update-StudioEditorProfile', 'function Refresh-Ui')
        self.assertIn('Group-Object editorUserId', profiles)
        self.assertIn("$accounts.Count -lt 2", profiles)
        self.assertIn("+ ' Accounts'", profiles)
        self.assertIn('$lines -join [Environment]::NewLine', profiles)
        self.assertIn('StudioProfileCache', profiles)
        docs = region("        $t.Add(@{ name = 'build_assembly';", "        $t.Add(@{ name = 'build_polygon_model';")
        for word in ('HalfBall', 'QuarterBall', 'CurvedCylinder', 'Torus', 'Pyramid', 'relativeTo',
                     'offset', '96 CSG', 'approximation', 'repeatSpec', 'rollback'):
            self.assertIn(word.lower(), docs.lower())
        self.assertIn('ordinaryParts =', SOURCE)

if __name__ == '__main__':
    unittest.main()
