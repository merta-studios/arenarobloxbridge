# Optional Organic Geometry Diagnostics

**Current policy (7.6.3):** The user’s explicit request and the target Place’s
established conventions decide the design, method, color, detail and motion.
Parts, assemblies, polygons and meshes can all be appropriate for any subject;
Blender is a recommendation for suitable new smooth/dense geometry, not a
requirement. Simple, stylized, primitive, monochrome, static and blockout work
are valid when they match the brief.

`organic=true`, `organicKind`, `organicTraits` and `ArenaOrganicBuild` are
optional metadata for per-model measurements. They do not require a particular
builder, loft, number of colors, anatomy, wings, animation, fresh audit or
`report_done` gate. Names alone do not select a style or method. The measurements
below are observations to compare with the user brief and Place—not a checklist
to satisfy.

## Optional loft geometry

When a user or Place selects the polygon builder, `build_polygon_model.volumes`
can describe a form whose cross-section changes along a centerline. Each section
contains a center and `heightRadius`/`depthRadius`; the bridge builds rings,
connects them with faces and can close the ends. This is one available method,
not a creature-only requirement.

```text
build_polygon_model {
  modelName = "OptionalLoftExample",
  organic = true,                 // optional diagnostic marker
  organicKind = "creature",      // optional descriptive metadata
  volumes = [{
    name = "Body", role = "body", sides = 10,
    sections = [
      {center={x=-2,y=2,z=0}, heightRadius=0.45, depthRadius=0.40},
      {center={x=-1,y=2,z=0}, heightRadius=0.80, depthRadius=0.65},
      {center={x= 0,y=2,z=0}, heightRadius=0.90, depthRadius=0.72},
      {center={x= 1,y=2,z=0}, heightRadius=0.72, depthRadius=0.58}
    ]
  }]
}
```

The schema’s geometry validation still applies when using a loft: sections need
usable centers/radii, and generated faces must be valid. A higher section count
or 8–16 sides can create a smoother silhouette, but is only a modeling choice.
`model_audit` may report the section count, side count, bounds, skipped faces and
cross-section ratios as `observations`; a different representation or profile
is valid. A missing `body`/`head` role is reported only as “not measured”, not as
missing required geometry.

## Optional features and measurements

The audit can measure role-tagged parts such as `eye_left`, `eye_right`,
`pupil_left`, `pupil_right`, `wing_left` and `wing_right`. These tags make the
matching measurements more specific; they do not require visible eyes,
physical pupils, wings, bilateral anatomy or any one-sided convention. Painted,
stylized, abstract, faceless, static or otherwise unusual designs remain valid
when requested or established by the Place.

For example, when separate physical eye parts are wanted, `build_assembly`
items can carry role attributes:

```text
items = [
  {className="Part", name="Eye_Left", properties={Shape="Ball"},
   attributes={ArenaOrganicRole="eye_left"}},
  {className="Part", name="Eye_Right", properties={Shape="Ball"},
   attributes={ArenaOrganicRole="eye_right"}}
]
```

`model_audit` returns `organicQuality.observations` and, for explicitly marked
creatures, per-model `observations` alongside any measured `creatureMetrics`.
Examples include loft bounds/section counts, role-tagged eye or wing positions,
polygon-triangle counts, color counts and an enabled-motion-script heuristic.
No observation is an error code or completion blocker. In particular:

- No polygon triangles is a representation measurement, not a polygon demand.
- Palette variety and dominant-color shares describe the measured colors; they
do not require a palette change.
- No matching motion script means only that the heuristic found none; static
  geometry is valid unless motion was requested or is a Place convention.
- Body/head depth, eye placement and wing bounds are shape heuristics, not
  universal anatomy rules.
- `finishScore` and `grade` are part-count/representation estimates, not a
  rating of artistic quality or a completion decision.

Audits are optional. If the user requests one, report what was measured and
compare the result with the actual brief. Do not add geometry, color or motion
just to clear an unrelated measurement. `report_done` is not blocked by organic
markers, observations, grade estimates, placeholders or blockout candidates.
The one geometry-specific pending workflow is an explicitly generated
`build_mesh_model` slot whose requested Roblox mesh geometry has not yet been
applied; the bridge may then report `MESH_UPLOAD_PENDING` and the concrete
upload/application step.

## Cylinder measurement note

A Roblox `CylinderPart` extends along its local X axis: `Size.X` is the length,
and `Size.Y`/`Size.Z` are diameters. This is a useful coordinate fact when
building or inspecting a cylinder. Axis/proportion warnings are heuristics;
wheels, discs, horizontal cylinders and intentional diagonal shapes should be
judged against the requested design.

```lua
local function cylinderBetween(parent, a, b, diameter, props)
    local delta = b - a
    local length = delta.Magnitude
    if length < 0.01 then return nil end
    local axis = delta.Unit
    local ref = (math.abs(axis.Y) > 0.99)
        and Vector3.new(0, 0, 1) or Vector3.new(0, 1, 0)
    local z = axis:Cross(ref).Unit
    local y = z:Cross(axis).Unit
    local part = Instance.new("Part")
    part.Shape = Enum.PartType.Cylinder
    part.Size = Vector3.new(length, diameter, diameter)
    part.CFrame = CFrame.fromMatrix((a + b) * 0.5, axis, y, z)
    part.Parent = parent
    return part
end
```

## Validation boundaries

Offline source/structure tests can verify schemas, advisory wording, persistence
and the absence of completion gates. They cannot verify Roblox Studio rendering
or the visual result. A Windows PowerShell parse/build check and an actual
Studio review are separate release checks; this document does not claim they
have run.
