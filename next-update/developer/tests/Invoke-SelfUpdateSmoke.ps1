#requires -Version 5.1
<#
Arena Roblox Bridge - isolierter Selbst-Update-Test (NUR Windows, PowerShell 5.1)

Was dieser Test tut:
  1. Baut ZWEI Test-EXEs mit dem Builder (-TestFixtureBuild, Ausgabe unter %TEMP%):
     "installiert" = Dateiversion der Quellversion (z. B. 7.8.0.0), "neu" = dieselbe
     Version mit um 1 erhoehtem Patch (z. B. 7.8.1.0). Die Versionen werden aus
     app/version.json gelesen, der Test ist damit nicht an eine feste Nummer gebunden.
  2. Startet einen lokalen HTTP-Server NUR auf 127.0.0.1 (Start-Job) als Fixture.
  3. Prueft in isolierten Installationsordnern (nie in release\, nie in den echten
     Benutzerdaten, nie in den Kanal-Dateien):
     S1  check mit Ergebnis-JSON (Schema 2)
     S2  Installation einer gestoppten EXE mit Backup, Zustandsdatei und Neustart
     S3  Downgrade wird abgelehnt
     S4  falscher SHA-256 wird abgelehnt und archiviert
     S5  Groessenlimit und falsche Groesse
     S6  deaktivierter Kanal aendert nichts
     S7  ungueltiges Manifest
     S8  Netzwerkfehler (kein Listener)
     S9  laufende EXE wird NIE beendet
     S10 Rollback nach einem Fehler nach dem Ersetzen
     S11 falsche Dateiversion im Artefakt wird abgelehnt (Manifest/Datei passen nicht)
     S12 aeltere sequence im Manifest wird nie installiert (Schutz vor Cache-Stand)
     S13 Abbruch waehrend des Downloads laesst alles unveraendert
     S14 Diagnose-Modus (doctor) liefert einen Bericht
     S15 Fortschrittsdatei meldet den Abschluss

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
$versionFile = Join-Path $projectRoot 'app\version.json'
$windowsPowerShell = Join-Path $env:WINDIR 'System32\WindowsPowerShell\v1.0\powershell.exe'
$powerShellExe = $windowsPowerShell
if (-not (Test-Path -LiteralPath $powerShellExe -PathType Leaf)) { throw 'Windows PowerShell 5.1 nicht gefunden.' }

$sourceVersion = [string](Get-Content -LiteralPath $versionFile -Raw -Encoding UTF8 | ConvertFrom-Json).version
if ($sourceVersion -notmatch '^\d+\.\d+\.\d+$') { throw 'app/version.json enthaelt keine dreiteilige Version.' }
$installedVersion = $sourceVersion
$versionParts = $sourceVersion.Split('.')
$newVersion = $versionParts[0] + '.' + $versionParts[1] + '.' + [string]([int]$versionParts[2] + 1)
$downgradeVersion = '1.0.0'
$slowVersion = $newVersion + '-slow'

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
function Read-Progress([string]$InstallDir) {
    $path = Join-Path $InstallDir '.arena-update\update-progress.json'
    if (Test-Path -LiteralPath $path -PathType Leaf) {
        try { return (Read-Json $path) } catch { return $null }
    }
    return $null
}

Write-Output ('Quellversion ' + $sourceVersion + ' -> Testversionen ' + $installedVersion + ' und ' + $newVersion + '.')

# ------------------------------------------------------------ Vorher: Kanaele merken
$channelHashesBefore = @{}
foreach ($file in Get-ChildItem -LiteralPath $channelsDir -Filter '*.json') {
    $channelHashesBefore[$file.Name] = Get-FileSha $file.FullName
}

# ------------------------------------------------------------ Builds
$buildInstalled = Join-Path $WorkRoot 'build-installed'
$buildNew = Join-Path $WorkRoot 'build-new'
Write-Output '== Build 1: installierte Test-EXE'
& $powerShellExe -NoLogo -NoProfile -ExecutionPolicy Bypass -File $builderPath -Channel beta -TestFixtureBuild -TestFileVersion ($installedVersion + '.0') -OutputDirectory $buildInstalled
Assert-Check 'Build der installierten Test-EXE gelingt' ($LASTEXITCODE -eq 0) ('Exit ' + $LASTEXITCODE)
Write-Output '== Build 2: neue Test-EXE'
& $powerShellExe -NoLogo -NoProfile -ExecutionPolicy Bypass -File $builderPath -Channel beta -TestFixtureBuild -TestFileVersion ($newVersion + '.0') -OutputDirectory $buildNew
Assert-Check 'Build der neuen Test-EXE gelingt' ($LASTEXITCODE -eq 0) ('Exit ' + $LASTEXITCODE)

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
    $updaterSha = Get-FileSha $updaterPath
    Assert-Check 'Build-Metadaten: testFixtureBuild=true, updaterSha256 passt, nichts veroeffentlicht' `
        ($meta.testFixtureBuild -eq $true -and $meta.updaterSha256 -eq $updaterSha -and $meta.published -eq $false)
} else {
    Assert-Check 'Build-Metadaten vorhanden' $false 'release-metadata.json fehlt'
}

# ------------------------------------------------------------ Fixture-Server (nur 127.0.0.1)
$serveDir = Join-Path $WorkRoot 'serve'
New-Item -ItemType Directory -Path $serveDir -Force | Out-Null
Copy-Item -LiteralPath $exeInstalledSource -Destination (Join-Path $serveDir ('ArenaBridge-' + $installedVersion + '.exe'))
Copy-Item -LiteralPath $exeNewSource -Destination (Join-Path $serveDir ('ArenaBridge-' + $newVersion + '.exe'))
Copy-Item -LiteralPath $exeNewSource -Destination (Join-Path $serveDir ('ArenaBridge-' + $slowVersion + '.exe'))

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
                if ($name -like '*slow*') {
                    # Absichtlich langsam: damit der Abbruchtest wirklich waehrend
                    # des Downloads greift.
                    $offset = 0
                    while ($offset -lt $bytes.Length) {
                        $count = [Math]::Min(32768, $bytes.Length - $offset)
                        $context.Response.OutputStream.Write($bytes, $offset, $count)
                        $context.Response.OutputStream.Flush()
                        $offset += $count
                        Start-Sleep -Milliseconds 220
                    }
                } else {
                    $context.Response.OutputStream.Write($bytes, 0, $bytes.Length)
                }
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

# ------------------------------------------------------------ Hilfsfunktionen fuer Szenarien
function New-Manifest {
    param(
        [string]$Name,
        [string]$Version,
        [string]$Url,
        [string]$Sha,
        [long]$Size,
        [int]$Sequence = 5,
        [bool]$Enabled = $true,
        [string]$Channel = 'beta',
        [string]$FileName = ''
    )
    if ([string]::IsNullOrWhiteSpace($FileName)) { $FileName = 'ArenaBridge-' + $Version + '.exe' }
    $path = Join-Path $WorkRoot ('manifest-' + $Name + '.json')
    $manifest = [ordered]@{
        schemaVersion = 2
        channel = $Channel
        enabled = $Enabled
        testFixture = $true
        sequence = $Sequence
        version = $Version
        publishedAtUtc = '2026-10-11T06:00:00Z'
        minimumUpdaterVersion = '2.0.0'
        artifact = [ordered]@{ fileName = $FileName; url = $Url; sha256 = $Sha; sizeBytes = $Size }
        notes = @('Privater Selbst-Update-Test (Fixture).')
    }
    if (-not $Enabled) {
        $manifest.version = ''
        $manifest.publishedAtUtc = ''
        $manifest.artifact = [ordered]@{ fileName = 'ArenaBridge.exe'; url = ''; sha256 = ''; sizeBytes = 0 }
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

function Invoke-Updater {
    param(
        [string]$Mode,
        [string]$InstallDir,
        [string]$ManifestPath = '',
        [string]$Case = 'case',
        [string[]]$Extra = @(),
        [string]$Channel = 'beta',
        [switch]$Hide
    )
    $logPath = Join-Path $WorkRoot ($Case + '\updater.log')
    $resultPath = Join-Path $WorkRoot ($Case + '\result.json')
    New-Item -ItemType Directory -Path (Split-Path -Parent $logPath) -Force | Out-Null
    $argumentList = @(
        '-NoLogo', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass',
        '-File', (Quote-Arg $updaterPath),
        '-Mode', $Mode, '-Channel', $Channel,
        '-InstallDirectory', (Quote-Arg $InstallDir),
        '-TestFixtureMode',
        '-ResultPath', (Quote-Arg $resultPath),
        '-LogPath', (Quote-Arg $logPath)
    )
    if (-not [string]::IsNullOrWhiteSpace($ManifestPath)) {
        $argumentList += @('-ManifestPath', (Quote-Arg $ManifestPath))
    }
    $argumentList += $Extra
    if ($Hide) {
        $process = Start-Process -FilePath $powerShellExe -ArgumentList ($argumentList -join ' ') -PassThru -WindowStyle Hidden
        return [pscustomobject]@{ Process = $process; ExitCode = $null; ResultPath = $resultPath; LogPath = $logPath }
    }
    $process = Start-Process -FilePath $powerShellExe -ArgumentList ($argumentList -join ' ') -Wait -PassThru -WindowStyle Hidden
    return [pscustomobject]@{ Process = $process; ExitCode = $process.ExitCode; ResultPath = $resultPath; LogPath = $logPath }
}

function Get-StatusFile([string]$InstallDir) {
    $path = Join-Path $InstallDir 'update-status.json'
    if (Test-Path -LiteralPath $path -PathType Leaf) { return Read-Json $path }
    return $null
}

$urlInstalled = 'http://127.0.0.1:' + $port + '/ArenaBridge-' + $installedVersion + '.exe'
$urlNew = 'http://127.0.0.1:' + $port + '/ArenaBridge-' + $newVersion + '.exe'
$urlSlow = 'http://127.0.0.1:' + $port + '/ArenaBridge-' + $slowVersion + '.exe'

# ------------------------------------------------------------ Szenario 1: check, update verfuegbar
$inst1 = New-Install 's1' $exeInstalledSource
$manifestNew = New-Manifest 'new' $newVersion $urlNew $shaNew $sizeNew 7
$run = Invoke-Updater -Mode 'check' -InstallDir $inst1 -ManifestPath $manifestNew -Case 's1'
$result = if (Test-Path -LiteralPath $run.ResultPath) { Read-Json $run.ResultPath } else { $null }
Assert-Check 'S1 check: Exit 0 und Status update-available' ($run.ExitCode -eq 0 -and $null -ne $result -and $result.status -eq 'update-available') ('Exit ' + $run.ExitCode)
Assert-Check 'S1 check: Ergebnis-JSON hat Schema 2 und die sequence' ($null -ne $result -and $result.schemaVersion -eq 2 -and $result.sequence -eq 7)
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
    $run = Invoke-Updater -Mode 'install' -InstallDir $inst2 -ManifestPath $manifestNew -Case 's2' -Extra @('-WaitForProcessId', '0', '-StartAfterUpdate')
    Assert-Check 'S2 install: Exit 0' ($run.ExitCode -eq 0) ('Exit ' + $run.ExitCode)
    $installedSha = Get-FileSha (Join-Path $inst2 'ArenaBridge.exe')
    Assert-Check 'S2 install: EXE ist die neue Datei (SHA-256)' ($installedSha -eq $shaNew)
    $backups = @(Get-ChildItem -LiteralPath (Join-Path $inst2 '.arena-update\backup') -Filter ('ArenaBridge.exe.' + $installedVersion + '-*.bak') -ErrorAction SilentlyContinue)
    Assert-Check 'S2 backup: alte EXE liegt als .bak mit SHA-256 der alten Version' ($backups.Count -eq 1 -and (Get-FileSha $backups[0].FullName) -eq $shaInstalled)
    $state = Join-Path $inst2 'update-state.json'
    $stateOk = $false
    if (Test-Path -LiteralPath $state) {
        $s = Read-Json $state
        $stateOk = ($s.schemaVersion -eq 2 -and $s.version -eq $newVersion -and $s.sha256 -eq $shaNew -and $s.sequence -eq 7)
    }
    Assert-Check 'S2 update-state.json: Schema 2, Version, SHA-256 und sequence' $stateOk
    $status2 = Get-StatusFile $inst2
    Assert-Check 'S2 update-status.json: neue Version' ($null -ne $status2 -and $status2.version -eq $newVersion)
    $history2 = Join-Path $inst2 'update-history.json'
    $historyOk = $false
    if (Test-Path -LiteralPath $history2) {
        $h = Read-Json $history2
        $historyOk = (@($h.entries).Count -ge 1 -and [string]$h.entries[0].status -eq 'ok')
    }
    Assert-Check 'S2 update-history.json: erfolgreicher Lauf eingetragen' $historyOk
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
$manifestOld = New-Manifest 'old' $downgradeVersion $urlNew $shaNew $sizeNew 8
$run = Invoke-Updater -Mode 'check' -InstallDir $inst3 -ManifestPath $manifestOld -Case 's3'
$result = if (Test-Path -LiteralPath $run.ResultPath) { Read-Json $run.ResultPath } else { $null }
Assert-Check 'S3 Downgrade: check meldet downgrade-refused' ($null -ne $result -and $result.status -eq 'downgrade-refused')
$run = Invoke-Updater -Mode 'install' -InstallDir $inst3 -ManifestPath $manifestOld -Case 's3' -Extra @('-WaitForProcessId', '0')
Assert-Check 'S3 Downgrade: install veraendert die EXE nicht' ((Get-FileSha (Join-Path $inst3 'ArenaBridge.exe')) -eq $shaInstalled)

# ------------------------------------------------------------ Szenario 4: falscher Hash
$inst4 = New-Install 's4' $exeInstalledSource
$manifestBadHash = New-Manifest 'badhash' $newVersion $urlNew ('0' * 64) $sizeNew 9
$run = Invoke-Updater -Mode 'install' -InstallDir $inst4 -ManifestPath $manifestBadHash -Case 's4' -Extra @('-WaitForProcessId', '0')
Assert-Check 'S4 falscher Hash: Exit ungleich 0' ($run.ExitCode -ne 0)
Assert-Check 'S4 falscher Hash: EXE unveraendert (alte SHA-256)' ((Get-FileSha (Join-Path $inst4 'ArenaBridge.exe')) -eq $shaInstalled)
$rejected4 = @(Get-ChildItem -LiteralPath (Join-Path $inst4 '.arena-update\rejected') -ErrorAction SilentlyContinue)
Assert-Check 'S4 falscher Hash: abgelehnte Datei liegt in rejected\' ($rejected4.Count -ge 1)
$status4 = Get-StatusFile $inst4
Assert-Check 'S4 falscher Hash: update-status.json meldet Fehler' ($null -ne $status4 -and [string]$status4.error -ne '')

# ------------------------------------------------------------ Szenario 5: Groessenlimit / gemeldete Groesse
$inst5 = New-Install 's5' $exeInstalledSource
$manifestSmall = New-Manifest 'toosmall' $newVersion $urlNew $shaNew ($sizeNew - 1) 10
$run = Invoke-Updater -Mode 'install' -InstallDir $inst5 -ManifestPath $manifestSmall -Case 's5' -Extra @('-WaitForProcessId', '0')
Assert-Check 'S5 Groesse: Exit ungleich 0 (mehr Bytes als deklariert)' ($run.ExitCode -ne 0)
Assert-Check 'S5 Groesse: EXE unveraendert' ((Get-FileSha (Join-Path $inst5 'ArenaBridge.exe')) -eq $shaInstalled)
$manifestHuge = New-Manifest 'huge' $newVersion $urlNew $shaNew 67108865 11
$run = Invoke-Updater -Mode 'check' -InstallDir $inst5 -ManifestPath $manifestHuge -Case 's5b'
$result = if (Test-Path -LiteralPath $run.ResultPath) { Read-Json $run.ResultPath } else { $null }
Assert-Check 'S5 Groesse: ueber 64 MiB wird im check als error abgelehnt' ($null -ne $result -and $result.status -eq 'error')

# ------------------------------------------------------------ Szenario 6: deaktiviertes Manifest
$inst6 = New-Install 's6' $exeInstalledSource
$manifestDisabled = New-Manifest 'disabled' '' '' '' 0 12 $false
$run = Invoke-Updater -Mode 'check' -InstallDir $inst6 -ManifestPath $manifestDisabled -Case 's6'
$result = if (Test-Path -LiteralPath $run.ResultPath) { Read-Json $run.ResultPath } else { $null }
Assert-Check 'S6 deaktiviert: check meldet disabled' ($null -ne $result -and $result.status -eq 'disabled')
$run = Invoke-Updater -Mode 'install' -InstallDir $inst6 -ManifestPath $manifestDisabled -Case 's6' -Extra @('-WaitForProcessId', '0')
$progress6 = Read-Progress $inst6
Assert-Check 'S6 deaktiviert: install meldet Fortschritt nothing und aendert nichts' `
    ($run.ExitCode -eq 0 -and $null -ne $progress6 -and $progress6.phase -eq 'nothing' -and (Get-FileSha (Join-Path $inst6 'ArenaBridge.exe')) -eq $shaInstalled)

# ------------------------------------------------------------ Szenario 7: ungueltiges Manifest
$inst7 = New-Install 's7' $exeInstalledSource
$invalidPath = Join-Path $WorkRoot 'manifest-invalid.json'
Write-Utf8 $invalidPath '{"schemaVersion":2,"channel":"beta","enabled":true}'
$run = Invoke-Updater -Mode 'check' -InstallDir $inst7 -ManifestPath $invalidPath -Case 's7'
$result = if (Test-Path -LiteralPath $run.ResultPath) { Read-Json $run.ResultPath } else { $null }
Assert-Check 'S7 ungueltiges Manifest: check meldet error' ($null -ne $result -and $result.status -eq 'error')

# ------------------------------------------------------------ Szenario 8: Netzwerkfehler (kein Listener)
$inst8 = New-Install 's8' $exeInstalledSource
$manifestDead = New-Manifest 'dead' $newVersion ('http://127.0.0.1:' + $deadPort + '/ArenaBridge-' + $newVersion + '.exe') $shaNew $sizeNew 13
$run = Invoke-Updater -Mode 'install' -InstallDir $inst8 -ManifestPath $manifestDead -Case 's8' -Extra @('-WaitForProcessId', '0')
Assert-Check 'S8 Netzwerkfehler: Exit ungleich 0' ($run.ExitCode -ne 0)
Assert-Check 'S8 Netzwerkfehler: EXE unveraendert' ((Get-FileSha (Join-Path $inst8 'ArenaBridge.exe')) -eq $shaInstalled)

# ------------------------------------------------------------ Szenario 9: laufende EXE wird NICHT beendet
$inst9 = New-Install 's9' (Join-Path $env:WINDIR 'System32\notepad.exe')
$shaNotepad = Get-FileSha (Join-Path $inst9 'ArenaBridge.exe')
$running = Start-Process -FilePath (Join-Path $inst9 'ArenaBridge.exe') -PassThru
Start-Sleep -Milliseconds 1500
try {
    $run = Invoke-Updater -Mode 'install' -InstallDir $inst9 -ManifestPath $manifestNew -Case 's9' -Extra @('-WaitForProcessId', [string]$running.Id, '-WaitTimeoutSeconds', '5')
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
    $run = Invoke-Updater -Mode 'install' -InstallDir $inst10 -ManifestPath $manifestNew -Case 's10' -Extra @('-WaitForProcessId', '0', '-StartAfterUpdate', '-TestFault', 'after-replace')
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

# ------------------------------------------------------------ Szenario 11: falsche Dateiversion im Artefakt
$inst11 = New-Install 's11' $exeInstalledSource
# Manifest sagt 7.8.1, geliefert wird die 7.8.0-Datei unter dem 7.8.1-Namen:
# Name, URL, Groesse und SHA-256 stimmen, nur die eingebaute Version passt nicht.
$manifestWrongVersion = New-Manifest 'wrongversion' $newVersion $urlInstalled $shaInstalled $sizeInstalled 14
$run = Invoke-Updater -Mode 'install' -InstallDir $inst11 -ManifestPath $manifestWrongVersion -Case 's11' -Extra @('-WaitForProcessId', '0')
Assert-Check 'S11 falsche Dateiversion: Exit ungleich 0' ($run.ExitCode -ne 0)
Assert-Check 'S11 falsche Dateiversion: EXE unveraendert' ((Get-FileSha (Join-Path $inst11 'ArenaBridge.exe')) -eq $shaInstalled)
$log11 = ''
if (Test-Path -LiteralPath $run.LogPath -PathType Leaf) { $log11 = Get-Content -LiteralPath $run.LogPath -Raw -Encoding UTF8 }
Assert-Check 'S11 falsche Dateiversion: Protokoll nennt den Versionskonflikt' ($log11 -match 'meldet Version')

# ------------------------------------------------------------ Szenario 12: aeltere sequence wird nie installiert
$inst12 = New-Install 's12' $exeInstalledSource
$manifestSeq5 = New-Manifest 'seq5' $newVersion $urlNew $shaNew $sizeNew 5
$run = Invoke-Updater -Mode 'install' -InstallDir $inst12 -ManifestPath $manifestSeq5 -Case 's12' -Extra @('-WaitForProcessId', '0')
Assert-Check 'S12 Vorbedingung: Installation mit sequence 5 gelingt' ($run.ExitCode -eq 0 -and (Get-FileSha (Join-Path $inst12 'ArenaBridge.exe')) -eq $shaNew)
$newerVersion = $versionParts[0] + '.' + $versionParts[1] + '.' + [string]([int]$versionParts[2] + 2)
$manifestStale = New-Manifest 'stale' $newerVersion $urlNew $shaNew $sizeNew 4
$run = Invoke-Updater -Mode 'check' -InstallDir $inst12 -ManifestPath $manifestStale -Case 's12b'
$result = if (Test-Path -LiteralPath $run.ResultPath) { Read-Json $run.ResultPath } else { $null }
Assert-Check 'S12 veraltetes Manifest: check meldet manifest-stale' ($null -ne $result -and $result.status -eq 'manifest-stale')
$run = Invoke-Updater -Mode 'install' -InstallDir $inst12 -ManifestPath $manifestStale -Case 's12c' -Extra @('-WaitForProcessId', '0')
Assert-Check 'S12 veraltetes Manifest: es wird nichts installiert' ($run.ExitCode -eq 0 -and (Get-FileSha (Join-Path $inst12 'ArenaBridge.exe')) -eq $shaNew)

# ------------------------------------------------------------ Szenario 13: Abbruch waehrend des Downloads
$inst13 = New-Install 's13' $exeInstalledSource
$manifestSlow = New-Manifest 'slow' $slowVersion $urlSlow $shaNew $sizeNew 15
$run = Invoke-Updater -Mode 'install' -InstallDir $inst13 -ManifestPath $manifestSlow -Case 's13' -Extra @('-WaitForProcessId', '0') -Hide
$cancelPath = Join-Path $inst13 '.arena-update\cancel.request'
$progressSeen = $false
$cancelDeadline = [DateTime]::UtcNow.AddSeconds(25)
while ([DateTime]::UtcNow -lt $cancelDeadline) {
    $progress = Read-Progress $inst13
    if ($null -ne $progress -and [string]$progress.phase -eq 'downloading') {
        $progressSeen = $true
        [IO.File]::WriteAllText($cancelPath, 'abbruch', (New-Object Text.UTF8Encoding($false)))
        break
    }
    if ($run.Process.HasExited) { break }
    Start-Sleep -Milliseconds 250
}
Assert-Check 'S13 Abbruch: Download lief und Fortschritt war sichtbar' $progressSeen
$finished13 = $run.Process.WaitForExit(60000)
Assert-Check 'S13 Abbruch: Updater endet sauber (Exit 0)' ($finished13 -and $run.Process.ExitCode -eq 0)
$progress13 = Read-Progress $inst13
Assert-Check 'S13 Abbruch: Fortschritt meldet cancelled' ($null -ne $progress13 -and $progress13.phase -eq 'cancelled')
Assert-Check 'S13 Abbruch: EXE unveraendert' ((Get-FileSha (Join-Path $inst13 'ArenaBridge.exe')) -eq $shaInstalled)

# ------------------------------------------------------------ Szenario 14: Diagnose-Modus
$inst14 = New-Install 's14' $exeInstalledSource
$run = Invoke-Updater -Mode 'doctor' -InstallDir $inst14 -ManifestPath $manifestNew -Case 's14'
$result = if (Test-Path -LiteralPath $run.ResultPath) { Read-Json $run.ResultPath } else { $null }
Assert-Check 'S14 Diagnose: Bericht mit Manifest, Version und Ordnern' `
    ($run.ExitCode -eq 0 -and $null -ne $result -and $result.manifestOk -eq $true -and $result.availableVersion -eq $newVersion -and $result.installDirectoryWriteable -eq $true)
Assert-Check 'S14 Diagnose: aendert die EXE nicht' ((Get-FileSha (Join-Path $inst14 'ArenaBridge.exe')) -eq $shaInstalled)

# ------------------------------------------------------------ Szenario 15: Fortschritt meldet den Abschluss
$progress2 = Read-Progress (Join-Path $WorkRoot 's2\install')
Assert-Check 'S15 Fortschritt: S2 endet mit phase done' ($null -ne $progress2 -and $progress2.phase -eq 'done')

# ------------------------------------------------------------ Aufraeumen und Schutzpruefung
try { Stop-Job -Job $serverJob -ErrorAction SilentlyContinue } catch {}
try { Remove-Job -Job $serverJob -Force -ErrorAction SilentlyContinue } catch {}

$channelsUnchanged = $true
foreach ($name in $channelHashesBefore.Keys) {
    if ((Get-FileSha (Join-Path $channelsDir $name)) -ne $channelHashesBefore[$name]) { $channelsUnchanged = $false }
}
Assert-Check 'Kanal-Dateien beta.json/stable.json wurden NICHT veraendert' $channelsUnchanged

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
