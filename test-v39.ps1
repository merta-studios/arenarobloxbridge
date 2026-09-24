# ============================================================================
# Arena Roblox Bridge 5.2 - Logik-Tests (Mock, ohne Studio / ohne UI)
# ----------------------------------------------------------------------------
# Ausfuehren auf dem PC (Windows PowerShell 5.1):
#   powershell.exe -NoProfile -ExecutionPolicy Bypass -File test-v39.ps1
#
# Die Tests pruefen die aktuelle 5.2-Logik OHNE Roblox Studio:
#   1. Syntax der kompletten ArenaBridge.ps1 (echter PowerShell-Parser)
#   2. UTF-8-BOM
#   3. Einstellungen: laden/speichern (settings.json Round-Trip)
#   4. Play-Verfolgung: wer hat den Test gestartet? (Update-PlayStateTracking)
#      - Nutzer startet -> startedBy=user, KI wird gesperrt
#      - KI startet     -> startedBy=assistant, KI darf weiter testen
#      - Plugin-Neuladen waehrend Nutzer-Test -> bleibt Nutzer-Test
#      - Nutzer stoppt KI-Test -> stoppedBy=user
#   5. Selbst-Test-Sperre (New-SelfTestBlockedResult)
#   6. report_done: aus/ohne Nachricht/erfolgreich (Mock-Warteschlange)
#   7. XAML der drei Fenster ist wohlgeformtes XML
#   8. Versions-Konsistenz (5.2 ueberall)
#   9. GET-API, Kopier-Bestaetigung und Autostart-Selbst-Update (Version 5)
# ============================================================================

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$ps1  = Join-Path $root 'ArenaBridge.ps1'
$script:Passed = 0
$script:Failed = 0

function Pass([string]$Name) {
    $script:Passed++
    Write-Host ("  [OK]   " + $Name) -ForegroundColor Green
}
function Fail([string]$Name, [string]$Detail) {
    $script:Failed++
    Write-Host ("  [FEHLER] " + $Name + "  ->  " + $Detail) -ForegroundColor Red
}
function Assert([bool]$Condition, [string]$Name, [string]$Detail) {
    if ($Condition) { Pass $Name } else { Fail $Name $Detail }
}

Write-Host '=== Arena Bridge 5.2 Logik-Tests ===' -ForegroundColor Cyan

# ----------------------------------------------------------------------------
# 1) Syntax der kompletten Datei mit dem echten Parser pruefen
# ----------------------------------------------------------------------------
Write-Host '`n1) Syntax-Pruefung (PowerShell-Parser)' -ForegroundColor Yellow
$tokens = $null; $parseErrors = $null
[void][System.Management.Automation.Language.Parser]::ParseFile($ps1, [ref]$tokens, [ref]$parseErrors)
Assert ($parseErrors.Count -eq 0) ('Syntax fehlerfrei (' + $parseErrors.Count + ' Parser-Fehler)') (($parseErrors | Select-Object -First 3 | ForEach-Object { $_.Message + ' @ Zeile ' + $_.Extent.StartLineNumber }) -join ' | ')

# ----------------------------------------------------------------------------
# 2) UTF-8 mit BOM
# ----------------------------------------------------------------------------
Write-Host '`n2) Codierung' -ForegroundColor Yellow
$bytes = [System.IO.File]::ReadAllBytes($ps1)
Assert ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) 'UTF-8 mit BOM vorhanden' 'BOM fehlt - Umlaute wuerden zerstoert'

# ----------------------------------------------------------------------------
# 3) Einstellungen: Round-Trip ueber settings.json (extrahierte Funktionen)
# ----------------------------------------------------------------------------
Write-Host '`n3) Einstellungen speichern/laden' -ForegroundColor Yellow
$text = [System.IO.File]::ReadAllText($ps1)
$startMark = '# EINSTELLUNGEN DAUERHAFT SPEICHERN (Version 3.8)'
$endMark   = '# GEMEINSAMER ZUSTAND'
$i0 = $text.IndexOf($startMark); $i1 = $text.IndexOf($endMark)
Assert ($i0 -ge 0 -and $i1 -gt $i0) 'Einstellungs-Funktionen im Skript gefunden' 'Marker fehlen'
if ($i0 -ge 0 -and $i1 -gt $i0) {
    $settingsBlock = $text.Substring($i0, $i1 - $i0)
    $tempDir = Join-Path $env:TEMP ('arena38test_' + [guid]::NewGuid().ToString('N').Substring(0,8))
    New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
    try {
        $script:AppDataRoot = $tempDir
        function Write-RuntimeLog { param([string]$Message) }
        Invoke-Expression $settingsBlock
        # Round-Trip: Werte aendern, speichern, neu laden
        $script:SettingsCache.selfTestAllowed = $false
        $script:SettingsCache.notifyOnDone = $true
        Save-BridgeSettingsFile
        Assert (Test-Path (Join-Path $tempDir 'settings.json')) 'settings.json wurde geschrieben'
        $savedSettings = Get-Content (Join-Path $tempDir 'settings.json') -Raw -Encoding UTF8 | ConvertFrom-Json
        Assert (-not ($savedSettings.PSObject.Properties.Name -contains 'accessModes')) 'Lesezugriff wird nicht gespeichert'
        $script:SettingsFile = Join-Path $tempDir 'settings.json'
        $reloaded = Get-BridgeSettingsFile
        Assert ($reloaded.selfTestAllowed -eq $false) 'selfTestAllowed=false ueberlebt Neustart'
        Assert ($reloaded.notifyOnDone -eq $true) 'notifyOnDone=true ueberlebt Neustart'
        Assert (-not ($reloaded.PSObject.Properties.Name -contains 'accessModes')) 'Neu geladene Einstellungen enthalten keinen Lesezugriff'
        # Defaults bei leerer Datei
        Remove-Item (Join-Path $tempDir 'settings.json') -Force
        $defaults = Get-BridgeSettingsFile
        Assert ($defaults.selfTestAllowed -eq $true -and $defaults.notifyOnDone -eq $false) 'Standardwerte: Selbst-Test AN, Fertig-Meldung AUS'
    } finally {
        Remove-Item $tempDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}

# ----------------------------------------------------------------------------
# 4) Play-Verfolgung: Update-PlayStateTracking (extrahiert + gemockt)
# ----------------------------------------------------------------------------
Write-Host '`n4) Play-Test-Verfolgung (wer hat gestartet?)' -ForegroundColor Yellow
$h0 = $text.IndexOf('function Test-AiPlayActive')
$h1 = $text.IndexOf('LAUFENDE BEFEHLE')
Assert ($h0 -ge 0 -and $h1 -gt $h0) 'Server-Helfer im Skript gefunden' 'Marker fehlen'
if ($h0 -ge 0 -and $h1 -gt $h0) {
    $helperBlock = $text.Substring($h0, $h1 - $h0)
    function Get-UnixSeconds { return [DateTimeOffset]::UtcNow.ToUnixTimeSeconds() }
    $script:MockEvents = New-Object System.Collections.Generic.List[object]
    function Add-BridgeEvent { param($sessionId, $kind, $message, $data) $script:MockEvents.Add(@{ sessionId = $sessionId; kind = $kind; message = $message; data = $data }) }
    $Shared = @{
        AiPlayIntents  = [System.Collections.Concurrent.ConcurrentDictionary[string,object]]::new()
        LastPlayEvents = [System.Collections.Concurrent.ConcurrentDictionary[string,object]]::new()
        RunOwners      = [System.Collections.Concurrent.ConcurrentDictionary[string,string]]::new()
        UserActiveAt   = [System.Collections.Concurrent.ConcurrentDictionary[string,long]]::new()
        BridgeSettings = [hashtable]::Synchronized(@{ selfTestAllowed = $true; notifyOnDone = $false })
    }
    Invoke-Expression $helperBlock

    function Get-Events { return @($script:MockEvents | ForEach-Object { $_ }) }

    # 4a) NUTZER startet einen Playtest (keine KI-Absicht)
    $script:MockEvents.Clear()
    $sid = 'sess-user-start'
    $new = Update-PlayStateTracking $sid @{ running = $false } @{ running = $true; mode = 'play'; userPlaytestActive = $false }
    Assert ($Shared.RunOwners[$sid] -eq 'user') 'Nutzer-Start: RunOwners=user'
    Assert ($new.userPlaytestActive -eq $true) 'Nutzer-Start: KI-Bearbeitung wird gesperrt (userPlaytestActive)'
    $ev = Get-Events
    Assert ($ev.Count -eq 1 -and $ev[0].kind -eq 'play_started' -and $ev[0].data.startedBy -eq 'user') 'Nutzer-Start: play_started-Ereignis mit startedBy=user'

    # 4b) KI startet einen Playtest (Absicht im Server vermerkt)
    $script:MockEvents.Clear()
    $sid = 'sess-ai-start'
    $Shared.AiPlayIntents[$sid] = @{ action = 'start'; at = (Get-UnixSeconds) }
    $new = Update-PlayStateTracking $sid @{ running = $false } @{ running = $true; mode = 'play_here'; userPlaytestActive = $false }
    Assert ($Shared.RunOwners[$sid] -eq 'assistant') 'KI-Start: RunOwners=assistant'
    Assert ($new.userPlaytestActive -eq $false) 'KI-Start: KI darf mit eigenem Test weiterarbeiten'
    $ev = Get-Events
    Assert ($ev.Count -eq 1 -and $ev[0].data.startedBy -eq 'assistant') 'KI-Start: play_started-Ereignis mit startedBy=assistant'

    # 4c) Plugin-Neuladen waehrend eines NUTZER-Tests (kein Wechsel sichtbar)
    $sid = 'sess-reload-user'
    $Shared.RunOwners[$sid] = 'user'
    $new = Update-PlayStateTracking $sid @{ running = $true } @{ running = $true; mode = 'play'; userPlaytestActive = $false }
    Assert ($new.userPlaytestActive -eq $true) 'Neuladen unter Nutzer-Test: bleibt als Nutzer-Test erkannt (KI gesperrt)'

    # 4d) Plugin-Neuladen waehrend eines KI-Tests
    $sid = 'sess-reload-ai'
    $Shared.RunOwners[$sid] = 'assistant'
    $new = Update-PlayStateTracking $sid @{ running = $true } @{ running = $true; mode = 'play'; userPlaytestActive = $false }
    Assert ($new.userPlaytestActive -eq $false) 'Neuladen unter KI-Test: bleibt KI-Test (KI darf weiter testen)'

    # 4e) Nutzer stoppt den KI-Test (keine Stop-Absicht der KI)
    $script:MockEvents.Clear()
    $sid = 'sess-ai-start'
    $new = Update-PlayStateTracking $sid @{ running = $true } @{ running = $false; userPlaytestActive = $false }
    $ev = Get-Events
    Assert ($ev.Count -eq 1 -and $ev[0].kind -eq 'play_stopped' -and $ev[0].data.stoppedBy -eq 'user') 'Nutzer stoppt KI-Test: play_stopped mit stoppedBy=user'
    Assert (-not $Shared.RunOwners.ContainsKey($sid)) 'Stop rueckt RunOwner zurueck'

    # 4f) KI stoppt selbst (Absicht 'stop')
    $script:MockEvents.Clear()
    $sid = 'sess-ai-stop'
    $Shared.AiPlayIntents[$sid] = @{ action = 'stop'; at = (Get-UnixSeconds) }
    $new = Update-PlayStateTracking $sid @{ running = $true } @{ running = $false; userPlaytestActive = $false }
    $ev = Get-Events
    Assert ($ev.Count -eq 1 -and $ev[0].data.stoppedBy -eq 'assistant') 'KI stoppt selbst: stoppedBy=assistant'

    # 4g) Frisch registriertes Fenster mit laufendem Test (alter Zustand unbekannt)
    $script:MockEvents.Clear()
    $sid = 'sess-fresh-running'
    $new = Update-PlayStateTracking $sid $null @{ running = $true; mode = 'play'; userPlaytestActive = $false }
    Assert ($new.userPlaytestActive -eq $true) 'Unbekannter laufender Test: gilt sicherheitshalber als Nutzer-Test'

    # 4h) Dedupe: gleicher Wechsel zweimal -> nur ein Ereignis
    $script:MockEvents.Clear()
    $sid = 'sess-dedupe'
    [void](Update-PlayStateTracking $sid @{ running = $false } @{ running = $true; mode = 'play'; userPlaytestActive = $false })
    [void](Update-PlayStateTracking $sid @{ running = $false } @{ running = $true; mode = 'play'; userPlaytestActive = $false })
    $ev = Get-Events
    Assert ($ev.Count -eq 1) 'Dedupe: kein doppeltes play_started-Ereignis'
}

# ----------------------------------------------------------------------------
# 5) Selbst-Test-Sperre
# ----------------------------------------------------------------------------
Write-Host '`n5) Selbst-Test-Sperre (Einstellung aus)' -ForegroundColor Yellow
if ($h0 -ge 0) {
    $blocked = New-SelfTestBlockedResult 'play_start'
    Assert ($blocked.ok -eq $false -and $blocked.code -eq 'SELF_TEST_DISABLED') 'play_start liefert SELF_TEST_DISABLED'
    Assert ($blocked.error -like '*user DISABLED AI self-testing*') 'Fehlermeldung nennt die Nutzer-Entscheidung'
    Assert ($blocked.whatStillWorks -like '*compile_check*') 'Hinweis nennt Editor-Simulationen als Alternative'
    Assert ($blocked.why -like '*NOT broken*') 'Bridge ist erkennbar NICHT kaputt'
}

# ----------------------------------------------------------------------------
# 6) report_done (Mock)
# ----------------------------------------------------------------------------
Write-Host '`n6) report_done (Fertig-Meldung)' -ForegroundColor Yellow
$r0 = $text.IndexOf("            'report_done' {")
$r1 = $text.IndexOf("            'get_events' {")
Assert ($r0 -ge 0 -and $r1 -gt $r0) 'report_done im Server-Tool gefunden' 'Marker fehlen'
if ($r0 -ge 0 -and $r1 -gt $r0) {
    $caseBody = $text.Substring($r0, $r1 - $r0)
    $caseBody = $caseBody.Substring($caseBody.IndexOf('{') + 1)
    $caseBody = $caseBody.Substring(0, $caseBody.LastIndexOf('}'))
    function To-Json { param($Value, [int]$Depth) return ($Value | ConvertTo-Json -Depth $Depth -Compress) }
    $Shared = @{
        BridgeSettings = [hashtable]::Synchronized(@{ selfTestAllowed = $true; notifyOnDone = $false })
        NotifyQueue    = [System.Collections.Concurrent.ConcurrentQueue[string]]::new()
    }
    $sessionId = 'sess-done'
    $script:MockEvents = New-Object System.Collections.Generic.List[object]
    function Get-SessionEntry { param($s) return $null }
    function Add-BridgeEvent { param($sessionId, $kind, $message, $data) $script:MockEvents.Add(@{ kind = $kind }) }
    $case = [scriptblock]::Create($caseBody)

    # 6a) Einstellung AUS -> NOTIFICATIONS_DISABLED
    $toolArgs = @{ message = 'Ich bin fertig' } | ConvertTo-Json | ConvertFrom-Json
    $res = & $case
    Assert ($res.ok -eq $false -and $res.code -eq 'NOTIFICATIONS_DISABLED') 'Einstellung aus: NOTIFICATIONS_DISABLED (kein Fehler)'

    # 6b) Einstellung AN, Nachricht fehlt -> BAD_ARGS
    $Shared.BridgeSettings.notifyOnDone = $true
    $toolArgs = @{} | ConvertTo-Json | ConvertFrom-Json
    $res = & $case
    Assert ($res.ok -eq $false -and $res.code -eq 'BAD_ARGS') 'Ohne message: BAD_ARGS'

    # 6c) Einstellung AN -> Meldung landet in der Warteschlange (-> Windows-Meldung)
    $toolArgs = @{ message = '  5 Aenderungen und Fehler behoben - fertig  ' } | ConvertTo-Json | ConvertFrom-Json
    $res = & $case
    $queued = $null
    $got = $Shared.NotifyQueue.TryDequeue([ref]$queued)
    Assert ($res.ok -eq $true -and $res.result.delivered -eq $true) 'Einstellung an: report_done liefert ok'
    Assert ($got -and $queued -like '*5 Aenderungen und Fehler behoben - fertig*') 'Meldung steht fuer die Windows-Benachrichtigung in der Warteschlange'
    Assert ($res.result.note -like '*LAST action*') 'Antwort erinnert: keine weiteren Aenderungen, Antwort beenden'
}

# ----------------------------------------------------------------------------
# 7) XAML wohlgeformt
# ----------------------------------------------------------------------------
Write-Host '`n7) Fenster-XAML' -ForegroundColor Yellow
$xamlCount = 0
$xamlMatches = [regex]::Matches($text, "@'\n(<\?xml[\s\S]*?\n</Window>|<Window[\s\S]*?\n</Window>)\n'@")
foreach ($m in $xamlMatches) {
    try { [void][xml]$m.Groups[1].Value; $xamlCount++ } catch { Fail ('XAML Block ' + $xamlCount) $_.Exception.Message }
}
Assert ($xamlMatches.Count -eq 3 -and $xamlCount -eq 3) 'Alle 3 Fenster (Haupt, Update-Hinweis, Einstellungen) sind gueltiges XML' ('gefundene Bloecke: ' + $xamlMatches.Count + ', gueltig: ' + $xamlCount)
$settingsXaml = ($xamlMatches | Where-Object { $_.Groups[1].Value -like '*SelfTestSwitch*' } | Select-Object -First 1)
Assert ($null -ne $settingsXaml -and $settingsXaml.Groups[1].Value -like '*ArenaSwitch*' -and $settingsXaml.Groups[1].Value -like '*NotifySwitch*' -and $settingsXaml.Groups[1].Value -like '*StartupSwitch*') 'Einstellungsfenster enthaelt alle drei Schalter'

# ----------------------------------------------------------------------------
# 8) Versions-Konsistenz
# ----------------------------------------------------------------------------
Write-Host '`n8) Version 5.2 ueberall' -ForegroundColor Yellow
Assert ($text.Contains("# Arena Roblox Bridge  -  Version 5.2")) 'Changelog-Kopf'
Assert ($text.Contains("DocsVersion     = '5.2'")) 'DocsVersion'
Assert ($text.Contains('local ARENA_VERSION  = "5.2"')) 'ARENA_VERSION (Plugin)'
Assert ($text.Contains('Arena Studio Bridge - Studio Plugin  (Version 5.2)')) 'Plugin-Kommentar'
Assert ($text.Contains("version = '5.2'")) 'Manifest-Version'
Assert ($text.Contains("serverVersion = '5.2'")) 'serverVersion'
Assert ($text.Contains('$versionText = ' + "'5.2'")) 'Show-UpdateNotice-Fallback'
Assert ($text.Contains('Text="Arena Roblox Bridge - Version 5.2"')) 'Einstellungs-Fusszeile'
$bridgeVersions = [regex]::Matches($text, "bridgeVersion = '(\d+\.\d+\.\d+)'")
Assert ($bridgeVersions.Count -eq 3 -and @($bridgeVersions | Where-Object { $_.Groups[1].Value -ne '5.2' }).Count -eq 0) 'bridgeVersion (3x)'
$versionJson = Get-Content (Join-Path $root 'version.json') -Raw -Encoding UTF8 | ConvertFrom-Json
Assert ($versionJson.version -eq '5.2') 'version.json'
Assert ($versionJson.notes.Length -gt 50) 'version.json hat Neuigkeiten-Text'

# ----------------------------------------------------------------------------
# 9) API-, Kopier- und Update-Regressionen
# ----------------------------------------------------------------------------
Write-Host '`n9) GET-API, Kopier-Bestaetigung, Autostart-Update' -ForegroundColor Yellow

# --- GET-API --------------------------------------------------------------
Assert ($text.Contains('GET-Vollsteuerung')) 'GET-Koerperaufbau im Router vorhanden'
$getBlockStart = $text.IndexOf('GET-Vollsteuerung')
$tokenCheck    = $text.IndexOf('$token = Get-Token $context.Request $body')
Assert ($getBlockStart -gt 0 -and $tokenCheck -gt $getBlockStart) 'GET-Koerper wird VOR der Token-Pruefung gebaut (gleicher Codepfad)'
foreach ($field in @('tool', 'uploadId', 'chunkIndex', 'chunkCount', 'timeoutSeconds')) {
    Assert ($text -match ("'" + [regex]::Escape($field) + "'")) ('GET-Parameter ' + $field + ' wird gelesen')
}
Assert ($text.Contains('foreach ($jsonField in @(''args'',''calls'',''extra''))')) 'args/calls/extra werden als JSON geparst'
Assert ($text.Contains('$getParamError')) 'Ungueltiges JSON liefert eine saubere 400-Antwort'
Assert ($text.Contains('callToolGet')) 'Manifest listet GET /api/tool'
Assert ($text.Contains('callManyGet')) 'Manifest listet GET /api/tools/parallel'
Assert ($text.Contains('uploadGet')) 'Manifest listet GET /api/upload'
Assert ($text.Contains('getOnlyNote')) 'Manifest erklaert die GET-Vollsteuerung'
Assert ($text.Contains('GET WORKS FOR EVERYTHING')) 'Sitzungsstart-Regeln erklaeren die GET-Nutzung'
Assert ($text.Contains('MultiPlaceToken')) 'Alle-Places-Token ist im gemeinsamen Zustand'
Assert ($text.Contains('MULTI_PLACE_SELECTION_REQUIRED')) 'Aggregate-Zugriff fordert eine explizite Place-Auswahl'
Assert ($text.Contains('Open-ArenaHistoryWindow')) 'Arena-Verlauf ist vorhanden'
Assert ($text.Contains('Start-PlaceIconLoad')) 'Place-Icon-Lader ist vorhanden'

# --- Kopier-Bestaetigung ---------------------------------------------------
Assert ($text.Contains('x:Name="CopyConfirm"')) 'Kopier-Hinweis ist im Haupt-XAML'
Assert ($text.Contains('$CopyConfirm     = $window.FindName(''CopyConfirm'')')) 'Kopier-Hinweis wird aus dem XAML geholt'
Assert ($text.Contains('function Show-CopyConfirm')) 'Show-CopyConfirm existiert'
Assert ($text.Contains('Prompt wurde in die Zwischenablage kopiert')) 'Bestaetigungstext vorhanden'
$copyStart = $text.IndexOf('function Copy-Prompt')
$copyEnd   = $text.IndexOf('function Set-RowMode', $copyStart)
$copyBody  = $text.Substring($copyStart, $copyEnd - $copyStart)
Assert ($copyBody.Contains('Show-CopyConfirm')) 'Copy-Prompt zeigt die Bestaetigung'
Assert (-not $copyBody.Contains('Show-Toast')) 'Copy-Prompt nutzt keine Toasts mehr'

# --- Autostart-Selbst-Update ----------------------------------------------
Assert ($text.Contains('function Invoke-AutostartSelfUpdate')) 'Autostart-Update-Funktion existiert'
Assert ($text.Contains('$script:RepoOwner = ''merta-studios''')) 'Repo-Besitzer ist hinterlegt'
Assert ($text.Contains('$script:RepoName = ''arenarobloxbridge''')) 'Repo-Name ist hinterlegt'
Assert ($text.Contains('$script:RepoBranchFallbacks = @(''main'', ''master'')')) 'Branch-Kette main -> master'
Assert ($text.Contains('function Get-UpdateBranchChain')) 'Branch-Kette wird aufgebaut'
Assert ($text.Contains('raw.githubusercontent.com/$($script:RepoOwner)')) 'version.json kommt von raw.githubusercontent.com'
Assert ($text.Contains('-TimeoutSec $script:SelfUpdateTimeout')) 'Download hat ein Zeitlimit'
Assert ($text.Contains('if ([string]::IsNullOrWhiteSpace($UpdateStatus)) {')) 'Update-Suche laeuft nur ohne -UpdateStatus (Autostart)'
Assert ($text.Contains("'-UpdateStatus', 'update-erfolgreich'")) 'Neustart meldet update-erfolgreich'
Assert ($text.Contains('$newPath = $script:ScriptPath + ''.new''')) 'Tausch laeuft ueber eine .new-Datei'
Assert ($text.Contains('Get-BridgeGhostProcesses')) 'Alte Instanzen werden beendet'
# Kein Netz darf den Start blockieren: der Aufruf steckt in try/catch
$callIdx = $text.IndexOf('$selfUpdated = Invoke-AutostartSelfUpdate')
$before   = $text.Substring([Math]::Max(0, $callIdx - 200), [Math]::Min(200, $callIdx))
Assert ($before.Contains('try {')) 'Update-Suche ist gegen Fehler abgesichert'

# --- Der Toast-Verzicht gilt weiterhin -------------------------------------
Assert (-not $text.Contains('New-ToastWindow')) 'Keine Toast-Fenster wiederbelebt'

# ----------------------------------------------------------------------------
# Ergebnis
# ----------------------------------------------------------------------------
Write-Host ''
Write-Host ('=== Ergebnis: ' + $script:Passed + ' bestanden, ' + $script:Failed + ' fehlgeschlagen ===') -ForegroundColor $(if ($script:Failed -eq 0) { 'Green' } else { 'Red' })
if ($script:Failed -gt 0) { exit 1 } else { exit 0 }
