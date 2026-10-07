# Universal 3D Model Build Contract

This contract applies to **every nontrivial visible 3D build**—props, furniture,
buildings, vehicles, tools, machines, landmarks, set pieces, characters,
creatures, plants, and custom shapes. It is not an animal-only rule. Keep a
truly simple object simple, and honor an explicit request for primitives,
blockout, low part count, or a plain style. For a nontrivial custom silhouette,
`build_polygon_model` is the first model-building call.

## Choose the right geometry tool

| Need | Preferred tool |
|---|---|
| Custom silhouette, angled/curved/tapered panel, hull, roof, body shell or other authored shape | `build_polygon_model` |
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
