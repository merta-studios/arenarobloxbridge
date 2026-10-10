[CmdletBinding()]
param(
    [ValidateSet('beta','stable')]
    [string]$Channel = 'beta',
    [string]$BuildVersion = ''
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
        description = 'Arena Roblox Bridge - lokale Beta-Testfassung'
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
        if ([int]$report.titleImageWidth -lt 100 -or [int]$report.titleImageHeight -lt 50) {
            throw 'The staged EXE smoke test did not decode the embedded title image.'
        }
        Write-Step ("Compiled EXE launched successfully: PowerShell " + [string]$report.powershell + ', WPF/STA OK, title image ' + [string]$report.titleImageWidth + 'x' + [string]$report.titleImageHeight + '.')
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

$repoRoot = [IO.Path]::GetFullPath((Split-Path -Parent $MyInvocation.MyCommand.Path))
$sourcePath = Join-Path $repoRoot 'ArenaBridge.ps1'
$versionPath = Join-Path $repoRoot 'version.json'
$parseGatePath = Join-Path $repoRoot 'parse-gate.ps1'
$iconPath = Join-Path (Join-Path $repoRoot 'assets') 'ArenaBridge.ico'
$titleArtworkPath = Join-Path (Join-Path $repoRoot 'assets') 'arena-bridge-title.jpg'
$outputDirectory = Join-Path (Join-Path $repoRoot 'user-builds') $Channel
$exePath = Join-Path $outputDirectory 'ArenaBridge.exe'
$diagnosticExePath = Join-Path $outputDirectory 'ArenaBridge-Diagnose.exe'
$diagnosticBatPath = Join-Path $outputDirectory 'Start-Diagnostic.bat'

foreach ($requiredPath in @($sourcePath,$versionPath,$parseGatePath,$iconPath,$titleArtworkPath)) {
    if (-not (Test-Path -LiteralPath $requiredPath -PathType Leaf)) {
        throw ("Required build input is missing: " + $requiredPath)
    }
}

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
if ($Channel -eq 'stable') {
    Write-Warning 'Stable builds are for a later release. They are not published automatically.'
    $confirmation = Read-Host 'Type RELEASE STABLE to build into user-builds/stable'
    if ($confirmation -cne 'RELEASE STABLE') { throw 'Stable build cancelled.' }
}

$windowsPowerShell = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
if (-not (Test-Path -LiteralPath $windowsPowerShell -PathType Leaf)) {
    throw 'Windows PowerShell 5.1 was not found. Run this build from a Windows installation with PowerShell.'
}
Write-Step 'Running the real PowerShell parser before compilation...'
& $windowsPowerShell -NoLogo -NoProfile -ExecutionPolicy Bypass -File $parseGatePath -Path $sourcePath
if ($LASTEXITCODE -ne 0) { throw 'PowerShell parse gate failed; no EXE was produced.' }

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

if (-not (Test-Path -LiteralPath $outputDirectory -PathType Container)) {
    New-Item -ItemType Directory -Path $outputDirectory -Force | Out-Null
}
$tempBuildDirectory = Join-Path $env:TEMP ('ArenaRobloxBridge-build-' + [Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $tempBuildDirectory -Force | Out-Null
$preparedSourcePath = Join-Path $tempBuildDirectory 'ArenaBridge.compile.ps1'
$stagingExePath = Join-Path $outputDirectory 'ArenaBridge.building.exe'
$stagingDiagnosticExePath = Join-Path $outputDirectory 'ArenaBridge-Diagnose.building.exe'
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
    $titleArtworkBytes = [IO.File]::ReadAllBytes($titleArtworkPath)
    if ($titleArtworkBytes.Length -le 1000 -or $titleArtworkBytes.Length -gt 10485760) {
        throw ("The title artwork has an unexpected size: " + [string]$titleArtworkBytes.Length + ' bytes.')
    }
    $titleArtworkBase64 = [Convert]::ToBase64String($titleArtworkBytes)
    $sourceReplacement = '$script:TitleArtworkBase64 = ''' + $titleArtworkBase64 + ''''
    $preparedSource = $sourceText.Replace($sourceMarker,$sourceReplacement)
    [IO.File]::WriteAllText($preparedSourcePath,$preparedSource,[Text.UTF8Encoding]::new($true))
    Write-Step ("Prepared self-contained source with title artwork (" + [string]$titleArtworkBytes.Length + ' bytes) and no extra runtime image file.')
    Write-Step 'Re-running the real Windows PowerShell parser against the exact embedded compile copy...'
    & $windowsPowerShell -NoLogo -NoProfile -ExecutionPolicy Bypass -File $parseGatePath -Path $preparedSourcePath
    if ($LASTEXITCODE -ne 0) { throw 'PowerShell parse gate failed for the embedded compile copy; no EXE was produced.' }

    foreach ($oldStagingPath in @($stagingExePath,$stagingDiagnosticExePath)) {
        if (Test-Path -LiteralPath $oldStagingPath) { Remove-Item -LiteralPath $oldStagingPath -Force }
    }
    $numericVersion = $sourceVersion + '.0'
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
        iconFileName = 'ArenaBridge.ico'
        iconSha256 = $iconSha256
        titleArtworkFileName = 'arena-bridge-title.jpg'
        titleArtworkSha256 = $artworkSha256
        builtAtUtc = [DateTime]::UtcNow.ToString('o')
        published = $false
        note = 'Local user build only. Publish only ArenaBridge.exe after the user test and explicit release approval. Diagnostic EXE/BAT are local-only.'
    }
    $metadataPath = Join-Path $outputDirectory 'release-metadata.json'
    Write-Utf8NoBom $metadataPath ($metadata | ConvertTo-Json -Depth 6)
    Write-Utf8NoBom (Join-Path $outputDirectory 'ArenaBridge.exe.sha256') ($sha256 + '  ArenaBridge.exe' + [Environment]::NewLine)
    Write-Utf8NoBom (Join-Path $outputDirectory 'ArenaBridge-Diagnose.exe.sha256') ($diagnosticSha256 + '  ArenaBridge-Diagnose.exe' + [Environment]::NewLine)

    Write-Step 'BETA BUILD COMPLETED. No GitHub release, upload, channel manifest, or stable build was changed.'
    Write-Host ''
    Write-Host 'NOW RUN THIS FILE ON YOUR PC TO TEST THE APP:' -ForegroundColor Green
    Write-Host ('  ' + $exePath) -ForegroundColor White
    Write-Host 'If the normal EXE shows nothing, close other ArenaBridge windows and run:' -ForegroundColor Yellow
    Write-Host ('  ' + $diagnosticBatPath) -ForegroundColor White
    Write-Host ('Local-only metadata: ' + $metadataPath)
    Write-Host 'For all-user distribution, publish only ArenaBridge.exe as a GitHub Release asset after testing; do not commit the EXE or diagnostic files.'
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
