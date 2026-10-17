#!/usr/bin/env python3
"""8.0.5: execute the real terrain math and the widget library with Lua doubles.

The terrain engine is deliberately testable without Studio: noise, presets,
grid building, bilinear sampling and material layering are pure Lua. Writing
voxels is not executed here (that needs the real Terrain service); the tests
prove the arithmetic, determinism and limits that feed the writer.
"""
from pathlib import Path
import unittest
from lupa import LuaRuntime

ROOT = Path(__file__).resolve().parents[2]
SOURCE = (ROOT / 'app/ArenaBridge.ps1').read_text(encoding='utf-8-sig')

def region(start, end):
    a = SOURCE.index(start)
    return SOURCE[a:SOURCE.index(end, a)]

class TerrainRuntime(unittest.TestCase):
    def setUp(self):
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        fixture = (Path(__file__).parent / 'fixtures/parts_runtime.lua').read_text()
        decode = region('local function decodeValue(value)', 'local commonProps =')
        terrain = region('TERRAIN = {}', 'tools.terrain_heightmap = function(args)')
        features = region('TERRAIN.FEATURE_SHAPES = {}', 'tools.terrain_feature = function(args)')
        self.lua.execute(fixture + '\n' + decode + '\n' + terrain + '\n' + features)

    def run_lua(self, text):
        return self.lua.execute(text)

    def test_every_preset_builds_a_bounded_deterministic_grid(self):
        presets = self.run_lua('return table.concat(TERRAIN.PRESET_NAMES, ",")').split(',')
        self.assertGreaterEqual(len(presets), 11)
        for preset in presets:
            with self.subTest(preset=preset):
                self.run_lua(f'''
                local grid, stats, code, message = TERRAIN.buildGrid({{
                    preset = "{preset}", mode = "generate",
                    center = {{x = 0, y = 0, z = 0}}, size = {{x = 64, z = 64}},
                    baseHeight = 0, maxHeight = 32, minHeight = -16,
                    seed = 1234, gridStep = 4, waterLevel = 4,
                }})
                assert(grid ~= nil, tostring(code) .. ": " .. tostring(message))
                assert(stats.cols >= 2 and stats.rows >= 2, "grid too small")
                assert(stats.minHeight >= -16.001 and stats.maxHeight <= 32.001,
                    "height escaped the clamp: " .. tostring(stats.minHeight) .. ".." .. tostring(stats.maxHeight))
                assert(stats.maxHeight >= stats.minHeight, "inverted heights")
                assert(stats.gridStep % 4 == 0, "grid step must be voxel aligned")
                local first = grid[1][1]
                local gridAgain = TERRAIN.buildGrid({{
                    preset = "{preset}", mode = "generate",
                    center = {{x = 0, y = 0, z = 0}}, size = {{x = 64, z = 64}},
                    baseHeight = 0, maxHeight = 32, minHeight = -16,
                    seed = 1234, gridStep = 4, waterLevel = 4,
                }})
                assert(math.abs(gridAgain[1][1] - first) < 1e-9, "same seed must give the same height")
                ''')

    def test_islands_and_archipelago_form_water_and_land(self):
        self.run_lua('''
        local grid, stats = TERRAIN.buildGrid({
            preset = "islands", center = {x = 0, y = 0, z = 0},
            size = {x = 192, z = 192}, baseHeight = 0, maxHeight = 40,
            minHeight = -40, seed = 9, gridStep = 4, waterLevel = 0,
        })
        assert(grid ~= nil)
        assert(grid[1][1] < 4, "the island rim must sit at or below the water line")
        assert(stats.maxHeight > stats.waterLevel, "the island centre must rise above the water")
        ''')
        self.run_lua('''
        local grid, stats = TERRAIN.buildGrid({
            preset = "archipelago", center = {x = 0, y = 0, z = 0},
            size = {x = 192, z = 192}, baseHeight = 0, maxHeight = 40,
            minHeight = -40, seed = 9, gridStep = 4, waterLevel = 0,
        })
        assert(grid ~= nil)
        assert(stats.minHeight < stats.waterLevel, "an archipelago needs water between its islands")
        assert(stats.maxHeight > stats.waterLevel, "an archipelago needs land above the water")
        ''')

    def test_explicit_heights_are_interpolated_not_ignored(self):
        self.run_lua('''
        local grid, stats = TERRAIN.buildGrid({
            mode = "explicit", preset = "custom",
            center = {x = 0, y = 0, z = 0}, size = {x = 32, z = 32},
            gridStep = 4, heights = { {0, 10}, {10, 20} },
            baseHeight = 0, maxHeight = 64, minHeight = -64,
        })
        assert(grid ~= nil)
        assert(grid[1][1] == 0, "corner value must be preserved")
        assert(grid[stats.rows][stats.cols] == 20, "opposite corner must be preserved")
        assert(grid[1][stats.cols] == 10, "second source value must be preserved")
        ''')

    def test_oversized_requests_are_clamped_and_budgeted(self):
        self.run_lua('''
        local grid, stats = TERRAIN.buildGrid({
            preset = "hills", center = {x = 0, y = 0, z = 0},
            size = {x = 5000, z = 5000}, gridStep = 3, maxHeight = 20,
        })
        assert(grid ~= nil)
        assert(stats.size.x <= 512 and stats.size.z <= 508, "size must be clamped to the writer limit")
        assert(stats.gridStep == 4, "gridStep must snap to a 4-stud multiple")
        assert(stats.columns <= TERRAIN.MAX_COLUMNS, "column budget must hold")
        assert(stats.columns > 10000, "the clamp should still allow large maps")
        ''')

    def test_sample_grid_interpolates_and_reports_slope(self):
        self.run_lua('''
        local grid = { {0, 10}, {0, 10} }
        local stats = { cols = 2, rows = 2, gridStep = 4 }
        local midpoint, slope = TERRAIN.sampleGrid(grid, stats, 0, 0, 2, 0)
        assert(math.abs(midpoint - 5) < 1e-9, "midpoint should interpolate to 5, got " .. tostring(midpoint))
        assert(slope >= 10, "slope must report the measured height delta")
        local outside = TERRAIN.sampleGrid(grid, stats, 0, 0, -40, 40)
        assert(outside == 0 or outside == 10, "sampling outside clamps to the nearest column")
        ''')

    def test_material_stack_layers_water_snow_and_rock(self):
        self.run_lua('''
        local ctx = { waterLevel = 0, baseHeight = 0, amplitude = 40, seed = 3, center = Vector3.new(0, 0, 0), radius = 40 }
        local args = {}
        local shore = TERRAIN.materialStack(args, ctx, -2, 0, nil)
        assert(shore.surface == Enum.Material.Sand, "below the waterline the surface is seabed sand")
        local high = TERRAIN.materialStack({ snowLine = 50 }, ctx, 60, 0, nil)
        assert(high.surface == Enum.Material.Snow, "above the explicit snow line the surface is snow")
        local noSnow = TERRAIN.materialStack(args, ctx, 60, 0, nil)
        assert(noSnow.surface ~= Enum.Material.Snow, "without a snow line no snow is invented")
        local steep = TERRAIN.materialStack({ snowLine = 500 }, ctx, 20, 24, nil)
        assert(steep.surface == Enum.Material.Rock, "steep ground becomes rock")
        local painted = TERRAIN.materialStack(args, ctx, 20, 0, Enum.Material.Slate)
        assert(painted.surface == Enum.Material.Slate, "an explicit material wins")
        ''')

    def test_chunk_region_is_voxel_aligned(self):
        self.run_lua('''
        local region = TERRAIN.chunkRegion(-17, 3, -9, 11, -6, 18)
        assert(region.Size.X % 4 == 0 and region.Size.Y % 4 == 0 and region.Size.Z % 4 == 0,
            "every read/write region must be a multiple of 4 studs")
        local nx, ny, nz = TERRAIN.regionShape(region)
        assert(nx * ny * nz <= TERRAIN.MAX_READ_WRITE_VOXELS,
            "a single chunk must stay inside the 4,194,304 voxel limit")
        assert(TERRAIN.MAX_READ_WRITE_VOXELS == 4194304)
        assert(TERRAIN.MAX_FILL_VOXELS == 67108864)
        ''')

    def test_every_feature_shape_is_finite_and_centred(self):
        names = self.run_lua('local n={} for k in pairs(TERRAIN.FEATURE_SHAPES) do table.insert(n,k) end table.sort(n) return table.concat(n, ",")').split(',')
        self.assertGreaterEqual(len(names), 13)
        for name in names:
            with self.subTest(feature=name):
                self.run_lua(f'''
                local ctx = {{ baseHeight = 0, center = Vector3.new(0, 0, 0), radius = 64, amplitude = 48, seed = 5, waterLevel = nil }}
                local shape = TERRAIN.FEATURE_SHAPES["{name}"]
                assert(type(shape) == "function")
                local centre = shape(0, 0, {{}}, ctx)
                local rim = shape(120, 120, {{}}, ctx)
                assert(centre == centre and rim == rim, "NaN in feature " .. "{name}")
                assert(math.abs(centre) < 500 and math.abs(rim) < 500, "feature height out of bounds")
                ''')

    def test_features_rise_above_the_base(self):
        for name in ('mountain', 'hill', 'ridge', 'plateau', 'volcano', 'cliff'):
            with self.subTest(feature=name):
                self.run_lua(f'''
                local ctx = {{ baseHeight = 0, center = Vector3.new(0, 0, 0), radius = 64, amplitude = 48, seed = 5 }}
                local value = TERRAIN.FEATURE_SHAPES["{name}"](0, 0, {{}}, ctx)
                assert(value > 1, "{name} should rise above the base, got " .. tostring(value))
                ''')


class WidgetLibrary(unittest.TestCase):
    def setUp(self):
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        widgets = region('UI_ENGINE.WIDGETS = {}', 'tools.ui_widget = function(args)')
        self.lua.execute('UI_ENGINE = {}\n' + widgets)

    def run_lua(self, text):
        return self.lua.execute(text)

    def walk(self, node, depth, seen):
        self.assertLessEqual(depth, 8, 'widget tree deeper than the engine limit')
        seen.append(node)
        rect = node['rect']
        self.assertIsNotNone(rect, 'every node needs a rect')
        for key in ('x', 'y', 'w', 'h'):
            value = rect[key]
            self.assertIsNotNone(value, f'missing rect.{key}')
            value = float(value)
            self.assertGreaterEqual(value, -50)
            self.assertLessEqual(value, 150)
        children = node['children']
        if children is not None:
            for index in range(1, len(children) + 1):
                child = children[index]
                if child is not None:
                    self.walk(child, depth + 1, seen)

    def test_all_eighteen_widgets_build_valid_specs(self):
        names = self.run_lua('return table.concat(UI_ENGINE.widgetNames(), ",")').split(',')
        self.assertEqual(len(names), 18, f'expected 18 widgets, found {len(names)}')
        for name in names:
            with self.subTest(widget=name):
                defn = self.run_lua(f'return UI_ENGINE.WIDGETS["{name}"]')
                self.assertIsNotNone(defn, 'widget definition missing')
                self.assertTrue(defn['label'])
                self.assertTrue(defn['summary'])
                self.assertTrue(defn['bestFor'])
                spec = defn['build'](self.lua.table())
                self.assertIsNotNone(spec)
                seen = []
                self.walk(spec, 0, seen)
                self.assertGreaterEqual(len(seen), 3, 'a widget must be more than an empty frame')

    def test_widget_items_are_used_when_given(self):
        spec = self.run_lua('return UI_ENGINE.WIDGETS["shop"].build({ title = "Gem Shop", items = { { name = "Speed Coil", price = "R$ 99" } } })')
        self.assertEqual(spec['children'][1]['text']['value'], 'Gem Shop')
        grid = spec['children'][3]
        first_card = grid['children'][1]
        self.assertEqual(first_card['text']['value'], 'Speed Coil')
        self.assertEqual(first_card['children'][1]['text']['value'], 'R$ 99')

    def test_widget_names_are_stable_and_searchable(self):
        names = self.run_lua('return table.concat(UI_ENGINE.widgetNames(), ",")').split(',')
        self.assertEqual(names, sorted(names), 'widget names must be sorted for deterministic output')
        for required in ('shop', 'inventory', 'battlepass', 'quests', 'settings', 'leaderboard',
                         'profile', 'dailyrewards', 'gacha', 'currency', 'hud', 'dialog',
                         'tooltip', 'hotbar', 'map', 'codex', 'tiers', 'social'):
            self.assertIn(required, names)


if __name__ == '__main__':
    unittest.main()
