#requires -Version 5.1
<#
Arena Roblox Bridge - Selbst-Update-Helfer (Updater 2.0.0)

Dieser Helfer wird vom Builder in ArenaBridge.exe eingebettet (als Base64 mit
fest eingetragener SHA-256) und von dort nach %LOCALAPPDATA% extrahiert. Die
EXE haengt NICHT von einer separat veroeffentlichten Updater-Datei ab.

Modi:
  check    Laedt das Kanal-Manifest, prueft es und schreibt ein JSON-Ergebnis.
           Veraendert keine Programmdateien.
  install  Laedt die im Manifest genannte Datei in einen Staging-Ordner, prueft
           Groesse, SHA-256, PE-Kopf UND die eingebaute Dateiversion, wartet auf
           das REGULAERE Beenden der laufenden EXE, ersetzt sie atomar mit
           Backup, schreibt Status und Verlauf und startet die Bridge neu.
           Schlaegt ein Schritt fehl, wird die alte Fassung wiederhergestellt.
  doctor   Schreibt einen Diagnosebericht (Umgebung, Kanal, Manifest, Zustand,
           Schreibrechte, letzter Lauf). Aendert nichts.

Warum Version 2.0.0 (Kurzfassung, Details in developer/docs/UPDATE-KONZEPT.md):
  - Die Artefakt-Datei heisst immer ArenaBridge-<Version>.exe. Der Dateiname
    und die URL werden aus der Manifest-Version ABGELEITET. Damit kann eine
    Veroeffentlichung niemals auf eine ueberschreibbare Sammeldatei zeigen.
  - Das Manifest wird mit Cache-Brecher geladen und bei Fehlern mehrfach
    versucht; nach einem Hash-Konflikt wird das Manifest genau einmal frisch
    nachgeladen (Selbstheilung nach einem Merge/Cache-Versatz).
  - sequence im Manifest: eine aeltere Folge als der lokale Stand wird nie
    eingespielt (Schutz vor einem veralteten Manifest aus einem Cache).
  - Vor dem Ersetzen wird die Dateiversion der neuen EXE geprueft: sie muss zur
    Manifest-Version passen. Ein falsches oder fremdes Artefakt wird abgelehnt.
  - Fortschritt in update-progress.json, Abbruch ueber Abbruch-Datei - ohne
    jemals einen Prozess zu beenden.

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
    [ValidateSet('check', 'install', 'doctor')][string]$Mode = 'check',
    [Parameter(Mandatory = $true)][ValidateSet('beta', 'stable')][string]$Channel,
    [string]$InstallDirectory = '',
    [string]$TargetExeName = 'ArenaBridge.exe',
    [string]$ResultPath = '',
    [string]$LogPath = '',
    [string]$ProgressPath = '',
    [string]$CancelPath = '',
    [int]$WaitForProcessId = 0,
    [int]$WaitTimeoutSeconds = 180,
    [switch]$StartAfterUpdate,
    [switch]$TestFixtureMode,
    [string]$ManifestPath = '',
    [ValidateSet('', 'after-replace')][string]$TestFault = ''
)

$ErrorActionPreference = 'Stop'
$script:UpdaterVersion = '2.0.0'
$script:ManifestSchemaVersion = 2
$script:MaxManifestBytes = 1048576
$script:MaxArtifactBytes = 67108864
$script:MinArtifactBytes = 1024
$script:MaxRedirects = 3
$script:LogMaxBytes = 1048576
$script:ManifestAttempts = 3
$script:ManifestRetrySeconds = 2
$script:CanonicalChannelBase = 'https://raw.githubusercontent.com/merta-studios/arenarobloxbridge/main/next-update/update-system/channels/'
$script:CanonicalReleaseBase = 'https://raw.githubusercontent.com/merta-studios/arenarobloxbridge/main/next-update/release/'
$script:ApprovedDownloadHosts = @('raw.githubusercontent.com')
$script:ApprovedRedirectHosts = @('raw.githubusercontent.com', 'objects.githubusercontent.com', 'release-assets.githubusercontent.com')
$script:ActiveLogPath = $LogPath
$script:TestFixtureActive = [bool]$TestFixtureMode
$script:CancelRequested = $false

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
    if (-not [string]::IsNullOrWhiteSpace($dir) -and -not (Test-Path -LiteralPath $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
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

function Get-ArtifactFileName([string]$Version) { return ('ArenaBridge-' + $Version + '.exe') }

function Get-ArtifactUrl([string]$Version) { return ($script:CanonicalReleaseBase + (Get-ArtifactFileName $Version)) }

function Get-CoreVersion([string]$Value) {
    if ([string]::IsNullOrWhiteSpace($Value)) { return '' }
    $parts = $Value.Split('-', 2)
    return $parts[0]
}

function Get-FileVersionCore([string]$Path) {
    try {
        $raw = [string]([Diagnostics.FileVersionInfo]::GetVersionInfo($Path).FileVersion)
    } catch { return '' }
    $match = [regex]::Match($raw, '^(\d+\.\d+\.\d+)')
    if (-not $match.Success) { return '' }
    return $match.Groups[1].Value
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

function Assert-NotCancelled {
    # Abbruch ist eine freundliche Bitte des Nutzers, kein Prozesseingriff.
    if ($script:CancelRequested) { throw 'ARENA_CANCEL:Der Nutzer hat das Update abgebrochen.' }
    if ([string]::IsNullOrWhiteSpace($script:ActiveCancelPath)) { return }
    if (Test-Path -LiteralPath $script:ActiveCancelPath -PathType Leaf) {
        $script:CancelRequested = $true
        throw 'ARENA_CANCEL:Der Nutzer hat das Update abgebrochen.'
    }
}

function Get-ApprovedDownload {
    param(
        [Parameter(Mandatory = $true)][Uri]$Uri,
        [Parameter(Mandatory = $true)][long]$MaxBytes,
        [long]$ExpectedBytes = 0,
        [string]$DestinationPath = '',
        [int]$TimeoutSeconds = 180,
        [scriptblock]$OnBytes = $null
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
            if ($status -eq 404) { throw 'ARENA_HTTP404:Die Datei liegt auf dem Server noch nicht (HTTP 404).' }
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
            $nextProgressAt = [long]0
            while ($true) {
                $readCount = $inStream.Read($buffer, 0, $buffer.Length)
                if ($readCount -le 0) { break }
                if ([DateTime]::UtcNow -gt $deadline) { throw 'Zeitlimit fuer den Download ueberschritten.' }
                $received += [long]$readCount
                if ($received -gt $MaxBytes) { throw 'Der Download ueberschreitet das Groessenlimit.' }
                if ($ExpectedBytes -gt 0 -and $received -gt $ExpectedBytes) { throw 'Der Download ist groesser als im Manifest angegeben.' }
                $outStream.Write($buffer, 0, $readCount)
                if ($received -ge $nextProgressAt) {
                    $nextProgressAt = $received + 131072
                    Assert-NotCancelled
                    if ($null -ne $OnBytes) { & $OnBytes $received }
                }
            }
            if ($received -le 0) { throw 'Leerer Download.' }
            if ($declaredLength -ge 0 -and $received -ne $declaredLength) { throw 'Download unvollstaendig (Content-Length stimmt nicht).' }
            if ($ExpectedBytes -gt 0 -and $received -ne $ExpectedBytes) { throw 'Groesse passt nicht zum Manifest.' }
            $outStream.Flush()
            $completed = $true
            if ($null -ne $OnBytes) { & $OnBytes $received }
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

function Get-WithCacheBreaker([string]$Url) {
    # raw.githubusercontent.com liefert pro URL einen Cache. Ein kurzer, sich
    # aendernder Abfrageteil holt nach einem Merge garantiert den neuen Stand.
    $separator = '?'
    if ($Url.Contains('?')) { $separator = '&' }
    return ($Url + $separator + 'cb=' + [DateTime]::UtcNow.Ticks.ToString())
}

function Get-ChannelManifestText([bool]$BustCache) {
    if ($script:TestFixtureActive) {
        if ([string]::IsNullOrWhiteSpace($ManifestPath)) { throw 'Der Test-Modus braucht -ManifestPath.' }
        if (-not (Test-Path -LiteralPath $ManifestPath -PathType Leaf)) { throw 'Test-Manifest nicht gefunden.' }
        if ((Get-Item -LiteralPath $ManifestPath).Length -gt $script:MaxManifestBytes) { throw 'Manifest ueberschreitet das Groessenlimit.' }
        return [IO.File]::ReadAllText($ManifestPath, [Text.Encoding]::UTF8)
    }
    if (-not [string]::IsNullOrWhiteSpace($ManifestPath)) { throw '-ManifestPath ist nur im Test-Modus erlaubt.' }
    $expectedUrl = $script:CanonicalChannelBase + $Channel + '.json'
    $attempt = 0
    $lastError = ''
    while ($attempt -lt $script:ManifestAttempts) {
        $attempt++
        $url = $expectedUrl
        if ($BustCache -or $attempt -gt 1) { $url = Get-WithCacheBreaker $expectedUrl }
        try {
            $download = Get-ApprovedDownload -Uri ([Uri]$url) -MaxBytes $script:MaxManifestBytes -TimeoutSeconds 30
            return [Text.Encoding]::UTF8.GetString([byte[]]$download.Bytes)
        } catch {
            $lastError = $_.Exception.Message
            if ($_.Exception.Message -like 'ARENA_CANCEL:*') { throw }
            Write-UpdateLog ('Manifest-Versuch ' + [string]$attempt + ' von ' + [string]$script:ManifestAttempts + ' fehlgeschlagen: ' + $lastError)
            if ($attempt -lt $script:ManifestAttempts) { Start-Sleep -Seconds $script:ManifestRetrySeconds }
        }
    }
    throw ('Das Kanal-Manifest konnte nicht geladen werden: ' + $lastError)
}

function Get-ChannelManifest([switch]$BustCache) {
    $raw = Get-ChannelManifestText ([bool]$BustCache)
    if ($raw.Length -gt 0 -and [int][char]$raw[0] -eq 0xFEFF) { $raw = $raw.Substring(1) }
    try {
        return ($raw | ConvertFrom-Json -ErrorAction Stop)
    } catch {
        throw 'Das Kanal-Manifest ist kein gueltiges JSON.'
    }
}

function Test-ChannelManifest($Manifest) {
    $schemaText = [string](Get-JsonProperty $Manifest 'schemaVersion')
    if ($schemaText -cne [string]$script:ManifestSchemaVersion) {
        throw ('Nicht unterstuetzte schemaVersion im Manifest (erwartet ' + [string]$script:ManifestSchemaVersion + ').')
    }
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

    $sequence = 0
    $rawSequence = [string](Get-JsonProperty $Manifest 'sequence')
    if ($rawSequence -cnotmatch '^\d{1,12}$') { throw 'sequence fehlt oder ist keine ganze Zahl.' }
    $sequence = [int]$rawSequence
    if ($sequence -lt 1) { throw 'sequence muss mindestens 1 sein.' }

    $artifact = Get-JsonProperty $Manifest 'artifact'
    if ($null -eq $artifact) { throw 'Manifest ohne artifact.' }

    if (-not $enabledValue) {
        # Ein deaktivierter Kanal darf keinerlei Download-Koordinaten anbieten.
        $urlText = [string](Get-JsonProperty $artifact 'url')
        $shaText = [string](Get-JsonProperty $artifact 'sha256')
        $sizeText = [string](Get-JsonProperty $artifact 'sizeBytes')
        if (-not [string]::IsNullOrWhiteSpace($urlText)) { throw 'Ein deaktivierter Kanal darf keine artifact.url nennen.' }
        if (-not [string]::IsNullOrWhiteSpace($shaText)) { throw 'Ein deaktivierter Kanal darf keine artifact.sha256 nennen.' }
        if ($sizeText -cnotmatch '^\d+$' -or [long]$sizeText -ne 0) { throw 'Ein deaktivierter Kanal muss artifact.sizeBytes 0 setzen.' }
        return [pscustomobject]@{
            Enabled = $false; Channel = $channelText; Version = ''; Sha256 = ''; SizeBytes = [long]0
            Url = ''; Notes = $notes; Sequence = $sequence; PublishedAtUtc = ''
        }
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

    # Dateiname und Ziel-URL sind aus der Version ABGELEITET: eine
    # Veroeffentlichung kann nicht versehentlich auf eine Sammeldatei zeigen,
    # die eine spaetere Veroeffentlichung ueberschreiben wuerde.
    $expectedName = Get-ArtifactFileName $versionText
    $expectedUrl = Get-ArtifactUrl $versionText
    if ([string](Get-JsonProperty $artifact 'fileName') -cne $expectedName) {
        throw ('artifact.fileName muss ' + $expectedName + ' sein (aus der Version abgeleitet).')
    }
    $urlText = [string](Get-JsonProperty $artifact 'url')
    if ($script:TestFixtureActive) {
        $expectedFixture = '^http://127\.0\.0\.1:\d{4,5}/' + [regex]::Escape($expectedName) + '$'
        if ($urlText -cnotmatch $expectedFixture) { throw ('Test-Artefakt-URL muss auf 127.0.0.1 zeigen und ' + $expectedName + ' heissen.') }
    } elseif ($urlText -cne $expectedUrl) {
        throw ('artifact.url ist nicht die erwartete Release-Datei ' + $expectedUrl + '.')
    }
    $artifactUri = $null
    if (-not [Uri]::TryCreate($urlText, [UriKind]::Absolute, [ref]$artifactUri) -or -not (Test-AllowedUri $artifactUri $false)) {
        throw 'artifact.url ist fuer den Download nicht erlaubt.'
    }
    $sha256 = ([string](Get-JsonProperty $artifact 'sha256')).ToLowerInvariant()
    if ($sha256 -cnotmatch '^[0-9a-f]{64}$') { throw 'artifact.sha256 muss 64 hexadezimale Zeichen enthalten.' }
    $sizeText = [string](Get-JsonProperty $artifact 'sizeBytes')
    if ($sizeText -cnotmatch '^\d{1,12}$') { throw 'artifact.sizeBytes muss eine ganze Zahl sein.' }
    $sizeBytes = [long]$sizeText
    if ($sizeBytes -lt $script:MinArtifactBytes -or $sizeBytes -gt $script:MaxArtifactBytes) {
        throw ('artifact.sizeBytes muss zwischen ' + $script:MinArtifactBytes + ' und ' + $script:MaxArtifactBytes + ' Bytes liegen.')
    }
    return [pscustomobject]@{
        Enabled = $true; Channel = $channelText; Version = $versionText; Sha256 = $sha256
        SizeBytes = $sizeBytes; Url = $urlText; Notes = $notes; Sequence = $sequence
        PublishedAtUtc = $publishedText
    }
}

function Get-InstalledState([string]$TargetPath, [string]$StatePath) {
    $stateVersion = ''
    $stateSha = ''
    $stateChannel = ''
    $stateSequence = 0
    if (Test-Path -LiteralPath $StatePath -PathType Leaf) {
        try {
            $state = Get-Content -LiteralPath $StatePath -Raw -Encoding UTF8 | ConvertFrom-Json -ErrorAction Stop
        } catch {
            throw 'Der lokale Update-Status ist unlesbar. Es wird ohne verlaessliche Versionshistorie nicht aktualisiert.'
        }
        $stateSchema = [string](Get-JsonProperty $state 'schemaVersion')
        if ($stateSchema -cne '1' -and $stateSchema -cne '2') { throw 'Lokaler Update-Status hat eine unbekannte schemaVersion.' }
        $stateChannel = [string](Get-JsonProperty $state 'channel')
        if ($stateChannel -cne 'beta' -and $stateChannel -cne 'stable') { throw 'Lokaler Update-Status hat einen ungueltigen Kanal.' }
        $stateVersion = [string](Get-JsonProperty $state 'version')
        if (-not (Test-UpdateVersion $stateVersion)) { throw 'Lokaler Update-Status hat eine ungueltige Version.' }
        $stateSha = ([string](Get-JsonProperty $state 'sha256')).ToLowerInvariant()
        $sequenceText = [string](Get-JsonProperty $state 'sequence')
        if ($sequenceText -cmatch '^\d{1,12}$') { $stateSequence = [int]$sequenceText }
    }
    $fileVersion = ''
    if (Test-Path -LiteralPath $TargetPath -PathType Leaf) { $fileVersion = Get-FileVersionCore $TargetPath }
    $installed = $stateVersion
    if ($fileVersion -ne '') {
        if ($installed -eq '' -or (Compare-UpdateVersion $fileVersion $installed) -gt 0) { $installed = $fileVersion }
    }
    return [pscustomobject]@{
        Version = $installed; StateVersion = $stateVersion; StateSha256 = $stateSha
        StateChannel = $stateChannel; StateSequence = $stateSequence; FileVersion = $fileVersion
        TargetExists = (Test-Path -LiteralPath $TargetPath -PathType Leaf)
    }
}

function Get-UpdateDecision($Manifest, $Installed, [string]$TargetPath) {
    if (-not $Manifest.Enabled) { return 'disabled' }
    if (-not $Installed.TargetExists) { return 'target-missing' }
    if ($Installed.Version -eq '') { return 'error' }
    if ($Installed.StateSequence -gt 0 -and $Manifest.Sequence -lt $Installed.StateSequence) { return 'manifest-stale' }
    $order = Compare-UpdateVersion $Manifest.Version $Installed.Version
    if ($order -lt 0) { return 'downgrade-refused' }
    if ($order -eq 0) {
        if ($Installed.StateSha256 -ceq $Manifest.Sha256) { return 'up-to-date' }
        if ($Installed.StateSha256 -ne '') { return 'version-conflict' }
        # Kein verlaesslicher Stand gespeichert (z. B. manuell installiert):
        # gleiche Version, aber anderer Dateiinhalt -> diese Fassung anbieten.
        try {
            if ((Get-Sha256Hex $TargetPath) -ceq $Manifest.Sha256) { return 'up-to-date' }
        } catch { return 'error' }
        return 'update-available'
    }
    return 'update-available'
}

function Write-UpdateProgress([string]$Phase, [string]$Message, [long]$ReceivedBytes = 0, [long]$TotalBytes = 0) {
    if ([string]::IsNullOrWhiteSpace($script:ActiveProgressPath)) { return }
    $percent = 0
    if ($TotalBytes -gt 0) {
        $percent = [int][Math]::Floor(([double]$ReceivedBytes / [double]$TotalBytes) * 100)
        if ($percent -lt 0) { $percent = 0 }
        if ($percent -gt 100) { $percent = 100 }
    }
    $payload = [ordered]@{
        schemaVersion = 1
        phase = $Phase
        message = $Message
        percent = $percent
        receivedBytes = $ReceivedBytes
        totalBytes = $TotalBytes
        updaterVersion = $script:UpdaterVersion
        channel = $Channel
        updatedAtUtc = [DateTime]::UtcNow.ToString('o')
    }
    try { Write-TextAtomic $script:ActiveProgressPath ($payload | ConvertTo-Json -Depth 4) } catch {}
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

function Add-UpdateHistory([string]$InstallDir, [string]$Status, [string]$Version, [string]$Message) {
    $historyPath = Join-Path $InstallDir 'update-history.json'
    $entries = New-Object System.Collections.ArrayList
    if (Test-Path -LiteralPath $historyPath -PathType Leaf) {
        try {
            $existing = Get-Content -LiteralPath $historyPath -Raw -Encoding UTF8 | ConvertFrom-Json -ErrorAction Stop
            foreach ($item in @($existing.entries)) { if ($null -ne $item) { [void]$entries.Add($item) } }
        } catch { }
    }
    [void]$entries.Add([ordered]@{
        status = $Status
        version = $Version
        message = $Message
        channel = $Channel
        updaterVersion = $script:UpdaterVersion
        atUtc = [DateTime]::UtcNow.ToString('o')
    })
    while ($entries.Count -gt 12) { $entries.RemoveAt(0) }
    try { Write-TextAtomic $historyPath ([ordered]@{ schemaVersion = 1; entries = $entries.ToArray() } | ConvertTo-Json -Depth 5) } catch {}
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

function Invoke-InstallFlow($Manifest, $Installed, [string]$TargetPath, [string]$StatePath, [string]$UpdateDir, [string]$InstallDir, [bool]$FreshManifest) {
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

    Write-UpdateProgress 'downloading' ('Version ' + $Manifest.Version + ' wird geladen ...') 0 $Manifest.SizeBytes
    Write-UpdateLog ('Lade Version ' + $Manifest.Version + ' in den Staging-Ordner (Limit ' + $script:MaxArtifactBytes + ' Bytes).')
    $flowSucceeded = $false
    try {
        $onBytes = {
            param($received)
            Write-UpdateProgress 'downloading' ('Version ' + $Manifest.Version + ' wird geladen ...') ([long]$received) ([long]$Manifest.SizeBytes)
        }
        # Der Download laeuft, WAEHREND die Bridge noch offen ist: der Nutzer
        # sieht den Fortschritt im Fenster. Erst danach wird das Beenden
        # angefordert (die Bridge schliesst sich dann selbst).
        [void](Get-ApprovedDownload -Uri ([Uri]$Manifest.Url) -MaxBytes $script:MaxArtifactBytes -ExpectedBytes $Manifest.SizeBytes -DestinationPath $stagingPath -TimeoutSeconds 300 -OnBytes $onBytes)
        Write-UpdateProgress 'verifying' 'Download vollstaendig - Pruefsumme wird berechnet ...' $Manifest.SizeBytes $Manifest.SizeBytes
        $stagedSize = (Get-Item -LiteralPath $stagingPath).Length
        if ($stagedSize -ne $Manifest.SizeBytes) { throw ('Dateigroesse stimmt nicht (erwartet ' + $Manifest.SizeBytes + ', erhalten ' + $stagedSize + ').') }
        if (-not (Test-WindowsX64Executable $stagingPath)) { throw 'Die heruntergeladene Datei ist keine Windows-x64-EXE.' }
        $stagedHash = Get-Sha256Hex $stagingPath
        if ($stagedHash -cne $Manifest.Sha256) { throw 'SHA-256 stimmt nicht mit dem Manifest ueberein. Die vorhandene EXE wurde nicht veraendert.' }
        # Version im Kopf der Datei: verhindert, dass ein fremdes oder falsch
        # benanntes Artefakt installiert wird.
        $stagedVersion = Get-FileVersionCore $stagingPath
        if ($stagedVersion -eq '') { throw 'Die neue EXE enthaelt keine Dateiversion; sie wird nicht installiert.' }
        if ($stagedVersion -cne (Get-CoreVersion $Manifest.Version)) {
            throw ('Die neue EXE meldet Version ' + $stagedVersion + ', das Manifest aber ' + $Manifest.Version + '.')
        }
        Write-UpdateLog ('Pruefung bestanden: Groesse, SHA-256 ' + $stagedHash.Substring(0, 16) + '..., x64-EXE, Dateiversion ' + $stagedVersion + '.')

        # Ab hier ist alles geprueft: die Bridge darf sich jetzt beenden.
        Write-UpdateProgress 'ready-to-install' 'Geprueft - die Bridge schliesst sich jetzt und wird ersetzt.' $Manifest.SizeBytes $Manifest.SizeBytes
        Assert-NotCancelled
        Write-UpdateProgress 'waiting-for-exit' 'Warte auf das regulaere Beenden der Bridge ...' $Manifest.SizeBytes $Manifest.SizeBytes
        Wait-ForTargetToExit $TargetPath $WaitForProcessId $WaitTimeoutSeconds
        Wait-ForTargetToExit $TargetPath 0 $WaitTimeoutSeconds
        Assert-NotCancelled

        Write-UpdateProgress 'installing' 'Die neue Fassung wird eingesetzt ...' $Manifest.SizeBytes $Manifest.SizeBytes
        $backupName = 'ArenaBridge.exe.' + $Installed.Version + '-' + (Get-Stamp) + '.bak'
        $backupPath = Join-Path $backupDir $backupName
        $replaced = $false
        try {
            [IO.File]::Replace($stagingPath, $TargetPath, $backupPath, $true)
            $replaced = $true
            if ((Get-Sha256Hex $TargetPath) -cne $stagedHash) { throw 'Hash der Zieldatei stimmt nach dem Ersetzen nicht.' }
            if ($TestFault -eq 'after-replace') { throw 'Absichtlicher Testfehler nach dem Ersetzen (nur Test-Modus).' }
            $state = [ordered]@{
                schemaVersion = 2
                channel = $Channel
                version = $Manifest.Version
                sha256 = $stagedHash
                sequence = $Manifest.Sequence
                previousVersion = [string]$Installed.Version
                installedAtUtc = [DateTime]::UtcNow.ToString('o')
                source = 'update-system'
            }
            Write-TextAtomic $StatePath ($state | ConvertTo-Json -Depth 4)
            Write-UpdateStatusFile $InstallDir $Manifest.Version $Manifest.Notes ''
            Add-UpdateHistory $InstallDir 'ok' $Manifest.Version ('Version ' + $Manifest.Version + ' installiert (vorher ' + [string]$Installed.Version + ').')
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

function Get-ErrorCode([string]$Message) {
    if ($Message -like 'ARENA_CANCEL:*') { return 'cancelled' }
    if ($Message -like 'ARENA_HTTP404:*') { return 'artifact-not-found' }
    if ($Message -like '*SHA-256*') { return 'hash-mismatch' }
    if ($Message -like '*Dateiversion*') { return 'version-mismatch' }
    if ($Message -like '*Dateigroesse*' -or $Message -like '*Groesse*') { return 'size-mismatch' }
    if ($Message -like '*konnte nicht geladen werden*' -or $Message -like '*Zeitlimit*' -or $Message -like '*Verbindung*') { return 'network' }
    if ($Message -like '*zu alt*') { return 'updater-too-old' }
    return 'error'
}

function Get-CleanMessage([string]$Message, [string]$ErrorCode) {
    $text = $Message
    if ($ErrorCode -eq 'cancelled') { return 'Der Nutzer hat das Update abgebrochen. Es wurde nichts geaendert.' }
    if ($ErrorCode -eq 'artifact-not-found') {
        return 'Die neue Datei ist auf GitHub noch nicht abrufbar (HTTP 404). Das kommt direkt nach einem Merge vor; bitte spaeter erneut versuchen.'
    }
    if ($text -like 'ARENA_*:*') { return $text.Substring($text.IndexOf(':') + 1) }
    return $text
}

function Get-DoctorReport($Manifest, $ManifestError, $Installed, [string]$InstallDir, [string]$TargetPath, [string]$StatePath, [string]$UpdateDir) {
    $writeable = $false
    $writeTestPath = Join-Path $InstallDir ('.arena-write-test-' + [Guid]::NewGuid().ToString('N') + '.tmp')
    try {
        [IO.File]::WriteAllText($writeTestPath, 'ok')
        $writeable = $true
        Remove-Item -LiteralPath $writeTestPath -Force -ErrorAction SilentlyContinue
    } catch { }
    $statusPath = Join-Path $InstallDir 'update-status.json'
    $lastStatus = $null
    if (Test-Path -LiteralPath $statusPath -PathType Leaf) {
        try { $lastStatus = Get-Content -LiteralPath $statusPath -Raw -Encoding UTF8 } catch { }
    }
    $manifestUrl = $script:CanonicalChannelBase + $Channel + '.json'
    return [ordered]@{
        schemaVersion = 1
        updaterVersion = $script:UpdaterVersion
        os = [Environment]::OSVersion.VersionString
        platform = [string][Environment]::OSVersion.Platform
        powershell = [string]$PSVersionTable.PSVersion
        testFixtureMode = [bool]$script:TestFixtureActive
        channel = $Channel
        manifestUrl = $manifestUrl
        manifestOk = ($null -eq $ManifestError)
        manifestError = [string]$ManifestError
        availableVersion = $(if ($null -ne $Manifest -and $Manifest.Enabled) { [string]$Manifest.Version } else { '' })
        sequence = $(if ($null -ne $Manifest) { [int]$Manifest.Sequence } else { 0 })
        installDirectory = $InstallDir
        installDirectoryWriteable = $writeable
        targetPath = $TargetPath
        targetExists = [bool]$Installed.TargetExists
        installedFileVersion = [string]$Installed.FileVersion
        installedStateVersion = [string]$Installed.StateVersion
        installedStateSequence = [int]$Installed.StateSequence
        updateDirectory = $UpdateDir
        updateStatusJson = $lastStatus
        checkedAtUtc = [DateTime]::UtcNow.ToString('o')
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
$logPath = ''
$script:ActiveProgressPath = ''
$script:ActiveCancelPath = ''
$lockStream = $null
$manifest = $null
$manifestError = ''
$installed = $null
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
    if (-not (Test-Path -LiteralPath $updateDir)) { New-Item -ItemType Directory -Path $updateDir -Force | Out-Null }
    if (-not [string]::IsNullOrWhiteSpace($LogPath)) { $script:ActiveLogPath = $LogPath }
    elseif ([string]::IsNullOrWhiteSpace($script:ActiveLogPath)) {
        $script:ActiveLogPath = Join-Path $env:LOCALAPPDATA 'ArenaRobloxBridge\bin\update-helper.log'
    }
    $logPath = [string]$script:ActiveLogPath
    $script:ActiveProgressPath = $ProgressPath
    if ([string]::IsNullOrWhiteSpace($script:ActiveProgressPath)) { $script:ActiveProgressPath = Join-Path $updateDir 'update-progress.json' }
    $script:ActiveCancelPath = $CancelPath
    if ([string]::IsNullOrWhiteSpace($script:ActiveCancelPath)) { $script:ActiveCancelPath = Join-Path $updateDir 'cancel.request' }
    if (Test-Path -LiteralPath $script:ActiveCancelPath -PathType Leaf) { Remove-Item -LiteralPath $script:ActiveCancelPath -Force }

    Write-UpdateLog ('Modus ' + $Mode + ', Kanal ' + $Channel + $(if ($script:TestFixtureActive) { ' (TEST-MODUS)' } else { '' }) + ', Updater ' + $script:UpdaterVersion + '.')

    try {
        $manifest = Test-ChannelManifest (Get-ChannelManifest)
    } catch {
        $manifestError = $_.Exception.Message
        # Die Diagnose soll auch dann etwas sagen, wenn das Manifest kaputt ist.
        if ($Mode -ne 'doctor') { throw }
    }
    if ($null -eq $manifest) {
        $manifest = [pscustomobject]@{
            Enabled = $false; Channel = $Channel; Version = ''; Sha256 = ''; SizeBytes = [long]0
            Url = ''; Notes = @(); Sequence = 0; PublishedAtUtc = ''
        }
    }

    $installed = Get-InstalledState $targetPath $statePath

    if ($Mode -eq 'doctor') {
        $report = Get-DoctorReport $manifest $manifestError $installed $installDirResolved $targetPath $statePath $updateDir
        if (-not [string]::IsNullOrWhiteSpace($ResultPath)) { Write-TextAtomic $ResultPath ($report | ConvertTo-Json -Depth 6) }
        Write-Host ''
        Write-Host 'Arena Roblox Bridge - Update-Diagnose'
        Write-Host ('  Updater:            ' + $report.updaterVersion + '  (PowerShell ' + $report.powershell + ')')
        Write-Host ('  Kanal:              ' + $report.channel + '   Manifest: ' + $(if ($report.manifestOk) { 'lesbar' } else { 'FEHLER' }))
        if (-not $report.manifestOk) { Write-Host ('    Grund:            ' + $report.manifestError) }
        Write-Host ('  Verfuegbar:         ' + $(if ($report.availableVersion) { $report.availableVersion + ' (sequence ' + $report.sequence + ')' } else { '(Kanal deaktiviert)' }))
        Write-Host ('  Installiert:        ' + $(if ($report.installedStateVersion) { $report.installedStateVersion } else { '(kein Update-Status)' }) + $(if ($report.installedFileVersion) { ', Dateiversion ' + $report.installedFileVersion } else { '' }))
        Write-Host ('  Ordner:             ' + $report.installDirectory + '  schreibbar: ' + $report.installDirectoryWriteable)
        Write-Host ('  Programmdatei:      ' + $report.targetPath + '  vorhanden: ' + $report.targetExists)
        Write-Host ('  Protokoll:          ' + $logPath)
        Write-Host ''
        $finalStatus = 'doctor'
        $finalMessage = 'Diagnose geschrieben.'
    }

    if ($Mode -ne 'doctor') {
    $decision = Get-UpdateDecision $manifest $installed $targetPath
    Write-UpdateLog ('Installiert: ' + $(if ($installed.Version) { $installed.Version } else { 'unbekannt' }) + '; verfuegbar: ' + $(if ($manifest.Enabled) { $manifest.Version } else { '(Kanal deaktiviert)' }) + '; Entscheidung: ' + $decision + '.')

    if ($Mode -eq 'check') {
        $resultRecord = [ordered]@{
            schemaVersion = 2
            status = $decision
            channel = $Channel
            updaterVersion = $script:UpdaterVersion
            installedVersion = [string]$installed.Version
            availableVersion = $(if ($manifest.Enabled) { [string]$manifest.Version } else { '' })
            sequence = [int]$manifest.Sequence
            artifactSizeBytes = [long]$manifest.SizeBytes
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
            Write-UpdateProgress 'nothing' 'Kein Update installiert.' 0 0
        } else {
            $lockPath = Join-Path $updateDir 'update.lock'
            $lockStream = Enter-UpdateLock $lockPath
            try {
                $outcome = $null
                try {
                    $outcome = Invoke-InstallFlow $manifest $installed $targetPath $statePath $updateDir $installDirResolved $true
                } catch {
                    $retryText = $_.Exception.Message
                    $retryCode = Get-ErrorCode $retryText
                    # Selbstheilung: nach einem Merge liefert der Cache gern noch
                    # das alte Manifest (alte Pruefsumme). Dann genau einmal
                    # frisch laden und erneut versuchen - ohne Dateiaenderung.
                    if (-not $script:TestFixtureActive -and ($retryCode -eq 'hash-mismatch' -or $retryCode -eq 'size-mismatch' -or $retryCode -eq 'artifact-not-found')) {
                        Write-UpdateLog 'Erster Versuch scheiterte; Manifest wird frisch nachgeladen und einmal wiederholt.'
                        Write-UpdateProgress 'retrying' 'Neuer Anlauf mit frischem Manifest ...' 0 0
                        $fresh = Test-ChannelManifest (Get-ChannelManifest -BustCache)
                        $freshDecision = Get-UpdateDecision $fresh (Get-InstalledState $targetPath $statePath) $targetPath
                        if ($freshDecision -eq 'update-available') {
                            $outcome = Invoke-InstallFlow $fresh $installed $targetPath $statePath $updateDir $installDirResolved $false
                        } else {
                            $finalStatus = 'nothing'
                            $finalMessage = ('Keine Installation nach frischer Pruefung: Entscheidung ' + $freshDecision + '.')
                            Write-UpdateLog $finalMessage
                        }
                    } else {
                        throw
                    }
                }
                if ($null -ne $outcome) {
                    $finalStatus = 'ok'
                    $finalMessage = $outcome.Message
                    $finalPrevious = $outcome
                }
            } finally {
                if ($null -ne $lockStream) { $lockStream.Dispose(); $lockStream = $null }
                Remove-Item -LiteralPath $lockPath -Force -ErrorAction SilentlyContinue
            }
        }
    }
    }
} catch {
    $messageText = $_.Exception.Message
    $code = Get-ErrorCode $messageText
    $clean = Get-CleanMessage $messageText $code
    if ($code -eq 'cancelled') {
        $finalStatus = 'cancelled'
        $finalMessage = $clean
        Write-UpdateLog ('ABBRUCH: ' + $clean)
        Write-UpdateProgress 'cancelled' $clean 0 0
    } else {
        $exitCode = 1
        $finalStatus = 'failed'
        $finalMessage = $clean
        Write-UpdateLog ('FEHLER (' + $code + '): ' + $messageText)
        Write-UpdateProgress 'error' $clean 0 0
        if ($Mode -eq 'check' -and -not [string]::IsNullOrWhiteSpace($ResultPath)) {
            try {
                Write-TextAtomic $ResultPath ([ordered]@{
                    schemaVersion = 2; status = 'error'; errorCode = $code; channel = $Channel
                    updaterVersion = $script:UpdaterVersion; message = $clean
                    checkedAtUtc = [DateTime]::UtcNow.ToString('o')
                } | ConvertTo-Json -Depth 4)
            } catch {}
        }
    }
}

# Nach einer Installation: die Bridge kontrolliert neu starten (oder die alte Fassung wiederherstellen).
if ($Mode -eq 'install' -and $installDirResolved -ne '') {
    try {
        if ($finalStatus -eq 'ok' -and $StartAfterUpdate) {
            Write-UpdateProgress 'restarting' 'Die neue Version wird gestartet ...' 0 0
            $started = Start-Process -FilePath $targetPath -ArgumentList '-UpdateStatus update-erfolgreich' -WorkingDirectory $installDirResolved -PassThru
            if ($started.WaitForExit(15000) -and [int]$started.ExitCode -ne 0) {
                Write-UpdateLog ('Die neue Version beendete sich sofort mit Exit-Code ' + [string]$started.ExitCode + '. Rollback folgt.')
                try {
                    Restore-Previous $targetPath $finalPrevious.BackupPath (Join-Path $updateDir 'rejected') $statePath $finalPrevious.OldStateText
                    $finalStatus = 'failed'
                    $finalMessage = 'Die neue Version startete nicht; die vorherige Version wurde wiederhergestellt.'
                    Add-UpdateHistory $installDirResolved 'rolled-back' $manifest.Version $finalMessage
                } catch {
                    $finalStatus = 'failed'
                    $finalMessage = 'KRITISCH: Rollback nach Startfehler fehlgeschlagen: ' + $_.Exception.Message
                }
                $exitCode = 1
            }
        }
        if ($finalStatus -eq 'failed' -and (Test-Path -LiteralPath $targetPath -PathType Leaf)) {
            $fallbackVersion = ''
            if ($null -ne $installed) { $fallbackVersion = [string]$installed.Version }
            Write-UpdateStatusFile $installDirResolved $fallbackVersion @() $finalMessage
            Add-UpdateHistory $installDirResolved 'failed' $(if ($null -ne $manifest) { [string]$manifest.Version } else { '' }) $finalMessage
            # Nur neu starten, wenn garantiert KEINE Instanz mehr laeuft (kein Doppelstart).
            if ($StartAfterUpdate -and @(Get-RunningTargetInstances $targetPath).Count -eq 0) {
                [void](Start-Process -FilePath $targetPath -ArgumentList '-UpdateStatus update-fehler' -WorkingDirectory $installDirResolved -PassThru)
            }
        } elseif ($finalStatus -eq 'nothing' -and $StartAfterUpdate -and (Test-Path -LiteralPath $targetPath -PathType Leaf) -and @(Get-RunningTargetInstances $targetPath).Count -eq 0) {
            [void](Start-Process -FilePath $targetPath -ArgumentList '-UpdateStatus kein-update' -WorkingDirectory $installDirResolved -PassThru)
        }
        if ($finalStatus -eq 'ok') { Write-UpdateProgress 'done' 'Die neue Version ist installiert.' 0 0 }
    } catch {
        Write-UpdateLog ('Neustart-Schritt fehlgeschlagen: ' + $_.Exception.Message)
    }
}

Write-UpdateLog ('Ende: ' + $finalStatus + $(if ($finalMessage) { ' - ' + $finalMessage } else { '' }))
exit $exitCode
