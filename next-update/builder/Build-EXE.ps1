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
    # Optional: echte Code-Signatur (Authenticode) gegen Viren-Fehlalarme.
    # Die haeufigste Ursache der Fehlalarme ist eine UNSIGNIERTE EXE. Wird eine
    # Signatur angeboten, signiert der Builder die fertige EXE VOR dem Smoke-Test
    # und laesst den Bau ohne gueltige Signatur scheitern. Ohne diese Angaben
    # bleibt der Bau exakt wie vorher (unsigniert). Anleitung mit Bezugsquellen
    # fuer Zertifikate: developer\docs\FALSE-POSITIVE-MELDUNG.md
    # -SignCertificatePath    Pfad zu einem .pfx/.p12 mit privatem Schluessel
    # -SignCertificateThumbprint  Alternative: Zertifikat aus Cert:\CurrentUser\My
    # -SignCertificatePassword    optional; sonst Umgebungsvariable
    #                             ARENABRIDGE_SIGN_PFX_PASSWORD oder sichere Abfrage
    # -SignTimestampUrl       Zeitstempel-Server; leer lassen = ohne Zeitstempel
    [string]$SignCertificatePath = '',
    [string]$SignCertificateThumbprint = '',
    [string]$SignCertificatePassword = '',
    [string]$SignTimestampUrl = 'http://timestamp.digicert.com',
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
        [string]$WindowTitle,
        [string]$Copyright,
        [string]$Trademark
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
    # Vollstaendige Dateiinformationen (Eigenschaften -> Details). Eine EXE ohne
    # Copyright-/Trademark-Angaben sieht fuer Viren-Heuristiken wie ein
    # zusammengebautes Wegwerf-Programm aus - das laesst sich vermeiden, ohne das
    # Verhalten der Bridge zu aendern.
    $installedParameters = (Get-Command Invoke-ps2exe -ErrorAction SilentlyContinue).Parameters
    if ($null -ne $installedParameters) {
        if ($installedParameters.ContainsKey('copyright') -and -not [string]::IsNullOrWhiteSpace($Copyright)) {
            $arguments['copyright'] = $Copyright
        }
        if ($installedParameters.ContainsKey('trademark') -and -not [string]::IsNullOrWhiteSpace($Trademark)) {
            $arguments['trademark'] = $Trademark
        }
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

function Invoke-FileReplaceWithoutBackup {
    param(
        [string]$SourcePath,
        [string]$DestinationPath
    )
    # Warum NICHT einfach [IO.File]::Replace($SourcePath,$DestinationPath,$null,$true)?
    # Windows PowerShell 5.1 wandelt $null beim Aufruf einer .NET-Methode mit
    # string-Parameter in eine LEERE ZEICHENKETTE um. File.Replace haelt "" fuer
    # einen Sicherungspfad und bricht sofort ab:
    #   Ausnahme beim Aufrufen von "Replace" mit 4 Argument(en):
    #   "Der Pfad hat ein ungueltiges Format." (The path is not of a legal form.)
    # Genau daran ist der 7.9.4-Bau zuletzt gescheitert - und zwar IMMER, sobald
    # release\ArenaRobloxBridge.exe schon vorhanden war (also ab dem zweiten Bau).
    # Ueber eine object[]-Argumentliste (Reflection) kommt $null dagegen als
    # echtes .NET-null an: die EXE wird atomar ersetzt und es entsteht KEINE
    # Sicherungsdatei im Ausgabeordner (7.9.4: dort liegt genau EINE Datei).
    $replaceMethod = [IO.File].GetMethod('Replace',[Type[]]@([System.String],[System.String],[System.String],[System.Boolean]))
    if ($null -eq $replaceMethod) {
        throw 'File.Replace(String, String, String, Boolean) is missing from this .NET runtime; nothing was published.'
    }
    try {
        [void]$replaceMethod.Invoke($null,[Object[]]@($SourcePath,$DestinationPath,$null,$true))
    } catch {
        # MethodInfo.Invoke verpackt die echte Ausnahme; hier soll die echte
        # Meldung (z. B. "wird von einem anderen Prozess verwendet") stehen.
        $inner = $_.Exception.InnerException
        if ($null -ne $inner) { throw $inner }
        throw
    }
}

function Test-AtomicReplaceSupport {
    # Kurzer Selbsttest VOR dem teuren Kompilieren: eine Datei atomar und ohne
    # Sicherungskopie ersetzen. Faellt das auf dieser Maschine aus, bricht der
    # Bau sofort mit einer verstaendlichen Meldung ab, statt erst nach Minuten
    # beim Einsetzen der fertigen EXE.
    $probeDirectory = Join-Path $env:TEMP ('ArenaRobloxBridge-replace-probe-' + [Guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $probeDirectory -Force | Out-Null
    try {
        $probeTarget = Join-Path $probeDirectory 'target.bin'
        $probeStaging = Join-Path $probeDirectory 'staging.bin'
        Write-Utf8NoBom $probeTarget 'alt'
        Write-Utf8NoBom $probeStaging 'neu'
        Invoke-FileReplaceWithoutBackup -SourcePath $probeStaging -DestinationPath $probeTarget
        if (-not (Test-Path -LiteralPath $probeTarget -PathType Leaf)) {
            throw 'The atomic replace probe deleted the target file instead of replacing it.'
        }
        if ([IO.File]::ReadAllText($probeTarget) -ne 'neu') {
            throw 'The atomic replace probe did not exchange the file contents.'
        }
        if (Test-Path -LiteralPath $probeStaging) {
            throw 'The atomic replace probe left the staging file behind; the replace was not atomic.'
        }
        if ([int](@(Get-ChildItem -LiteralPath $probeDirectory -File).Count) -ne 1) {
            throw 'The atomic replace probe created a backup copy; the output folder must stay at exactly one program file.'
        }
        Write-Step 'Atomic replace self-test passed: the build output can be published without leaving a backup copy.'
    } catch {
        throw ("The atomic replace self-test failed, so the EXE would not be publishable at the end of this build. " + $_.Exception.Message)
    } finally {
        Remove-Item -LiteralPath $probeDirectory -Recurse -Force -ErrorAction SilentlyContinue
    }
}

function Resolve-BridgeSigningCertificate {
    # Laedt das Signaturzertifikat VOR dem teuren Kompilieren: fehlt es, ist das
    # Passwort falsch oder fehlt der private Schluessel, bricht der Bau sofort
    # mit klarer Meldung ab. Ohne Zertifikatsangaben passiert hier nichts (der
    # Bau bleibt dann unsigniert wie vorher).
    param(
        [string]$CertificatePath,
        [string]$CertificateThumbprint,
        [string]$CertificatePassword,
        [switch]$NoPrompt
    )
    if ([string]::IsNullOrWhiteSpace($CertificatePath) -and [string]::IsNullOrWhiteSpace($CertificateThumbprint)) {
        return $null
    }
    if (-not [string]::IsNullOrWhiteSpace($CertificateThumbprint)) {
        $normalized = ($CertificateThumbprint -replace '[^0-9A-Fa-f]','').ToUpperInvariant()
        if ($normalized.Length -lt 40) {
            throw 'SignCertificateThumbprint must be a complete certificate thumbprint (40 hexadecimal characters).'
        }
        $found = @()
        foreach ($store in @('Cert:\CurrentUser\My','Cert:\LocalMachine\My')) {
            $found += @(Get-ChildItem -Path $store -ErrorAction SilentlyContinue | Where-Object { $_.Thumbprint -eq $normalized })
        }
        $certificate = $found | Where-Object { $_.HasPrivateKey } | Select-Object -First 1
        if ($null -eq $certificate) {
            throw ('No certificate with thumbprint ' + $normalized + ' and a private key was found in Cert:\CurrentUser\My or Cert:\LocalMachine\My. Install the code-signing certificate first and run the build again.')
        }
        return $certificate
    }
    if (-not (Test-Path -LiteralPath $CertificatePath -PathType Leaf)) {
        throw ('The code-signing certificate file was not found: ' + $CertificatePath)
    }
    $extension = [IO.Path]::GetExtension($CertificatePath).ToLowerInvariant()
    if ($extension -ne '.pfx' -and $extension -ne '.p12') {
        throw 'SignCertificatePath must point to a .pfx or .p12 file with the private key (a plain .cer cannot sign).'
    }
    if ([string]::IsNullOrEmpty($CertificatePassword)) {
        if (-not [string]::IsNullOrEmpty($env:ARENABRIDGE_SIGN_PFX_PASSWORD)) {
            $CertificatePassword = $env:ARENABRIDGE_SIGN_PFX_PASSWORD
        } elseif ($NoPrompt) {
            throw 'The .pfx password is missing. Set the environment variable ARENABRIDGE_SIGN_PFX_PASSWORD or pass -SignCertificatePassword.'
        } else {
            Write-Step 'Reading the .pfx password (input stays hidden)...'
            $secure = Read-Host -AsSecureString -Prompt 'Password of the code-signing .pfx'
            $CertificatePassword = [System.Net.NetworkCredential]::new('',$secure).Password
        }
    }
    try {
        $flags = [System.Security.Cryptography.X509Certificates.X509KeyStorageFlags]::Exportable
        $certificate = [System.Security.Cryptography.X509Certificates.X509Certificate2]::new($CertificatePath,$CertificatePassword,$flags)
    } catch {
        throw ('The .pfx could not be opened (wrong password or damaged file): ' + $_.Exception.Message)
    }
    if (-not $certificate.HasPrivateKey) {
        throw 'The .pfx does not contain a private key; this certificate cannot sign the EXE.'
    }
    return $certificate
}

function Invoke-BridgeCodeSign {
    # Signiert die fertige EXE VOR dem Smoke-Test und prueft die Signatur danach
    # unabhaengig nach. Ohne Zertifikat passiert nichts.
    param(
        [string]$ExecutablePath,
        $Certificate,
        [string]$TimestampUrl
    )
    if ($null -eq $Certificate) { return $null }
    if (-not (Test-Path -LiteralPath $ExecutablePath -PathType Leaf)) {
        throw ('The staged executable to sign is missing: ' + $ExecutablePath)
    }
    $signParameters = @{
        LiteralPath = $ExecutablePath
        Certificate = $Certificate
        HashAlgorithm = 'SHA256'
        Force = $true
        Confirm = $false
    }
    $timestampText = 'none'
    if (-not [string]::IsNullOrWhiteSpace($TimestampUrl)) {
        $signParameters['TimestampServer'] = $TimestampUrl
        $timestampText = $TimestampUrl
    }
    $signature = Set-AuthenticodeSignature @signParameters
    if ($null -eq $signature -or [string]$signature.Status -ne 'Valid') {
        $message = ''
        if ($null -ne $signature) { $message = [string]$signature.Status + ' ' + [string]$signature.StatusMessage }
        throw ('Code signing failed; the EXE was not published. ' + $message + ' Tip: without internet the timestamp server is unreachable - pass -SignTimestampUrl '''' to skip the timestamp.')
    }
    $verified = Get-AuthenticodeSignature -LiteralPath $ExecutablePath
    $verifiedStatus = ''
    if ($null -ne $verified) { $verifiedStatus = [string]$verified.Status }
    if ($verifiedStatus -ne 'Valid') {
        throw ('The freshly signed EXE does not carry a valid signature (status ' + $verifiedStatus + '); the output was not published.')
    }
    if ($null -ne $verified.SignerCertificate) {
        Write-Step ('Signed the staged EXE for ' + [string]$verified.SignerCertificate.Subject + ' (SHA-256, timestamp: ' + $timestampText + '). Antivirus engines and SmartScreen see a publisher instead of an unknown program.')
    } else {
        Write-Step ('Signed the staged EXE (SHA-256, timestamp: ' + $timestampText + ').')
    }
    return $verified
}

function Publish-LocalBuild {
    param(
        [string]$StagingPath,
        [string]$TargetPath
    )
    # Version 7.9.4: Der Ausgabeordner enthaelt genau EINE Datei - die neue
    # ArenaRobloxBridge.exe. Der frueher zusaetzlich abgelegte
    # "*.previous-<Zeitstempel>.exe"-Rest entfaellt; ersetzt wird atomar und
    # OHNE Sicherungskopie. Drei kurze Anlaeufe: direkt nach dem Smoke-Test
    # koennen Virenscanner oder der Explorer die neue Datei noch einen
    # Augenblick festhalten.
    $lastError = $null
    for ($attempt = 1; $attempt -le 3; $attempt++) {
        try {
            if (Test-Path -LiteralPath $TargetPath -PathType Leaf) {
                Invoke-FileReplaceWithoutBackup -SourcePath $StagingPath -DestinationPath $TargetPath
            } else {
                [IO.File]::Move($StagingPath,$TargetPath)
            }
            return
        } catch {
            $lastError = $_
            if ($attempt -lt 3) { Start-Sleep -Milliseconds 400 }
        }
    }
    $detail = ''
    if ($null -ne $lastError) {
        if ($null -ne $lastError.Exception) {
            $detail = [string]$lastError.Exception.Message
            if ([string]::IsNullOrWhiteSpace($detail) -and $null -ne $lastError.Exception.InnerException) {
                $detail = [string]$lastError.Exception.InnerException.Message
            }
        }
        if ([string]::IsNullOrWhiteSpace($detail)) { $detail = [string]$lastError }
    }
    throw ("Could not safely publish the local build output. Close every running ArenaRobloxBridge window and run Build-EXE.bat again. " + $detail)
}

function Remove-LegacyReleaseArtifacts {
    # Version 7.9.4: Frueher legte der Builder neben ArenaRobloxBridge.exe eine
    # zweite EXE (ArenaBridge-Diagnose.exe), einen Starter (Start-Diagnostic.bat),
    # eine zweite Pruefsummendatei und Backup-Kopien in release\ ab. Diese Reste
    # werden beim Bauen entfernt, damit dort genau eine EXE liegt.
    param([string]$Directory)
    if ([string]::IsNullOrWhiteSpace($Directory) -or -not (Test-Path -LiteralPath $Directory -PathType Container)) { return }
    $removed = New-Object System.Collections.Generic.List[string]
    $legacyNames = @(
        'ArenaBridge-Diagnose.exe',
        'ArenaBridge-Diagnose.exe.sha256',
        'ArenaBridge-Diagnose.building.exe',
        'ArenaRobloxBridge.building.exe',
        'Start-Diagnostic.bat'
    )
    foreach ($name in $legacyNames) {
        $path = Join-Path $Directory $name
        if (Test-Path -LiteralPath $path -PathType Leaf) {
            Remove-Item -LiteralPath $path -Force -ErrorAction SilentlyContinue
            if (-not (Test-Path -LiteralPath $path)) { $removed.Add($name) }
        }
    }
    foreach ($pattern in @('*.previous-*.exe')) {
        foreach ($old in @(Get-ChildItem -LiteralPath $Directory -Filter $pattern -File -ErrorAction SilentlyContinue)) {
            Remove-Item -LiteralPath $old.FullName -Force -ErrorAction SilentlyContinue
            if (-not (Test-Path -LiteralPath $old.FullName)) { $removed.Add($old.Name) }
        }
    }
    if ($removed.Count -gt 0) {
        Write-Step ("Removed " + [string]$removed.Count + ' leftover diagnostic/backup file(s) from the output folder: ' + ($removed -join ', ') + '. Only ArenaRobloxBridge.exe remains.')
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
$releaseDirectory = Join-Path $repoRoot 'release'
$betaReleaseDirectory = Join-Path $repoRoot 'beta-release'
$buildOutputDirectory = $releaseDirectory
if (-not [string]::IsNullOrWhiteSpace($OutputDirectory)) {
    $buildOutputDirectory = [IO.Path]::GetFullPath($OutputDirectory)
    if ($TestFixtureBuild) {
        $repoPrefix = $repoRoot.TrimEnd('\') + '\'
        if ($buildOutputDirectory.TrimEnd('\') -ieq $releaseDirectory.TrimEnd('\') -or $buildOutputDirectory.StartsWith($repoPrefix, [StringComparison]::OrdinalIgnoreCase)) {
            throw 'A test-fixture build must never write inside the repository (release\ is the publication folder).'
        }
        if ($Channel -ne 'beta') { throw 'A test-fixture build is only allowed for channel beta.' }
    }
}
if (-not [string]::IsNullOrWhiteSpace($TestFileVersion)) {
    if (-not $TestFixtureBuild) { throw '-TestFileVersion is only accepted together with -TestFixtureBuild.' }
    if ($TestFileVersion -cnotmatch '^\d+\.\d+\.\d+\.\d+$') { throw '-TestFileVersion must be a four-part numeric version such as 7.7.1.0.' }
}
$exePath = Join-Path $buildOutputDirectory 'ArenaRobloxBridge.exe'

foreach ($requiredPath in @($sourcePath,$versionPath,$parseGatePath,$iconPath,$titleArtworkPath,$programLogoPath,$backgroundImagePath)) {
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
    $confirmation = Read-Host 'Type RELEASE STABLE to overwrite release\ArenaRobloxBridge.exe'
    if ($confirmation -cne 'RELEASE STABLE') { throw 'Stable build cancelled.' }
}

$windowsPowerShell = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
if (-not (Test-Path -LiteralPath $windowsPowerShell -PathType Leaf)) {
    throw 'Windows PowerShell 5.1 was not found. Run this build from a Windows installation with PowerShell.'
}
# 7.9.4-Hotfix: Vor dem teuren Kompilieren pruefen, ob der atomare Austausch der
# fertigen EXE auf dieser Maschine ueberhaupt moeglich ist (kein $null-Leerstring,
# keine Sicherungskopie im Ausgabeordner).
Test-AtomicReplaceSupport
# 8.0.0: Ein eventuell vorhandenes Signaturzertifikat ebenfalls VOR dem teuren
# Kompilieren aufloesen (fehlendes Zertifikat, falsches Passwort, fehlender
# privater Schluessel = sofortiger, klarer Abbruch statt Zeitverlust).
# Ohne -SignCertificatePath/-SignCertificateThumbprint wird die Umgebungsvariable
# ARENABRIDGE_SIGN_PFX ausgewertet (Pfad zum .pfx). Damit funktioniert auch der
# normale Weg ueber Build-EXE.bat: Zertifikat einmal als Umgebungsvariable
# hinterlegen, danach wie gewohnt bauen. Passwort: -SignCertificatePassword,
# ARENABRIDGE_SIGN_PFX_PASSWORD oder die sichere Abfrage.
if ([string]::IsNullOrWhiteSpace($SignCertificatePath) -and [string]::IsNullOrWhiteSpace($SignCertificateThumbprint) -and -not [string]::IsNullOrWhiteSpace($env:ARENABRIDGE_SIGN_PFX)) {
    $SignCertificatePath = $env:ARENABRIDGE_SIGN_PFX
    Write-Step ('Using the code-signing certificate from the environment variable ARENABRIDGE_SIGN_PFX: ' + $SignCertificatePath)
}
$signingCertificate = Resolve-BridgeSigningCertificate -CertificatePath $SignCertificatePath -CertificateThumbprint $SignCertificateThumbprint -CertificatePassword $SignCertificatePassword -NoPrompt:$NonInteractive
if ($null -ne $signingCertificate) {
    Write-Step ('Code signing is enabled: ' + [string]$signingCertificate.Subject + ' (thumbprint ' + [string]$signingCertificate.Thumbprint + '). Without a valid signature no build is published.')
} else {
    Write-Step 'Code signing is NOT enabled: the EXE will be unsigned, and antivirus engines and SmartScreen may warn. See developer\docs\FALSE-POSITIVE-MELDUNG.md'
}
Write-Step 'Running the real PowerShell parser before compilation...'
& $windowsPowerShell -NoLogo -NoProfile -ExecutionPolicy Bypass -File $parseGatePath -Path $sourcePath
if ($LASTEXITCODE -ne 0) { throw 'PowerShell parse gate failed; no EXE was produced.' }
# Version 7.9.0: Der Selbst-Update-Helfer ist entfernt; die EXE enthaelt keinen eigenen Updater mehr.

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
$stagingExePath = Join-Path $buildOutputDirectory 'ArenaRobloxBridge.building.exe'
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
    # Version 7.9.0: Die Version steht in der EXE genau dort, wo der Platzhalter
    # __ARENA_BUILD_VERSION__ im Quelltext steht (Dateiversion, Anzeige, Diagnose).
    $versionMarker = '__ARENA_BUILD_VERSION__'
    if (([regex]::Matches($sourceText, [regex]::Escape($versionMarker))).Count -lt 1) {
        throw 'The version placeholder __ARENA_BUILD_VERSION__ is missing from ArenaBridge.ps1.'
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
    # Pruefe nur die echte Zuweisung ($script:BackgroundImageBase64 = '__ARENA_...'),
    # nicht den blossen Platzhalter-Text: der steht absichtlich auch in den
    # Laufzeit-Pruefungen des Smoke-Tests (-eq '__ARENA_...') und wuerde sonst
    # faelschlich als "nicht ersetzt" gemeldet.
    if ($preparedSource.Contains($backgroundMarker)) {
        throw 'Background placeholder was not replaced: the $script:BackgroundImageBase64 assignment still holds __ARENA_BACKGROUND_IMAGE_BASE64__.'
    }
    $preparedSource = $preparedSource.Replace($versionMarker, $BuildVersion)
    if ($preparedSource.Contains($versionMarker)) { throw 'Version placeholder was not replaced in the compile copy.' }
    [IO.File]::WriteAllText($preparedSourcePath,$preparedSource,[Text.UTF8Encoding]::new($true))
    Write-Step ("Prepared self-contained source with title artwork (" + [string]$titleArtworkBytes.Length + " bytes), the program logo (" + [string]$programLogoBytes.Length + " bytes) and the window background (" + [string]$backgroundBytes.Length + " bytes). No external runtime image is required.")
    Write-Step 'Re-running the real Windows PowerShell parser against the exact embedded compile copy...'
    & $windowsPowerShell -NoLogo -NoProfile -ExecutionPolicy Bypass -File $parseGatePath -Path $preparedSourcePath
    if ($LASTEXITCODE -ne 0) { throw 'PowerShell parse gate failed for the embedded compile copy; no EXE was produced.' }

    if (Test-Path -LiteralPath $stagingExePath) { Remove-Item -LiteralPath $stagingExePath -Force }
    $numericVersion = $sourceVersion + '.0'
    if (-not [string]::IsNullOrWhiteSpace($TestFileVersion)) { $numericVersion = $TestFileVersion }
    # Version 7.9.4: GENAU EINE EXE. Der frueher zusaetzlich gebaute
    # Konsolen-Diagnose-Zwilling (ArenaBridge-Diagnose.exe) entfaellt.
    Write-Step ("Compiling " + $BuildVersion + ' for channel ' + $Channel + ' (hidden-console release EXE)...')
    Invoke-BridgeCompiler -InputPath $preparedSourcePath -OutputPath $stagingExePath -IconPath $iconPath -NumericVersion $numericVersion -NoConsole $true -WindowTitle 'Arena Roblox Bridge' -Copyright 'Copyright (C) 2026 MertaStudios' -Trademark 'Arena Roblox Bridge'

    # 8.0.0: Optionale Authenticode-Signatur VOR dem Smoke-Test, damit genau die
    # Datei geprueft wird, die danach eingesetzt wird. Ohne Zertifikat aendert
    # sich am Ablauf nichts.
    $signatureInfo = Invoke-BridgeCodeSign -ExecutablePath $stagingExePath -Certificate $signingCertificate -TimestampUrl $SignTimestampUrl

    Test-StagedExecutable -ExecutablePath $stagingExePath -ReportPath $smokeReportPath

    # Die neue EXE wird erst nach dem bestandenen Smoke-Test eingesetzt
    # (atomarer Austausch, kein zweites Programm als Beifang).
    Publish-LocalBuild -StagingPath $stagingExePath -TargetPath $exePath
    if ($buildOutputDirectory -ieq $releaseDirectory) {
        Remove-LegacyReleaseArtifacts -Directory $buildOutputDirectory
    }

    $file = Get-Item -LiteralPath $exePath
    $sha256 = (Get-FileHash -LiteralPath $exePath -Algorithm SHA256).Hash.ToLowerInvariant()
    $iconSha256 = (Get-FileHash -LiteralPath $iconPath -Algorithm SHA256).Hash.ToLowerInvariant()
    $artworkSha256 = (Get-FileHash -LiteralPath $titleArtworkPath -Algorithm SHA256).Hash.ToLowerInvariant()
    $programLogoSha256 = (Get-FileHash -LiteralPath $programLogoPath -Algorithm SHA256).Hash.ToLowerInvariant()
    $backgroundSha256 = (Get-FileHash -LiteralPath $backgroundImagePath -Algorithm SHA256).Hash.ToLowerInvariant()
    $metadata = [ordered]@{
        # Version 7.9.0: einfaches Selbst-Update. Die GitHub Action schreibt latest.json.
        # Version 7.9.4: Schema 4 - nur noch eine EXE (keine Diagnose-Dateien mehr).
        schemaVersion = 4
        publishTool = '.github/workflows/publish-bridge.yml (writes next-update/release/latest.json)'
        channel = $Channel
        version = $BuildVersion
        sourceVersion = $sourceVersion
        fileName = 'ArenaRobloxBridge.exe'
        sizeBytes = [long]$file.Length
        sha256 = $sha256
        # Version 7.9.4: Genau eine EXE im Ausgabeordner. Die frueheren Felder
        # diagnosticFileName/diagnosticSizeBytes/diagnosticSha256 entfallen.
        outputFileCount = 1
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
        testFixtureBuild = [bool]$TestFixtureBuild
        builtAtUtc = [DateTime]::UtcNow.ToString('o')
        published = $false
        # 8.0.0: Signaturzustand und vollstaendige Dateiinformationen - beides
        # senkt die Zahl der Viren-Fehlalarme (siehe FALSE-POSITIVE-MELDUNG.md).
        signedWithAuthenticode = [bool]($null -ne $signatureInfo)
        signerSubject = $(if ($null -ne $signatureInfo -and $null -ne $signatureInfo.SignerCertificate) { [string]$signatureInfo.SignerCertificate.Subject } else { '' })
        signerThumbprint = $(if ($null -ne $signatureInfo -and $null -ne $signatureInfo.SignerCertificate) { [string]$signatureInfo.SignerCertificate.Thumbprint } else { '' })
        signTimestampUrl = $SignTimestampUrl
        fileCopyright = 'Copyright (C) 2026 MertaStudios'
        fileTrademark = 'Arena Roblox Bridge'
        note = 'Lokaler Testbau. Veroeffentlicht wird nur durch Einchecken der getesteten Datei als next-update/release/ArenaRobloxBridge.exe.'
    }
    $metadataPath = Join-Path $buildOutputDirectory 'release-metadata.json'
    Write-Utf8NoBom $metadataPath ($metadata | ConvertTo-Json -Depth 6)
    Write-Utf8NoBom (Join-Path $buildOutputDirectory 'ArenaRobloxBridge.exe.sha256') ($sha256 + '  ArenaRobloxBridge.exe' + [Environment]::NewLine)

    Write-Step 'LOCAL TEST BUILD COMPLETED. No GitHub upload/release or update-channel manifest was changed.'
    Write-Host ''
    Write-Host 'ONE FILE WAS BUILT - THERE IS NO SECOND EXE ANY MORE:' -ForegroundColor Green
    Write-Host ('  ' + $exePath) -ForegroundColor White
    if ($null -ne $signatureInfo -and $null -ne $signatureInfo.SignerCertificate) {
        Write-Host ('Signed for: ' + [string]$signatureInfo.SignerCertificate.Subject) -ForegroundColor Green
        Write-Host 'A valid signature is the most effective protection against antivirus false positives.'
    } else {
        Write-Host 'This EXE is NOT signed (code signing is optional).' -ForegroundColor Yellow
        Write-Host 'Antivirus engines can report a false positive for unsigned, compiled PowerShell programs.'
        Write-Host 'What to do about it: next-update\developer\docs\FALSE-POSITIVE-MELDUNG.md'
    }
    Write-Host 'If this EXE shows no window, close every other ArenaBridge window and start it again.' -ForegroundColor Yellow
    Write-Host ('Start report: ' + (Join-Path $env:LOCALAPPDATA 'START-CHECK.txt'))
    Write-Host ('Start log:    ' + (Join-Path $env:LOCALAPPDATA 'ArenaRobloxBridge\bin\startup-diagnose.txt'))
    Write-Host ('Local-only metadata: ' + $metadataPath)
    Write-Host 'No users were updated. Only after explicit approval may the exact tested ArenaRobloxBridge.exe be uploaded to next-update/release/ArenaRobloxBridge.exe; do not upload the local metadata.'
} finally {
    if ($stagingExePath -and (Test-Path -LiteralPath $stagingExePath)) {
        Remove-Item -LiteralPath $stagingExePath -Force -ErrorAction SilentlyContinue
    }
    if (Test-Path -LiteralPath $tempBuildDirectory) {
        Remove-Item -LiteralPath $tempBuildDirectory -Recurse -Force -ErrorAction SilentlyContinue
    }
}
