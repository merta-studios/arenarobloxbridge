#!/usr/bin/env python3
"""Offline acceptance checks for the isolated 7.6.5 test/release workflow.

This is structural and network-free: it never runs the EXE builder, Windows
PowerShell, the updater, or Roblox. It verifies the private-test gate, the one
release/ output folder, the supplied logo in both branding paths, the channel state
(disabled placeholder or a released manifest with complete coordinates) and the
standalone updater's safe-publication prerequisites.
"""
from __future__ import annotations

import json
import re
import struct
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
APP_ROOT = ROOT / "app"
SOURCE = APP_ROOT / "ArenaBridge.ps1"
VERSION = "7.8.0"
FAILURES: list[str] = []


def check(condition: bool, message: str) -> None:
    print(("[OK]   " if condition else "[FAIL] ") + message)
    if not condition:
        FAILURES.append(message)


def region(text: str, start: str, end: str) -> str:
    begin = text.index(start)
    return text[begin:text.index(end, begin)]


def powershell_parse_errors(path: Path) -> list[tuple[int, str]]:
    """Collect Tree-sitter errors; this does not execute a PowerShell runtime."""
    from tree_sitter import Language, Parser
    import tree_sitter_powershell as tsp

    raw = path.read_bytes()
    root = Parser(Language(tsp.language())).parse(raw).root_node
    pending = [root]
    errors: list[tuple[int, str]] = []
    while pending:
        node = pending.pop()
        if node.type == "ERROR" or node.is_missing:
            line = raw.count(b"\n", 0, node.start_byte) + 1
            fragment = raw[node.start_byte:node.end_byte].decode("utf-8", "replace")[:120]
            errors.append((line, fragment))
        pending.extend(node.children)
    return errors


def main() -> int:
    metadata = json.loads((APP_ROOT / "version.json").read_text(encoding="utf-8"))
    source_bytes = SOURCE.read_bytes()
    source = source_bytes.decode("utf-8-sig")
    check(metadata.get("version") == VERSION, "the prepared copy and release metadata agree on 7.8.0")
    check(source_bytes.startswith(b"\xef\xbb\xbf") and len(source_bytes) > 2_000_000,
          "next-update/app/ArenaBridge.ps1 is a complete UTF-8-BOM PowerShell bridge source")
    check("function Get-PluginSource {" in source and "function Start-BridgeRuntime {" in source,
          "the copied source contains the embedded Studio plugin and Bridge entrypoint")
    guide_source = region(source, "function Get-BridgeGuides {", "function Get-DocsResponse")
    # PowerShell 5.1 accepts U+2019 as a quote delimiter, even inside ASCII-quoted prose.
    check(chr(0x2019) not in guide_source and "Place''s" in guide_source and "user''s" in guide_source,
          "Bridge guide strings escape apostrophes safely for the Windows PowerShell 5.1 parser")

    latest = str(metadata.get("notes", [""])[0])
    for marker in ("Nutzerwünsche", "Place-Konventionen", "Blender ist eine passende Empfehlung, keine Pflicht",
                   "Fortschritt als nicht anwendbar", "API-Pfade", "IP-Einrichtung",
                   "Root-Updater bleibt unangetastet", "EXEs baut der Nutzer selbst"):
        check(marker in latest, f"current release note includes the confirmed scope: {marker}")

    # User-visible Open Cloud activity history: action/function + safe outcome,
    # without paths, resource keys, response bodies or unredacted failures.
    summary_fn = region(source, "function Get-OpenCloudHistorySummary($Value)",
                        "# Vollständige, deutsch formulierte Texte für alle Werkzeuge")
    for marker in ("Nutzdaten enthalten; Werte aus Datenschutzgründen nicht im Verlauf gespeichert",
                   "$safeScalars = @('state','status')", "@('count','total','returned','operationCount','entryCount','dataStoreCount','assetCount')",
                   "resource IDs/names, entry keys, prices, payloads or returned values",
                   "Feldnamen und -werte nicht im Verlauf gespeichert", "if ($summary.Length -gt 220)"):
        check(marker in summary_fn, f"Open Cloud history summary limits data to safe fields: {marker}")
    activity_fn = region(source, "function Get-ArenaActivityText", "function Get-ArenaActivityKind")
    cloud_start = activity_fn.index("if ($tool -eq 'open_cloud') {")
    cloud_end = activity_fn.index("if ($tool -eq 'search') {", cloud_start)
    cloud_activity = activity_fn[cloud_start:cloud_end]
    for marker in ("@('action')", "@('operation')", "@('operationSummary')",
                   "@('httpMethod','method')", "@('status','httpStatus')", "@('resultSummary')",
                   "Open Cloud call", "Ergebnis:", "Get-OpenCloudHistorySummary"):
        check(marker in cloud_activity, f"history names action/function and a minimized result: {marker}")
    for forbidden in ("apiPath", "requestPath", "resourceId", "datastoreName",
                      "$result.error", "$result.robloxResponse", "result.error"):
        check(forbidden not in cloud_activity,
              f"Open Cloud activity text does not expose raw/path/resource detail {forbidden}")
    error_helper = region(source, "function Invoke-OpenCloudCatalogTool {",
                          "function Get-OpenCloudAssetSpec {")
    check("Protect-OpenCloudResponse" in error_helper and "resultSummary = ('HTTP-Fehlerantwort" in error_helper,
          "raw Cloud error details are protected and the history gets a redacted result summary")

    # Exact tutorial copy; IP configuration/examples are absent only from the
    # tutorial, while existing localhost network settings remain in the source.
    settings_xaml = region(source, "$settingsXaml = @'", "    $settingsReader = [System.Xml.XmlNodeReader]")
    step4 = region(settings_xaml, 'x:Name="CloudStep4"', 'x:Name="CloudStep5"')
    exact_step4 = "Füge die Berechtigungen hinzu, die du willst! Hier siehst du eine ausführliche Liste, was jede Berechtigung kann:"
    check(exact_step4 in step4, "tutorial step 4 uses the exact user-approved sentence")
    tutorial = region(settings_xaml, 'x:Name="CloudStep1"', 'x:Name="CloudStep7"')
    check(not re.search(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", tutorial),
          "tutorial has no concrete IPv4 examples")
    check(not re.search(r"\bIP(?:-Adresse|-Adresse|[- ]?Konfiguration|[- ]?Einstellung(?:en)?)\b", tutorial, re.I),
          "tutorial contains no IP-configuration instruction")
    check('$script:LocalBaseUrl = "http://127.0.0.1:$script:Port"' in source
          and '$listener.Prefixes.Add("http://127.0.0.1:$Port/")' in source,
          "existing local Bridge connection settings remain present and unchanged by tutorial copy edits")

    # The supplied PNG must be the exact app-window logo and the source for a
    # valid multi-size Windows ICO; the same PNG is embedded into the EXE.
    title_art = APP_ROOT / "assets" / "arena-bridge-title.jpg"
    icon_path = APP_ROOT / "assets" / "ArenaBridge.ico"
    logo_path = APP_ROOT / "assets" / "neueslogo.png"
    title_bytes = title_art.read_bytes()
    icon_bytes = icon_path.read_bytes()
    logo_bytes = logo_path.read_bytes()
    check(title_bytes.startswith(b"\xff\xd8\xff") and title_bytes.endswith(b"\xff\xd9")
          and len(title_bytes) > 1000,
          "optimized hero image is a non-empty JPEG asset")
    check(logo_bytes.startswith(b"\x89PNG\r\n\x1a\n")
          and struct.unpack(">II", logo_bytes[16:24]) == (1024, 1024),
          "neueslogo.png is the supplied valid square 1024px PNG")
    icon_header = struct.unpack("<HHH", icon_bytes[:6]) if len(icon_bytes) >= 6 else (1, 0, 0)
    icon_ok = icon_header[:2] == (0, 1) and icon_header[2] >= 5
    if icon_ok:
        icon_ok = all(
            struct.unpack("<I", icon_bytes[6 + 16 * i + 8:6 + 16 * i + 12])[0] > 0
            and struct.unpack("<I", icon_bytes[6 + 16 * i + 12:6 + 16 * i + 16])[0] +
                struct.unpack("<I", icon_bytes[6 + 16 * i + 8:6 + 16 * i + 12])[0] <= len(icon_bytes)
            for i in range(icon_header[2])
        )
    check(icon_ok, "multi-size Windows ICO resource has valid entries derived from the PNG")
    xaml_start = source.index("$xaml = @'") + len("$xaml = @'")
    xaml_end = source.index("\n'@", xaml_start)
    main_xaml = source[xaml_start:xaml_end]
    try:
        root_element = ET.fromstring(main_xaml)
        xaml_valid = root_element.tag.endswith("Window")
    except ET.ParseError as error:
        xaml_valid = False
        print(f"[FAIL] main WPF XAML is valid XML: {error}")
    check(xaml_valid, "main WPF markup is parseable XML")
    namespaced_name = "{http://schemas.microsoft.com/winfx/2006/xaml}Name"
    main_logo = next((node for node in root_element.iter()
                      if node.attrib.get(namespaced_name) == "ProgramLogoImage"), None) if xaml_valid else None
    splash_image = next((node for node in root_element.iter()
                         if node.attrib.get(namespaced_name) == "SplashHeroImage"), None) if xaml_valid else None
    check(main_logo is not None and "Set-ProgramBrandLogo -ImageControl $ProgramLogoImage" in source,
          "the supplied logo replaces the fake main-window title mark and is loaded at startup")
    check("NoticeLogoImage" in source and "Set-ProgramBrandLogo -ImageControl $noticeLogoImage" in source,
          "the update-notice window uses the same program logo")
    check(splash_image is not None and "Set-SplashTitleArtwork" in source
          and "BitmapCacheOption]::OnLoad" in source,
          "startup splash still loads its separate embedded hero image")
    check("$script:ProgramLogoBase64 = '__ARENA_PROGRAM_LOGO_BASE64__'" in source
          and "__ARENA_PROGRAM_LOGO_BASE64__" in source,
          "app source has a unique builder-injected program-logo marker")
    check("SINGLE_INSTANCE_DUPLICATE" in source and "already open" not in source
          and "WScript.Shell" in source and "Popup($duplicateMessage" in source,
          "launching a second instance creates a START-CHECK and a visible explanation")
    smoke_region = region(source, "if ($env:ARENABRIDGE_BUILD_SMOKE -eq '1') {", "# 7.2.9 PROOF_OF_LIFE")
    for marker in ("PresentationFramework", "ApartmentState]::STA", "FromBase64String",
                   "BitmapImage]::new()", "ARENABRIDGE_BUILD_SMOKE_PATH", "programLogoWidth",
                   "__ARENA_PROGRAM_LOGO_BASE64__", "exit $smokeExitCode"):
        check(marker in smoke_region, f"compiled EXE smoke test validates host/WPF/logo: {marker}")
    check("Invoke-WebRequest" not in smoke_region and "Start-BridgeRuntime" not in smoke_region,
          "build smoke test has no network, Studio or Bridge-runtime side effects")

    # The user-facing root is intentionally sparse: one BAT, two guides and
    # named app/builder/developer/update-system/release folders.
    bat_path = ROOT / "Build-EXE.bat"
    build_path = ROOT / "builder" / "Build-EXE.ps1"
    parse_gate_path = ROOT / "builder" / "parse-gate.ps1"
    check(bat_path.is_file() and build_path.is_file() and parse_gate_path.is_file(),
          "the root BAT points to an internal builder and parser in builder/")
    root_bats = list(ROOT.glob("*.bat"))
    check(root_bats == [bat_path], "Build-EXE.bat is the only BAT in the downloaded next-update root")
    check(not (ROOT / "ArenaBridge.ps1").exists() and not (ROOT / "version.json").exists()
          and not list(ROOT.glob("test_*.py")),
          "source/version and regression tests are kept out of the user-facing root")
    generator_path = ROOT / "developer" / "ci" / "generate_opencloud_catalog.py"
    generator = generator_path.read_text(encoding="utf-8") if generator_path.is_file() else ""
    check("ROOT = Path(__file__).resolve().parents[2]" in generator
          and "APP_ROOT = ROOT / 'app'" in generator
          and "Usage: python developer/ci/generate_opencloud_catalog.py" in generator
          and "path = APP_ROOT/'ArenaBridge.ps1'" in generator,
          "moved Open Cloud catalog generator resolves its source and output under app/")
    ci_example_path = ROOT / "developer" / "ci" / "windows-parse.yml.example"
    ci_example = ci_example_path.read_text(encoding="utf-8") if ci_example_path.is_file() else ""
    check("next-update/builder/parse-gate.ps1" in ci_example
          and "next-update/app/ArenaBridge.ps1" in ci_example,
          "example Windows parser CI points at the reorganized builder and app source")
    bat_bytes = bat_path.read_bytes()
    check(b"\xef\xbb\xbf" not in bat_bytes[:3] and bat_bytes.count(b"\r\n") == bat_bytes.count(b"\n"),
          "double-click BAT is plain ASCII with Windows CRLF endings")
    bat = bat_path.read_text(encoding="ascii")
    build = build_path.read_text(encoding="utf-8-sig")
    for marker in ("builder\\Build-EXE.ps1", "-Channel stable", "BUILD ERFOLGREICH",
                   "release\\ArenaBridge.exe", "Start-Diagnostic.bat", "START-HIER.txt",
                   "app\\assets\\neueslogo.png", "kein Nutzer aktualisiert"):
        check(marker in bat, f"single test-build BAT gives an exact next action/path: {marker}")
    for marker in ("The EXE build must run on Windows", "64-bit Windows",
                   "Join-Path $appRoot 'ArenaBridge.ps1'", "Join-Path $appRoot 'version.json'",
                   "Join-Path $builderRoot 'parse-gate.ps1'", "Join-Path $repoRoot 'release'",
                   "Join-Path $assetsDirectory 'ArenaBridge.ico'", "Join-Path $assetsDirectory 'neueslogo.png'",
                   "Test-WindowsIconFile -Path $iconPath", "programLogoHeader", "arena-bridge-title.jpg",
                   "Invoke-ps2exe @arguments", "iconFile = $IconPath", "STA = $true", "x64 = $true",
                   "noConsole = $NoConsole", "unique title-artwork injection marker",
                   "__ARENA_TITLE_ARTWORK_BASE64__", "__ARENA_PROGRAM_LOGO_BASE64__",
                   "programLogoWidth -lt 32", "programLogoSha256", "ArenaBridge.exe.sha256",
                   "release-metadata.json", "No GitHub upload/release or update-channel manifest",
                   "next-update/release/ArenaBridge.exe", "explicit release approval"):
        check(marker in build, f"private EXE build safety/branding step is present: {marker}")
    check("Invoke-ps2exe @arguments" in build and "-InputPath $preparedSourcePath" in build
          and "ArenaBridge.ps1" in build and "ProgramLogoBase64" in build,
          "builder compiles a temporary source copy with both branded images embedded")

    # The null Path regression must be exercised by the same safe resolver used
    # by normal startup, not just by the old shallow host/WPF smoke check.
    app_folder_resolver = region(source, "function Resolve-BridgeAppFolder {", "# Isolated build smoke test")
    check("Split-Path -Parent -Path ([string]$candidate)" in app_folder_resolver
          and "IsNullOrWhiteSpace([string]$candidate)" in app_folder_resolver,
          "path resolver skips null/empty candidates before calling Split-Path")
    smoke_region = region(source, "if ($env:ARENABRIDGE_BUILD_SMOKE -eq '1') {", "# 7.2.9 PROOF_OF_LIFE")
    check("Resolve-BridgeAppFolder -ScriptPath $smokeScriptPath -ExecutablePath $smokeExePath" in smoke_region
          and "$expectedExeFolder" in smoke_region and "appFolderResolved = $false" in smoke_region
          and "$smokeReport.appFolderResolved = $true" in smoke_region,
          "compiled EXE smoke test confirms AppFolder resolves to the EXE directory")
    app_folder_block = region(source, "# PS1 runs use the script directory;", "$script:UpdateDetails = $null")
    check("Resolve-BridgeAppFolder" in app_folder_block
          and "Split-Path -Parent $script:ScriptPath" not in source,
          "normal startup shares the safe resolver and never Split-Paths a null ScriptPath")

    check(not (ROOT / "user-builds").exists() and not (ROOT / "release-inbox").exists(),
          "the obsolete two-tree user-builds/release-inbox layout is removed")
    release_dir = ROOT / "release"
    check(release_dir.is_dir() and (release_dir / "README.txt").is_file()
          and ((not (release_dir / "ArenaBridge.exe").exists()) or (release_dir / "ArenaBridge.exe").is_file())
          and not (release_dir / "ArenaBridge-Diagnose.exe").exists(),
          "one release/ folder exists, documents the workflow, and has no generated EXE in source")
    ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    ignore_rules = [line.strip() for line in ignore.splitlines()
                    if line.strip() and not line.lstrip().startswith("#")]
    check("/release/ArenaBridge-Diagnose.exe" in ignore_rules
          and "/release/Start-Diagnostic.bat" in ignore_rules
          and "/release/release-metadata.json" in ignore_rules
          and "/release/ArenaBridge.exe" not in ignore_rules,
          "local diagnostics are ignored but the explicitly approved normal EXE can be uploaded")
    check((ROOT / "START-HIER.txt").is_file(), "downloaded next-update folder has a prominent German start guide")
    check((ROOT / "update-system" / "updater" / "README.md").is_file(),
          "future updater folder documents its integration and bootstrap gates")

    # A private build/test cycle never touches a channel. A channel that a release session
    # has activated must instead publish exactly the tested artifact; every other channel
    # stays an empty placeholder. The deep gates live in test_v800_update_manifest.py.
    channels_root = ROOT / "update-system" / "channels"
    schema = json.loads((channels_root / "manifest.schema.json").read_text(encoding="utf-8"))
    import jsonschema  # type: ignore
    validator = jsonschema.Draft202012Validator(schema)
    for channel in ("beta", "stable"):
        manifest = json.loads((channels_root / f"{channel}.json").read_text(encoding="utf-8"))
        artifact = manifest.get("artifact", {})
        check(manifest.get("channel") == channel and manifest.get("schemaVersion") == 2
              and manifest.get("testFixture") is False,
              f"{channel} manifest names its channel, uses schema 2 and is no test fixture")
        if manifest.get("enabled"):
            check(channel == "stable", f"{channel} manifest: only stable may be activated")
            version = str(manifest.get("version", ""))
            check(artifact.get("fileName") == f"ArenaBridge-{version}.exe",
                  f"{channel} manifest: published artifact is the immutable ArenaBridge-<Version>.exe")
            sha = str(artifact.get("sha256", "") or "")
            check(re.fullmatch(r"[0-9a-fA-F]{64}", sha) is not None
                  and isinstance(artifact.get("sizeBytes"), int) and artifact.get("sizeBytes", 0) > 0
                  and str(artifact.get("url", "")).startswith(
                      "https://raw.githubusercontent.com/merta-studios/arenarobloxbridge/main/next-update/release/"),
                  f"{channel} manifest publishes complete https-only artifact coordinates")
            continue
        check(manifest.get("enabled") is False, f"{channel} manifest is an explicitly disabled placeholder")
        check(artifact.get("fileName") == "ArenaBridge.exe"
              and not artifact.get("url") and not artifact.get("sha256") and artifact.get("sizeBytes") == 0,
              f"{channel} manifest contains no unpublished artifact coordinates")
        check(str(manifest.get("version", "")) == "" and str(manifest.get("publishedAtUtc", "")) == "",
              f"{channel} manifest leaves version and timestamp empty while disabled")

    # Der Artefaktname wird nicht mehr per const erzwungen, sondern ueber den
    # aktivierten Zweig des Schemas (abgeleiteter, unveraenderlicher Name).
    # Das wird hier verhaltensbasiert gegen das echte Schema geprueft.
    version = "9.9.9"
    good = {
        "schemaVersion": 2, "channel": "stable", "enabled": True, "testFixture": False,
        "sequence": 2, "version": version, "publishedAtUtc": "2026-10-11T06:30:00Z",
        "minimumUpdaterVersion": "2.0.0",
        "artifact": {
            "fileName": f"ArenaBridge-{version}.exe",
            "url": "https://raw.githubusercontent.com/merta-studios/arenarobloxbridge/main/"
                   f"next-update/release/ArenaBridge-{version}.exe",
            "sha256": "0" * 64, "sizeBytes": 1234567,
        },
        "notes": ["Testnotiz"],
    }
    check(not list(validator.iter_errors(good)),
          "channel schema accepts an activated manifest with the derived immutable artifact name")
    for name, mutate in (
        ("the old shared file name ArenaBridge.exe", lambda d: d["artifact"].__setitem__("fileName", "ArenaBridge.exe")),
        ("missing artifact coordinates", lambda d: d["artifact"].pop("sha256")),
        ("an unversioned artifact url", lambda d: d["artifact"].__setitem__("url", "https://example.invalid/x.exe")),
        ("zero sequence", lambda d: d.__setitem__("sequence", 0)),
        ("a mandatory field (forced updates are not supported)", lambda d: d.__setitem__("mandatory", False)),
    ):
        mutant = json.loads(json.dumps(good))
        mutate(mutant)
        check(bool(list(validator.iter_errors(mutant))), f"channel schema rejects {name}")

    # Future updater is a standalone handoff artifact. It validates host,
    # version, size and SHA-256, waits rather than killing the process, stages,
    # atomically replaces, preserves a backup, and attempts rollback.
    updater_path = ROOT / "update-system" / "updater" / "Update-Bridge.ps1"
    updater = updater_path.read_text(encoding="utf-8-sig")
    for powershell_path in (build_path, parse_gate_path, updater_path):
        errors = powershell_parse_errors(powershell_path)
        check(not errors,
              f"Tree-sitter parses {powershell_path.relative_to(ROOT)} without syntax/error nodes: {errors[:3]}")
    for marker in ("Test-AllowedUri", "Get-ApprovedDownload", "Get-ChannelManifest", "Test-ChannelManifest",
                   "$script:MaxManifestBytes = 1048576", "$script:MaxArtifactBytes = 67108864",
                   "$script:MaxRedirects = 3", "Compare-UpdateVersion", "Get-UpdateDecision",
                   "downgrade-refused", "Wait-ForTargetToExit", "[IO.FileMode]::CreateNew",
                   "ArenaBridge.exe.new", "Get-Sha256Hex", "$request.AllowAutoRedirect = $false",
                   "[IO.File]::Replace($stagingPath, $TargetPath, $backupPath, $true)", "Restore-Previous",
                   "-UpdateStatus update-erfolgreich", "Test-WindowsX64Executable", "Enter-UpdateLock",
                   "Remove-OldFiles", "IsDefaultPort", "minimumUpdaterVersion", "update-state.json",
                   "update-status.json", "update-fehler", "kein-update", "0x8664",
                   "$script:UpdaterVersion = '3.0.0'", "objects.githubusercontent.com",
                   "minimumUpdaterVersion"):
        check(marker in updater, f"Updater 2.0.0 keeps its safety/staging contract: {marker}")
    check("Invoke-WebRequest" not in updater,
          "updater streams and validates redirects instead of following unchecked web requests")
    check("Stop-Process" not in updater and "taskkill" not in updater and ".Kill(" not in updater,
          "updater never terminates a running Bridge process")
    # 7.7.0: the updater is embedded only through the protected integration block.
    # The app never reads channel files directly and the legacy root updater is retired.
    integ = region(source, "# >>> ARENA-UPDATE-INTEGRATION >>>", "# <<< ARENA-UPDATE-INTEGRATION <<<")
    check("channels/beta.json" not in source and "channels/stable.json" not in source,
          "the app never reads channel manifests directly (only the updater does, from a fixed repository URL)")
    check(all(marker in integ for marker in ("__ARENA_UPDATE_CHANNEL__", "__ARENA_UPDATER_BASE64__",
                                             "__ARENA_UPDATER_SHA256__", "__ARENA_TEST_FIXTURE_BUILD__",
                                             "Invoke-ArenaUpdateGate", "Start-ArenaGateInstall")),
          "update integration block contains all builder placeholders and the check/install entry points")
    check("\n    Invoke-AutostartSelfUpdate" not in source and "$selfUpdated = Invoke-AutostartSelfUpdate" not in source
          and "STILLGELEGT (7.7.0)" in source and "Invoke-ArenaUpdateGate" in source,
          "the legacy root self-update call is removed from the startup path")
    check("ARENABRIDGE_SELFUPDATE_TEST_MANIFEST" in integ and "if ([string]$script:TestFixtureBuild -cne '1') { return '' }" in integ,
          "the test-manifest path is only reachable in a -TestFixtureBuild, never in a normal build")

    # Verify the exact one-folder build/test/freigabe workflow and the future-session gate.
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    start_guide = (ROOT / "START-HIER.txt").read_text(encoding="utf-8")
    handoff = (ROOT / "developer" / "docs" / "GANZ WICHTIG LESEN VOR JEDER BEARBEITUNG").read_text(encoding="utf-8")
    runner_path = ROOT / "developer" / "tests" / "run_offline_tests.py"
    runner = runner_path.read_text(encoding="utf-8") if runner_path.is_file() else ""
    check('TEST_DIR.glob("test_*.py")' in runner and "subprocess.run(" in runner
          and "[sys.executable, \"-u\", str(script)]" in runner
          and "result.returncode" in runner,
          "offline regression runner executes each test and propagates failures")
    for marker in ("**`Build-EXE.bat`**", r"next-update\release\ArenaBridge.exe",
                   "Start-Diagnostic.bat", "neueslogo.png", "release-inbox/", "user-builds/",
                   "neuen Chat", "neuen PR", "Release-Session", "Stable",
                   "deaktiviert", "Bootstrap", r"python developer\tests\run_offline_tests.py"):
        check(marker in readme, f"README makes the build/test/release workflow explicit: {marker}")
    check(all((ROOT / folder).is_dir() for folder in ("app", "builder", "developer", "update-system", "release")),
          "app, builder, developer, update-system and the single release folder exist")
    for marker in ("Build-EXE.bat", r"release\ArenaBridge.exe", "Start-Diagnostic.bat",
                   "neueslogo.png", "Channel-Manifeste bleiben aus",
                   "kopierbaren", "Update-Bridge.ps1 ist in die EXE eingebettet"):
        check(marker in start_guide, f"START-HIER gives the exact current user action: {marker}")
    for marker in ("AUSSCHLIESSLICH in next-update/", "KEIN next-update/release-inbox/",
                   "KEIN next-update/user-builds/", "Korrekturwunsch", "AUSSCHLIESSLICH mit",
                   "PROMPT-VORLAGE FUER DIE NAECHSTE SESSION", "Update-Bridge.ps1",
                   "Bootstrap/Migration", "SHA-256"):
        check(marker in handoff, f"critical handoff guide includes the new owner rule: {marker}")
    update_readme = (ROOT / "update-system" / "README.md").read_text(encoding="utf-8")
    update_readme_plain = re.sub(r"\s+", " ", re.sub(r"[*`]", "", update_readme))
    check("Update-Bridge.ps1" in update_readme
          and "Windows-Ergebnisse" in update_readme_plain
          and "Aussage des Nutzers" in update_readme_plain
          and "bekommen dieses System nicht automatisch" in update_readme_plain
          and "release/ArenaBridge.exe" in update_readme
          and "enabled: false" in update_readme_plain
          and re.search(r"Letzte veröffentlichte Version: (keine|\d+\.\d+\.\d+)", update_readme_plain) is not None
          and "raw.githubusercontent.com" in update_readme_plain,
          "update-system README states the honest release status: Windows runs taken from the "
          "user report, no automatic reach of installs without an updater, live version, raw cache hint")

    if FAILURES:
        print(f"\nFAILED: {len(FAILURES)} preparation check(s).")
        return 1
    print("\nOK: private test gate, one release folder, logo embedding, channel state and safe updater checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
