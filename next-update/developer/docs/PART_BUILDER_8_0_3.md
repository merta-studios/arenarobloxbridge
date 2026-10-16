# Ordinary Part builder – 8.0.3

This extends **`build_assembly`**, not `build_polygon_model` or Blender. These are ordinary Roblox Parts, local CSG unions/subtractions and editable compound Models. No external mesh upload is required. Honor explicit user requests and the existing Place's geometry conventions.

The authoritative machine-readable documentation is supplied to Arena in the session-start package and through `get_docs { tool: "build_assembly" }` / `GET /api/docs?tool=build_assembly`.

## Shapes

`Block`, `Ball`, `Cylinder`, `Wedge`, `CornerWedge`, `HalfBall`, `QuarterBall`, `HalfCylinder`, `QuarterCylinder`, `Tube`, `Ring`, `Torus`, `CurvedCylinder`, `Arch`, `Capsule`, `Cone`, `Pyramid`, `Stairs`, `SpiralStairs`, `Polyline`.

Shape names are case-insensitive and tolerate spaces, hyphens and underscores. `Dome` aliases `HalfBall`.

- `size` defaults to `[4,4,4]`, or uses `properties.Size`. All dimensions must be positive. For clipped shapes it describes the **source primitive's box**, not the surviving half's bounding box. Half shapes retain local `Y >= 0`; quarter shapes additionally retain `Z >= 0`.
- Roblox cylinders, half/quarter cylinders, `Tube` and `Capsule` run along local **X**. `Ring` runs along **Y**.
- `Tube`/`Ring`: outer `radius`, `wallThickness`, `length`; the inner cylinder extends through both ends. `wallThickness` must be strictly smaller than `radius` with at least 0.01 studs remaining.
- `CurvedCylinder`/`Arch`: radius, full cross-section `thickness`, `angle` in degrees (1–360), `startAngle`, `segments` (2–64), `fuse` (default true). They follow an arc in the local **XZ plane**. Curves require `thickness <= 1.8 * radius`. The builder increases too-small segment counts to at least `ceil(angle / 45)` and cuts shared miter planes to avoid protruding cylinder ends. `Arch` uses rectangular segments. These are segmented approximations, not analytic spline geometry.
- `Torus`: the curved-cylinder recipe with a forced 360° sweep. Radius/thickness/segments/fuse are the same controls.
- `Capsule`: local-X shaft plus two balls, using `radius` and overall `length > 2 * radius`. It remains an editable compound Model.
- `Cone`: **stepped approximation** made of 2–64 cylinders, default 16. Do not describe it as a mathematically smooth cone.
- `Pyramid`: four planar CSG cuts in the source box.
- `Stairs`: `steps` (1–128) within the source box, rising along local Z.
- `SpiralStairs`: `steps`, `radius`, total `angle`; `size` controls tread dimensions and total rise.
- `Polyline`: 2–129 local `points`, cylinder `thickness`, ball joins at intermediate points. It is not a polygon-mesh tool.

A single surviving piece returns its actual Part/UnionOperation; compound recipes return a Model. Inspect the result's `className` and `partCount`, rather than assuming every virtual shape is one native Part. Roblox CSG may shift the surviving Part's center/bounds; an anchor refers to the **actual returned instance or Model pivot**.

## Bridge-calculated relative placement

```json
{
  "modelName": "PartsDemo",
  "defaults": {"Anchored": true, "Material": "SmoothPlastic"},
  "items": [
    {
      "id": "base",
      "shape": "Block",
      "size": [12, 1, 12],
      "position": [20, 1, 0],
      "orientation": [0, 90, 0]
    },
    {
      "id": "dome",
      "shape": "HalfBall",
      "size": [8, 8, 8],
      "relativeTo": "base",
      "offset": [0, 0.5, 0]
    },
    {
      "id": "pipe",
      "shape": "CurvedCylinder",
      "radius": "6",
      "thickness": "1",
      "angle": "120",
      "segments": "12",
      "relativeTo": "base",
      "offset": [0, 4, 0]
    },
    {
      "id": "posts",
      "name": "Post{n}",
      "shape": "Cylinder",
      "size": [4, 0.5, 0.5],
      "orientation": [0, 0, 90],
      "relativeTo": "base",
      "offset": [-4, 2, -4],
      "repeatSpec": {"count": "3", "offset": [0, 0, 4]}
    },
    {
      "id": "cap",
      "shape": "Ball",
      "size": [1, 1, 1],
      "relativeTo": "posts[3]",
      "offset": [2, 0, 0]
    }
  ]
}
```

`relativeTo` can be an earlier item `id` (or its name/index fallback), a repeated anchor such as `posts[3]`, or an existing Roblox instance reference. No forward references. IDs/names used as anchors must be unique. `posts` means the first repetition. The Bridge computes all CFrames:

- default local placement: `anchorFrame * CFrame(offset) * requestedPositionAndOrientation`;
- `space: "world"`: translate the anchor by the world-space offset before composing the requested transform;
- without an anchor, `position` is world-space and an optional `offset` adds a world translation;
- `repeatSpec.offset` is a per-copy offset in the item's frame;
- circular repeats use `repeatSpec.radius`, `angleStep` (default 360/count), `startAngle`, `heightStep`;
- optional assembly `pivot` moves the complete result after construction.

Use `properties`, `attributes` and property-only `defaults` for ordinary Roblox style/behavior. For shape recipes, their geometry owns `Size`, `Shape` and final transform; style properties do not overwrite those computed values. Traditional `className` + `properties` items continue to work without a `shape`.

## Performance and failures

Use one `build_assembly` call instead of hundreds of small tool calls. Limit curved segments to the visual fidelity actually needed; `fuse: false` avoids the final union when an editable compound is preferable, but still performs miter cuts.

- Hard ceiling: **2,000 created primitives**, including temporary CSG cutters, and **96 CSG operations** per assembly. `maxParts` can lower the primitive budget, never raise it.
- Repetition counts and dimensions accept numeric strings; boolean property strings are normalized. Invalid/non-finite dimensions and malformed vectors fail instead of silently becoming zero/defaults.
- Geometry, references, budgets or CSG failure destroy **only the newly created assembly**, returning `ASSEMBLY_ROLLED_BACK`. Existing anchors are not modified.
- Individual property issues are returned in `errors`; they are not silently reported as successful property changes. Inspect warnings even when geometry creation succeeds.
- Results include `primitiveCount`, `csgOperations`, created references, `supportedShapes` and measurements of a small sample.
- Native CSG can yield or be refused by Studio. Offline tests use doubles; visually verify actual shape surfaces and collisions in Studio before release. See [V8_0_3_ACCEPTANCE.md](V8_0_3_ACCEPTANCE.md).
