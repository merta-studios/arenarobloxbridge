#!/usr/bin/env python3
"""Offline acceptance checks for the isolated 7.6.3 update preparation.

This test is structural and network-free. It never invokes Build-EXE.ps1,
Windows PowerShell, the updater, or a Roblox endpoint; the user builds EXEs
locally. Tree-sitter only parses the prepared PowerShell files as text. This
protects next-update/ from being wired into the root updater before the planned
beta-first handoff.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "ArenaBridge.ps1"
VERSION = "7.6.3"
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
    metadata = json.loads((ROOT / "version.json").read_text(encoding="utf-8"))
    source_bytes = SOURCE.read_bytes()
    source = source_bytes.decode("utf-8-sig")
    check(metadata.get("version") == VERSION, "the prepared copy and release metadata agree on 7.6.3")
    check(source_bytes.startswith(b"\xef\xbb\xbf") and len(source_bytes) > 2_000_000,
          "next-update/ArenaBridge.ps1 is a complete UTF-8-BOM PowerShell bridge source")
    check("function Get-PluginSource {" in source and "function Start-BridgeRuntime {" in source,
          "the copied source contains the embedded Studio plugin and Bridge entrypoint")

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

    # User builds only: BAT -> PowerShell builder -> parse gate -> exact copy;
    # no build is run in this test or by the preparation script.
    bat_path = ROOT / "Build-EXE.bat"
    build_path = ROOT / "Build-EXE.ps1"
    check(bat_path.is_file() and build_path.is_file(), "BAT launcher and PowerShell build script are prepared")
    bat = bat_path.read_text(encoding="utf-8-sig")
    build = build_path.read_text(encoding="utf-8-sig")
    for marker in ("Build-EXE.ps1", "-Channel", "beta", "stable"):
        check(marker in bat, f"BAT offers the user's selected build channel: {marker}")
    for marker in ("The EXE build must run on Windows", "does not build an EXE in the Arena sandbox",
                   "Join-Path $repoRoot 'ArenaBridge.ps1'", "Join-Path $repoRoot 'parse-gate.ps1'",
                   "Join-Path (Join-Path $repoRoot 'user-builds') $Channel",
                   "-File $parseGatePath -Path $sourcePath", "Invoke-ps2exe",
                   "$buildCoreVersion = ($BuildVersion -split '-',2)[0]",
                   "BuildVersion core must match version.json source version",
                   "$ps2exeArguments = @{", "noConsole = $true", "STA = $true", "x64 = $true",
                   "Invoke-ps2exe @ps2exeArguments", "version = $numericVersion",
                   "[long]209715200", "Staging output removed",
                   "Type RELEASE STABLE", "[IO.File]::Replace($stagingExePath,$exePath,$backupPath,$true)",
                   "Previous build is preserved", "no release or channel manifest was changed"):
        check(marker in build, f"user-owned EXE build safety step is present: {marker}")
    check("Build-EXE.ps1" in bat and "ArenaBridge.ps1" in build,
          "build pipeline reads only the source beside the new script under next-update")
    check(not list(ROOT.rglob("*.exe")), "no EXE was built or left in next-update")
    ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    check("/user-builds/*/*.exe" in ignore and "/release-inbox/*/*" in ignore,
          "local EXEs, metadata and release inbox artifacts stay out of Git")
    for channel in ("beta", "stable"):
        folder = ROOT / "user-builds" / channel
        check(folder.is_dir() and (folder / ".gitkeep").is_file(),
              f"user-builds/{channel}/ exists for local builds")

    # Beta first, stable later; neither channel is enabled or published yet.
    for channel in ("beta", "stable"):
        manifest = json.loads((ROOT / "channels" / f"{channel}.json").read_text(encoding="utf-8"))
        check(manifest.get("channel") == channel and manifest.get("enabled") is False,
              f"{channel} manifest is an explicitly disabled placeholder")
        artifact = manifest.get("artifact", {})
        check(artifact.get("fileName") == "ArenaBridge.exe" and not artifact.get("url")
              and not artifact.get("sha256") and artifact.get("sizeBytes") == 0,
              f"{channel} manifest contains no unpublished artifact coordinates")
    schema = json.loads((ROOT / "channels" / "manifest.schema.json").read_text(encoding="utf-8"))
    check(schema.get("properties", {}).get("channel", {}).get("enum") == ["beta", "stable"]
          and schema.get("properties", {}).get("artifact", {}).get("properties", {}).get("fileName", {}).get("const") == "ArenaBridge.exe",
          "channel schema constrains channel and artifact identity")

    # Future updater is a standalone handoff artifact. It validates host,
    # version, size and SHA-256, waits rather than killing the process, stages,
    # atomically replaces, preserves a backup, and attempts rollback.
    updater_path = ROOT / "updater" / "Update-Bridge.ps1"
    updater = updater_path.read_text(encoding="utf-8-sig")
    for powershell_path in (build_path, ROOT / "parse-gate.ps1", updater_path):
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
          "future updater/manifests are not integrated into the root-copied Bridge executable")

    # Keep tutorial text exact and ensure the updater handoff remains described
    # as not yet integrated; no release publication is implied.
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    runner_path = ROOT / "run_offline_tests.py"
    runner = runner_path.read_text(encoding="utf-8") if runner_path.is_file() else ""
    check('ROOT.glob("test_*.py")' in runner and "subprocess.run(" in runner
          and "[sys.executable, \"-u\", str(script)]" in runner
          and "result.returncode" in runner,
          "offline regression runner executes each script and propagates failures")
    for marker in ("Root-Bridge, der bestehende Updater", "baut EXEs selbst",
                   "beide\nabsichtlich `enabled: false`", "Der Nutzer baut selbst eine Beta-EXE",
                   "Stable bleibt\n   deaktiviert.", "noch nicht in `ArenaBridge.ps1` eingebunden",
                   "Versionskern muss mit `version.json` übereinstimmen",
                   "prüft auch jedes Redirect-Ziel erneut", "streamt EXE-Downloads mit fester",
                   "ungültigem\n  lokalem Update-Status", "python run_offline_tests.py",
                   "`unittest`-TestCase-Klassen"):
        check(marker in readme, f"handoff README preserves rollout/test instructions: {marker}")

    if FAILURES:
        print(f"\nFAILED: {len(FAILURES)} preparation check(s).")
        return 1
    print("\nOK: isolated user-build, beta-first manifests, safe future updater, tutorial/privacy, and no-EXE checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
