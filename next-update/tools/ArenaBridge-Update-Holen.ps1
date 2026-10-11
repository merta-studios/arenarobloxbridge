#requires -Version 5.1
<#
Arena Roblox Bridge - Update-Holer (einmalige Migration fuer alte Installationen)

WOFUER IST DAS DA?
  EXEs, die noch keinen eingebauten Updater haben (alles vor 7.7.0), koennen sich
  nicht selbst aktualisieren. Dieses kleine Werkzeug holt genau einmal den
  offiziellen Updater und laesst ihn die vorhandene Installation aktualisieren.

Wie es arbeitet (kurz und ehrlich):
  1. Es sucht die vorhandene ArenaBridge.exe (oder du gibst den Ordner an).
  2. Es laedt NUR von zwei festen HTTPS-Adressen auf raw.githubusercontent.com:
     den Updater und danach den Kanal-Stand.
     Es gibt keine frei waehlbare Adresse, keine Zugangsdaten, keine Umleitung
     auf fremde Hosts (jede Weiterleitung wird einzeln geprueft).
  3. Den Rest macht der offizielle Updater: Groesse, SHA-256, x64-Kopf und
     Dateiversion pruefen, die alte EXE als Backup behalten, atomar ersetzen und
     die neue Fassung starten. Schlaegt etwas fehl, bleibt die alte Fassung.
  4. Es wird NIE ein laufendes Programm beendet. Laeuft die Bridge noch, wartet
     der Updater auf ihr regulaeres Ende.

Aufruf-Beispiele:
  .\ArenaBridge-Update-Holen.ps1                       (sucht die Installation selbst)
  .\ArenaBridge-Update-Holen.ps1 -InstallDirectory "C:\ArenaBridge"
  .\ArenaBridge-Update-Holen.ps1 -DryRun               (nur pruefen, nichts installieren)
  .\ArenaBridge-Update-Holen.ps1 -Channel beta         (Vorabkanal, falls freigegeben)

Diese Datei ist reines ASCII, damit Windows PowerShell 5.1 sie unabhaengig von
der Codierung sicher liest.
#>
[CmdletBinding()]
param(
    [string]$InstallDirectory = '',
    [ValidateSet('stable', 'beta')][string]$Channel = 'stable',
    [switch]$DryRun,
    [switch]$NoPause
)

$ErrorActionPreference = 'Stop'
$script:UpdaterUrl = 'https://raw.githubusercontent.com/merta-studios/arenarobloxbridge/main/next-update/update-system/updater/Update-Bridge.ps1'
$script:ApprovedHosts = @('raw.githubusercontent.com', 'objects.githubusercontent.com', 'release-assets.githubusercontent.com')
$script:WorkDir = Join-Path $env:TEMP ('arena-update-holen-' + [Guid]::NewGuid().ToString('N').Substring(0, 8))
$script:Failed = $false

function Write-Step([string]$Text) { Write-Host ('  ' + $Text) }
function Write-Head([string]$Text) {
    Write-Host ''
    Write-Host ('=== ' + $Text) -ForegroundColor Cyan
}

function Get-FixedDownload([string]$Url, [string]$Destination, [long]$MaxBytes) {
    # Download ausschliesslich per HTTPS auf genehmigte GitHub-Hosts, mit eigener
    # Weiterleitungspruefung und Groessenlimit.
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    $uri = [Uri]$Url
    if ($uri.Scheme -ne 'https' -or -not $script:ApprovedHosts.Contains($uri.Host.ToLowerInvariant())) {
        throw 'Adresse ist nicht erlaubt.'
    }
    $redirects = 0
    while ($true) {
        $request = [Net.HttpWebRequest]::Create($uri)
        $request.Method = 'GET'
        $request.AllowAutoRedirect = $false
        $request.Timeout = 30000
        $request.ReadWriteTimeout = 30000
        $request.UserAgent = 'ArenaRobloxBridge-Migration/1.0'
        $response = $null
        try { $response = [Net.HttpWebResponse]$request.GetResponse() }
        catch [System.Net.WebException] {
            if ($null -ne $_.Exception.Response) { $response = [Net.HttpWebResponse]$_.Exception.Response }
            else { throw ('Keine Verbindung: ' + $_.Exception.Message) }
        }
        $status = [int]$response.StatusCode
        if ($status -in @(301, 302, 303, 307, 308)) {
            if ($redirects -ge 3) { throw 'Zu viele Weiterleitungen.' }
            $location = [string]$response.Headers['Location']
            $next = $null
            if (-not [Uri]::TryCreate($uri, $location, [ref]$next)) { throw 'Ungueltige Weiterleitung.' }
            if ($next.Scheme -ne 'https' -or -not $script:ApprovedHosts.Contains($next.Host.ToLowerInvariant())) {
                throw 'Weiterleitung auf einen nicht genehmigten Host wurde verweigert.'
            }
            $uri = $next
            $redirects++
            continue
        }
        if ($status -eq 404) { throw 'Die Datei liegt auf GitHub noch nicht (HTTP 404).' }
        if ($status -ne 200) { throw ('Server antwortete mit HTTP ' + [string]$status + '.') }
        $length = [long]$response.ContentLength
        if ($length -gt $MaxBytes) { throw 'Datei ueberschreitet das erlaubte Limit.' }
        $stream = $response.GetResponseStream()
        $out = [IO.File]::Open($Destination, [IO.FileMode]::Create, [IO.FileAccess]::Write, [IO.FileShare]::None)
        try {
            $buffer = [byte[]]::new(65536)
            $total = [long]0
            while ($true) {
                $read = $stream.Read($buffer, 0, $buffer.Length)
                if ($read -le 0) { break }
                $total += $read
                if ($total -gt $MaxBytes) { throw 'Datei ueberschreitet das erlaubte Limit.' }
                $out.Write($buffer, 0, $read)
            }
        } finally {
            $out.Dispose()
            if ($null -ne $stream) { $stream.Dispose() }
            $response.Close()
        }
        if ($total -le 0) { throw 'Leerer Download.' }
        return $total
    }
}

function Get-InstalledVersion([string]$ExePath) {
    try { return [string]([Diagnostics.FileVersionInfo]::GetVersionInfo($ExePath).FileVersion) } catch { return '' }
}

function Find-InstallDirectory {
    $candidates = New-Object System.Collections.Generic.List[string]
    foreach ($process in @(Get-Process -Name 'ArenaBridge' -ErrorAction SilentlyContinue)) {
        try {
            $path = [string]$process.Path
            if (-not [string]::IsNullOrWhiteSpace($path)) { $candidates.Add((Split-Path -Parent $path)) }
        } catch { }
    }
    foreach ($root in @($env:LOCALAPPDATA, (Join-Path $env:USERPROFILE 'Desktop'), (Join-Path $env:USERPROFILE 'Downloads'))) {
        if ([string]::IsNullOrWhiteSpace($root)) { continue }
        $direct = Join-Path $root 'ArenaBridge.exe'
        if (Test-Path -LiteralPath $direct -PathType Leaf) { $candidates.Add($root) }
        try {
            foreach ($child in @(Get-ChildItem -LiteralPath $root -Directory -ErrorAction SilentlyContinue)) {
                if (Test-Path -LiteralPath (Join-Path $child.FullName 'ArenaBridge.exe') -PathType Leaf) {
                    $candidates.Add($child.FullName)
                }
            }
        } catch { }
    }
    $candidates.Add($PSScriptRoot)
    $candidates.Add((Split-Path -Parent $PSScriptRoot))
    $best = ''
    $bestVersion = ''
    foreach ($candidate in ($candidates | Select-Object -Unique)) {
        $exe = Join-Path $candidate 'ArenaBridge.exe'
        if (-not (Test-Path -LiteralPath $exe -PathType Leaf)) { continue }
        $version = Get-InstalledVersion $exe
        if ([string]::IsNullOrWhiteSpace($best) -or
            ([version]$version -gt [version]$bestVersion)) {
            $best = $candidate
            $bestVersion = $version
        }
    }
    return $best
}

Write-Host ''
Write-Host 'ARENA ROBLOX BRIDGE - UPDATE HOLEN' -ForegroundColor Green
Write-Host 'Dieses Werkzeug holt den offiziellen Updater und aktualisiert deine vorhandene'
Write-Host 'Installation. Es beendet kein laufendes Programm und laedt nur von GitHub.'

$install = $InstallDirectory
if (-not [string]::IsNullOrWhiteSpace($install)) {
    $install = [IO.Path]::GetFullPath($install.Trim('"').Trim())
    if (-not (Test-Path -LiteralPath (Join-Path $install 'ArenaBridge.exe') -PathType Leaf)) {
        Write-Host ('FEHLER: In ' + $install + ' liegt keine ArenaBridge.exe.') -ForegroundColor Red
        if (-not $NoPause) { [void](Read-Host 'Enter zum Beenden') }
        exit 2
    }
} else {
    $install = Find-InstallDirectory
    if ([string]::IsNullOrWhiteSpace($install)) {
        Write-Host 'Ich habe keine Installation gefunden. Bitte den Ordner mit der ArenaBridge.exe angeben.'
        Write-Host 'Tipp: Ordner per Drag and Drop in dieses Fenster ziehen.'
        $install = Read-Host 'Ordner'
        $install = [IO.Path]::GetFullPath($install.Trim('"').Trim())
    }
}

$exePath = Join-Path $install 'ArenaBridge.exe'
if (-not (Test-Path -LiteralPath $exePath -PathType Leaf)) {
    Write-Host ('FEHLER: ' + $exePath + ' fehlt.') -ForegroundColor Red
    if (-not $NoPause) { [void](Read-Host 'Enter zum Beenden') }
    exit 2
}

Write-Head '1) Vorhandene Installation'
Write-Step ('Ordner:   ' + $install)
Write-Step ('Version:  ' + (Get-InstalledVersion $exePath))
Write-Step ('Datei:    ' + $exePath)
if (@(Get-Process -Name 'ArenaBridge' -ErrorAction SilentlyContinue).Count -gt 0) {
    Write-Step 'Hinweis: Die Bridge laeuft gerade. Der Updater wartet auf ihr regulaeres Ende.'
}

New-Item -ItemType Directory -Path $script:WorkDir -Force | Out-Null
$updaterPath = Join-Path $script:WorkDir 'Update-Bridge.ps1'
$logPath = Join-Path $script:WorkDir 'update-holen.log'

Write-Head '2) Offiziellen Updater laden (nur HTTPS auf GitHub)'
try {
    $bytes = Get-FixedDownload $script:UpdaterUrl $updaterPath 1048576
    $hash = (Get-FileHash -LiteralPath $updaterPath -Algorithm SHA256).Hash.ToLowerInvariant()
    Write-Step ('Geladen:  ' + [string]$bytes + ' Bytes')
    Write-Step ('SHA-256:  ' + $hash)
    Write-Step ('Quelle:   ' + $script:UpdaterUrl)
} catch {
    Write-Host ('FEHLER beim Laden des Updaters: ' + $_.Exception.Message) -ForegroundColor Red
    $script:Failed = $true
}

if (-not $script:Failed) {
    $mode = 'install'
    if ($DryRun) { $mode = 'check' }
    Write-Head ('3) Updater starten (' + $mode + ', Kanal ' + $Channel + ')')
    $resultPath = Join-Path $script:WorkDir 'result.json'
    $arguments = @(
        '-NoLogo', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass',
        '-File', ('"' + $updaterPath + '"'),
        '-Mode', $mode,
        '-Channel', $Channel,
        '-InstallDirectory', ('"' + $install + '"'),
        '-LogPath', ('"' + $logPath + '"')
    )
    if (-not $DryRun) { $arguments += @('-StartAfterUpdate') }
    $powershell = Join-Path $env:WINDIR 'System32\WindowsPowerShell\v1.0\powershell.exe'
    if (-not (Test-Path -LiteralPath $powershell -PathType Leaf)) { $powershell = 'powershell.exe' }
    if ($DryRun) {
        $process = Start-Process -FilePath $powershell -ArgumentList (($arguments + @('-ResultPath', ('"' + $resultPath + '"'))) -join ' ') -Wait -PassThru -WindowStyle Hidden
    } else {
        $process = Start-Process -FilePath $powershell -ArgumentList ($arguments -join ' ') -Wait -PassThru -WindowStyle Hidden
    }
    Write-Step ('Helfer-Exitcode: ' + [string]$process.ExitCode)

    Write-Head '4) Ergebnis'
    if ($DryRun -and (Test-Path -LiteralPath $resultPath -PathType Leaf)) {
        try {
            $record = Get-Content -LiteralPath $resultPath -Raw -Encoding UTF8 | ConvertFrom-Json
            Write-Step ('Status:      ' + [string]$record.status)
            Write-Step ('Installiert: ' + [string]$record.installedVersion)
            Write-Step ('Verfuegbar:  ' + [string]$record.availableVersion)
            if ([string]$record.status -eq 'disabled') {
                Write-Step 'Es ist gerade keine neue Version freigegeben. Es wurde nichts geaendert.'
            }
        } catch { Write-Step 'Ergebnisdatei war nicht lesbar.' }
    }
    if ($process.ExitCode -ne 0) {
        Write-Host 'Das Update wurde NICHT ausgefuehrt. Die bisherige Installation ist unveraendert.' -ForegroundColor Yellow
    } elseif (-not $DryRun) {
        Write-Host 'Fertig. Die neue Fassung wurde geprueft und gestartet.' -ForegroundColor Green
    }
    Write-Step ('Protokoll: ' + $logPath)
}

if ($script:Failed) {
    Write-Host ''
    Write-Host 'ABBRUCH: Es wurde nichts installiert.' -ForegroundColor Red
}
if (-not $NoPause) { [void](Read-Host 'Enter zum Beenden') }
if ($script:Failed) { exit 1 }
exit 0
