#!/usr/bin/env python3
"""Execute the actual embedded Parts builder with Roblox math/CSG test doubles."""
from pathlib import Path
import unittest
from lupa import LuaRuntime

ROOT = Path(__file__).resolve().parents[2]
SOURCE = (ROOT / 'app/ArenaBridge.ps1').read_text(encoding='utf-8-sig')

def region(start, end):
    a = SOURCE.index(start)
    return SOURCE[a:SOURCE.index(end, a)]

class PartsRuntime(unittest.TestCase):
    def setUp(self):
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        fixture = (Path(__file__).parent / 'fixtures/parts_runtime.lua').read_text()
        decode = region('local function decodeValue(value)', 'local commonProps =')
        apply = region('local function applyProperties(inst, properties)', 'local function createOne(spec)')
        vec = region('function MASTER_BUILD.vec3(value)', 'function MASTER_BUILD.parseScript')
        build = region('MASTER_BUILD.partShapes =', '\n\n-- ---------------------------------------------------------------------------\n-- UI ENGINE')
        self.lua.execute(fixture + '\n' + decode + '\n' + apply + '\n' + vec + '\n' + build)

    def run_lua(self, text):
        return self.lua.execute(text)

    def test_complete_plugin_compiles_without_execution(self):
        start = SOURCE.index("function Get-PluginSource {\n@'\n") + len("function Get-PluginSource {\n@'\n")
        end = SOURCE.index("\n'@\n}", start)
        self.lua.compile(SOURCE[start:end])

    def test_malformed_vectors_do_not_silently_default(self):
        for vector in ('{x="typo",y=1,z=2}', '{x=math.huge,y=0,z=0}', '{x=false,y=1,z=2}', '"not a vector"'):
            with self.subTest(vector=vector):
                self.run_lua('local r=tools.build_assembly({items={{shape="Ball",size=' + vector + '}}}); assert(not r.ok)')

    def test_every_recipe_executes(self):
        self.run_lua('''
        for _,shape in ipairs(MASTER_BUILD.partShapes) do
            local reply=tools.build_assembly({items={{id="shape",shape=shape,points={{x=0,y=0,z=0},{x=4,y=0,z=0},{x=4,y=4,z=0}}}}})
            assert(reply.ok,shape..": "..tostring(reply.error))
            assert(reply.result.count==1 and reply.result.created[1].partCount>0,shape)
            assert(reply.result.primitiveCount<=2000,shape)
        end
        ''')

    def test_local_and_world_offsets_rotated_anchor(self):
        self.run_lua('''
        local reply=tools.build_assembly({items={
            {id="base",shape="Block",position={x=10,y=2,z=3},orientation={x=0,y=90,z=0}},
            {id="local",shape="Ball",relativeTo="base",offset={x=2,y=3,z=0}},
            {id="world",shape="Ball",relativeTo="base",offset={x=2,y=3,z=0},space="world"}
        }})
        assert(reply.ok,reply.error)
        local a=reply.result.created[2].instance.CFrame.Position
        local b=reply.result.created[3].instance.CFrame.Position
        assert(math.abs(a.X-10)<1e-8 and a.Y==5 and math.abs(a.Z-1)<1e-8)
        assert(b.X==12 and b.Y==5 and b.Z==3)
        ''')

    def test_repeats_and_reference_by_repeat_index(self):
        self.run_lua('''
        local reply=tools.build_assembly({defaults={Anchored=true},items={
            {id="post",name="Post{n}",shape="Cylinder",repeatSpec={count="3",offset={x="5",y="0",z="0"}}},
            {id="cap",shape="Ball",relativeTo="post[3]",offset={x=0,y=2,z=0}}
        }})
        assert(reply.ok,reply.error)
        assert(reply.result.count==4)
        assert(reply.result.created[3].name=="Post3")
        assert(reply.result.created[4].instance.CFrame.Position.X==10)
        assert(reply.result.created[4].instance.Anchored==true)
        ''')

    def test_legacy_class_properties_and_numeric_strings(self):
        self.run_lua('''
        local reply=tools.build_assembly({items={{className="Part",name="Legacy",properties={Size={x="2",y="4",z="6"},Position={x="1",y="3",z="5"},Transparency="0.25",Anchored="true"},attributes={ArenaOrganicRole="eye_left"}}}})
        assert(reply.ok,reply.error)
        local part=reply.result.created[1].instance
        assert(part.Size.Y==4 and part.CFrame.Position.Z==5)
        assert(part.Transparency==0.25 and part.Anchored==true)
        assert(part.attributes.ArenaOrganicRole=="eye_left")
        ''')

    def test_csg_failure_rolls_back_not_anchor(self):
        self.run_lua('''
        local anchor=Instance.new("Part");anchor.Parent=fixture.workspace
        fixture.refs={external=anchor};fixture.failCSG=true
        local reply=tools.build_assembly({items={{id="base",shape="Block"},{shape="HalfBall",relativeTo="external"}}})
        assert(not reply.ok and reply.code=="ASSEMBLY_ROLLED_BACK")
        assert(not anchor.destroyed)
        for _,p in ipairs(fixture.pool) do assert(p==anchor or p==fixture.workspace or p.destroyed,"leaked "..p.Name) end
        ''')

    def test_budget_and_bad_reference_rollback(self):
        for args in ('maxParts=1,items={{shape="HalfBall"}}',
                     'maxParts=0,items={{shape="Block"}}',
                     'items={{id="x",shape="Block"},{id="x",shape="Ball"}}',
                     'items={{shape="Ball",relativeTo="future"}}',
                     'items={{shape="NOPE"}}',
                     'items={{shape="Tube",radius=1,wallThickness=2}}',
                     'items={{shape="Block",repeatSpec={count=2001}}}'):
            with self.subTest(args=args):
                self.run_lua('fixture.pool={fixture.workspace}; local r=tools.build_assembly({' + args + '''}); assert(not r.ok)
                for _,p in ipairs(fixture.pool) do assert(p==fixture.workspace or p.destroyed,"leaked "..p.Name) end''')

    def test_curve_miters_and_segment_guard(self):
        self.run_lua('''
        local reply=tools.build_assembly({items={{shape="CurvedCylinder",angle="360",segments="2",radius=8,thickness=1}}})
        assert(reply.ok,reply.error)
        assert(reply.result.csgOperations==9) -- minimum 8 cuts + 1 fuse
        assert(reply.result.primitiveCount==24) -- 8 cylinders + 16 cutters
        assert(reply.result.created[1].className=="UnionOperation")
        local cut=fixture.csg[1]
        assert(#cut.cutters==2 and cut.cutters[1].destroyed and cut.base.destroyed)
        ''')

    def test_nonfused_and_approximation_are_models(self):
        self.run_lua('''
        local reply=tools.build_assembly({items={{id="arc",shape="CurvedCylinder",fuse=false},{id="cone",shape="Cone"}}})
        assert(reply.ok,reply.error)
        assert(reply.result.created[1].className=="Model")
        assert(reply.result.created[2].className=="Model")
        assert(reply.result.created[2].partCount==16)
        ''')

if __name__ == '__main__':
    unittest.main()
