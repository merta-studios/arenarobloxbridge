# 8.1.0 — UI Engine 4.0 beta candidate acceptance

Status: **unpublished beta-release candidate**. Do not promote until the user
has tested the Windows EXE and explicitly approved release.

## What changed

- UI Engine 4.0 with 40 distinct art-direction recipes (family, composition,
  signature, material query, icon style, gradient, text-shadow policy).
- Upgraded UIGradient support: Linear/Radial/Elliptical/Conical, Scale,
  Clamp/Repeat/Mirror, explicit `allowBeta=true`, measured capability probes,
  honest Linear/Clamp/Scale=1 fallback, stop and active-gradient budgets.
- Role-aware UICorner defaults: large panels/modals/headers/cards no longer
  inherit toy-button pill radii. Explicit user radii are preserved and audited.
- Real image workflow: `ui_texture action=inventory|search|recipe`, role-scoped
  `assets={panel,card,header}`, per-item artwork, full-opacity backgrounds,
  tile/crop/fit/stretch/9-slice. No blanket texture inheritance over icons.
- Calculated geometry: `ui_shape` (ear clipping → right-triangle altitude masks
  → rotated Frames in CanvasGroups, aspect lock, memory fallback).
- Path2D UI suite in `ui_path`: native stroke-only cubic splines, presets,
  inspect/sample/edit, arc-length layouts with real image markers, motion along
  a curve, card/skill-tree connectors, and rebuilt progress arcs over a track.
  Older Studio gets an explicitly approximate cubic-bezier Frame polyline.
  `GetLength` is cached on inspect and never polled by the 30 Hz dirty-driven
  LocalScript runtime. Progress is rebuilt geometry, not a fake native trim API.
- Offset-copy text shadows with layout-safe wrapper and runtime sync.
- Emoji-only artwork is rejected across declarative UI, generic property writes,
  `run_lua` and inserted scripts. Mixed dialogue emoji needs explicit opt-in.
- New tools: `ui_gradient`, `ui_shape`, `ui_path`, `ui_text`, `ui_design`.
- Session builds stay on their own branch; promotion verifies a source+EXE
  provenance manifest before copying anything into `release/`.

## Offline evidence

- `python next-update/developer/tests/run_offline_tests.py` → 33/33 passed
  (including the expanded Path2D suite; `test_v810_ui.py` alone: 19/19).
- New Lua runtime tests execute the embedded engine against GUI doubles:
  gradients/fallback, corners, shadows+sync, emoji guards, preflight rollback,
  role textures, all 18 widgets, shapes/paths, polygon rasterization, Path2D
  sampling/edit contracts, live layout/motion runtime, connectors, progress arcs,
  emoji-marker rollback and measured native capability probes.
- Tree-sitter PowerShell parse baseline unchanged; Lua parse/load checked.

## Still required before release (user / Windows / Roblox)

1. Windows PowerShell 5.1 parse + ps2exe build in CI (dispatched on this branch).
2. Start the candidate EXE on Windows; connect a real Studio place.
3. Enable Studio Beta *Upgraded UIGradients* and verify `ui_capabilities`.
4. Verify real Toolbox/uploaded image permissions and rendering in Studio.
5. Inspect phone/desktop fit, contrast, CanvasGroup memory on low quality.
6. Exercise `ui_path action=recipes`, then a wave layout with real images,
   a moving icon, a connector between two cards, and a 270° progress arc.
   Verify Play-mode runtime updates, older-Studio fallback reporting, and that
   no live game is published with beta gradient properties.
7. Only then explicitly run promotion (`confirm=RELEASE`) on main.

Roblox references: DevForum 4846594 (upgraded gradients, Studio Beta),
UIGradient/UICorner/CanvasGroup/Path2D/Path2DControlPoint creator docs and the
2D-paths guide. Beta property availability is not a live-publish guarantee.
