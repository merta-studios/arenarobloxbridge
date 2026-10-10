#!/usr/bin/env python3
"""Offline acceptance checks for the isolated 7.6.4 update preparation.

This test is structural and network-free. It never invokes Build-EXE.ps1,
Windows PowerShell, the updater, or a Roblox endpoint; the user builds EXEs
locally. Tree-sitter only parses the prepared PowerShell files as text. This
protects next-update/ from being wired into the root updater before the planned
beta-first handoff.
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
VERSION = "7.6.4"
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
    check(metadata.get("version") == VERSION, "the prepared copy and release metadata agree on 7.6.4")
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

    # Branded startup image and EXE icon are valid inputs; the main splash XAML
    # contains a named image target and the embedded image is wired in code.
    title_art = APP_ROOT / "assets" / "arena-bridge-title.jpg"
    icon_path = APP_ROOT / "assets" / "ArenaBridge.ico"
    title_bytes = title_art.read_bytes()
    icon_bytes = icon_path.read_bytes()
    check(title_bytes.startswith(b"\xff\xd8\xff") and title_bytes.endswith(b"\xff\xd9")
          and len(title_bytes) > 1000,
          "optimized hero image is a non-empty JPEG asset")
    icon_header = struct.unpack("<HHH", icon_bytes[:6]) if len(icon_bytes) >= 6 else (1, 0, 0)
    icon_ok = icon_header[:2] == (0, 1) and icon_header[2] >= 1
    if icon_ok:
        icon_ok = all(
            struct.unpack("<I", icon_bytes[6 + 16 * i + 8:6 + 16 * i + 12])[0] > 0
            and struct.unpack("<I", icon_bytes[6 + 16 * i + 12:6 + 16 * i + 16])[0] +
                struct.unpack("<I", icon_bytes[6 + 16 * i + 8:6 + 16 * i + 12])[0] <= len(icon_bytes)
            for i in range(icon_header[2])
        )
    check(icon_ok, "multi-size Windows ICO resource has valid entries")
    xaml_start = source.index("$xaml = @'") + len("$xaml = @'")
    xaml_end = source.index("\n'@", xaml_start)
    main_xaml = source[xaml_start:xaml_end]
    try:
        root_element = ET.fromstring(main_xaml)
        xaml_valid = root_element.tag.endswith("Window")
    except ET.ParseError as error:
        xaml_valid = False
        print(f"[FAIL] main WPF XAML is valid XML: {error}")
    check(xaml_valid, "main splash WPF markup is parseable XML")
    namespaced_name = "{http://schemas.microsoft.com/winfx/2006/xaml}Name"
    splash_image = next((node for node in root_element.iter() if node.attrib.get(namespaced_name) == "SplashHeroImage"), None) if xaml_valid else None
    check(splash_image is not None and "Set-SplashTitleArtwork" in source
          and "BitmapCacheOption]::OnLoad" in source,
          "startup splash loads the embedded hero image safely from memory")
    check("SINGLE_INSTANCE_DUPLICATE" in source and "already open" not in source
          and "WScript.Shell" in source and "Popup($duplicateMessage" in source,
          "launching a second instance creates a START-CHECK and a visible explanation")
    smoke_region = region(source, "if ($env:ARENABRIDGE_BUILD_SMOKE -eq '1') {", "# 7.2.9 PROOF_OF_LIFE")
    for marker in ("PresentationFramework", "ApartmentState]::STA", "FromBase64String",
                   "BitmapImage]::new()", "ARENABRIDGE_BUILD_SMOKE_PATH", "exit $smokeExitCode"):
        check(marker in smoke_region, f"compiled EXE smoke test validates host/WPF/image: {marker}")
    check("Invoke-WebRequest" not in smoke_region and "Start-BridgeRuntime" not in smoke_region,
          "build smoke test has no network, Studio or Bridge-runtime side effects")

    # The user-facing root is intentionally sparse: one BAT, two short guides,
    # and named folders for app, builder, the future update system and developer tools.
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
    for marker in ("builder\\Build-EXE.ps1", "-Channel beta", "BUILD ERFOLGREICH",
                   "user-builds\\beta\\ArenaBridge.exe", "Start-Diagnostic.bat", "START-HIER.txt",
                   "app\\assets\\ArenaBridge.custom.ico"):
        check(marker in bat, f"single beta BAT gives an exact next action/path: {marker}")
    for marker in ("The EXE build must run on Windows", "64-bit Windows",
                   "Join-Path $appRoot 'ArenaBridge.ps1'", "Join-Path $appRoot 'version.json'",
                   "Join-Path $builderRoot 'parse-gate.ps1'",
                   "Join-Path (Join-Path $repoRoot 'user-builds') $Channel",
                   "Join-Path $assetsDirectory 'ArenaBridge.ico'", "ArenaBridge.custom.ico",
                   "Test-WindowsIconFile -Path $iconPath", "CustomIconPath",
                   "arena-bridge-title.jpg", "Invoke-ps2exe @arguments", "iconFile = $IconPath",
                   "iconSelection = $iconSelection", "STA = $true", "x64 = $true",
                   "noConsole = $NoConsole", "The unique title-artwork injection marker is missing",
                   "TitleArtworkBase64 = ''__ARENA_TITLE_ARTWORK_BASE64__''",
                   "[IO.File]::WriteAllText($preparedSourcePath,$preparedSource,[Text.UTF8Encoding]::new($true))",
                   "Test-StagedExecutable -ExecutablePath $stagingExePath", "appFolderResolved -ne $true",
                   "ARENABRIDGE_BUILD_SMOKE", "30-second build smoke test",
                   "ArenaBridge-Diagnose.building.exe", "Start-Diagnostic.bat",
                   "release-metadata.json", "No GitHub release, upload, channel manifest",
                   "only ArenaBridge.exe after the user test and explicit release approval"):
        check(marker in build, f"user-owned EXE build safety step is present: {marker}")
    check("Invoke-ps2exe @arguments" in build and "-InputPath $preparedSourcePath" in build
          and "ArenaBridge.ps1" in build,
          "build compiles only an artwork-injected temporary copy of the isolated app source")

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

    check(not list((ROOT / "user-builds").rglob("*.exe"))
          and not list((ROOT / "release-inbox").rglob("*.exe")),
          "no user or release EXE was built or left in next-update")
    ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    check("/user-builds/*/*.exe" in ignore and "/user-builds/*/Start-Diagnostic.bat" in ignore
          and "/release-inbox/*/*" in ignore and "/app/assets/ArenaBridge.custom.ico" in ignore,
          "local EXEs, diagnostic BAT, custom icon, metadata and release inbox artifacts stay out of Git")
    for channel in ("beta", "stable"):
        folder = ROOT / "user-builds" / channel
        check(folder.is_dir() and (folder / ".gitkeep").is_file(),
              f"user-builds/{channel}/ exists for local builds")
    check((ROOT / "START-HIER.txt").is_file(), "downloaded next-update folder has a prominent German start guide")
    check((ROOT / "update-system" / "updater" / "README.md").is_file(),
          "future updater folder explains that it is not integrated")

    # Beta first, stable later; neither channel is enabled or published yet.
    channels_root = ROOT / "update-system" / "channels"
    for channel in ("beta", "stable"):
        manifest = json.loads((channels_root / f"{channel}.json").read_text(encoding="utf-8"))
        check(manifest.get("channel") == channel and manifest.get("enabled") is False,
              f"{channel} manifest is an explicitly disabled placeholder")
        artifact = manifest.get("artifact", {})
        check(artifact.get("fileName") == "ArenaBridge.exe" and not artifact.get("url")
              and not artifact.get("sha256") and artifact.get("sizeBytes") == 0,
              f"{channel} manifest contains no unpublished artifact coordinates")
    schema = json.loads((channels_root / "manifest.schema.json").read_text(encoding="utf-8"))
    check(schema.get("properties", {}).get("channel", {}).get("enum") == ["beta", "stable"]
          and schema.get("properties", {}).get("artifact", {}).get("properties", {}).get("fileName", {}).get("const") == "ArenaBridge.exe",
          "channel schema constrains channel and artifact identity")

    # Future updater is a standalone handoff artifact. It validates host,
    # version, size and SHA-256, waits rather than killing the process, stages,
    # atomically replaces, preserves a backup, and attempts rollback.
    updater_path = ROOT / "update-system" / "updater" / "Update-Bridge.ps1"
    updater = updater_path.read_text(encoding="utf-8-sig")
    for powershell_path in (build_path, parse_gate_path, updater_path):
        errors = powershell_parse_errors(powershell_path)
        check(not errors,
              f"Tree-sitter parses {powershell_path.relative_to(ROOT)} without syntax/error nodes: {errors[:3]}")
    for marker in ("Test-GitHubHost", "github.com", "githubusercontent.com",
                   "Test-ApprovedGitHubUri", "$Uri.IsDefaultPort", "$script:MaxManifestBytes = 1048576",
                   "$script:MaxArtifactBytes", "no embedded credentials", "Compare-UpdateVersion",
                   "Refusing downgrade", "Wait-ForTargetProcessToExit", "the updater will not terminate it",
                   "$request.AllowAutoRedirect = $false", "$redirectCount -ge $MaxRedirects",
                   "redirect target is outside the approved HTTPS host set", "$declaredLength -gt $MaxBytes",
                   "$receivedBytes -gt $MaxBytes", "Streamed response exceeded", "-TimeoutSeconds 180",
                   "ConvertFrom-Json -ErrorAction Stop", "schemaVersion is missing or unsupported",
                   "channel is invalid", "version is invalid", "refusing to update without trustworthy version history",
                   "[IO.File]::Open($DestinationPath,[IO.FileMode]::CreateNew", "Get-ApprovedGitHubDownload -Uri $artifactUri",
                   "ArenaBridge.exe.new", "Get-FileHash -LiteralPath $stagingPath -Algorithm SHA256",
                   "does not match the channel manifest", "[IO.File]::Replace($stagingPath,$targetPath,$backupPath,$true)",
                   "rollback was attempted", "Start-Process -FilePath $targetPath"):
        check(marker in updater, f"standalone updater safely stages/replaces a stopped EXE: {marker}")
    check("Invoke-WebRequest" not in updater,
          "updater streams and validates redirects instead of following unchecked web requests")
    check("Stop-Process" not in updater and "taskkill" not in updater,
          "updater never terminates a running Bridge process")
    check("Update-Bridge.ps1" not in source and "channels/beta.json" not in source
          and "channels/stable.json" not in source,
          "future updater/manifests are not integrated into the isolated Bridge executable")

    # Verify the uncomplicated user path, explicit EXE destination, personal
    # icon instructions, and that developer material is kept in its own folder.
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    start_guide = (ROOT / "START-HIER.txt").read_text(encoding="utf-8")
    runner_path = ROOT / "developer" / "tests" / "run_offline_tests.py"
    runner = runner_path.read_text(encoding="utf-8") if runner_path.is_file() else ""
    check('TEST_DIR.glob("test_*.py")' in runner and "subprocess.run(" in runner
          and "[sys.executable, \"-u\", str(script)]" in runner
          and "result.returncode" in runner,
          "offline regression runner executes each test and propagates failures")
    for marker in ("**`Build-EXE.bat`**", r"user-builds\beta\ArenaBridge.exe",
                   "Start-Diagnostic.bat", r"%LOCALAPPDATA%\START-CHECK.txt",
                   "Eigenes Logo für die EXE", "ArenaBridge.custom.ico",
                   "merta-studios/arenarobloxbridge", "GitHub-Release",
                   "alte Struktur im Hauptordner", "enabled: false",
                   r"python developer\tests\run_offline_tests.py"):
        check(marker in readme, f"README makes the build/folder/icon workflow explicit: {marker}")
    check(all((ROOT / folder).is_dir() for folder in ("app", "builder", "developer", "update-system")),
          "app, builder, developer and update-system are separate, named folders")
    for marker in ("Build-EXE.bat", r"user-builds\beta\ArenaBridge.exe",
                   "Start-Diagnostic.bat", "ArenaBridge.custom.ico", "enabled: false",
                   "Die alte Update-Struktur im Hauptordner bleibt unangetastet"):
        check(marker in start_guide, f"START-HIER gives the user the exact next step: {marker}")

    if FAILURES:
        print(f"\nFAILED: {len(FAILURES)} preparation check(s).")
        return 1
    print("\nOK: isolated user-build, beta-first manifests, safe future updater, tutorial/privacy, and no-EXE checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
