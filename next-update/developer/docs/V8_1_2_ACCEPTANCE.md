# 8.1.2 — approximate Path2D closed-path fill

Status: **unpublished beta-release candidate**. This does not promote anything
to `release/`.

## What was added

Roblox Path2D still has **no native fill API**. 8.1.2 adds an explicit,
approximate Bridge fill for closed paths:

- `ui_path create closed=true fill=true` stacks smaller inset Path2D strokes
  behind the outline. Each fill layer is scaled toward the centroid, given a
  larger thickness, and placed at a lower ZIndex than the outline.
- Tuning: `fillColor`, `fillLayers` (1..16, default 8), `fillOverlap`
  (1..2, default 1.18), `fillZIndex`.
- `ui_path action=fill ref=... fill=true|false` toggles/rebuilds fill on an
  existing Arena path holder.
- `ui_path action=edit` rebuilds the fill stack after control-point edits and
  refuses to open a filled path unless fill is disabled first.
- Reports expose `fill.approximate=true`, `fill.nativeFill=false`,
  `nativeStrokeOnly=true`, layer/instance counts, thickness, ZIndex and concave
  risk. `strokeOnly=false` means the Bridge composition contains an approximate
  fill, not that Roblox added a native fill.
- Older Studio without Path2D uses the same inset idea with thick Frame
  polyline rings, capped to fewer layers, and reports the fallback method.

## Limits

- This is a visual stroke-stack approximation, not a vector fill.
- Concave or self-intersecting outlines can leave gaps or overdraw; the report
  warns and recommends `ui_shape` or a real image for critical artwork.
- Fill layers are static edit-mode geometry. They are rebuilt by Bridge
  create/edit/fill actions, not by a per-frame runtime fill algorithm.
- Inspect edges, memory and low-graphics quality in Studio before release.

## Offline evidence

- `test_v810_ui.py` covers native inset Path2D layers, lower ZIndex, larger
  thickness, fillColor, inspect/edit/toggle behavior, closed-path requirement,
  concave warning, layer budget clamping, and Frame fallback.
- Full offline suite and Windows PowerShell 5.1 parse/build run in CI before the
  candidate EXE is replaced.
