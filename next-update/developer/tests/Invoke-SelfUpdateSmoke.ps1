#requires -Version 5.1
<#
Arena Roblox Bridge - isolierter Selbst-Update-Test (NUR Windows, PowerShell 5.1)

Was dieser Test tut:
  1. Baut ZWEI Test-EXEs mit dem Builder (-TestFixtureBuild, Ausgabe unter %TEMP%):
     "installiert" = FileVersion 7.7.0.0, "neu" = FileVersion 7.7.1.0.
  2. Startet einen lokalen HTTP-Server NUR auf 127.0.0.1 (Start-Job) als Fixture.
  3. Prueft in isolierten Installationsordnern (nie in release\, nie in den echten
     Benutzerdaten, nie channels\*.json):
     check-Modus, Installation einer gestoppten EXE mit Backup und Neustart,
     Downgrade-Ablehnung, falscher Hash, Groessenlimit, deaktiviertes und
     ungueltiges Manifest, Netzwerkfehler, laufende EXE (wird NICHT beendet)
     und Rollback nach einem Fehler.

Der Test veraendert keine Datei ausserhalb von %TEMP%\arena-selfupdate-*.
Exit 0 = alle Pruefungen bestanden, 1 = mindestens eine fehlgeschlagen.
Exit 77 = nicht Windows (uebersprungen).
#>
[CmdletBinding()]
param(
    [string]$WorkRoot = '',
    [switch]$KeepWorkRoot
)

$ErrorActionPreference = 'Stop'

if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
    Write-Output 'SKIP: Der Selbst-Update-Test laeuft nur unter Windows.'
    exit 77
}

$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$updaterPath = Join-Path $projectRoot 'update-system\updater\Update-Bridge.ps1'
$builderPath = Join-Path $projectRoot 'builder\Build-EXE.ps1'
$channelsDir = Join-Path $projectRoot 'update-system\channels'
$windowsPowerShell = Join-Path $env:WINDIR 'System32\WindowsPowerShell\v1.0\powershell.exe'
$powerShellExe = $windowsPowerShell
if (-not (Test-Path -LiteralPath $powerShellExe -PathType Leaf)) { throw 'Windows PowerShell 5.1 nicht gefunden.' }

if ([string]::IsNullOrWhiteSpace($WorkRoot)) {
    $WorkRoot = Join-Path $env:TEMP ('arena-selfupdate-' + [Guid]::NewGuid().ToString('N').Substring(0, 12))
}
$WorkRoot = [IO.Path]::GetFullPath($WorkRoot)
if (Test-Path -LiteralPath $WorkRoot) { throw 'WorkRoot existiert bereits; bitte einen neuen Pfad angeben.' }
New-Item -ItemType Directory -Path $WorkRoot -Force | Out-Null

$script:Checks = New-Object System.Collections.ArrayList
$script:Failed = $false
function Assert-Check([string]$Name, [bool]$Condition, [string]$Detail = '') {
    [void]$script:Checks.Add([pscustomobject]@{ Name = $Name; Passed = $Condition })
    if ($Condition) { Write-Output ('[PASS] ' + $Name) }
    else {
        $script:Failed = $true
        Write-Output ('[FAIL] ' + $Name + $(if ($Detail) { ' -- ' + $Detail } else { '' }))
    }
}
function Get-FileSha([string]$Path) {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}
function Quote-Arg([string]$Value) { return ('"' + $Value + '"') }
function Write-Utf8([string]$Path, [string]$Text) {
    [IO.File]::WriteAllText($Path, $Text, (New-Object Text.UTF8Encoding($false)))
}
function Wait-ForFile([string]$Path, [int]$TimeoutSec) {
    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSec)
    while ([DateTime]::UtcNow -lt $deadline) {
        if (Test-Path -LiteralPath $Path -PathType Leaf) { return $true }
        Start-Sleep -Milliseconds 500
    }
    return (Test-Path -LiteralPath $Path -PathType Leaf)
}
function Read-Json([string]$Path) {
    return (Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json)
}

# ------------------------------------------------------------ Vorher: Kanaele merken
$channelHashesBefore = @{}
foreach ($file in Get-ChildItem -LiteralPath $channelsDir -Filter '*.json') {
    $channelHashesBefore[$file.Name] = Get-FileSha $file.FullName
}

# ------------------------------------------------------------ Builds
$buildInstalled = Join-Path $WorkRoot 'build-7.7.0'
$buildNew = Join-Path $WorkRoot 'build-7.7.1'
Write-Output '== Build 1: installierte Test-EXE (FileVersion 7.7.0.0)'
& $powerShellExe -NoLogo -NoProfile -ExecutionPolicy Bypass -File $builderPath -Channel beta -TestFixtureBuild -OutputDirectory $buildInstalled
Assert-Check 'Build der installierten Test-EXE gelingt' ($LASTEXITCODE -eq 0) ("Exit " + $LASTEXITCODE)
Write-Output '== Build 2: neue Test-EXE (FileVersion 7.7.1.0)'
& $powerShellExe -NoLogo -NoProfile -ExecutionPolicy Bypass -File $builderPath -Channel beta -TestFixtureBuild -TestFileVersion '7.7.1.0' -OutputDirectory $buildNew
Assert-Check 'Build der neuen Test-EXE gelingt' ($LASTEXITCODE -eq 0) ("Exit " + $LASTEXITCODE)

$exeInstalledSource = Join-Path $buildInstalled 'ArenaBridge.exe'
$exeNewSource = Join-Path $buildNew 'ArenaBridge.exe'
if (-not ((Test-Path -LiteralPath $exeInstalledSource) -and (Test-Path -LiteralPath $exeNewSource))) {
    Write-Output 'ABBRUCH: Test-EXEs fehlen; weitere Pruefungen sind nicht moeglich.'
    exit 1
}
$shaInstalled = Get-FileSha $exeInstalledSource
$shaNew = Get-FileSha $exeNewSource
$sizeInstalled = (Get-Item -LiteralPath $exeInstalledSource).Length
$sizeNew = (Get-Item -LiteralPath $exeNewSource).Length
Assert-Check 'Test-EXEs sind unterschiedlich (echte neue Datei)' ($shaInstalled -ne $shaNew)

$metaPath = Join-Path $buildInstalled 'release-metadata.json'
if (Test-Path -LiteralPath $metaPath) {
    $meta = Read-Json $metaPath
    $updaterSha = (Get-FileHash -LiteralPath (Join-Path $projectRoot 'update-system\updater\Update-Bridge.ps1') -Algorithm SHA256).Hash.ToLowerInvariant()
    Assert-Check 'Build-Metadaten: testFixtureBuild=true, updaterSha256 passt' ($meta.testFixtureBuild -eq $true -and $meta.updaterSha256 -eq $updaterSha -and $meta.published -eq $false)
} else {
    Assert-Check 'Build-Metadaten vorhanden' $false 'release-metadata.json fehlt'
}

# ------------------------------------------------------------ Fixture-Server (nur 127.0.0.1)
$serveDir = Join-Path $WorkRoot 'serve'
New-Item -ItemType Directory -Path $serveDir -Force | Out-Null
Copy-Item -LiteralPath $exeInstalledSource -Destination (Join-Path $serveDir 'ArenaBridge-770.exe')
Copy-Item -LiteralPath $exeNewSource -Destination (Join-Path $serveDir 'ArenaBridge-771.exe')

function Get-FreePort {
    $probe = New-Object Net.Sockets.TcpListener([Net.IPAddress]::Loopback, 0)
    $probe.Start()
    $port = ([Net.IPEndPoint]$probe.LocalEndpoint).Port
    $probe.Stop()
    return $port
}
$port = Get-FreePort
$deadPort = Get-FreePort   # wird NICHT belegt: Verbindungsfehler fuer den Netzwerktest

$serverJob = Start-Job -ArgumentList $port, $serveDir -ScriptBlock {
    param([int]$Port, [string]$Dir)
    $listener = New-Object System.Net.HttpListener
    $listener.Prefixes.Add('http://127.0.0.1:' + $Port + '/')
    $listener.Start()
    try {
        while ($true) {
            $context = $listener.GetContext()
            $name = [IO.Path]::GetFileName($context.Request.Url.LocalPath)
            $file = Join-Path $Dir $name
            if ($name -ne '' -and (Test-Path -LiteralPath $file -PathType Leaf)) {
                $bytes = [IO.File]::ReadAllBytes($file)
                $context.Response.StatusCode = 200
                $context.Response.ContentLength64 = $bytes.Length
                $context.Response.OutputStream.Write($bytes, 0, $bytes.Length)
            } else {
                $context.Response.StatusCode = 404
            }
            $context.Response.OutputStream.Close()
        }
    } finally { $listener.Stop() }
}

$serverReady = $false
$serverDeadline = [DateTime]::UtcNow.AddSeconds(20)
while (-not $serverReady -and [DateTime]::UtcNow -lt $serverDeadline) {
    try {
        $client = New-Object Net.Sockets.TcpClient
        $client.Connect('127.0.0.1', $port)
        $client.Close()
        $serverReady = $true
    } catch { Start-Sleep -Milliseconds 400 }
}
Assert-Check 'Fixture-Server auf 127.0.0.1 erreichbar' $serverReady
$urlInstalled = 'http://127.0.0.1:' + $port + '/ArenaBridge-770.exe'
$urlNew = 'http://127.0.0.1:' + $port + '/ArenaBridge-771.exe'

# ------------------------------------------------------------ Hilfsfunktionen fuer Szenarien
function New-Manifest([string]$Name, [string]$Version, [string]$Url, [string]$Sha, [long]$Size, [bool]$Enabled = $true) {
    $path = Join-Path $WorkRoot ('manifest-' + $Name + '.json')
    $manifest = [ordered]@{
        schemaVersion = 1
        channel = 'beta'
        enabled = $Enabled
        testFixture = $true
        version = $Version
        publishedAtUtc = '2026-10-10T12:00:00Z'
        minimumUpdaterVersion = '1.1.0'
        mandatory = $false
        artifact = [ordered]@{ fileName = 'ArenaBridge.exe'; url = $Url; sha256 = $Sha; sizeBytes = $Size }
        notes = @('Privater Selbst-Update-Test (Fixture).')
    }
    Write-Utf8 $path ($manifest | ConvertTo-Json -Depth 6)
    return $path
}

function New-Install([string]$Case, [string]$SourceExe) {
    $dir = Join-Path $WorkRoot ($Case + '\install')
    New-Item -ItemType Directory -Path $dir -Force | Out-Null
    Copy-Item -LiteralPath $SourceExe -Destination (Join-Path $dir 'ArenaBridge.exe')
    return $dir
}

function Invoke-Updater([string]$Mode, [string]$InstallDir, [string]$ManifestPath, [string]$Case, [string[]]$Extra = @()) {
    $logPath = Join-Path $WorkRoot ($Case + '\updater.log')
    $resultPath = Join-Path $WorkRoot ($Case + '\result.json')
    New-Item -ItemType Directory -Path (Split-Path -Parent $logPath) -Force | Out-Null
    $argumentList = @(
        '-NoLogo', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass',
        '-File', (Quote-Arg $updaterPath),
        '-Mode', $Mode, '-Channel', 'beta',
        '-InstallDirectory', (Quote-Arg $InstallDir),
        '-ManifestPath', (Quote-Arg $ManifestPath),
        '-TestFixtureMode',
        '-ResultPath', (Quote-Arg $resultPath),
        '-LogPath', (Quote-Arg $logPath)
    ) + $Extra
    $process = Start-Process -FilePath $powerShellExe -ArgumentList ($argumentList -join ' ') -Wait -PassThru -WindowStyle Hidden
    return [pscustomobject]@{ ExitCode = $process.ExitCode; ResultPath = $resultPath; LogPath = $logPath }
}

function Get-StatusFile([string]$InstallDir) {
    $path = Join-Path $InstallDir 'update-status.json'
    if (Test-Path -LiteralPath $path -PathType Leaf) { return Read-Json $path }
    return $null
}

# ------------------------------------------------------------ Szenario 1: check, update verfuegbar
$inst1 = New-Install 's1' $exeInstalledSource
$manifest771 = New-Manifest 'new771' '7.7.1' $urlNew $shaNew $sizeNew
$run = Invoke-Updater 'check' $inst1 $manifest771 's1'
$result = if (Test-Path -LiteralPath $run.ResultPath) { Read-Json $run.ResultPath } else { $null }
Assert-Check 'S1 check: Exit 0 und Status update-available' ($run.ExitCode -eq 0 -and $null -ne $result -and $result.status -eq 'update-available') ("Exit " + $run.ExitCode)
Assert-Check 'S1 check: installierte EXE unveraendert' ((Get-FileSha (Join-Path $inst1 'ArenaBridge.exe')) -eq $shaInstalled)

# ------------------------------------------------------------ Szenario 2: gestoppte EXE, Installation, Backup, Neustart
$inst2 = New-Install 's2' $exeInstalledSource
$reportPath2 = Join-Path $WorkRoot 's2\smoke-report.json'
New-Item -ItemType Directory -Path (Split-Path -Parent $reportPath2) -Force | Out-Null
$previousSmoke = $env:ARENABRIDGE_BUILD_SMOKE
$previousSmokePath = $env:ARENABRIDGE_BUILD_SMOKE_PATH
$env:ARENABRIDGE_BUILD_SMOKE = '1'
$env:ARENABRIDGE_BUILD_SMOKE_PATH = $reportPath2
try {
    $run = Invoke-Updater 'install' $inst2 $manifest771 's2' @('-WaitForProcessId', '0', '-StartAfterUpdate')
    Assert-Check 'S2 install: Exit 0' ($run.ExitCode -eq 0) ("Exit " + $run.ExitCode)
    $installedSha = Get-FileSha (Join-Path $inst2 'ArenaBridge.exe')
    Assert-Check 'S2 install: EXE ist die neue Datei (SHA-256)' ($installedSha -eq $shaNew)
    $backups = @(Get-ChildItem -LiteralPath (Join-Path $inst2 '.arena-update\backup') -Filter 'ArenaBridge.exe.7.7.0-*.bak' -ErrorAction SilentlyContinue)
    Assert-Check 'S2 backup: alte EXE liegt als .bak mit SHA-256 der alten Version' ($backups.Count -eq 1 -and (Get-FileSha $backups[0].FullName) -eq $shaInstalled)
    $state = Join-Path $inst2 'update-state.json'
    $stateOk = $false
    if (Test-Path -LiteralPath $state) { $s = Read-Json $state; $stateOk = ($s.version -eq '7.7.1' -and $s.sha256 -eq $shaNew) }
    Assert-Check 'S2 update-state.json: Version 7.7.1 und SHA-256 der neuen EXE' $stateOk
    $status2 = Get-StatusFile $inst2
    Assert-Check 'S2 update-status.json: Version 7.7.1' ($null -ne $status2 -and $status2.version -eq '7.7.1')
    $restarted = Wait-ForFile $reportPath2 90
    $smokeOk = $false
    if ($restarted) { $r2 = Read-Json $reportPath2; $smokeOk = ($r2.status -eq 'passed') }
    Assert-Check 'S2 Neustart: neue EXE startet und meldet Smoke-Status passed' ($restarted -and $smokeOk)
} finally {
    if ($null -eq $previousSmoke) { Remove-Item Env:\ARENABRIDGE_BUILD_SMOKE -ErrorAction SilentlyContinue } else { $env:ARENABRIDGE_BUILD_SMOKE = $previousSmoke }
    if ($null -eq $previousSmokePath) { Remove-Item Env:\ARENABRIDGE_BUILD_SMOKE_PATH -ErrorAction SilentlyContinue } else { $env:ARENABRIDGE_BUILD_SMOKE_PATH = $previousSmokePath }
}

# ------------------------------------------------------------ Szenario 3: Downgrade wird abgelehnt
$inst3 = New-Install 's3' $exeInstalledSource
$manifest760 = New-Manifest 'old760' '7.6.0' $urlNew $shaNew $sizeNew
$run = Invoke-Updater 'check' $inst3 $manifest760 's3'
$result = if (Test-Path -LiteralPath $run.ResultPath) { Read-Json $run.ResultPath } else { $null }
Assert-Check 'S3 Downgrade: check meldet downgrade-refused' ($null -ne $result -and $result.status -eq 'downgrade-refused')
$run = Invoke-Updater 'install' $inst3 $manifest760 's3' @('-WaitForProcessId', '0')
Assert-Check 'S3 Downgrade: install veraendert die EXE nicht' ((Get-FileSha (Join-Path $inst3 'ArenaBridge.exe')) -eq $shaInstalled)

# ------------------------------------------------------------ Szenario 4: falscher Hash
$inst4 = New-Install 's4' $exeInstalledSource
$manifestBadHash = New-Manifest 'badhash' '7.7.1' $urlNew ('0' * 64) $sizeNew
$run = Invoke-Updater 'install' $inst4 $manifestBadHash 's4' @('-WaitForProcessId', '0')
Assert-Check 'S4 falscher Hash: Exit ungleich 0' ($run.ExitCode -ne 0)
Assert-Check 'S4 falscher Hash: EXE unveraendert (alte SHA-256)' ((Get-FileSha (Join-Path $inst4 'ArenaBridge.exe')) -eq $shaInstalled)
$rejected4 = @(Get-ChildItem -LiteralPath (Join-Path $inst4 '.arena-update\rejected') -ErrorAction SilentlyContinue)
Assert-Check 'S4 falscher Hash: abgelehnte Datei liegt in rejected\' ($rejected4.Count -ge 1)
$status4 = Get-StatusFile $inst4
Assert-Check 'S4 falscher Hash: update-status.json meldet Fehler' ($null -ne $status4 -and [string]$status4.error -ne '')

# ------------------------------------------------------------ Szenario 5: Groessenlimit / gemeldete Groesse
$inst5 = New-Install 's5' $exeInstalledSource
$manifestSmall = New-Manifest 'toosmall' '7.7.1' $urlNew $shaNew ($sizeNew - 1)
$run = Invoke-Updater 'install' $inst5 $manifestSmall 's5' @('-WaitForProcessId', '0')
Assert-Check 'S5 Groesse: Exit ungleich 0 (mehr Bytes als deklariert)' ($run.ExitCode -ne 0)
Assert-Check 'S5 Groesse: EXE unveraendert' ((Get-FileSha (Join-Path $inst5 'ArenaBridge.exe')) -eq $shaInstalled)
$manifestHuge = New-Manifest 'huge' '7.7.1' $urlNew $shaNew 67108865
$run = Invoke-Updater 'check' $inst5 $manifestHuge 's5b'
$result = if (Test-Path -LiteralPath $run.ResultPath) { Read-Json $run.ResultPath } else { $null }
Assert-Check 'S5 Groesse: ueber 64 MiB wird im check als error abgelehnt' ($null -ne $result -and $result.status -eq 'error')

# ------------------------------------------------------------ Szenario 6: deaktiviertes Manifest
$inst6 = New-Install 's6' $exeInstalledSource
$manifestDisabled = New-Manifest 'disabled' '7.7.1' $urlNew $shaNew $sizeNew $false
$run = Invoke-Updater 'check' $inst6 $manifestDisabled 's6'
$result = if (Test-Path -LiteralPath $run.ResultPath) { Read-Json $run.ResultPath } else { $null }
Assert-Check 'S6 deaktiviert: check meldet disabled' ($null -ne $result -and $result.status -eq 'disabled')

# ------------------------------------------------------------ Szenario 7: ungueltiges Manifest
$inst7 = New-Install 's7' $exeInstalledSource
$invalidPath = Join-Path $WorkRoot 'manifest-invalid.json'
Write-Utf8 $invalidPath '{"schemaVersion":2,"channel":"beta"}'
$run = Invoke-Updater 'check' $inst7 $invalidPath 's7'
$result = if (Test-Path -LiteralPath $run.ResultPath) { Read-Json $run.ResultPath } else { $null }
Assert-Check 'S7 ungueltiges Manifest: check meldet error' ($null -ne $result -and $result.status -eq 'error')

# ------------------------------------------------------------ Szenario 8: Netzwerkfehler (kein Listener)
$inst8 = New-Install 's8' $exeInstalledSource
$manifestDead = New-Manifest 'dead' '7.7.1' ('http://127.0.0.1:' + $deadPort + '/ArenaBridge-771.exe') $shaNew $sizeNew
$run = Invoke-Updater 'install' $inst8 $manifestDead 's8' @('-WaitForProcessId', '0')
Assert-Check 'S8 Netzwerkfehler: Exit ungleich 0' ($run.ExitCode -ne 0)
Assert-Check 'S8 Netzwerkfehler: EXE unveraendert' ((Get-FileSha (Join-Path $inst8 'ArenaBridge.exe')) -eq $shaInstalled)

# ------------------------------------------------------------ Szenario 9: laufende EXE wird NICHT beendet
$inst9 = New-Install 's9' (Join-Path $env:WINDIR 'System32\notepad.exe')
$shaNotepad = Get-FileSha (Join-Path $inst9 'ArenaBridge.exe')
$running = Start-Process -FilePath (Join-Path $inst9 'ArenaBridge.exe') -PassThru
Start-Sleep -Milliseconds 1500
try {
    $run = Invoke-Updater 'install' $inst9 $manifest771 's9' @('-WaitForProcessId', [string]$running.Id, '-WaitTimeoutSeconds', '5')
    Assert-Check 'S9 laufende EXE: Installation wird verweigert (Exit ungleich 0)' ($run.ExitCode -ne 0)
    Assert-Check 'S9 laufende EXE: der Updater hat den Prozess NICHT beendet' (-not $running.HasExited)
    Assert-Check 'S9 laufende EXE: Datei unveraendert' ((Get-FileSha (Join-Path $inst9 'ArenaBridge.exe')) -eq $shaNotepad)
} finally {
    # Testprozess gehoert diesem Harness; nur er wird am Ende beendet.
    if (-not $running.HasExited) { Stop-Process -Id $running.Id -Force -ErrorAction SilentlyContinue }
}

# ------------------------------------------------------------ Szenario 10: Rollback nach Fehler nach dem Ersetzen
$inst10 = New-Install 's10' $exeInstalledSource
$reportPath10 = Join-Path $WorkRoot 's10\smoke-report.json'
New-Item -ItemType Directory -Path (Split-Path -Parent $reportPath10) -Force | Out-Null
$previousSmoke = $env:ARENABRIDGE_BUILD_SMOKE
$previousSmokePath = $env:ARENABRIDGE_BUILD_SMOKE_PATH
$env:ARENABRIDGE_BUILD_SMOKE = '1'
$env:ARENABRIDGE_BUILD_SMOKE_PATH = $reportPath10
try {
    $run = Invoke-Updater 'install' $inst10 $manifest771 's10' @('-WaitForProcessId', '0', '-StartAfterUpdate', '-TestFault', 'after-replace')
    Assert-Check 'S10 Rollback: Exit ungleich 0' ($run.ExitCode -ne 0)
    Assert-Check 'S10 Rollback: alte EXE wiederhergestellt (SHA-256)' ((Get-FileSha (Join-Path $inst10 'ArenaBridge.exe')) -eq $shaInstalled)
    $rejected10 = @(Get-ChildItem -LiteralPath (Join-Path $inst10 '.arena-update\rejected') -ErrorAction SilentlyContinue)
    Assert-Check 'S10 Rollback: fehlerhafte neue EXE liegt in rejected\' ($rejected10.Count -ge 1)
    $status10 = Get-StatusFile $inst10
    Assert-Check 'S10 Rollback: update-status.json meldet Fehler/Wiederherstellung' ($null -ne $status10 -and [string]$status10.error -match 'wiederhergestellt')
    $restarted10 = Wait-ForFile $reportPath10 90
    Assert-Check 'S10 Rollback: alte EXE wird mit update-fehler neu gestartet' $restarted10
} finally {
    if ($null -eq $previousSmoke) { Remove-Item Env:\ARENABRIDGE_BUILD_SMOKE -ErrorAction SilentlyContinue } else { $env:ARENABRIDGE_BUILD_SMOKE = $previousSmoke }
    if ($null -eq $previousSmokePath) { Remove-Item Env:\ARENABRIDGE_BUILD_SMOKE_PATH -ErrorAction SilentlyContinue } else { $env:ARENABRIDGE_BUILD_SMOKE_PATH = $previousSmokePath }
}

# ------------------------------------------------------------ Aufraeumen und Schutzpruefung
try { Stop-Job -Job $serverJob -ErrorAction SilentlyContinue } catch {}
try { Remove-Job -Job $serverJob -Force -ErrorAction SilentlyContinue } catch {}

$channelsUnchanged = $true
foreach ($name in $channelHashesBefore.Keys) {
    if ((Get-FileSha (Join-Path $channelsDir $name)) -ne $channelHashesBefore[$name]) { $channelsUnchanged = $false }
}
Assert-Check 'Kanal-Manifeste beta.json/stable.json wurden NICHT veraendert' $channelsUnchanged

$passed = @($script:Checks | Where-Object { $_.Passed }).Count
$total = $script:Checks.Count
Write-Output ''
Write-Output ('Selbst-Update-Test: ' + $passed + ' von ' + $total + ' Pruefungen bestanden.')
Write-Output ('Arbeitsordner: ' + $WorkRoot)
if (-not $KeepWorkRoot -and -not $script:Failed) {
    Remove-Item -LiteralPath $WorkRoot -Recurse -Force -ErrorAction SilentlyContinue
} else {
    Write-Output 'Arbeitsordner bleibt fuer die Analyse erhalten.'
}
if ($script:Failed) { exit 1 }
exit 0
