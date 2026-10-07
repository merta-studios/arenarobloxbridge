# Universal 3D Model Build Contract

This contract applies to **every nontrivial visible 3D build**—props, furniture,
buildings, vehicles, tools, machines, landmarks, set pieces, characters,
creatures, plants, and custom shapes. It is not an animal-only rule. Keep a
truly simple object simple, and honor an explicit request for primitives,
blockout, low part count, or a plain style. For a nontrivial custom silhouette,
`build_polygon_model` is the first model-building call. **Exception since
7.4.0:** for shapes that wedges cannot carry (smooth or organic surfaces, very
high detail, or a model that must not become thousands of parts), the
**Blender mesh path** (`build_mesh_model`) is the better first call — see
"Mesh path" below. Everything else in this contract still applies.

## Choose the right geometry tool

| Need | Preferred tool |
|---|---|
| Custom silhouette, angled/curved/tapered panel, hull, roof, body shell or other authored shape | `build_polygon_model` |
| Smooth/organic surface, very fine detail, or a shape where thousands of Wedges are too heavy | `build_mesh_model` (Blender mesh path, 7.4.0) |
| Several named components/materials built together | `build_polygon_model.submodels` |
| Long form whose cross-section changes along a path (hull, shaft, handle, column, branch, pipe) | `build_polygon_model.volumes` |
| Repeated stairs, rails, ribs, windows, spokes, structural frames or modules | `build_assembly` alongside the custom silhouette |
| A genuinely standard shape or small support, pivot, connector or accent | Native `Part`/`WedgePart`; batch repeated instances |

One polygon is **one planar skin**, not a solid model. A front-view outline with
thickness is still a thin plate. For a closed object, build every required face
(front/back/sides/ends) with shared coordinates, or set `closeOpenings=true` on
a submodel to ask the builder to cap unmatched boundary loops. Explicit faces
are more predictable than relying on automatic caps.

## How to form the call

1. Inspect the target Place/selection and avoid deleting or replacing user work
   without permission. Pick a consistent local coordinate frame, model bounds,
   style and major components before writing geometry.
2. Make one structured `build_polygon_model` call for the principal silhouette.
   Group surfaces by named `submodels` with unique names (especially names
   referenced by `mainWelds`); use each submodel's `style` for its
   color/material role. Add repeated structure with `build_assembly`, then
   accents/details with the appropriate build/refine tools.
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
   Each section gives `center`, `heightRadius` and `depthRadius`; use at least
   three stations, 6–16 sides, radii >= 0.025 before global scaling, and
   noncoincident adjacent centers. More stations/sides produce a smoother
   outline but consume more geometry budget. This works for any suitable
   shape; the stricter body/head station counts apply only to creatures.
7. Check the **build result**, not only `ok`: `incomplete` must be false,
   `facesSkipped` must be zero and `skipped` empty. Read every `fallbackFaces`
   entry and warning; fix the named points/submodel instead of accepting a hole.
   The default budget is 4,000 WedgeParts (`maxWedges` may be raised to 10,000).
   Roughly estimate `2 * (pointCount - 2)` WedgeParts per polygon, plus any
   generated caps. Simplify or split coherent submodels if the budget is tight.
8. Use the returned model reference for `model_audit`, inspect measurements and
   fix the reported issues. For a scene, also run `world_audit`. Finish only
   after the real geometry has been checked; do not call a source file or a
   successful API response a visual inspection.

## Working example: a closed low-poly house shell

The front is at **−Z**. The seven shell faces share exact edge coordinates;
`Walls` and `Roof` have separate visual roles. Door and window are intentionally
separate, slightly forward-facing detail skins. The call is a structured tool
payload, not code to install in a Script.

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

This example demonstrates a multi-face object—not a one-polygon box. Extend it
with repeated window frames/rails through `build_assembly`, then audit the
returned model. Replace wall/roof dimensions and colors to create a different
building; the same workflow applies to a vehicle hull, furniture shell,
machine housing, prop, or other category.

## Shape-specific patterns

- **Buildings/architecture:** polygon faces for gables, roofs, arches and
  facade silhouettes; `build_assembly` for repeated windows, columns and rails.
- **Vehicles:** `volumes` for a tapered hull/body; polygons for windshields,
  fenders and panels; `build_assembly` for wheels, seats and repeated ribs.
- **Furniture/props:** polygon-built seat/back/housing/handles; modular supports
  and repeated legs from `build_assembly`; native parts only for standard
  connectors and accents.
- **Machines/tools/weapons:** a polygon or lofted primary shell first, then
  named panels, guards, grips, pivots and repeated mechanical details.
- **Terrain/set pieces:** polygons or lofts for distinctive rock/cliff/hill
  profiles, with `site_survey`, `world_style` and `world_audit` for placed
  scenes. Use voxel filling only when a regular filled region is actually
  intended.

Low-poly describes the facet style, not permission to omit the silhouette,
back/sides, meaningful components or finish. For a deliberately simple request,
keep it simple and record the requested grade instead of adding needless parts.

## Mesh path (7.4.0): Blender, upload by the user, insert by the bridge

`build_mesh_model` is the second, voluntary way to build a nontrivial model. Use
it when the polygon path would end in a poor shape or in thousands of Wedges,
not as a replacement for it.

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
   MeshPart, so split moving parts (limbs, wheels, doors) into their own slots
   and join them in Studio with Welds/Motor6D as usual.
3. `mesh_status` — poll it (not in a tight loop) until the slots show measured
   triangles and size in studs. The bridge measures the OBJ itself: triangles,
   vertices, bounding box in studs, file size. A slot above the limit (~10,000
   triangles) is rejected — build it simpler (fewer subdivisions, Decimate or
   Remesh, smaller slots).
4. The bridge creates the **rectangular MeshPart placeholders** with the
   measured size, position and rotation, marked with `ArenaMeshSlot` /
   `ArenaMeshState` / `ArenaPlaceholder`.
5. **The user uploads.** Roblox has no automatic mesh upload and no public API
   for it: the bridge window "Mesh-Uploads" opens by itself (modeless) as soon
   as a measured OBJ file waits for upload. The user uses "Ordner öffnen",
   uploads the OBJ file(s) in Studio (3D Importer or drag & drop) or in the
   Creator Dashboard, pastes the mesh id(s) into the text fields and presses
   "Fertig" — the bridge then inserts the geometry and deletes the OBJ file.
   "Stornieren" cancels a slot (placeholder and files are deleted; an already
   applied mesh is NOT restored). If the user
   gives you the id in chat, call `mesh_apply_asset` with the slot `key`s from
   `mesh_status`.
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

- One slot = one script = one MeshPart. 1 Blender unit = 1 stud, Y is up, the
  runner centres the bbox automatically and applies modifiers on export.
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
