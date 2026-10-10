[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('beta','stable')]
    [string]$Channel,

    [string]$ManifestPath = '',
    [string]$ManifestUrl = '',
    [string]$InstallDirectory = (Join-Path $env:LOCALAPPDATA 'ArenaRobloxBridge\app'),
    [int]$WaitForProcessId = 0,
    [switch]$StartAfterUpdate
)

$ErrorActionPreference = 'Stop'
$script:UpdaterVersion = '1.0.0'
$script:MaxManifestBytes = 1048576
$script:MaxArtifactBytes = 209715200

function Write-UpdateLog([string]$Text) {
    Write-Host ("[ArenaBridge updater] " + $Text)
}

function Test-GitHubHost([string]$HostName) {
    $hostValue = ([string]$HostName).Trim('.').ToLowerInvariant()
    return ($hostValue -eq 'github.com' -or $hostValue -eq 'githubusercontent.com' -or $hostValue.EndsWith('.githubusercontent.com'))
}

function Test-ApprovedGitHubUri([Uri]$Uri) {
    if ($null -eq $Uri) { return $false }
    return ($Uri.Scheme -eq 'https' -and $Uri.IsDefaultPort
        -and [string]::IsNullOrEmpty($Uri.UserInfo)
        -and [string]::IsNullOrEmpty($Uri.Fragment)
        -and (Test-GitHubHost $Uri.Host))
}

function Get-ApprovedGitHubDownload {
    param(
        [Parameter(Mandatory = $true)][Uri]$Uri,
        [Parameter(Mandatory = $true)][long]$MaxBytes,
        [string]$DestinationPath = '',
        [long]$ExpectedBytes = 0,
        [int]$MaxRedirects = 5,
        [int]$TimeoutSeconds = 180
    )
    if ($MaxBytes -le 0) { throw 'MaxBytes must be positive.' }
    if ($ExpectedBytes -lt 0 -or $ExpectedBytes -gt $MaxBytes) { throw 'ExpectedBytes is outside the permitted download limit.' }
    if ($MaxRedirects -lt 0 -or $MaxRedirects -gt 10) { throw 'MaxRedirects must be between 0 and 10.' }
    if ($TimeoutSeconds -le 0 -or $TimeoutSeconds -gt 600) { throw 'TimeoutSeconds must be between 1 and 600.' }
    if (-not (Test-ApprovedGitHubUri $Uri)) { throw 'Download URL must use HTTPS on an approved GitHub host and the default HTTPS port.' }

    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    $deadlineUtc = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
    $requestTimeoutMs = [Math]::Min(30000,($TimeoutSeconds * 1000))
    $currentUri = $Uri
    $redirectCount = 0
    while ($true) {
        if ([DateTime]::UtcNow -gt $deadlineUtc) { throw ("GitHub download exceeded the " + [string]$TimeoutSeconds + '-second timeout.') }
        if (-not (Test-ApprovedGitHubUri $currentUri)) { throw 'A redirect left the approved GitHub HTTPS host set; download refused.' }
        $response = $null
        $inputStream = $null
        $outputStream = $null
        $memoryStream = $null
        $createdDestination = $false
        $completed = $false
        try {
            $request = [System.Net.HttpWebRequest]::Create($currentUri)
            $request.Method = 'GET'
            $request.AllowAutoRedirect = $false
            $request.AutomaticDecompression = [System.Net.DecompressionMethods]::None
            $request.Timeout = $requestTimeoutMs
            $request.ReadWriteTimeout = [Math]::Min(30000,$requestTimeoutMs)
            $request.KeepAlive = $false
            try { $response = $request.GetResponse() }
            catch [System.Net.WebException] {
                if ($null -ne $_.Exception.Response) { $response = $_.Exception.Response }
                else { throw }
            }
            if ($null -eq $response) { throw 'GitHub returned no HTTP response.' }
            $statusCode = [int]$response.StatusCode
            if ($statusCode -eq 301 -or $statusCode -eq 302 -or $statusCode -eq 303 -or $statusCode -eq 307 -or $statusCode -eq 308) {
                if ($redirectCount -ge $MaxRedirects) { throw 'GitHub download exceeded the redirect limit.' }
                $location = [string]$response.Headers['Location']
                if ([string]::IsNullOrWhiteSpace($location)) { throw 'GitHub redirect did not include a Location header.' }
                $nextUri = $null
                if (-not [Uri]::TryCreate($currentUri,$location,[ref]$nextUri)) { throw 'GitHub returned an invalid redirect URL.' }
                if (-not (Test-ApprovedGitHubUri $nextUri)) { throw 'GitHub redirect target is outside the approved HTTPS host set.' }
                $currentUri = $nextUri
                $redirectCount++
                continue
            }
            if ($statusCode -lt 200 -or $statusCode -ge 300) { throw ("Approved GitHub host returned HTTP " + [string]$statusCode + '.') }

            $declaredLength = [long]$response.ContentLength
            if ($declaredLength -gt $MaxBytes) { throw ("Response Content-Length exceeds the " + [string]$MaxBytes + '-byte limit.') }
            if ($declaredLength -eq 0) { throw 'GitHub returned an empty download.' }
            if ($ExpectedBytes -gt 0 -and $declaredLength -ge 0 -and $declaredLength -ne $ExpectedBytes) {
                throw 'Response Content-Length does not match the expected manifest size.'
            }
            if ([string]::IsNullOrWhiteSpace($DestinationPath)) {
                $memoryStream = New-Object System.IO.MemoryStream
                $outputStream = $memoryStream
            } else {
                $outputStream = [IO.File]::Open($DestinationPath,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
                $createdDestination = $true
            }
            $inputStream = $response.GetResponseStream()
            if ($null -eq $inputStream) { throw 'GitHub response did not contain a readable body.' }
            $buffer = [byte[]]::new(65536)
            $receivedBytes = [long]0
            while (($readCount = $inputStream.Read($buffer,0,$buffer.Length)) -gt 0) {
                if ([DateTime]::UtcNow -gt $deadlineUtc) { throw ("GitHub download exceeded the " + [string]$TimeoutSeconds + '-second timeout.') }
                $receivedBytes += [long]$readCount
                if ($receivedBytes -gt $MaxBytes) { throw ("Streamed response exceeded the " + [string]$MaxBytes + '-byte limit.') }
                if ($ExpectedBytes -gt 0 -and $receivedBytes -gt $ExpectedBytes) { throw 'Streamed response exceeds the expected manifest size.' }
                if ($declaredLength -ge 0 -and $receivedBytes -gt $declaredLength) { throw 'Response body exceeds its declared Content-Length.' }
                $outputStream.Write($buffer,0,$readCount)
            }
            if ($receivedBytes -le 0) { throw 'GitHub returned an empty download.' }
            if ($declaredLength -ge 0 -and $receivedBytes -ne $declaredLength) { throw 'Response body ended before the declared Content-Length.' }
            if ($ExpectedBytes -gt 0 -and $receivedBytes -ne $ExpectedBytes) { throw 'Downloaded size does not match the channel manifest.' }

            if (-not [string]::IsNullOrWhiteSpace($DestinationPath)) {
                $outputStream.Flush()
                $outputStream.Dispose()
                $outputStream = $null
                $completed = $true
                return [pscustomobject]@{ Path = $DestinationPath; SizeBytes = $receivedBytes; Uri = $currentUri.AbsoluteUri }
            }
            $contentBytes = $memoryStream.ToArray()
            $completed = $true
            return [pscustomobject]@{ Bytes = $contentBytes; SizeBytes = $receivedBytes; Uri = $currentUri.AbsoluteUri }
        } finally {
            if ($null -ne $inputStream) { $inputStream.Dispose() }
            if ($null -ne $outputStream) { $outputStream.Dispose() }
            if ($null -ne $memoryStream) { $memoryStream.Dispose() }
            if ($null -ne $response) { $response.Close() }
            if ($createdDestination -and -not $completed -and (Test-Path -LiteralPath $DestinationPath -PathType Leaf)) {
                Remove-Item -LiteralPath $DestinationPath -Force -ErrorAction SilentlyContinue
            }
        }
    }
}

function Test-UpdateVersion([string]$Value) {
    return ($Value -match '^\d+\.\d+\.\d+(?:-[0-9A-Za-z]+(?:[.-][0-9A-Za-z]+)*)?$')
}

function Convert-UpdateVersion([string]$Value) {
    if (-not (Test-UpdateVersion $Value)) { throw ("Invalid semantic version: " + $Value) }
    $parts = $Value.Split('-',2)
    $core = $parts[0].Split('.') | ForEach-Object { [int64]$_ }
    $pre = @()
    if ($parts.Count -gt 1) { $pre = @($parts[1] -split '[.-]') }
    return [pscustomobject]@{ Core=$core; PreRelease=$pre; Original=$Value }
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
    $limit = [Math]::Max($a.PreRelease.Count,$b.PreRelease.Count)
    for ($i = 0; $i -lt $limit; $i++) {
        if ($i -ge $a.PreRelease.Count) { return -1 }
        if ($i -ge $b.PreRelease.Count) { return 1 }
        $leftId = [string]$a.PreRelease[$i]
        $rightId = [string]$b.PreRelease[$i]
        $leftNumber = [int64]0; $rightNumber = [int64]0
        $leftNumeric = [int64]::TryParse($leftId,[ref]$leftNumber)
        $rightNumeric = [int64]::TryParse($rightId,[ref]$rightNumber)
        if ($leftNumeric -and $rightNumeric) {
            if ($leftNumber -gt $rightNumber) { return 1 }
            if ($leftNumber -lt $rightNumber) { return -1 }
        } elseif ($leftNumeric) { return -1 }
        elseif ($rightNumeric) { return 1 }
        else {
            $cmp = [string]::Compare($leftId,$rightId,[StringComparison]::OrdinalIgnoreCase)
            if ($cmp -gt 0) { return 1 }
            if ($cmp -lt 0) { return -1 }
        }
    }
    return 0
}

function Write-Utf8NoBom([string]$Path, [string]$Text) {
    [IO.File]::WriteAllText($Path,$Text,[Text.UTF8Encoding]::new($false))
}

function Get-ChannelManifest {
    param([string]$Path,[string]$Url,[string]$SelectedChannel)
    if (-not [string]::IsNullOrWhiteSpace($Path) -and -not [string]::IsNullOrWhiteSpace($Url)) {
        throw 'Pass either -ManifestPath or -ManifestUrl, not both.'
    }
    if ([string]::IsNullOrWhiteSpace($Path) -and [string]::IsNullOrWhiteSpace($Url)) {
        $Path = Join-Path (Join-Path (Split-Path -Parent $PSScriptRoot) 'channels') ($SelectedChannel + '.json')
    }
    if (-not [string]::IsNullOrWhiteSpace($Url)) {
        $uri = $null
        if (-not [Uri]::TryCreate($Url,[UriKind]::Absolute,[ref]$uri) -or -not (Test-ApprovedGitHubUri $uri)) {
            throw 'ManifestUrl must use HTTPS on github.com or githubusercontent.com, the default HTTPS port, and no embedded credentials.'
        }
        $manifestDownload = Get-ApprovedGitHubDownload -Uri $uri -MaxBytes $script:MaxManifestBytes -TimeoutSeconds 30
        $raw = [Text.Encoding]::UTF8.GetString([byte[]]$manifestDownload.Bytes)
        if ($raw.Length -gt 0 -and $raw[0] -eq [char]0xFEFF) { $raw = $raw.Substring(1) }
    } else {
        if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw ("Manifest file not found: " + $Path) }
        $manifestFile = Get-Item -LiteralPath $Path
        if ([long]$manifestFile.Length -gt $script:MaxManifestBytes) { throw ("Manifest exceeds the " + [string]$script:MaxManifestBytes + '-byte limit.') }
        $raw = Get-Content -LiteralPath $Path -Raw -Encoding UTF8
    }
    try { return ($raw | ConvertFrom-Json -ErrorAction Stop) }
    catch { throw ("Channel manifest is not valid JSON: " + $_.Exception.Message) }
}

function Wait-ForTargetProcessToExit([string]$TargetPath,[int]$ProcessId) {
    $normalizedTarget = [IO.Path]::GetFullPath($TargetPath)
    $bridgeProcesses = @(Get-Process -Name 'ArenaBridge' -ErrorAction SilentlyContinue)
    if ($ProcessId -gt 0) {
        $requested = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
        if ($null -ne $requested) {
            if ($requested.ProcessName -ne 'ArenaBridge') {
                throw ("PID " + $ProcessId + ' is not an ArenaBridge process; refusing to wait on an unrelated process.')
            }
            $processPath = ''
            try { $processPath = [IO.Path]::GetFullPath([string]$requested.Path) } catch {}
            if ($processPath -and -not $processPath.Equals($normalizedTarget,[StringComparison]::OrdinalIgnoreCase)) {
                throw ("PID " + $ProcessId + ' belongs to a different ArenaBridge.exe installation.')
            }
            Write-UpdateLog ("Waiting for ArenaBridge PID " + $ProcessId + ' to exit; the updater will not terminate it.')
            try { Wait-Process -Id $ProcessId -Timeout 180 -ErrorAction Stop } catch {
                $stillRunning = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
                if ($null -ne $stillRunning) { throw 'The running Bridge did not exit within 180 seconds; no files were changed.' }
            }
        }
    }
    $remaining = @(Get-Process -Name 'ArenaBridge' -ErrorAction SilentlyContinue)
    foreach ($process in $remaining) {
        if ($ProcessId -gt 0 -and $process.Id -eq $ProcessId) { continue }
        $processPath = ''
        try { $processPath = [IO.Path]::GetFullPath([string]$process.Path) } catch {}
        if (-not $processPath -or $processPath.Equals($normalizedTarget,[StringComparison]::OrdinalIgnoreCase)) {
            throw ("ArenaBridge PID " + $process.Id + ' is still running. Close the other instance; the updater never kills or overwrites a running executable.')
        }
    }
}

if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
    throw 'The channel updater is Windows-only.'
}
if ([string]::IsNullOrWhiteSpace($InstallDirectory)) { throw 'InstallDirectory is empty.' }
$InstallDirectory = [IO.Path]::GetFullPath($InstallDirectory)
$manifest = Get-ChannelManifest -Path $ManifestPath -Url $ManifestUrl -SelectedChannel $Channel

if ([int]$manifest.schemaVersion -ne 1) { throw 'Unsupported channel-manifest schemaVersion.' }
if ([string]$manifest.channel -cne $Channel) { throw ("Manifest channel does not match requested channel '" + $Channel + "'.") }
if ($manifest.enabled -ne $true) {
    Write-UpdateLog ("Channel '" + $Channel + "' is disabled; no update is available and no files were changed.")
    exit 0
}
if (-not (Test-UpdateVersion ([string]$manifest.version))) { throw 'Enabled manifest must contain a valid version (x.y.z or x.y.z-beta.n).' }
if ($Channel -eq 'stable' -and [string]$manifest.version -match '-') { throw 'Stable channel manifests cannot publish prerelease versions.' }
if ([string]$manifest.minimumUpdaterVersion -and (Compare-UpdateVersion $script:UpdaterVersion ([string]$manifest.minimumUpdaterVersion)) -lt 0) {
    throw ("This updater is too old. Required: " + [string]$manifest.minimumUpdaterVersion + '; installed: ' + $script:UpdaterVersion)
}
$artifact = $manifest.artifact
if ($null -eq $artifact -or [string]$artifact.fileName -cne 'ArenaBridge.exe') { throw 'Manifest artifact.fileName must be exactly ArenaBridge.exe.' }
if ([string]$artifact.sha256 -notmatch '^[A-Fa-f0-9]{64}$') { throw 'Manifest artifact.sha256 must contain 64 hexadecimal characters.' }
$artifactUri = $null
if (-not [Uri]::TryCreate([string]$artifact.url,[UriKind]::Absolute,[ref]$artifactUri) -or -not (Test-ApprovedGitHubUri $artifactUri)) {
    throw 'Artifact URL must use HTTPS on github.com or githubusercontent.com, the default HTTPS port, and no embedded credentials.'
}
if ([long]$artifact.sizeBytes -le 0 -or [long]$artifact.sizeBytes -gt $script:MaxArtifactBytes) {
    throw ("Manifest artifact.sizeBytes must be between 1 and " + $script:MaxArtifactBytes + ' bytes.')
}

$notes = @()
try { $notes = @($manifest.notes | Where-Object { -not [string]::IsNullOrWhiteSpace([string]$_) }) } catch {}
if ($notes.Count -gt 0) { Write-UpdateLog ($notes -join [Environment]::NewLine) }
$targetPath = Join-Path $InstallDirectory 'ArenaBridge.exe'
$statePath = Join-Path $InstallDirectory 'update-state.json'
$workDirectory = Join-Path $InstallDirectory '.arena-update'
if (-not (Test-Path -LiteralPath $InstallDirectory -PathType Container)) {
    New-Item -ItemType Directory -Path $InstallDirectory -Force | Out-Null
}
if (-not (Test-Path -LiteralPath $workDirectory -PathType Container)) {
    New-Item -ItemType Directory -Path $workDirectory -Force | Out-Null
}
$lockPath = Join-Path $workDirectory 'update.lock'
$lockStream = $null
try { $lockStream = [IO.File]::Open($lockPath,[IO.FileMode]::CreateNew,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None) }
catch { throw 'Another update is already running (update.lock exists). Close the updater and retry after confirming no process is active.' }
try {
    if (Test-Path -LiteralPath $statePath -PathType Leaf) {
        try {
            $state = Get-Content -LiteralPath $statePath -Raw -Encoding UTF8 | ConvertFrom-Json -ErrorAction Stop
            if ($null -eq $state -or [int]$state.schemaVersion -ne 1) {
                throw 'Local update-state schemaVersion is missing or unsupported.'
            }
            if ([string]$state.channel -cne 'beta' -and [string]$state.channel -cne 'stable') {
                throw 'Local update-state channel is invalid.'
            }
            if (-not (Test-UpdateVersion ([string]$state.version))) {
                throw 'Local update-state version is invalid.'
            }
            $order = Compare-UpdateVersion ([string]$manifest.version) ([string]$state.version)
            if ($order -eq 0 -and [string]$state.channel -ceq $Channel) {
                Write-UpdateLog ("Version " + [string]$manifest.version + ' is already installed in channel ' + $Channel + '.')
                exit 0
            }
            if ($order -lt 0) {
                throw ("Refusing downgrade from " + [string]$state.version + ' on channel ' + [string]$state.channel + ' to ' + [string]$manifest.version + ' on channel ' + $Channel + '.')
            }
        } catch {
            if ($_.Exception.Message -like 'Refusing downgrade*') { throw }
            throw ("Local update-state file is unreadable or invalid; refusing to update without trustworthy version history. " + $_.Exception.Message)
        }
    }

    Wait-ForTargetProcessToExit -TargetPath $targetPath -ProcessId $WaitForProcessId
    $stagingPath = Join-Path $workDirectory 'ArenaBridge.exe.new'
    if (Test-Path -LiteralPath $stagingPath) { Remove-Item -LiteralPath $stagingPath -Force }
    Write-UpdateLog ("Downloading version " + [string]$manifest.version + ' from the configured GitHub release asset...')
    $downloadResult = Get-ApprovedGitHubDownload -Uri $artifactUri -DestinationPath $stagingPath -MaxBytes $script:MaxArtifactBytes -ExpectedBytes ([long]$artifact.sizeBytes) -TimeoutSeconds 180
    $downloadedFile = Get-Item -LiteralPath $stagingPath
    if ($downloadedFile.Length -ne [long]$artifact.sizeBytes -or $downloadedFile.Length -gt $script:MaxArtifactBytes) {
        Remove-Item -LiteralPath $stagingPath -Force -ErrorAction SilentlyContinue
        throw ("Downloaded size does not match the manifest (expected " + [string]$artifact.sizeBytes + ', got ' + [string]$downloadedFile.Length + ').')
    }
    $downloadedHash = (Get-FileHash -LiteralPath $stagingPath -Algorithm SHA256).Hash.ToLowerInvariant()
    if (-not $downloadedHash.Equals(([string]$artifact.sha256).ToLowerInvariant(),[StringComparison]::Ordinal)) {
        Remove-Item -LiteralPath $stagingPath -Force -ErrorAction SilentlyContinue
        throw 'Downloaded SHA-256 does not match the channel manifest; the existing EXE was not changed.'
    }

    # Re-check immediately before replacement; never terminate the application.
    Wait-ForTargetProcessToExit -TargetPath $targetPath -ProcessId 0
    $backupPath = Join-Path $InstallDirectory ('ArenaBridge.exe.previous-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
    try {
        if (Test-Path -LiteralPath $targetPath -PathType Leaf) {
            [IO.File]::Replace($stagingPath,$targetPath,$backupPath,$true)
        } else {
            [IO.File]::Move($stagingPath,$targetPath)
        }
        $installedHash = (Get-FileHash -LiteralPath $targetPath -Algorithm SHA256).Hash.ToLowerInvariant()
        if (-not $installedHash.Equals($downloadedHash,[StringComparison]::Ordinal)) { throw 'Installed file hash changed during replacement.' }
    } catch {
        if (Test-Path -LiteralPath $backupPath) {
            if (Test-Path -LiteralPath $targetPath) {
                $rejectedPath = Join-Path $workDirectory ('ArenaBridge.exe.rejected-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff'))
                [IO.File]::Move($targetPath,$rejectedPath)
            }
            [IO.File]::Move($backupPath,$targetPath)
        }
        throw ("Safe replacement failed; rollback was attempted. " + $_.Exception.Message)
    }

    $state = [ordered]@{
        schemaVersion = 1
        channel = $Channel
        version = [string]$manifest.version
        sha256 = $downloadedHash
        installedAtUtc = [DateTime]::UtcNow.ToString('o')
        manifestUrl = if ($ManifestUrl) { [string]$ManifestUrl } else { '' }
    }
    $stateTemp = $statePath + '.new'
    Write-Utf8NoBom $stateTemp ($state | ConvertTo-Json -Depth 6)
    if (Test-Path -LiteralPath $statePath) {
        $stateBackup = $statePath + '.previous'
        if (Test-Path -LiteralPath $stateBackup) { Remove-Item -LiteralPath $stateBackup -Force }
        [IO.File]::Replace($stateTemp,$statePath,$stateBackup,$true)
    } else {
        [IO.File]::Move($stateTemp,$statePath)
    }
    Write-UpdateLog ("Installed " + [string]$manifest.version + ' on channel ' + $Channel + '. Previous executable: ' + $(if (Test-Path -LiteralPath $backupPath) { $backupPath } else { 'none' }))
    if ($StartAfterUpdate) { Start-Process -FilePath $targetPath }
} finally {
    if ($null -ne $lockStream) { $lockStream.Dispose() }
    try { if (Test-Path -LiteralPath $lockPath) { Remove-Item -LiteralPath $lockPath -Force -ErrorAction SilentlyContinue } } catch {}
}
