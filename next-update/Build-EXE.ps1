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

if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
    throw 'The EXE build must run on Windows. This script does not build an EXE in the Arena sandbox.'
}

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$sourcePath = Join-Path $repoRoot 'ArenaBridge.ps1'
$versionPath = Join-Path $repoRoot 'version.json'
$parseGatePath = Join-Path $repoRoot 'parse-gate.ps1'
$outputDirectory = Join-Path (Join-Path $repoRoot 'user-builds') $Channel
$exePath = Join-Path $outputDirectory 'ArenaBridge.exe'

foreach ($requiredPath in @($sourcePath,$versionPath,$parseGatePath)) {
    if (-not (Test-Path -LiteralPath $requiredPath -PathType Leaf)) {
        throw ("Required build input is missing: " + $requiredPath)
    }
}

$versionInfo = Get-Content -LiteralPath $versionPath -Raw -Encoding UTF8 | ConvertFrom-Json
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
    Install-Module -Name ps2exe -Scope CurrentUser -Force -AllowClobber
}
Import-Module ps2exe -ErrorAction Stop
if (-not (Get-Command Invoke-ps2exe -ErrorAction SilentlyContinue)) {
    throw 'The ps2exe module loaded but Invoke-ps2exe was not found.'
}

if (-not (Test-Path -LiteralPath $outputDirectory -PathType Container)) {
    New-Item -ItemType Directory -Path $outputDirectory -Force | Out-Null
}
$stagingExePath = Join-Path $outputDirectory 'ArenaBridge.building.exe'
if (Test-Path -LiteralPath $stagingExePath) { Remove-Item -LiteralPath $stagingExePath -Force }
$numericVersion = $sourceVersion + '.0'
Write-Step ("Compiling source version " + $sourceVersion + ' for channel ' + $Channel + '...')
$ps2exeArguments = @{
    inputFile = $sourcePath
    outputFile = $stagingExePath
    noConsole = $true
    STA = $true
    x64 = $true
    title = 'Arena Roblox Bridge'
    product = 'Arena Roblox Bridge'
    version = $numericVersion
}
Invoke-ps2exe @ps2exeArguments
if (-not (Test-Path -LiteralPath $stagingExePath -PathType Leaf)) {
    throw 'ps2exe returned without creating the requested staging executable.'
}

$file = Get-Item -LiteralPath $stagingExePath
if ($file.Length -le 0 -or $file.Length -gt [long]209715200) { # 200 MiB
    Remove-Item -LiteralPath $stagingExePath -Force -ErrorAction SilentlyContinue
    throw ("Unexpected EXE size: " + [string]$file.Length + ' bytes. Staging output removed.')
}
$sha256 = (Get-FileHash -LiteralPath $stagingExePath -Algorithm SHA256).Hash.ToLowerInvariant()
$backupPath = ''
try {
    if (Test-Path -LiteralPath $exePath -PathType Leaf) {
        $backupPath = Join-Path $outputDirectory ('ArenaBridge.previous-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff') + '.exe')
        [IO.File]::Replace($stagingExePath,$exePath,$backupPath,$true)
        Write-Step ("Previous user build preserved at " + $backupPath)
    } else {
        [IO.File]::Move($stagingExePath,$exePath)
    }
} catch {
    if ($backupPath -and (Test-Path -LiteralPath $backupPath) -and -not (Test-Path -LiteralPath $exePath)) {
        [IO.File]::Move($backupPath,$exePath)
    }
    throw ("Could not safely publish the local build output. Previous build is preserved when present. " + $_.Exception.Message)
}
$file = Get-Item -LiteralPath $exePath
$metadata = [ordered]@{
    schemaVersion = 1
    channel = $Channel
    version = $BuildVersion
    sourceVersion = $sourceVersion
    fileName = 'ArenaBridge.exe'
    sizeBytes = [long]$file.Length
    sha256 = $sha256
    builtAtUtc = [DateTime]::UtcNow.ToString('o')
    published = $false
    note = 'Local user build only. Publishing and channel-manifest edits are manual.'
}
$metadataPath = Join-Path $outputDirectory 'release-metadata.json'
[IO.File]::WriteAllText($metadataPath, ($metadata | ConvertTo-Json -Depth 6), [Text.UTF8Encoding]::new($false))
[IO.File]::WriteAllText((Join-Path $outputDirectory 'ArenaBridge.exe.sha256'), ($sha256 + '  ArenaBridge.exe' + [Environment]::NewLine), [Text.UTF8Encoding]::new($false))

Write-Step 'Build completed; no release or channel manifest was changed.'
Write-Host ("EXE:      " + $exePath)
Write-Host ("Version:  " + $BuildVersion)
Write-Host ("SHA-256:  " + $sha256)
Write-Host ("Metadata: " + $metadataPath)
