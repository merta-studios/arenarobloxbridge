# ==============================================================================
# REPARATUR-7.3.1.ps1  --  Parser-Reparatur fuer bereits installierte 7.3.0
# ==============================================================================
# Doppelklick auf REPARATUR-STARTEN.cmd startet dieses Skript auf Windows
# PowerShell 5.1 (der Engine, die von 7.3.0 nicht mehr startete). Was es tut:
#   1) Ziel-Datei suchen: %LOCALAPPDATA%\ArenaRobloxBridge\app\ArenaBridge.ps1
#   2) Sicherung als .bak-731 (nur einmal; eine bestehende .bak-731 wird
#      nicht ueberschrieben - damit ist ein Rollback moeglich).
#   3) Echten Parser-Prueflauf VOR dem Patchen ausfuehren (Gold-Gate).
#      Erwartet: 9 Parse-Fehler ab Zeile 27432. Wenn 0 Fehler oder andere
#      Stellen: Meldung und Abbruch (Datei ist bereits repariert oder
#      eine andere Fassung liegt vor - nichts kaputtmachen).
#   4) Den Parser-Fehler beheben: Die fuenf Zeilen der $signature-Verkettung
#      im Fragen-Renderer werden so umgeschrieben, dass der +-Operator am
#      ZEILENENDE steht (Zeilenumbruch-Regel Windows PowerShell 5.1).
#      Der String-Wert bleibt bytegleich - keine Aenderung der Logik.
#   5) Versionsliterale 7.3.0 -> 7.3.1 in den Funktionsstellen (diagnose,
#      fallbacks, footer). Historische Changelog-Kommentare bleiben.
#   6) BOM + LF werden beibehalten (UTF-8 mit BOM, LF).
#   7) Erneuter Parser-Prueflauf NACH dem Patchen.
#      Nur wenn 0 Fehler: REPARATUR OK. Sonst wird die Sicherung
#      zurueckkopiert und eine Meldung gezeigt.
# Danach START-BRIDGE.cmd starten - Fenster muss sich oeffnen.
# ==============================================================================

$ErrorActionPreference = 'Stop'

$AppDir = Join-Path $env:LOCALAPPDATA 'ArenaRobloxBridge\app'
$Target = Join-Path $AppDir 'ArenaBridge.ps1'
$Backup = Join-Path $AppDir 'ArenaBridge.ps1.bak-731'

function Write-Info($msg) { Write-Host "[REPARATUR 7.3.1] $msg" -ForegroundColor Cyan }
function Write-Ok($msg)   { Write-Host "[REPARATUR 7.3.1] $msg" -ForegroundColor Green }
function Write-Bad($msg)  { Write-Host "[REPARATUR 7.3.1] $msg" -ForegroundColor Red }

function Invoke-ParseGate([string]$Path) {
    $tokens = $null
    $errors = $null
    [void][System.Management.Automation.Language.Parser]::ParseFile($Path, [ref]$tokens, [ref]$errors)
    $sorted = @($errors) | Sort-Object { $_.Extent.StartLineNumber }
    return $sorted
}

# --- 1) Ziel-Datei --------------------------------------------------------------
if (-not (Test-Path -LiteralPath $Target -PathType Leaf)) {
    Write-Bad "Zieldatei nicht gefunden: $Target"
    Write-Bad "Ist Arena Roblox Bridge installiert? START-BRIDGE.cmd einmal starten."
    Read-Host "Enter zum Beenden"
    exit 2
}

$sizeBefore = (Get-Item -LiteralPath $Target).Length
Write-Info "Zieldatei : $Target"
Write-Info "Größe     : $sizeBefore Bytes"

# --- 2) Sicherung --------------------------------------------------------------
if (Test-Path -LiteralPath $Backup -PathType Leaf) {
    Write-Info "Sicherung .bak-731 existiert bereits - wird NICHT ueberschrieben."
} else {
    Copy-Item -LiteralPath $Target -Destination $Backup -Force
    Write-Ok  "Sicherung angelegt: $Backup"
}

# --- 3) Parser VOR Reparatur ----------------------------------------------------
Write-Info "Parser-Pruefung VOR Reparatur (Windows PowerShell $($PSVersionTable.PSVersion))..."
$errorsBefore = Invoke-ParseGate $Target
Write-Info "Parse-Fehler vor Patchen: $($errorsBefore.Count)"
if ($errorsBefore.Count -eq 0) {
    Write-Ok "Die Datei ist bereits parse-faehig (0 Fehler). Wahrscheinlich"
    Write-Ok "ist 7.3.1 schon aktiv oder eine neuere Fassung liegt vor."
    Write-Info "Keine Aenderung vorgenommen. START-BRIDGE.cmd starten."
    Read-Host "Enter zum Beenden"
    exit 0
}
foreach ($e in $errorsBefore) {
    Write-Host ("  Zeile {0}:{1} - {2}" -f $e.Extent.StartLineNumber, $e.Extent.StartColumnNumber, $e.Message)
}

# Pruefen, dass es der bekannte Fehler ist (irgendein Fehler ab Zeile 27420..27460 mit "+" oder ")"-Meldung)
$signatureLineHit = $false
foreach ($e in $errorsBefore) {
    if ($e.Extent.StartLineNumber -ge 27420 -and $e.Extent.StartLineNumber -le 27460) {
        $signatureLineHit = $true; break
    }
}
if (-not $signatureLineHit) {
    Write-Bad "Die Parse-Fehler liegen NICHT an der bekannten $signature-Stelle"
    Write-Bad "im Fragen-Renderer. Es ist wahrscheinlich eine andere Fassung oder"
    Write-Bad "ein anderer Fehler. Keine Aenderung vorgenommen - die Datei"
    Write-Bad "unveraendert lassen und einen anderen Weg waehlen (z. B. Datei"
    Write-Bad "loeschen und neu downloaden oder Backup .bak-731 zurueckkopieren)."
    Read-Host "Enter zum Beenden"
    exit 3
}

# --- 4) Patchen ----------------------------------------------------------------
Write-Info "Patche $signature-Verkettung (Operator ans Zeilenende)..."
$bytes = [System.IO.File]::ReadAllBytes($Target)
$hasBom = ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF)
$utf8 = New-Object System.Text.UTF8Encoding($true)  # with BOM for encode
$text = [System.Text.Encoding]::UTF8.GetString($bytes, ($(if($hasBom){3}else{0})), $bytes.Length - $(if($hasBom){3}else{0}))

# Normalize to LF for patching (defensive), then re-emit as LF
$text = $text -replace "`r`n", "`n"

# Broken signature block (exact)
$oldBlock = "        `$signature = ([string]`$Info.AskId + '|step=' + [string]`$Info.Step`n" +
            "            + '|visible=' + (`$visibleIds.ToArray() -join ',')`n" +
            "            + '|answered=' + ((`$answeredKeys.ToArray() | Sort-Object) -join ',')`n" +
            "            + '|state=' + `$askState + '|alive=' + [string]`$agentAlive`n" +
            "            + '|discarded=' + [string]`$discarded)"

$newBlock = "        `$signature = ([string]`$Info.AskId + '|step=' + [string]`$Info.Step +`n" +
            "            '|visible=' + (`$visibleIds.ToArray() -join ',') +`n" +
            "            '|answered=' + ((`$answeredKeys.ToArray() | Sort-Object) -join ',') +`n" +
            "            '|state=' + `$askState + '|alive=' + [string]`$agentAlive +`n" +
            "            '|discarded=' + [string]`$discarded)"

if (-not $text.Contains($oldBlock)) {
    Write-Bad "Der bekannte $signature-Block wurde im Text nicht gefunden."
    Write-Bad "Moeglicherweise wurde die Datei bereits teilweise veraendert."
    Write-Bad "Keine Aenderung vorgenommen."
    Read-Host "Enter zum Beenden"
    exit 4
}
$text = $text.Replace($oldBlock, $newBlock)

# --- 5) Versionsliterale 7.3.0 -> 7.3.1 (funktionale Stellen, nicht Kommentare) ---
$versionReplacements = @(
    @("PROOF_OF_LIFE Version=7.3.0",  "PROOF_OF_LIFE Version=7.3.1"),
    @("(Version 7.3.0)",              "(Version 7.3.1)"),
    @("'Version: 7.3.0'",             "'Version: 7.3.1'"),
    @("DocsVersion     = '7.3.0'",    "DocsVersion     = '7.3.1'"),
    @("Version = '7.3.0'",            "Version = '7.3.1'"),
    @("Bridge-Version=7.3.0",         "Bridge-Version=7.3.1"),
    @("`$script:Shared.RuntimeInfo.Version = '7.3.0'", "`$script:Shared.RuntimeInfo.Version = '7.3.1'"),
    @("Arena Studio Bridge - Studio Plugin  (Version 7.3.0)", "Arena Studio Bridge - Studio Plugin  (Version 7.3.1)"),
    @('local ARENA_VERSION  = "7.3.0"', 'local ARENA_VERSION  = "7.3.1"'),
    @("'- Bridge/Plugin-Stand: 7.3.0 / '", "'- Bridge/Plugin-Stand: 7.3.1 / '"),
    @("version = '7.3.0'",            "version = '7.3.1'"),
    @("bridgeVersion = '7.3.0'",      "bridgeVersion = '7.3.1'"),
    @("bridgeVersion='7.3.0'",        "bridgeVersion='7.3.1'"),
    @("serverVersion = '7.3.0'",      "serverVersion = '7.3.1'"),
    @("`$versionText = '7.3.0'",      "`$versionText = '7.3.1'"),
    @("`$verText = '7.3.0'",          "`$verText = '7.3.1'"),
    @('"Arena Roblox Bridge - Version 7.3.0"', '"Arena Roblox Bridge - Version 7.3.1"'),
    @("'Version 7.3.0 - aktuell.",    "'Version 7.3.1 - aktuell.")
)
foreach ($pair in $versionReplacements) {
    $text = $text.Replace($pair[0], $pair[1])
}

# --- 6) Schreiben mit BOM + LF -------------------------------------------------
# Bewusst LF (wie Original), UTF-8 mit BOM.
$outBytes = $utf8.GetBytes($text)
# $utf8 mit BOM erzeugt bereits das BOM-Praefix (EF BB BF).
[System.IO.File]::WriteAllBytes($Target, $outBytes)

$sizeAfter = (Get-Item -LiteralPath $Target).Length
Write-Info "Datei geschrieben: $sizeAfter Bytes (vorher $sizeBefore)."
$bomCheck = [System.IO.File]::ReadAllBytes($Target)
$hasBomAfter = ($bomCheck.Length -ge 3 -and $bomCheck[0] -eq 0xEF -and $bomCheck[1] -eq 0xBB -and $bomCheck[2] -eq 0xBF)
Write-Info "BOM vorhanden nach Schreiben: $hasBomAfter"

# --- 7) Parser NACH Reparatur ---------------------------------------------------
Write-Info "Parser-Pruefung NACH Reparatur..."
$errorsAfter = Invoke-ParseGate $Target
Write-Info "Parse-Fehler nach Patchen: $($errorsAfter.Count)"
if ($errorsAfter.Count -gt 0) {
    Write-Bad "Nach dem Patchen gibt es noch Parse-Fehler - ROLLBACK."
    foreach ($e in $errorsAfter) {
        Write-Host ("  Zeile {0}:{1} - {2}" -f $e.Extent.StartLineNumber, $e.Extent.StartColumnNumber, $e.Message)
    }
    Copy-Item -LiteralPath $Backup -Destination $Target -Force
    Write-Bad "Sicherung zurueckkopiert. Datei ist wieder im 7.3.0-Ausgangszustand."
    Read-Host "Enter zum Beenden"
    exit 5
}

Write-Ok "REPARATUR OK: 0 Parse-Fehler."
Write-Ok "Die Bridge startet jetzt mit START-BRIDGE.cmd."
Write-Info "Sicherung (unveraenderte 7.3.0) liegt unter: $Backup"
Read-Host "Enter zum Beenden"
exit 0
