beta-release/ contains the UNPUBLISHED 8.1.0 release candidate.

What is here
- ArenaRobloxBridge.exe - Windows x64 candidate built by GitHub Actions
  ("Exe Builder (Release-Kandidat)") from this branch. It carries exactly the
  version in app/version.json and the matching file version (8.1.0.0).
- candidate.json - provenance manifest: source fingerprint of app/ + builder/,
  EXE SHA-256/size/version, source commit, branch and workflow run. It is not a
  release manifest and is never served to installed bridges.

How to test
1. Download ArenaRobloxBridge.exe from this folder on the session branch.
2. Close the running bridge and start the candidate. Keep your normal release
   installation if you want an easy fallback.
3. In Roblox Studio enable File > Beta Features > Upgraded UIGradients and
   restart Studio if you want to test the new gradient modes. The bridge also
   works without the beta feature and reports the linear fallback.
4. Exercise ui_capabilities, ui_design, ui_texture inventory/search,
   ui_widget/build_interface, ui_shape, ui_path, ui_text and ui_audit.
5. Path2D additions: ui_path action=recipes; create preset=wave/ring;
   action=layout with real image items; action=motion + control;
   action=connect between two cards; action=progress + set_progress.
   Check Play-mode runtime, arc-length spacing, and the explicit cubic
   Frame fallback on older Studio. Progress arcs are rebuilt geometry,
   not a native Path2D trim property.

Important
- This folder publishes NOTHING. release/ and release/latest.json remain the
  last published version until an explicit promotion.
- Promotion is a separate manual workflow on main ("Release freigeben",
  confirm=RELEASE). It re-verifies candidate.json against the current source
  and EXE before copying anything into release/.
- Do not publish a live Roblox game using upgraded gradient properties while
  Roblox still marks them Studio Beta.
- Windows/Roblox live validation by the user is still required before release.
