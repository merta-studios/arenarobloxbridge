#requires -Version 5.1
<#
Arena Roblox Bridge - Selbst-Update-Helfer (Updater 1.1.0)

Dieser Helfer wird vom Builder in ArenaBridge.exe eingebettet (als Base64 mit
fest eingetragener SHA-256) und von dort in %LOCALAPPDATA% extrahiert. Die
EXE haengt NICHT von einer separat veroeffentlichten Updater-Datei ab.

Modi:
  check    Laedt das Kanal-Manifest, prueft es und schreibt ein JSON-Ergebnis.
           Veraendert keine Programmdateien.
  install  Wartet auf das REGULAERE Beenden der laufenden EXE, laedt die neue
           Datei in einen Staging-Ordner, prueft Groesse, SHA-256 und PE-Kopf,
           ersetzt die EXE atomar mit Backup, schreibt den Status und startet
           die Bridge kontrolliert neu. Schlaegt ein Schritt fehl, wird die
           alte Fassung wiederhergestellt.

Harte Regeln (durch update-system/PROTECTED.md und einen Offline-Test gesichert):
  - Keine Prozessbeendigung durch dieses Skript: eine laufende Bridge wird
    nie gewaltsam beendet, es gibt keinen Beende- oder Kill-Befehl.
  - Download nur per HTTPS auf genehmigten GitHub-Hosts, feste Repository-URL,
    keine frei waehlbaren URLs, keine Zugangsdaten.
  - Downgrade-Schutz gegen lokalen Stand (update-state.json und Dateiversion).
  - Test-Modus (-TestFixtureMode) ist nur mit einem Test-Manifest moeglich;
    normale Nutzerstarts uebergeben diesen Schalter nie.

Diese Datei ist ASCII-only, damit PowerShell 5.1 sie unabhaengig von der
Codierung sicher liest.
#>
[CmdletBinding()]
param(
    [ValidateSet('check', 'install')][string]$Mode = 'check',
    [Parameter(Mandatory = $true)][ValidateSet('beta', 'stable')][string]$Channel,
    [string]$InstallDirectory = '',
    [string]$TargetExeName = 'ArenaBridge.exe',
    [string]$ResultPath = '',
    [string]$LogPath = '',
    [int]$WaitForProcessId = 0,
    [int]$WaitTimeoutSeconds = 180,
    [switch]$StartAfterUpdate,
    [switch]$TestFixtureMode,
    [string]$ManifestPath = '',
    [ValidateSet('', 'after-replace')][string]$TestFault = ''
)

$ErrorActionPreference = 'Stop'
$script:UpdaterVersion = '1.1.0'
$script:MaxManifestBytes = 1048576
$script:MaxArtifactBytes = 67108864
$script:MinArtifactBytes = 1024
$script:MaxRedirects = 3
$script:LogMaxBytes = 1048576
$script:CanonicalManifestBase = 'https://raw.githubusercontent.com/merta-studios/arenarobloxbridge/main/next-update/update-system/channels/'
$script:CanonicalArtifactUrl = 'https://raw.githubusercontent.com/merta-studios/arenarobloxbridge/main/next-update/release/ArenaBridge.exe'
$script:ApprovedDownloadHosts = @('raw.githubusercontent.com')
$script:ApprovedRedirectHosts = @('raw.githubusercontent.com', 'objects.githubusercontent.com', 'release-assets.githubusercontent.com')
$script:ActiveLogPath = $LogPath
$script:TestFixtureActive = [bool]$TestFixtureMode

function Write-UpdateLog([string]$Text) {
    $line = ('{0:o} [updater {1}] {2}' -f [DateTime]::UtcNow, $script:UpdaterVersion, $Text)
    Write-Host $line
    try {
        if (-not [string]::IsNullOrWhiteSpace($script:ActiveLogPath)) {
            $logDir = Split-Path -Parent $script:ActiveLogPath
            if (-not (Test-Path -LiteralPath $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
            if ((Test-Path -LiteralPath $script:ActiveLogPath -PathType Leaf) -and ((Get-Item -LiteralPath $script:ActiveLogPath).Length -gt $script:LogMaxBytes)) {
                Move-Item -LiteralPath $script:ActiveLogPath -Destination ($script:ActiveLogPath + '.old') -Force
            }
            [IO.File]::AppendAllText($script:ActiveLogPath, $line + [Environment]::NewLine, [Text.UTF8Encoding]::new($false))
        }
    } catch {}
}

function Get-JsonProperty($Object, [string]$Name) {
    if ($null -eq $Object) { return $null }
    $property = $Object.PSObject.Properties[$Name]
    if ($null -eq $property) { return $null }
    return $property.Value
}

function Get-Sha256Hex([string]$Path) {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Get-Sha256HexBytes([byte[]]$Bytes) {
    $sha = [Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($sha.ComputeHash($Bytes)).Replace('-', '').ToLowerInvariant()) }
    finally { $sha.Dispose() }
}

function Get-Stamp { return (Get-Date).ToString('yyyyMMdd-HHmmss-fff') }

function Write-TextAtomic([string]$Path, [string]$Text) {
    $dir = Split-Path -Parent $Path
    if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    $temp = $Path + '.' + [Guid]::NewGuid().ToString('N') + '.tmp'
    [IO.File]::WriteAllText($temp, $Text, [Text.UTF8Encoding]::new($false))
    if (Test-Path -LiteralPath $Path -PathType Leaf) {
        [IO.File]::Replace($temp, $Path, $null, $true)
    } else {
        [IO.File]::Move($temp, $Path)
    }
}

function Test-UpdateVersion([string]$Value) {
    return ($Value -cmatch '^\d+\.\d+\.\d+(?:-[0-9A-Za-z]+(?:[.-][0-9A-Za-z]+)*)?$')
}

function Convert-UpdateVersion([string]$Value) {
    if (-not (Test-UpdateVersion $Value)) { throw ('Ungueltige Versionsnummer: ' + $Value) }
    $parts = $Value.Split('-', 2)
    $core = @($parts[0].Split('.') | ForEach-Object { [int64]$_ })
    $pre = @()
    if ($parts.Count -gt 1) { $pre = @($parts[1] -split '[.-]') }
    return [pscustomobject]@{ Core = $core; PreRelease = $pre; Original = $Value }
}

function Compare-UpdateVersion([string]$Left, [string]$Right) {
    $a = Convert-UpdateVersion $Left
    $b = Convert-UpdateVersion $Right
    for ($i = 0; $i -lt 3; $i++) {
        if ($a.Core[$i] -gt $b.Core[$i]) { return 1 }
        if ($a.Core[$i] -lt $b.Core[$i]) { return -1 }
    }
    if ($a.PreRelease.Count -eq 0 -and $b.PreRelease.Count -eq 0) { return 0 }
    if ($a.PreRelease.Count -eq 0) { return 1 }
    if ($b.PreRelease.Count -eq 0) { return -1 }
    $limit = [Math]::Max($a.PreRelease.Count, $b.PreRelease.Count)
    for ($i = 0; $i -lt $limit; $i++) {
        if ($i -ge $a.PreRelease.Count) { return -1 }
        if ($i -ge $b.PreRelease.Count) { return 1 }
        $leftId = [string]$a.PreRelease[$i]
        $rightId = [string]$b.PreRelease[$i]
        $leftNumber = [int64]0
        $rightNumber = [int64]0
        $leftNumeric = [int64]::TryParse($leftId, [ref]$leftNumber)
        $rightNumeric = [int64]::TryParse($rightId, [ref]$rightNumber)
        if ($leftNumeric -and $rightNumeric) {
            if ($leftNumber -gt $rightNumber) { return 1 }
            if ($leftNumber -lt $rightNumber) { return -1 }
        } elseif ($leftNumeric) { return -1 }
        elseif ($rightNumeric) { return 1 }
        else {
            $cmp = [string]::Compare($leftId, $rightId, [StringComparison]::OrdinalIgnoreCase)
            if ($cmp -gt 0) { return 1 }
            if ($cmp -lt 0) { return -1 }
        }
    }
    return 0
}

function Get-FileVersionCore([string]$Path) {
    try {
        $raw = [string]([Diagnostics.FileVersionInfo]::GetVersionInfo($Path).FileVersion)
    } catch { return '' }
    $match = [regex]::Match($raw, '^(\d+)\.(\d+)\.(\d+)')
    if (-not $match.Success) { return '' }
    return ($match.Groups[1].Value + '.' + $match.Groups[2].Value + '.' + $match.Groups[3].Value)
}

function Test-AllowedUri([Uri]$Uri, [bool]$IsRedirect) {
    if ($null -eq $Uri) { return $false }
    if (-not [string]::IsNullOrEmpty($Uri.UserInfo) -or -not [string]::IsNullOrEmpty($Uri.Fragment)) { return $false }
    if ($script:TestFixtureActive) {
        # Test-Modus: ausschliesslich lokaler Fixture-Server auf 127.0.0.1.
        return ($Uri.Scheme -eq 'http' -and $Uri.Host -eq '127.0.0.1' -and $Uri.Port -ge 1024)
    }
    if ($Uri.Scheme -ne 'https' -or -not $Uri.IsDefaultPort) { return $false }
    $hostName = $Uri.Host.ToLowerInvariant()
    if ($IsRedirect) { return ($script:ApprovedRedirectHosts -contains $hostName) }
    return ($script:ApprovedDownloadHosts -contains $hostName)
}

function Get-ApprovedDownload {
    param(
        [Parameter(Mandatory = $true)][Uri]$Uri,
        [Parameter(Mandatory = $true)][long]$MaxBytes,
        [long]$ExpectedBytes = 0,
        [string]$DestinationPath = '',
        [int]$TimeoutSeconds = 180
    )
    if ($MaxBytes -le 0) { throw 'Interne Groessenbegrenzung ist ungueltig.' }
    if ($ExpectedBytes -lt 0 -or $ExpectedBytes -gt $MaxBytes) { throw 'Erwartete Groesse liegt ausserhalb des Limits.' }
    if (-not (Test-AllowedUri $Uri $false)) { throw 'Download-URL ist nicht erlaubt (nur HTTPS auf genehmigten GitHub-Hosts).' }
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
    $requestTimeoutMs = [int][Math]::Min(30000, $TimeoutSeconds * 1000)
    $currentUri = $Uri
    $redirectCount = 0
    while ($true) {
        if ([DateTime]::UtcNow -gt $deadline) { throw 'Zeitlimit fuer den Download ueberschritten.' }
        $response = $null
        $inStream = $null
        $outStream = $null
        $completed = $false
        try {
            $request = [Net.HttpWebRequest]::Create($currentUri)
            $request.Method = 'GET'
            $request.AllowAutoRedirect = $false
            $request.AutomaticDecompression = [Net.DecompressionMethods]::None
            $request.Timeout = $requestTimeoutMs
            $request.ReadWriteTimeout = $requestTimeoutMs
            $request.KeepAlive = $false
            $request.UserAgent = ('ArenaRobloxBridge-Updater/' + $script:UpdaterVersion)
            try {
                $response = [Net.HttpWebResponse]$request.GetResponse()
            } catch [System.Net.WebException] {
                if ($null -ne $_.Exception.Response) { $response = [Net.HttpWebResponse]$_.Exception.Response }
                else { throw }
            }
            if ($null -eq $response) { throw 'Keine HTTP-Antwort vom Server.' }
            $status = [int]$response.StatusCode
            if ($status -in @(301, 302, 303, 307, 308)) {
                if ($redirectCount -ge $script:MaxRedirects) { throw 'Zu viele Weiterleitungen.' }
                $location = [string]$response.Headers['Location']
                if ([string]::IsNullOrWhiteSpace($location)) { throw 'Weiterleitung ohne Ziel.' }
                $nextUri = $null
                if (-not [Uri]::TryCreate($currentUri, $location, [ref]$nextUri)) { throw 'Ungueltige Weiterleitung.' }
                if (-not (Test-AllowedUri $nextUri $true)) { throw 'Weiterleitung auf einen nicht genehmigten Host wurde verweigert.' }
                $currentUri = $nextUri
                $redirectCount++
                continue
            }
            if ($status -lt 200 -or $status -ge 300) { throw ('Server antwortete mit HTTP ' + [string]$status + '.') }

            $declaredLength = [long]$response.ContentLength
            if ($declaredLength -gt $MaxBytes) { throw 'Content-Length ueberschreitet das Groessenlimit.' }
            if ($declaredLength -eq 0) { throw 'Leerer Download.' }
            if ($ExpectedBytes -gt 0 -and $declaredLength -ge 0 -and $declaredLength -ne $ExpectedBytes) {
                throw 'Content-Length passt nicht zur Groesse im Manifest.'
            }
            if ([string]::IsNullOrWhiteSpace($DestinationPath)) {
                $outStream = New-Object IO.MemoryStream
            } else {
                $outStream = [IO.File]::Open($DestinationPath, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
            }
            $inStream = $response.GetResponseStream()
            if ($null -eq $inStream) { throw 'Antwort enthaelt keinen lesbaren Inhalt.' }
            $buffer = [byte[]]::new(65536)
            $received = [long]0
            while ($true) {
                $readCount = $inStream.Read($buffer, 0, $buffer.Length)
                if ($readCount -le 0) { break }
                if ([DateTime]::UtcNow -gt $deadline) { throw 'Zeitlimit fuer den Download ueberschritten.' }
                $received += [long]$readCount
                if ($received -gt $MaxBytes) { throw 'Der Download ueberschreitet das Groessenlimit.' }
                if ($ExpectedBytes -gt 0 -and $received -gt $ExpectedBytes) { throw 'Der Download ist groesser als im Manifest angegeben.' }
                $outStream.Write($buffer, 0, $readCount)
            }
            if ($received -le 0) { throw 'Leerer Download.' }
            if ($declaredLength -ge 0 -and $received -ne $declaredLength) { throw 'Download unvollstaendig (Content-Length stimmt nicht).' }
            if ($ExpectedBytes -gt 0 -and $received -ne $ExpectedBytes) { throw 'Groesse passt nicht zum Manifest.' }
            $outStream.Flush()
            $completed = $true
            if ([string]::IsNullOrWhiteSpace($DestinationPath)) {
                return [pscustomobject]@{ Bytes = $outStream.ToArray(); SizeBytes = $received; Uri = $currentUri.AbsoluteUri }
            }
            return [pscustomobject]@{ Path = $DestinationPath; SizeBytes = $received; Uri = $currentUri.AbsoluteUri }
        } finally {
            if ($null -ne $inStream) { $inStream.Dispose() }
            if ($null -ne $outStream) { $outStream.Dispose() }
            if ($null -ne $response) { $response.Close() }
            if (-not $completed -and -not [string]::IsNullOrWhiteSpace($DestinationPath) -and (Test-Path -LiteralPath $DestinationPath -PathType Leaf)) {
                Remove-Item -LiteralPath $DestinationPath -Force -ErrorAction SilentlyContinue
            }
        }
    }
}

function Get-ChannelManifest {
    if ($script:TestFixtureActive) {
        if ([string]::IsNullOrWhiteSpace($ManifestPath)) { throw 'Der Test-Modus braucht -ManifestPath.' }
        if (-not (Test-Path -LiteralPath $ManifestPath -PathType Leaf)) { throw 'Test-Manifest nicht gefunden.' }
        if ((Get-Item -LiteralPath $ManifestPath).Length -gt $script:MaxManifestBytes) { throw 'Manifest ueberschreitet das Groessenlimit.' }
        $raw = [IO.File]::ReadAllText($ManifestPath, [Text.Encoding]::UTF8)
    } else {
        if (-not [string]::IsNullOrWhiteSpace($ManifestPath)) { throw '-ManifestPath ist nur im Test-Modus erlaubt.' }
        $expectedUrl = $script:CanonicalManifestBase + $Channel + '.json'
        $download = Get-ApprovedDownload -Uri ([Uri]$expectedUrl) -MaxBytes $script:MaxManifestBytes -TimeoutSeconds 30
        $raw = [Text.Encoding]::UTF8.GetString([byte[]]$download.Bytes)
    }
    if ($raw.Length -gt 0 -and [int][char]$raw[0] -eq 0xFEFF) { $raw = $raw.Substring(1) }
    try {
        return ($raw | ConvertFrom-Json -ErrorAction Stop)
    } catch {
        throw 'Das Kanal-Manifest ist kein gueltiges JSON.'
    }
}

function Test-ChannelManifest($Manifest) {
    $schemaText = [string](Get-JsonProperty $Manifest 'schemaVersion')
    if ($schemaText -cne '1') { throw 'Nicht unterstuetzte schemaVersion im Manifest.' }
    $channelText = [string](Get-JsonProperty $Manifest 'channel')
    if ($channelText -cne $Channel) { throw ('Manifest-Kanal "' + $channelText + '" passt nicht zum angeforderten Kanal "' + $Channel + '".') }
    $enabledValue = Get-JsonProperty $Manifest 'enabled'
    if (-not ($enabledValue -is [bool])) { throw 'enabled muss true oder false sein.' }
    $fixtureValue = Get-JsonProperty $Manifest 'testFixture'
    $isFixture = $false
    if ($null -ne $fixtureValue) {
        if (-not ($fixtureValue -is [bool])) { throw 'testFixture muss true oder false sein.' }
        $isFixture = [bool]$fixtureValue
    }
    if ($isFixture -and -not $script:TestFixtureActive) { throw 'Ein Test-Manifest wird im Nutzerbetrieb nie akzeptiert.' }
    if ($script:TestFixtureActive -and -not $isFixture) { throw 'Im Test-Modus ist nur ein Test-Manifest mit testFixture=true erlaubt.' }

    $notes = @()
    $rawNotes = Get-JsonProperty $Manifest 'notes'
    if ($null -ne $rawNotes) { $notes = @($rawNotes | Where-Object { -not [string]::IsNullOrWhiteSpace([string]$_) } | ForEach-Object { [string]$_ }) }

    if (-not $enabledValue) {
        return [pscustomobject]@{ Enabled = $false; Channel = $channelText; Version = ''; Sha256 = ''; SizeBytes = [long]0; Url = ''; Notes = $notes }
    }

    $versionText = [string](Get-JsonProperty $Manifest 'version')
    if (-not (Test-UpdateVersion $versionText)) { throw 'Aktiviertes Manifest braucht eine gueltige Version (x.y.z oder x.y.z-beta.n).' }
    if ($channelText -ceq 'stable' -and $versionText.Contains('-')) { throw 'Der Stable-Kanal veroeffentlicht keine Vorabversionen.' }
    $publishedText = [string](Get-JsonProperty $Manifest 'publishedAtUtc')
    $publishedAt = [DateTime]::MinValue
    if (-not [DateTime]::TryParse($publishedText, [Globalization.CultureInfo]::InvariantCulture, [Globalization.DateTimeStyles]::AssumeUniversal, [ref]$publishedAt)) {
        throw 'publishedAtUtc fehlt oder ist kein gueltiges Datum.'
    }
    $minimumUpdater = [string](Get-JsonProperty $Manifest 'minimumUpdaterVersion')
    if (-not [string]::IsNullOrWhiteSpace($minimumUpdater)) {
        if (-not (Test-UpdateVersion $minimumUpdater)) { throw 'minimumUpdaterVersion ist ungueltig.' }
        if ((Compare-UpdateVersion $script:UpdaterVersion $minimumUpdater) -lt 0) {
            throw ('Dieser Updater ist zu alt (benoetigt ' + $minimumUpdater + ', installiert ' + $script:UpdaterVersion + ').')
        }
    }

    $artifact = Get-JsonProperty $Manifest 'artifact'
    if ($null -eq $artifact) { throw 'Manifest ohne artifact.' }
    if ([string](Get-JsonProperty $artifact 'fileName') -cne 'ArenaBridge.exe') { throw 'artifact.fileName muss exakt ArenaBridge.exe sein.' }
    $sha256 = ([string](Get-JsonProperty $artifact 'sha256')).ToLowerInvariant()
    if ($sha256 -cnotmatch '^[0-9a-f]{64}$') { throw 'artifact.sha256 muss 64 hexadezimale Zeichen enthalten.' }
    $sizeText = [string](Get-JsonProperty $artifact 'sizeBytes')
    if ($sizeText -cnotmatch '^\d{1,12}$') { throw 'artifact.sizeBytes muss eine ganze Zahl sein.' }
    $sizeBytes = [long]$sizeText
    if ($sizeBytes -lt $script:MinArtifactBytes -or $sizeBytes -gt $script:MaxArtifactBytes) {
        throw ('artifact.sizeBytes muss zwischen ' + $script:MinArtifactBytes + ' und ' + $script:MaxArtifactBytes + ' Bytes liegen.')
    }
    $urlText = [string](Get-JsonProperty $artifact 'url')
    if ($script:TestFixtureActive) {
        if ($urlText -cnotmatch '^http://127\.0\.0\.1:\d{4,5}/ArenaBridge\.exe$') { throw 'Test-Artefakt-URL muss auf 127.0.0.1 zeigen.' }
    } elseif ($urlText -cne $script:CanonicalArtifactUrl) {
        throw 'artifact.url ist nicht die genehmigte Repository-Datei next-update/release/ArenaBridge.exe.'
    }
    $artifactUri = $null
    if (-not [Uri]::TryCreate($urlText, [UriKind]::Absolute, [ref]$artifactUri) -or -not (Test-AllowedUri $artifactUri $false)) {
        throw 'artifact.url ist fuer den Download nicht erlaubt.'
    }
    return [pscustomobject]@{
        Enabled = $true; Channel = $channelText; Version = $versionText; Sha256 = $sha256
        SizeBytes = $sizeBytes; Url = $urlText; Notes = $notes; Mandatory = [bool](Get-JsonProperty $Manifest 'mandatory')
    }
}

function Get-InstalledState([string]$TargetPath, [string]$StatePath) {
    $stateVersion = ''
    $stateSha = ''
    $stateChannel = ''
    if (Test-Path -LiteralPath $StatePath -PathType Leaf) {
        try {
            $state = Get-Content -LiteralPath $StatePath -Raw -Encoding UTF8 | ConvertFrom-Json -ErrorAction Stop
        } catch {
            throw 'Der lokale Update-Status ist unlesbar. Es wird ohne verlaessliche Versionshistorie nicht aktualisiert.'
        }
        if ([string](Get-JsonProperty $state 'schemaVersion') -cne '1') { throw 'Lokaler Update-Status hat eine unbekannte schemaVersion.' }
        $stateChannel = [string](Get-JsonProperty $state 'channel')
        if ($stateChannel -cne 'beta' -and $stateChannel -cne 'stable') { throw 'Lokaler Update-Status hat einen ungueltigen Kanal.' }
        $stateVersion = [string](Get-JsonProperty $state 'version')
        if (-not (Test-UpdateVersion $stateVersion)) { throw 'Lokaler Update-Status hat eine ungueltige Version.' }
        $stateSha = ([string](Get-JsonProperty $state 'sha256')).ToLowerInvariant()
    }
    $fileVersion = ''
    if (Test-Path -LiteralPath $TargetPath -PathType Leaf) { $fileVersion = Get-FileVersionCore $TargetPath }
    $installed = $stateVersion
    if ($fileVersion -ne '') {
        if ($installed -eq '' -or (Compare-UpdateVersion $fileVersion $installed) -gt 0) { $installed = $fileVersion }
    }
    return [pscustomobject]@{
        Version = $installed; StateVersion = $stateVersion; StateSha256 = $stateSha
        StateChannel = $stateChannel; FileVersion = $fileVersion
        TargetExists = (Test-Path -LiteralPath $TargetPath -PathType Leaf)
    }
}

function Get-UpdateDecision($Manifest, $Installed) {
    if (-not $Manifest.Enabled) { return 'disabled' }
    if ($Installed.Version -eq '') { return 'error' }
    $order = Compare-UpdateVersion $Manifest.Version $Installed.Version
    if ($order -lt 0) { return 'downgrade-refused' }
    if ($order -eq 0) {
        if ($Installed.StateSha256 -eq '' -or $Installed.StateSha256 -ceq $Manifest.Sha256) { return 'up-to-date' }
        return 'version-conflict'
    }
    return 'update-available'
}

function Test-WindowsX64Executable([string]$Path) {
    $bytes = [byte[]]::new(4096)
    $stream = [IO.File]::OpenRead($Path)
    try { $read = $stream.Read($bytes, 0, $bytes.Length) } finally { $stream.Dispose() }
    if ($read -lt 256) { return $false }
    if ($bytes[0] -ne 0x4D -or $bytes[1] -ne 0x5A) { return $false }
    $peOffset = [BitConverter]::ToInt32($bytes, 0x3C)
    if ($peOffset -lt 0 -or ($peOffset + 6) -gt $read) { return $false }
    if ($bytes[$peOffset] -ne 0x50 -or $bytes[$peOffset + 1] -ne 0x45 -or $bytes[$peOffset + 2] -ne 0 -or $bytes[$peOffset + 3] -ne 0) { return $false }
    $machine = [BitConverter]::ToUInt16($bytes, $peOffset + 4)
    return ($machine -eq 0x8664)
}

function Get-RunningTargetInstances([string]$TargetPath) {
    $normalizedTarget = [IO.Path]::GetFullPath($TargetPath)
    $found = New-Object System.Collections.ArrayList
    foreach ($process in @(Get-Process -Name 'ArenaBridge' -ErrorAction SilentlyContinue)) {
        $processPath = ''
        try { $processPath = [IO.Path]::GetFullPath([string]$process.Path) } catch {}
        # Unlesbarer Pfad zaehlt als laufend (konservativ).
        if ($processPath -eq '' -or $processPath.Equals($normalizedTarget, [StringComparison]::OrdinalIgnoreCase)) {
            [void]$found.Add($process)
        }
    }
    return ,($found.ToArray())
}

function Wait-ForTargetToExit([string]$TargetPath, [int]$ProcessId, [int]$TimeoutSec) {
    if ($ProcessId -gt 0) {
        $requested = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
        if ($null -ne $requested) {
            if ($requested.ProcessName -cne 'ArenaBridge') { throw ('PID ' + $ProcessId + ' ist kein ArenaBridge-Prozess.') }
            $requestedPath = ''
            try { $requestedPath = [IO.Path]::GetFullPath([string]$requested.Path) } catch {}
            if ($requestedPath -ne '' -and -not $requestedPath.Equals([IO.Path]::GetFullPath($TargetPath), [StringComparison]::OrdinalIgnoreCase)) {
                throw ('PID ' + $ProcessId + ' gehoert zu einer anderen ArenaBridge-Installation.')
            }
            Write-UpdateLog ('Warte auf das regulaere Beenden von PID ' + $ProcessId + '. Der Updater beendet den Prozess NICHT.')
            if (-not $requested.WaitForExit($TimeoutSec * 1000)) {
                throw 'Die laufende Bridge wurde nicht innerhalb des Zeitlimits beendet. Es wurden keine Dateien geaendert.'
            }
        }
    }
    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSec)
    while ($true) {
        $running = @(Get-RunningTargetInstances $TargetPath)
        if ($running.Count -eq 0) { return }
        if ([DateTime]::UtcNow -gt $deadline) {
            throw 'Eine ArenaBridge-Instanz laeuft noch. Der Updater beendet laufende Programme nie; es wurden keine Dateien geaendert.'
        }
        Start-Sleep -Milliseconds 500
    }
}

function Enter-UpdateLock([string]$LockPath) {
    $lockDir = Split-Path -Parent $LockPath
    if (-not (Test-Path -LiteralPath $lockDir)) { New-Item -ItemType Directory -Path $lockDir -Force | Out-Null }
    try {
        $stream = [IO.File]::Open($LockPath, [IO.FileMode]::CreateNew, [IO.FileAccess]::ReadWrite, [IO.FileShare]::None)
    } catch {
        # Ein verwaister Lock (Absturz) hat keinen offenen Handle und laesst sich loeschen.
        # Ein laufender Updater haelt den Handle offen -> Loeschen schlaegt fehl -> Abbruch.
        try { Remove-Item -LiteralPath $LockPath -Force -ErrorAction Stop }
        catch { throw 'Ein anderes Update laeuft bereits (update.lock ist belegt).' }
        $stream = [IO.File]::Open($LockPath, [IO.FileMode]::CreateNew, [IO.FileAccess]::ReadWrite, [IO.FileShare]::None)
    }
    $bytes = [Text.Encoding]::UTF8.GetBytes([string]$PID)
    $stream.Write($bytes, 0, $bytes.Length)
    $stream.Flush()
    return $stream
}

function Write-UpdateStatusFile([string]$InstallDir, [string]$Version, [string[]]$Notes, [string]$ErrorText) {
    $errorValue = $null
    if (-not [string]::IsNullOrWhiteSpace($ErrorText)) { $errorValue = $ErrorText }
    $payload = [ordered]@{
        version = $Version
        notes = @($Notes)
        error = $errorValue
        updaterVersion = $script:UpdaterVersion
        writtenAtUtc = [DateTime]::UtcNow.ToString('o')
    }
    Write-TextAtomic (Join-Path $InstallDir 'update-status.json') ($payload | ConvertTo-Json -Depth 6)
}

function Restore-Previous([string]$TargetPath, [string]$BackupPath, [string]$RejectedDir, [string]$StatePath, $OldStateText) {
    if ($BackupPath -and (Test-Path -LiteralPath $BackupPath -PathType Leaf)) {
        if (Test-Path -LiteralPath $TargetPath -PathType Leaf) {
            if (-not (Test-Path -LiteralPath $RejectedDir)) { New-Item -ItemType Directory -Path $RejectedDir -Force | Out-Null }
            $rejectedPath = Join-Path $RejectedDir ('ArenaBridge.exe.rejected-' + (Get-Stamp))
            [IO.File]::Move($TargetPath, $rejectedPath)
        }
        [IO.File]::Move($BackupPath, $TargetPath)
    }
    if ($null -eq $OldStateText) {
        if (Test-Path -LiteralPath $StatePath -PathType Leaf) { Remove-Item -LiteralPath $StatePath -Force }
    } else {
        Write-TextAtomic $StatePath ([string]$OldStateText)
    }
}

function Remove-OldFiles([string]$Directory, [string]$Filter, [int]$Keep) {
    try {
        if (-not (Test-Path -LiteralPath $Directory)) { return }
        $files = @(Get-ChildItem -LiteralPath $Directory -Filter $Filter -File | Sort-Object LastWriteTimeUtc -Descending)
        if ($files.Count -gt $Keep) {
            foreach ($old in $files[$Keep..($files.Count - 1)]) { Remove-Item -LiteralPath $old.FullName -Force -ErrorAction SilentlyContinue }
        }
    } catch {}
}

function Invoke-InstallFlow($Manifest, $Installed, [string]$TargetPath, [string]$StatePath, [string]$UpdateDir, [string]$InstallDir) {
    $stagingDir = Join-Path $UpdateDir 'staging'
    $backupDir = Join-Path $UpdateDir 'backup'
    $rejectedDir = Join-Path $UpdateDir 'rejected'
    foreach ($dir in @($stagingDir, $backupDir, $rejectedDir)) {
        if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    }
    $stagingPath = Join-Path $stagingDir 'ArenaBridge.exe.new'
    if (Test-Path -LiteralPath $stagingPath) { Remove-Item -LiteralPath $stagingPath -Force }
    $oldStateText = $null
    if (Test-Path -LiteralPath $StatePath -PathType Leaf) { $oldStateText = [IO.File]::ReadAllText($StatePath, [Text.Encoding]::UTF8) }

    Wait-ForTargetToExit $TargetPath $WaitForProcessId $WaitTimeoutSeconds
    Write-UpdateLog ('Lade Version ' + $Manifest.Version + ' in den Staging-Ordner (Limit ' + $script:MaxArtifactBytes + ' Bytes).')
    $flowSucceeded = $false
    try {
        [void](Get-ApprovedDownload -Uri ([Uri]$Manifest.Url) -MaxBytes $script:MaxArtifactBytes -ExpectedBytes $Manifest.SizeBytes -DestinationPath $stagingPath -TimeoutSeconds 180)
        $stagedSize = (Get-Item -LiteralPath $stagingPath).Length
        if ($stagedSize -ne $Manifest.SizeBytes) { throw ('Dateigroesse stimmt nicht (erwartet ' + $Manifest.SizeBytes + ', erhalten ' + $stagedSize + ').') }
        if (-not (Test-WindowsX64Executable $stagingPath)) { throw 'Die heruntergeladene Datei ist keine Windows-x64-EXE.' }
        $stagedHash = Get-Sha256Hex $stagingPath
        if ($stagedHash -cne $Manifest.Sha256) { throw 'SHA-256 stimmt nicht mit dem Manifest ueberein. Die vorhandene EXE wurde nicht veraendert.' }
        Write-UpdateLog ('Pruefung bestanden: Groesse, SHA-256 ' + $stagedHash.Substring(0, 16) + '..., Windows-x64-EXE.')

        # Vor dem Ersetzen erneut sicherstellen, dass nichts mehr laeuft.
        Wait-ForTargetToExit $TargetPath 0 $WaitTimeoutSeconds

        $backupName = 'ArenaBridge.exe.' + $Installed.Version + '-' + (Get-Stamp) + '.bak'
        $backupPath = Join-Path $backupDir $backupName
        $replaced = $false
        try {
            [IO.File]::Replace($stagingPath, $TargetPath, $backupPath, $true)
            $replaced = $true
            if ((Get-Sha256Hex $TargetPath) -cne $stagedHash) { throw 'Hash der Zieldatei stimmt nach dem Ersetzen nicht.' }
            if ($TestFault -eq 'after-replace') { throw 'Absichtlicher Testfehler nach dem Ersetzen (nur Test-Modus).' }
            $state = [ordered]@{
                schemaVersion = 1
                channel = $Channel
                version = $Manifest.Version
                sha256 = $stagedHash
                installedAtUtc = [DateTime]::UtcNow.ToString('o')
                source = 'update-system'
            }
            Write-TextAtomic $StatePath ($state | ConvertTo-Json -Depth 4)
            Write-UpdateStatusFile $InstallDir $Manifest.Version $Manifest.Notes ''
        } catch {
            $failureText = $_.Exception.Message
            if ($replaced -or (Test-Path -LiteralPath $backupPath -PathType Leaf)) {
                try { Restore-Previous $TargetPath $backupPath $rejectedDir $StatePath $oldStateText } catch {
                    throw ('KRITISCH: Rueckrollen fehlgeschlagen: ' + $_.Exception.Message + ' Backup: ' + $backupPath)
                }
                throw ('Ersetzen fehlgeschlagen; die alte Fassung wurde wiederhergestellt. ' + $failureText)
            }
            throw ('Ersetzen fehlgeschlagen; die alte Fassung blieb unveraendert. ' + $failureText)
        }
        Remove-OldFiles $backupDir 'ArenaBridge.exe.*.bak' 3
        Remove-OldFiles $rejectedDir 'ArenaBridge.exe.rejected-*' 3
        Write-UpdateLog ('Version ' + $Manifest.Version + ' ist installiert. Vorherige EXE: ' + $backupPath)
        $flowSucceeded = $true
        return [pscustomobject]@{ Status = 'ok'; Message = ('Version ' + $Manifest.Version + ' installiert.'); BackupPath = $backupPath; OldStateText = $oldStateText }
    } finally {
        # Erfolgreich: die Staging-Datei wurde durch Replace verbraucht. Fehlgeschlagen:
        # die abgelehnte Datei wird fuer die Analyse in rejected\ archiviert (nie ueber die EXE).
        if (Test-Path -LiteralPath $stagingPath -PathType Leaf) {
            if ($flowSucceeded) { Remove-Item -LiteralPath $stagingPath -Force -ErrorAction SilentlyContinue }
            else {
                try { [IO.File]::Move($stagingPath, (Join-Path $rejectedDir ('ArenaBridge.exe.rejected-' + (Get-Stamp)))) }
                catch { Remove-Item -LiteralPath $stagingPath -Force -ErrorAction SilentlyContinue }
            }
        }
    }
}

# ---------------------------------------------------------------- Hauptablauf
$exitCode = 0
$finalStatus = ''
$finalMessage = ''
$finalPrevious = $null
$installDirResolved = ''
$targetPath = ''
$statePath = ''
$updateDir = ''
$resultRecord = $null
$lockStream = $null
try {
    if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) { throw 'Der Updater ist nur fuer Windows vorgesehen.' }
    if ($TestFault -ne '' -and -not $TestFixtureMode) { throw '-TestFault ist nur im Test-Modus erlaubt.' }
    if ($TargetExeName -cne 'ArenaBridge.exe') { throw 'Die laufende Datei muss exakt ArenaBridge.exe heissen.' }
    if ([string]::IsNullOrWhiteSpace($InstallDirectory)) { throw 'InstallDirectory fehlt.' }
    $installDirResolved = [IO.Path]::GetFullPath($InstallDirectory)
    if (-not (Test-Path -LiteralPath $installDirResolved -PathType Container)) { throw 'Installationsordner existiert nicht.' }
    $targetPath = Join-Path $installDirResolved $TargetExeName
    $statePath = Join-Path $installDirResolved 'update-state.json'
    $updateDir = Join-Path $installDirResolved '.arena-update'
    if ([string]::IsNullOrWhiteSpace($script:ActiveLogPath)) {
        $script:ActiveLogPath = Join-Path $env:LOCALAPPDATA 'ArenaRobloxBridge\bin\update-helper.log'
    }
    Write-UpdateLog ('Modus ' + $Mode + ', Kanal ' + $Channel + $(if ($script:TestFixtureActive) { ' (TEST-MODUS)' } else { '' }) + '.')

    $rawManifest = Get-ChannelManifest
    $manifest = Test-ChannelManifest $rawManifest
    $installed = Get-InstalledState $targetPath $statePath
    $decision = Get-UpdateDecision $manifest $installed
    Write-UpdateLog ('Installiert: ' + $(if ($installed.Version) { $installed.Version } else { 'unbekannt' }) + '; verfuegbar: ' + $(if ($manifest.Enabled) { $manifest.Version } else { '(Kanal deaktiviert)' }) + '; Entscheidung: ' + $decision + '.')

    if ($Mode -eq 'check') {
        $resultRecord = [ordered]@{
            schemaVersion = 1
            status = $decision
            channel = $Channel
            updaterVersion = $script:UpdaterVersion
            installedVersion = [string]$installed.Version
            availableVersion = $(if ($manifest.Enabled) { [string]$manifest.Version } else { '' })
            notes = @($manifest.Notes)
            testFixture = [bool]$script:TestFixtureActive
            checkedAtUtc = [DateTime]::UtcNow.ToString('o')
        }
        if (-not [string]::IsNullOrWhiteSpace($ResultPath)) { Write-TextAtomic $ResultPath ($resultRecord | ConvertTo-Json -Depth 6) }
    } else {
        if ($decision -ne 'update-available') {
            $finalStatus = 'nothing'
            $finalMessage = ('Keine Installation: Entscheidung ' + $decision + '.')
            Write-UpdateLog $finalMessage
        } else {
            $lockPath = Join-Path $updateDir 'update.lock'
            if (-not (Test-Path -LiteralPath $updateDir)) { New-Item -ItemType Directory -Path $updateDir -Force | Out-Null }
            $lockStream = Enter-UpdateLock $lockPath
            try {
                $outcome = Invoke-InstallFlow $manifest $installed $targetPath $statePath $updateDir $installDirResolved
                $finalStatus = 'ok'
                $finalMessage = $outcome.Message
                $finalPrevious = $outcome
            } finally {
                if ($null -ne $lockStream) { $lockStream.Dispose(); $lockStream = $null }
                Remove-Item -LiteralPath $lockPath -Force -ErrorAction SilentlyContinue
            }
        }
    }
} catch {
    $exitCode = 1
    $finalStatus = 'failed'
    $finalMessage = $_.Exception.Message
    Write-UpdateLog ('FEHLER: ' + $finalMessage)
    if ($Mode -eq 'check' -and -not [string]::IsNullOrWhiteSpace($ResultPath)) {
        try {
            Write-TextAtomic $ResultPath ([ordered]@{ schemaVersion = 1; status = 'error'; channel = $Channel; updaterVersion = $script:UpdaterVersion; message = $finalMessage; checkedAtUtc = [DateTime]::UtcNow.ToString('o') } | ConvertTo-Json -Depth 4)
        } catch {}
    }
}

# Nach einer Installation: die Bridge kontrolliert neu starten (oder die alte Fassung wiederherstellen).
if ($Mode -eq 'install' -and $installDirResolved -ne '') {
    try {
        if ($finalStatus -eq 'ok' -and $StartAfterUpdate) {
            $started = Start-Process -FilePath $targetPath -ArgumentList '-UpdateStatus update-erfolgreich' -WorkingDirectory $installDirResolved -PassThru
            if ($started.WaitForExit(5000) -and [int]$started.ExitCode -ne 0) {
                Write-UpdateLog ('Die neue Version beendete sich sofort mit Exit-Code ' + [string]$started.ExitCode + '. Rollback folgt.')
                try {
                    Restore-Previous $targetPath $finalPrevious.BackupPath (Join-Path $updateDir 'rejected') $statePath $finalPrevious.OldStateText
                    $finalStatus = 'failed'
                    $finalMessage = 'Die neue Version startete nicht; die vorherige Version wurde wiederhergestellt.'
                } catch {
                    $finalStatus = 'failed'
                    $finalMessage = 'KRITISCH: Rollback nach Startfehler fehlgeschlagen: ' + $_.Exception.Message
                }
                $exitCode = 1
            }
        }
        if ($finalStatus -eq 'failed' -and (Test-Path -LiteralPath $targetPath -PathType Leaf)) {
            Write-UpdateStatusFile $installDirResolved ([string]$installed.Version) @() $finalMessage
            # Nur neu starten, wenn garantiert KEINE Instanz mehr laeuft (kein Doppelstart).
            if ($StartAfterUpdate -and @(Get-RunningTargetInstances $targetPath).Count -eq 0) {
                [void](Start-Process -FilePath $targetPath -ArgumentList '-UpdateStatus update-fehler' -WorkingDirectory $installDirResolved -PassThru)
            }
        } elseif ($finalStatus -eq 'nothing' -and $StartAfterUpdate -and (Test-Path -LiteralPath $targetPath -PathType Leaf) -and @(Get-RunningTargetInstances $targetPath).Count -eq 0) {
            [void](Start-Process -FilePath $targetPath -ArgumentList '-UpdateStatus kein-update' -WorkingDirectory $installDirResolved -PassThru)
        } elseif ($finalStatus -eq 'ok' -and -not $StartAfterUpdate) {
            Write-UpdateLog 'Installation abgeschlossen (ohne Neustart, wie angefordert).'
        }
    } catch {
        Write-UpdateLog ('Neustart-Schritt fehlgeschlagen: ' + $_.Exception.Message)
    }
}

Write-UpdateLog ('Ende: ' + $finalStatus + $(if ($finalMessage) { ' - ' + $finalMessage } else { '' }))
exit $exitCode
