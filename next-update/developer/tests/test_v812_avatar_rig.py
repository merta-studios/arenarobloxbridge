#!/usr/bin/env python3
"""Offline tests for 8.1.2 Avatar Catalog & Character Rig Builder (R6/R15)
plus Upgraded UIShadow / Color3 Contrast registration & safety contracts.
"""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from lupa import LuaRuntime
import tree_sitter_powershell as tsp
from tree_sitter import Language, Parser

ROOT = Path(__file__).resolve().parents[2]
PS1 = ROOT / "app" / "ArenaBridge.ps1"
SOURCE = PS1.read_text(encoding="utf-8-sig")


def region(start: str, end: str) -> str:
    a = SOURCE.index(start)
    b = SOURCE.index(end, a + len(start))
    return SOURCE[a:b]


def extract_avatar_rig_lua() -> str:
    return region(
        "AVATAR_RIG = {}",
        "-- ------------------------- Mesh-Bau (Version 7.4.0) -------------------------",
    )


RIG_HARNESS_LUA = r"""
function math.clamp(v, a, b)
    if v < a then return a elseif v > b then return b end
    return v
end

local Vec3 = {}
Vec3.__index = function(v, k)
    if k == "Magnitude" then return math.sqrt(v.X*v.X + v.Y*v.Y + v.Z*v.Z) end
    if k == "Unit" then
        local m = v.Magnitude
        if m < 1e-9 then return Vector3.new(0, 0, 0) end
        return Vector3.new(v.X/m, v.Y/m, v.Z/m)
    end
    return Vec3[k]
end
Vec3.__add = function(a, b) return Vector3.new(a.X+b.X, a.Y+b.Y, a.Z+b.Z) end
Vec3.__sub = function(a, b) return Vector3.new(a.X-b.X, a.Y-b.Y, a.Z-b.Z) end
Vec3.__mul = function(a, b)
    if type(a) == "number" then a, b = b, a end
    return Vector3.new(a.X*b, a.Y*b, a.Z*b)
end
Vector3 = { new = function(x, y, z) return setmetatable({ X = x or 0, Y = y or 0, Z = z or 0, _type = "Vector3" }, Vec3) end }

local CF = {}
CF.__index = CF
CF.__mul = function(a, b)
    return CFrame.new(a.Position.X + b.Position.X, a.Position.Y + b.Position.Y, a.Position.Z + b.Position.Z, a._yaw + b._yaw)
end
CFrame = {
    new = function(x, y, z, yaw)
        if type(x) == "table" and x._type == "Vector3" then
            return setmetatable({ Position = x, _yaw = 0, _type = "CFrame" }, CF)
        end
        return setmetatable({ Position = Vector3.new(x or 0, y or 0, z or 0), _yaw = yaw or 0, _type = "CFrame" }, CF)
    end,
    Angles = function(rx, ry, rz)
        return setmetatable({ Position = Vector3.new(0, 0, 0), _yaw = ry or 0, _type = "CFrame" }, CF)
    end,
    lookAt = function(pos, target)
        local dx = target.X - pos.X
        local dz = target.Z - pos.Z
        return setmetatable({ Position = pos, _yaw = math.atan(-dx, -dz), _type = "CFrame" }, CF)
    end,
}

local C3 = {}
C3.__index = C3
Color3 = {
    new = function(r, g, b) return setmetatable({ R = r or 0, G = g or 0, B = b or 0, _type = "Color3" }, C3) end,
    fromRGB = function(r, g, b) return Color3.new((r or 0)/255, (g or 0)/255, (b or 0)/255) end,
}
function C3:ToHex()
    return string.format("%02X%02X%02X", math.floor(self.R*255 + 0.5), math.floor(self.G*255 + 0.5), math.floor(self.B*255 + 0.5))
end

Enum = setmetatable({}, {
    __index = function(t, k)
        local e = setmetatable({}, { __index = function(_, n) return setmetatable({ Name = n, Enum = k, _type = "EnumItem" }, { __tostring = function(s) return k .. "." .. s.Name end }) end })
        rawset(t, k, e)
        return e
    end
})

RaycastParams = { new = function() return { FilterType = nil, FilterDescendantsInstances = {} } end }

function typeof(v)
    if type(v) == "table" and v._type then return v._type end
    return type(v)
end

local Inst = {}
Inst.__index = Inst
local nextId = 0
local refs = {}

local function newInst(cls, name)
    nextId = nextId + 1
    local o = setmetatable({
        ClassName = cls,
        Name = name or cls,
        Parent = nil,
        _children = {},
        _attrs = {},
        _id = nextId,
        _type = "Instance",
    }, Inst)
    if cls == "HumanoidDescription" then
        o.Head = 0; o.Torso = 0; o.LeftArm = 0; o.RightArm = 0; o.LeftLeg = 0; o.RightLeg = 0
        o.Shirt = 0; o.Pants = 0; o.GraphicTShirt = 0; o.Face = 0
        o.HeadColor = Color3.fromRGB(255, 224, 189)
        o.TorsoColor = Color3.fromRGB(255, 224, 189)
        o.LeftArmColor = Color3.fromRGB(255, 224, 189)
        o.RightArmColor = Color3.fromRGB(255, 224, 189)
        o.LeftLegColor = Color3.fromRGB(255, 224, 189)
        o.RightLegColor = Color3.fromRGB(255, 224, 189)
        o.HeightScale = 1; o.WidthScale = 1; o.DepthScale = 1; o.HeadScale = 1
        o.ProportionScale = 0; o.BodyTypeScale = 0
        o.IdleAnimation = 0; o.WalkAnimation = 0; o.RunAnimation = 0; o.JumpAnimation = 0
        o.FallAnimation = 0; o.ClimbAnimation = 0; o.SwimAnimation = 0; o.MoodAnimation = 0
        o._accessories = {}
        function o:GetAccessories(includeRigid)
            local out = {}
            for _, a in ipairs(self._accessories) do
                if includeRigid or a.IsLayered then table.insert(out, a) end
            end
            return out
        end
        function o:SetAccessories(list, includeRigid)
            self._accessories = {}
            for _, a in ipairs(list or {}) do table.insert(self._accessories, a) end
        end
    elseif cls == "Humanoid" then
        o.RigType = Enum.HumanoidRigType.R15
        o.DisplayName = ""
        o._desc = newInst("HumanoidDescription")
        function o:GetAppliedDescription() return self._desc end
        function o:ApplyDescriptionAsync(d) self._desc = d end
        function o:ApplyDescription(d) self._desc = d end
    elseif cls == "Part" or cls == "MeshPart" then
        o.Size = Vector3.new(2, 2, 1)
        o.CFrame = CFrame.new(0, 3, 0)
        o.Anchored = false
    elseif cls == "Model" then
        o._pivot = CFrame.new(0, 3, 0)
        o._boxSize = Vector3.new(4, 6, 2)
        o.PrimaryPart = nil
        function o:GetBoundingBox() return self._pivot, self._boxSize end
        function o:GetPivot() return self._pivot end
        function o:PivotTo(cf)
            self._pivot = cf
            if self.PrimaryPart then self.PrimaryPart.CFrame = cf end
        end
    end
    return o
end

Inst.__newindex = function(t, k, v)
    if k == "Parent" then
        local old = rawget(t, "Parent")
        if old then
            for i, c in ipairs(old._children) do
                if c == t then table.remove(old._children, i); break end
            end
        end
        rawset(t, "Parent", v)
        if v then table.insert(v._children, t) end
        return
    end
    rawset(t, k, v)
end

function Inst:IsA(c)
    if self.ClassName == c then return true end
    if c == "BasePart" and (self.ClassName == "Part" or self.ClassName == "MeshPart") then return true end
    return false
end
function Inst:GetChildren() local o = {}; for _, c in ipairs(self._children) do table.insert(o, c) end; return o end
function Inst:GetDescendants()
    local o = {}
    local function walk(n)
        for _, c in ipairs(n._children) do table.insert(o, c); walk(c) end
    end
    walk(self)
    return o
end
function Inst:FindFirstChild(name) for _, c in ipairs(self._children) do if c.Name == name then return c end end end
function Inst:FindFirstChildOfClass(c) for _, x in ipairs(self._children) do if x.ClassName == c then return x end end end
function Inst:SetAttribute(k, v) self._attrs[k] = v end
function Inst:GetAttribute(k) return self._attrs[k] end
function Inst:GetFullName() return self.Parent and (self.Parent:GetFullName() .. "." .. self.Name) or self.Name end
function Inst:Clone()
    local c = newInst(self.ClassName, self.Name)
    for k, v in pairs(self) do
        if k ~= "_children" and k ~= "Parent" and k ~= "_id" and k ~= "_accessories" then
            c[k] = v
        end
    end
    if self._accessories then
        c._accessories = {}
        for _, a in ipairs(self._accessories) do table.insert(c._accessories, a) end
    end
    return c
end
function Inst:Destroy() self.Parent = nil end

Instance = { new = newInst }

local workspaceSvc = newInst("Workspace", "Workspace")
_TEST_GROUND_Y = 10
function workspaceSvc:Raycast(origin, dir, params)
    local floor = newInst("Part", "Baseplate")
    return { Position = Vector3.new(origin.X, _TEST_GROUND_Y, origin.Z), Instance = floor }
end

local playersSvc = newInst("Players", "Players")
function playersSvc:GetUserIdFromNameAsync(name)
    if name == "Builderman" then return 156 end
    error("Unknown username")
end
function playersSvc:GetHumanoidDescriptionFromUserId(uid)
    local d = newInst("HumanoidDescription")
    d.Shirt = 1001; d.Pants = 1002; d.Face = 1003
    d.TorsoColor = Color3.fromRGB(10, 20, 30)
    return d
end
function playersSvc:GetHumanoidDescriptionFromOutfitId(oid)
    local d = newInst("HumanoidDescription")
    if oid == 77701 then
        d.Head = 60801; d.Torso = 60802; d.LeftArm = 60803; d.RightArm = 60804; d.LeftLeg = 60805; d.RightLeg = 60806
    else
        d.Head = 50001; d.Torso = 50002
    end
    return d
end
function playersSvc:CreateHumanoidModelFromDescriptionAsync(desc, rigType)
    local m = newInst("Model", "CharacterRig")
    local hrp = newInst("Part", "HumanoidRootPart")
    hrp.CFrame = CFrame.new(0, 3, 0)
    hrp.Parent = m
    local head = newInst("Part", "Head"); head.Parent = m
    local torso = newInst("Part", rigType.Name == "R6" and "Torso" or "UpperTorso"); torso.Parent = m
    local hum = newInst("Humanoid", "Humanoid")
    hum.RigType = rigType
    hum._desc = desc
    hum.Parent = m
    m.PrimaryPart = hrp
    return m
end

local assetSvc = newInst("AssetService", "AssetService")
function assetSvc:GetBundleDetailsAsync(bundleId)
    if bundleId == 608 then
        return { Name = "Neoclassic Male v2", Items = { { Type = "UserOutfit", Id = 77701 } } }
    elseif bundleId == 9999 then
        return {
            Name = "Custom SciFi Bundle",
            Items = {
                { Type = "Asset", Id = 9001, Name = "SciFi Head" },
                { Type = "Asset", Id = 9002, Name = "SciFi Torso" },
                { Type = "Asset", Id = 9003, Name = "SciFi Left Arm" },
                { Type = "Asset", Id = 9004, Name = "SciFi Right Arm" },
                { Type = "Asset", Id = 9005, Name = "SciFi Left Leg" },
                { Type = "Asset", Id = 9006, Name = "SciFi Right Leg" },
            }
        }
    end
    error("Bundle lookup simulated offline fallback")
end

local marketSvc = newInst("MarketplaceService", "MarketplaceService")
local mockProducts = {
    [144076358] = { AssetTypeId = 11, Name = "Blue Jacket Classic Shirt" },
    [144076760] = { AssetTypeId = 12, Name = "Dark Jeans Classic Pants" },
    [1028606]   = { AssetTypeId = 8,  Name = "Red Baseball Cap" },
    [555001]    = { AssetTypeId = 67, Name = "3D Leather Jacket" },
    [555002]    = { AssetTypeId = 68, Name = "3D Cargo Pants" },
    [555003]    = { AssetTypeId = 41, Name = "Spiky Anime Hair" },
    [9001] = { AssetTypeId = 17, Name = "SciFi Head" },
    [9002] = { AssetTypeId = 27, Name = "SciFi Torso" },
    [9003] = { AssetTypeId = 29, Name = "SciFi Left Arm" },
    [9004] = { AssetTypeId = 28, Name = "SciFi Right Arm" },
    [9005] = { AssetTypeId = 30, Name = "SciFi Left Leg" },
    [9006] = { AssetTypeId = 31, Name = "SciFi Right Leg" },
}
function marketSvc:GetProductInfo(id)
    local info = mockProducts[id]
    if not info then error("No mock product for " .. tostring(id)) end
    return info
end

local services = {
    Workspace = workspaceSvc,
    Players = playersSvc,
    AssetService = assetSvc,
    MarketplaceService = marketSvc,
}
game = { GetService = function(_, n) return services[n] end }

function describeRef(inst)
    local id = "#" .. tostring(inst._id)
    refs[id] = inst
    return { id = id, name = inst.Name, className = inst.ClassName, path = inst:GetFullName() }
end
function resolveRef(r)
    if r == "game.Workspace" or r == "Workspace" then return workspaceSvc end
    if refs[r] then return refs[r] end
    return nil, "not found"
end
function decodeValue(v)
    if type(v) == "table" and v.type == "CFrame" and v.position then
        return CFrame.new(v.position.x or 0, v.position.y or 0, v.position.z or 0)
    end
    return nil
end
function ok(t) return { ok = true, result = t } end
function failCode(c, m) return { ok = false, code = c, error = m } end
function waypoint() end
tools = {}
"""


class AvatarRigLuaTests(unittest.TestCase):
    def setUp(self) -> None:
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute(RIG_HARNESS_LUA)
        self.lua.execute(extract_avatar_rig_lua())

    def test_templates_action_lists_all_11_standard_rigs(self) -> None:
        self.assertTrue(self.lua.execute("""
            local res = tools.build_rig({ action = "templates" })
            assert(res.ok == true)
            assert(res.result.count == 11)
            local found = {}
            for _, t in ipairs(res.result.templates) do found[t.name] = t end
            for _, req in ipairs({"blocky","noob","man","woman","manv2","womanv2","robloxian_2_0","boy","girl","neoclassic_male","classic_male"}) do
                assert(found[req] ~= nil, "missing template " .. req)
            end
            assert(found.man.bundleId == 238)
            assert(found.woman.bundleId == 239)
            assert(found.manv2.bundleId == 608)
            assert(found.womanv2.bundleId == 606)
            assert(found.robloxian_2_0.bundleId == 311)
            assert(found.boy.bundleId == 109)
            assert(found.girl.bundleId == 108)
            return true
        """))

    def test_build_r15_manv2_with_classic_layered_and_rigid_accessories(self) -> None:
        self.assertTrue(self.lua.execute("""
            local res = tools.build_rig({
                action = "build",
                template = "manv2",
                rigType = "R15",
                name = "HeroNPC",
                displayName = "Shopkeeper",
                shirt = 144076358,
                pants = 144076760,
                tshirt = 999111,
                face = 222333,
                layeredClothing = {
                    555001, -- auto-classified as Jacket (67)
                    { assetId = 555002, type = "Pants", order = 2, puffiness = 0.25 },
                },
                accessories = {
                    1028606, -- auto-classified as Hat (8)
                    { assetId = 555003, type = "Hair" },
                },
                skinColor = "#F2C7A5",
                scales = { height = 1.05, width = 0.95 },
                position = { x = 12, y = 0, z = -8 },
                snapToGround = true,
                yaw = 90,
                anchored = true,
            })
            assert(res.ok == true)
            local r = res.result
            assert(r.rig.name == "HeroNPC")
            assert(r.rigType == "R15")
            assert(r.anchored == true)
            assert(r.source.template == "manv2")
            assert(r.source.bundleId == 608)
            assert(r.placement.snappedToGround == true)
            -- Ground is at Y=10, rig box height=6, feet at Y=10 -> center Y=13
            assert(math.abs(r.placement.rootPosition.x - 12) < 1e-6)
            assert(math.abs(r.placement.rootPosition.y - 13) < 1e-6)
            assert(math.abs(r.placement.rootPosition.z - (-8)) < 1e-6)
            assert(r.description.shirt == 144076358)
            assert(r.description.pants == 144076760)
            assert(r.description.graphicTShirt == 999111)
            assert(r.description.face == 222333)
            -- Loaded outfitId 77701 from bundle 608
            assert(r.description.bodyParts.head == 60801)
            assert(r.description.bodyParts.torso == 60802)
            assert(#r.description.layeredClothing == 2)
            assert(#r.description.rigidAccessories == 2)
            assert(r.description.scales.height == 1.05)

            -- Inspect the spawned rig
            local insp = tools.build_rig({ action = "inspect", ref = r.rig.id })
            assert(insp.ok == true)
            assert(insp.result.description.shirt == 144076358)
            assert(#insp.result.description.layeredClothing == 2)
            assert(#insp.result.description.rigidAccessories == 2)

            -- Re-dress the rig with clearExisting=true
            local dress = tools.build_rig({
                action = "dress",
                ref = r.rig.id,
                clearExisting = true,
                shirt = 888111,
                pants = 888222,
                accessories = { { assetId = 1028606, type = "Hat" } },
            })
            assert(dress.ok == true)
            assert(dress.result.description.shirt == 888111)
            assert(dress.result.description.pants == 888222)
            assert(#dress.result.description.layeredClothing == 0)
            assert(#dress.result.description.rigidAccessories == 1)
            return true
        """))

    def test_build_r6_warns_on_layered_clothing_and_supports_noob_and_woman_fallbacks(self) -> None:
        self.assertTrue(self.lua.execute("""
            local r6 = tools.build_rig({
                template = "noob",
                rigType = "R6",
                layeredClothing = { { assetId = 555001, type = "Jacket" } },
                position = { 0, 5, 0 },
                anchorMode = "feet",
            })
            assert(r6.ok == true)
            assert(r6.result.rigType == "R6")
            assert(r6.result.source.template == "noob")
            -- Must warn that 3D layered clothing requires R15
            local sawR6Warn = false
            for _, w in ipairs(r6.result.warnings) do
                if tostring(w):find("R6") then sawR6Warn = true end
            end
            assert(sawR6Warn == true)

            -- Offline fallback body parts for "woman" bundle (239) when GetBundleDetailsAsync errors
            local w = tools.build_rig({ template = "female", rigType = "R15", position = { 5, 0, 5 } })
            assert(w.ok == true)
            assert(w.result.source.template == "woman")
            assert(w.result.description.bodyParts.head == 86498113)
            assert(w.result.description.bodyParts.torso == 86499666)

            -- Custom bundle without UserOutfit (body part asset list)
            local cb = tools.build_rig({ bundleId = 9999, rigType = "R15", lookAt = { x = 10, y = 0, z = 0 } })
            assert(cb.ok == true)
            assert(cb.result.description.bodyParts.head == 9001)
            assert(cb.result.description.bodyParts.torso == 9002)
            assert(cb.result.description.bodyParts.rightLeg == 9006)

            -- Clone user avatar by username
            local u = tools.build_rig({ username = "Builderman", rigType = "R15" })
            assert(u.ok == true)
            assert(u.result.source.userId == 156)
            assert(u.result.description.shirt == 1001)
            return true
        """))


class AvatarCatalogAndContractsTests(unittest.TestCase):
    def test_zero_top_level_locals_in_avatar_rig_module(self) -> None:
        lua = extract_avatar_rig_lua()
        top_locals = [line for line in lua.splitlines() if line.startswith("local ")]
        self.assertEqual(top_locals, [], f"AVATAR_RIG must add 0 top-level locals (Luau 200-local limit): {top_locals}")

    def test_powershell_avatar_catalog_and_inspect_contracts(self) -> None:
        search_fn = region("function Invoke-AvatarCatalogSearch(", "function Invoke-AvatarItemInspect(")
        inspect_fn = region("function Invoke-AvatarItemInspect(", "function Invoke-ToolboxServerTool(")
        thumb_fn = region("function Invoke-CatalogThumbnailBytes(", "function Get-AvatarRigTemplatesCatalog")
        toolbox_fn = region("function Invoke-ToolboxServerTool(", "function Invoke-Screenshot(")
        server_fn = region("function Invoke-ServerTool(", "'capture_screenshot'")

        # Catalog v2 API uses AssetTypeIds / BundleTypeIds (not broken Category/Subcategory)
        self.assertIn("https://catalog.roblox.com/v2/search/items/details?", search_fn)
        self.assertIn("AssetTypeIds=", search_fn)
        self.assertIn("BundleTypeIds=", search_fn)
        self.assertNotIn("Category=", search_fn)
        self.assertNotIn("Subcategory=", search_fn)
        # Uses single-attempt Invoke-CatalogHttp and official thumbnails.roblox.com
        self.assertIn("Invoke-CatalogHttp $searchUrl", search_fn)
        self.assertIn("https://thumbnails.roblox.com/v1/assets?assetIds=", search_fn)
        self.assertIn("https://thumbnails.roblox.com/v1/bundles/thumbnails?bundleIds=", search_fn)
        # Snaps API Limit to valid Catalog v2 sizes (10/28/30/60)
        for valid_size in ("$apiLimit = 10", "$apiLimit = 28", "$apiLimit = 30", "$apiLimit = 60"):
            self.assertIn(valid_size, search_fn)

        # Inspect supports assets, bundles, users + thumbnail download + base64 blob
        self.assertIn("https://economy.roblox.com/v2/assets/", inspect_fn)
        self.assertIn("https://catalog.roblox.com/v1/bundles/", inspect_fn)
        self.assertIn("https://users.roblox.com/v1/usernames/users", inspect_fn)
        self.assertIn("https://avatar.roblox.com/v1/users/", inspect_fn)
        self.assertIn("$downloadState = @{ count = 0 }", inspect_fn)
        self.assertIn("New-Blob $b64 'inspect_avatar_item'", inspect_fn)

        # Thumbnail downloader enforces HTTPS + rbxcdn.com + 2 MiB cap + no redirects
        self.assertIn("rbxcdn\\.com$", thumb_fn)
        self.assertIn("AllowAutoRedirect = $false", thumb_fn)
        self.assertIn("2097152", thumb_fn)

        # Routed through Toolbox throttle gate
        for tool in ("'search_avatar_catalog'", "'inspect_avatar_item'"):
            self.assertIn(tool, toolbox_fn)
            self.assertIn(tool, server_fn)

    def test_versions_and_registration_consistency(self) -> None:
        v_app = json.loads((ROOT / "app" / "version.json").read_text(encoding="utf-8"))
        v_beta = json.loads((ROOT / "beta-release" / "candidate.json").read_text(encoding="utf-8"))
        v_pub = json.loads((ROOT / "release" / "latest.json").read_text(encoding="utf-8"))
        self.assertEqual(v_app["version"], "8.1.2")
        self.assertEqual(v_beta["version"], "8.1.2")
        self.assertEqual(v_pub["version"], "8.0.5")

        docs = region("function Get-ToolDocs {", "function Get-BridgeGuides {")
        sets = region("function Get-ActivityToolSets {", "function Get-ArenaActivityText")
        for tool in ("ui_shadow", "search_avatar_catalog", "inspect_avatar_item", "build_rig"):
            self.assertIn(f"name = '{tool}'", docs)
            self.assertIn(f"'{tool}'", sets)
        self.assertIn("avatarRigRules = @{", SOURCE)

    def test_powershell_treesitter_warning_baseline_not_exceeded(self) -> None:
        parser = Parser(Language(tsp.language()))
        tree = parser.parse(PS1.read_bytes())
        errors = 0

        def walk(node) -> None:
            nonlocal errors
            if node.type == "ERROR" or node.is_missing:
                errors += 1
            for child in node.children:
                walk(child)

        walk(tree.root_node)
        self.assertLessEqual(errors, 8, f"PowerShell tree-sitter error baseline exceeded: {errors} > 8")


if __name__ == "__main__":
    unittest.main()
