# 8.1.1 — Roblox release-status correction

Status: **unpublished beta-release candidate**. This patch corrects the Bridge's
Roblox API release-status handling. It does not promote anything to `release/`.

## Verified official status

- Roblox staff update, 2026-10-29: Upgraded UIGradients are **fully released**
  and available to publish in experiences. The `Upgraded UIGradients` flag was
  removed from Studio Beta Features. Elliptical was added after the Studio Beta.
  Source: https://devforum.roblox.com/t/full-release-upgraded-ui-gradients/4846594
- Path2D full release: 2024-06-17. Source:
  https://devforum.roblox.com/t/path2d-full-release/3027288
- Some narrative Creator Docs pages still contain stale beta callouts. The
  Bridge follows the newer official staff release announcement plus live
  property probes, not the stale callout.

## Code changes

- Removed the `allowBeta=true` requirement from UIGradient application.
- Old callers may still pass `allowBeta`; it is accepted and ignored.
- Gradient reports now expose `releaseStatus="released"`, `requiresOptIn=false`,
  `livePublishReady=true` and per-property capability fallbacks.
- Capability probes remain: an older Studio that lacks Type/Scale/TileMode still
  gets an explicit Linear/Clamp/Scale=1 fallback, but only for the unsupported
  property. No Beta Features toggle is suggested.
- `ui_capabilities`, `ui_design`, tool docs and session guides no longer describe
  upgraded gradients as beta or forbid live publication because of beta status.
- `ui_audit` no longer treats historical `ArenaGradientBeta=true` markers as a
  publication problem. It reports actual capability fallbacks instead.
- Path2D capability metadata records its full-release status. Path2D remains
  stroke-only; progress arcs remain rebuilt geometry, not a native trim API.
- Other unrelated beta/preview features are not reclassified by this patch.

## Offline evidence

- `test_v810_ui.py` covers: no-opt-in released gradients, old `allowBeta=false`
  compatibility, partial legacy Studio fallback, and audit behavior for
  historical beta markers vs actual fallbacks.
- Full offline suite and Windows PowerShell 5.1 parse/build run in CI before the
  candidate EXE is replaced.

## Still required before Bridge release

1. Start the candidate EXE on Windows and connect a current Roblox Studio place.
2. Run `ui_capabilities refresh=true`; confirm gradient probes pass without any
   Beta Features toggle.
3. Apply a conical/radial/elliptical gradient without `allowBeta` and inspect it
   in Studio and Play mode.
4. Exercise Path2D layout/motion/connectors/progress as in the 8.1.0 acceptance
   notes.
5. Only after user approval, explicitly promote the candidate on main.
