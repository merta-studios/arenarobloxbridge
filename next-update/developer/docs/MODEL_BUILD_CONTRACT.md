# Project-First 3D Geometry Guide

**Method priority:** follow the user's explicit method or style first; otherwise
inspect and preserve the target Place's established geometry conventions; only
then use general recommendations. This file documents available builders; it
does not impose one builder on every task. Parts, assemblies, polygons and
Blender meshes are all valid when requested or when they fit the Place. Do not
convert existing geometry merely to satisfy a generic preference.

Blender (`build_mesh_model`) is a recommendation for suitable greenfield
geometry—especially smooth or dense forms—not a requirement. Polygon geometry
(`build_polygon_model`) is available whenever it matches the task, the user's
request or the Place convention; it does not require a special permission flag.
Native Parts and `build_assembly` are equally valid when appropriate. Keep a
truly simple object simple and honor requests for primitives, blockout, low part
count, or a deliberately plain style.

## Choose the right geometry tool

| Need or established convention | Suitable option (not a forced choice) |
|---|---|
| Existing Place uses Parts, meshes, polygons, or a particular pipeline | Preserve and extend that convention |
| Custom panels, crisp low-poly surfaces, or a polygon-based Place | `build_polygon_model` |
| Smooth/dense geometry where the Blender pipeline fits | `build_mesh_model` (Blender) |
| Named polygon components/material groups, if using polygons | `build_polygon_model.submodels` |
| Long form whose cross-section changes along a path, if using polygons | `build_polygon_model.volumes` |
| Repeated stairs, rails, ribs, windows, spokes, structural frames or modules | `build_assembly` or the Place's established method |
| Standard shapes, simple geometry, or an explicit Parts request | Native `Part`/`WedgePart`; batch repeated instances |

One polygon is **one planar skin**, not a solid model. A front-view outline with
thickness is still a thin plate. For a closed object, build every required face
(front/back/sides/ends) with shared coordinates, or set `closeOpenings=true` on
a submodel to ask the builder to cap unmatched boundary loops. Explicit faces
are more predictable than relying on automatic caps.

## How to form the call

1. Inspect the target Place/selection and avoid deleting or replacing user work
   without permission. Pick a consistent local coordinate frame, model bounds,
   style and major components before writing geometry.
2. Choose the builder from the explicit request and observed Place convention.
   If polygons are the appropriate choice, make one structured
   `build_polygon_model` call for the principal silhouette. Group surfaces by
   named `submodels` with unique names (especially names referenced by
   `mainWelds`); use each submodel's `style` for its color/material role. Add
   repeated structure with `build_assembly`, then accents/details with the
   appropriate build/refine tools. If a different method is requested or
   established, use that method instead.
3. A polygon is `{name, points=[{x,y,z}, ...], style?}`. Give it at least three
   distinct, ordered points on one plane. Use a simple boundary loop: no
   self-intersection, duplicate/collinear runs, or arbitrary point cloud. A
   closing copy of the first point is unnecessary. Split complicated outlines
   into a few simple faces; concave simple faces are supported.
4. Points define the geometry. `origin` translates the whole result,
   `rotation` rotates it in degrees, and `scale` scales it. Do not try to place
   or resize a polygon through `style.properties.Position`, `Size`, `CFrame`,
   or `Orientation`; those geometry properties are deliberately ignored.
5. Choose a deliberate thickness, color, material, anchoring and collision
   policy. Polygon faces are triangulated into two `WedgePart`s per triangle
   and are welded inside each submodel by default. Leave `autoWeld` enabled
   unless separate physical pieces are intentional. For a moving/unanchored
   model, set the relevant parts `anchored=false` and define `mainWelds` between
   named submodels where needed.
6. For a tapered/curved volume, provide `volumes=[{name,role,sides,sections}]`.
   Each section gives `center`, `heightRadius` and `depthRadius`; valid positive
   radii and distinct adjacent centers are required by the geometry schema.
   More stations/sides can produce a smoother outline but consume more geometry
   budget. Creature/body/head measurements are optional heuristics, not stricter
   build requirements.
7. Read the **build result**, not only `ok`: `incomplete`, `facesSkipped`,
   `skipped` and `fallbackFaces` describe polygon-builder output. If the task
   requires a closed/complete polygon shell, inspect those fields and repair
   actual missing or invalid faces. The default budget is 4,000 WedgeParts
   (`maxWedges` may be raised to 10,000). Roughly estimate
   `2 * (pointCount - 2)` WedgeParts per polygon, plus generated caps.
8. `model_audit`, `world_audit` and visual Studio review are optional ways to
   inspect a result. Use them when requested or useful; compare findings with
   the brief and Place convention. Do not turn heuristic grade, palette,
   primitive/part-count, placeholder or phase observations into a completion
   requirement. Be honest about what was or was not visually checked.

## Working example: a closed low-poly house shell

The front is at **−Z**. The seven shell faces share exact edge coordinates;
`Walls` and `Roof` have separate visual roles. Door and window are intentionally
separate, slightly forward-facing detail skins. This is one optional reference
payload, not a required style or code to install in a Script.

```text
build_polygon_model {
  modelName = "LowPolyHouse",
  grade = "lowpoly",
  origin = {x=0, y=0, z=0},
  rotation = {x=0, y=0, z=0},
  scale = 1,
  style = {thickness=0.04, anchored=true, canCollide=true},
  submodels = [
    {
      name = "Walls",
      style = {color="#D7B77E", material="SmoothPlastic"},
      polygons = [
        {name="FrontGable", points=[{x=-2,y=0,z=-1},{x=2,y=0,z=-1},{x=2,y=3,z=-1},{x=0,y=5,z=-1},{x=-2,y=3,z=-1}]},
        {name="BackGable",  points=[{x=2,y=0,z=1},{x=-2,y=0,z=1},{x=-2,y=3,z=1},{x=0,y=5,z=1},{x=2,y=3,z=1}]},
        {name="LeftWall",   points=[{x=-2,y=0,z=-1},{x=-2,y=0,z=1},{x=-2,y=3,z=1},{x=-2,y=3,z=-1}]},
        {name="RightWall",  points=[{x=2,y=0,z=-1},{x=2,y=3,z=-1},{x=2,y=3,z=1},{x=2,y=0,z=1}]},
        {name="Floor",      points=[{x=-2,y=0,z=-1},{x=2,y=0,z=-1},{x=2,y=0,z=1},{x=-2,y=0,z=1}]}
      ]
    },
    {
      name = "Roof",
      style = {color="#A65F35", material="SmoothPlastic"},
      polygons = [
        {name="LeftSlope",  points=[{x=-2,y=3,z=-1},{x=0,y=5,z=-1},{x=0,y=5,z=1},{x=-2,y=3,z=1}]},
        {name="RightSlope", points=[{x=0,y=5,z=-1},{x=2,y=3,z=-1},{x=2,y=3,z=1},{x=0,y=5,z=1}]}
      ]
    },
    {
      name = "FrontDetails",
      style = {thickness=0.025, thicknessPlacement="center", canCollide=false},
      polygons = [
        {name="Door", style={color="#59402F"}, points=[{x=-0.45,y=0,z=-1.04},{x=0.45,y=0,z=-1.04},{x=0.45,y=1.8,z=-1.04},{x=-0.45,y=1.8,z=-1.04}]},
        {name="Window", style={color="#79C9D0"}, points=[{x=0.75,y=2.0,z=-1.04},{x=1.35,y=2.0,z=-1.04},{x=1.35,y=2.6,z=-1.04},{x=0.75,y=2.6,z=-1.04}]}
      ]
    }
  ]
}
```

This example demonstrates a closed multi-face shell. Extend it with repeated
window frames/rails through `build_assembly` if those details fit the request;
replace the dimensions/colors or use another method to match the target Place.
The geometry rules apply only when choosing this polygon builder.

## Shape-specific patterns

- **Buildings/architecture:** polygon faces for gables, roofs, arches and
  facade silhouettes; `build_assembly` for repeated windows, columns and rails.
- **Vehicles:** possible options include `volumes` for tapered forms, polygons
  for panels, assemblies for repeated pieces, or the Place's existing method.
- **Furniture/props:** use the representation, number of parts and finish that
  fit the brief; Parts, meshes, polygons and assemblies are all available.
- **Machines/tools/weapons:** named components and mechanical detail can help
  when they are requested; no shell-first method is mandatory.
- **Terrain/set pieces:** polygons, lofts, native parts or existing assets can
  fit different styles. `site_survey`, `world_style` and `world_audit` are
  optional tools for relevant large/new world work.

Low-poly can describe a faceted style, but the requested scope determines how
much structure is appropriate. A deliberately simple or blockout result can be
complete; grade metadata is optional and no global score decides whether the
work is finished.

## Optional mesh path: Blender, automated Open Cloud upload, bridge insertion

Use `build_mesh_model` when the user requests it, the Place establishes a mesh
workflow, or Blender is a good fit for new smooth/dense geometry. It is neither
a mandatory default nor a replacement requirement for Parts or polygons. Once
this path is selected, the following bridge pipeline applies.

The capability probe behind `blender_status` runs **the same runner text** as
every real build (`runner.py`: empty scene, slot script, OBJ export, centring,
measurement). Since 7.4.2 the runner imports `bpy` at module level — in
7.4.0/7.4.1 it was imported only inside `main()`, which made `arena_export()`
die with `NameError: name 'bpy' is not defined` on all three export paths
(`state="failed"`, `probe="failed"`, `ready=false` even with a working
Blender). If the probe fails, read the `detail` text: a `NameError` points at
the runner, a `TypeError` at a changed `bpy.ops.wm.obj_export` parameter.

Workflow (own the whole loop, never fake it):

1. `blender_status` — is Blender ready? If not, `build_mesh_model` answers
   `BLENDER_NOT_READY`; tell the user honestly. The check can be repeated at
   any time — click row 4 of the start screen or call
   `blender_status { action: "check" }`; that always runs the real capability
   probe. Alternatively keep building with `build_polygon_model`.
2. `build_mesh_model` — one Blender script per slot, `offset` per slot,
   `origin` for the model. It returns a `jobId` immediately: **Blender runs in
   the background, so never wait synchronously.** Each slot becomes one
   MeshPart.

   **One connected model per slot is a useful default, not a rule.** If it
   matches the user request and Place, a tree or prop that moves as one rigid
   object can be a single mesh. Use multiple slots when the user/Place requests
   separate pieces, parts need independent movement or properties, or size and
   triangle limits call for it. Do not merge or split components solely to obey
   this general recommendation.

   **AXES AND UNITS (7.5.1) — the one truth:** 1 Blender unit = 1 stud, and
   inside the slot script **Z is up** (Blender convention). The runner exports
   the whole model into the Roblox frame (Blender +Z becomes Roblox +Y, the
   other axis becomes depth; the FBX/GLB upload comes from the same centred
   scene as the measured OBJ). So build a tree upright along Z in the script —
   it arrives upright in Roblox. Never build "up" along Blender Y because
   Roblox has Y up: that produced the lying tree in 7.4/7.5 (a trunk measured
   7.96 studs along Z instead of Y). Never rotate axes yourself, never pass
   your own `forward_axis`/`up_axis`, never convert units. `mesh_status`
   reports the measured size already in Roblox studs (x width, y height,
   z depth) — if the measurement looks wrong, fix the SCRIPT, not the export.
3. `mesh_status` — poll it (not in a tight loop) until the slots show measured
   triangles and size in studs. The bridge measures the OBJ itself: triangles,
   vertices, bounding box in studs, file size. A slot above the limit (~10,000
   triangles) is rejected — build it simpler (fewer subdivisions, Decimate or
   Remesh, smaller slots).
4. The bridge creates the **rectangular MeshPart placeholders** with the
   measured size, position and rotation, marked with `ArenaMeshSlot` /
   `ArenaMeshState` / `ArenaPlaceholder`.
5. **You upload — the user does nothing (7.5.0).** Roblox has no mesh upload
   API *in Studio*, but it has an official one over Open Cloud
   (`POST https://apis.roblox.com/assets/v1/assets`). The bridge uses exactly
   that: the user stores his own Roblox Open Cloud API key ONCE in the bridge
   settings (section "ROBLOX OPEN CLOUD", with a collapsible tutorial that also
   names the required rights: **assets + read + write**). From then on
   `upload_asset { slotKey }` sends the FBX/GLB file the bridge already built
   (`mesh_status` names it under `uploadPath`) to Roblox and answers with the
   **real asset id**;
   `POST https://apis.roblox.com/assets/v1/assets` is the only upload path, and
   the bridge derives the asset owner (user or group) itself from the key via
   the official introspect endpoint
   (`POST https://apis.roblox.com/api-keys/v1/introspect`) — the user types
   neither a name nor an id, and a failed upload always answers with the exact
   `filePath`/`filePathHint` so the file can be uploaded by hand if needed; `mesh_apply_asset { slots = [ { key, assetId } ] }` puts
   the geometry into the existing placeholders. The mesh window "Mesh-Uploads"
   is **removed** since 7.5.0 — there is no manual step left.
   If the key is missing, `upload_asset` answers `OPENCLOUD_KEY_MISSING` with a
   German `userMessage`: say that sentence to the user verbatim and wait — do
   not ask for an asset id and do not report done. `mesh_cancel` / `mesh_drop`
   discard a slot (placeholder and files are deleted; an already applied mesh is
   NOT restored).
6. Insertion uses `InsertService:CreateMeshPartAsync` + `MeshPart:ApplyMesh`,
   because `MeshPart.MeshId` is write-restricted. The **existing** instance
   survives: name, size, position, welds, attributes and animations stay. The
   answer reports the mesh id **read back** from the place.
7. `model_audit` counts mesh placeholders separately (`meshSlotCount` /
   `meshSlots`) and `report_done` answers `MESH_UPLOAD_PENDING` while a
   placeholder still waits for its upload. "Done" would be a lie — say what is
   missing and where the files are. Only a `handoff` can end the turn honestly
   while a mesh is still waiting.

Hard rules for Blender scripts (the bridge rejects violations before start):

- One slot = one script = one MeshPart (ONE MODEL = ONE MESH, see above).
  1 Blender unit = 1 stud, **Z is up in the script** (the export turns it into
  Roblox Y), the runner centres the bbox automatically and applies modifiers
  on export.
- Allowed: `bpy`, `bmesh`, `math`, `mathutils`, `random` and ordinary mesh
  code. Forbidden: `os`, `sys`, `subprocess`, `shutil`, `socket`, `urllib`,
  `requests`, `ctypes`, `winreg`, `__import__`, `importlib`, `eval`, `exec`,
  `bpy.ops.wm.*` and every export function — scene, export, centring and
  measurement belong to the bridge.
- Roblox keeps **one** colour/material per MeshPart and no Blender materials.
  Set `color`/`material` per slot; use more slots instead of more materials in
  Blender.
- A mesh is a black box inside the place: the honest evidence is the bridge's
  OBJ measurement, the read-back mesh id and the user's visual check.
