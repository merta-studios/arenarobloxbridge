[CmdletBinding()]
param(
    [ValidateSet('beta','stable')]
    [string]$Channel = 'beta',
    [string]$BuildVersion = '',
    # Nur fuer den privaten Selbst-Update-Test (Harness developer/tests/Invoke-SelfUpdateSmoke.ps1).
    # Erzeugt einen Testbau mit aktivierter Test-Manifestfunktion und schreibt NIE nach release\.
    [switch]$TestFixtureBuild,
    [string]$OutputDirectory = '',
    # Test-only: numeric FileVersion of a test-fixture EXE (e.g. 7.7.1.0) so the
    # self-update test can serve a genuinely newer artifact. Requires -TestFixtureBuild.
    [string]$TestFileVersion = '',
    # Schalter fuer Build-EXE.bat oder CI: ueberspringt die interaktive Bestaetigung bei -Channel stable
    [switch]$NonInteractive
)

$ErrorActionPreference = 'Stop'
$PSDefaultParameterValues['*:ErrorAction'] = 'Stop'

function Write-Step([string]$Text) {
    Write-Host ("[ArenaBridge build] " + $Text) -ForegroundColor Cyan
}

function Write-Utf8NoBom([string]$Path, [string]$Text) {
    [IO.File]::WriteAllText($Path,$Text,[Text.UTF8Encoding]::new($false))
}

function Invoke-BridgeCompiler {
    param(
        [string]$InputPath,
        [string]$OutputPath,
        [string]$IconPath,
        [string]$NumericVersion,
        [bool]$NoConsole,
        [string]$WindowTitle
    )
    $arguments = @{
        inputFile = $InputPath
        outputFile = $OutputPath
        noConsole = $NoConsole
        STA = $true
        x64 = $true
        title = $WindowTitle
        description = 'Arena Roblox Bridge - lokaler Test-Build'
        company = 'Arena Roblox Bridge'
        product = 'Arena Roblox Bridge'
        version = $NumericVersion
        iconFile = $IconPath
    }
    Invoke-ps2exe @arguments | Out-Null
    if (-not (Test-Path -LiteralPath $OutputPath -PathType Leaf)) {
        throw ("ps2exe returned without creating the requested executable: " + $OutputPath)
    }
    $file = Get-Item -LiteralPath $OutputPath
    if ($file.Length -le 0 -or $file.Length -gt [long]209715200) { # 200 MiB
        throw ("Unexpected EXE size: " + [string]$file.Length + ' bytes. Staging output is invalid.')
    }
}

function Test-StagedExecutable {
    param(
        [string]$ExecutablePath,
        [string]$ReportPath
    )
    if (Test-Path -LiteralPath $ReportPath) { Remove-Item -LiteralPath $ReportPath -Force }
    $previousSmokeFlag = $env:ARENABRIDGE_BUILD_SMOKE
    $previousSmokePath = $env:ARENABRIDGE_BUILD_SMOKE_PATH
    $process = $null
    try {
        $env:ARENABRIDGE_BUILD_SMOKE = '1'
        $env:ARENABRIDGE_BUILD_SMOKE_PATH = $ReportPath
        Write-Step 'Starting the staged EXE in isolated build-smoke mode (no Studio, network, settings, or updater changes)...'
        $process = Start-Process -FilePath $ExecutablePath -PassThru -WindowStyle Hidden
        if (-not $process.WaitForExit(30000)) {
            try { $process.Kill() } catch {}
            throw 'The staged EXE did not finish its 30-second build smoke test; the output was not published.'
        }
        $process.Refresh()
        if ([int]$process.ExitCode -ne 0) {
            $detail = ''
            if (Test-Path -LiteralPath $ReportPath -PathType Leaf) {
                try { $detail = [string](Get-Content -LiteralPath $ReportPath -Raw -Encoding UTF8 | ConvertFrom-Json).error } catch {}
            }
            throw ("The staged EXE smoke test failed with exit code " + [string]$process.ExitCode + $(if ($detail) { ': ' + $detail } else { '.' }))
        }
        if (-not (Test-Path -LiteralPath $ReportPath -PathType Leaf)) {
            throw 'The staged EXE exited without a smoke-test report. The executable was not published.'
        }
        $report = Get-Content -LiteralPath $ReportPath -Raw -Encoding UTF8 | ConvertFrom-Json -ErrorAction Stop
        if ([string]$report.status -cne 'passed') {
            throw ("The staged EXE did not report a passing smoke test: " + [string]$report.error)
        }
        if ($report.appFolderResolved -ne $true) {
            throw 'The staged EXE smoke test did not resolve the executable application folder; no output was published.'
        }
        if ([int]$report.titleImageWidth -lt 100 -or [int]$report.titleImageHeight -lt 50) {
            throw 'The staged EXE smoke test did not decode the embedded title image.'
        }
        if ([int]$report.programLogoWidth -lt 32 -or [int]$report.programLogoHeight -lt 32) {
            throw 'The staged EXE smoke test did not decode the embedded neueslogo.png branding.'
        }
        if ([int]$report.backgroundImageWidth -lt 640 -or [int]$report.backgroundImageHeight -lt 360) {
            throw 'The staged EXE smoke test did not decode the embedded liquidglasbackground.png window background.'
        }
        Write-Step ("Compiled EXE launched successfully: PowerShell " + [string]$report.powershell + ', WPF/STA OK, title image ' + [string]$report.titleImageWidth + 'x' + [string]$report.titleImageHeight + ', app logo ' + [string]$report.programLogoWidth + 'x' + [string]$report.programLogoHeight + ', background ' + [string]$report.backgroundImageWidth + 'x' + [string]$report.backgroundImageHeight + '.')
    } finally {
        if ($null -ne $process) { try { $process.Dispose() } catch {} }
        if ($null -eq $previousSmokeFlag) { Remove-Item Env:\ARENABRIDGE_BUILD_SMOKE -ErrorAction SilentlyContinue }
        else { $env:ARENABRIDGE_BUILD_SMOKE = $previousSmokeFlag }
        if ($null -eq $previousSmokePath) { Remove-Item Env:\ARENABRIDGE_BUILD_SMOKE_PATH -ErrorAction SilentlyContinue }
        else { $env:ARENABRIDGE_BUILD_SMOKE_PATH = $previousSmokePath }
        if (Test-Path -LiteralPath $ReportPath) { Remove-Item -LiteralPath $ReportPath -Force -ErrorAction SilentlyContinue }
    }
}

function Publish-LocalBuild {
    param(
        [string]$StagingPath,
        [string]$TargetPath
    )
    $directory = Split-Path -Parent $TargetPath
    $baseName = [IO.Path]::GetFileNameWithoutExtension($TargetPath)
    $backupPath = ''
    try {
        if (Test-Path -LiteralPath $TargetPath -PathType Leaf) {
            $backupPath = Join-Path $directory ($baseName + '.previous-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff') + '.exe')
            [IO.File]::Replace($StagingPath,$TargetPath,$backupPath,$true)
            Write-Step ("Previous local build preserved at " + $backupPath)
        } else {
            [IO.File]::Move($StagingPath,$TargetPath)
        }
    } catch {
        if ($backupPath -and (Test-Path -LiteralPath $backupPath) -and -not (Test-Path -LiteralPath $TargetPath)) {
            [IO.File]::Move($backupPath,$TargetPath)
        }
        throw ("Could not safely publish the local build output. The previous file is preserved when present. " + $_.Exception.Message)
    }
}

function Test-WindowsIconFile([string]$Path) {
    if ([string]::IsNullOrWhiteSpace($Path) -or [IO.Path]::GetExtension($Path) -ine '.ico') {
        throw 'The EXE icon must be a Windows .ico file.'
    }
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw ("The selected EXE icon does not exist: " + $Path)
    }
    $bytes = [IO.File]::ReadAllBytes($Path)
    if ($bytes.Length -lt 22 -or $bytes.Length -gt 33554432) {
        throw ("The selected .ico has an invalid size: " + [string]$bytes.Length + ' bytes.')
    }
    $reserved = [BitConverter]::ToUInt16($bytes,0)
    $imageType = [BitConverter]::ToUInt16($bytes,2)
    $entryCount = [BitConverter]::ToUInt16($bytes,4)
    if ($reserved -ne 0 -or $imageType -ne 1 -or $entryCount -lt 1 -or $entryCount -gt 256) {
        throw 'The selected file is not a valid Windows ICO resource (expected an ICO header and 1-256 image entries).'
    }
    $directoryEnd = 6 + (16 * [int]$entryCount)
    if ($directoryEnd -gt $bytes.Length) { throw 'The selected ICO directory is truncated.' }
    for ($index = 0; $index -lt $entryCount; $index++) {
        $entryOffset = 6 + (16 * $index)
        $imageLength = [long][BitConverter]::ToUInt32($bytes,$entryOffset + 8)
        $imageOffset = [long][BitConverter]::ToUInt32($bytes,$entryOffset + 12)
        if ($imageLength -le 0 -or $imageOffset -lt $directoryEnd -or
            ($imageOffset + $imageLength) -gt $bytes.Length) {
            throw ("ICO image entry " + [string]$index + ' points outside the file or has no image data.')
        }
    }
    return $true
}

function Write-DiagnosticLauncher([string]$Path) {
    $text = @'
@echo off
setlocal
title Arena Roblox Bridge - Diagnostic start
set "APP=%~dp0ArenaBridge-Diagnose.exe"
if not exist "%APP%" (
  echo Diagnostic EXE is missing: "%APP%"
  echo Re-run Build-EXE.bat from the next-update folder.
  pause
  exit /b 2
)
echo.
echo ARENA ROBLOX BRIDGE - DIAGNOSTIC START
echo Close any other ArenaBridge window first. This mode keeps a console visible.
echo Normal beta app: "%~dp0ArenaBridge.exe"
echo.
set "ARENABRIDGE_DIAGNOSTIC_MODE=1"
"%APP%"
set "RESULT=%ERRORLEVEL%"
set "ARENABRIDGE_DIAGNOSTIC_MODE="
echo.
echo Diagnostic EXE exit code: %RESULT%
echo Start check: "%LOCALAPPDATA%\START-CHECK.txt"
echo Startup log: "%LOCALAPPDATA%\ArenaRobloxBridge\bin\startup-diagnose.txt"
echo Start-entry log: "%LOCALAPPDATA%\ArenaRobloxBridge-start-entry.txt"
echo Keep this window open and copy the console output if the app still fails.
echo.
pause
exit /b %RESULT%
'@
    $text = $text -replace "`n", "`r`n"
    [IO.File]::WriteAllText($Path,$text,[Text.Encoding]::ASCII)
}

if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
    throw 'The EXE build must run on Windows. This script does not build an EXE in the Arena sandbox.'
}
if (-not [Environment]::Is64BitOperatingSystem) {
    throw 'The Bridge beta is x64-only. Run the builder on 64-bit Windows.'
}

$builderRoot = [IO.Path]::GetFullPath((Split-Path -Parent $MyInvocation.MyCommand.Path))
$repoRoot = [IO.Path]::GetFullPath((Split-Path -Parent $builderRoot))
$appRoot = Join-Path $repoRoot 'app'
$assetsDirectory = Join-Path $appRoot 'assets'
$sourcePath = Join-Path $appRoot 'ArenaBridge.ps1'
$versionPath = Join-Path $appRoot 'version.json'
$parseGatePath = Join-Path $builderRoot 'parse-gate.ps1'
$iconPath = Join-Path $assetsDirectory 'ArenaBridge.ico'
$titleArtworkPath = Join-Path $assetsDirectory 'arena-bridge-title.jpg'
$programLogoPath = Join-Path $assetsDirectory 'neueslogo.png'
# Version 7.7.1: vom Nutzer bereitgestelltes Fensterhintergrund-Bild.
$backgroundImagePath = Join-Path $assetsDirectory 'liquidglasbackground.png'
$updaterPath = Join-Path $repoRoot 'update-system\updater\Update-Bridge.ps1'
$releaseDirectory = Join-Path $repoRoot 'release'
$buildOutputDirectory = $releaseDirectory
if ($TestFixtureBuild) {
    if ([string]::IsNullOrWhiteSpace($OutputDirectory)) { throw '-TestFixtureBuild requires -OutputDirectory outside the repository (for example a folder under %TEMP%).' }
    $buildOutputDirectory = [IO.Path]::GetFullPath($OutputDirectory)
    $repoPrefix = $repoRoot.TrimEnd('\') + '\'
    if ($buildOutputDirectory.TrimEnd('\') -ieq $releaseDirectory.TrimEnd('\') -or $buildOutputDirectory.StartsWith($repoPrefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw 'A test-fixture build must never write inside the repository (release\ is the publication folder).'
    }
    if ($Channel -ne 'beta') { throw 'A test-fixture build is only allowed for channel beta.' }
} elseif (-not [string]::IsNullOrWhiteSpace($OutputDirectory)) {
    throw '-OutputDirectory is only accepted together with -TestFixtureBuild. Normal builds always write to release\.'
}
if (-not [string]::IsNullOrWhiteSpace($TestFileVersion)) {
    if (-not $TestFixtureBuild) { throw '-TestFileVersion is only accepted together with -TestFixtureBuild.' }
    if ($TestFileVersion -cnotmatch '^\d+\.\d+\.\d+\.\d+$') { throw '-TestFileVersion must be a four-part numeric version such as 7.7.1.0.' }
}
$exePath = Join-Path $buildOutputDirectory 'ArenaBridge.exe'
$diagnosticExePath = Join-Path $buildOutputDirectory 'ArenaBridge-Diagnose.exe'
$diagnosticBatPath = Join-Path $buildOutputDirectory 'Start-Diagnostic.bat'

foreach ($requiredPath in @($sourcePath,$versionPath,$parseGatePath,$iconPath,$titleArtworkPath,$programLogoPath,$backgroundImagePath,$updaterPath)) {
    if (-not (Test-Path -LiteralPath $requiredPath -PathType Leaf)) {
        throw ("Required build input is missing: " + $requiredPath)
    }
}
[void](Test-WindowsIconFile -Path $iconPath)
$programLogoHeader = [IO.File]::ReadAllBytes($programLogoPath)
if ($programLogoHeader.Length -lt 1000 -or $programLogoHeader.Length -gt 10485760 -or
    $programLogoHeader[0] -ne 137 -or $programLogoHeader[1] -ne 80 -or
    $programLogoHeader[2] -ne 78 -or $programLogoHeader[3] -ne 71 -or
    $programLogoHeader[4] -ne 13 -or $programLogoHeader[5] -ne 10 -or
    $programLogoHeader[6] -ne 26 -or $programLogoHeader[7] -ne 10) {
    throw 'app\assets\neueslogo.png is missing, too small/large, or is not a valid PNG file.'
}
# Das Hintergrundbild ist Pflicht-Branding: ohne es bleibt das Fenster leer.
$backgroundHeader = [IO.File]::ReadAllBytes($backgroundImagePath)
if ($backgroundHeader.Length -lt 10000 -or $backgroundHeader.Length -gt 20971520 -or
    $backgroundHeader[0] -ne 137 -or $backgroundHeader[1] -ne 80 -or
    $backgroundHeader[2] -ne 78 -or $backgroundHeader[3] -ne 71 -or
    $backgroundHeader[4] -ne 13 -or $backgroundHeader[5] -ne 10 -or
    $backgroundHeader[6] -ne 26 -or $backgroundHeader[7] -ne 10) {
    throw 'app\assets\liquidglasbackground.png is missing, too small/large, or is not a valid PNG file.'
}
# PNG-IHDR: Breite/Hoehe stehen big-endian an Offset 16..23.
$backgroundPixelWidth = ([int]$backgroundHeader[16] * 16777216) + ([int]$backgroundHeader[17] * 65536) + ([int]$backgroundHeader[18] * 256) + [int]$backgroundHeader[19]
$backgroundPixelHeight = ([int]$backgroundHeader[20] * 16777216) + ([int]$backgroundHeader[21] * 65536) + ([int]$backgroundHeader[22] * 256) + [int]$backgroundHeader[23]
if ($backgroundPixelWidth -lt 920 -or $backgroundPixelHeight -lt 620) {
    throw ('app\assets\liquidglasbackground.png is smaller than the 920x620 window and would look blurry: ' + [string]$backgroundPixelWidth + 'x' + [string]$backgroundPixelHeight + '.')
}
Write-Step ("Using the EXE icon generated from the supplied logo: " + $iconPath)
Write-Step ("Embedding the same app logo into the Bridge window: " + $programLogoPath)
Write-Step ("Embedding the window background image: " + $backgroundImagePath + " (" + [string]$backgroundPixelWidth + "x" + [string]$backgroundPixelHeight + ")")

$versionInfo = Get-Content -LiteralPath $versionPath -Raw -Encoding UTF8 | ConvertFrom-Json -ErrorAction Stop
$sourceVersion = [string]$versionInfo.version
if ($sourceVersion -notmatch '^\d+\.\d+\.\d+$') {
    throw ("version.json must contain a three-part release version; found: " + $sourceVersion)
}
if ([string]::IsNullOrWhiteSpace($BuildVersion)) {
    if ($Channel -eq 'beta') { $BuildVersion = $sourceVersion + '-beta.1' }
    else { $BuildVersion = $sourceVersion }
}
if ($BuildVersion -notmatch '^\d+\.\d+\.\d+(?:-[0-9A-Za-z]+(?:[.-][0-9A-Za-z]+)*)?$') {
    throw ("Invalid build version: " + $BuildVersion)
}
$buildCoreVersion = ($BuildVersion -split '-',2)[0]
if ($buildCoreVersion -ne $sourceVersion) {
    throw ("BuildVersion core must match version.json source version " + $sourceVersion + '; found: ' + $buildCoreVersion)
}
if ($Channel -eq 'stable' -and $BuildVersion.Contains('-')) {
    throw 'Stable builds cannot use a prerelease version. Use beta first, then a stable version.'
}
if ($Channel -eq 'stable' -and -not $NonInteractive) {
    Write-Warning 'A stable build writes to the same single release\ folder. Do not run this during private testing.'
    $confirmation = Read-Host 'Type RELEASE STABLE to overwrite release\ArenaBridge.exe'
    if ($confirmation -cne 'RELEASE STABLE') { throw 'Stable build cancelled.' }
}

$windowsPowerShell = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
if (-not (Test-Path -LiteralPath $windowsPowerShell -PathType Leaf)) {
    throw 'Windows PowerShell 5.1 was not found. Run this build from a Windows installation with PowerShell.'
}
Write-Step 'Running the real PowerShell parser before compilation (app and updater)...'
& $windowsPowerShell -NoLogo -NoProfile -ExecutionPolicy Bypass -File $parseGatePath -Path $sourcePath
if ($LASTEXITCODE -ne 0) { throw 'PowerShell parse gate failed; no EXE was produced.' }
& $windowsPowerShell -NoLogo -NoProfile -ExecutionPolicy Bypass -File $parseGatePath -Path $updaterPath
if ($LASTEXITCODE -ne 0) { throw 'PowerShell parse gate failed for Update-Bridge.ps1; no EXE was produced.' }

# Updater: strict checks before it is embedded. PS 5.1 reads BOM-less UTF-8 as ANSI, so the
# embedded updater must be pure ASCII. Its version is taken from its own source.
$updaterBytes = [IO.File]::ReadAllBytes($updaterPath)
if ($updaterBytes.Length -lt 2000 -or $updaterBytes.Length -gt 1048576) {
    throw ('The updater has an unexpected size: ' + [string]$updaterBytes.Length + ' bytes.')
}
foreach ($byte in $updaterBytes) {
    if ($byte -gt 127) { throw 'Update-Bridge.ps1 must be pure ASCII (PS 5.1 reads BOM-less UTF-8 as ANSI). Build aborted.' }
}
$updaterSourceText = [Text.Encoding]::ASCII.GetString($updaterBytes)
$updaterVersionMatch = [regex]::Match($updaterSourceText, '(?m)^\$script:UpdaterVersion = ''(\d+\.\d+\.\d+)''\r?$')
if (-not $updaterVersionMatch.Success) { throw 'Update-Bridge.ps1 does not declare $script:UpdaterVersion as a three-part version.' }
$updaterVersion = $updaterVersionMatch.Groups[1].Value
$updaterSha256 = ([BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash($updaterBytes))).Replace('-', '').ToLowerInvariant()
$updaterBase64 = [Convert]::ToBase64String($updaterBytes)
Write-Step ('Updater ' + $updaterVersion + ' embedded (SHA-256 ' + $updaterSha256 + ').')

$ps2exeModule = Get-Module -ListAvailable -Name ps2exe | Select-Object -First 1
if ($null -eq $ps2exeModule) {
    Write-Step 'Installing ps2exe for the current Windows user (no administrator install)...'
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Install-Module -Name ps2exe -Scope CurrentUser -Force -AllowClobber -Repository PSGallery
}
Import-Module ps2exe -ErrorAction Stop
$compiler = Get-Command Invoke-ps2exe -ErrorAction SilentlyContinue
if ($null -eq $compiler) { throw 'The ps2exe module loaded but Invoke-ps2exe was not found.' }
foreach ($requiredParameter in @('inputFile','outputFile','noConsole','STA','x64','title','description','company','product','version','iconFile')) {
    if (-not $compiler.Parameters.ContainsKey($requiredParameter)) {
        throw ("The installed ps2exe module is missing the required parameter '" + $requiredParameter + "'. Update ps2exe and run Build-EXE.bat again.")
    }
}

if (-not (Test-Path -LiteralPath $buildOutputDirectory -PathType Container)) {
    New-Item -ItemType Directory -Path $buildOutputDirectory -Force | Out-Null
}
$tempBuildDirectory = Join-Path $env:TEMP ('ArenaRobloxBridge-build-' + [Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $tempBuildDirectory -Force | Out-Null
$preparedSourcePath = Join-Path $tempBuildDirectory 'ArenaBridge.compile.ps1'
$stagingExePath = Join-Path $buildOutputDirectory 'ArenaBridge.building.exe'
$stagingDiagnosticExePath = Join-Path $buildOutputDirectory 'ArenaBridge-Diagnose.building.exe'
$smokeReportPath = Join-Path $tempBuildDirectory 'smoke-report.json'

try {
    $sourceText = [IO.File]::ReadAllText($sourcePath,[Text.Encoding]::UTF8)
    $sourceMarker = '$script:TitleArtworkBase64 = ''__ARENA_TITLE_ARTWORK_BASE64__'''
    if (-not $sourceText.Contains($sourceMarker)) {
        throw 'The unique title-artwork injection marker is missing from ArenaBridge.ps1.'
    }
    if ($sourceText.IndexOf($sourceMarker,[StringComparison]::Ordinal) -ne $sourceText.LastIndexOf($sourceMarker,[StringComparison]::Ordinal)) {
        throw 'The title-artwork injection marker must appear exactly once.'
    }
    $logoMarker = '$script:ProgramLogoBase64 = ''__ARENA_PROGRAM_LOGO_BASE64__'''
    if (-not $sourceText.Contains($logoMarker)) {
        throw 'The unique program-logo injection marker is missing from ArenaBridge.ps1.'
    }
    if ($sourceText.IndexOf($logoMarker,[StringComparison]::Ordinal) -ne $sourceText.LastIndexOf($logoMarker,[StringComparison]::Ordinal)) {
        throw 'The program-logo injection marker must appear exactly once.'
    }
    $backgroundMarker = '$script:BackgroundImageBase64 = ''__ARENA_BACKGROUND_IMAGE_BASE64__'''
    if (-not $sourceText.Contains($backgroundMarker)) {
        throw 'The unique background-image injection marker is missing from ArenaBridge.ps1.'
    }
    if ($sourceText.IndexOf($backgroundMarker,[StringComparison]::Ordinal) -ne $sourceText.LastIndexOf($backgroundMarker,[StringComparison]::Ordinal)) {
        throw 'The background-image injection marker must appear exactly once.'
    }
    $titleArtworkBytes = [IO.File]::ReadAllBytes($titleArtworkPath)
    if ($titleArtworkBytes.Length -le 1000 -or $titleArtworkBytes.Length -gt 10485760) {
        throw ("The title artwork has an unexpected size: " + [string]$titleArtworkBytes.Length + ' bytes.')
    }
    $updateMarkers = @(
        @{ Marker = '$script:UpdateChannel = ''__ARENA_UPDATE_CHANNEL__'''; Value = ('$script:UpdateChannel = ''' + $Channel + '''') },
        @{ Marker = '$script:EmbeddedUpdaterBase64 = ''__ARENA_UPDATER_BASE64__'''; Value = ('$script:EmbeddedUpdaterBase64 = ''' + $updaterBase64 + '''') },
        @{ Marker = '$script:EmbeddedUpdaterSha256 = ''__ARENA_UPDATER_SHA256__'''; Value = ('$script:EmbeddedUpdaterSha256 = ''' + $updaterSha256 + '''') },
        @{ Marker = '$script:TestFixtureBuild = ''__ARENA_TEST_FIXTURE_BUILD__'''; Value = $(if ($TestFixtureBuild) { '$script:TestFixtureBuild = ''1''' } else { '$script:TestFixtureBuild = ''0''' }) }
    )
    foreach ($entry in $updateMarkers) {
        if (([regex]::Matches($sourceText, [regex]::Escape($entry.Marker))).Count -ne 1) {
            throw ('The update-system marker must appear exactly once in ArenaBridge.ps1: ' + $entry.Marker)
        }
    }
    $titleArtworkBase64 = [Convert]::ToBase64String($titleArtworkBytes)
    $programLogoBytes = [IO.File]::ReadAllBytes($programLogoPath)
    $programLogoBase64 = [Convert]::ToBase64String($programLogoBytes)
    $backgroundBytes = [IO.File]::ReadAllBytes($backgroundImagePath)
    if ($backgroundBytes.Length -le 10000 -or $backgroundBytes.Length -gt 20971520) {
        throw ("The window background image has an unexpected size: " + [string]$backgroundBytes.Length + ' bytes.')
    }
    $backgroundBase64 = [Convert]::ToBase64String($backgroundBytes)
    $sourceReplacement = '$script:TitleArtworkBase64 = ''' + $titleArtworkBase64 + ''''
    $preparedSource = $sourceText.Replace($sourceMarker,$sourceReplacement)
    $logoReplacement = '$script:ProgramLogoBase64 = ''' + $programLogoBase64 + ''''
    $preparedSource = $preparedSource.Replace($logoMarker,$logoReplacement)
    $backgroundReplacement = '$script:BackgroundImageBase64 = ''' + $backgroundBase64 + ''''
    $preparedSource = $preparedSource.Replace($backgroundMarker,$backgroundReplacement)
    foreach ($leftoverBackground in @('__ARENA_BACKGROUND_IMAGE_BASE64__')) {
        if ($preparedSource.Contains($leftoverBackground)) { throw ('Background placeholder was not replaced: ' + $leftoverBackground) }
    }
    foreach ($entry in $updateMarkers) { $preparedSource = $preparedSource.Replace($entry.Marker, $entry.Value) }
    foreach ($leftover in @('__ARENA_UPDATE_CHANNEL__','__ARENA_UPDATER_BASE64__','__ARENA_UPDATER_SHA256__','__ARENA_TEST_FIXTURE_BUILD__')) {
        if ($preparedSource.Contains($leftover)) { throw ('Update-system placeholder was not replaced: ' + $leftover) }
    }
    [IO.File]::WriteAllText($preparedSourcePath,$preparedSource,[Text.UTF8Encoding]::new($true))
    Write-Step ("Prepared self-contained source with title artwork (" + [string]$titleArtworkBytes.Length + " bytes), the program logo (" + [string]$programLogoBytes.Length + " bytes) and the window background (" + [string]$backgroundBytes.Length + " bytes). No external runtime image is required.")
    Write-Step 'Re-running the real Windows PowerShell parser against the exact embedded compile copy...'
    & $windowsPowerShell -NoLogo -NoProfile -ExecutionPolicy Bypass -File $parseGatePath -Path $preparedSourcePath
    if ($LASTEXITCODE -ne 0) { throw 'PowerShell parse gate failed for the embedded compile copy; no EXE was produced.' }

    foreach ($oldStagingPath in @($stagingExePath,$stagingDiagnosticExePath)) {
        if (Test-Path -LiteralPath $oldStagingPath) { Remove-Item -LiteralPath $oldStagingPath -Force }
    }
    $numericVersion = $sourceVersion + '.0'
    if (-not [string]::IsNullOrWhiteSpace($TestFileVersion)) { $numericVersion = $TestFileVersion }
    Write-Step ("Compiling " + $BuildVersion + ' for channel ' + $Channel + ' (hidden-console release EXE)...')
    Invoke-BridgeCompiler -InputPath $preparedSourcePath -OutputPath $stagingExePath -IconPath $iconPath -NumericVersion $numericVersion -NoConsole $true -WindowTitle 'Arena Roblox Bridge'
    Write-Step 'Compiling a separate console-enabled diagnostic EXE for local troubleshooting...'
    Invoke-BridgeCompiler -InputPath $preparedSourcePath -OutputPath $stagingDiagnosticExePath -IconPath $iconPath -NumericVersion $numericVersion -NoConsole $false -WindowTitle 'Arena Roblox Bridge - Diagnose'

    Test-StagedExecutable -ExecutablePath $stagingExePath -ReportPath $smokeReportPath

    # Publish the troubleshooting twin first; the normal ArenaBridge.exe is
    # replaced last so a failure cannot leave a half-built release executable.
    Publish-LocalBuild -StagingPath $stagingDiagnosticExePath -TargetPath $diagnosticExePath
    Publish-LocalBuild -StagingPath $stagingExePath -TargetPath $exePath
    Write-DiagnosticLauncher -Path $diagnosticBatPath

    $file = Get-Item -LiteralPath $exePath
    $diagnosticFile = Get-Item -LiteralPath $diagnosticExePath
    $sha256 = (Get-FileHash -LiteralPath $exePath -Algorithm SHA256).Hash.ToLowerInvariant()
    $diagnosticSha256 = (Get-FileHash -LiteralPath $diagnosticExePath -Algorithm SHA256).Hash.ToLowerInvariant()
    $iconSha256 = (Get-FileHash -LiteralPath $iconPath -Algorithm SHA256).Hash.ToLowerInvariant()
    $artworkSha256 = (Get-FileHash -LiteralPath $titleArtworkPath -Algorithm SHA256).Hash.ToLowerInvariant()
    $programLogoSha256 = (Get-FileHash -LiteralPath $programLogoPath -Algorithm SHA256).Hash.ToLowerInvariant()
    $backgroundSha256 = (Get-FileHash -LiteralPath $backgroundImagePath -Algorithm SHA256).Hash.ToLowerInvariant()
    $metadata = [ordered]@{
        schemaVersion = 1
        channel = $Channel
        version = $BuildVersion
        sourceVersion = $sourceVersion
        fileName = 'ArenaBridge.exe'
        sizeBytes = [long]$file.Length
        sha256 = $sha256
        diagnosticFileName = 'ArenaBridge-Diagnose.exe'
        diagnosticSizeBytes = [long]$diagnosticFile.Length
        diagnosticSha256 = $diagnosticSha256
        iconFileName = [IO.Path]::GetFileName($iconPath)
        iconSha256 = $iconSha256
        titleArtworkFileName = 'arena-bridge-title.jpg'
        titleArtworkSha256 = $artworkSha256
        programLogoFileName = 'neueslogo.png'
        programLogoSha256 = $programLogoSha256
        backgroundImageFileName = 'liquidglasbackground.png'
        backgroundImageSha256 = $backgroundSha256
        backgroundImageSizeBytes = [long]$backgroundBytes.Length
        updateChannel = $Channel
        updaterFileName = 'Update-Bridge.ps1 (embedded in ArenaBridge.exe, not published separately)'
        updaterVersion = $updaterVersion
        updaterSha256 = $updaterSha256
        updaterSizeBytes = [long]$updaterBytes.Length
        testFixtureBuild = [bool]$TestFixtureBuild
        builtAtUtc = [DateTime]::UtcNow.ToString('o')
        published = $false
        note = 'Local private-test build only. Never publish during review/testing. After explicit release approval, use the exact tested ArenaBridge.exe at next-update/release/ArenaBridge.exe; diagnostic files and metadata are local-only. testFixtureBuild=true means a non-publishable test EXE that must never be placed in release\\.'
    }
    $metadataPath = Join-Path $buildOutputDirectory 'release-metadata.json'
    Write-Utf8NoBom $metadataPath ($metadata | ConvertTo-Json -Depth 6)
    Write-Utf8NoBom (Join-Path $buildOutputDirectory 'ArenaBridge.exe.sha256') ($sha256 + '  ArenaBridge.exe' + [Environment]::NewLine)
    Write-Utf8NoBom (Join-Path $buildOutputDirectory 'ArenaBridge-Diagnose.exe.sha256') ($diagnosticSha256 + '  ArenaBridge-Diagnose.exe' + [Environment]::NewLine)

    Write-Step 'LOCAL TEST BUILD COMPLETED. No GitHub upload/release or update-channel manifest was changed.'
    Write-Host ''
    Write-Host 'NOW RUN THIS FILE ON YOUR PC TO TEST THE APP:' -ForegroundColor Green
    Write-Host ('  ' + $exePath) -ForegroundColor White
    Write-Host 'If the normal EXE shows nothing, close other ArenaBridge windows and run:' -ForegroundColor Yellow
    Write-Host ('  ' + $diagnosticBatPath) -ForegroundColor White
    Write-Host ('Local-only metadata: ' + $metadataPath)
    Write-Host 'No users were updated. Only after explicit approval may the exact tested ArenaBridge.exe be uploaded to next-update/release/ArenaBridge.exe; do not upload diagnostic files or metadata.'
} finally {
    foreach ($stagingPath in @($stagingExePath,$stagingDiagnosticExePath)) {
        if ($stagingPath -and (Test-Path -LiteralPath $stagingPath)) {
            Remove-Item -LiteralPath $stagingPath -Force -ErrorAction SilentlyContinue
        }
    }
    if (Test-Path -LiteralPath $tempBuildDirectory) {
        Remove-Item -LiteralPath $tempBuildDirectory -Recurse -Force -ErrorAction SilentlyContinue
    }
}
