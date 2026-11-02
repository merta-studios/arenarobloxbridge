#!/usr/bin/env python3
"""8.1.x UI Engine 4.0: execute real embedded Lua against offline GUI doubles.

This proves construction, math, fallbacks and guard behavior. It does not claim
to reproduce Roblox's renderer, asset permissions or live-client beta support.
"""
from pathlib import Path
import math
import unittest
from lupa import LuaRuntime

ROOT = Path(__file__).resolve().parents[2]
SOURCE = (ROOT / 'app/ArenaBridge.ps1').read_text(encoding='utf-8-sig')
FIXTURE = (Path(__file__).parent / 'fixtures/gui_runtime.lua').read_text()


def region(start, end):
    a = SOURCE.index(start)
    return SOURCE[a:SOURCE.index(end, a)]


class UiEngine40(unittest.TestCase):
    def setUp(self):
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        engine = region('UI_ENGINE = {}', 'local function runAssetImport(args, assetId, parent)')
        guard = region('function UI_ENGINE.guardCommand(tool, args)', 'executeTool = function(tool, args, insideBatch)')
        self.lua.execute(FIXTURE + '\n' + engine + '\n' + guard)

    def run_lua(self, code):
        return self.lua.execute(code)

    def test_forty_distinct_art_directions(self):
        self.assertEqual(self.run_lua('local n=0; for _ in pairs(UI_ENGINE.SKINS) do n=n+1 end; return n'), 40)
        self.run_lua('''
        local seen={}
        for name in pairs(UI_ENGINE.SKINS) do
            local d=assert(UI_ENGINE.DIRECTIONS[name], name)
            assert(d.family and d.composition and d.signature and d.iconStyle, name)
            local key=d.family.."|"..d.composition.."|"..d.signature
            assert(not seen[key], "duplicate art direction: "..name)
            seen[key]=true
        end
        ''')

    def test_released_gradients_need_no_opt_in_and_report_release_status(self):
        result = self.run_lua('''
        local parent=Instance.new("Frame")
        local g,r=UI_ENGINE.gradient(parent,{{0,Color3.new(1,0,0)},{1,Color3.new(0,0,1)}},45,nil,"G",
            {type="conical",scale=1.5,tileMode="mirror"})
        assert(r.type=="conical" and r.scale==1.5 and r.tileMode=="mirror")
        assert(r.releaseStatus=="released" and r.requiresOptIn==false and r.betaRequired==false)
        assert(r.livePublishReady==true and r.fallback==false)
        assert(g.Type==Enum.GradientType.Conical and g.Scale==1.5 and g.TileMode==Enum.GradientTileMode.Mirror)
        assert(g:GetAttribute("ArenaGradientBeta")==false and g:GetAttribute("ArenaGradientReleaseStatus")=="released")
        -- Old callers may still pass allowBeta=false/true; it must not gate a released API.
        local old,f=UI_ENGINE.gradient(parent,{{0,Color3.new()},{1,Color3.new(1,1,1)}},0,nil,"Old",
            {type="radial",scale=2,tileMode="repeat",allowBeta=false})
        assert(f.type=="radial" and f.scale==2 and f.tileMode=="repeat" and f.fallback==false)
        assert(old.Type==Enum.GradientType.Radial and old.Scale==2 and old.TileMode==Enum.GradientTileMode.Repeat)
        return true
        ''')
        self.assertTrue(result)

    def test_legacy_studio_falls_back_only_for_unsupported_properties(self):
        self.assertTrue(self.run_lua('''
        UI_ENGINE._caps={gradientType=true,gradientScale=false,gradientTileMode=true,
            gradientTypes={Linear=true,Radial=true,Elliptical=false,Conical=true},
            gradientTileModes={Clamp=true,Repeat=true,Mirror=true}}
        local parent=Instance.new("Frame")
        local g,r=UI_ENGINE.gradient(parent,{{0,Color3.new()},{1,Color3.new(1,1,1)}},0,nil,"Partial",
            {type="conical",scale=2,tileMode="mirror"})
        assert(r.type=="conical" and r.tileMode=="mirror" and r.scale==1)
        assert(r.fallback==true and r.fallbacks.scale==1 and r.fallbacks.type==nil)
        assert(g.Type==Enum.GradientType.Conical and g.TileMode==Enum.GradientTileMode.Mirror and g.Scale==1)
        local h,e=UI_ENGINE.gradient(parent,{{0,Color3.new()},{1,Color3.new(1,1,1)}},0,nil,"OldType",
            {type="elliptical",scale=1,tileMode="clamp"})
        assert(e.type=="linear" and e.fallbacks.type=="linear")
        assert(h.Type==Enum.GradientType.Linear)
        return true
        '''))

    def test_audit_does_not_treat_historical_beta_marker_as_publish_block(self):
        self.assertTrue(self.run_lua('''
        local screen=Instance.new("ScreenGui"); screen.Parent=game:GetService("StarterGui")
        local frame=Instance.new("Frame"); frame.BackgroundColor3=Color3.fromRGB(30,30,30); frame.Size=UDim2.fromScale(0.5,0.5); frame.Position=UDim2.fromScale(0.25,0.25); frame.AnchorPoint=Vector2.new(0.5,0.5); frame.Parent=screen
        local g=Instance.new("UIGradient"); g.Parent=frame
        g:SetAttribute("ArenaGradientBeta",true)
        local r=tools.ui_audit({ref=describeRef(screen).id})
        assert(r.ok, tostring(r.error))
        assert(r.result.gradientBudget.releaseStatus=="full-release")
        assert(r.result.gradientBudget.legacyBetaMarkers==1)
        assert(r.result.problems.betaGradients==nil)
        assert(r.result.counts.gradientFallbacks==0)
        g:SetAttribute("ArenaGradientFallback",true)
        local f=tools.ui_audit({ref=describeRef(screen).id})
        assert(f.result.counts.gradientFallbacks==1 and #f.result.problems.gradientFallbacks==1)
        return true
        '''))

    def test_gradient_stop_budget_and_invalid_times(self):
        self.run_lua('''
        local ok=pcall(function()
            local stops={}
            for i=0,6 do stops[#stops+1]={i/6,Color3.new()} end
            UI_ENGINE.gradient(Instance.new("Frame"),stops)
        end)
        assert(not ok)
        local bad=pcall(UI_ENGINE.gradient,Instance.new("Frame"),{{0.5,Color3.new()},{0.2,Color3.new()}})
        assert(not bad)
        ''')

    def test_role_corners_do_not_turn_panels_into_pills(self):
        result = self.run_lua('''
        local skin=UI_ENGINE.resolveSkin("candy")
        local panel=UI_ENGINE.cornerForRole(skin,"panel")
        local card=UI_ENGINE.cornerForRole(skin,"card")
        local explicit=UI_ENGINE.cornerForRole(skin,"panel","pill")
        assert(UI_ENGINE.radiusPixels(panel,900,600)<=22)
        assert(UI_ENGINE.radiusPixels(card,220,180)<=18)
        assert(explicit=="pill")
        assert(UI_ENGINE.radiusPixels(0.5,100,40)==20)
        return true
        ''')
        self.assertTrue(result)

    def test_offset_text_shadow_and_runtime_sync(self):
        self.assertTrue(self.run_lua('''
        local screen=Instance.new("ScreenGui")
        local skin=UI_ENGINE.resolveSkin("comic")
        local label,shadow,block=UI_ENGINE.textNode(screen,{value="PLAY",display=true,shadow={offsetY=0.08}},skin,UI_ENGINE.caps())
        assert(label.Parent==shadow.Parent and label.Parent==block)
        assert(shadow.ZIndex==label.ZIndex-1)
        assert(math.abs(shadow.Position.Y.Scale-label.Position.Y.Scale-0.08)<1e-9)
        assert(label:FindFirstChild("ArenaTextStroke"))
        UI_ENGINE.installTextRuntime(screen,{textShadows=1,warnings={}})
        script={Parent=screen}; assert(load(UI_ENGINE.TEXT_SHADOW_RUNTIME))()
        label.Text="START"; label.TextSize=27
        assert(shadow.Text=="START" and shadow.TextSize==27)
        local again=UI_ENGINE.installTextRuntime(screen,{textShadows=1,warnings={}})
        assert(again==nil or again.Name=="ArenaTextEffects")
        return true
        '''))

    def test_emoji_art_is_blocked_but_explicit_dialogue_is_not(self):
        self.assertTrue(self.run_lua('''
        assert(UI_ENGINE.guardEmoji("🔥","icon","ui"))
        assert(UI_ENGINE.guardEmoji("🔥!","label","ui"))
        assert(UI_ENGINE.guardEmoji("1️⃣","label","ui"))
        assert(UI_ENGINE.guardEmoji("Hello 🔥","label","ui"))
        assert(not UI_ENGINE.guardEmoji({value="Hello 🔥",allowEmojiText=true},"label","ui"))
        assert(UI_ENGINE.guardCommand("set_property",{property="Text",value="🔥"}))
        assert(UI_ENGINE.guardCommand("create_instance",{properties={Text="🔥"}}))
        assert(UI_ENGINE.guardCommand("run_lua",{source='local x=Instance.new("TextLabel"); x.Text="🔥"'}))
        assert(not UI_ENGINE.guardCommand("run_lua",{source='print("hello")'}))
        return true
        '''))

    def test_preflight_rejects_before_mutation(self):
        self.assertTrue(self.run_lua('''
        local before=#game:GetService("StarterGui"):GetDescendants()
        local r=tools.build_interface({skin="minimal",surfaces={{role="panel",text="OK",children={{role="icon",text="🔥"}}}}})
        assert(r.ok==false and r.code=="BAD_ARGS")
        assert(#game:GetService("StarterGui"):GetDescendants()==before)
        return true
        '''))

    def test_real_images_are_role_scoped_not_blanket_inherited(self):
        self.assertTrue(self.run_lua('''
        local r=tools.build_interface({skin="minimal",assets={panel="111",card="222"},
            surfaces={{role="panel",text="Title",children={{role="card",text="Item"},{role="card",text="Plain"}}}}})
        assert(r.ok, tostring(r.error))
        assert(#r.result.imageAssets>=2)
        local ok=pcall(UI_ENGINE.assetRef,"not-an-id"); assert(not ok)
        assert(UI_ENGINE.assetRef("123")=="rbxassetid://123")
        return true
        '''))

    def test_all_widgets_build_with_their_compositions(self):
        names = self.run_lua('return table.concat(UI_ENGINE.widgetNames(),",")').split(',')
        self.assertEqual(len(names), 18)
        for name in names:
            with self.subTest(widget=name):
                self.run_lua(f'''
                local r=tools.ui_widget({{kind="{name}",skin="tycoon",items={{ {{name="Sword",price="R$ 10",image="123"}},{{name="Shield",price="R$ 20"}} }}}})
                assert(r.ok, tostring(r.error))
                ''')

    def test_shape_and_native_path_construction(self):
        self.assertTrue(self.run_lua('''
        local r=tools.ui_shape({shape="trapezoid",skin="scifi"})
        assert(r.ok and r.result.report.canvasGroups>0 and r.result.report.aspectLocked)
        assert(r.result.report.segmentedGradient==true)
        local p=tools.ui_path({points={{x=0,y=0},{x=50,y=100},{x=100,y=0}},closed=true,thickness=4,
            gradient={type="radial"}})
        assert(p.ok and p.result.report.mode=="Path2D" and p.result.report.strokeOnly)
        return true
        '''))

    def test_path_fallback_is_cubic_and_explicit(self):
        self.assertTrue(self.run_lua('''
        UI_ENGINE._caps={canvasGroup=false,path2D=false,pathControlPoints=false,pathSampling=false,gradientType=false,gradientScale=false,gradientTileMode=false,gradientTypes={},gradientTileModes={}}
        local p=tools.ui_path({points={{x=0,y=50,right={x=30,y=-40}},{x=100,y=50,left={x=-30,y=-40}}},gradient={type="conical"}})
        assert(p.ok and p.result.report.mode=="cubic-bezier Frame fallback (approximate)")
        assert(p.result.report.fallbackSegments>2 and p.result.report.gradient.segmented)
        local ref=p.result.path.id
        local mid=tools.ui_path({action="sample",ref=ref,t=0.5})
        assert(mid.ok and mid.result.approximate and mid.result.samples[1].position.yScale<0.5)
        local e=tools.ui_path({action="edit",ref=ref,operation="update",index=1,point={x=0,y=60}})
        assert(e.ok and e.result.mode:find("fallback"))
        local s=tools.ui_shape({shape="trapezoid",gradient=false})
        assert(s.ok and s.result.report.memoryFallback==true)
        return true
        '''))

    def test_path_presets_sampling_and_edit_contracts(self):
        self.assertTrue(self.run_lua('''
        local ring=tools.ui_path({preset="ring",radius=40,thickness=5})
        assert(ring.ok and ring.result.report.closed and ring.result.report.aspectLocked)
        local ref=ring.result.path.id
        local inspect=tools.ui_path({action="inspect",ref=ref})
        assert(inspect.ok and inspect.result.length and inspect.result.boundingRect)
        local again=tools.ui_path({action="inspect",ref=ref})
        assert(again.result.lengthCached==true)
        local arc=tools.ui_path({action="sample",ref=ref,count=9,arcLength=true})
        local par=tools.ui_path({action="sample",ref=ref,count=9,arcLength=false})
        assert(arc.ok and par.ok and #arc.result.samples==9)
        local function dist(a,b) local dx=(a.position.xScale-b.position.xScale)*400; local dy=(a.position.yScale-b.position.yScale)*300; return math.sqrt(dx*dx+dy*dy) end
        local d1=dist(arc.result.samples[1],arc.result.samples[2]); local d2=dist(arc.result.samples[4],arc.result.samples[5])
        assert(math.abs(d1-d2)<2, "arc-length spacing should be visually even")
        local before=inspect.result.data.points
        local bad=tools.ui_path({action="edit",ref=ref,operation="remove",index=99})
        assert(not bad.ok)
        local after=tools.ui_path({action="inspect",ref=ref})
        assert(#after.result.data.points==#before)
        local upd=tools.ui_path({action="edit",ref=ref,operation="update",index=1,point={x=50,y=10}})
        assert(upd.ok and math.abs(upd.result.data.points[1].y-10)<1e-9)
        return true
        '''))

    def test_path_layout_motion_and_runtime_are_live_and_bounded(self):
        self.assertTrue(self.run_lua('''
        local p=tools.ui_path({preset="wave"})
        local ref=p.result.path.id
        local l=tools.ui_path({action="layout",ref=ref,items={{image="111"},{image="222"},{image="333"}},rotateToTangent=true})
        assert(l.ok and l.result.report.targets==3)
        local m=tools.ui_path({action="motion",ref=ref,item={image="999"},mode="loop",duration=1})
        assert(m.ok)
        local holder=resolveRef(ref)
        local runtime=holder:FindFirstChild("ArenaPathRuntime")
        assert(runtime and runtime.Source:find("GetLength")==nil, "runtime must not poll GetLength")
        script=runtime; assert(load(runtime.Source))()
        local target=holder:FindFirstChild("PathLinks"):FindFirstChild("MotionTarget").Value
        local before=target.Position
        fireHeartbeat(0.1); fireHeartbeat(0.1)
        assert(target.Position~=before, "motion should move the target")
        local c=tools.ui_path({action="control",ref=ref,playing=false,t=0.25})
        assert(c.ok and c.result.playing==false)
        fireHeartbeat(0.1)
        local items={}; for i=1,25 do items[i]={image="123"} end
        local budget=tools.ui_path({action="layout",ref=ref,items=items})
        assert(not budget.ok)
        return true
        '''))

    def test_path_connector_and_progress_are_explicit_constructions(self):
        self.assertTrue(self.run_lua('''
        local gui=Instance.new("ScreenGui"); gui.Parent=game:GetService("StarterGui")
        local a=Instance.new("Frame"); a.Size=UDim2.fromOffset(80,40); a.Position=UDim2.fromOffset(20,20); a.Parent=gui
        local b=Instance.new("Frame"); b.Size=UDim2.fromOffset(80,40); b.Position=UDim2.fromOffset(250,180); b.Parent=gui
        local con=tools.ui_path({action="connect",parentRef=describeRef(gui).id,fromRef=describeRef(a).id,toRef=describeRef(b).id,curvature=0.5})
        assert(con.ok and con.result.report.kind=="connector")
        local holder=resolveRef(con.result.path.id)
        assert(holder:FindFirstChild("PathLinks"):FindFirstChild("From").Value==a)
        local p=tools.ui_path({action="progress",value=0.25,sweep=270,trackThickness=8})
        assert(p.ok and p.result.report.progressPolicy:find("NOT a native"))
        local pref=p.result.path.id
        local ph=resolveRef(pref)
        assert(ph:FindFirstChild("ProgressPath") and ph:FindFirstChild("ProgressLabel"))
        local sp=tools.ui_path({action="set_progress",ref=pref,value=0.8})
        assert(sp.ok and math.abs(sp.result.value-0.8)<1e-9)
        assert(ph:FindFirstChild("ProgressLabel").Text=="80%")
        local runtime=ph:FindFirstChild("ArenaPathRuntime"); script=runtime; assert(load(runtime.Source))()
        ph:SetAttribute("ArenaProgress",0.5); fireHeartbeat(0.1)
        assert(ph:FindFirstChild("ProgressLabel").Text=="50%")
        return true
        '''))

    def test_path_markers_reject_emoji_art_and_native_caps_are_probed(self):
        self.assertTrue(self.run_lua('''
        local before=#game:GetService("StarterGui"):GetDescendants()
        local r=tools.ui_path({preset="line",markers={{text="🔥"}}})
        assert(not r.ok and r.code=="BAD_ARGS")
        assert(#game:GetService("StarterGui"):GetDescendants()==before)
        local caps=UI_ENGINE.caps(true)
        assert(caps.path2D and caps.pathControlPoints and caps.pathSampling and caps.pathTangents)
        assert(caps.pathEditing and caps.pathChangedEvent and caps.pathLength and caps.pathBounds)
        assert(caps.pathPointBudget==50 and caps.pathMaxControlPoints==100)
        return true
        '''))

    def test_polygon_rejects_self_intersection_and_degeneracy(self):
        self.run_lua('''
        local ok=pcall(UI_ENGINE.polygonTriangles,{{0,0},{100,100},{0,100},{100,0}}); assert(not ok)
        local flat=pcall(UI_ENGINE.polygonTriangles,{{0,0},{50,0},{100,0}}); assert(not flat)
        local t=UI_ENGINE.polygonTriangles({{20,0},{80,0},{100,100},{0,100}})
        assert(#t==2)
        ''')

    def test_right_triangle_masks_rasterize_to_the_polygon(self):
        # Independently rasterize the emitted transforms in pixel space. A point
        # is painted iff it lies inside a CanvasGroup and its rotated fill Frame.
        points = [(20, 0), (80, 0), (100, 100), (0, 100)]
        aspect = 1.6
        tris = self.run_lua('return UI_ENGINE.polygonTriangles({{20,0},{80,0},{100,100},{0,100}})')
        masks = []
        for tri in tris.values():
            masks.extend(self.lua.eval('function(t,a) return UI_ENGINE.rightTriangleMasks(t,a) end')(tri, aspect).values())

        def inside(poly, x, y):
            signs = []
            for i, a in enumerate(poly):
                b = poly[(i + 1) % len(poly)]
                signs.append((b[0]-a[0])*(y-a[1])-(b[1]-a[1])*(x-a[0]))
            return all(v >= -1e-7 for v in signs) or all(v <= 1e-7 for v in signs)

        errors = 0
        for iy in range(1, 100, 2):
            for ix in range(1, 100, 2):
                px, py = ix*aspect, iy
                painted = False
                for m in masks:
                    ang = math.radians(m.rotation)
                    dx, dy = px-m.x*aspect, py-m.y
                    lx = (dx*math.cos(ang)+dy*math.sin(ang))/(m.w*aspect) + .5
                    ly = (-dx*math.sin(ang)+dy*math.cos(ang))/m.h + .5
                    if not (0 <= lx <= 1 and 0 <= ly <= 1):
                        continue
                    fa = math.radians(180-m.diagonal)
                    dw, dh = 1/math.cos(math.radians(m.diagonal)), 1/math.sin(math.radians(m.diagonal))
                    qx, qy = (lx-1)*m.w*aspect, ly*m.h
                    fx = (qx*math.cos(fa)+qy*math.sin(fa))/(dw*m.w*aspect)
                    fy = (-qx*math.sin(fa)+qy*math.cos(fa))/(dh*m.h)
                    if 0 <= fx <= 1 and 0 <= fy <= 1:
                        painted = True
                        break
                if painted != inside(points, ix, iy):
                    errors += 1
        self.assertLessEqual(errors, 16, f"mask raster differs from polygon at {errors} samples")


class RegistrationAndGuides(unittest.TestCase):
    def test_new_tools_registered_in_lua_and_docs(self):
        docs = region('function Get-ToolDocs', 'function Get-DocsResponse')
        for tool in ('ui_gradient', 'ui_shape', 'ui_path', 'ui_text', 'ui_design'):
            self.assertIn(f"tools.{tool} = function", SOURCE)
            self.assertIn(f"name = '{tool}'", docs)
        self.assertIn("'ui_texture','ui_design','ui_gradient','ui_shape','ui_path','ui_text'", SOURCE)
        self.assertIn('ui_texture action=search', SOURCE)

    def test_guides_cover_beta_corners_assets_geometry_and_emoji(self):
        guide = region('uiEngineRules = @{', 'coordinateGuide = @(')
        for marker in ('fully released by Roblox on 2026-10-29', 'min(width,height)', 'action=inventory', 'CanvasGroup', 'offset-copy', 'Emoji-only', 'Path2D', 'GetPositionOnCurveArcLength', 'stroke-only'):
            self.assertIn(marker, guide)
        self.assertIn('uiDesignRules = @{', SOURCE)


if __name__ == '__main__':
    unittest.main()
