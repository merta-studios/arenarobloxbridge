#!/usr/bin/env python3
"""8.0.5 contracts: terrain tools, camera recovery, desktop shortcut, GUI 3.0."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = (ROOT / 'app/ArenaBridge.ps1').read_text(encoding='utf-8-sig')
VERSION = json.loads((ROOT / 'app/version.json').read_text())
CATALOG = json.loads((ROOT / 'app/localization/en.json').read_text())

NEW_TOOLS = (
    'terrain_heightmap', 'terrain_sculpt', 'terrain_paint', 'terrain_water',
    'terrain_feature', 'terrain_carve', 'terrain_measure', 'terrain_clear',
    'camera_state', 'camera_reset', 'camera_focus', 'camera_guard', 'ui_widget',
)


def region(start, end):
    a = SOURCE.index(start)
    return SOURCE[a:SOURCE.index(end, a)]


def plugin_source():
    start = SOURCE.index("function Get-PluginSource {\n@'\n") + len("function Get-PluginSource {\n@'\n")
    return SOURCE[start:SOURCE.index("\n'@\n}", start)]


class Version805(unittest.TestCase):
    def test_version_and_notes(self):
        self.assertEqual(VERSION['version'], '8.0.5')
        self.assertEqual(len(VERSION['notes']), len(VERSION['notesEn']))
        note = VERSION['notes'][0]
        self.assertTrue(note.startswith('• 8.0.5 — '), note[:40])
        self.assertGreaterEqual(note.count('•'), 5)
        self.assertLess(len(' '.join(note.split())), 600)
        self.assertIn('Gelände', note)
        self.assertIn('Kamera', note)
        self.assertIn('GUI', note)
        self.assertIn('Verknüpfung', note)
        self.assertIn('desktop shortcut', VERSION['notesEn'][0])

    def test_every_note_is_translated(self):
        for de, en in zip(VERSION['notes'], VERSION['notesEn']):
            self.assertIn(de, CATALOG)
            self.assertEqual(CATALOG[de], en)


class DesktopShortcut(unittest.TestCase):
    def setUp(self):
        self.block = region('function Initialize-ArenaDesktopShortcut', 'function Remove-DeadSession')

    def test_shortcut_is_created_and_repaired(self):
        for marker in ('Get-ArenaDesktopFolder', 'Get-ArenaShortcutInfo', 'Test-ArenaBridgeShortcutTarget',
                       'Initialize-ArenaDesktopShortcut', 'Arena Roblox Bridge.lnk'):
            self.assertIn(marker, SOURCE)
        self.assertIn('Arena.NotifyLink', self.block)
        self.assertIn('Arena.ArenaRobloxBridge', self.block)
        self.assertIn('WScript.Shell', self.block)
        self.assertIn('$script:IsExeMode', self.block)
        self.assertIn('already-current', self.block)

    def test_shortcut_never_touches_foreign_programs(self):
        self.assertIn('Test-ArenaBridgeShortcutTarget', self.block)
        self.assertIn('ArenaBridge*.exe', SOURCE)
        self.assertIn('ArenaRobloxBridge*.exe', SOURCE)
        self.assertNotIn('Remove-Item -LiteralPath $canonical -Force', self.block)
        self.assertNotIn('HKLM', self.block)

    def test_shortcut_runs_on_every_bridge_start(self):
        runtime = SOURCE[SOURCE.index('function Start-BridgeRuntime'):]
        self.assertIn('Initialize-ArenaDesktopShortcut', runtime)
        self.assertLess(runtime.index('Initialize-ArenaDesktopShortcut'), runtime.index('Install-RobloxPlugin'))


class CameraGuard(unittest.TestCase):
    def setUp(self):
        self.plugin = plugin_source()

    def test_camera_guard_engine_exists(self):
        self.assertIn('CAMERA.heal', self.plugin)
        self.assertIn('CAMERA.watch', self.plugin)
        self.assertIn('CAMERA.afterCommand', self.plugin)
        self.assertIn('plugin_load', self.plugin)
        self.assertIn('after_playtest', self.plugin)
        self.assertIn('saved_stuck_state', self.plugin)
        self.assertIn('Enum.CameraType.Fixed', self.plugin)
        self.assertIn('Enum.CameraType.Custom', self.plugin)

    def test_camera_tools_are_registered(self):
        docs = region('function Get-ToolDocs', 'function Get-DocsResponse')
        for tool in ('camera_state', 'camera_reset', 'camera_focus', 'camera_guard'):
            self.assertIn(f"name = '{tool}'", docs)
            self.assertIn(f"tools.{tool} = function", self.plugin)
            self.assertIn(f"            {tool} = '", SOURCE)

    def test_every_bridge_command_repairs_the_camera(self):
        handle = region('local function handleCommand', 'local function pumpCommandQueue')
        self.assertIn('CAMERA.noteBridgeCommand', handle)
        self.assertIn('CAMERA.afterCommand', handle)
        self.assertLess(handle.index('CAMERA.afterCommand'), handle.rindex('return result'))

    def test_playtests_and_unload_restore_the_camera(self):
        sim_stop = region('tools.sim_stop = function(args)', 'tools.sim_status = function(args)')
        self.assertIn('CAMERA.heal("sim_stop', sim_stop)
        self.assertIn('CAMERA.heal("plugin_unloading"', self.plugin)
        self.assertIn('Kamera reparieren', self.plugin)

    def test_camera_focus_never_leaves_scriptable(self):
        focus = region('tools.camera_focus = function(args)', 'CAMERA.GUARD_SOURCE = ')
        self.assertIn('CameraType.Fixed', focus)
        self.assertIn('Scriptable', focus)

    def test_camera_recovery_is_documented(self):
        guides = region('cameraRules = @{', 'toolboxRules = @{')
        self.assertIn('Scriptable', guides)
        self.assertIn('camera_reset', guides)
        self.assertIn('CameraType.Fixed', guides)


class TerrainTools(unittest.TestCase):
    def setUp(self):
        self.plugin = plugin_source()

    def test_every_terrain_tool_exists_and_is_registered(self):
        docs = region('function Get-ToolDocs', 'function Get-DocsResponse')
        write_tools = region('local PERSISTENT_WRITE_TOOLS', 'local WRITE_TOOLS = {}')
        read_tools = region('function Get-ActivityToolSets', 'function Get-OpenCloudHistorySummary')
        for tool in NEW_TOOLS[:8]:
            self.assertIn(f"tools.{tool} = function", self.plugin, tool)
            self.assertIn(f"name = '{tool}'", docs, tool)
            self.assertIn(f"            {tool} = '", SOURCE, tool)
            if tool == 'terrain_measure':
                self.assertIn(f"'{tool}'", read_tools)
            else:
                self.assertTrue(re.search(rf"\b{tool}\s*=\s*true", write_tools), tool)

    def test_terrain_math_covers_all_presets_and_features(self):
        presets = region('TERRAIN.PRESET_NAMES =', 'function TERRAIN.terrain()')
        for preset in ('plains', 'hills', 'mountains', 'islands', 'archipelago', 'dunes',
                       'canyon', 'plateau', 'swamp', 'volcano', 'custom'):
            self.assertIn(f'"{preset}"', presets)
        features = region('TERRAIN.FEATURE_SHAPES = {}', 'tools.terrain_feature = function(args)')
        for feature in ('mountain', 'ridge', 'hill', 'plateau', 'crater', 'volcano', 'canyon',
                        'island', 'archipelago', 'dunes', 'cliff', 'valley', 'terrace'):
            self.assertIn(f'TERRAIN.FEATURE_SHAPES.{feature} =', features)

    def test_voxel_limits_and_water_channel_are_real(self):
        self.assertIn('TERRAIN.MAX_READ_WRITE_VOXELS = 4194304', self.plugin)
        self.assertIn('TERRAIN.MAX_FILL_VOXELS = 67108864', self.plugin)
        self.assertIn('ExpandToGrid(4)', self.plugin)
        self.assertIn('ReadVoxelChannels', self.plugin)
        self.assertIn('WriteVoxelChannels', self.plugin)
        self.assertIn('LiquidOccupancy', self.plugin)

    def test_long_writes_are_resumable(self):
        engine = region('function TERRAIN.writeHeightmap', 'function TERRAIN.readHeightsFromChunk')
        self.assertIn('resumeToken = { chunk = chunkIndex, total = totalChunks }', engine)
        self.assertIn('maxChunks', engine)
        self.assertIn('task.wait()', engine)

    def test_destructive_clear_requires_confirmation(self):
        clear = region('tools.terrain_clear = function(args)', 'tools.build_polygon_model = function(args)')
        self.assertIn('CONFIRM_REQUIRED', clear)
        self.assertIn('args.confirm ~= true', clear)
        self.assertIn('TERRAIN.beginRecording', clear)
        self.assertIn('ChangeHistoryService', SOURCE)

    def test_terrain_lua_is_lua51_safe(self):
        # math.pow and ctx.base were real bugs caught by the Lua runtime test:
        # math.pow does not exist in Luau and ctx.base was never a field.
        self.assertNotIn('math.pow', self.plugin)
        self.assertNotIn('ctx.base ', self.plugin)

    def test_terrain_guides_are_delivered(self):
        guides = region('terrainRules = @{', 'cameraRules = @{')
        for marker in ('terrain_heightmap', 'terrain_feature', 'terrain_water', 'terrain_measure',
                       'LiquidOccupancy', '4,194,304', 'resumeToken'):
            self.assertIn(marker, guides)


class GuiEngine30(unittest.TestCase):
    def setUp(self):
        self.plugin = plugin_source()
        self.skins = region('UI_ENGINE.SKINS = {', 'function UI_ENGINE.skinNames()')
        self.widgets = region('UI_ENGINE.WIDGETS = {}', 'tools.ui_widget = function(args)')

    def test_forty_distinct_skins(self):
        names = re.findall(r'^\s{4}([a-z][a-z0-9]*) = \{ label = ', self.skins, re.M)
        self.assertGreaterEqual(len(names), 40, names)
        self.assertEqual(len(set(names)), len(names), 'skin names must be unique')
        for name in ('pop', 'cloud', 'gel', 'neon', 'gold', 'inkwash', 'blueprint', 'pirate',
                     'medieval', 'scifi', 'sports', 'gothic', 'tropical', 'desert', 'dreamcore', 'toybox'):
            self.assertIn(name, names)

    def test_outline_gloss_and_decor_are_engine_layers(self):
        for function in ('UI_ENGINE.outlineLayer', 'UI_ENGINE.glossLayer', 'UI_ENGINE.decorLayer',
                         'UI_ENGINE.outlineSpec'):
            self.assertIn('function ' + function + '(', self.plugin)
            self.assertIn(function, SOURCE)
        self.assertIn('UI_ENGINE.OUTLINES = {', self.plugin)
        self.assertIn('ArenaOutline', self.plugin)
        self.assertIn('ArenaGloss', self.plugin)
        self.assertIn('ArenaDecor', self.plugin)
        surface = region('function UI_ENGINE.surface(opts)', 'function UI_ENGINE.textNode')
        self.assertIn('UI_ENGINE.outlineLayer', surface)
        self.assertIn('UI_ENGINE.glossLayer', surface)
        self.assertIn('UI_ENGINE.decorLayer', surface)
        # content stays above decoration so text is never covered
        self.assertIn('content.ZIndex = 4', surface)
        decor = region('function UI_ENGINE.decorLayer', 'function UI_ENGINE.surface(opts)')
        self.assertIn('local zIndex = math.floor(tonumber(d.zIndex) or 3)', decor)
        self.assertIn('UI_ENGINE.DECOR_BUDGET', decor)

    def test_eighteen_widgets_and_the_tool(self):
        self.assertEqual(self.widgets.count('UI_ENGINE.widgetDef("'), 18)
        for name in ('shop', 'inventory', 'battlepass', 'quests', 'settings', 'leaderboard',
                     'profile', 'dailyrewards', 'gacha', 'currency', 'hud', 'dialog',
                     'tooltip', 'hotbar', 'map', 'codex', 'tiers', 'social'):
            self.assertIn(f'UI_ENGINE.widgetDef("{name}"', self.widgets)
        self.assertIn('tools.ui_widget = function', self.plugin)
        self.assertIn("name = 'ui_widget'", region('function Get-ToolDocs', 'function Get-DocsResponse'))
        self.assertIn("ui_widget = '", labels_region())
        self.assertIn('ui_widget = true', SOURCE)

    def test_widget_tool_uses_engine_rules_not_hand_built_frames(self):
        widget_tool = region('tools.ui_widget = function(args)', 'tools.ui_texture = function(args)')
        self.assertIn('UI_ENGINE.ensureScreen', widget_tool)
        self.assertIn('UI_ENGINE.buildNode', widget_tool)
        self.assertIn('UI_ENGINE.newContext', widget_tool)
        self.assertNotIn('UDim2.new(0, ', widget_tool)
        self.assertNotIn('Instance.new("TextLabel")', widget_tool)

    def test_skin_list_reports_forty_and_style_layers(self):
        skin_tool = region('tools.ui_skin = function(args)', 'tools.build_surface = function(args)')
        self.assertIn('40 skins (8.0.5)', skin_tool)
        self.assertIn('outline', skin_tool)
        self.assertIn('gloss', skin_tool)
        self.assertIn('decor', skin_tool)

    def test_audit_measures_the_new_layers(self):
        audit = region('tools.ui_audit = function(args)', '\n\nlocal function ')
        self.assertIn('ArenaOutline', audit)
        self.assertIn('ArenaGloss', audit)
        self.assertIn('ArenaDecor', audit)
        self.assertIn('decorOveruse', audit)


def labels_region():
    start = SOURCE.index("        get_bridge_log = 'Bridge-Protokoll")
    end = SOURCE.index("\n    }\n", start)
    return SOURCE[start:end]


class RegistrationConsistency(unittest.TestCase):
    def test_new_tools_have_labels_docs_and_activity_texts(self):
        labels = labels_region()
        docs = region('function Get-ToolDocs', 'function Get-DocsResponse')
        activity = region('function Get-ArenaActivityText', 'function Get-ArenaActivityKind')
        for tool in NEW_TOOLS:
            self.assertRegex(labels, rf"(?m)^\s+{tool} = '[^']+'", tool)
            self.assertIn(f"name = '{tool}'", docs, tool)
            self.assertRegex(activity, rf"(?m)^\s+{tool} = '[^']+'", tool)

    def test_activity_labels_are_english_in_the_catalog(self):
        activity = region('function Get-ArenaActivityText', 'function Get-ArenaActivityKind')
        for tool in NEW_TOOLS:
            match = re.search(rf"^\s+{tool} = '([^']*)'", activity, re.M)
            self.assertIsNotNone(match, tool)
            self.assertIn(match.group(1), CATALOG, tool)

    def test_tool_counts_match_every_catalog(self):
        docs = re.findall(r"\$t\.Add\(@\{ name = '([a-z_0-9]+)';", SOURCE)
        activity = re.findall(r"^\s{12}([a-z_][a-z0-9_]*)\s*=\s*'", region('function Get-ArenaActivityText', 'function Get-ArenaActivityKind'), re.M)
        labels = re.findall(r"^\s{8}([a-z_][a-z0-9_]*)\s*=\s*'", labels_region(), re.M)
        self.assertEqual(len(docs), 159)
        self.assertEqual(len(activity), 159)
        self.assertEqual(len(labels), 159)
        self.assertEqual(set(docs), set(activity))
        self.assertEqual(set(docs), set(labels))


class PublishedStateUntouched(unittest.TestCase):
    def test_published_manifest_stays_below_the_candidate(self):
        latest = json.loads((ROOT / 'release/latest.json').read_text())
        self.assertLessEqual(tuple(map(int, latest['version'].split('.'))), (8, 0, 3))


if __name__ == '__main__':
    unittest.main()
