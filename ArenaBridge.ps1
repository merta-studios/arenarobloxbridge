# ============================================================================
# Arena Roblox Bridge  -  Version 3.7
#
# NEU IN DIESER VERSION (3.7) - PLAYTEST-SCHUTZ + GRAU/PINK-DESIGN:
#   1.  UPDATE-FENSTER: Es bleibt garantiert offen, bis der Nutzer bewusst
#       auf OK klickt. Erst danach werden Studio, Plugin, Server und Tunnel
#       gestartet. Weder Timer noch Fenster-Schliessen koennen es umgehen.
#   2.  PLAYTEST-SCHUTZ: Dauerhafte Bearbeitungen werden bereits in der
#       Bridge abgefangen, solange Studio in Play/Run ist. Arena erhaelt eine
#       unuebersehbare STOP_CURRENT_RESPONSE-Anweisung und soll den Nutzer
#       bitten, den Playtest selbst zu beenden, bevor die Arbeit weitergeht.
#   3.  DESIGN: Die komplette Oberflaeche hat eine neue, kontrastreiche
#       Anthrazit-/Grau-/Pink-Optik mit klareren Flaechen und Akzenten.
#
# NEU IN DIESER VERSION (3.6) - UPDATE-SYSTEM ÜBER GITHUB + FEINSCHLIFF:
#   1.  UPDATE-SYSTEM: Das Programm wird von einem kleinen Starter (der
#       ArenaBridge.exe) geladen. Der Starter prueft online im GitHub-
#       Repository, ob es eine neue Version gibt, laedt sie herunter und
#       startet das Programm IMMER mit einem Status-Parameter:
#         update-erfolgreich      Update wurde installiert
#         erster-start            Programm wurde zum ersten Mal geladen
#         kein-update             Kein neues Update vorhanden
#         keine-verbindung        Keine Verbindung zum Update-Server
#         update-fehler           Update konnte nicht installiert werden
#         update-suche-fehler     Update-Suche ist fehlgeschlagen
#   2.  UPDATE-HINWEIS: Bei 'update-erfolgreich' und 'erster-start' zeigt
#       das Programm ZUERST ein eigenes Fenster an ("Update installiert" /
#       "Willkommen") mit den Neuigkeiten der Version und einem OK-Button.
#       Erst nach OK erscheint der Startbildschirm und alles startet normal.
#   3.  FEHLER-BENACHRICHTIGUNG: Bei 'keine-verbindung', 'update-fehler'
#       oder 'update-suche-fehler' erscheint eine rote "1" am Einstellungs-
#       Button (Zahnrad). Ein Klick auf die Einstellungen zeigt die
#       Fehlermeldung im Bereich "Updates".
#   4.  POPUP-NACHRICHTEN UNTEN RECHTS ENTFERNT: Die kleinen Einblendungen
#       (Toasts) sind komplett weg. Wichtige Zustände zeigt der
#       Startbildschirm bzw. die Titelleiste.
#   5.  AUSWAHLMENÜ ("..."): Ein weiterer Klick auf "..." schliesst das
#       offene Menü wieder (echtes Umschalten). Klick auf "Nur Lesezugriff"
#       laesst das Menü offen, damit mehrere Optionen hintereinander
#       eingestellt werden koennen.
#
# NEU IN DIESER VERSION (3.5) - BUGFIX-RELEASE (Port-Freigabe, Startbildschirm):
#   1.  PORT-FREIGABE REPARIERT: Der lokale HTTP-Server der Bridge nutzt
#       http.sys - Windows zeigt als Port-Besitzer PID 4 (System) an, NICHT
#       den echten Verursacher. Auf deutschen Windows heisst der netstat-
#       Status dazu noch "ABHOEREN" statt "LISTENING". Beides zusammen sorgte
#       dafuer, dass eine alte Bridge-Instanz im Hintergrund NICHT beendet
#       werden konnte ("Port konnte nicht freigegeben werden"). Jetzt werden
#       andere Arena-Bridge-Prozesse zusaetzlich UEBER DEN PROZESSNAMEN
#       gefunden (weitere ArenaBridge.exe bzw. PowerShell mit
#       ArenaBridge.ps1) und beendet - unabhaengig davon, was der Port-Table
#       verraet. Zwei Wellen, Diagnose ins Protokoll.
#   2.  STARTBILDSCHIRM REPARIERT: Bricht der Start ab (z.B. Port belegt),
#       blieb der Startbildschirm in 3.4 unsichtbar, weil "Plugin nicht
#       installiert" faelschlich als Fehler gewertet und sofort ausgeblendet
#       wurde. Jetzt gibt es einen sauberen Startzustand: Der Startbildschirm
#       bleibt sichtbar, zeigt "Start fehlgeschlagen" mit klarer Anleitung
#       und blendet erst nach 10 Sekunden aus. Auch die Statuszeilen zeigen
#       bei abgebrochenem Start "Uebersprungen"/"Nicht gestartet" statt
#       irrefuehrender Fehler.
#
# NEU IN DIESER VERSION (3.4) - STARTBILDSCHIRM, PORT, WIRKLICHES BEENDEN
# (Design-Sprache und Bedienung der Spieleliste bleiben unveraendert):
#   1.  STARTBILDSCHIRM: Die drei kleinen Status-Kaerten oben (Roblox Studio,
#       Studio-Plugin, Cloudflare-Tunnel) sind weg. Stattdessen gibt es einen
#       kompletten Startbildschirm mit grossem Ladekreisel, der live zeigt,
#       was gerade vorbereitet wird (Studio / Plugin / Tunnel mit
#       Ampel-Punkten, aktive Punkte pulsieren). Die Spieleliste erscheint
#       erst, wenn alles bereit ist - oder sofort bei einem Fehler, damit
#       niemand vor einem ewigen Kreisel sitzt.
#   2.  PORT AUTOMATISCH FREIGEBEN: Ist der lokale Port (17681) schon belegt
#       (z.B. eine alte Bridge-Instanz im Hintergrund), wird der belegende
#       Prozess automatisch gesucht und beendet - Systemprozesse werden
#       natuerlich nie angeruehrt. Danach startet die Bridge normal.
#   3.  WIRKLICHES BEENDEN: Ein Klick auf das Kreuz oben rechts beendet das
#       Programm jetzt GARANTIERT komplett (Environment.Exit). Vorher konnte
#       der Prozess im Hintergrund weiterlaufen und den Port blockieren -
#       das ist jetzt vorbei.
#
# NEU IN DIESER VERSION (3.3) - AUTOMATISCHE INSTALLATION + EXE-BAU
# (Bedienung und Aussehen des Fensters bleiben unveraendert):
#   1.  CLOUDFLARED WIRD VOLLAUTOMATISCH INSTALLIERT: Fehlt cloudflared (der
#       Cloudflare-Tunnel), laedt das Programm es ohne jede Nachfrage selbst
#       herunter - aus der offiziellen Quelle github.com/cloudflare/cloudflared
#       (immer die neueste Version) - nach
#       %LOCALAPPDATA%\ArenaRobloxBridge\bin\cloudflared.exe und startet den
#       Tunnel danach von allein. Keine Eingabe, keine Admin-Rechte noetig.
#       Klappt der Download nicht (z.B. Firmennetz), wird automatisch winget
#       als zweiter Weg versucht. Der Fortschritt steht im Fenster
#       ("Wird installiert") und im Protokoll.
#   2.  EXE-FAEHIG: Das Skript erkennt selbst, ob es als kompilierte EXE
#       (ps2exe) laeuft, und passt sich an: keine Selbstreparatur der Datei,
#       Autostart zeigt auf die EXE statt auf eine PowerShell-Zeile. Damit
#       genuegt zum Weitergeben EINE einzige ArenaBridge.exe - Freunde muessen
#       nichts installieren (cloudflared und das Studio-Plugin kommen
#       automatisch; nur Roblox Studio selbst muss vorhanden sein, da es ein
#       Roblox-Konto benoetigt).
#   3.  Erkannte cloudflared-Installationen (PATH, Program Files, eigene
#       Kopie) werden alle gefunden und benutzt - nichts wird doppelt geladen.
#
# WICHTIG ZUR DATEICODIERUNG (Umlaute):
#   Diese Datei MUSS als "UTF-8 mit BOM" gespeichert sein. Windows PowerShell
#   5.1 liest Skripte ohne BOM als ANSI (CP1252) ein. Dabei werden Umlaute
#   zerstört. Die BOM am Dateianfang verhindert das. Geht sie verloren,
#   repariert sich das Skript beim nächsten Start selbst.
#
# DESIGN-REGEL FÜR DIES ESKRIPT:
#   Die Bedienung, das Aussehen und die Animationen des Fensters sind NICHT
#   veränderbar (das ist das Programm des Nutzers). Alle Änderungen in
#   Version 3.2 (wie 3.1) betreffen AUSSCHLIESSLICH die Kommunikation mit der KI
#   (Dokumentation, Tools, Fehler, Jobs, Ereignisse, Assets, Playtest).
#
# NEU IN DIESER VERSION (3.2) - BUGFIX-RELISE, Bedienung/Design unverändert:
#   1.  PART-ERSTELLUNG REPARIERT: create_instance / bulk_create / clone /
#       fill_region crashten in aktuellen Studio-Versionen mit "CanCollide is
#       not a valid member of RaycastParams" (das sind BasePart-Properties,
#       keine RaycastParams-Members). Alle betroffenen Zuweisungen entfernt;
#       die Geometrie-Warteschleife darf nie mehr ein Ergebnis zerstoeren
#       (Fehler werden als Hinweis zurueckgegeben, die erstellten Ids bleiben).
#   2.  run_lua / compile_check / Jobs mit source repariert: Neuere Studio-
#       Versionen haben load() aus dem Plugin-Kontext entfernt ("attempt to
#       call a nil value"). Jetzt robuste Fallback-Kette: load -> loadstring
#       -> Require-Trick (temporaeres ModuleScript, "local _ENV" bindet die
#       persistente Umgebung). Fehler melden jetzt Stack-Traces.
#   3.  Selektor-Referenzen funktionieren jetzt WIRKLICH: { query = ... },
#       { tag = ... }, { className = ..., rootRef = ... } akzeptiert an allen
#       refs-Stellen (z.B. bulk_delete, set_property) - wie in der Doku
#       angekündigt. Ein Selektor expandiert auf alle Treffer (max. 500).
#   4.  bulk_create: Doku-Vertrag umgesetzt - template als Spez-Tabelle +
#       count, grid mit { rows, columns, spacingX, spacingZ }, nameTemplate
#       "{n}". Obergrenze 200 -> 400 Instanzen pro Call (weniger Calls).
#
# VERSION 3.1:
#   1.  VOLLER DOKU-TRAG: Bei der ersten Tool-Aufruf einer Sitzung bekommt
#       die KI automatisch die komplette Dokumentation (alle Tools mit
#       Parametern/Typen/Default, Rückgabewerten, lauffähigen Beispielen und
#       Fehlerfällen). Zusätzlich: GET /api/docs?tool= / ?category= / ?full=
#       und das Tool get_docs. Die Doku ist pro Tool, pro Kategorie oder
#       komplett abrufbar.
#   2.  JOBS: Lange Arbeit läuft im Studio als Hintergrund-Job mit Id weiter
#       (start_job, job_status, job_result, list_jobs, cancel_job). Jeder
#       Tool-Call kann mit args.asJob=true in den Hintergrund gehen. Ein
#       Timeout tötet nichts mehr: Der Befehl läuft im Studio zu Ende, das
#       Ergebnis kommt nach (siehe _bridge.lateResults) und Studio arbeitet
#       Befehle strikt nacheinander ab - es wird nie gegen ein noch laufendes
#       Skript gemessen.
#   3.  BESTÄNDIGER LUA-WORKER: run_lua und Jobs laufen in EINEM persistenten
#       Umgebung. Ein Helfer aus einem früheren Call (z.B. "M = {...}") ist im
#       nächsten Call ohne Neukleben sichtbar (lua_state zeigt den Stand).
#   4.  FEHLER ALS KLASSEN: Jede Fehlerantwort hat jetzt einen Code
#       (STUDIO_TIMEOUT, PLAY_MODE_ACTIVE, COMPILE_ERROR, RUNTIME_ERROR,
#       REGION_LIMIT, UNION_BUDGET, CATALOG_UNAVAILABLE, ASSET_TYPE_MISMATCH,
#       REF_NOT_FOUND, ...). Die Bedeutung aller Codes steht in der Doku.
#       compile_check prüft Lua-Syntax, OHNE den Code auszuführen.
#   5.  ROTATION VERSTEHEN: coordinate_guide erklärt das Koordinatensystem
#       UND misst live, wie Cylinder/Wedge/Block im Place ausgerichtet sind
#       (kein Raten). describe_orientation sagt in Klartext, wohin die
#       Seiten eines Parts zeigen. point_at richtet einen Part (mit
#       formbewusster Achse, z.B. die Achse eines Zylinders) auf ein Ziel.
#   6.  PLAYTEST ECHT: play_start mode=play wartet bis Player + Charakter +
#       Client-Agent da sind und meldet PLAY_NO_PLAYER mit Diagnose, wenn
#       nicht. mode=run erklärt schwarz auf weiß, dass dort KEIN Player und
#       KEIN Client existiert. Wenn der BENUTZER im Playtest selbst spielt
#       (Kamera drehen, Avatar laufen, GUI klicken), bekommt die KI sofort
#       ein Ereignis - damit sie das nicht für einen Bug hält.
#   7.  GUI-TEST-HARNESS: gui_check prüft Sichtbarkeit/Text von Elementen,
#       gui_click kann nach dem Klick ein ERWARTETES ERGEBNIS prüfen.
#   8.  RÄUMLICHE ABFRAGEN ALS TOOLS: parts_in_box, parts_in_sphere,
#       nearest_parts, what_is_in_the_way, raycast_many, ground_height,
#       measure_height, verify_measurable - mit Filter, Toleranz und Batch.
#       Neue Geometrie wird automatisch gewartet, bis sie messbar ist.
#   9.  FÜLLEN SICHER: probe_world misst beim ersten Mal die Welle (Raster-
#       Schritt, Wasserhöhe, Höhenregel) und speichert sie. fill_region füllt
#       nach der GEMESSENEN Regel (nie geraten), in kleinen Chunks, mit
#       Resume-Token (Abbruch = weitermachen) und Zell-für-Zell-Fehlern.
#       Tieferes Überschreiben erst nach Aufräumen mit Air.
#  10.  UNION MIT VERNOFT: Vorprüfung (anchored, Eltern, Größe),
#       Komplexitäts-Budget mit Warnung und Konkretem Vorschlag ("ein Part
#       statt 40"), Batch über mehrere Gruppen, sauberer Fehler, wenn Roblox
#       die Operation verweigert, Undo-Punkt als eigener Schritt. scene_stats
#       für große Places (17.000+ Teile).
#  11.  ASSETS ZUVERLÄSSIG: Katalogsuche mit echtem Typ-Mapping (Bilder kommen
#       jetzt tatsächlich), lokalem Cache (keine doppelten Lade pro Session),
#       Tyvalidierung VOR dem Einbauen (ASSET_TYPE_MISMATCH) und klarem
#       Protokoll "Katalog nicht verfügbar -> prozedural bauen" (es gibt
#       catalog_status als Schnelltest).
#  12.  SELEKTOREN STATT ID-LISTEN: Viele Tools akzeptieren jetzt
#       {tag='Wall'} / {className='Part', rootRef='#haus'} / {query='Crate'}
#       statt 50 einzeln erfasster Ids. bulk_create kann aus Template +
#       Raster eine ganze Anordnung erzeugen.
#
# VORHERIGE VERSIONEN (3.0):
#   1.  Jedes Objekt in Roblox bekommt eine eigene Id ("#42"). 55 Teile mit
#       dem Namen "Part" sind damit einzeln lesbar UND einzeln änderbar.
#   2.  Scripte können punktgenau geändert werden (patch_script): einzelne
#       Zeilen, Textstellen oder ganze Funktionen - ohne die Datei neu zu
#       schreiben. Der komplette Austausch (set_script_source) bleibt erhalten.
#   3.  Voller Zugriff auf das Ausgabefenster: lesen, filtern, leeren, auf
#       eine Zeile warten, Fehler zählen, auch Client-Ausgaben im Test.
#   4.  Die KI kann den Test selbst starten und stoppen (Play und Run, KEIN
#       echtes Mehrspieler-Team-Test), zwischen Server und Client wechseln,
#       Befehle ausführen und die Ausgabe mitlesen.
#   5.  Schutz: will die KI im Play-Modus bauen oder Scripte ändern, wird das
#       blockiert - mit dem Hinweis, dass alle Änderungen beim Stopp verloren
#       gehen und sie vorher stoppen soll.
#   6.  Testen im Play-Modus: Charakter bewegen, GUIs anklicken, Tasten und
#       Maus simulieren, Zustand des Spielers auslesen.
#   7.  Unions komplett: zusammenfügen, abziehen (negativ), schneiden und
#       wieder trennen - mit Warnungen und Obergrenzen, damit nichts entsteht,
#       das die KI danach nicht mehr überblicken kann.
#   8.  Klonen statt nachbauen - auch 60 Kopien auf einmal, mit Versatz.
#   9.  Massenarbeit: bulk_create, bulk_delete, bulk_set_properties und
#       "batch" mit parallel=true (mehrere kleine Aufgaben gleichzeitig).
#  10.  Die KI kann selbst in der Toolbox suchen (Decals, Sounds, Meshes,
#       Bilder, Videos) und bekommt die Asset-Ids. Von fertigen Free Models
#       wird sie ausdrücklich abgeraten.
#  11.  Umlaute-Fehler behoben: Anfragen werden jetzt immer als UTF-8 gelesen
#       (vorher ANSI - daraus wurde aus "BöseElla" ein "BÃ¶seElla").
#  12.  Befehle kommen sofort an (Long-Poll statt Abfrage alle 0,35 s) und
#       erzeugen dabei deutlich weniger Dauerlast.
#  13.  Riesige Antworten werden in Stücken übertragen und im Programm
#       zwischengespeichert - nichts wird mehr abgeschnitten.
#  14.  Mehrere Studio-Fenster: jedes Fenster hat eine eigene Sitzung und
#       einen eigenen Token. Der Namenswechsel in der Liste und der
#       gemeinsame Zugriff auf beide Places sind damit behoben.
#  15.  Startet oder stoppt der BENUTZER den Test, merkt die KI das sofort
#       und weiß, dass es kein Fehler und kein Absturz war.
#  16.  Bauhilfe: etwas auf etwas anderes setzen (mit Versatz zur Mitte),
#       stapeln, im Raster anordnen, auf den Boden setzen, ausrichten,
#       um einen Punkt drehen, Abstände messen, Überschneidungen prüfen.
#  17.  Screenshots sind eingebaut, werden der KI aber ausdrücklich
#       abgeraten - stattdessen gibt es eine Textbeschreibung der Szene.
#
# Design und Bedienung des Fensters sind unverändert.
# ============================================================================

# ----------------------------------------------------------------------------
# START-PARAMETER (Version 3.7)
# Der Starter (ArenaBridge.exe) ruft dieses Skript immer mit einem der
# folgenden Status-Parameter auf (weitere Details stehen in der Datei
# update-status.json neben diesem Skript):
#   update-erfolgreich / erster-start / kein-update /
#   keine-verbindung / update-fehler / update-suche-fehler
# Ohne Parameter (direkter Start) gibt es keinen Update-Hinweis.
# ----------------------------------------------------------------------------
param(
    [string]$UpdateStatus = ''
)

$ErrorActionPreference = 'Stop'

# ----------------------------------------------------------------------------
# Codierung: Umlaute und Sonderzeichen richtig verarbeiten
# ----------------------------------------------------------------------------
try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    $OutputEncoding = [System.Text.Encoding]::UTF8
} catch {}
try {
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.SecurityProtocolType]::Tls12
} catch {}

# ----------------------------------------------------------------------------
# UMLAUTE RETTEN
# Windows PowerShell 5.1 liest eine Skriptdatei ohne BOM als ANSI (CP1252).
# Der Marker unten ("äöüßÄÖÜ") erkennt das: korrekt gelesen hat er 7 Zeichen,
# falsch gelesen 14. Erkennt das Skript den Fehler, repariert es die Datei
# (UTF-8 mit BOM) und führt den korrekten Inhalt direkt aus.
# ----------------------------------------------------------------------------
function Test-ScriptEncoding {
    param([string]$Text)
    if ([string]::IsNullOrEmpty($Text)) { return $false }
    $match = [regex]::Match($Text, "EncodingMarker\s*=\s*'([^']*)'")
    if (-not $match.Success) { return $false }
    $value = $match.Groups[1].Value
    if ($value.Length -ne 7) { return $false }
    foreach ($zeichen in $value.ToCharArray()) {
        $code = [int][char]$zeichen
        if ($code -lt 128 -or $code -eq 0xFFFD) { return $false }
    }
    return $true
}

$script:EncodingMarker = 'äöüßÄÖÜ'
$script:EncodingOk = ($script:EncodingMarker.Length -eq 7)
$script:ScriptPath = $MyInvocation.MyCommand.Path
if ([string]::IsNullOrWhiteSpace($script:ScriptPath)) {
    # Nach einer Selbstreparatur läuft das Skript aus dem Speicher heraus.
    # Dann steht der Pfad in dieser Umgebungsvariablen.
    if ($env:ARENABRIDGE_PATH) { $script:ScriptPath = $env:ARENABRIDGE_PATH }
    elseif ($PSScriptRoot) { $script:ScriptPath = Join-Path $PSScriptRoot 'ArenaBridge.ps1' }
}

if (-not $script:EncodingOk) {
    try {
        if ($script:ScriptPath -and (Test-Path -LiteralPath $script:ScriptPath) -and -not $env:ARENABRIDGE_ENCFIX) {
            $bytes = [System.IO.File]::ReadAllBytes($script:ScriptPath)
            $candidates = New-Object System.Collections.Generic.List[string]
            try {
                $candidates.Add([System.Text.UTF8Encoding]::new($false, $true).GetString($bytes))
            } catch {}
            try {
                $candidates.Add([System.Text.Encoding]::GetEncoding(1252).GetString($bytes))
            } catch {}

            $text = $null
            foreach ($candidate in $candidates) {
                if (Test-ScriptEncoding $candidate) { $text = $candidate; break }
            }
            if ([string]::IsNullOrEmpty($text)) {
                foreach ($candidate in $candidates) {
                    try {
                        $repaired = [System.Text.Encoding]::UTF8.GetString([System.Text.Encoding]::GetEncoding(1252).GetBytes($candidate))
                        if (Test-ScriptEncoding $repaired) { $text = $repaired; break }
                    } catch {}
                }
            }
            if (-not [string]::IsNullOrEmpty($text)) {
                $text = $text.TrimStart([char]0xFEFF)
                [System.IO.File]::WriteAllText($script:ScriptPath, $text, [System.Text.UTF8Encoding]::new($true))
                $env:ARENABRIDGE_ENCFIX = '1'
                $env:ARENABRIDGE_PATH = $script:ScriptPath
                & ([scriptblock]::Create($text))
                exit
            }
        }
    } catch {}
}

# ----------------------------------------------------------------------------
# Eigenes Konsolenfenster verstecken (fremde Konsolen bleiben offen).
# ----------------------------------------------------------------------------
try {
    $consoleHelper = Add-Type -MemberDefinition @'
[System.Runtime.InteropServices.DllImport("kernel32.dll")] public static extern uint GetConsoleProcessList(uint[] list, uint count);
[System.Runtime.InteropServices.DllImport("kernel32.dll")] public static extern IntPtr GetConsoleWindow();
[System.Runtime.InteropServices.DllImport("user32.dll")] public static extern bool ShowWindow(System.IntPtr hWnd, int nCmdShow);
'@ -Name 'ArenaConsole' -Namespace 'Arena' -PassThru -ErrorAction Stop

    $processBuffer = New-Object uint32[] 64
    $attached = $consoleHelper::GetConsoleProcessList($processBuffer, 64)
    $consoleHandle = $consoleHelper::GetConsoleWindow()
    if ($attached -eq 1 -and $consoleHandle -ne [IntPtr]::Zero) {
        [void]$consoleHelper::ShowWindow($consoleHandle, 0)
    }
} catch {}

Add-Type -AssemblyName PresentationFramework
Add-Type -AssemblyName PresentationCore
Add-Type -AssemblyName WindowsBase
Add-Type -AssemblyName System.Web

# EXE-MODUS (Version 3.3): In einer kompilierten EXE (gebaut mit ps2exe)
# gibt es keinen Skriptpfad - $MyInvocation.MyCommand.Path und $PSScriptRoot
# sind dann leer. Das Programm erkennt das, nimmt den Ordner der EXE als
# Basis und laesst die Selbstreparatur der Datei weg (eine EXE braucht sie
# nicht, sie ist bereits fix kompiliert).
$script:IsExeMode = [string]::IsNullOrWhiteSpace($script:ScriptPath)
$script:ExePath = $null
if ($script:IsExeMode) {
    try { $script:ExePath = [System.Diagnostics.Process]::GetCurrentProcess().MainModule.FileName } catch {}
}

if ($script:ScriptPath) {
    $script:AppRoot = Split-Path -Parent $script:ScriptPath
} elseif ($script:ExePath) {
    $script:AppRoot = Split-Path -Parent $script:ExePath
} else {
    $script:AppRoot = (Get-Location).Path
}
$script:RepoRoot = Split-Path -Parent $script:AppRoot
$script:LauncherPath = Join-Path $script:RepoRoot 'Arena Roblox Bridge.cmd'
$script:AppDataRoot = Join-Path $env:LOCALAPPDATA 'ArenaRobloxBridge'
$script:BinFolder = Join-Path $script:AppDataRoot 'bin'
$script:Port = 17681
$script:LocalBaseUrl = "http://127.0.0.1:$script:Port"
$script:TunnelUrl = $null
$script:TunnelProcess = $null
$script:TunnelMissing = $false
$script:TunnelFailed = $false
$script:TunnelStartedAt = $null
$script:TunnelHttp2Tried = $false
$script:TunnelSlowNotified = $false
$script:TunnelErrorNotified = $false
$script:TunnelReadyNotified = $false
$script:TunnelMissingNotified = $false
$script:TunnelReaders = @()
# Automatische cloudflared-Installation (Version 3.3)
$script:TunnelInstalling = $false
$script:TunnelInstallFailed = $false
$script:TunnelInstallMessage = ''
$script:TunnelInstallStartedAt = $null
$script:TunnelInstallErrorNotified = $false
$script:TunnelInstaller = $null
$script:ServerPowerShell = $null
$script:ServerRunspacePool = $null
$script:ServerCheckDone = $false
$script:ServerStarted = $false
$script:StartTime = Get-Date
$script:TunnelLines = [System.Collections.Concurrent.ConcurrentQueue[string]]::new()
$script:UiRows = @{}
$script:PlaceNames = @{}
$script:RobloxStudioPath = $null
$script:PluginInstalled = $false
$script:LastTunnelMessage = ''
$script:RuntimeLog = Join-Path $script:AppDataRoot 'runtime.log'
$script:ShotFolder = Join-Path $script:AppDataRoot 'screenshots'
$script:WindowNameCache = @()
$script:WindowNameCacheAt = [DateTime]::MinValue
# Startbildschirm (Version 3.4)
$script:SplashDismissed = $false
$script:SplashReadyAt = $null
$script:SplashTunnelPulse = $false
# Startzustand (Version 3.5): wurde der Start abgebrochen (z.B. Port belegt)?
$script:StartupBlocked = $false
$script:SplashTerminalAt = $null

New-Item -ItemType Directory -Path $script:AppDataRoot -Force | Out-Null
New-Item -ItemType Directory -Path $script:ShotFolder -Force | Out-Null
New-Item -ItemType Directory -Path $script:BinFolder -Force | Out-Null

# ----------------------------------------------------------------------------
# UPDATE-STATUS VERARBEITEN (Version 3.7)
# Der Starter schreibt neben das Skript eine Datei update-status.json mit den
# Details (Version, Neuigkeiten, Fehlermeldung). Der Status-Parameter
# entscheidet, was die Oberflaeche zeigt.
# ----------------------------------------------------------------------------
$script:AppFolder = Split-Path -Parent $script:ScriptPath
if ([string]::IsNullOrWhiteSpace($script:AppFolder)) { $script:AppFolder = $script:AppDataRoot }
$script:UpdateDetails = $null
try {
    $updateStatusFile = Join-Path $script:AppFolder 'update-status.json'
    if (Test-Path -LiteralPath $updateStatusFile) {
        $script:UpdateDetails = (Get-Content -LiteralPath $updateStatusFile -Raw -Encoding UTF8 | ConvertFrom-Json)
    }
} catch { $script:UpdateDetails = $null }

function Get-UpdateStatusText {
    # Klarer deutscher Text zum Status-Parameter (fuer Hinweisfenster/Einstellungen)
    switch ($UpdateStatus) {
        'update-erfolgreich'   { return 'Update installiert' }
        'erster-start'         { return 'Erster Start' }
        'kein-update'          { return 'Kein neues Update' }
        'keine-verbindung'     { return 'Keine Verbindung zum Update-Server' }
        'update-fehler'        { return 'Update konnte nicht installiert werden' }
        'update-suche-fehler'  { return 'Update-Suche fehlgeschlagen' }
        default                { return '' }
    }
}

function Test-UpdateError {
    # Wahr, wenn der Starter einen Fehler melden wollte (rote "1" am Zahnrad)
    return (@('keine-verbindung', 'update-fehler', 'update-suche-fehler') -contains $UpdateStatus)
}

# ----------------------------------------------------------------------------
# GEMEINSAMER ZUSTAND
# Alle Threads (HTTP-Server, Oberfläche) arbeiten auf diesen Sammlungen.
# Sie stecken in EINER Tabelle, damit der Server nur ein Argument braucht.
# ----------------------------------------------------------------------------
$script:Shared = [hashtable]::Synchronized(@{
    # sessionId -> JSON eines Studio-Fensters
    Sessions        = [System.Collections.Concurrent.ConcurrentDictionary[string,string]]::new()
    SessionTokens   = [System.Collections.Concurrent.ConcurrentDictionary[string,string]]::new()
    TokenSessions   = [System.Collections.Concurrent.ConcurrentDictionary[string,string]]::new()
    AccessModes     = [System.Collections.Concurrent.ConcurrentDictionary[string,string]]::new()
    # sessionId -> Warteschlange mit Befehlen (JSON)
    CommandQueues   = [System.Collections.Concurrent.ConcurrentDictionary[string,object]]::new()
    # sessionId -> Signal: weckt den wartenden Long-Poll sofort auf
    CommandSignals  = [System.Collections.Concurrent.ConcurrentDictionary[string,object]]::new()
    # commandId -> Ergebnis (JSON-Text)
    CommandResults  = [System.Collections.Concurrent.ConcurrentDictionary[string,string]]::new()
    ResultSignals   = [System.Collections.Concurrent.ConcurrentDictionary[string,object]]::new()
    # commandId -> Teilstücke einer großen Antwort
    ResultChunks    = [System.Collections.Concurrent.ConcurrentDictionary[string,object]]::new()
    # sessionId -> Zeitpunkt des letzten offenen Long-Polls
    Presence        = [System.Collections.Concurrent.ConcurrentDictionary[string,long]]::new()
    # sessionId -> Anzahl gerade offener Long-Polls (echte Lebendigkeit)
    Pollers         = [System.Collections.Concurrent.ConcurrentDictionary[string,int]]::new()
    # blobId -> große Antwort, die in Stücken abgeholt wird
    Blobs           = [System.Collections.Concurrent.ConcurrentDictionary[string,string]]::new()
    BlobInfo        = [System.Collections.Concurrent.ConcurrentDictionary[string,string]]::new()
    # uploadId -> großer Text, den die KI hochgeladen hat
    Uploads         = [System.Collections.Concurrent.ConcurrentDictionary[string,string]]::new()
    # sessionId -> Ereignisse (Benutzer hat Play gestartet usw.)
    Events          = [System.Collections.Concurrent.ConcurrentDictionary[string,object]]::new()
    Counters        = [System.Collections.Concurrent.ConcurrentDictionary[string,long]]::new()
    # sessionId -> Befehle, die im Studio noch laufen (Timeout überlebt)
    PendingCommands = [System.Collections.Concurrent.ConcurrentDictionary[string,object]]::new()
    # sessionId -> true, wenn die Start-Doku bereits an die KI ging
    DocsSent        = [System.Collections.Concurrent.ConcurrentDictionary[string,bool]]::new()
    # Pfad des lokalen Asset-Caches (Suche/Details, damit pro Session nichts neu geladen wird)
    AssetCachePath  = Join-Path $script:AppDataRoot 'asset_cache.json'
    LogFile         = $script:RuntimeLog
    ShotFolder      = $script:ShotFolder
    Port            = $script:Port
    DocsVersion     = '3.7'
})

function Write-RuntimeLog {
    param([string]$Message)
    try {
        $line = '{0:u} {1}' -f (Get-Date), $Message
        Add-Content -LiteralPath $script:RuntimeLog -Value $line -Encoding UTF8
    } catch {}
}

$runModeText = if ($script:IsExeMode) { "EXE-Modus ($script:ExePath)" } else { "Skript-Modus ($script:ScriptPath)" }
Write-RuntimeLog "=== Programmstart (PID $PID, PowerShell $($PSVersionTable.PSVersion), $runModeText) ==="
Write-RuntimeLog "Codierung: Umlaute korrekt gelesen = $script:EncodingOk (Marker-Laenge $($script:EncodingMarker.Length))"

try {
    [System.AppDomain]::CurrentDomain.add_UnhandledException({
        param($sender, $eventArgs)
        try { Write-RuntimeLog "SCHWERER FEHLER: $($eventArgs.ExceptionObject)" } catch {}
    })
} catch {}

function New-Token {
    $bytes = New-Object byte[] 24
    [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
    [Convert]::ToBase64String($bytes).TrimEnd('=').Replace('+', '-').Replace('/', '_')
}

# ----------------------------------------------------------------------------
# Kaputte Umlaute reparieren (falls doch einmal ANSI-Text ankommt).
# Aus "BÃ¶seElla" wird wieder "BöseElla".
# ----------------------------------------------------------------------------
function Repair-Mojibake {
    param([string]$Text)
    if ([string]::IsNullOrEmpty($Text)) { return $Text }
    if ($Text -notmatch '[ÃÂ]') { return $Text }
    try {
        $bytes = [System.Text.Encoding]::GetEncoding(1252).GetBytes($Text)
        $repaired = [System.Text.UTF8Encoding]::new($false, $true).GetString($bytes)
        if (-not [string]::IsNullOrWhiteSpace($repaired)) { return $repaired }
    } catch {}
    return $Text
}

function Find-RobloxStudio {
    $roots = @(
        (Join-Path $env:LOCALAPPDATA 'Roblox\Versions'),
        (Join-Path ${env:ProgramFiles(x86)} 'Roblox\Versions'),
        (Join-Path $env:ProgramFiles 'Roblox\Versions')
    ) | Where-Object { $_ -and (Test-Path $_) }

    $found = @()
    foreach ($root in $roots) {
        $found += Get-ChildItem -Path $root -Directory -ErrorAction SilentlyContinue |
            ForEach-Object { Join-Path $_.FullName 'RobloxStudioBeta.exe' } |
            Where-Object { Test-Path $_ } |
            ForEach-Object { Get-Item $_ }
    }

    $uninstallRoots = @(
        'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*',
        'HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*'
    )
    foreach ($key in $uninstallRoots) {
        Get-ItemProperty -Path $key -ErrorAction SilentlyContinue |
            Where-Object {
                $displayName = $_.PSObject.Properties['DisplayName']
                $displayName -and $displayName.Value -like '*Roblox Studio*'
            } |
            ForEach-Object {
                $candidate = $null
                $installLocation = $_.PSObject.Properties['InstallLocation']
                $displayIcon = $_.PSObject.Properties['DisplayIcon']
                if ($installLocation -and $installLocation.Value) {
                    $candidate = Join-Path $installLocation.Value 'RobloxStudioBeta.exe'
                } elseif ($displayIcon -and $displayIcon.Value) {
                    $candidate = ([string]$displayIcon.Value -replace '^"|"$', '') -replace ',\d+$', ''
                }
                if ($candidate -and (Test-Path $candidate)) {
                    $found += Get-Item $candidate
                }
            }
    }

    $found | Sort-Object LastWriteTime -Descending | Select-Object -First 1
}


# ----------------------------------------------------------------------------
# STUDIO-PLUGIN (Lua)
# Wird bei jedem Start neu nach %LOCALAPPDATA%\Roblox\Plugins geschrieben.
# ----------------------------------------------------------------------------
function Get-PluginSource {
@'
--[[============================================================================
  Arena Studio Bridge - Studio Plugin  (Version 3.7)

  Dieses Plugin verbindet ein Roblox-Studio-Fenster mit dem Programm
  "Arena Roblox Bridge" auf dem PC. Jedes Studio-Fenster bekommt eine eigene
  Sitzung und damit einen eigenen Token.

  Wichtige Neuerungen:
    * Jedes Objekt bekommt eine eigene Id (#12). Damit sind 55 gleich
      benannte "Part" eindeutig ansprechbar.
    * Scripte koennen punktgenau geaendert werden (patch_script), ohne den
      ganzen Text neu zu schreiben.
    * Vollstaendiger Zugriff auf das Ausgabefenster (Output) inklusive
      Client-Ausgaben im Testmodus.
    * Play/Run starten, stoppen, pausieren; Server- und Client-Kontext;
      Charakter steuern, GUIs benutzen, Tasten und Maus simulieren.
    * Schutz: dauerhafte Aenderungen werden im Play-Modus blockiert, weil sie
      beim Stoppen verloren gehen.
    * Unions: zusammenfuegen, abziehen, schneiden, trennen - mit Warnungen.
    * Klonen, Massenoperationen (60 Teile auf einmal) und Bauhilfen.
    * Grosse Ergebnisse werden in Stuecken uebertragen statt abgeschnitten.

  Wichtige Neuerungen 3.1:
    * Persistenter Lua-Worker: run_lua und Jobs teilen sich EINE Umgebung -
      Helper, Variablen und Caches ueberleben einzelne Rufe.
    * Job-System: lange Operationen laufen nach Timeouts weiter
      (job_status/job_result), kooperative Abbrechung, kein Doppellauf.
    * Neue Geometrie wird automatisch so lange gewartet, bis sie per Raycast
      messbar ist (create/clone/bulk_create, fill_region).
    * Orientierung wird GEMESSEN: measureShape, point_at, describe_orientation,
      coordinate_guide - keine ratenden Drehwerte mehr.
    * Raeumliches Verstehen: parts_in_box, nearest_parts, what_is_in_the_way,
      ground_height, measure_height, scene_stats.
    * Weltprofil: probe_world + fill_region nach Messwert-Regel
      (Wasser y1-2, sonst y1 oder y1+2, kein Raten, keine Tiefen-Ueberschreibung).
    * Union mit Vorpruefung: anchored, Eltern, Groessen, Dreiecks-Budget,
      "einer statt vierzig"-Vorschlag, saubere SOLID_REFUSED-Fehler.
    * Echter Playtest: Player/Charakter/Client-Agent werden aktiv gewartet;
      Run-Modus erklaert seine Grenzen; BENUTZER-Aktionen (Kamera, GUI-Klicks,
      Avatar-Bewegung) werden der KI gemeldet.
    * GUI-Test-Harness: gui_check, gui_click mit expect, set_camera.
    * Fehler als Klassen (codes) statt Freitext: BAD_ARGS, REF_NOT_FOUND,
      BUDGET_EXCEEDED, PLAY_NO_PLAYER, SOLID_REFUSED, REGION_LIMIT, ...
    * Dokumentationen auf Abruf (get_docs) und automatisch am Sitzungsstart.
============================================================================]]

local HttpService        = game:GetService("HttpService")
local Selection          = game:GetService("Selection")
local RunService         = game:GetService("RunService")
local LogService         = game:GetService("LogService")
local CollectionService  = game:GetService("CollectionService")
local Workspace          = game:GetService("Workspace")
local Players            = game:GetService("Players")
local ReplicatedStorage  = game:GetService("ReplicatedStorage")
local Lighting           = game:GetService("Lighting")

local ChangeHistoryService = nil
pcall(function() ChangeHistoryService = game:GetService("ChangeHistoryService") end)
local InsertService = nil
pcall(function() InsertService = game:GetService("InsertService") end)
local VirtualInputManager = nil
pcall(function() VirtualInputManager = game:GetService("VirtualInputManager") end)
local StudioService = nil
pcall(function() StudioService = game:GetService("StudioService") end)

local BASE_URL       = "__BASE_URL__"
local ARENA_VERSION  = "3.7"
local POLL_WAIT      = 12      -- Sekunden Long-Poll (Befehle kommen sofort an)
local HEARTBEAT_EVERY = 5      -- Sekunden
local CHUNK_SIZE     = 48000   -- Bytes je Teilstueck einer Antwort
local MAX_OUTPUT     = 6000    -- Zeilen im Ausgabespeicher

-- ---------------------------------------------------------------------------
-- Grundzustand
-- ---------------------------------------------------------------------------
local running        = true
local instanceGuid   = HttpService:GenerateGUID(false)
local sessionId      = nil
local accessMode     = "readwrite"
local lastHeartbeat  = 0
local connected      = false
local defaultContext = "server"   -- fuer Laufzeit-Befehle im Play-Modus
local userPlaytestActive = false       -- vom Nutzer gestarteter/aktiv gespielter Test

local capabilities = {
    virtualInput   = (VirtualInputManager ~= nil),
    changeHistory  = (ChangeHistoryService ~= nil),
    insertService  = (InsertService ~= nil),
    solidModeling  = true,
    clientAgent    = false,
}

-- ---------------------------------------------------------------------------
-- Oberflaeche des Plugins (unveraendert schlicht)
-- ---------------------------------------------------------------------------
local toolbar = plugin:CreateToolbar("Arena Bridge")
local button = toolbar:CreateButton("Arena Bridge", "Arena Bridge läuft automatisch im Hintergrund.", "")
button.ClickableWhenViewportHidden = true

local widgetInfo = DockWidgetPluginGuiInfo.new(Enum.InitialDockState.Float, false, false, 380, 190, 380, 190)
local widget = plugin:CreateDockWidgetPluginGui("ArenaBridgeStatus", widgetInfo)
widget.Title = "Arena Bridge"

local frame = Instance.new("Frame")
frame.Size = UDim2.fromScale(1, 1)
frame.BackgroundColor3 = Color3.fromRGB(20, 17, 20)
frame.BorderSizePixel = 0
frame.Parent = widget

local title = Instance.new("TextLabel")
title.BackgroundTransparency = 1
title.Position = UDim2.fromOffset(18, 16)
title.Size = UDim2.new(1, -36, 0, 34)
title.Font = Enum.Font.GothamBold
title.TextSize = 18
title.TextColor3 = Color3.fromRGB(255, 240, 248)
title.TextXAlignment = Enum.TextXAlignment.Left
title.Text = "Arena Bridge ist aktiv"
title.Parent = frame

local body = Instance.new("TextLabel")
body.BackgroundTransparency = 1
body.Position = UDim2.fromOffset(18, 56)
body.Size = UDim2.new(1, -36, 1, -74)
body.Font = Enum.Font.Gotham
body.TextSize = 14
body.TextWrapped = true
body.TextColor3 = Color3.fromRGB(180, 163, 173)
body.TextXAlignment = Enum.TextXAlignment.Left
body.TextYAlignment = Enum.TextYAlignment.Top
body.Text = "Dieses Plugin verbindet das aktuell geöffnete Place automatisch mit dem Programm Arena Roblox Bridge. Dieses Fenster kann jederzeit geschlossen werden - die Verbindung bleibt dabei aktiv."
body.Parent = frame

button.Click:Connect(function()
    widget.Enabled = true
end)

-- ---------------------------------------------------------------------------
-- HTTP
-- ---------------------------------------------------------------------------
local function post(path, payload)
    local ok, response = pcall(function()
        return HttpService:RequestAsync({
            Url = BASE_URL .. path,
            Method = "POST",
            Headers = {
                ["Content-Type"] = "application/json; charset=utf-8",
                ["X-Arena-Plugin"] = ARENA_VERSION,
            },
            Body = HttpService:JSONEncode(payload),
        })
    end)
    if not ok or not response or not response.Success or response.Body == "" then
        return nil
    end
    local decodedOk, decoded = pcall(function()
        return HttpService:JSONDecode(response.Body)
    end)
    if decodedOk then
        return decoded
    end
    return nil
end

-- ---------------------------------------------------------------------------
-- Laufzeit-Zustand (Play / Run / Edit)
-- ---------------------------------------------------------------------------
local function currentContext()
    if RunService:IsRunning() then
        if RunService:IsServer() then
            return "server"
        end
        return "client"
    end
    return "edit"
end

local function currentMode()
    if not RunService:IsRunning() then
        if RunService:IsEdit() then
            return "edit"
        end
        return "paused"
    end
    local isRunMode = false
    pcall(function() isRunMode = RunService:IsRunMode() end)
    if isRunMode then
        return "run"
    end
    return "play"
end

local function playState()
    return {
        running    = RunService:IsRunning(),
        mode       = currentMode(),
        context    = currentContext(),
        isEdit     = RunService:IsEdit(),
        isServer   = RunService:IsServer(),
        isClient   = RunService:IsClient(),
        playerCount = #Players:GetPlayers(),
        userPlaytestActive = userPlaytestActive,
    }
end

-- ---------------------------------------------------------------------------
-- MITTEILUNGEN AN DIE KI (z.B. "der Benutzer hat den Test gestartet").
-- Frueh deklariert, damit sie auch in spaeter definierten, aber fruher
-- erzeugten Callbacks greift.
-- ---------------------------------------------------------------------------
local notices = {}
local noticeSeq = 0

local function addNotice(kind, message, data)
    noticeSeq = noticeSeq + 1
    local notice = { seq = noticeSeq, kind = kind, message = message, time = os.time(), data = data }
    table.insert(notices, notice)
    while #notices > 40 do table.remove(notices, 1) end
    -- Sofort an das Programm melden, damit die Bridge Bescheid weiss
    task.spawn(function()
        if sessionId then
            post("/plugin/event", { sessionId = sessionId, event = notice, state = playState() })
        end
    end)
    return notice
end

-- Frueh deklariert (Zuweisung kommt unten in "AUSFUEHRUNG").
local executeTool

-- ---------------------------------------------------------------------------
-- Ausgabefenster (Output) mitschreiben
-- ---------------------------------------------------------------------------
local outputBuffer = {}
local outputSeq = 0
local outputStart = 1     -- Index des ersten Eintrags im Ring
local errorCount = 0
local warningCount = 0

local function pushOutput(message, messageType, source)
    outputSeq = outputSeq + 1
    local entry = {
        seq     = outputSeq,
        time    = os.time(),
        message = tostring(message),
        type    = tostring(messageType or "Output"),
        source  = source or currentContext(),
    }
    if entry.type == "MessageError" or entry.type == "Error" then
        errorCount = errorCount + 1
    elseif entry.type == "MessageWarning" or entry.type == "Warning" then
        warningCount = warningCount + 1
    end
    outputBuffer[outputSeq] = entry
    if outputSeq - outputStart + 1 > MAX_OUTPUT then
        local removeUntil = outputSeq - MAX_OUTPUT
        for i = outputStart, removeUntil do
            outputBuffer[i] = nil
        end
        outputStart = removeUntil + 1
    end
end

local function shortType(messageType)
    local name = tostring(messageType)
    name = string.gsub(name, "^Enum%.MessageType%.", "")
    return name
end

pcall(function()
    for _, item in ipairs(LogService:GetLogHistory()) do
        pushOutput(item.message, shortType(item.messageType), "history")
    end
end)

LogService.MessageOut:Connect(function(message, messageType)
    pushOutput(message, shortType(messageType), currentContext())
end)

local function readOutput(options)
    options = options or {}
    local limit = tonumber(options.limit) or 200
    if limit > 2000 then limit = 2000 end
    local since = tonumber(options.since) or 0
    local filter = options.filter
    local wanted = nil
    if type(options.types) == "table" and #options.types > 0 then
        wanted = {}
        for _, name in ipairs(options.types) do
            wanted[string.lower(tostring(name))] = true
        end
    end
    local onlyErrors = options.onlyErrors == true

    local matches = {}
    for i = outputStart, outputSeq do
        local entry = outputBuffer[i]
        if entry and entry.seq > since then
            local keep = true
            if onlyErrors and entry.type ~= "MessageError" then keep = false end
            if keep and wanted and not wanted[string.lower(entry.type)] then keep = false end
            if keep and filter and filter ~= "" then
                local ok, found = pcall(function()
                    if options.regex == true then
                        return string.find(entry.message, filter) ~= nil
                    end
                    return string.find(string.lower(entry.message), string.lower(filter), 1, true) ~= nil
                end)
                if not ok or not found then keep = false end
            end
            if keep then
                table.insert(matches, entry)
            end
        end
    end

    local total = #matches
    local result = {}
    local startIndex = 1
    if total > limit then
        startIndex = total - limit + 1
    end
    for i = startIndex, total do
        table.insert(result, matches[i])
    end
    return {
        lines        = result,
        returned     = #result,
        matched      = total,
        cursor       = outputSeq,
        oldestStored = outputStart,
        errorCount   = errorCount,
        warningCount = warningCount,
        hint         = "Use cursor as 'since' on the next call to read only new lines.",
    }
end

-- ---------------------------------------------------------------------------
-- IDs UND REFERENZEN
-- Jedes Objekt bekommt beim ersten Kontakt eine stabile Id ("#42").
-- Damit sind 55 gleichnamige Parts eindeutig ansprechbar.
-- ---------------------------------------------------------------------------
local nextId = 0
local idToInstance = setmetatable({}, { __mode = "v" })
local instanceToId = setmetatable({}, { __mode = "k" })

local function idOf(inst)
    if inst == nil then return nil end
    local existing = instanceToId[inst]
    if existing then return existing end
    nextId = nextId + 1
    local id = "#" .. tostring(nextId)
    instanceToId[inst] = id
    idToInstance[id] = inst
    return id
end

local function pathOf(inst)
    if inst == nil then return nil end
    if inst == game then return "game" end
    local parts = {}
    local current = inst
    local guard = 0
    while current and current ~= game and guard < 200 do
        guard = guard + 1
        local name = current.Name
        local parent = current.Parent
        if parent then
            local sameName = 0
            local index = 0
            for _, child in ipairs(parent:GetChildren()) do
                if child.Name == name then
                    sameName = sameName + 1
                    if child == current then
                        index = sameName
                    end
                end
            end
            if sameName > 1 then
                name = name .. "[" .. tostring(index) .. "]"
            end
        end
        table.insert(parts, 1, name)
        current = parent
    end
    return "game." .. table.concat(parts, ".")
end

local function isAlive(inst)
    if inst == nil then return false end
    if inst == game then return true end
    local ok, result = pcall(function()
        return inst.Parent ~= nil or inst:IsDescendantOf(game)
    end)
    return ok and result == true
end

local function splitPathSegments(path)
    local segments = {}
    for segment in string.gmatch(path, "[^%.]+") do
        table.insert(segments, segment)
    end
    return segments
end

local function childByToken(parent, token)
    -- Erlaubt: Name, Name[2], Name#3 (3. Kind mit diesem Namen)
    local name, index = string.match(token, "^(.-)%[(%d+)%]$")
    if not name then
        name, index = string.match(token, "^(.-)#(%d+)$")
    end
    if name then
        local wanted = tonumber(index)
        local seen = 0
        for _, child in ipairs(parent:GetChildren()) do
            if child.Name == name then
                seen = seen + 1
                if seen == wanted then return child end
            end
        end
        return nil
    end
    return parent:FindFirstChild(token)
end

local function findByPath(path)
    if path == nil or path == "" or path == "game" then
        return game
    end
    local normalized = string.gsub(tostring(path), "^game%.", "")
    local current = game
    for _, token in ipairs(splitPathSegments(normalized)) do
        if current == nil then return nil end
        local nextInst = childByToken(current, token)
        if nextInst == nil then
            -- Dienste, die noch nicht geladen sind
            local ok, service = pcall(function() return game:GetService(token) end)
            if ok and service and current == game then
                nextInst = service
            end
        end
        current = nextInst
    end
    return current
end

-- FIX 3.2: Vorwaerts-Deklarationen (findMatches/resolveSelector stehen weiter
-- unten, MUSSSEN aber hier im Scope sein, damit resolveRef/resolveMany sie
-- als Upvalue und nicht als nil-Global sehen).
local findMatches
local resolveSelector

-- Loest eine Referenz auf. Erlaubt sind:
--   "#42"                      -> Id
--   "game.Workspace.Part[3]"   -> Pfad mit Index
--   { id = "#42" }             -> Tabelle
--   { path = "game.Workspace" }
--   { query|tag|className }    -> Selektor (siehe resolveSelector)
--   "selection"                -> aktuelle Auswahl (erstes Objekt)
local function resolveRef(ref)
    if ref == nil then return nil, "Reference missing." end
    if typeof(ref) == "Instance" then return ref end

    if type(ref) == "table" then
        if ref.id then return resolveRef(ref.id) end
        if ref.path then return resolveRef(ref.path) end
        if ref.ref then return resolveRef(ref.ref) end
        -- FIX 3.2: Selektor-Referenzen (in der Doku angekündigt, jetzt funktionsfähig):
        --   { query = "door" }, { tag = "Door" }, { className = "Part", rootRef = "#50" }
        if ref.query or ref.tag or ref.className then
            local matches, selErr = resolveSelector(ref, 1)
            if matches then
                return matches[1]
            end
            return nil, selErr
        end
        return nil, "Reference table needs 'id', 'path' or a selector ({ query = ... }, { tag = ... }, { className = ..., rootRef = ... })."
    end

    local text = tostring(ref)
    if text == "" then return nil, "Reference is empty." end

    if string.sub(text, 1, 1) == "#" then
        local inst = idToInstance[text]
        if inst == nil then
            return nil, "Unknown id " .. text .. " (object was deleted or the plugin was reloaded). Use search/get_tree to get fresh ids."
        end
        if not isAlive(inst) then
            return inst, nil, true
        end
        return inst
    end
    if string.sub(text, 1, 3) == "id:" then
        return resolveRef("#" .. string.sub(text, 4))
    end
    if text == "selection" then
        local selected = Selection:Get()
        if #selected == 0 then return nil, "Selection is empty." end
        return selected[1]
    end

    local inst = findByPath(text)
    if inst == nil then
        return nil, "Path not found: " .. text
    end
    return inst
end

local function resolveMany(refs)
    local list = {}
    local errors = {}
    if refs == nil then return list, errors end
    if type(refs) ~= "table" or refs.id or refs.path or refs.query or refs.tag or refs.className then
        refs = { refs }
    end
    for _, ref in ipairs(refs) do
        if type(ref) == "table" and (ref.query or ref.tag or ref.className) then
            -- FIX 3.2: Selektor expandiert auf ALLE Treffer (max. 500).
            local matches, totalOrErr = resolveSelector(ref, 500)
            if matches then
                for _, inst in ipairs(matches) do
                    table.insert(list, inst)
                end
                if type(totalOrErr) == "number" and totalOrErr > 500 then
                    table.insert(errors, "Selector matched " .. tostring(totalOrErr) .. " objects - only the first 500 were used.")
                end
            else
                table.insert(errors, totalOrErr or "Selector matched nothing.")
            end
        else
            local inst, err = resolveRef(ref)
            if inst then
                table.insert(list, inst)
            else
                table.insert(errors, err or ("Could not resolve " .. tostring(ref)))
            end
        end
    end
    return list, errors
end

local function describeRef(inst)
    if inst == nil then return nil end
    return {
        id        = idOf(inst),
        name      = inst.Name,
        className = inst.ClassName,
        path      = pathOf(inst),
    }
end

-- ---------------------------------------------------------------------------
-- Werte kodieren / dekodieren
-- ---------------------------------------------------------------------------
local function encodeValue(value)
    local t = typeof(value)
    if t == "nil" or t == "string" or t == "number" or t == "boolean" then
        return value
    elseif t == "Vector3" then
        return { type = "Vector3", x = value.X, y = value.Y, z = value.Z }
    elseif t == "Vector2" then
        return { type = "Vector2", x = value.X, y = value.Y }
    elseif t == "Color3" then
        return { type = "Color3", r = value.R, g = value.G, b = value.B,
                 rgb = { math.floor(value.R * 255 + 0.5), math.floor(value.G * 255 + 0.5), math.floor(value.B * 255 + 0.5) } }
    elseif t == "CFrame" then
        local p = value.Position
        local rx, ry, rz = value:ToOrientation()
        return {
            type = "CFrame",
            position = { x = p.X, y = p.Y, z = p.Z },
            orientation = { x = math.deg(rx), y = math.deg(ry), z = math.deg(rz) },
            orientationRadians = { x = rx, y = ry, z = rz },
        }
    elseif t == "UDim2" then
        return { type = "UDim2", xScale = value.X.Scale, xOffset = value.X.Offset, yScale = value.Y.Scale, yOffset = value.Y.Offset }
    elseif t == "UDim" then
        return { type = "UDim", scale = value.Scale, offset = value.Offset }
    elseif t == "BrickColor" then
        return { type = "BrickColor", name = value.Name, number = value.Number }
    elseif t == "EnumItem" then
        return { type = "EnumItem", enum = tostring(value.EnumType), name = value.Name, value = tostring(value) }
    elseif t == "NumberRange" then
        return { type = "NumberRange", min = value.Min, max = value.Max }
    elseif t == "Rect" then
        return { type = "Rect", minX = value.Min.X, minY = value.Min.Y, maxX = value.Max.X, maxY = value.Max.Y }
    elseif t == "Instance" then
        return { type = "Instance", id = idOf(value), path = pathOf(value), className = value.ClassName, name = value.Name }
    elseif t == "ColorSequence" then
        local points = {}
        for _, keypoint in ipairs(value.Keypoints) do
            table.insert(points, { time = keypoint.Time, r = keypoint.Value.R, g = keypoint.Value.G, b = keypoint.Value.B })
        end
        return { type = "ColorSequence", keypoints = points }
    elseif t == "NumberSequence" then
        local points = {}
        for _, keypoint in ipairs(value.Keypoints) do
            table.insert(points, { time = keypoint.Time, value = keypoint.Value, envelope = keypoint.Envelope })
        end
        return { type = "NumberSequence", keypoints = points }
    elseif t == "table" then
        local copy = {}
        for key, item in pairs(value) do
            copy[key] = encodeValue(item)
        end
        return copy
    end
    return tostring(value)
end

local function decodeValue(value)
    if type(value) ~= "table" then
        return value
    end
    if value.type == nil then
        -- Kurzform fuer Vektoren: {x=,y=,z=}
        if value.x ~= nil and value.y ~= nil and value.z ~= nil then
            return Vector3.new(value.x, value.y, value.z)
        end
        if value.r ~= nil and value.g ~= nil and value.b ~= nil then
            if value.r > 1 or value.g > 1 or value.b > 1 then
                return Color3.fromRGB(value.r, value.g, value.b)
            end
            return Color3.new(value.r, value.g, value.b)
        end
        return value
    end
    if value.type == "Vector3" then
        return Vector3.new(value.x or 0, value.y or 0, value.z or 0)
    elseif value.type == "Vector2" then
        return Vector2.new(value.x or 0, value.y or 0)
    elseif value.type == "Color3" then
        if value.rgb then
            return Color3.fromRGB(value.rgb[1] or 0, value.rgb[2] or 0, value.rgb[3] or 0)
        end
        if (value.r or 0) > 1 or (value.g or 0) > 1 or (value.b or 0) > 1 then
            return Color3.fromRGB(value.r or 0, value.g or 0, value.b or 0)
        end
        return Color3.new(value.r or 0, value.g or 0, value.b or 0)
    elseif value.type == "CFrame" then
        local p = value.position or {}
        local o = value.orientation or {}
        local base = CFrame.new(p.x or 0, p.y or 0, p.z or 0)
        if value.orientationRadians then
            local r = value.orientationRadians
            return base * CFrame.fromOrientation(r.x or 0, r.y or 0, r.z or 0)
        end
        return base * CFrame.fromOrientation(math.rad(o.x or 0), math.rad(o.y or 0), math.rad(o.z or 0))
    elseif value.type == "UDim2" then
        return UDim2.new(value.xScale or 0, value.xOffset or 0, value.yScale or 0, value.yOffset or 0)
    elseif value.type == "UDim" then
        return UDim.new(value.scale or 0, value.offset or 0)
    elseif value.type == "BrickColor" then
        return BrickColor.new(value.name or "Medium stone grey")
    elseif value.type == "NumberRange" then
        return NumberRange.new(value.min or 0, value.max or value.min or 0)
    elseif value.type == "Rect" then
        return Rect.new(value.minX or 0, value.minY or 0, value.maxX or 0, value.maxY or 0)
    elseif value.type == "EnumItem" then
        local enumName = string.gsub(tostring(value.enum or ""), "^Enum%.", "")
        local ok, result = pcall(function()
            return Enum[enumName][value.name]
        end)
        if ok then return result end
        return nil
    elseif value.type == "Instance" then
        local inst = resolveRef(value.id or value.path)
        return inst
    elseif value.type == "ColorSequence" then
        local points = {}
        for _, keypoint in ipairs(value.keypoints or {}) do
            table.insert(points, ColorSequenceKeypoint.new(keypoint.time or 0, Color3.new(keypoint.r or 0, keypoint.g or 0, keypoint.b or 0)))
        end
        if #points >= 2 then return ColorSequence.new(points) end
        return nil
    elseif value.type == "NumberSequence" then
        local points = {}
        for _, keypoint in ipairs(value.keypoints or {}) do
            table.insert(points, NumberSequenceKeypoint.new(keypoint.time or 0, keypoint.value or 0, keypoint.envelope or 0))
        end
        if #points >= 2 then return NumberSequence.new(points) end
        return nil
    end
    return value.value
end

-- Setzt eine Eigenschaft und uebersetzt bequeme Kurzformen
-- (z.B. Material = "Neon", Color = {255,0,0}).
local function setProperty(inst, property, rawValue)
    local value = rawValue
    if type(rawValue) == "table" then
        if #rawValue == 3 and property ~= "Size" and (property == "Color" or property == "Color3" or string.find(property, "Color")) then
            value = Color3.fromRGB(rawValue[1], rawValue[2], rawValue[3])
        elseif #rawValue == 3 then
            value = Vector3.new(rawValue[1], rawValue[2], rawValue[3])
        else
            value = decodeValue(rawValue)
        end
    elseif type(rawValue) == "string" then
        local current = nil
        local okCurrent = pcall(function() current = inst[property] end)
        if okCurrent and typeof(current) == "EnumItem" then
            local enumType = tostring(current.EnumType)
            enumType = string.gsub(enumType, "^Enum%.", "")
            local okEnum, enumValue = pcall(function() return Enum[enumType][rawValue] end)
            if okEnum then value = enumValue end
        elseif okCurrent and typeof(current) == "BrickColor" then
            value = BrickColor.new(rawValue)
        elseif okCurrent and typeof(current) == "Color3" and string.sub(rawValue, 1, 1) == "#" then
            local hex = string.sub(rawValue, 2)
            local r = tonumber(string.sub(hex, 1, 2), 16) or 0
            local g = tonumber(string.sub(hex, 3, 4), 16) or 0
            local b = tonumber(string.sub(hex, 5, 6), 16) or 0
            value = Color3.fromRGB(r, g, b)
        end
    end

    local ok, err = pcall(function()
        inst[property] = value
    end)
    if not ok then
        return false, tostring(err)
    end
    return true
end

local commonProps = {
    "Name", "ClassName", "Archivable", "Parent",
    "Position", "Size", "Orientation", "CFrame", "Color", "BrickColor", "Material", "Transparency",
    "Reflectance", "Anchored", "CanCollide", "CanTouch", "CanQuery", "Massless", "Shape", "CastShadow",
    "Text", "TextColor3", "TextSize", "TextScaled", "Font", "BackgroundColor3", "BackgroundTransparency",
    "BorderSizePixel", "Visible", "Image", "ImageColor3", "ScaleType", "ZIndex", "AnchorPoint",
    "Enabled", "Value", "Volume", "SoundId", "Looped", "Playing", "PlaybackSpeed", "TimePosition",
    "Texture", "MeshId", "TextureID", "Scale", "Face", "Adornee", "Attachment0", "Attachment1",
    "Brightness", "Range", "Angle", "Health", "MaxHealth", "WalkSpeed", "JumpPower", "HipHeight",
    "PrimaryPart", "WorldPivot", "Disabled", "RunContext", "CollisionFidelity", "RenderFidelity",
}

local function readProps(inst, includeSource, includeAll)
    local props = {}
    local list = commonProps
    for _, prop in ipairs(list) do
        local ok, value = pcall(function() return inst[prop] end)
        if ok and value ~= nil then
            props[prop] = encodeValue(value)
        end
    end
    if includeSource and inst:IsA("LuaSourceContainer") then
        local ok, source = pcall(function() return inst.Source end)
        if ok then
            props.Source = source
            props.SourceLineCount = select(2, string.gsub(source, "\n", "\n")) + 1
        end
    elseif inst:IsA("LuaSourceContainer") then
        local ok, source = pcall(function() return inst.Source end)
        if ok then
            props.SourceBytes = #source
            props.SourceLineCount = select(2, string.gsub(source, "\n", "\n")) + 1
        end
    end
    local attrsOk, attrs = pcall(function() return inst:GetAttributes() end)
    if attrsOk then
        local safeAttrs = {}
        local hasAny = false
        for key, value in pairs(attrs) do
            safeAttrs[key] = encodeValue(value)
            hasAny = true
        end
        if hasAny then props.Attributes = safeAttrs end
    end
    local tagsOk, tags = pcall(function() return CollectionService:GetTags(inst) end)
    if tagsOk and #tags > 0 then
        props.Tags = tags
    end
    if includeAll then
        props._note = "Only common properties are listed. Use run_lua for exotic properties."
    end
    return props
end

-- ---------------------------------------------------------------------------
-- BAUM UND SUCHE
-- ---------------------------------------------------------------------------
local function treeNode(inst, depth, maxDepth, state, includeProperties, includeSource)
    if state.count >= state.maxNodes then
        state.truncated = true
        return nil
    end
    state.count = state.count + 1
    local item = {
        id         = idOf(inst),
        name       = inst.Name,
        className  = inst.ClassName,
        path       = pathOf(inst),
        childCount = #inst:GetChildren(),
    }
    if inst:IsA("BasePart") then
        item.position = { x = inst.Position.X, y = inst.Position.Y, z = inst.Position.Z }
        item.size = { x = inst.Size.X, y = inst.Size.Y, z = inst.Size.Z }
    end
    if inst:IsA("LuaSourceContainer") then
        local ok, source = pcall(function() return inst.Source end)
        if ok then
            item.sourceBytes = #source
            item.sourceLines = select(2, string.gsub(source, "\n", "\n")) + 1
        end
    end
    if includeProperties then
        item.properties = readProps(inst, includeSource, false)
    end
    if depth < maxDepth then
        item.children = {}
        for _, child in ipairs(inst:GetChildren()) do
            local childNode = treeNode(child, depth + 1, maxDepth, state, includeProperties, includeSource)
            if childNode then
                table.insert(item.children, childNode)
            end
            if state.truncated then break end
        end
    end
    return item
end

local function nameCollisions(parent, name)
    local count = 0
    for _, child in ipairs(parent:GetChildren()) do
        if child.Name == name then count = count + 1 end
    end
    return count
end

-- ---------------------------------------------------------------------------
-- SCRIPTE: LESEN, SUCHEN, PUNKTGENAU AENDERN
-- ---------------------------------------------------------------------------
local function hashString(text)
    -- kleiner, stabiler Hash (djb2) - dient nur zum Abgleich
    local hash = 5381
    for i = 1, #text do
        hash = (hash * 33 + string.byte(text, i)) % 4294967296
    end
    return string.format("%08x", hash) .. "-" .. tostring(#text)
end

local function splitLines(text)
    local lines = {}
    local position = 1
    while true do
        local newlineAt = string.find(text, "\n", position, true)
        if not newlineAt then
            table.insert(lines, string.sub(text, position))
            break
        end
        table.insert(lines, string.sub(text, position, newlineAt - 1))
        position = newlineAt + 1
    end
    return lines
end

local function joinLines(lines)
    return table.concat(lines, "\n")
end

local function lineOfOffset(text, offset)
    local line = 1
    for i = 1, math.min(offset, #text) do
        if string.byte(text, i) == 10 then line = line + 1 end
    end
    return line
end

local function findOccurrences(text, needle, plain)
    local hits = {}
    local position = 1
    local guard = 0
    while guard < 100000 do
        guard = guard + 1
        local from, to = string.find(text, needle, position, plain)
        if not from then break end
        table.insert(hits, { from = from, to = to, line = lineOfOffset(text, from) })
        position = to + 1
        if to < from then position = from + 1 end
    end
    return hits
end

-- Fuehrt eine einzelne Aenderung an einem Skripttext aus.
local function applyEdit(text, edit, report)
    local op = string.lower(tostring(edit.op or edit.mode or "replace"))

    if op == "replace" or op == "replaceall" or op == "regex" or op == "pattern" then
        local plain = not (op == "regex" or op == "pattern" or edit.regex == true or edit.pattern == true)
        local needle = edit.find or edit.old or edit.pattern or edit.search
        if needle == nil or needle == "" then
            return nil, "Edit needs 'find' (the text to replace)."
        end
        local replacement = edit.replace
        if replacement == nil then replacement = edit.new end
        if replacement == nil then replacement = "" end

        local hits = findOccurrences(text, needle, plain)
        if #hits == 0 then
            return nil, "Text not found: " .. string.sub(tostring(needle), 1, 120)
        end

        local wantAll = (op == "replaceall") or edit.all == true
        local occurrence = tonumber(edit.occurrence)
        if not wantAll and occurrence == nil and #hits > 1 then
            local lines = {}
            for _, hit in ipairs(hits) do table.insert(lines, hit.line) end
            return nil, "Ambiguous edit: '" .. string.sub(tostring(needle), 1, 60) .. "' occurs " .. tostring(#hits)
                .. " times (lines " .. table.concat(lines, ", ") .. "). Pass occurrence=<n> or all=true, or use a longer unique snippet."
        end

        if wantAll then
            local newText
            if plain then
                -- Zeichenweise ersetzen, damit Sonderzeichen keine Rolle spielen
                local pieces = {}
                local position = 1
                for _, hit in ipairs(hits) do
                    table.insert(pieces, string.sub(text, position, hit.from - 1))
                    table.insert(pieces, replacement)
                    position = hit.to + 1
                end
                table.insert(pieces, string.sub(text, position))
                newText = table.concat(pieces)
            else
                newText = string.gsub(text, needle, replacement)
            end
            table.insert(report, { op = "replaceAll", count = #hits, firstLine = hits[1].line })
            return newText
        end

        local index = occurrence or 1
        local hit = hits[index]
        if hit == nil then
            return nil, "Occurrence " .. tostring(index) .. " does not exist (found " .. tostring(#hits) .. ")."
        end
        local newText
        if plain then
            newText = string.sub(text, 1, hit.from - 1) .. replacement .. string.sub(text, hit.to + 1)
        else
            local replaced = string.gsub(string.sub(text, hit.from), needle, replacement, 1)
            newText = string.sub(text, 1, hit.from - 1) .. replaced
        end
        table.insert(report, { op = "replace", occurrence = index, line = hit.line })
        return newText
    end

    if op == "insertbefore" or op == "insertafter" then
        local needle = edit.find or edit.anchor
        if needle == nil or needle == "" then
            return nil, "Edit needs 'find' as anchor."
        end
        local hits = findOccurrences(text, needle, not (edit.regex == true))
        if #hits == 0 then
            return nil, "Anchor not found: " .. string.sub(tostring(needle), 1, 120)
        end
        local index = tonumber(edit.occurrence) or 1
        local hit = hits[index]
        if hit == nil then
            return nil, "Anchor occurrence " .. tostring(index) .. " does not exist."
        end
        local addition = tostring(edit.text or edit.insert or "")
        local newText
        if edit.inline == true then
            -- Genau an der Fundstelle einfuegen, ohne neue Zeile.
            if op == "insertbefore" then
                newText = string.sub(text, 1, hit.from - 1) .. addition .. string.sub(text, hit.from)
            else
                newText = string.sub(text, 1, hit.to) .. addition .. string.sub(text, hit.to + 1)
            end
        else
            -- Standard: zeilenweise einfuegen. Der neue Text kommt als eigene
            -- Zeile ueber bzw. unter die Zeile mit der Fundstelle - genau das
            -- erwartet man beim Einfuegen von Code.
            local lines = splitLines(text)
            local target = (op == "insertafter") and lineOfOffset(text, hit.to) or hit.line
            local additionLines = splitLines(addition)
            -- Einrueckung der Ankerzeile uebernehmen, wenn der neue Text keine hat.
            local indent = string.match(lines[target] or "", "^[ \t]*") or ""
            if indent ~= "" and string.match(additionLines[1] or "", "^[ \t]") == nil then
                for i = 1, #additionLines do
                    if additionLines[i] ~= "" then
                        additionLines[i] = indent .. additionLines[i]
                    end
                end
            end
            local out = {}
            for i = 1, #lines do
                if op == "insertbefore" and i == target then
                    for _, l in ipairs(additionLines) do table.insert(out, l) end
                end
                table.insert(out, lines[i])
                if op == "insertafter" and i == target then
                    for _, l in ipairs(additionLines) do table.insert(out, l) end
                end
            end
            newText = joinLines(out)
        end
        table.insert(report, {
            op = op,
            line = hit.line,
            mode = (edit.inline == true) and "inline" or "line",
        })
        return newText
    end

    if op == "replacelines" or op == "deletelines" or op == "insertafterline" or op == "insertbeforeline" then
        local lines = splitLines(text)
        local startLine = tonumber(edit.startLine or edit.line) or 1
        local endLine = tonumber(edit.endLine) or startLine
        if startLine < 1 then startLine = 1 end
        if endLine > #lines then endLine = #lines end
        if startLine > #lines + 1 then
            return nil, "startLine " .. tostring(startLine) .. " is beyond the end of the script (" .. tostring(#lines) .. " lines)."
        end

        if op == "replacelines" then
            local replacementLines = splitLines(tostring(edit.text or ""))
            local out = {}
            for i = 1, startLine - 1 do table.insert(out, lines[i]) end
            for _, line in ipairs(replacementLines) do table.insert(out, line) end
            for i = endLine + 1, #lines do table.insert(out, lines[i]) end
            table.insert(report, { op = "replaceLines", startLine = startLine, endLine = endLine, newLines = #replacementLines })
            return joinLines(out)
        elseif op == "deletelines" then
            local out = {}
            for i = 1, #lines do
                if i < startLine or i > endLine then table.insert(out, lines[i]) end
            end
            table.insert(report, { op = "deleteLines", startLine = startLine, endLine = endLine })
            return joinLines(out)
        else
            local additionLines = splitLines(tostring(edit.text or ""))
            local out = {}
            local anchor = startLine
            if op == "insertbeforeline" then anchor = startLine - 1 end
            for i = 1, math.min(anchor, #lines) do table.insert(out, lines[i]) end
            for _, line in ipairs(additionLines) do table.insert(out, line) end
            for i = math.min(anchor, #lines) + 1, #lines do table.insert(out, lines[i]) end
            table.insert(report, { op = op, atLine = anchor })
            return joinLines(out)
        end
    end

    if op == "append" then
        local addition = tostring(edit.text or "")
        table.insert(report, { op = "append", bytes = #addition })
        if #text > 0 and string.sub(text, -1) ~= "\n" then
            return text .. "\n" .. addition
        end
        return text .. addition
    end

    if op == "prepend" then
        local addition = tostring(edit.text or "")
        table.insert(report, { op = "prepend", bytes = #addition })
        if #addition > 0 and string.sub(addition, -1) ~= "\n" then
            return addition .. "\n" .. text
        end
        return addition .. text
    end

    if op == "replacefunction" then
        local name = tostring(edit.name or "")
        if name == "" then return nil, "replaceFunction needs 'name'." end
        local lines = splitLines(text)
        local startLine, indent = nil, ""
        for index, line in ipairs(lines) do
            local pattern = "^(%s*)[%w%s%.:_]-function%s+" .. string.gsub(name, "([%.%-%(%)%[%]%+%*%?%^%$%%])", "%%%1") .. "%s*%("
            local found = string.match(line, pattern)
            if found ~= nil then
                startLine = index
                indent = found
                break
            end
            local localPattern = "^(%s*)local%s+" .. string.gsub(name, "([%.%-%(%)%[%]%+%*%?%^%$%%])", "%%%1") .. "%s*=%s*function%s*%("
            found = string.match(line, localPattern)
            if found ~= nil then
                startLine = index
                indent = found
                break
            end
        end
        if startLine == nil then
            return nil, "Function '" .. name .. "' not found."
        end
        local endLine = nil
        for index = startLine + 1, #lines do
            if string.match(lines[index], "^" .. indent .. "end%f[%W]") then
                endLine = index
                break
            end
        end
        if endLine == nil then
            return nil, "Could not find the matching 'end' of function '" .. name .. "'. Use replaceLines instead."
        end
        local replacementLines = splitLines(tostring(edit.text or ""))
        local out = {}
        for i = 1, startLine - 1 do table.insert(out, lines[i]) end
        for _, line in ipairs(replacementLines) do table.insert(out, line) end
        for i = endLine + 1, #lines do table.insert(out, lines[i]) end
        table.insert(report, { op = "replaceFunction", name = name, startLine = startLine, endLine = endLine })
        return joinLines(out)
    end

    return nil, "Unknown edit op: " .. tostring(op)
end

local function previewAround(text, lineNumber, radius)
    local lines = splitLines(text)
    local from = math.max(1, lineNumber - radius)
    local to = math.min(#lines, lineNumber + radius)
    local out = {}
    for i = from, to do
        table.insert(out, string.format("%5d| %s", i, lines[i]))
    end
    return table.concat(out, "\n")
end

-- ---------------------------------------------------------------------------
-- BAUHILFE: Groessen, Ecken, Ausrichtung
-- ---------------------------------------------------------------------------
local function boundsOf(inst)
    if inst:IsA("BasePart") then
        return inst.CFrame, inst.Size
    end
    if inst:IsA("Model") then
        local ok, cframe, size = pcall(function()
            local c, s = inst:GetBoundingBox()
            return c, s
        end)
        if ok and cframe then
            return cframe, size
        end
    end
    local ok, cframe = pcall(function() return inst:GetPivot() end)
    if ok and cframe then
        return cframe, Vector3.new(0, 0, 0)
    end
    return nil, nil
end

local function setPivotOf(inst, cframe)
    if inst:IsA("BasePart") then
        inst.CFrame = cframe
        return true
    end
    local ok = pcall(function() inst:PivotTo(cframe) end)
    return ok
end

local function getPivotOf(inst)
    if inst:IsA("BasePart") then return inst.CFrame end
    local ok, cframe = pcall(function() return inst:GetPivot() end)
    if ok then return cframe end
    return nil
end

local function boundsInfo(inst)
    local cframe, size = boundsOf(inst)
    if cframe == nil then
        return { id = idOf(inst), path = pathOf(inst), note = "This instance has no geometry." }
    end
    local position = cframe.Position
    local half = size / 2
    return {
        id       = idOf(inst),
        name     = inst.Name,
        className = inst.ClassName,
        path     = pathOf(inst),
        center   = { x = position.X, y = position.Y, z = position.Z },
        size     = { x = size.X, y = size.Y, z = size.Z },
        min      = { x = position.X - half.X, y = position.Y - half.Y, z = position.Z - half.Z },
        max      = { x = position.X + half.X, y = position.Y + half.Y, z = position.Z + half.Z },
        top      = position.Y + half.Y,
        bottom   = position.Y - half.Y,
        cframe   = encodeValue(cframe),
    }
end

local FACE_VECTORS = {
    top    = Vector3.new(0, 1, 0),
    bottom = Vector3.new(0, -1, 0),
    front  = Vector3.new(0, 0, -1),
    back   = Vector3.new(0, 0, 1),
    left   = Vector3.new(-1, 0, 0),
    right  = Vector3.new(1, 0, 0),
}

-- Legt A auf/an eine Flaeche von B, mit Versatz von der Mitte aus.
local function placeOnFace(mover, target, face, offsetA, offsetB, gap, inside, matchRotation)
    local targetCFrame, targetSize = boundsOf(target)
    local moverCFrame, moverSize = boundsOf(mover)
    if targetCFrame == nil or moverCFrame == nil then
        return nil, "Both instances need geometry (BasePart or Model)."
    end
    face = string.lower(tostring(face or "top"))
    local normal = FACE_VECTORS[face]
    if normal == nil then
        return nil, "Unknown face '" .. face .. "'. Use top, bottom, front, back, left or right."
    end

    local targetHalf = (targetSize * normal).Magnitude / 2
    local moverHalf = (moverSize * normal).Magnitude / 2
    local distance = targetHalf + gap
    if inside then
        distance = targetHalf - moverHalf - gap
    else
        distance = distance + moverHalf
    end

    -- Achsen der Flaeche fuer den seitlichen Versatz
    local up = Vector3.new(0, 1, 0)
    if math.abs(normal.Y) > 0.9 then up = Vector3.new(0, 0, -1) end
    local right = normal:Cross(up).Unit
    local realUp = right:Cross(normal).Unit

    local worldNormal = targetCFrame:VectorToWorldSpace(normal)
    local worldRight = targetCFrame:VectorToWorldSpace(right)
    local worldUp = targetCFrame:VectorToWorldSpace(realUp)

    local position = targetCFrame.Position + worldNormal * distance + worldRight * (offsetA or 0) + worldUp * (offsetB or 0)

    local newCFrame
    if matchRotation then
        newCFrame = CFrame.fromMatrix(position, targetCFrame.RightVector, targetCFrame.UpVector)
    else
        local rotation = moverCFrame - moverCFrame.Position
        newCFrame = CFrame.new(position) * rotation
    end
    setPivotOf(mover, newCFrame)
    return {
        moved = describeRef(mover),
        target = describeRef(target),
        face = face,
        newPosition = { x = position.X, y = position.Y, z = position.Z },
        gap = gap,
    }
end

-- ---------------------------------------------------------------------------
-- CLIENT-AGENT
-- Im Play-Modus laeuft dieses Plugin im Server-Kontext. Fuer alles, was nur
-- der Client kennt (GUIs, Kamera, lokale Ausgaben), wird ein kleiner
-- LocalScript in den Spieler eingesetzt. Er wird nie mitgespeichert
-- (Archivable = false) und verschwindet mit dem Testlauf.
-- ---------------------------------------------------------------------------
local CLIENT_AGENT_SOURCE = [==[
-- Arena Bridge Client Agent (nur waehrend des Tests aktiv)
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local LogService = game:GetService("LogService")
local GuiService = game:GetService("GuiService")
local UserInputService = game:GetService("UserInputService")

local cameraUserIntentUntil = 0

local player = Players.LocalPlayer
local link = ReplicatedStorage:WaitForChild("ArenaBridgeLink", 20)
local logLink = ReplicatedStorage:WaitForChild("ArenaBridgeLog", 20)
if not link then return end

local function guiPath(inst)
    local parts = {}
    local current = inst
    while current and current ~= player.PlayerGui do
        table.insert(parts, 1, current.Name)
        current = current.Parent
    end
    return table.concat(parts, ".")
end

local function collectGui(maxItems)
    local items = {}
    local inset = GuiService:GetGuiInset()
    for _, screen in ipairs(player.PlayerGui:GetChildren()) do
        if screen:IsA("LayerCollector") then
            for _, obj in ipairs(screen:GetDescendants()) do
                if obj:IsA("GuiObject") and #items < maxItems then
                    local visible = obj.Visible
                    local parent = obj.Parent
                    while visible and parent and parent:IsA("GuiObject") do
                        visible = parent.Visible
                        parent = parent.Parent
                    end
                    local text = nil
                    pcall(function() text = obj.Text end)
                    table.insert(items, {
                        name = obj.Name,
                        className = obj.ClassName,
                        path = screen.Name .. "." .. guiPath(obj),
                        text = text,
                        visible = visible and screen.Enabled,
                        clickable = obj:IsA("GuiButton"),
                        x = obj.AbsolutePosition.X,
                        y = obj.AbsolutePosition.Y,
                        width = obj.AbsoluteSize.X,
                        height = obj.AbsoluteSize.Y,
                        centerX = obj.AbsolutePosition.X + obj.AbsoluteSize.X / 2,
                        centerY = obj.AbsolutePosition.Y + obj.AbsoluteSize.Y / 2 + inset.Y,
                    })
                end
            end
        end
    end
    return items
end

local function findGui(query)
    local wanted = string.lower(tostring(query or ""))
    local best = nil
    for _, item in ipairs(collectGui(600)) do
        local nameMatch = string.find(string.lower(item.name), wanted, 1, true)
        local textMatch = item.text and string.find(string.lower(tostring(item.text)), wanted, 1, true)
        local pathMatch = string.find(string.lower(item.path), wanted, 1, true)
        if nameMatch or textMatch or pathMatch then
            if best == nil or (item.clickable and not best.clickable) then
                best = item
            end
        end
    end
    return best
end

local function characterInfo()
    local character = player.Character
    if not character then return { hasCharacter = false } end
    local humanoid = character:FindFirstChildOfClass("Humanoid")
    local root = character:FindFirstChild("HumanoidRootPart")
    return {
        hasCharacter = true,
        position = root and { x = root.Position.X, y = root.Position.Y, z = root.Position.Z } or nil,
        health = humanoid and humanoid.Health or nil,
        maxHealth = humanoid and humanoid.MaxHealth or nil,
        walkSpeed = humanoid and humanoid.WalkSpeed or nil,
        state = humanoid and tostring(humanoid:GetState()) or nil,
        moveDirection = humanoid and { x = humanoid.MoveDirection.X, y = humanoid.MoveDirection.Y, z = humanoid.MoveDirection.Z } or nil,
    }
end

link.OnClientInvoke = function(request)
    request = request or {}
    local action = tostring(request.action or "")
    local args = request.args or {}

    if action == "state" then
        local camera = workspace.CurrentCamera
        return {
            ok = true,
            player = player.Name,
            character = characterInfo(),
            camera = camera and {
                position = { x = camera.CFrame.Position.X, y = camera.CFrame.Position.Y, z = camera.CFrame.Position.Z },
                viewportSize = { x = camera.ViewportSize.X, y = camera.ViewportSize.Y },
                cameraType = tostring(camera.CameraType),
            } or nil,
            guiInset = { x = GuiService:GetGuiInset().X, y = GuiService:GetGuiInset().Y },
            mouseBehavior = tostring(UserInputService.MouseBehavior),
        }
    elseif action == "gui_dump" then
        return { ok = true, items = collectGui(tonumber(args.limit) or 200) }
    elseif action == "gui_find" then
        local item = findGui(args.query)
        if item then return { ok = true, item = item } end
        return { ok = false, error = "No GUI element matches '" .. tostring(args.query) .. "'." }
    elseif action == "set_text" then
        local item = findGui(args.query)
        if not item then return { ok = false, error = "GUI element not found." } end
        local target = player.PlayerGui
        for segment in string.gmatch(item.path, "[^%.]+") do
            target = target:FindFirstChild(segment)
            if not target then break end
        end
        if target then
            local ok = pcall(function() target.Text = tostring(args.text or "") end)
            return { ok = ok, path = item.path }
        end
        return { ok = false, error = "GUI element vanished." }
    elseif action == "move" then
        local character = player.Character
        local humanoid = character and character:FindFirstChildOfClass("Humanoid")
        if not humanoid then return { ok = false, error = "No humanoid." } end
        local target = args.position
        if target then
            humanoid:MoveTo(Vector3.new(target.x or 0, target.y or 0, target.z or 0))
            if args.waitForArrival then
                local reached = humanoid.MoveToFinished:Wait()
                return { ok = true, reached = reached, state = characterInfo() }
            end
            return { ok = true, state = characterInfo() }
        end
        return { ok = false, error = "position missing." }
    elseif action == "jump" then
        local character = player.Character
        local humanoid = character and character:FindFirstChildOfClass("Humanoid")
        if not humanoid then return { ok = false, error = "No humanoid." } end
        humanoid.Jump = true
        return { ok = true }
    elseif action == "camera" then
        cameraUserIntentUntil = os.clock() + 4
        local camera = workspace.CurrentCamera
        if args.position and camera then
            camera.CameraType = Enum.CameraType.Scriptable
            camera.CFrame = CFrame.new(Vector3.new(args.position.x or 0, args.position.y or 0, args.position.z or 0))
            if args.lookAt then
                camera.CFrame = CFrame.lookAt(camera.CFrame.Position, Vector3.new(args.lookAt.x or 0, args.lookAt.y or 0, args.lookAt.z or 0))
            end
        end
        return { ok = true }
    elseif action == "ping" then
        return { ok = true, time = os.clock() }
    end
    return { ok = false, error = "Unknown client action: " .. action }
end

-- Client-Ausgaben an den Server weiterreichen (Sammelpakete alle 0.4s)
local userLink = ReplicatedStorage:WaitForChild("ArenaBridgeUser", 20)
local pendingUser = {}

local function reportUser(kind, data)
    table.insert(pendingUser, { kind = kind, data = data, time = os.time() })
    if #pendingUser > 20 then table.remove(pendingUser, 1) end
end

-- Benutzer drehen/bewegen die Kamera? (wird gedrosselt, KI-Kamerabefehle unterdrueckt)
local lastCam = nil
local lastCamReport = 0
RunService.Heartbeat:Connect(function()
    local camera = workspace.CurrentCamera
    if camera then
        local cf = camera.CFrame
        if lastCam then
            local deltaPos = (cf.Position - lastCam.Position).Magnitude
            local deltaLook = (cf.LookVector - lastCam.LookVector).Magnitude
            if (deltaPos > 0.5 or deltaLook > 0.02) and os.clock() - lastCamReport > 3
                and os.clock() > cameraUserIntentUntil then
                reportUser(deltaLook > 0.02 and "user_rotating_camera" or "user_moving_camera", nil)
                lastCamReport = os.clock()
            end
        end
        lastCam = cf
    end
end)

-- Benutzer klickt in der GUI (oder in die Welt)?
UserInputService.InputBegan:Connect(function(input, gameProcessed)
    local isPointer = input.UserInputType == Enum.UserInputType.MouseButton1
        or input.UserInputType == Enum.UserInputType.Touch
    if isPointer then
        if gameProcessed then
            reportUser("user_gui_click", {
                x = input.Position and input.Position.X or nil,
                y = input.Position and input.Position.Y or nil,
            })
        else
            reportUser("user_clicking_viewport", nil)
        end
    end
end)

if logLink or userLink then
    local pending = {}
    LogService.MessageOut:Connect(function(message, messageType)
        table.insert(pending, { message = message, type = tostring(messageType.Name) })
        if #pending > 200 then table.remove(pending, 1) end
    end)
    task.spawn(function()
        while true do
            task.wait(0.4)
            if logLink and #pending > 0 then
                local batch = pending
                pending = {}
                pcall(function() logLink:FireServer(batch) end)
            end
            if userLink and #pendingUser > 0 then
                local batchUser = pendingUser
                pendingUser = {}
                pcall(function() userLink:FireServer(batchUser) end)
            end
        end
    end)
end
]==]

local clientLink = nil
local clientLogLink = nil
local clientAgentTemplate = nil

local function cleanupRuntimeHelpers()
    for _, name in ipairs({ "ArenaBridgeLink", "ArenaBridgeLog", "ArenaBridgeUser" }) do
        local existing = ReplicatedStorage:FindFirstChild(name)
        if existing then
            pcall(function() existing:Destroy() end)
        end
    end
    for _, player in ipairs(Players:GetPlayers()) do
        local gui = player:FindFirstChild("PlayerGui")
        if gui then
            local agent = gui:FindFirstChild("ArenaClientAgent")
            if agent then pcall(function() agent:Destroy() end) end
        end
    end
    clientLink = nil
    clientLogLink = nil
    capabilities.clientAgent = false
end

local function installClientAgent(player)
    if clientAgentTemplate == nil then return end
    local ok = pcall(function()
        local gui = player:WaitForChild("PlayerGui", 10)
        if gui == nil then return end
        local existing = gui:FindFirstChild("ArenaClientAgent")
        if existing then existing:Destroy() end
        local copy = clientAgentTemplate:Clone()
        copy.Parent = gui
        copy.Disabled = false
    end)
    if ok then
        capabilities.clientAgent = true
    end
end

local function ensureRuntimeHelpers()
    if not RunService:IsRunning() then return false end
    if not RunService:IsServer() then return false end

    if ReplicatedStorage:FindFirstChild("ArenaBridgeLink") == nil then
        local remote = Instance.new("RemoteFunction")
        remote.Name = "ArenaBridgeLink"
        remote.Archivable = false
        remote.Parent = ReplicatedStorage
        clientLink = remote
    else
        clientLink = ReplicatedStorage:FindFirstChild("ArenaBridgeLink")
    end

    if ReplicatedStorage:FindFirstChild("ArenaBridgeLog") == nil then
        local logRemote = Instance.new("RemoteEvent")
        logRemote.Name = "ArenaBridgeLog"
        logRemote.Archivable = false
        logRemote.Parent = ReplicatedStorage
        clientLogLink = logRemote
        logRemote.OnServerEvent:Connect(function(_, batch)
            if type(batch) ~= "table" then return end
            for _, entry in ipairs(batch) do
                pushOutput(entry.message, entry.type or "Output", "client")
            end
        end)
    else
        clientLogLink = ReplicatedStorage:FindFirstChild("ArenaBridgeLog")
    end

    if ReplicatedStorage:FindFirstChild("ArenaBridgeUser") == nil then
        local userRemote = Instance.new("RemoteEvent")
        userRemote.Name = "ArenaBridgeUser"
        userRemote.Archivable = false
        userRemote.Parent = ReplicatedStorage
        userRemote.OnServerEvent:Connect(function(_, batch)
            if type(batch) ~= "table" then return end
            for _, entry in ipairs(batch) do
                local kind = tostring(entry and entry.kind or "")
                if kind ~= "" then
                    -- Kamera-/GUI-Aktivitaet beweist, dass der Nutzer den laufenden
                    -- Test gerade selbst bedient. Ab jetzt haben seine Aktionen
                    -- Vorrang und dauerhafte KI-Bearbeitungen werden blockiert.
                    userPlaytestActive = true
                    addNotice(kind,
                        "The USER did something in the game: " .. kind .. ". This is the user playing, NOT a bug in your scripts - do not change anything because of it.",
                        entry.data)
                end
            end
        end)
    end

    if clientAgentTemplate == nil or clientAgentTemplate.Parent == nil then
        local script = Instance.new("LocalScript")
        script.Name = "ArenaClientAgent"
        script.Archivable = false
        script.Source = CLIENT_AGENT_SOURCE
        script.Disabled = true
        script.Parent = ReplicatedStorage
        clientAgentTemplate = script
    end

    for _, player in ipairs(Players:GetPlayers()) do
        local gui = player:FindFirstChild("PlayerGui")
        if gui == nil or gui:FindFirstChild("ArenaClientAgent") == nil then
            task.spawn(installClientAgent, player)
        end
    end
    return true
end

Players.PlayerAdded:Connect(function(player)
    if RunService:IsRunning() and RunService:IsServer() then
        ensureRuntimeHelpers()
        task.spawn(installClientAgent, player)
    end
end)

local function callClient(action, args, timeout)
    if not RunService:IsRunning() then
        return nil, "Not in play mode. Start a test with play_start first."
    end
    ensureRuntimeHelpers()
    local player = Players:GetPlayers()[1]
    if player == nil then
        return nil, "No player in the test session. Use play_start with mode 'play' (Run mode has no character)."
    end
    if clientLink == nil then
        return nil, "Client link is not available."
    end
    local result = nil
    local errorText = nil
    local finished = false
    task.spawn(function()
        local ok, response = pcall(function()
            return clientLink:InvokeClient(player, { action = action, args = args or {} })
        end)
        if ok then result = response else errorText = tostring(response) end
        finished = true
    end)
    local waited = 0
    local limit = timeout or 8
    while not finished and waited < limit do
        task.wait(0.05)
        waited = waited + 0.05
    end
    if not finished then
        return nil, "Client did not answer in time (agent may still be loading)."
    end
    if errorText then return nil, errorText end
    return result
end

-- ---------------------------------------------------------------------------
-- EINGABEN SIMULIEREN (Tastatur / Maus)
-- ---------------------------------------------------------------------------
local function keyCodeFromName(name)
    if name == nil then return nil end
    local text = tostring(name)
    if #text == 1 then text = string.upper(text) end
    local ok, code = pcall(function() return Enum.KeyCode[text] end)
    if ok and code then return code end
    return nil
end

local function sendKey(name, duration, modifiers)
    if VirtualInputManager == nil then
        return false, "VirtualInputManager is not available in this Studio version."
    end
    local code = keyCodeFromName(name)
    if code == nil then
        return false, "Unknown key '" .. tostring(name) .. "'."
    end
    local mods = {}
    for _, modifier in ipairs(modifiers or {}) do
        local modCode = keyCodeFromName(modifier)
        if modCode then table.insert(mods, modCode) end
    end
    local ok, err = pcall(function()
        for _, modCode in ipairs(mods) do
            VirtualInputManager:SendKeyEvent(true, modCode, false, game)
        end
        VirtualInputManager:SendKeyEvent(true, code, false, game)
        task.wait(duration or 0.08)
        VirtualInputManager:SendKeyEvent(false, code, false, game)
        for _, modCode in ipairs(mods) do
            VirtualInputManager:SendKeyEvent(false, modCode, false, game)
        end
    end)
    if not ok then return false, tostring(err) end
    return true
end

local function sendClick(x, y, button, holdSeconds)
    if VirtualInputManager == nil then
        return false, "VirtualInputManager is not available in this Studio version."
    end
    local ok, err = pcall(function()
        VirtualInputManager:SendMouseMoveEvent(x, y, game)
        task.wait(0.03)
        VirtualInputManager:SendMouseButtonEvent(x, y, button or 0, true, game, 0)
        task.wait(holdSeconds or 0.06)
        VirtualInputManager:SendMouseButtonEvent(x, y, button or 0, false, game, 0)
    end)
    if not ok then return false, tostring(err) end
    return true
end

-- ---------------------------------------------------------------------------
-- PLAY / RUN STEUERN
-- Zum Starten und Stoppen werden die echten Studio-Tastenkuerzel benutzt.
-- Grund: RunService:Stop() setzt den Place NICHT zurueck - Aenderungen aus
-- dem Testlauf wuerden im Place haengen bleiben. Der echte Stopp-Knopf
-- stellt den Zustand von vorher wieder her.
-- ---------------------------------------------------------------------------
local aiPlayIntent = { action = nil, at = 0 }

local function waitForState(wantRunning, seconds)
    local waited = 0
    while waited < (seconds or 12) do
        if RunService:IsRunning() == wantRunning then return true end
        task.wait(0.15)
        waited = waited + 0.15
    end
    return RunService:IsRunning() == wantRunning
end

-- Wann der letzte KI-gesteuerte Charakterbefehl war (damit die
-- Benutzer-Erkennung nicht KI-Bewegung als Benutzer-Bewegung meldet).
local aiMoveUntil = 0

local function startPlay(mode)
    mode = string.lower(tostring(mode or "play"))
    if RunService:IsRunning() then
        return { ok = true, alreadyRunning = true, state = playState() }
    end
    aiPlayIntent = { action = "start", at = os.time() }

    local warnings = {}
    local usedShortcut = false
    if VirtualInputManager ~= nil then
        local key = "F5"
        if mode == "run" then key = "F8" end
        local okKey = sendKey(key, 0.06, {})
        usedShortcut = okKey == true
    end

    if not usedShortcut then
        table.insert(warnings, "VirtualInputManager was not available, so the Studio shortcut could not be used. Falling back to RunService:Run() - this starts a RUN simulation inside the edit place, and stopping it will NOT restore the place automatically.")
        local okRun = pcall(function() RunService:Run() end)
        if not okRun then
            return { ok = false, code = "PLAY_FALLBACK_RUN", error = "Could not start the test. Ask the user to press Play in Studio." }
        end
    end

    local reached = waitForState(true, 15)
    if not reached then
        return {
            ok = false,
            code = "PLAY_FALLBACK_RUN",
            error = "Studio did not enter play mode within 15 seconds. Possible reasons: the Studio window is not focused, or a dialog is open.",
            state = playState(),
            warnings = warnings,
        }
    end
    task.wait(0.6)
    ensureRuntimeHelpers()
    local result = { ok = true, state = playState(), warnings = warnings, note = "Test is running. Persistent edits are blocked until you call play_stop." }
    if not usedShortcut then
        result.code = "PLAY_FALLBACK_RUN"
        table.insert(warnings, "The real Play shortcut could not be pressed, so Run mode started instead (no player). Retry with the Studio window focused to get a real player.")
    end

    local actualMode = currentMode()
    if mode == "play" and actualMode == "play" then
        -- ECHTER Play-Modus: warten bis Player + Charakter + Client-Agent da sind.
        local player = nil
        local character = nil
        local humanoid = nil
        local root = nil
        local agentOk = false
        local waited = 0
        while waited < 20 do
            player = Players:GetPlayers()[1]
            character = player and player.Character
            humanoid = character and character:FindFirstChildOfClass("Humanoid")
            root = character and character:FindFirstChild("HumanoidRootPart")
            if root then
                local pingResp, _ = callClient("ping", {}, 4)
                if type(pingResp) == "table" and pingResp.ok == true then
                    agentOk = true
                    break
                end
            end
            task.wait(0.5)
            waited = waited + 0.5
        end
        if player == nil or character == nil or root == nil then
            local recent = readOutput({ limit = 30, onlyErrors = true })
            return {
                ok = false,
                code = "PLAY_NO_PLAYER",
                error = "Play mode started, but no player character appeared within 20 seconds.",
                recentErrors = recent.lines,
                state = playState(),
                advice = "Check recentErrors for spawn problems (custom spawn systems, data loading, death loops). Call play_stop, look at the errors, fix the cause, then play_start again.",
            }
        end
        result.playerReady = true
        result.character = { name = character.Name, health = humanoid and humanoid.Health or nil }
        if agentOk then
            result.clientAgent = true
        else
            result.clientAgent = false
            table.insert(warnings, "The character exists but the client agent did not answer yet - gui_* / set_camera tools may need a retry after a few seconds.")
        end
    else
        result.modeInfo = {
            hasPlayer = false,
            hasCharacter = false,
            hasClient = false,
            hasGui = false,
            meaning = "Run mode is a physics + server-script simulation ONLY. There is NO player, NO character, NO client and NO GUI - by design, not a bug.",
            usePlayFor = "For a real player, character, GUI clicks and client output: play_start { mode = 'play' }.",
        }
    end
    return result
end

local function stopPlay()
    if not RunService:IsRunning() then
        return { ok = true, alreadyStopped = true, state = playState() }
    end
    aiPlayIntent = { action = "stop", at = os.time() }

    local warnings = {}
    local usedShortcut = false
    if VirtualInputManager ~= nil then
        usedShortcut = sendKey("F5", 0.06, { "LeftShift" }) == true
    end
    if not usedShortcut then
        table.insert(warnings, "Studio shortcut not available; used RunService:Stop(). Changes made during the test may remain in the place - check the place before saving.")
        pcall(function() RunService:Stop() end)
    end
    local reached = waitForState(false, 15)
    cleanupRuntimeHelpers()
    if not reached then
        return { ok = false, error = "Studio is still running after 15 seconds.", state = playState(), warnings = warnings }
    end
    return { ok = true, state = playState(), warnings = warnings, note = "Test stopped. The place is back in edit mode - persistent edits are allowed again." }
end

-- ---------------------------------------------------------------------------
-- UNIONS (Solid Modeling)
-- ---------------------------------------------------------------------------
local UNION_SOFT_LIMIT = 8
local UNION_HARD_LIMIT = 24

local function collisionFidelityFrom(name)
    local ok, value = pcall(function() return Enum.CollisionFidelity[name or "Default"] end)
    if ok and value then return value end
    return Enum.CollisionFidelity.Default
end

local function renderFidelityFrom(name)
    local ok, value = pcall(function() return Enum.RenderFidelity[name or "Automatic"] end)
    if ok and value then return value end
    return Enum.RenderFidelity.Automatic
end

local UNION_TRIANGLE_WARN = 4000
local UNION_TRIANGLE_REFUSE = 16000

local function estimateTriangles(parts)
    local total = 0
    for _, part in ipairs(parts) do
        if part:IsA("PartOperation") then
            total = total + 4000
        elseif part:IsA("MeshPart") then
            total = total + 1500
        elseif part:IsA("BasePart") then
            local s = part.Size
            local biggest = math.max(s.X, s.Y, s.Z)
            total = total + 24 + math.floor(biggest / 8)
        end
    end
    return total
end

-- Wenn die Teile zu EINEM Block zusammenpassen: der guenstigere Weg ist
-- ein einzelner Part (kein Solid Modeling, kein Verlust der Einzelteile).
local function singleBlockSuggestion(parts)
    local minX, minY, minZ = math.huge, math.huge, math.huge
    local maxX, maxY, maxZ = -math.huge, -math.huge, -math.huge
    local volume = 0
    for _, part in ipairs(parts) do
        if not part:IsA("BasePart") or part:IsA("PartOperation") or part:IsA("MeshPart") then
            return nil
        end
        local s = part.Size
        volume = volume + s.X * s.Y * s.Z
        local c = part.CFrame.Position
        local half = s / 2
        if c.X - half.X < minX then minX = c.X - half.X end
        if c.Y - half.Y < minY then minY = c.Y - half.Y end
        if c.Z - half.Z < minZ then minZ = c.Z - half.Z end
        if c.X + half.X > maxX then maxX = c.X + half.X end
        if c.Y + half.Y > maxY then maxY = c.Y + half.Y end
        if c.Z + half.Z > maxZ then maxZ = c.Z + half.Z end
    end
    local boxVolume = (maxX - minX) * (maxY - minY) * (maxZ - minZ)
    if boxVolume > 0 and math.abs(volume - boxVolume) <= boxVolume * 0.05 then
        return {
            size = { x = maxX - minX, y = maxY - minY, z = maxZ - minZ },
            center = { x = (minX + maxX) / 2, y = (minY + maxY) / 2, z = (minZ + maxZ) / 2 },
            suggestion = "These parts tile into ONE solid block. A single Part of that size does the same job - no solid modeling cost, no one-way merge.",
        }
    end
    return nil
end

local function unionWarnings(parts, kind)
    local warnings = {
        "Solid modeling is one-way: after " .. kind .. " the individual parts are gone. You can no longer read or move them separately - use 'separate' to get them back (properties like colour per part may be lost).",
    }
    if #parts > UNION_SOFT_LIMIT then
        table.insert(warnings, "You are combining " .. tostring(#parts) .. " parts. Large unions are hard to inspect and slow to render. Prefer several small unions grouped in a Model.")
    end
    local totalVolume = 0
    for _, part in ipairs(parts) do
        if part:IsA("BasePart") then
            totalVolume = totalVolume + (part.Size.X * part.Size.Y * part.Size.Z)
        end
    end
    if totalVolume > 200000 then
        table.insert(warnings, "The combined volume is very large. Consider building with plain parts instead - unions of huge geometry hurt performance.")
    end
    return warnings
end

-- Vorpruefung: liefert warnings (Tabelle) oder einen Fehler (code, message, extra).
local function precheckSolid(parts, minimum, args)
    if #parts < minimum then
        return nil, "BAD_ARGS", "Need at least " .. tostring(minimum) .. " parts.", nil
    end
    for _, part in ipairs(parts) do
        if not part:IsA("BasePart") then
            return nil, "BAD_ARGS", "'" .. part.Name .. "' (" .. part.ClassName .. ") is not a BasePart.", nil
        end
    end
    local warnings = {}
    if #parts > UNION_HARD_LIMIT and args.force ~= true then
        return nil, "UNION_BUDGET",
            "Refusing to combine " .. tostring(#parts) .. " parts at once (limit " .. tostring(UNION_HARD_LIMIT)
            .. "). Build in smaller groups so the result stays editable, or pass force=true if you really want this.",
            nil
    end

    -- Anchored: Solid Modeling braucht stehende Teile
    local unanchored = {}
    for _, part in ipairs(parts) do
        if not part.Anchored then table.insert(unanchored, part.Name) end
    end
    if #unanchored > 0 then
        if args.fixAnchored == true then
            for _, part in ipairs(parts) do part.Anchored = true end
            table.insert(warnings, "Anchored " .. tostring(#unanchored) .. " unanchored part(s) (fixAnchored=true): " .. table.concat(unanchored, ", "))
        else
            return nil, "UNION_PRECHECK",
                "These parts are NOT anchored and will fall before/during the solid operation: " .. table.concat(unanchored, ", ")
                .. ". Pass fixAnchored=true to anchor them first (recommended) or anchor them yourself.",
                { parts = unanchored }
        end
    end

    -- Gleicher Parent (Warnung - das Ergebnis kommt in den Parent des ersten Teils)
    local parents = {}
    for _, part in ipairs(parts) do
        if part.Parent then parents[tostring(part.Parent:GetFullName())] = true end
    end
    local parentCount = 0
    for _ in pairs(parents) do parentCount = parentCount + 1 end
    if parentCount > 1 then
        table.insert(warnings, "The parts live in DIFFERENT parents. The result will be placed in the parent of the first part - move the others first if that is not intended.")
    end

    -- Groessen
    local sizeIssues = {}
    for _, part in ipairs(parts) do
        local s = part.Size
        local biggest = math.max(s.X, s.Y, s.Z)
        local smallest = math.min(s.X, s.Y, s.Z)
        if biggest > 500 then table.insert(sizeIssues, part.Name .. " is very large (" .. tostring(biggest) .. " studs)") end
        if smallest < 0.05 then table.insert(sizeIssues, part.Name .. " is extremely thin") end
    end
    if #sizeIssues > 0 then
        table.insert(warnings, "Size warnings: " .. table.concat(sizeIssues, "; ") .. ".")
    end

    -- Dreiecks-Budget
    local triangles = estimateTriangles(parts)
    if triangles > UNION_TRIANGLE_REFUSE and args.force ~= true then
        return nil, "UNION_BUDGET",
            "Estimated " .. tostring(triangles) .. " triangles - above the refusal limit of " .. tostring(UNION_TRIANGLE_REFUSE)
            .. " (the result would be slow to render and nearly impossible to edit). Build in smaller groups, or pass force=true.",
            { estimatedTriangles = triangles, limit = UNION_TRIANGLE_REFUSE }
    end
    if triangles > UNION_TRIANGLE_WARN then
        table.insert(warnings, "Estimated " .. tostring(triangles) .. " triangles (warning limit " .. tostring(UNION_TRIANGLE_WARN)
            .. ") - expect slow rendering. Fewer parts per union is much cheaper.")
    end

    -- Guenstigere Alternative?
    local cheaper = singleBlockSuggestion(parts)
    if cheaper then
        table.insert(warnings, cheaper.suggestion)
    end

    local extra = {}
    extra.estimatedTriangles = triangles
    if cheaper then extra.cheaperAlternative = cheaper end
    return warnings, nil, nil, extra
end


-- ---------------------------------------------------------------------------
-- JOBS UND PERSISTENTER LUA-WORKER
-- Lange Arbeit laeuft als Job im Hintergrund weiter (Timeout koennen nichts
-- toeten). run_lua und Jobs teilen sich EINE persistente Lua-Umgebung:
-- Helfer aus einem frueheren Call (ohne "local") sind spaeter sichtbar.
-- ---------------------------------------------------------------------------
local jobs = {}
local jobSeq = 0
local MAX_JOBS = 16

local function jobSnapshot(job)
    return {
        id         = job.id,
        name       = job.name,
        status     = job.status,
        progress   = job.progress,
        message    = job.message,
        startedAt  = job.startedAt,
        finishedAt = job.finishedAt,
        ageSeconds = job.finishedAt and (os.time() - job.startedAt) or (os.time() - job.startedAt),
    }
end

local function jobsCount()
    local n = 0
    for _ in pairs(jobs) do n = n + 1 end
    return n
end

local function newJob(name, fn)
    jobSeq = jobSeq + 1
    local jobId = "job_" .. tostring(jobSeq)
    local job = {
        id = jobId,
        name = name or "job",
        status = "running",
        progress = 0,
        message = "gestartet",
        startedAt = os.time(),
        finishedAt = nil,
        cancelled = false,
        result = nil,
        error = nil,
        errorCode = nil,
    }
    jobs[jobId] = job
    -- Alte, fertige Jobs raumen (laufende bleiben immer erhalten).
    while true do
        local oldest = nil
        local oldestTime = 0
        for id, j in pairs(jobs) do
            if j.status ~= "running" then
                local t = j.finishedAt or 0
                if oldest == nil or t < oldestTime then
                    oldest = id
                    oldestTime = t
                end
            end
        end
        if oldest and jobsCount() > MAX_JOBS then
            jobs[oldest] = nil
        else
            break
        end
    end

    local function jobProgress(percent, message)
        job.progress = tonumber(percent) or job.progress
        if message then job.message = tostring(message) end
    end
    local function jobCancelled()
        return job.cancelled
    end
    local jobApi = { id = jobId, progress = jobProgress, cancelled = jobCancelled }

    task.spawn(function()
        local okRun, result = pcall(fn, jobApi)
        job.finishedAt = os.time()
        if job.cancelled then
            job.status = "cancelled"
        elseif okRun then
            job.status = "done"
            job.result = result
        else
            job.status = "error"
            job.error = tostring(result)
        end
    end)
    return jobId
end

local function jobsList()
    local list = {}
    for id, job in pairs(jobs) do
        table.insert(list, jobSnapshot(job))
    end
    table.sort(list, function(a, b) return (a.startedAt or 0) > (b.startedAt or 0) end)
    return list
end

-- ---------------------------------------------------------------------------
-- Persistente Lua-Umgebung (run_lua + Jobs teilen sich diese)
-- ---------------------------------------------------------------------------
local function makeLuaEnv()
    return setmetatable({}, { __index = _G })
end
local luaEnv = makeLuaEnv()

local function luaEnvKeys()
    local keys = {}
    for key, _ in pairs(luaEnv) do
        table.insert(keys, tostring(key))
    end
    table.sort(keys)
    return keys
end

-- Fuer lange Arbeit, die als Job laeuft: der Job meldet Fortschritt und
-- prueft job:cancelled() in Schleifen (Lua-Threads lassen sich nicht hart toeten).
-- ---------------------------------------------------------------------------

-- ---------------------------------------------------------------------------
-- WELT-MESSWERKZEUGE
-- Hoehe kommt AUSSCHLIESSLICH per Raycast (ReadVoxels-Indexmathematik ist
-- in diesem Place falsch). Neue Geometrie wird erst zurueckgegeben, wenn
-- sie messbar ist (FillRegion/Create sind nicht in derselben Frame sichtbar).
-- ---------------------------------------------------------------------------
-- FIX 3.2: CanCollide/CanQuery/CanTouch sind Properties von BasePart, KEINE
-- Members von RaycastParams. Die Zuweisung warf in aktuellen Studio-Versionen
-- "X is not a valid member of RaycastParams" und crashte damit JEDE BasePart-
-- Erstellung (create_instance, bulk_create, clone_instance, fill_region).
local function measureRayParams(excludeRefs)
    local params = RaycastParams.new()
    params.FilterType = Enum.RaycastFilterType.Exclude
    params.FilterDescendantsInstances = excludeRefs or {}
    return params
end

local function overlapParamsNew(excludeRefs)
    local params = OverlapParams.new()
    params.FilterType = Enum.RaycastFilterType.Exclude
    params.FilterDescendantsInstances = excludeRefs or {}
    return params
end

local function isWaterLike(inst)
    if inst == nil then return false end
    local okM, material = pcall(function() return inst.Material end)
    if okM and material == Enum.Material.Water then return true end
    local okT, transp = pcall(function() return inst.Transparency end)
    local okS, size = pcall(function() return inst.Size end)
    if okT and okS and transp >= 0.4 and (size.X >= 50 or size.Z >= 50) then
        return true
    end
    return false
end

-- Warten, bis (neue) Geometrie auf Raycasts antwortet.
local function waitMeasurableCore(insts, maxSeconds)
    maxSeconds = tonumber(maxSeconds) or 2
    local startAt = os.clock()
    local frames = 0
    while true do
        frames = frames + 1
        local allReady = true
        for _, inst in ipairs(insts) do
            local okAlive, alive = pcall(function() return inst and inst.Parent ~= nil end)
            if not (okAlive and alive) then
                allReady = false
                break
            end
            local cframe, size = boundsOf(inst)
            local ready = false
            if cframe then
                local params = measureRayParams({ inst })
                local hit = Workspace:Raycast(cframe.Position + Vector3.new(0, size.Y / 2 + 5, 0), Vector3.new(0, -size.Y - 10, 0), params)
                if hit and hit.Instance == inst then ready = true end
            end
            if not ready then
                allReady = false
                break
            end
        end
        if allReady then
            return { ready = true, frames = frames, waitedMs = math.floor((os.clock() - startAt) * 1000) }
        end
        if os.clock() - startAt >= maxSeconds then
            return {
                ready = false,
                frames = frames,
                waitedMs = math.floor((os.clock() - startAt) * 1000),
                note = "New geometry did not answer raycasts immediately. Call verify_measurable on these ids before measuring again.",
            }
        end
        task.wait(0.05)
    end
end

-- FIX 3.2: Messfehler duerfen niemals die Create/Bulk-Ergebnisse zerstoeren.
-- Zuvor crashte ein einziger kaputter Raycast-Weg den ganzen Tool-Call,
-- obwohl die Instanzen längst erstellt waren (die Ids gingen verloren).
local function waitMeasurable(insts, maxSeconds)
    local okRun, result = pcall(waitMeasurableCore, insts or {}, maxSeconds)
    if okRun and type(result) == "table" then
        return result
    end
    return { ready = false, frames = 0, waitedMs = 0, note = "Geometry verification unavailable: " .. tostring(result) }
end

-- ---------------------------------------------------------------------------
-- FORMEN MESSEN (kein Raten): senkrechte Raycasts ueber die Oberflaeche,
-- 5x5-Raster, nur Treffer auf den Teil selbst. Ergebnis pro Instanz gecacht
-- (automatisch neu gemessen bei geaenderter Position/Groesse/Form).
-- ---------------------------------------------------------------------------
local shapeCache = setmetatable({}, { __mode = "k" })

local function shapeKeyOf(inst)
    local cframe, size = boundsOf(inst)
    if not cframe or size == nil then return nil end
    return cframe.Position.X .. "," .. cframe.Position.Y .. "," .. cframe.Position.Z .. "|"
        .. size.X .. "," .. size.Y .. "," .. size.Z .. "|" .. tostring(inst.Shape)
end

local function measureShape(inst)
    if inst == nil or not inst:IsA("BasePart") then return nil end
    local key = shapeKeyOf(inst)
    if key == nil then return nil end
    local cached = shapeCache[inst]
    if cached and cached.key == key then return cached.value end

    local cframe, size = boundsOf(inst)
    local top = cframe.Position.Y + size.Y / 2
    local samples = {}
    for ix = -2, 2 do
        for iz = -2, 2 do
            local x = cframe.Position.X + (ix / 2) * (size.X / 2)
            local z = cframe.Position.Z + (iz / 2) * (size.Z / 2)
            local params = RaycastParams.new()
            params.FilterType = Enum.RaycastFilterType.Include
            params.FilterDescendantsInstances = { inst }
            local hit = Workspace:Raycast(Vector3.new(x, top + 2000, z), Vector3.new(0, -4000, 0), params)
            if hit then
                table.insert(samples, { x = x, z = z, y = hit.Position.Y, ix = ix, iz = iz })
            end
        end
    end

    local value
    if #samples == 0 then
        value = { shape = tostring(inst.Shape), note = "No surface hit from above - could not measure this shape." }
    else
        local minY, maxY = math.huge, -math.huge
        for _, s in ipairs(samples) do
            if s.y < minY then minY = s.y end
            if s.y > maxY then maxY = s.y end
        end
        local flatTol = math.max(0.15, size.Y * 0.01)
        local shapeName = tostring(inst.Shape)
        if (maxY - minY) < flatTol then
            local cornerHit = false
            for _, s in ipairs(samples) do
                if math.abs(s.ix) == 2 and math.abs(s.iz) == 2 then cornerHit = true end
            end
            if shapeName == "Cylinder" and not cornerHit then
                value = {
                    shape = "Cylinder", flatTop = true, axis = "vertical", topY = maxY,
                    note = "Cylinder with a VERTICAL length axis: the flat caps point up and down, the length direction is the part's local Y axis (top/bottom).",
                }
            elseif shapeName == "Ball" then
                value = { shape = "Ball", flatTop = false, note = "Sphere: no faces, no length axis. 'point_at' steuert die -Z-Richtung (front)." }
            else
                value = { shape = shapeName, flatTop = true, topY = maxY, note = "Flat top - an axis-aligned block, no hidden orientation." }
            end
        else
            local high = {}
            for _, s in ipairs(samples) do
                if maxY - s.y <= flatTol + 0.01 then table.insert(high, s) end
            end
            if #high >= 2 then
                local ax, az = high[1].x, high[1].z
                local bx, bz = high[#high].x, high[#high].z
                local axisVec = Vector3.new(bx - ax, 0, bz - az)
                if axisVec.Magnitude < 0.01 then
                    value = {
                        shape = shapeName, highPoint = { x = ax, z = az }, topY = maxY, bottomY = minY,
                        note = "Single highest point - if this is a Cylinder it lies horizontally (length axis is horizontal).",
                    }
                else
                    local highEdge = { a = { x = ax, z = az }, b = { x = bx, z = bz } }
                    if shapeName == "Wedge" then
                        local midX, midZ, n = 0, 0, 0
                        for _, s in ipairs(samples) do
                            if maxY - s.y > flatTol + 0.01 then midX = midX + s.x; midZ = midZ + s.z; n = n + 1 end
                        end
                        if n > 0 then
                            midX, midZ = midX / n, midZ / n
                            local toLow = Vector3.new(midX - (ax + bx) / 2, 0, midZ - (az + bz) / 2)
                            if toLow.Magnitude > 0.01 then
                                local slopeDir = toLow.Unit
                                value = {
                                    shape = "Wedge", highEdge = highEdge, slopeDir = { x = slopeDir.X, z = slopeDir.Z },
                                    topY = maxY, bottomY = minY,
                                    note = "Wedge (ramp): HIGH edge from (" .. string.format("%.1f", ax) .. ", " .. string.format("%.1f", az)
                                        .. ") to (" .. string.format("%.1f", bx) .. ", " .. string.format("%.1f", bz)
                                        .. "). The slope goes DOWN toward (" .. string.format("%.2f", slopeDir.X) .. ", " .. string.format("%.2f", slopeDir.Z) .. ").",
                                }
                            else
                                value = {
                                    shape = "Wedge", highEdge = highEdge, topY = maxY, bottomY = minY,
                                    note = "Wedge (ramp): HIGH edge from (" .. string.format("%.1f", ax) .. ", " .. string.format("%.1f", az)
                                        .. ") to (" .. string.format("%.1f", bx) .. ", " .. string.format("%.1f", bz) .. ").",
                                }
                            end
                        else
                            value = {
                                shape = "Wedge", highEdge = highEdge, topY = maxY, bottomY = minY,
                                note = "Wedge (ramp): HIGH edge from (" .. string.format("%.1f", ax) .. ", " .. string.format("%.1f", az)
                                    .. ") to (" .. string.format("%.1f", bx) .. ", " .. string.format("%.1f", bz) .. ").",
                            }
                        end
                    else
                        value = {
                            shape = shapeName, highEdge = highEdge, topY = maxY, bottomY = minY,
                            note = shapeName .. ": the highest points form a line from (" .. string.format("%.1f", ax) .. ", " .. string.format("%.1f", az)
                                .. ") to (" .. string.format("%.1f", bx) .. ", " .. string.format("%.1f", bz)
                                .. ") - that line is the LENGTH axis of the shape (e.g. a horizontal Cylinder).",
                        }
                    end
                end
            else
                value = {
                    shape = shapeName, topY = maxY, bottomY = minY,
                    note = "The top surface is not flat and no clear high edge was measured. Use describe_orientation for the exact face directions.",
                }
            end
        end
    end
    shapeCache[inst] = { key = key, value = value }
    return value
end

-- Klartext fuer eine Welt-Richtung (0° = -Z = weg von der Standardkamera).
local function dirHeading(v)
    local h = Vector3.new(v.X, 0, v.Z)
    if h.Magnitude < 0.05 then
        if v.Y > 0.5 then return "straight UP"
        elseif v.Y < -0.5 then return "straight DOWN"
        else return "flat (no clear direction)" end
    end
    local angle = math.atan2(h.X, -h.Z) * 180 / math.pi
    if angle < 0 then angle = angle + 360 end
    local names = {
        "north (away from the default camera)",
        "north-east",
        "east (toward +X)",
        "south-east",
        "south (toward the default camera)",
        "south-west",
        "west (toward -X)",
        "north-west",
    }
    local index = math.floor(angle / 45 + 0.5)
    if index > 8 then index = 8 end
    return string.format("%s (heading %.0f degrees from north)", names[index], angle)
end

local function facesOf(cframe)
    return {
        front  = dirHeading(cframe:VectorToWorldSpace(Vector3.new(0, 0, -1))),
        back   = dirHeading(cframe:VectorToWorldSpace(Vector3.new(0, 0, 1))),
        left   = dirHeading(cframe:VectorToWorldSpace(Vector3.new(-1, 0, 0))),
        right  = dirHeading(cframe:VectorToWorldSpace(Vector3.new(1, 0, 0))),
        top    = dirHeading(cframe:VectorToWorldSpace(Vector3.new(0, 1, 0))),
        bottom = dirHeading(cframe:VectorToWorldSpace(Vector3.new(0, -1, 0))),
    }
end

-- ---------------------------------------------------------------------------
-- WERKZEUGE
-- ---------------------------------------------------------------------------
local tools = {}

local function ok(result, warnings)
    return { ok = true, result = result, warnings = warnings }
end

local function fail(message, extra)
    local response = { ok = false, error = message }
    if extra then
        for key, value in pairs(extra) do response[key] = value end
    end
    return response
end

-- Fehler mit Code: die KI reagiert auf den code, nicht auf den Text.
local function failCode(code, message, extra)
    local response = { ok = false, code = code, error = message }
    if extra then
        for key, value in pairs(extra) do response[key] = value end
    end
    return response
end

local function waypoint(name)
    if ChangeHistoryService == nil then return end
    pcall(function() ChangeHistoryService:SetWaypoint("Arena: " .. tostring(name)) end)
end

-- ------------------------- Informationen -----------------------------------
tools.get_place_info = function()
    return ok({
        name       = game.Name,
        placeId    = game.PlaceId,
        gameId     = game.GameId,
        creatorId  = game.CreatorId,
        rootPath   = "game",
        pluginVersion = ARENA_VERSION,
        state      = playState(),
        capabilities = capabilities,
    })
end

tools.bridge_info = tools.get_place_info

tools.get_tree = function(args)
    local root, err = resolveRef(args.rootRef or args.rootPath or args.ref or "game")
    if not root then return fail(err) end
    local state = { count = 0, maxNodes = tonumber(args.maxNodes) or 3000, truncated = false }
    local node = treeNode(root, 0, tonumber(args.maxDepth) or 6, state, args.includeProperties == true, args.includeSource == true)
    local warnings = nil
    if state.truncated then
        warnings = { "Tree was cut off at " .. tostring(state.maxNodes) .. " nodes. Read smaller sub-trees (rootRef) or raise maxNodes." }
    end
    return ok({ tree = node, nodeCount = state.count, truncated = state.truncated }, warnings)
end

-- FIX 3.2: Gemeinsamer Suchkern - wird von tools.search UND von den
-- Selektor-Referenzen { query= } / { tag= } / { className=, rootRef= } benutzt.
-- (Zuweisung an die Vorwaerts-Deklaration ueben, damit alle Funktionen im
-- Chunk dasselbe Upvalue sehen.)
findMatches = function(root, query, className, tag, limit, exact)
    local matches = {}
    local total = 0
    local q = string.lower(tostring(query or ""))
    local list = root:GetDescendants()
    for _, inst in ipairs(list) do
        local nameMatch = true
        if q ~= "" then
            local lowerName = string.lower(inst.Name)
            if exact then
                nameMatch = (lowerName == q)
            else
                nameMatch = string.find(lowerName, q, 1, true) ~= nil
            end
        end
        local classMatch = true
        if className then
            local isOk, isType = pcall(function() return inst:IsA(className) end)
            classMatch = (inst.ClassName == className) or (isOk and isType)
        end
        local tagMatch = true
        if tag then
            local tagOk, hasTag = pcall(function() return CollectionService:HasTag(inst, tag) end)
            tagMatch = tagOk and hasTag
        end
        if nameMatch and classMatch and tagMatch then
            total = total + 1
            if #matches < limit then
                table.insert(matches, inst)
            end
        end
    end
    return matches, total
end

-- Loest eine Selektor-Referenz auf eine Liste von Instanzen auf.
-- Erfolg: (InstanzListe, Gesamtzahl). Fehler: (nil, Fehlermeldung).
resolveSelector = function(ref, limit)
    limit = limit or 500
    local root = game
    if ref.rootRef or ref.rootPath then
        local r, err = resolveRef(ref.rootRef or ref.rootPath)
        if r then
            root = r
        else
            return nil, "Selector rootRef not found: " .. tostring(err)
        end
    end
    local matches, total = findMatches(root, ref.query, ref.className, ref.tag, limit, ref.exact == true)
    if #matches == 0 then
        return nil, "Selector matched nothing."
    end
    return matches, total
end

tools.search = function(args)
    local root, err = resolveRef(args.rootRef or args.rootPath or "game")
    if not root then return fail(err) end
    local query = string.lower(tostring(args.query or ""))
    local limit = tonumber(args.limit) or 200
    local found, total = findMatches(root, query, args.className, args.tag, limit, args.exact == true)
    local matches = {}
    for _, inst in ipairs(found) do
        local entry = describeRef(inst)
        if inst:IsA("BasePart") then
            entry.position = { x = inst.Position.X, y = inst.Position.Y, z = inst.Position.Z }
            entry.size = { x = inst.Size.X, y = inst.Size.Y, z = inst.Size.Z }
        end
        if inst:IsA("LuaSourceContainer") then
            local sourceOk, source = pcall(function() return inst.Source end)
            if sourceOk then entry.sourceLines = select(2, string.gsub(source, "\n", "\n")) + 1 end
        end
        table.insert(matches, entry)
    end

    local warnings = nil
    if total > #matches then
        warnings = { "Found " .. tostring(total) .. " matches, returning the first " .. tostring(#matches) .. ". Raise 'limit' to get more." }
    end
    if total > 1 and query ~= "" then
        local sameName = 0
        for _, entry in ipairs(matches) do
            if string.lower(entry.name) == query then sameName = sameName + 1 end
        end
        if sameName > 1 then
            warnings = warnings or {}
            table.insert(warnings, "Several objects share the name '" .. tostring(args.query) .. "'. Always address them by their id (e.g. \"#42\") - the path alone is ambiguous.")
        end
    end
    return ok({ matches = matches, totalMatches = total, returned = #matches }, warnings)
end

tools.get_instance = function(args)
    local inst, err = resolveRef(args.ref or args.path)
    if not inst then return fail(err) end
    local children = {}
    for _, child in ipairs(inst:GetChildren()) do
        local entry = describeRef(child)
        entry.childCount = #child:GetChildren()
        table.insert(children, entry)
    end
    local warnings = nil
    if inst.Parent and nameCollisions(inst.Parent, inst.Name) > 1 then
        warnings = { "There are several siblings named '" .. inst.Name .. "'. Use the id " .. idOf(inst) .. " to address exactly this one." }
    end
    return ok({
        id = idOf(inst),
        name = inst.Name,
        className = inst.ClassName,
        path = pathOf(inst),
        parent = inst.Parent and describeRef(inst.Parent) or nil,
        properties = readProps(inst, args.includeSource == true, args.includeAllProperties == true),
        children = children,
        childCount = #children,
    }, warnings)
end

tools.get_children = function(args)
    local inst, err = resolveRef(args.ref or args.path or "game")
    if not inst then return fail(err) end
    local offset = tonumber(args.offset) or 0
    local limit = tonumber(args.limit) or 500
    local all = inst:GetChildren()
    local items = {}
    for index = offset + 1, math.min(#all, offset + limit) do
        local entry = describeRef(all[index])
        entry.childCount = #all[index]:GetChildren()
        table.insert(items, entry)
    end
    return ok({ children = items, total = #all, offset = offset, returned = #items })
end

tools.get_properties = function(args)
    local list, errors = resolveMany(args.refs or args.ref)
    local wanted = args.properties
    local results = {}
    for _, inst in ipairs(list) do
        local entry = describeRef(inst)
        entry.properties = {}
        if type(wanted) == "table" and #wanted > 0 then
            for _, property in ipairs(wanted) do
                local okRead, value = pcall(function() return inst[property] end)
                if okRead then
                    entry.properties[property] = encodeValue(value)
                else
                    entry.properties[property] = nil
                end
            end
        else
            entry.properties = readProps(inst, args.includeSource == true, false)
        end
        table.insert(results, entry)
    end
    return ok({ items = results, errors = errors })
end

tools.get_selection = function()
    local items = {}
    for _, inst in ipairs(Selection:Get()) do
        table.insert(items, describeRef(inst))
    end
    return ok({ selection = items, count = #items })
end

tools.select_instance = function(args)
    local list, errors = resolveMany(args.refs or args.ref or args.path)
    if #list == 0 then return fail("Nothing to select. " .. table.concat(errors, " ")) end
    if args.add == true then
        local current = Selection:Get()
        for _, inst in ipairs(list) do table.insert(current, inst) end
        Selection:Set(current)
    else
        Selection:Set(list)
    end
    local items = {}
    for _, inst in ipairs(list) do table.insert(items, describeRef(inst)) end
    return ok({ selected = items, errors = errors })
end

tools.resolve_ref = function(args)
    local inst, err = resolveRef(args.ref or args.path or args.id)
    if not inst then return fail(err) end
    return ok(describeRef(inst))
end

-- Textbeschreibung der Szene: die bessere Alternative zu Screenshots.
tools.describe_scene = function(args)
    local root, err = resolveRef(args.rootRef or "game.Workspace")
    if not root then return fail(err) end
    local maxItems = tonumber(args.maxItems) or 120
    local lines = {}
    local items = {}
    local counts = {}

    local function record(inst, depth)
        local className = inst.ClassName
        counts[className] = (counts[className] or 0) + 1
        if #items >= maxItems then return end
        local entry = describeRef(inst)
        local text = string.rep("  ", depth) .. inst.Name .. " [" .. className .. "] " .. idOf(inst)
        if inst:IsA("BasePart") then
            entry.position = { x = inst.Position.X, y = inst.Position.Y, z = inst.Position.Z }
            entry.size = { x = inst.Size.X, y = inst.Size.Y, z = inst.Size.Z }
            text = text .. string.format(" pos(%.1f, %.1f, %.1f) size(%.1f, %.1f, %.1f) %s %s",
                inst.Position.X, inst.Position.Y, inst.Position.Z,
                inst.Size.X, inst.Size.Y, inst.Size.Z,
                tostring(inst.Material.Name),
                tostring(inst.BrickColor.Name))
            if inst.Transparency > 0 then
                text = text .. string.format(" transparency %.2f", inst.Transparency)
            end
            if not inst.Anchored then text = text .. " NOT-ANCHORED" end
        elseif inst:IsA("Model") then
            local cframe, size = boundsOf(inst)
            if cframe then
                text = text .. string.format(" center(%.1f, %.1f, %.1f) extent(%.1f, %.1f, %.1f) parts=%d",
                    cframe.Position.X, cframe.Position.Y, cframe.Position.Z, size.X, size.Y, size.Z, #inst:GetDescendants())
            end
        elseif inst:IsA("LuaSourceContainer") then
            local sourceOk, source = pcall(function() return inst.Source end)
            if sourceOk then
                text = text .. " lines=" .. tostring(select(2, string.gsub(source, "\n", "\n")) + 1)
            end
        end
        table.insert(items, entry)
        table.insert(lines, text)
    end

    local maxDepth = tonumber(args.maxDepth) or 2
    local function walk(inst, depth)
        for _, child in ipairs(inst:GetChildren()) do
            record(child, depth)
            if depth < maxDepth then
                walk(child, depth + 1)
            end
        end
    end
    record(root, 0)
    walk(root, 1)

    local camera = Workspace.CurrentCamera
    local cameraText = "unknown"
    if camera then
        local position = camera.CFrame.Position
        local look = camera.CFrame.LookVector
        cameraText = string.format("camera at (%.1f, %.1f, %.1f) looking (%.2f, %.2f, %.2f)",
            position.X, position.Y, position.Z, look.X, look.Y, look.Z)
    end

    local summary = {}
    for className, count in pairs(counts) do
        table.insert(summary, className .. " x" .. tostring(count))
    end
    table.sort(summary)

    return ok({
        text = cameraText .. "\n" .. table.concat(lines, "\n"),
        items = items,
        classSummary = summary,
        truncated = (#items >= maxItems),
        hint = "This textual description replaces screenshots. It is far more reliable for an AI than an image.",
    })
end

tools.scene_stats = function(args)
    local root, err = resolveRef(args.rootRef or "game.Workspace")
    if not root then return failCode("REF_NOT_FOUND", err) end
    local counts = {}
    local total = 0
    local totalParts = 0
    local operations = 0
    for _, inst in ipairs(root:GetDescendants()) do
        total = total + 1
        counts[inst.ClassName] = (counts[inst.ClassName] or 0) + 1
        if inst:IsA("BasePart") then
            totalParts = totalParts + 1
            if inst:IsA("PartOperation") then operations = operations + 1 end
        end
    end
    local modelList = {}
    for _, inst in ipairs(root:GetDescendants()) do
        if inst:IsA("Model") and (inst.Parent == nil or not inst.Parent:IsA("Model")) then
            local n = 0
            for _, d in ipairs(inst:GetDescendants()) do
                if d:IsA("BasePart") then n = n + 1 end
            end
            table.insert(modelList, { model = describeRef(inst), parts = n })
        end
    end
    table.sort(modelList, function(a, b) return a.parts > b.parts end)
    local topModels = {}
    for i = 1, math.min(10, #modelList) do table.insert(topModels, modelList[i]) end
    local classSummary = {}
    for className, count in pairs(counts) do
        table.insert(classSummary, { className = className, count = count })
    end
    table.sort(classSummary, function(a, b) return a.count > b.count end)
    local summaryTop = {}
    for i = 1, math.min(25, #classSummary) do table.insert(summaryTop, classSummary[i]) end
    return ok({
        totalDescendants = total,
        totalParts = totalParts,
        partOperations = operations,
        models = #modelList,
        topModels = topModels,
        classes = summaryTop,
        note = "For very big places (15.000+ parts) prefer targeted queries (search with tag/className, get_tree with rootRef+maxDepth) over full dumps.",
    })
end

tools.viewport_info = function()
    local camera = Workspace.CurrentCamera
    if camera == nil then return fail("No camera found.") end
    local looking = {}
    local origin = camera.CFrame.Position
    local direction = camera.CFrame.LookVector * 500
    local params = RaycastParams.new()
    local hit = Workspace:Raycast(origin, direction, params)
    if hit then
        looking = {
            instance = describeRef(hit.Instance),
            position = { x = hit.Position.X, y = hit.Position.Y, z = hit.Position.Z },
            distance = (hit.Position - origin).Magnitude,
            material = tostring(hit.Material),
        }
    end
    return ok({
        camera = encodeValue(camera.CFrame),
        fieldOfView = camera.FieldOfView,
        viewportSize = { x = camera.ViewportSize.X, y = camera.ViewportSize.Y },
        lookingAt = looking,
    })
end

tools.get_bounds = function(args)
    local list, errors = resolveMany(args.refs or args.ref)
    if #list == 0 then return fail("No instance resolved. " .. table.concat(errors, " ")) end
    local items = {}
    for _, inst in ipairs(list) do
        table.insert(items, boundsInfo(inst))
    end
    if #items == 1 then
        return ok(items[1])
    end
    return ok({ items = items, errors = errors })
end

tools.measure = function(args)
    local a, errA = resolveRef(args.refA or args.ref)
    local b, errB = resolveRef(args.refB or args.targetRef)
    if not a then return fail(errA) end
    if not b then return fail(errB) end
    local ca = getPivotOf(a)
    local cb = getPivotOf(b)
    if ca == nil or cb == nil then return fail("Both instances need a position.") end
    local delta = cb.Position - ca.Position
    return ok({
        distance = delta.Magnitude,
        delta = { x = delta.X, y = delta.Y, z = delta.Z },
        from = describeRef(a),
        to = describeRef(b),
    })
end

tools.raycast = function(args)
    local origin = decodeValue(args.origin)
    local direction = decodeValue(args.direction)
    if typeof(origin) ~= "Vector3" or typeof(direction) ~= "Vector3" then
        return fail("origin and direction must be {x,y,z}.")
    end
    local params = RaycastParams.new()
    local ignoreList, _ = resolveMany(args.ignore)
    if #ignoreList > 0 then
        params.FilterType = Enum.RaycastFilterType.Exclude
        params.FilterDescendantsInstances = ignoreList
    end
    local hit = Workspace:Raycast(origin, direction, params)
    if hit == nil then
        return ok({ hit = false })
    end
    return ok({
        hit = true,
        instance = describeRef(hit.Instance),
        position = { x = hit.Position.X, y = hit.Position.Y, z = hit.Position.Z },
        normal = { x = hit.Normal.X, y = hit.Normal.Y, z = hit.Normal.Z },
        distance = (hit.Position - origin).Magnitude,
        material = tostring(hit.Material),
    })
end


-- ------------------------- Raumabfragen (Batch/Filter/Toleranz) ----------
local function filterMatches(inst, filter)
    if filter == nil then return true end
    if filter.className then
        local wanted = tostring(filter.className)
        local okIs, isType = pcall(function() return inst:IsA(wanted) end)
        if not (inst.ClassName == wanted or (okIs and isType)) then return false end
    end
    if filter.tag then
        local okTag, hasTag = pcall(function() return CollectionService:HasTag(inst, tostring(filter.tag)) end)
        if not (okTag and hasTag) then return false end
    end
    if filter.tags then
        for _, tag in ipairs(filter.tags) do
            local okTag, hasTag = pcall(function() return CollectionService:HasTag(inst, tostring(tag)) end)
            if not (okTag and hasTag) then return false end
        end
    end
    return true
end

local function resolveExcluded(exclude)
    local list = {}
    local exList, _ = resolveMany(exclude)
    for _, inst in ipairs(exList) do table.insert(list, inst) end
    return list
end

local function collectInBox(minVec, maxVec, filter, exclude, limit)
    limit = tonumber(limit) or 200
    local params = overlapParamsNew(resolveExcluded(exclude))
    local found = {}
    local total = 0
    local parts = Workspace:GetPartBoundsInBox((minVec + maxVec) / 2, (maxVec - minVec), params)
    for _, inst in ipairs(parts) do
        if filterMatches(inst, filter) then
            total = total + 1
            if #found < limit then
                local entry = describeRef(inst)
                local cf, size = boundsOf(inst)
                if cf and size then
                    entry.position = { x = cf.Position.X, y = cf.Position.Y, z = cf.Position.Z }
                    entry.size = { x = size.X, y = size.Y, z = size.Z }
                end
                table.insert(found, entry)
            end
        end
    end
    return found, total
end

tools.parts_in_box = function(args)
    local minVec = decodeValue(args.min)
    local maxVec = decodeValue(args.max)
    if typeof(minVec) ~= "Vector3" or typeof(maxVec) ~= "Vector3" then
        return failCode("BAD_ARGS", "min and max must be {x,y,z}.")
    end
    local found, total = collectInBox(minVec, maxVec, args.filter, args.exclude, args.limit)
    return ok({ items = found, found = #found, totalMatches = total, clear = (total == 0) })
end

tools.parts_in_sphere = function(args)
    local center = decodeValue(args.center)
    if typeof(center) ~= "Vector3" then return failCode("BAD_ARGS", "center must be {x,y,z}.") end
    local radius = tonumber(args.radius) or 10
    local half = Vector3.new(radius, radius, radius)
    local found, _ = collectInBox(center - half, center + half, args.filter, args.exclude, math.max(tonumber(args.limit) or 200, 500))
    local inside = {}
    for _, entry in ipairs(found) do
        local delta = Vector3.new(entry.position.x - center.X, entry.position.y - center.Y, entry.position.z - center.Z)
        local tolerance = 0
        if entry.size then tolerance = (entry.size.x + entry.size.y + entry.size.z) / 6 end
        if delta.Magnitude <= radius + tolerance then
            table.insert(inside, entry)
        end
    end
    return ok({
        items = inside,
        found = #inside,
        note = "Sphere test: part-center distance plus half the part extent (approximate - a box corner can poke through).",
    })
end

tools.nearest_parts = function(args)
    local from = decodeValue(args.position)
    if typeof(from) ~= "Vector3" and (args.ref or args.fromRef) then
        local inst, err = resolveRef(args.ref or args.fromRef)
        if not inst then return failCode("REF_NOT_FOUND", err) end
        local cf = getPivotOf(inst)
        if cf then from = cf.Position end
    end
    if typeof(from) ~= "Vector3" then return failCode("BAD_ARGS", "Need position {x,y,z} or ref/fromRef.") end
    local radius = tonumber(args.radius) or 50
    local limit = tonumber(args.limit) or 20
    local found, _ = collectInBox(
        from - Vector3.new(radius, radius, radius),
        from + Vector3.new(radius, radius, radius),
        args.filter, args.exclude, math.max(limit, 500))
    local scored = {}
    for _, entry in ipairs(found) do
        local delta = Vector3.new(entry.position.x - from.X, entry.position.y - from.Y, entry.position.z - from.Z)
        entry.distance = math.floor(delta.Magnitude * 100) / 100
        table.insert(scored, entry)
    end
    table.sort(scored, function(a, b) return a.distance < b.distance end)
    local out = {}
    for i = 1, math.min(limit, #scored) do table.insert(out, scored[i]) end
    return ok({ items = out, count = #out, from = { x = from.X, y = from.Y, z = from.Z } })
end

tools.what_is_in_the_way = function(args)
    local pointA = decodeValue(args.from)
    if typeof(pointA) ~= "Vector3" and args.fromRef then
        local inst, err = resolveRef(args.fromRef)
        if not inst then return failCode("REF_NOT_FOUND", err) end
        local cf = getPivotOf(inst)
        if cf then pointA = cf.Position end
    end
    local pointB = decodeValue(args.to)
    if typeof(pointB) ~= "Vector3" and args.toRef then
        local inst, err = resolveRef(args.toRef)
        if not inst then return failCode("REF_NOT_FOUND", err) end
        local cf = getPivotOf(inst)
        if cf then pointB = cf.Position end
    end
    if typeof(pointA) ~= "Vector3" or typeof(pointB) ~= "Vector3" then
        return failCode("BAD_ARGS", "Need from/to as {x,y,z} or fromRef/toRef.")
    end
    local dir = pointB - pointA
    local length = dir.Magnitude
    if length < 0.01 then return failCode("BAD_ARGS", "from and to are the same point.") end
    local width = tonumber(args.width) or 2
    local exList = resolveExcluded(args.exclude)
    if args.fromRef then
        local instA = resolveRef(args.fromRef)
        if instA then table.insert(exList, instA) end
    end
    if args.toRef then
        local instB = resolveRef(args.toRef)
        if instB then table.insert(exList, instB) end
    end
    local lo = Vector3.new(math.min(pointA.X, pointB.X), math.min(pointA.Y, pointB.Y), math.min(pointA.Z, pointB.Z))
        - Vector3.new(width / 2, width / 2, width / 2)
    local hi = Vector3.new(math.max(pointA.X, pointB.X), math.max(pointA.Y, pointB.Y), math.max(pointA.Z, pointB.Z))
        + Vector3.new(width / 2, width / 2, width / 2)
    local params = overlapParamsNew(exList)
    local limit = tonumber(args.limit) or 50
    local found = {}
    local parts = Workspace:GetPartBoundsInBox((lo + hi) / 2, (hi - lo), params)
    for _, inst in ipairs(parts) do
        if filterMatches(inst, args.filter) then
            local cf = getPivotOf(inst)
            if cf then
                local rel = cf.Position - pointA
                local t = rel:Dot(dir) / (length * length)
                if t >= -0.05 and t <= 1.05 then
                    local tc = math.max(0, math.min(1, t))
                    local closest = pointA + dir * tc
                    local dist = (cf.Position - closest).Magnitude
                    local entry = describeRef(inst)
                    entry.position = { x = cf.Position.X, y = cf.Position.Y, z = cf.Position.Z }
                    entry.distanceFromLine = math.floor(dist * 100) / 100
                    table.insert(found, entry)
                end
            end
        end
        if #found >= limit then break end
    end
    return ok({
        items = found,
        count = #found,
        clear = (#found == 0),
        note = "Axis-aligned box around the line (width on every axis); A and B are excluded.",
    })
end

tools.raycast_many = function(args)
    local casts = args.casts or {}
    if #casts == 0 then
        return failCode("BAD_ARGS", "casts must be a list of { origin = {x,y,z}, direction = {x,y,z} }.")
    end
    if #casts > 500 then
        return failCode("REGION_LIMIT", "Too many casts (" .. tostring(#casts) .. ", max 500 per call).")
    end
    local params = measureRayParams(resolveExcluded(args.exclude))
    local hits = {}
    local hitCount = 0
    for index, cast in ipairs(casts) do
        local origin = decodeValue(cast.origin)
        local direction = decodeValue(cast.direction)
        if typeof(origin) ~= "Vector3" or typeof(direction) ~= "Vector3" then
            table.insert(hits, { index = index, error = "origin/direction must be {x,y,z}" })
        else
            local hit = Workspace:Raycast(origin, direction, params)
            if hit then
                hitCount = hitCount + 1
                table.insert(hits, {
                    index = index, hit = true,
                    instance = describeRef(hit.Instance),
                    position = { x = hit.Position.X, y = hit.Position.Y, z = hit.Position.Z },
                    normal = { x = hit.Normal.X, y = hit.Normal.Y, z = hit.Normal.Z },
                    distance = (hit.Position - origin).Magnitude,
                    material = tostring(hit.Material),
                    waterLike = isWaterLike(hit.Instance),
                })
            else
                table.insert(hits, { index = index, hit = false })
            end
        end
    end
    return ok({ results = hits, count = #hits, hitCount = hitCount })
end

tools.ground_height = function(args)
    local positions = args.positions or {}
    if #positions == 0 and args.min and args.max then
        local minVec = decodeValue(args.min)
        local maxVec = decodeValue(args.max)
        if typeof(minVec) ~= "Vector3" or typeof(maxVec) ~= "Vector3" then
            return failCode("BAD_ARGS", "Need positions (a list of {x,y,z}) or min+max {x,y,z} with step.")
        end
        local step = tonumber(args.step) or 4
        if step < 0.5 then step = 0.5 end
        local x = math.min(minVec.X, maxVec.X)
        local z = math.min(minVec.Z, maxVec.Z)
        local maxX = math.max(minVec.X, maxVec.X)
        local maxZ = math.max(minVec.Z, maxVec.Z)
        while x <= maxX + 0.001 do
            while z <= maxZ + 0.001 do
                table.insert(positions, { x = x, y = minVec.Y + 400, z = z })
                z = z + step
            end
            x = x + step
        end
    end
    if #positions == 0 then
        return failCode("BAD_ARGS", "Need positions (a list of {x,y,z}; the ray starts there and goes straight down) or min/max+step for a grid.")
    end
    if #positions > 4000 then
        return failCode("REGION_LIMIT", "Too many sample points (" .. tostring(#positions) .. ", max 4000). Raise the step or split the area.")
    end
    local params = measureRayParams(resolveExcluded(args.exclude))
    local results = {}
    for _, p in ipairs(positions) do
        local vec = decodeValue(p)
        if typeof(vec) == "Vector3" then
            local hit = Workspace:Raycast(vec, Vector3.new(0, -4000, 0), params)
            if hit then
                table.insert(results, {
                    position = { x = vec.X, y = vec.Y, z = vec.Z },
                    groundY = hit.Position.Y,
                    ground = describeRef(hit.Instance),
                    material = tostring(hit.Material),
                    waterLike = isWaterLike(hit.Instance),
                })
            else
                table.insert(results, { position = { x = vec.X, y = vec.Y, z = vec.Z }, groundY = nil, note = "no surface below" })
            end
        end
    end
    return ok({
        heights = results,
        count = #results,
        hint = "Heights are RAYCAST results - the only allowed way to get world Y in this place.",
    })
end

tools.measure_height = function(args)
    local inst, err = resolveRef(args.ref)
    if not inst then return failCode("REF_NOT_FOUND", err) end
    local cframe, size = boundsOf(inst)
    if not cframe or size == nil then return failCode("BAD_ARGS", "Instance has no geometry.") end
    local params = measureRayParams({ inst })
    local origin = cframe.Position + Vector3.new(0, -size.Y / 2 - 1, 0)
    local hit = Workspace:Raycast(origin, Vector3.new(0, -4000, 0), params)
    local result = {
        instance = describeRef(inst),
        top = cframe.Position.Y + size.Y / 2,
        bottom = cframe.Position.Y - size.Y / 2,
        height = size.Y,
    }
    if hit then
        result.groundY = hit.Position.Y
        result.heightAboveGround = result.bottom - hit.Position.Y
        result.ground = describeRef(hit.Instance)
        result.waterLike = isWaterLike(hit.Instance)
    else
        result.note = "No surface found below."
    end
    return ok(result)
end

tools.verify_measurable = function(args)
    local list, errors = resolveMany(args.refs or args.ref)
    if #list == 0 then return failCode("REF_NOT_FOUND", "Nothing resolved. " .. table.concat(errors, " ")) end
    local check = {}
    for i = 1, math.min(10, #list) do table.insert(check, list[i]) end
    local info = waitMeasurable(check, tonumber(args.seconds) or 2)
    return ok({ checked = #list, geometry = info })
end

-- ------------------------- Erstellen / Aendern ------------------------------
local function applyProperties(inst, properties)
    local problems = {}
    if type(properties) ~= "table" then return problems end
    for key, value in pairs(properties) do
        if key ~= "ClassName" and key ~= "Parent" then
            local okSet, err = setProperty(inst, key, value)
            if not okSet then
                table.insert(problems, key .. ": " .. tostring(err))
            end
        end
    end
    return problems
end

local function createOne(spec)
    local parent, err = resolveRef(spec.parentRef or spec.parentPath or "game.Workspace")
    if not parent then return nil, err end
    local className = spec.className or "Part"
    local created = nil
    local createOk, createErr = pcall(function()
        created = Instance.new(className)
    end)
    if not createOk or created == nil then
        return nil, "Cannot create '" .. tostring(className) .. "': " .. tostring(createErr)
    end
    created.Name = spec.name or className
    local problems = applyProperties(created, spec.properties)
    created.Parent = parent
    local entry = describeRef(created)
    entry.propertyProblems = (#problems > 0) and problems or nil
    return entry
end

tools.create_instance = function(args)
    local count = tonumber(args.count) or 1
    if count <= 1 then
        local entry, err = createOne(args)
        if not entry then return fail(err) end
        waypoint("create " .. tostring(args.className))
        local createdInst = resolveRef(entry.id)
        local geometry = waitMeasurable({ createdInst }, 2)
        entry.geometry = geometry
        return ok(entry)
    end
    local created = {}
    local createdInsts = {}
    local offset = decodeValue(args.offset) or Vector3.new(0, 0, 0)
    for index = 1, count do
        local spec = {
            parentRef = args.parentRef or args.parentPath,
            className = args.className,
            name = (args.name or args.className or "Part") .. tostring(index),
            properties = args.properties,
        }
        local entry, err = createOne(spec)
        if entry then
            local inst = resolveRef(entry.id)
            if inst and inst:IsA("BasePart") then
                if typeof(offset) == "Vector3" and offset.Magnitude > 0 then
                    inst.Position = inst.Position + offset * (index - 1)
                end
                if #createdInsts < 8 then table.insert(createdInsts, inst) end
            end
            table.insert(created, entry)
        end
    end
    waypoint("create " .. tostring(count) .. "x " .. tostring(args.className))
    local geometry = waitMeasurable(createdInsts, 2)
    return ok({ created = created, count = #created, geometry = geometry })
end

tools.bulk_create = function(args)
    local items = args.items or args.instances or {}

    -- FIX 3.2: Doku-Vertrag endlich umgesetzt:
    --   * template als SPEZ-Tabelle { className, properties, parentRef } + count
    --   * grid mit { rows, columns, spacingX, spacingZ } (frueher nur rows/cols,
    --     obwohl die Doku "columns" sagte -> Grids lieferten still 1 Teil)
    --   * nameTemplate "{n}" (frueher wurde nur "$" ersetzt)
    local templateSpec = (type(args.template) == "table") and args.template or {}
    local grid = args.grid
    local wantCount = tonumber(args.count)
    if #items == 0 and (type(grid) == "table" or (wantCount and wantCount > 0)) then
        local origin = decodeValue(args.origin)
        local className = args.className or templateSpec.className or "Part"
        local baseProps = args.properties or templateSpec.properties
        local nameTemplate = tostring(args.nameTemplate or "Part")
        local cells = {}
        if type(grid) == "table" then
            if typeof(origin) ~= "Vector3" then
                return failCode("BAD_ARGS", "grid needs origin {x,y,z} and grid { rows, columns, spacingX, spacingZ }.")
            end
            local rows = math.max(1, math.floor(tonumber(grid.rows) or 1))
            local cols = math.max(1, math.floor(tonumber(grid.cols or grid.columns) or 1))
            local sx = tonumber(grid.spacingX) or 4
            local sz = tonumber(grid.spacingZ) or 4
            for r = 0, rows - 1 do
                for c = 0, cols - 1 do
                    table.insert(cells, origin + Vector3.new(c * sx, 0, r * sz))
                end
            end
        else
            if typeof(origin) ~= "Vector3" then
                return failCode("BAD_ARGS", "count needs origin {x,y,z} (plus optional offset {x,y,z} between copies).")
            end
            local off = decodeValue(args.offset) or Vector3.new(0, 0, 0)
            for i = 0, wantCount - 1 do
                table.insert(cells, origin + off * i)
            end
        end
        if #cells > 400 then
            return failCode("BUDGET_EXCEEDED", "This would create " .. tostring(#cells) .. " instances - max 400 per call. Split into smaller calls.")
        end
        local counter = 0
        for _, pos in ipairs(cells) do
            counter = counter + 1
            local props = {}
            if type(baseProps) == "table" then
                for key, value in pairs(baseProps) do props[key] = value end
            end
            props.Position = pos
            local name = nameTemplate:gsub("{n}", tostring(counter)):gsub("%$", tostring(counter))
            table.insert(items, {
                className = className,
                name = name,
                properties = props,
                parentRef = args.parentRef or args.parentPath or templateSpec.parentRef,
            })
        end
    end

    -- Vorlage: stattdessen ein fertiges Teil/Modell klonen
    local templateInst = nil
    if args.templateRef then
        local t, errT = resolveRef(args.templateRef)
        if t == nil then return failCode("REF_NOT_FOUND", errT) end
        templateInst = t
    end

    if #items > 400 then
        return failCode("BUDGET_EXCEEDED", "bulk_create got " .. tostring(#items) .. " items - max 400 per call. Split the list into smaller calls.")
    end

    local created = {}
    local createdInsts = {}
    local errors = {}
    for index, spec in ipairs(items) do
        local entry = nil
        local err = nil
        if templateInst then
            local parentT, errP = resolveRef(spec.parentRef or spec.parentPath or "game.Workspace")
            if parentT == nil then
                err = errP
            else
                local cloneInst = templateInst:Clone()
                if spec.name then cloneInst.Name = spec.name end
                local props = (type(spec.properties) == "table") and spec.properties or {}
                local pos = props.Position
                if typeof(pos) == "Vector3" then
                    cloneInst.CFrame = CFrame.new(pos)
                end
                for key, value in pairs(props) do
                    if key ~= "Position" then
                        pcall(function() cloneInst[key] = value end)
                    end
                end
                cloneInst.Parent = parentT
                entry = describeRef(cloneInst)
            end
        else
            entry, err = createOne(spec)
        end
        if entry then
            local inst = resolveRef(entry.id)
            if inst and inst:IsA("BasePart") and #createdInsts < 8 then
                table.insert(createdInsts, inst)
            end
            table.insert(created, entry)
        else
            table.insert(errors, "item " .. tostring(index) .. ": " .. tostring(err))
        end
    end
    waypoint("bulk create " .. tostring(#created))
    local geometry = waitMeasurable(createdInsts, 2)
    return ok({ created = created, count = #created, errors = errors, geometry = geometry })
end

tools.clone_instance = function(args)
    local source, err = resolveRef(args.ref or args.path)
    if not source then return fail(err) end
    if source == game then return fail("Cannot clone the DataModel.") end

    local parent = source.Parent
    if args.parentRef or args.parentPath then
        local resolved, parentErr = resolveRef(args.parentRef or args.parentPath)
        if not resolved then return fail(parentErr) end
        parent = resolved
    end

    local count = tonumber(args.count) or 1
    if count < 1 then count = 1 end
    if count > 500 then return fail("Refusing to clone more than 500 copies at once.") end

    local offset = decodeValue(args.offset)
    if typeof(offset) ~= "Vector3" then offset = Vector3.new(0, 0, 0) end
    local rotationStep = tonumber(args.rotateStep) or 0
    local nameTemplate = args.nameTemplate

    local copies = {}
    local wasArchivable = source.Archivable
    if not wasArchivable then source.Archivable = true end
    for index = 1, count do
        local copy = source:Clone()
        if copy == nil then
            source.Archivable = wasArchivable
            return fail("Clone failed (Archivable is false or the instance cannot be copied).")
        end
        if nameTemplate then
            copy.Name = string.gsub(tostring(nameTemplate), "{n}", tostring(index))
        end
        copy.Parent = parent
        if offset.Magnitude > 0 or rotationStep ~= 0 then
            local pivot = getPivotOf(copy)
            if pivot then
                local moved = pivot + (offset * index)
                if rotationStep ~= 0 then
                    moved = moved * CFrame.Angles(0, math.rad(rotationStep * index), 0)
                end
                setPivotOf(copy, moved)
            end
        end
        table.insert(copies, describeRef(copy))
    end
    source.Archivable = wasArchivable
    waypoint("clone " .. tostring(count) .. "x " .. source.Name)
    local copiedInsts = {}
    for _, c in ipairs(copies) do
        local inst = resolveRef(c.id)
        if inst and inst:IsA("BasePart") and #copiedInsts < 8 then table.insert(copiedInsts, inst) end
    end
    local geometry = waitMeasurable(copiedInsts, 2)
    return ok({ clones = copies, count = #copies, source = describeRef(source), geometry = geometry })
end

tools.delete_instance = function(args)
    local inst, err = resolveRef(args.ref or args.path)
    if not inst then return fail(err) end
    if inst == game then return fail("Cannot delete the DataModel.") end
    local info = describeRef(inst)
    inst:Destroy()
    waypoint("delete " .. tostring(info.name))
    return ok({ deleted = info })
end

tools.bulk_delete = function(args)
    local list, errors = resolveMany(args.refs or args.ref)
    local deleted = {}
    for _, inst in ipairs(list) do
        if inst ~= game then
            local info = describeRef(inst)
            local okDelete = pcall(function() inst:Destroy() end)
            if okDelete then
                table.insert(deleted, info)
            else
                table.insert(errors, "Could not delete " .. tostring(info.path))
            end
        end
    end
    waypoint("bulk delete " .. tostring(#deleted))
    return ok({ deleted = deleted, count = #deleted, errors = errors })
end

tools.rename_instance = function(args)
    local inst, err = resolveRef(args.ref or args.path)
    if not inst then return fail(err) end
    inst.Name = tostring(args.name or inst.Name)
    waypoint("rename")
    return ok(describeRef(inst))
end

tools.move_instance = function(args)
    local list, errors = resolveMany(args.refs or args.ref or args.path)
    local parent, parentErr = resolveRef(args.parentRef or args.parentPath)
    if not parent then return fail(parentErr) end
    local moved = {}
    for _, inst in ipairs(list) do
        if inst ~= game then
            local okMove = pcall(function() inst.Parent = parent end)
            if okMove then
                table.insert(moved, describeRef(inst))
            else
                table.insert(errors, "Could not move " .. inst.Name)
            end
        end
    end
    waypoint("move")
    return ok({ moved = moved, parent = describeRef(parent), errors = errors })
end

tools.set_property = function(args)
    local list, errors = resolveMany(args.refs or args.ref or args.path)
    if #list == 0 then return fail("No instance resolved. " .. table.concat(errors, " ")) end
    local property = tostring(args.property or "")
    if property == "" then return fail("property missing.") end
    local changed = {}
    for _, inst in ipairs(list) do
        local okSet, err = setProperty(inst, property, args.value)
        if okSet then
            table.insert(changed, describeRef(inst))
        else
            table.insert(errors, inst.Name .. ": " .. tostring(err))
        end
    end
    waypoint("set " .. property)
    return ok({ changed = changed, count = #changed, property = property, errors = errors })
end

tools.set_properties = function(args)
    local list, errors = resolveMany(args.refs or args.ref or args.path)
    if #list == 0 then return fail("No instance resolved. " .. table.concat(errors, " ")) end
    local changed = {}
    for _, inst in ipairs(list) do
        local problems = applyProperties(inst, args.properties)
        for _, problem in ipairs(problems) do
            table.insert(errors, inst.Name .. ": " .. problem)
        end
        table.insert(changed, describeRef(inst))
    end
    waypoint("set properties")
    return ok({ changed = changed, count = #changed, errors = errors })
end

tools.bulk_set_properties = function(args)
    local items = args.items or {}
    local changed = {}
    local errors = {}
    for index, item in ipairs(items) do
        local inst, err = resolveRef(item.ref or item.path)
        if inst then
            local problems = applyProperties(inst, item.properties)
            for _, problem in ipairs(problems) do
                table.insert(errors, "item " .. tostring(index) .. " " .. problem)
            end
            table.insert(changed, describeRef(inst))
        else
            table.insert(errors, "item " .. tostring(index) .. ": " .. tostring(err))
        end
    end
    waypoint("bulk set properties")
    return ok({ changed = changed, count = #changed, errors = errors })
end

tools.set_attribute = function(args)
    local list, errors = resolveMany(args.refs or args.ref or args.path)
    if #list == 0 then return fail("No instance resolved.") end
    for _, inst in ipairs(list) do
        local okSet, err = pcall(function()
            inst:SetAttribute(tostring(args.name), decodeValue(args.value))
        end)
        if not okSet then table.insert(errors, tostring(err)) end
    end
    waypoint("set attribute")
    return ok({ count = #list, attribute = args.name, errors = errors })
end

tools.add_tag = function(args)
    local list = resolveMany(args.refs or args.ref)
    for _, inst in ipairs(list) do
        pcall(function() CollectionService:AddTag(inst, tostring(args.tag)) end)
    end
    return ok({ count = #list, tag = args.tag })
end

tools.remove_tag = function(args)
    local list = resolveMany(args.refs or args.ref)
    for _, inst in ipairs(list) do
        pcall(function() CollectionService:RemoveTag(inst, tostring(args.tag)) end)
    end
    return ok({ count = #list, tag = args.tag })
end

tools.group_instances = function(args)
    local list, errors = resolveMany(args.refs)
    if #list < 1 then return fail("Need at least one instance. " .. table.concat(errors, " ")) end
    local parent = list[1].Parent
    if args.parentRef then
        local resolved = resolveRef(args.parentRef)
        if resolved then parent = resolved end
    end
    local model = Instance.new(args.className or "Model")
    model.Name = args.name or "Group"
    model.Parent = parent
    for _, inst in ipairs(list) do
        pcall(function() inst.Parent = model end)
    end
    if model:IsA("Model") then
        local firstPart = nil
        for _, inst in ipairs(list) do
            if inst:IsA("BasePart") then firstPart = inst break end
        end
        if firstPart then
            pcall(function() model.PrimaryPart = firstPart end)
        end
    end
    waypoint("group")
    return ok({ group = describeRef(model), count = #list })
end

tools.ungroup = function(args)
    local model, err = resolveRef(args.ref)
    if not model then return fail(err) end
    local parent = model.Parent
    local moved = {}
    for _, child in ipairs(model:GetChildren()) do
        local okMove = pcall(function() child.Parent = parent end)
        if okMove then table.insert(moved, describeRef(child)) end
    end
    model:Destroy()
    waypoint("ungroup")
    return ok({ moved = moved, count = #moved })
end

-- ------------------------- Skripte ------------------------------------------
tools.get_script = function(args)
    local inst, err = resolveRef(args.ref or args.path)
    if not inst then return fail(err) end
    if not inst:IsA("LuaSourceContainer") then
        return fail("'" .. inst.Name .. "' is a " .. inst.ClassName .. ", not a script.")
    end
    local source = inst.Source
    local lines = splitLines(source)
    local startLine = tonumber(args.startLine) or 1
    local endLine = tonumber(args.endLine) or #lines
    if startLine < 1 then startLine = 1 end
    if endLine > #lines then endLine = #lines end

    local selected = {}
    for index = startLine, endLine do
        if args.withLineNumbers == false then
            table.insert(selected, lines[index])
        else
            table.insert(selected, string.format("%5d| %s", index, lines[index]))
        end
    end
    local text = table.concat(selected, "\n")

    return ok({
        id         = idOf(inst),
        path       = pathOf(inst),
        className  = inst.ClassName,
        totalLines = #lines,
        totalBytes = #source,
        startLine  = startLine,
        endLine    = endLine,
        hash       = hashString(source),
        source     = text,
        hint       = "Use patch_script with small unique snippets instead of rewriting the whole file. Pass the hash as expectHash to make sure nobody changed the script in between.",
    })
end

tools.find_in_script = function(args)
    local inst, err = resolveRef(args.ref or args.path)
    if not inst then return fail(err) end
    if not inst:IsA("LuaSourceContainer") then return fail("Not a script.") end
    local source = inst.Source
    local needle = tostring(args.query or args.find or "")
    if needle == "" then return fail("query missing.") end
    local plain = not (args.regex == true)
    local hits = findOccurrences(source, needle, plain)
    local contextLines = tonumber(args.contextLines) or 2
    local results = {}
    for _, hit in ipairs(hits) do
        table.insert(results, {
            line = hit.line,
            offset = hit.from,
            preview = previewAround(source, hit.line, contextLines),
        })
        if #results >= (tonumber(args.limit) or 40) then break end
    end
    return ok({ matches = results, count = #hits, totalLines = select(2, string.gsub(source, "\n", "\n")) + 1, hash = hashString(source) })
end

tools.set_script_source = function(args)
    local inst, err = resolveRef(args.ref or args.path)
    if not inst then return fail(err) end
    if not inst:IsA("LuaSourceContainer") then return fail("Not a script.") end
    local newSource = tostring(args.source or "")
    local oldSource = inst.Source
    if args.expectHash and args.expectHash ~= hashString(oldSource) then
        return fail("The script changed since you read it (hash mismatch). Read it again with get_script before writing.", { currentHash = hashString(oldSource) })
    end
    inst.Source = newSource
    waypoint("script " .. inst.Name)
    local warnings = nil
    if #oldSource > 4000 and #newSource < #oldSource * 0.6 then
        warnings = { "The new source is much shorter than the old one (" .. tostring(#oldSource) .. " -> " .. tostring(#newSource) .. " bytes). If that was not intended, use undo and switch to patch_script." }
    end
    return ok({
        id = idOf(inst),
        path = pathOf(inst),
        bytes = #newSource,
        lines = select(2, string.gsub(newSource, "\n", "\n")) + 1,
        previousBytes = #oldSource,
        hash = hashString(newSource),
    }, warnings)
end

-- Punktgenaue Aenderungen: nur die betroffene Stelle wird ersetzt.
tools.patch_script = function(args)
    local inst, err = resolveRef(args.ref or args.path)
    if not inst then return fail(err) end
    if not inst:IsA("LuaSourceContainer") then return fail("Not a script.") end

    local source = inst.Source
    if args.expectHash and args.expectHash ~= hashString(source) then
        return fail("The script changed since you read it (hash mismatch). Read it again with get_script.", { currentHash = hashString(source) })
    end

    local edits = args.edits
    if edits == nil and args.edit then edits = { args.edit } end
    if type(edits) ~= "table" or #edits == 0 then
        return fail("patch_script needs 'edits': a list like [{op='replace', find='...', replace='...'}].")
    end

    local report = {}
    local working = source
    for index, edit in ipairs(edits) do
        local newText, editError = applyEdit(working, edit, report)
        if newText == nil then
            return fail("Edit " .. tostring(index) .. " failed: " .. tostring(editError), {
                appliedBefore = report,
                unchanged = true,
                hash = hashString(source),
            })
        end
        working = newText
    end

    local oldLines = select(2, string.gsub(source, "\n", "\n")) + 1
    local newLines = select(2, string.gsub(working, "\n", "\n")) + 1

    if args.dryRun == true then
        return ok({
            dryRun = true,
            wouldChange = (working ~= source),
            operations = report,
            oldLines = oldLines,
            newLines = newLines,
            preview = string.sub(working, 1, 2000),
        })
    end

    inst.Source = working
    waypoint("patch " .. inst.Name)

    local firstLine = nil
    for _, entry in ipairs(report) do
        firstLine = entry.line or entry.startLine or entry.firstLine or entry.atLine
        if firstLine then break end
    end

    return ok({
        id = idOf(inst),
        path = pathOf(inst),
        operations = report,
        oldLines = oldLines,
        newLines = newLines,
        lineDelta = newLines - oldLines,
        bytes = #working,
        hash = hashString(working),
        preview = firstLine and previewAround(working, firstLine, 4) or nil,
    })
end

tools.insert_script = function(args)
    local parent, err = resolveRef(args.parentRef or args.parentPath or "game.ServerScriptService")
    if not parent then return fail(err) end
    local className = args.className or "Script"
    local created = Instance.new(className)
    created.Name = args.name or className
    local okSource = pcall(function() created.Source = tostring(args.source or "") end)
    if not okSource then
        created:Destroy()
        return fail("'" .. className .. "' has no Source property. Use Script, LocalScript or ModuleScript.")
    end
    if args.properties then applyProperties(created, args.properties) end
    created.Parent = parent
    waypoint("insert script")
    return ok({
        id = idOf(created),
        path = pathOf(created),
        className = created.ClassName,
        lines = select(2, string.gsub(created.Source, "\n", "\n")) + 1,
        hash = hashString(created.Source),
    })
end

tools.bulk_insert_scripts = function(args)
    local items = args.items or {}
    local created = {}
    local errors = {}
    for index, item in ipairs(items) do
        local result = tools.insert_script(item)
        if result.ok then
            table.insert(created, result.result)
        else
            table.insert(errors, "item " .. tostring(index) .. ": " .. tostring(result.error))
        end
    end
    return ok({ created = created, count = #created, errors = errors })
end

-- ------------------------- Bauhilfe -----------------------------------------
tools.place_on = function(args)
    local mover, errA = resolveRef(args.ref)
    local target, errB = resolveRef(args.targetRef)
    if not mover then return fail(errA) end
    if not target then return fail(errB) end
    local result, err = placeOnFace(
        mover, target,
        args.face or "top",
        tonumber(args.offsetX) or tonumber(args.offsetU) or 0,
        tonumber(args.offsetZ) or tonumber(args.offsetV) or 0,
        tonumber(args.gap) or 0,
        args.inside == true,
        args.matchRotation == true
    )
    if not result then return fail(err) end
    waypoint("place on")
    return ok(result)
end

tools.align = tools.place_on

-- "align" ist derselbe Befehl wie place_on (nur ein anderer Name dafuer).
tools.align = function(args)
    return tools.place_on(args)
end

tools.stack = function(args)
    local list, errors = resolveMany(args.refs)
    if #list < 1 then return fail("Need at least one instance. " .. table.concat(errors, " ")) end
    local axis = string.lower(tostring(args.axis or "y"))
    local gap = tonumber(args.gap) or 0
    local base = nil
    if args.baseRef then
        base = resolveRef(args.baseRef)
    end

    local results = {}
    local cursor = nil
    if base then
        local cframe, size = boundsOf(base)
        if cframe then
            if axis == "y" then cursor = cframe.Position.Y + size.Y / 2
            elseif axis == "x" then cursor = cframe.Position.X + size.X / 2
            else cursor = cframe.Position.Z + size.Z / 2 end
        end
    end

    for _, inst in ipairs(list) do
        local cframe, size = boundsOf(inst)
        if cframe then
            local half
            if axis == "y" then half = size.Y / 2 elseif axis == "x" then half = size.X / 2 else half = size.Z / 2 end
            if cursor == nil then
                if axis == "y" then cursor = cframe.Position.Y - half
                elseif axis == "x" then cursor = cframe.Position.X - half
                else cursor = cframe.Position.Z - half end
            end
            local position = cframe.Position
            local newPosition
            if axis == "y" then
                newPosition = Vector3.new(position.X, cursor + gap + half, position.Z)
            elseif axis == "x" then
                newPosition = Vector3.new(cursor + gap + half, position.Y, position.Z)
            else
                newPosition = Vector3.new(position.X, position.Y, cursor + gap + half)
            end
            if args.alignToBase == true and base then
                local baseCFrame = boundsOf(base)
                if baseCFrame then
                    if axis == "y" then
                        newPosition = Vector3.new(baseCFrame.Position.X, newPosition.Y, baseCFrame.Position.Z)
                    end
                end
            end
            setPivotOf(inst, CFrame.new(newPosition) * (cframe - cframe.Position))
            cursor = cursor + gap + half * 2
            table.insert(results, { instance = describeRef(inst), position = { x = newPosition.X, y = newPosition.Y, z = newPosition.Z } })
        end
    end
    waypoint("stack")
    return ok({ stacked = results, count = #results, axis = axis })
end

tools.grid_arrange = function(args)
    local list, errors = resolveMany(args.refs)
    if #list == 0 then return fail("Need instances. " .. table.concat(errors, " ")) end
    local columns = tonumber(args.columns) or math.ceil(math.sqrt(#list))
    local spacingX = tonumber(args.spacingX) or tonumber(args.spacing) or 10
    local spacingZ = tonumber(args.spacingZ) or tonumber(args.spacing) or 10
    local origin = decodeValue(args.origin)
    if typeof(origin) ~= "Vector3" then
        local firstCFrame = getPivotOf(list[1])
        origin = firstCFrame and firstCFrame.Position or Vector3.new(0, 0, 0)
    end
    local placed = {}
    for index, inst in ipairs(list) do
        local column = (index - 1) % columns
        local row = math.floor((index - 1) / columns)
        local position = origin + Vector3.new(column * spacingX, 0, row * spacingZ)
        local pivot = getPivotOf(inst)
        local rotation = pivot and (pivot - pivot.Position) or CFrame.new()
        setPivotOf(inst, CFrame.new(position) * rotation)
        table.insert(placed, { instance = describeRef(inst), position = { x = position.X, y = position.Y, z = position.Z } })
    end
    waypoint("grid")
    return ok({ placed = placed, count = #placed, columns = columns })
end

tools.distribute = function(args)
    local list, errors = resolveMany(args.refs)
    if #list < 2 then return fail("Need at least two instances.") end
    local axis = string.lower(tostring(args.axis or "x"))
    local spacing = tonumber(args.spacing)
    local pivots = {}
    for _, inst in ipairs(list) do
        table.insert(pivots, getPivotOf(inst))
    end
    local startPosition = pivots[1].Position
    local endPosition = pivots[#pivots].Position
    local placed = {}
    for index, inst in ipairs(list) do
        local factor = (index - 1) / (#list - 1)
        local position
        if spacing then
            local step = Vector3.new(axis == "x" and spacing or 0, axis == "y" and spacing or 0, axis == "z" and spacing or 0)
            position = startPosition + step * (index - 1)
        else
            position = startPosition:Lerp(endPosition, factor)
        end
        local rotation = pivots[index] - pivots[index].Position
        setPivotOf(inst, CFrame.new(position) * rotation)
        table.insert(placed, { instance = describeRef(inst), position = { x = position.X, y = position.Y, z = position.Z } })
    end
    waypoint("distribute")
    return ok({ placed = placed, count = #placed })
end

tools.snap_to_ground = function(args)
    local list, errors = resolveMany(args.refs or args.ref)
    if #list == 0 then return failCode("REF_NOT_FOUND", "No instance resolved. " .. table.concat(errors, " ")) end
    local offset = tonumber(args.offset) or 0
    local maxDrop = tonumber(args.maxDrop)
    local results = {}
    for _, inst in ipairs(list) do
        local cframe, size = boundsOf(inst)
        if cframe and size then
            local params = measureRayParams({ inst })
            local origin = cframe.Position
            local hit = Workspace:Raycast(origin, Vector3.new(0, -4000, 0), params)
            if hit then
                local newY = hit.Position.Y + size.Y / 2 + offset
                local drop = origin.Y - newY
                if maxDrop and drop > maxDrop then
                    table.insert(results, {
                        instance = describeRef(inst),
                        note = "Ground is " .. string.format("%.1f", drop) .. " studs below (maxDrop " .. tostring(maxDrop)
                            .. ") - NOT moved. Pass a bigger maxDrop if that is intended.",
                        ground = describeRef(hit.Instance),
                    })
                else
                    setPivotOf(inst, CFrame.new(origin.X, newY, origin.Z) * (cframe - cframe.Position))
                    table.insert(results, { instance = describeRef(inst), y = newY, ground = describeRef(hit.Instance) })
                end
            else
                table.insert(results, { instance = describeRef(inst), note = "Nothing below - not moved." })
            end
        end
    end
    waypoint("snap to ground")
    return ok({ results = results, count = #results })
end

tools.look_at = function(args)
    local inst, err = resolveRef(args.ref)
    if not inst then return fail(err) end
    local targetPosition = nil
    if args.targetRef then
        local target = resolveRef(args.targetRef)
        if target then
            local cframe = getPivotOf(target)
            if cframe then targetPosition = cframe.Position end
        end
    end
    if targetPosition == nil then
        local decoded = decodeValue(args.position)
        if typeof(decoded) == "Vector3" then targetPosition = decoded end
    end
    if targetPosition == nil then return fail("Need targetRef or position.") end
    local pivot = getPivotOf(inst)
    if pivot == nil then return fail("Instance has no position.") end
    local newCFrame = CFrame.lookAt(pivot.Position, targetPosition)
    if args.keepUpright == true then
        newCFrame = CFrame.lookAt(pivot.Position, Vector3.new(targetPosition.X, pivot.Position.Y, targetPosition.Z))
    end
    setPivotOf(inst, newCFrame)
    waypoint("look at")
    return ok({ instance = describeRef(inst), cframe = encodeValue(newCFrame) })
end

tools.coordinate_guide = function(args)
    local system = {
        axes = "+X = right (east), +Y = up, +Z = toward the default camera (south). The default Studio camera looks toward -Z, so the front face of a fresh part (-Z) points AWAY from the default camera (north).",
        yaw = "Rotation around +Y in degrees, positive = counter-clockwise seen from above. A yaw of d degrees turns the front face to world direction (-sin d, 0, -cos d) - so positive yaw turns the front toward -X (west/left).",
        cframe = "CFrame values come back in degrees (orientation) and radians (orientationRadians). pitch = around X, yaw = around Y, roll = around Z.",
        shapeDefaults = {
            block = "Axis aligned - no hidden orientation.",
            ball = "Sphere - no faces.",
            cylinder = "Length axis is VERTICAL (local Y) by default, flat caps on top and bottom.",
            wedge = "A ramp - the high edge and slope direction are MEASURED per part (see the measured section below).",
        },
        workflow = "1) coordinate_guide (once per session) 2) describe_orientation on the part 3) point_at (axis='top' for a cylinder's length) or rotate_around with the measured axis 4) describe_orientation again to verify.",
    }
    local measured = {}
    local refs = args.refs or args.ref
    if refs then
        local list, _ = resolveMany(refs)
        for _, inst in ipairs(list) do
            local shape = measureShape(inst)
            if shape then table.insert(measured, { instance = describeRef(inst), shape = shape }) end
        end
    else
        local limit = tonumber(args.limit) or 12
        local root, err = resolveRef(args.rootRef or "game.Workspace")
        if not root then return failCode("REF_NOT_FOUND", err) end
        for _, inst in ipairs(root:GetDescendants()) do
            if #measured >= limit then break end
            if inst:IsA("BasePart") and (inst.Shape == Enum.PartType.Cylinder
                or inst.Shape == Enum.PartType.Wedge or inst.Shape == Enum.PartType.Ball) then
                local shape = measureShape(inst)
                if shape then table.insert(measured, { instance = describeRef(inst), shape = shape }) end
            end
        end
    end
    return ok({
        system = system,
        measured = measured,
        note = "The measured values are raycast results from right now - not guesses. They are cached per part and re-measured automatically when position/size/shape change.",
    })
end

tools.describe_orientation = function(args)
    local inst, err = resolveRef(args.ref)
    if not inst then return failCode("REF_NOT_FOUND", err) end
    local cframe = getPivotOf(inst)
    if cframe == nil then return failCode("BAD_ARGS", "Instance has no CFrame.") end
    local rx, ry, rz = cframe:ToOrientation()
    local result = {
        instance = describeRef(inst),
        faces = facesOf(cframe),
        rotation = { pitch = math.deg(rx), yaw = math.deg(ry), roll = math.deg(rz) },
        note = "front = the part's -Z face (the face a model would look out of). Positive yaw turns the front toward -X.",
    }
    local shape = measureShape(inst)
    if shape then result.shape = shape end
    return ok(result)
end

tools.point_at = function(args)
    local inst, errA = resolveRef(args.ref)
    if not inst then return failCode("REF_NOT_FOUND", errA) end
    local targetPosition = nil
    if args.targetRef then
        local target, errT = resolveRef(args.targetRef)
        if not target then return failCode("REF_NOT_FOUND", errT) end
        local cframe = getPivotOf(target)
        if cframe then targetPosition = cframe.Position end
    end
    if targetPosition == nil then
        local decoded = decodeValue(args.position)
        if typeof(decoded) == "Vector3" then targetPosition = decoded end
    end
    if targetPosition == nil then return failCode("BAD_ARGS", "Need targetRef or position {x,y,z}.") end
    local pivot = getPivotOf(inst)
    if pivot == nil then return failCode("BAD_ARGS", "Instance has no CFrame.") end
    local axis = string.lower(tostring(args.axis or "front"))
    if axis ~= "front" and axis ~= "back" and axis ~= "top" and axis ~= "bottom"
        and axis ~= "left" and axis ~= "right" then
        return failCode("BAD_ARGS", "axis must be front, back, top, bottom, left or right.")
    end
    local dir = targetPosition - pivot.Position
    if dir.Magnitude < 0.001 then return failCode("BAD_ARGS", "Target is at the same position.") end
    dir = dir.Unit
    local newCFrame
    if axis == "front" then
        newCFrame = CFrame.lookAt(pivot.Position, targetPosition)
    elseif axis == "back" then
        newCFrame = CFrame.lookAt(pivot.Position, pivot.Position - dir)
    elseif axis == "left" then
        newCFrame = CFrame.lookAt(pivot.Position, targetPosition) * CFrame.Angles(0, math.rad(-90), 0)
    elseif axis == "right" then
        newCFrame = CFrame.lookAt(pivot.Position, targetPosition) * CFrame.Angles(0, math.rad(90), 0)
    elseif axis == "top" then
        -- Längenachse (lokal Y, z.B. Zylinder) zeigt zum Ziel
        local ref = math.abs(dir.Y) > 0.9 and Vector3.new(1, 0, 0) or Vector3.new(0, 1, 0)
        local right = ref:Cross(dir).Unit
        local look = right:Cross(dir)
        newCFrame = CFrame.fromMatrix(pivot.Position, right, dir, look)
    else
        local up = -dir
        local ref = math.abs(up.Y) > 0.9 and Vector3.new(1, 0, 0) or Vector3.new(0, 1, 0)
        local right = ref:Cross(up).Unit
        local look = right:Cross(up)
        newCFrame = CFrame.fromMatrix(pivot.Position, right, up, look)
    end
    setPivotOf(inst, newCFrame)
    waypoint("point at")
    return ok({
        instance = describeRef(inst),
        axis = axis,
        target = encodeValue(targetPosition),
        cframe = encodeValue(newCFrame),
        facesNow = {
            front = dirHeading(newCFrame:VectorToWorldSpace(Vector3.new(0, 0, -1))),
            back  = dirHeading(newCFrame:VectorToWorldSpace(Vector3.new(0, 0, 1))),
            top   = dirHeading(newCFrame:VectorToWorldSpace(Vector3.new(0, 1, 0))),
        },
        hint = "Verify with describe_orientation - it includes the measured shape facts (wedge high edge, cylinder axis).",
    })
end

tools.rotate_around = function(args)
    local list, errors = resolveMany(args.refs or args.ref)
    if #list == 0 then return fail("No instance resolved.") end
    local degrees = tonumber(args.degrees) or 0
    local axisName = string.lower(tostring(args.axis or "y"))
    local axis = Vector3.new(0, 1, 0)
    if axisName == "x" then axis = Vector3.new(1, 0, 0) end
    if axisName == "z" then axis = Vector3.new(0, 0, 1) end

    local pivotPosition = decodeValue(args.pivot)
    if typeof(pivotPosition) ~= "Vector3" then
        if args.pivotRef then
            local target = resolveRef(args.pivotRef)
            local cframe = target and getPivotOf(target)
            if cframe then pivotPosition = cframe.Position end
        end
    end
    if typeof(pivotPosition) ~= "Vector3" then
        local cframe = getPivotOf(list[1])
        pivotPosition = cframe and cframe.Position or Vector3.new(0, 0, 0)
    end

    local rotation = CFrame.fromAxisAngle(axis, math.rad(degrees))
    local results = {}
    for _, inst in ipairs(list) do
        local pivot = getPivotOf(inst)
        if pivot then
            local relative = pivot.Position - pivotPosition
            local rotated = rotation * relative
            local newCFrame = CFrame.new(pivotPosition + rotated) * rotation * (pivot - pivot.Position)
            setPivotOf(inst, newCFrame)
            table.insert(results, describeRef(inst))
        end
    end
    waypoint("rotate around")
    return ok({ rotated = results, count = #results, degrees = degrees, axis = axisName })
end

tools.move_relative = function(args)
    local list, errors = resolveMany(args.refs or args.ref)
    if #list == 0 then return fail("No instance resolved. " .. table.concat(errors, " ")) end
    local right = tonumber(args.right) or tonumber(args.x) or 0
    local up = tonumber(args.up) or tonumber(args.y) or 0
    local forward = tonumber(args.forward) or tonumber(args.z) or 0
    local space = string.lower(tostring(args.space or "world"))
    local results = {}
    for _, inst in ipairs(list) do
        local pivot = getPivotOf(inst)
        if pivot then
            local newCFrame
            if space == "local" or space == "object" then
                newCFrame = pivot * CFrame.new(right, up, -forward)
            else
                newCFrame = pivot + Vector3.new(right, up, forward)
            end
            setPivotOf(inst, newCFrame)
            table.insert(results, { instance = describeRef(inst), position = encodeValue(newCFrame.Position) })
        end
    end
    waypoint("move relative")
    return ok({ moved = results, count = #results })
end

tools.resize_part = function(args)
    local inst, err = resolveRef(args.ref)
    if not inst then return fail(err) end
    if not inst:IsA("BasePart") then return fail("resize_part works on BaseParts. For models scale each part or use a Model:ScaleTo call via run_lua.") end
    local newSize = decodeValue(args.size)
    if typeof(newSize) ~= "Vector3" then return fail("size must be {x,y,z}.") end
    local anchor = string.lower(tostring(args.anchor or "center"))
    local oldSize = inst.Size
    local oldCFrame = inst.CFrame
    inst.Size = newSize
    if anchor == "bottom" then
        inst.CFrame = oldCFrame * CFrame.new(0, (newSize.Y - oldSize.Y) / 2, 0)
    elseif anchor == "top" then
        inst.CFrame = oldCFrame * CFrame.new(0, -(newSize.Y - oldSize.Y) / 2, 0)
    end
    waypoint("resize")
    return ok({ instance = describeRef(inst), size = encodeValue(inst.Size), position = encodeValue(inst.Position) })
end

tools.fit_between = function(args)
    local inst, err = resolveRef(args.ref)
    if not inst then return fail(err) end
    if not inst:IsA("BasePart") then return fail("fit_between needs a BasePart.") end
    local pointA = decodeValue(args.from)
    local pointB = decodeValue(args.to)
    if typeof(pointA) ~= "Vector3" and args.fromRef then
        local target = resolveRef(args.fromRef)
        local cframe = target and getPivotOf(target)
        if cframe then pointA = cframe.Position end
    end
    if typeof(pointB) ~= "Vector3" and args.toRef then
        local target = resolveRef(args.toRef)
        local cframe = target and getPivotOf(target)
        if cframe then pointB = cframe.Position end
    end
    if typeof(pointA) ~= "Vector3" or typeof(pointB) ~= "Vector3" then
        return fail("Need from/to as {x,y,z} or fromRef/toRef.")
    end
    local thickness = tonumber(args.thickness) or 1
    local distance = (pointB - pointA).Magnitude
    inst.Size = Vector3.new(thickness, thickness, distance)
    inst.CFrame = CFrame.lookAt((pointA + pointB) / 2, pointB)
    waypoint("fit between")
    return ok({ instance = describeRef(inst), length = distance })
end

tools.overlap_check = function(args)
    local list, errors = resolveMany(args.refs or args.ref)
    if #list == 0 then return failCode("REF_NOT_FOUND", "No instance resolved. " .. table.concat(errors, " ")) end
    local tolerance = tonumber(args.tolerance) or 0
    local limit = tonumber(args.limit) or 50
    local exList = resolveExcluded(args.ignore)
    for _, inst in ipairs(list) do table.insert(exList, inst) end
    local params = overlapParamsNew(exList)
    local items = {}
    for _, inst in ipairs(list) do
        local cframe, size = boundsOf(inst)
        if cframe and size then
            local boxSize = size + Vector3.new(tolerance * 2, tolerance * 2, tolerance * 2)
            local parts = Workspace:GetPartBoundsInBox(cframe.Position, boxSize, params)
            local overlapping = {}
            for _, part in ipairs(parts) do
                table.insert(overlapping, describeRef(part))
                if #overlapping >= limit then break end
            end
            table.insert(items, {
                instance = describeRef(inst),
                overlapping = overlapping,
                count = #parts,
                clear = (#parts == 0),
            })
        end
    end
    if #items == 1 then return ok(items[1]) end
    return ok({ items = items })
end

-- ------------------------- Unions -------------------------------------------
local function finishSolidResult(newPart, parent, name, sources, keepOriginals, kind, extra)
    if newPart == nil then
        return failCode("SOLID_REFUSED",
            "Roblox refused the solid operation - it returned nothing. This happens when the parts do not intersect/overlap, are disconnected, or are too complex. NOTHING was changed - all original parts are still there.",
            {
                kind = kind,
                robloxMessage = "Solid modeling returned no new part.",
                hints = {
                    "Check that the parts actually overlap (measure_distance or get_bounds).",
                    "Very thin or far-apart parts are common causes.",
                    "Try keepOriginals=true to keep the input for a different approach.",
                },
            })
    end
    newPart.Name = name or (kind .. "Result")
    newPart.Parent = parent
    local warnings = unionWarnings(sources, kind)
    if extra and extra.estimatedTriangles then
        table.insert(warnings, "Estimated triangles: " .. tostring(extra.estimatedTriangles) .. ".")
    end
    if not keepOriginals then
        for _, part in ipairs(sources) do
            if part ~= newPart then
                pcall(function() part:Destroy() end)
            end
        end
    else
        table.insert(warnings, "Originals were kept (keepOriginals=true) - they now sit inside the result and may be invisible.")
    end
    return ok({
        result = describeRef(newPart),
        partsUsed = #sources,
        bounds = boundsInfo(newPart),
        canBeUndone = "Use 'separate' to split the union back into parts (or undo for the waypoint that was set before this operation).",
    }, warnings)
end

-- Führt EINE Solid-Operation aus (wird von union/subtract/intersect + groups benutzt).
local function runSolidOperation(kind, base, others, args)
    local sources = { base }
    for _, part in ipairs(others) do table.insert(sources, part) end
    local warnings, code, message, extra = precheckSolid(sources, 2, args)
    if code then
        local resp = failCode(code, message, extra)
        return resp
    end
    local parent = base.Parent
    if args.parentRef then
        local resolved = resolveRef(args.parentRef)
        if resolved then parent = resolved end
    end
    if args.undoPoint ~= false then
        waypoint("before " .. kind .. " " .. base.Name)
    end
    local newPart = nil
    local okRun, runErr = pcall(function()
        if kind == "union" then
            newPart = base:UnionAsync(others, collisionFidelityFrom(args.collisionFidelity), renderFidelityFrom(args.renderFidelity))
        elseif kind == "subtract" then
            newPart = base:SubtractAsync(others, collisionFidelityFrom(args.collisionFidelity), renderFidelityFrom(args.renderFidelity))
        else
            newPart = base:IntersectAsync(others, collisionFidelityFrom(args.collisionFidelity), renderFidelityFrom(args.renderFidelity))
        end
    end)
    if not okRun then
        return failCode("SOLID_REFUSED",
            "Roblox refused the solid operation: " .. tostring(runErr) .. " NOTHING was changed - all original parts are still there.",
            {
                kind = kind,
                robloxMessage = tostring(runErr),
                hints = {
                    "Check that the parts actually overlap (measure_distance or get_bounds).",
                    "Unanchored parts move while the operation runs - anchor them first (fixAnchored=true).",
                    "Try keepOriginals=true to keep the input for a different approach.",
                },
            })
    end
    return finishSolidResult(newPart, parent, args.name or (kind == "subtract" and (base.Name .. "Cut") or kind .. "Result"), sources, args.keepOriginals == true, kind, extra)
end

-- Batch: groups = [ {refs = {...}, name = ...}, ... ] -> mehrere Operationen in einem Call.
local function resolveGroups(kind, args)
    local groups = args.groups
    if type(groups) == "table" and #groups > 0 then
        local out = {}
        for index, group in ipairs(groups) do
            local refs = group.refs or group
            local list, errors = resolveMany(refs)
            if #list < 2 then
                table.insert(out, { group = index, error = "Group needs at least 2 parts. " .. table.concat(errors, " ") })
            else
                local others = {}
                for ii = 2, #list do table.insert(others, list[ii]) end
                table.insert(out, { group = index, base = list[1], others = others, name = group.name })
            end
        end
        return out
    end
    return nil
end

tools.union = function(args)
    local groups = resolveGroups("union", args)
    if groups then
        local results = {}
        for _, g in ipairs(groups) do
            if g.base then
                local gArgs = {}
                for key, value in pairs(args) do gArgs[key] = value end
                gArgs.name = g.name or ("Union" .. tostring(g.group))
                table.insert(results, runSolidOperation("union", g.base, g.others, gArgs))
            else
                table.insert(results, { ok = false, code = "REF_NOT_FOUND", error = g.error })
            end
        end
        return ok({ groups = results, count = #results })
    end
    local parts, errors = resolveMany(args.refs)
    local others = {}
    for ii = 2, #parts do table.insert(others, parts[ii]) end
    local result = runSolidOperation("union", parts[1], others, args)
    if type(errors) == "table" and #errors > 0 then
        if type(result) == "table" then result.resolveErrors = errors end
    end
    return result
end

tools.subtract = function(args)
    local base, err = resolveRef(args.baseRef or args.ref)
    if not base then return failCode("REF_NOT_FOUND", err) end
    local negatives, negErrors = resolveMany(args.negativeRefs or args.refs)
    local result = runSolidOperation("subtract", base, negatives, args)
    if type(negErrors) == "table" and #negErrors > 0 then
        if type(result) == "table" then result.resolveErrors = negErrors end
    end
    return result
end

tools.negate = tools.subtract

tools.intersect = function(args)
    local groups = resolveGroups("intersect", args)
    if groups then
        local results = {}
        for _, g in ipairs(groups) do
            if g.base then
                local gArgs = {}
                for key, value in pairs(args) do gArgs[key] = value end
                gArgs.name = g.name or ("Intersection" .. tostring(g.group))
                table.insert(results, runSolidOperation("intersect", g.base, g.others, gArgs))
            else
                table.insert(results, { ok = false, code = "REF_NOT_FOUND", error = g.error })
            end
        end
        return ok({ groups = results, count = #results })
    end
    local parts, errors = resolveMany(args.refs)
    local others = {}
    for ii = 2, #parts do table.insert(others, parts[ii]) end
    local result = runSolidOperation("intersect", parts[1], others, args)
    if type(errors) == "table" and #errors > 0 then
        if type(result) == "table" then result.resolveErrors = errors end
    end
    return result
end

tools.separate = function(args)
    local inst, err = resolveRef(args.ref)
    if not inst then return fail(err) end
    if not inst:IsA("PartOperation") then
        return fail("'" .. inst.Name .. "' is a " .. inst.ClassName .. ", not a union.")
    end
    local parent = inst.Parent
    local pieces = nil
    local okRun, runErr = pcall(function()
        pieces = inst:SeparateAsync()
    end)
    if not okRun then return fail("SeparateAsync failed: " .. tostring(runErr)) end
    local items = {}
    for _, piece in ipairs(pieces or {}) do
        piece.Parent = parent
        table.insert(items, describeRef(piece))
    end
    pcall(function() inst:Destroy() end)
    waypoint("separate")
    return ok({ pieces = items, count = #items }, { "The pieces are plain parts again. Colours or materials of the original union may not be restored exactly." })
end

tools.union_info = function(args)
    local inst, err = resolveRef(args.ref)
    if not inst then return fail(err) end
    local isUnion = inst:IsA("PartOperation")
    return ok({
        instance = describeRef(inst),
        isUnion = isUnion,
        collisionFidelity = isUnion and tostring(inst.CollisionFidelity) or nil,
        renderFidelity = isUnion and tostring(inst.RenderFidelity) or nil,
        bounds = boundsInfo(inst),
        advice = isUnion and "You cannot inspect the original parts of a union. Call separate to edit them." or "Not a union.",
    })
end

-- ------------------------- FUELLEN (nach GEMESSENER Regel) ------------------
local worldProfile = nil

tools.probe_world = function(args)
    local center = decodeValue(args.center)
    if typeof(center) ~= "Vector3" then center = Vector3.new(0, 0, 0) end
    local radius = tonumber(args.radius) or 40
    local step = tonumber(args.step) or 10
    if step < 1 then step = 1 end
    local params = measureRayParams({})
    local heights = {}
    local waterY = nil
    local total = 0
    local x = center.X - radius
    while x <= center.X + radius + 0.001 do
        local z = center.Z - radius
        while z <= center.Z + radius + 0.001 do
            local dx = x - center.X
            local dz = z - center.Z
            if dx * dx + dz * dz <= radius * radius then
                total = total + 1
                local hit = Workspace:Raycast(Vector3.new(x, center.Y + 400, z), Vector3.new(0, -800, 0), params)
                if hit then
                    local y = hit.Position.Y
                    table.insert(heights, y)
                    if isWaterLike(hit.Instance) and (waterY == nil or y > waterY) then
                        waterY = y
                    end
                end
            end
            z = z + step
        end
        x = x + step
    end
    if #heights < 8 then
        return failCode("BAD_ARGS", "Too few surface samples (" .. tostring(#heights) .. " of " .. tostring(total)
            .. "). Is this place empty here? Try a bigger radius or a center that sits on the ground.")
    end
    -- Gitter-Schritt: haeufigste kleine Differenz zwischen den Flaechen
    table.sort(heights)
    local distinct = {}
    for i = 1, #heights do
        if i == 1 or heights[i] - heights[i - 1] > 0.1 then
            table.insert(distinct, heights[i])
        end
    end
    local diffs = {}
    for i = 2, #distinct do
        table.insert(diffs, distinct[i] - distinct[i - 1])
    end
    local gridStep = nil
    local candidates = { 0.5, 1, 2, 4, 8, 16, 32, 64 }
    for _, cand in ipairs(candidates) do
        local matches = 0
        for _, d in ipairs(diffs) do
            if d > 0.01 then
                local k = math.floor(d / cand + 0.5)
                if k >= 1 and math.abs(d - k * cand) < 0.06 * cand + 0.01 then
                    matches = matches + 1
                end
            end
        end
        if #diffs > 0 and matches / #diffs >= 0.6 then
            gridStep = cand
            break
        end
    end
    local sample = {}
    for i = 1, math.min(40, #heights) do sample[i] = heights[i] end
    local profile = {
        measuredAt = os.time(),
        center = { x = center.X, y = center.Y, z = center.Z },
        radius = radius,
        sampleCount = total,
        surfaceSamples = sample,
        gridStep = gridStep,
        waterY = waterY,
        fillRule = {
            formula = "fresh column: y1 if y1 is divisible by gridStep, else ceil(y1/gridStep)*gridStep + 2. water column: y1 - 2.",
            gridStep = gridStep,
            waterY = waterY,
            note = "Heights are ALWAYS measured per column at fill time (raycast). This profile only fixes the grid step and the water level.",
        },
    }
    worldProfile = profile
    return ok(profile, { "Stored: fill_region now uses this profile. Re-run probe_world after big terrain changes." })
end

tools.fill_region = function(args)
    local minVec = decodeValue(args.min)
    local maxVec = decodeValue(args.max)
    if typeof(minVec) ~= "Vector3" or typeof(maxVec) ~= "Vector3" then
        return failCode("BAD_ARGS", "min and max must be {x,y,z}.")
    end
    local gridStep = tonumber(args.gridStep)
    if gridStep == nil then
        if worldProfile == nil then
            return failCode("WORLD_NOT_PROBED", "fill_region needs a measured world profile - call probe_world first (or pass an explicit gridStep). Fill heights are never guessed.")
        end
        gridStep = worldProfile.gridStep
        if gridStep == nil then
            return failCode("WORLD_NOT_PROBED", "The measured profile has no reliable grid step - pass gridStep explicitly (e.g. 4).")
        end
    end
    if gridStep <= 0.1 then return failCode("BAD_ARGS", "gridStep must be > 0.1 studs.") end

    local minX, maxX = math.min(minVec.X, maxVec.X), math.max(minVec.X, maxVec.X)
    local minZ, maxZ = math.min(minVec.Z, maxVec.Z), math.max(minVec.Z, maxVec.Z)
    local bottomY = math.min(minVec.Y, maxVec.Y)
    local topY = math.max(minVec.Y, maxVec.Y)
    if topY <= bottomY then return failCode("BAD_ARGS", "max.Y must be above min.Y.") end

    local cols = math.floor((maxX - minX) / gridStep + 0.999) + 1
    local rows = math.floor((maxZ - minZ) / gridStep + 0.999) + 1
    local totalColumns = cols * rows
    if totalColumns > 4000 then
        return failCode("REGION_LIMIT",
            "Region is " .. tostring(totalColumns) .. " grid columns (" .. string.format("%.0f x %.0f", maxX - minX, maxZ - minZ)
            .. " studs at step " .. tostring(gridStep) .. "), max is 4000. Split the region into smaller boxes - every call returns a resumeToken, so the next box continues instead of restarting.",
            { measuredLimit = 4000, regionColumns = totalColumns })
    end
    if (maxX - minX) > 400 or (maxZ - minZ) > 400 then
        return failCode("REGION_LIMIT", "One side of the region is over 400 studs - split it up.", { measuredLimit = 400 })
    end

    local with = args.with or "Air"
    local isAir = (tostring(with) == "Air")
    local fillTo = args.fillTo or "rule"
    local clearBelowFirst = (args.clearBelowFirst ~= false)
    local confirmClear = (args.confirmClear == true)
    local chunkBudget = tonumber(args.chunkBudget) or 200
    local stopOnError = (args.stopOnError == true)

    local created = 0
    local cleared = 0
    local alreadyDone = 0
    local skippedNeedClear = {}
    local skippedNoSurface = 0
    local failedCells = {}
    local createdParts = {}
    local startedAt = os.clock()

    local startIndex = 1
    if type(args.resumeToken) == "table" and tonumber(args.resumeToken.index) then
        startIndex = tonumber(args.resumeToken.index) + 1
        if startIndex > totalColumns then startIndex = totalColumns + 1 end
    end

    local function columnAt(n)
        local col = (n - 1) % cols
        local row = math.floor((n - 1) / cols)
        return minX + col * gridStep, minZ + row * gridStep
    end

    local rayTopY = topY + 500
    local params = measureRayParams({})
    local lastProgressAt = os.clock()

    local function reportProgress(n, force)
        local now = os.clock()
        if force or now - lastProgressAt > 0.2 then
            lastProgressAt = now
            local pct = math.floor((n / totalColumns) * 100)
            local doneCount = n - startIndex + 1
            local rate = doneCount / math.max(0.01, os.clock() - startedAt)
            if args._job then
                args._job.progress(pct, doneCount .. "/" .. tostring(totalColumns) .. " columns, " .. string.format("%.0f", rate) .. " columns/s")
            end
            task.wait(0.01)
        end
    end

    for n = startIndex, totalColumns do
        if args._job and args._job.cancelled() then
            return ok({
                aborted = "cancelled",
                created = created, cleared = cleared, alreadyDone = alreadyDone,
                skippedNeedClear = #skippedNeedClear, skippedNoSurface = skippedNoSurface,
                failedCells = failedCells, totalColumns = totalColumns,
                resumeToken = { index = n - 1 },
                note = "Job cancelled - repeat the call with this resumeToken to continue here.",
            })
        end
        local x, z = columnAt(n)
        local okCell, err = pcall(function()
            if isAir then
                -- Air: in dieser Spalte den Box-Bereich von ArenaFill-Teilen befreien.
                local lo3 = Vector3.new(x - gridStep / 2, bottomY, z - gridStep / 2)
                local hi3 = Vector3.new(x + gridStep / 2, topY + 0.1, z + gridStep / 2)
                local boxParts = Workspace:GetPartBoundsInBox((lo3 + hi3) / 2, (hi3 - lo3), overlapParamsNew({}))
                local foreign = false
                for _, part in ipairs(boxParts) do
                    local cfP, sizeP = boundsOf(part)
                    if cfP and sizeP then
                        local okTag, hasTag = pcall(function() return CollectionService:HasTag(part, "ArenaFill") end)
                        local partTop = cfP.Position.Y + sizeP.Y / 2
                        local partBottom = cfP.Position.Y - sizeP.Y / 2
                        if okTag and hasTag and partTop <= topY + 0.05 and partBottom >= bottomY - 0.05 then
                            pcall(function() part:Destroy() end)
                            cleared = cleared + 1
                        else
                            foreign = true
                        end
                    end
                end
                if foreign and #skippedNeedClear < 30 then
                    table.insert(skippedNeedClear, {
                        column = { x = x, z = z },
                        note = "Contains non-ArenaFill parts (or parts extending below the box) - NOT cleared. Your parts are never touched.",
                    })
                end
                return
            end

            local hit = Workspace:Raycast(Vector3.new(x, rayTopY, z), Vector3.new(0, -800, 0), params)
            if hit == nil then
                skippedNoSurface = skippedNoSurface + 1
                return
            end
            local y1 = hit.Position.Y
            local waterTop = isWaterLike(hit.Instance)

            local target
            if type(fillTo) == "number" then
                target = fillTo
            elseif tostring(fillTo) == "top" then
                target = topY
            else
                if waterTop then
                    target = y1 - 2
                else
                    local rounded = math.floor(y1 / gridStep + 0.5) * gridStep
                    if math.abs(y1 - rounded) < 0.01 then
                        target = y1
                    else
                        target = math.ceil(y1 / gridStep) * gridStep + 2
                    end
                end
            end

            if target <= y1 + 0.05 then
                alreadyDone = alreadyDone + 1
                return
            end

            if target > y1 + 0.05 then
                local bottom = math.max(y1, bottomY)
                if target > bottom + 0.05 then
                    local part = Instance.new("Part")
                    local tplName = (type(with) == "table" and with.name) or nil
                    part.Name = tplName or "Fill"
                    part.Size = Vector3.new(gridStep, target - bottom, gridStep)
                    part.Position = Vector3.new(x, bottom + (target - bottom) / 2, z)
                    part.Anchored = true
                    if type(with) == "table" and type(with.properties) == "table" then
                        applyProperties(part, with.properties)
                    end
                    part.Parent = Workspace
                    CollectionService:AddTag(part, "ArenaFill")
                    created = created + 1
                    if #createdParts < 5 then table.insert(createdParts, part) end
                else
                    alreadyDone = alreadyDone + 1
                end
                return
            end

            -- Tiefer als die Oberflaeche: [target, y1] muss frei sein.
            -- Nur ArenaFill-Teile werden geloescht, und nur wenn sie komplett
            -- im Bereich liegen. Fremde/teilverdeckende Teile bleiben unangetastet.
            local lo4 = Vector3.new(x - gridStep / 2, target, z - gridStep / 2)
            local hi4 = Vector3.new(x + gridStep / 2, y1 + 0.1, z + gridStep / 2)
            local boxParts = Workspace:GetPartBoundsInBox((lo4 + hi4) / 2, (hi4 - lo4), overlapParamsNew({}))
            local foreign = false
            for _, part in ipairs(boxParts) do
                local cfP, sizeP = boundsOf(part)
                if cfP and sizeP then
                    local okTag, hasTag = pcall(function() return CollectionService:HasTag(part, "ArenaFill") end)
                    local partBottom = cfP.Position.Y - sizeP.Y / 2
                    if okTag and hasTag and partBottom >= target - 0.05 then
                        if clearBelowFirst or confirmClear then
                            pcall(function() part:Destroy() end)
                            cleared = cleared + 1
                        else
                            foreign = true
                        end
                    else
                        foreign = true
                    end
                end
            end
            if foreign and #skippedNeedClear < 30 then
                table.insert(skippedNeedClear, {
                    column = { x = x, z = z },
                    note = "Existing parts block the depth (not ArenaFill, or they extend below target) - column NOT changed. Only 'ArenaFill'-tagged parts are ever cleared.",
                })
            else
                -- Bereich ist jetzt frei: von target bis zur Oberflaeche y1 auffuellen.
                if y1 - target > 0.05 then
                    local part = Instance.new("Part")
                    part.Name = tplName or "Fill"
                    part.Size = Vector3.new(gridStep, y1 - target, gridStep)
                    part.Position = Vector3.new(x, target + (y1 - target) / 2, z)
                    part.Anchored = true
                    if type(with) == "table" and type(with.properties) == "table" then
                        applyProperties(part, with.properties)
                    end
                    part.Parent = Workspace
                    CollectionService:AddTag(part, "ArenaFill")
                    created = created + 1
                    if #createdParts < 5 then table.insert(createdParts, part) end
                else
                    alreadyDone = alreadyDone + 1
                end
            end
        end)
        if not okCell then
            table.insert(failedCells, { x = x, z = z, error = tostring(err) })
            if stopOnError then
                return ok({
                    created = created, cleared = cleared, alreadyDone = alreadyDone,
                    skippedNeedClear = #skippedNeedClear, skippedNoSurface = skippedNoSurface,
                    failedCells = failedCells, totalColumns = totalColumns,
                    stoppedAt = n, resumeToken = { index = n - 1 },
                    note = "Stopped on the first cell error - continue with the same resumeToken.",
                })
            end
        end
        if (n - startIndex + 1) % chunkBudget == 0 or n == totalColumns then
            reportProgress(n, (n == totalColumns))
        end
    end

    local elapsed = os.clock() - startedAt
    local rate = (totalColumns - startIndex + 1) / math.max(0.01, elapsed)
    local geometry = { ready = true, frames = 0 }
    if created > 0 then
        geometry = waitMeasurable(createdParts, 2)
    end
    return ok({
        created = created,
        cleared = cleared,
        alreadyDone = alreadyDone,
        skippedNeedClear = skippedNeedClear,
        skippedNoSurface = skippedNoSurface,
        failedCells = failedCells,
        totalColumns = totalColumns,
        partsPerSecond = math.floor(rate * 10) / 10,
        geometry = geometry,
        resumeToken = nil,
        usedProfile = {
            gridStep = gridStep,
            waterY = (worldProfile and worldProfile.waterY) or nil,
            fillRule = "rule",
        },
        note = "All created parts carry the tag 'ArenaFill' - fill_region only ever clears those. Your own parts are never touched.",
    })
end

-- ------------------------- Assets -------------------------------------------
tools.insert_asset = function(args)
    if InsertService == nil then return fail("InsertService is not available.") end
    local assetId = tonumber(args.assetId)
    if assetId == nil then return fail("assetId must be a number.") end
    local parent, err = resolveRef(args.parentRef or "game.Workspace")
    if not parent then return fail(err) end

    local model = nil
    local okLoad, loadErr = pcall(function()
        model = InsertService:LoadAsset(assetId)
    end)
    if not okLoad or model == nil then
        return fail("LoadAsset failed for " .. tostring(assetId) .. ": " .. tostring(loadErr)
            .. " (the asset may be private or not a model/mesh). For decals, sounds and textures you normally do NOT need to insert an asset - just set the property to rbxassetid://" .. tostring(assetId) .. ".")
    end

    local inserted = {}
    if args.unpack == false then
        model.Parent = parent
        table.insert(inserted, describeRef(model))
    else
        for _, child in ipairs(model:GetChildren()) do
            child.Parent = parent
            if args.name then child.Name = tostring(args.name) end
            table.insert(inserted, describeRef(child))
        end
        model:Destroy()
    end
    waypoint("insert asset")
    return ok({ inserted = inserted, assetId = assetId, count = #inserted })
end

tools.apply_asset = function(args)
    local list, errors = resolveMany(args.refs or args.ref)
    if #list == 0 then return fail("No instance resolved. " .. table.concat(errors, " ")) end
    local assetId = tonumber(args.assetId)
    if assetId == nil then return fail("assetId must be a number.") end
    local url = "rbxassetid://" .. tostring(assetId)
    local applied = {}
    for _, inst in ipairs(list) do
        local property = args.property
        if property == nil then
            if inst:IsA("Decal") or inst:IsA("Texture") then property = "Texture"
            elseif inst:IsA("Sound") then property = "SoundId"
            elseif inst:IsA("ImageLabel") or inst:IsA("ImageButton") then property = "Image"
            elseif inst:IsA("SpecialMesh") then property = "MeshId"
            elseif inst:IsA("MeshPart") then property = "TextureID"
            elseif inst:IsA("Animation") then property = "AnimationId"
            end
        end
        if property == nil then
            table.insert(errors, inst.Name .. ": cannot guess the property, pass 'property'.")
        else
            local okSet, setErr = setProperty(inst, property, url)
            if okSet then
                table.insert(applied, { instance = describeRef(inst), property = property, value = url })
            else
                table.insert(errors, inst.Name .. ": " .. tostring(setErr))
            end
        end
    end
    waypoint("apply asset")
    return ok({ applied = applied, count = #applied, errors = errors })
end

-- ------------------------- Ausgabefenster -----------------------------------
tools.get_output = function(args)
    return ok(readOutput(args))
end

tools.clear_output = function()
    outputBuffer = {}
    outputStart = outputSeq + 1
    errorCount = 0
    warningCount = 0
    pcall(function() LogService:ClearOutput() end)
    return ok({ cleared = true, cursor = outputSeq })
end

tools.get_errors = function(args)
    args = args or {}
    local snapshot = readOutput({
        since = args.since,
        limit = tonumber(args.limit) or 100,
        onlyErrors = true,
        filter = args.filter,
        regex = args.regex == true,
    })
    snapshot.errorCount = errorCount
    snapshot.warningCount = warningCount
    if snapshot.returned == 0 then
        snapshot.note = "No errors in the output buffer. If a script silently does nothing, add print() lines and read them with get_output."
    end
    return ok(snapshot)
end

tools.wait_for_output = function(args)
    local pattern = tostring(args.pattern or args.filter or "")
    local timeout = tonumber(args.timeoutSeconds) or 15
    if timeout > 110 then timeout = 110 end
    local since = tonumber(args.since) or outputSeq
    local deadline = os.clock() + timeout
    while os.clock() < deadline do
        local snapshot = readOutput({ since = since, limit = 200, filter = pattern, regex = args.regex == true, types = args.types })
        if snapshot.returned > 0 then
            return ok({ found = true, lines = snapshot.lines, cursor = snapshot.cursor })
        end
        task.wait(0.15)
    end
    return ok({ found = false, cursor = outputSeq, waited = timeout, note = "Nothing matched within the timeout." })
end

-- ------------------------- Play / Test --------------------------------------
tools.play_status = function()
    local state = playState()
    state.capabilities = capabilities
    state.defaultContext = defaultContext
    state.advice = state.running
        and "A test is running. Persistent edits are blocked (pass allowInPlayMode=true only for throw-away test changes). Call play_stop before real building."
        or "Edit mode - all changes are permanent and will be saved."
    return ok(state)
end

tools.play_start = function(args)
    local result = startPlay(args.mode or "play")
    if result.ok then
        return ok(result, result.warnings)
    end
    return fail(result.error, { state = result.state, warnings = result.warnings })
end

tools.play_stop = function()
    local result = stopPlay()
    if result.ok then
        return ok(result, result.warnings)
    end
    return fail(result.error, { state = result.state, warnings = result.warnings })
end

tools.play_pause = function()
    if not RunService:IsRunning() then return fail("Nothing is running.") end
    local okRun = pcall(function() RunService:Pause() end)
    if not okRun then return fail("Pause failed.") end
    return ok({ paused = true, state = playState() })
end

tools.play_resume = function()
    local okRun = pcall(function() RunService:Run() end)
    if not okRun then return fail("Resume failed.") end
    return ok({ resumed = true, state = playState() })
end

tools.set_context = function(args)
    local wanted = string.lower(tostring(args.context or "server"))
    if wanted ~= "server" and wanted ~= "client" then
        return fail("context must be 'server' or 'client'.")
    end
    defaultContext = wanted
    return ok({ context = defaultContext, note = "Runtime tools now target the " .. defaultContext .. " side." })
end

-- FIX 3.2: Robuste Lua-Ausfuehrung ueber alle Studio-Versionen hinweg.
-- Neuere Studio-Versionen haben load() aus dem Plugin-Kontext entfernt;
-- dadurch waren run_lua, compile_check und source-Jobs gebrochen
-- ("attempt to call a nil value" auf der load()-Zeile). Fallback-Kette:
--   1. load()        (neue API, mit eigener env)
--   2. loadstring()  (sehr alte API, ohne env)
--   3. Require-Trick: Ein temporeres ModuleScript fuehrt den Code aus.
--      "local _ENV" bindet die persistente Umgebung; der top-level Return
--      des Nutzers wird natuerlich der Wert von require().
local requireBoxSeq = 0

local function requireExec(source, envTable)
    requireBoxSeq = requireBoxSeq + 1
    local holder = Instance.new("Folder")
    holder.Name = "__ArenaLuaBox"
    local mod = Instance.new("ModuleScript")
    mod.Name = "Box" .. tostring(requireBoxSeq)
    local header = "local _ENV = _G.__ARENA_BRIDGE_LUA_ENV__ or _G\n"
    local okSet, setErr = pcall(function() mod.Source = header .. source end)
    if not okSet then
        return false, "Compile error: " .. tostring(setErr)
    end
    mod.Parent = holder
    holder.Parent = ReplicatedStorage
    local okStash, stashErr = pcall(function() _G.__ARENA_BRIDGE_LUA_ENV__ = envTable end)
    local okReq, reqValue = xpcall(require, debug.traceback, mod)
    pcall(function() _G.__ARENA_BRIDGE_LUA_ENV__ = nil end)
    holder:Destroy()
    if not okStash then
        return false, "Persistent environment unavailable: " .. tostring(stashErr)
    end
    if not okReq then
        return false, tostring(reqValue)
    end
    return true, reqValue
end

local function execUserSource(source, envTable, chunkName)
    if type(load) == "function" then
        local okL, fnOrErr = pcall(function() return load(source, chunkName, "t", envTable) end)
        if okL then
            if type(fnOrErr) == "function" then
                return xpcall(fnOrErr, debug.traceback)
            end
            return false, "Compile error: " .. tostring(fnOrErr)
        end
    end
    if type(loadstring) == "function" then
        local okL, fnOrErr = pcall(function() return loadstring(source) end)
        if okL then
            if type(fnOrErr) == "function" then
                return xpcall(fnOrErr, debug.traceback)
            end
            return false, "Compile error: " .. tostring(fnOrErr)
        end
    end
    return requireExec(source, envTable)
end

-- Fuehrt Lua in der PERSISTENTEN Umgebung aus (Helfer ohne "local" ueberleben).
local function runPersistentLua(source, job)
    local startSeq = outputSeq
    local okRun, result = execUserSource(source, luaEnv, "arena_lua")
    local printed = readOutput({ since = startSeq, limit = 200 })
    if not okRun then
        local msg = tostring(result)
        if string.find(msg, "Compile error:", 1, true) == 1 then
            return failCode("COMPILE_ERROR", msg, {
                fix = "Fix the syntax, then verify WITHOUT running via compile_check.",
            })
        end
        return failCode("RUNTIME_ERROR", msg, { output = printed.lines })
    end
    if job then job.progress(100, "fertig") end
    return ok({
        returned = encodeValue(result),
        hadReturn = (result ~= nil),
        output = printed.lines,
        context = currentContext(),
        environment = "persistent",
        persistentKeys = luaEnvKeys(),
    })
end

tools.run_lua = function(args)
    local context = string.lower(tostring(args.context or "auto"))
    if context == "client" then
        return failCode("NO_PLAYER", "Arbitrary Lua cannot run on the client (loadstring is disabled there). Use client_action, gui_click, gui_dump, move_character or send_input instead - they cover character, GUI and input.")
    end
    local source = tostring(args.source or args.code or "")
    if source == "" then return failCode("BAD_ARGS", "source missing.") end
    return runPersistentLua(source, nil)
end

tools.compile_check = function(args)
    local source = tostring(args.source or args.code or "")
    if source == "" then return failCode("BAD_ARGS", "source missing.") end
    if type(load) == "function" then
        local okL, fnOrErr = pcall(function() return load(source, "arena_check", "t", luaEnv) end)
        if okL then
            if type(fnOrErr) == "function" then
                return ok({ compiles = true, checked = "syntax only - the code was NOT executed" })
            end
            local line = string.match(tostring(fnOrErr), ":(%d+):")
            return failCode("COMPILE_ERROR", tostring(fnOrErr), {
                line = line and tonumber(line) or nil,
                checked = "syntax only - the code was NOT executed",
            })
        end
    end
    -- FIX 3.2 Fallback (load() fehlt im Plugin-Kontext): Source auf ein
    -- temporeres ModuleScript zu SETZEN kompiliert den Code, fuehrt ihn aber
    -- NICHT aus - genau die reine Syntaxpruefung, die compile_check ist.
    local holder = Instance.new("Folder")
    holder.Name = "__ArenaCheckBox"
    local tmp = Instance.new("ModuleScript")
    tmp.Name = "Check"
    tmp.Parent = holder
    local okSet, setErr = pcall(function() tmp.Source = source end)
    holder:Destroy()
    if not okSet then
        local line = string.match(tostring(setErr), ":(%d+):")
        return failCode("COMPILE_ERROR", tostring(setErr), {
            line = line and tonumber(line) or nil,
            checked = "syntax only - the code was NOT executed",
        })
    end
    return ok({ compiles = true, checked = "syntax only - the code was NOT executed" })
end

tools.lua_state = function()
    local keys = luaEnvKeys()
    local activeJobs = {}
    for _, job in ipairs(jobsList()) do
        if job.status == "running" then table.insert(activeJobs, job) end
    end
    return ok({
        keys = keys,
        count = #keys,
        jobs = activeJobs,
        note = "These are the non-local variables defined by earlier run_lua / job calls. They persist until clear_lua_state (confirm=true).",
    })
end

tools.clear_lua_state = function(args)
    if args and args.confirm ~= true then
        return failCode("BAD_ARGS", "clear_lua_state is destructive: pass confirm=true.")
    end
    local cancelled = 0
    for _, job in pairs(jobs) do
        if job.status == "running" then
            job.cancelled = true
            cancelled = cancelled + 1
        end
    end
    luaEnv = makeLuaEnv()
    return ok({ cleared = true, jobsCancelRequested = cancelled })
end

-- ---------------------------------------------------------------------------
-- JOB-TOOLS
-- ---------------------------------------------------------------------------
tools.start_job = function(args)
    local source = tostring(args.source or args.code or "")
    local tool = args.tool
    local jobArgs = args.args or {}
    local name = args.name
    local jobId = nil
    if source ~= "" then
        jobId = newJob(name or "lua_job", function(job)
            return runPersistentLua(source, job)
        end)
    elseif tool then
        if tool == "start_job" then
            return failCode("BAD_ARGS", "start_job cannot wrap itself.")
        end
        if not tools[tool] then
            return failCode("UNKNOWN_TOOL", "Unknown job tool: " .. tostring(tool))
        end
        jobId = newJob(tostring(tool), function(job)
            local jArgs = {}
            for key, value in pairs(jobArgs) do jArgs[key] = value end
            jArgs._job = { progress = job.progress, cancelled = job.cancelled }
            return executeTool(tool, jArgs, true)
        end)
    else
        return failCode("BAD_ARGS", "start_job needs source (Lua) or tool+args.")
    end
    return ok({
        jobId = jobId,
        status = "running",
        poll = "job_status",
        note = "The job runs in the background and survives timeouts. Check job_status, then job_result.",
    })
end

tools.job_status = function(args)
    local job = jobs[args and tostring(args.jobId)]
    if not job then
        return failCode("JOB_NOT_FOUND", "Unknown jobId '" .. tostring(args and args.jobId) .. "' (it may have been evicted after job_result).")
    end
    return ok(jobSnapshot(job))
end

tools.job_result = function(args)
    local job = jobs[args and tostring(args.jobId)]
    if not job then
        return failCode("JOB_NOT_FOUND", "Unknown jobId '" .. tostring(args and args.jobId) .. "'.")
    end
    if job.status == "running" then
        return failCode("JOB_RUNNING", "The job is not finished yet.", { status = jobSnapshot(job) })
    end
    if job.status == "cancelled" then
        return failCode("RUNTIME_ERROR", "The job was cancelled.", { status = jobSnapshot(job) })
    end
    if job.status == "error" then
        return failCode(job.errorCode or "RUNTIME_ERROR", job.error, { status = jobSnapshot(job) })
    end
    -- done: Ergebnis kann selbst ok=false sein (z.B. ein Tool-Fehler im Job).
    local result = job.result
    if type(result) ~= "table" then
        result = { ok = true, result = result }
    end
    return result
end

tools.list_jobs = function()
    return ok({ jobs = jobsList(), count = jobsCount() })
end

tools.cancel_job = function(args)
    local job = jobs[args and tostring(args.jobId)]
    if not job then
        return failCode("JOB_NOT_FOUND", "Unknown jobId '" .. tostring(args and args.jobId) .. "'.")
    end
    if job.status == "running" then
        job.cancelled = true
        return ok({ jobId = job.id, requested = true, note = "Cancellation is cooperative: the job notices it at its next check (job:cancelled()) and stops itself. Nothing is killed hard." })
    end
    return ok({ jobId = job.id, requested = false, status = job.status, note = "The job already finished." })
end

tools.client_action = function(args)
    local response, err = callClient(args.action, args.args or args, tonumber(args.timeoutSeconds) or 8)
    if response == nil then
        return failCode("NO_PLAYER", err)
    end
    if type(response) == "table" and response.ok == false then
        return failCode("RUNTIME_ERROR", response.error or "Client action failed.", { client = true })
    end
    return ok(response)
end

tools.character_state = function()
    if not RunService:IsRunning() then return fail("No test running. Call play_start first.") end
    local player = Players:GetPlayers()[1]
    if player == nil then return fail("No player. Run mode has no character - use play_start with mode 'play'.") end
    local character = player.Character
    if character == nil then return ok({ hasCharacter = false, player = player.Name }) end
    local humanoid = character:FindFirstChildOfClass("Humanoid")
    local root = character:FindFirstChild("HumanoidRootPart")
    return ok({
        hasCharacter = true,
        player = player.Name,
        position = root and encodeValue(root.Position) or nil,
        cframe = root and encodeValue(root.CFrame) or nil,
        health = humanoid and humanoid.Health or nil,
        maxHealth = humanoid and humanoid.MaxHealth or nil,
        walkSpeed = humanoid and humanoid.WalkSpeed or nil,
        jumpPower = humanoid and humanoid.JumpPower or nil,
        state = humanoid and tostring(humanoid:GetState()) or nil,
    })
end

tools.move_character = function(args)
    if not RunService:IsRunning() then return fail("No test running. Call play_start first.") end
    local player = Players:GetPlayers()[1]
    if player == nil then return fail("No player in this test session.") end
    local character = player.Character
    local humanoid = character and character:FindFirstChildOfClass("Humanoid")
    if humanoid == nil then return fail("Character has no Humanoid yet.") end
    aiMoveUntil = os.clock() + 5

    local target = decodeValue(args.position)
    if typeof(target) ~= "Vector3" and args.targetRef then
        local inst = resolveRef(args.targetRef)
        local pivot = inst and getPivotOf(inst)
        if pivot then target = pivot.Position end
    end

    if typeof(target) == "Vector3" then
        humanoid:MoveTo(target)
        if args.waitForArrival ~= false then
            local reached = false
            local finished = false
            humanoid.MoveToFinished:Once(function(value)
                reached = value
                finished = true
            end)
            local waited = 0
            local limit = tonumber(args.timeoutSeconds) or 12
            while not finished and waited < limit do
                task.wait(0.1)
                waited = waited + 0.1
            end
            local root = character:FindFirstChild("HumanoidRootPart")
            return ok({
                reached = reached,
                position = root and encodeValue(root.Position) or nil,
                distanceLeft = root and (target - root.Position).Magnitude or nil,
            })
        end
        return ok({ moving = true })
    end

    -- Bewegung ueber Tasten (echte Eingabe), z.B. keys = "W"
    local keys = args.keys or args.direction
    if keys then
        local duration = tonumber(args.duration) or 1
        if type(keys) == "string" then keys = { keys } end
        local pressed = {}
        for _, key in ipairs(keys) do
            local okKey, keyErr = sendKey(key, duration, args.shift and { "LeftShift" } or nil)
            table.insert(pressed, { key = key, ok = okKey, error = keyErr })
        end
        local root = character:FindFirstChild("HumanoidRootPart")
        return ok({ pressed = pressed, position = root and encodeValue(root.Position) or nil })
    end

    return fail("Need position {x,y,z}, targetRef, or keys like ['W'].")
end

tools.teleport_character = function(args)
    if not RunService:IsRunning() then return fail("No test running.") end
    local player = Players:GetPlayers()[1]
    if player == nil then return fail("No player.") end
    local character = player.Character
    if character == nil then return fail("No character.") end
    aiMoveUntil = os.clock() + 6
    local target = decodeValue(args.position)
    if typeof(target) ~= "Vector3" and args.targetRef then
        local inst = resolveRef(args.targetRef)
        local pivot = inst and getPivotOf(inst)
        if pivot then target = pivot.Position + Vector3.new(0, 5, 0) end
    end
    if typeof(target) ~= "Vector3" then return fail("Need position or targetRef.") end
    local okMove = pcall(function() character:PivotTo(CFrame.new(target)) end)
    if not okMove then return fail("Teleport failed.") end
    return ok({ position = encodeValue(target) })
end

tools.respawn_character = function()
    if not RunService:IsRunning() then return fail("No test running.") end
    local player = Players:GetPlayers()[1]
    if player == nil then return fail("No player.") end
    local okLoad = pcall(function() player:LoadCharacter() end)
    if not okLoad then return fail("LoadCharacter failed.") end
    task.wait(0.5)
    return ok({ respawned = true })
end

local function guiFindInItems(items, query)
    local wanted = string.lower(tostring(query))
    local best = nil
    for _, item in ipairs(items) do
        local nameMatch = string.find(string.lower(item.name), wanted, 1, true)
        local textMatch = item.text and string.find(string.lower(tostring(item.text)), wanted, 1, true)
        local pathMatch = string.find(string.lower(item.path), wanted, 1, true)
        if nameMatch or textMatch or pathMatch then
            if best == nil or (item.clickable and not best.clickable) then
                best = item
            end
        end
    end
    return best
end

tools.gui_dump = function(args)
    local response, err = callClient("gui_dump", { limit = tonumber(args.limit) or 200 }, 8)
    if response == null then return failCode("NO_PLAYER", err) end
    return ok(response)
end

-- GUI-TEST-HARNESS: EIN Dump, dann alle erwarteten Zustaende gepraeft.
tools.gui_check = function(args)
    local checks = args.checks or args.expect or {}
    if #checks == 0 then
        return failCode("BAD_ARGS", "checks must be a list, e.g. { { query = 'Start', expectVisible = true }, { query = 'Score', expectText = '10' } }.")
    end
    local response, err = callClient("gui_dump", { limit = tonumber(args.limit) or 400 }, 8)
    if response == nil then return failCode("NO_PLAYER", err) end
    local items = response.items or {}
    local results = {}
    local allPassed = true
    for _, check in ipairs(checks) do
        local query = check.query or check.text or check.name
        if query == nil then
            table.insert(results, { passed = false, error = "check needs query/text/name" })
            allPassed = false
        else
            local item = guiFindInItems(items, query)
            local entry = { query = query, found = (item ~= nil) }
            local passed = true
            if item == nil then
                passed = (check.expectPresent == false)
                if not passed then entry.fail = "element not found" end
            else
                entry.item = { name = item.name, path = item.path, text = item.text, visible = item.visible, clickable = item.clickable }
                if check.expectPresent == false then
                    passed = false
                    entry.fail = "expected to be absent, but it exists"
                end
                if passed and check.expectVisible ~= nil and check.expectVisible ~= item.visible then
                    passed = false
                    entry.fail = "visible = " .. tostring(item.visible) .. ", expected " .. tostring(check.expectVisible)
                end
                if passed and check.expectText then
                    local textOk = item.text and string.find(tostring(item.text), tostring(check.expectText), 1, true) ~= nil
                    if not textOk then
                        -- Text auch in anderen Elementen suchen (z.B. Counter neben dem Button)
                        for _, other in ipairs(items) do
                            if other.text and string.find(tostring(other.text), tostring(check.expectText), 1, true) then
                                textOk = true
                                break
                            end
                        end
                    end
                    if not textOk then
                        passed = false
                        entry.fail = "no element contains the text '" .. tostring(check.expectText) .. "'"
                    end
                end
            end
            entry.passed = passed
            if not passed then allPassed = false end
            table.insert(results, entry)
        end
    end
    return ok({ allPassed = allPassed, checks = results, guiItemCount = #items })
end

tools.gui_click = function(args)
    local query = args.query or args.text or args.name
    if query == nil then return failCode("BAD_ARGS", "Need query/text/name of the GUI element.") end
    local response, err = callClient("gui_find", { query = query }, 8)
    if response == nil then return failCode("NO_PLAYER", err) end
    if response.ok ~= true or response.item == nil then
        return failCode("GUI_NOT_FOUND", response.error or "GUI element not found.")
    end
    local item = response.item
    if item.visible == false then
        return failCode("GUI_NOT_FOUND", "The element '" .. tostring(item.name) .. "' is currently not visible.", { element = item })
    end
    local clicked, clickErr = sendClick(item.centerX, item.centerY, 0, tonumber(args.holdSeconds) or 0.06)
    if not clicked then
        return failCode("RUNTIME_ERROR", "Could not send the click: " .. tostring(clickErr), { element = item })
    end
    task.wait(tonumber(args.settleSeconds) or 0.35)
    local recent = readOutput({ limit = 25 })

    -- Erwartetes Ergebnis pruefen (gui_click mit expect)
    local expect = args.expect
    local expectResult = nil
    local afterSnapshot = nil
    if expect ~= nil then
        task.wait(tonumber(args.waitSeconds) or 0.8)
        local dumpResp, dumpErr = callClient("gui_dump", { limit = 400 }, 8)
        if dumpResp == nil then
            expectResult = { expected = expect, passed = false, error = dumpErr or "gui dump failed" }
        else
            local items = dumpResp.items or {}
            afterSnapshot = { guiItemCount = #items }
            local target = guiFindInItems(items, query)
            if type(expect) == "table" then
                local okExpect = true
                local problems = {}
                if expect.visible ~= nil and (target == nil or target.visible ~= expect.visible) then
                    okExpect = false
                    table.insert(problems, "visibility")
                end
                if expect.text then
                    local foundText = false
                    for _, other in ipairs(items) do
                        if other.text and string.find(tostring(other.text), tostring(expect.text), 1, true) then
                            foundText = true
                            break
                        end
                    end
                    if not foundText then
                        okExpect = false
                        table.insert(problems, "text '" .. tostring(expect.text) .. "'")
                    end
                end
                expectResult = {
                    expected = expect,
                    passed = okExpect,
                    problems = (#problems > 0) and problems or nil,
                    target = target and { name = target.name, visible = target.visible, text = target.text } or nil,
                }
            elseif type(expect) == "string" then
                local found = false
                for _, other in ipairs(items) do
                    if (other.text and string.find(tostring(other.text), expect, 1, true))
                        or string.find(string.lower(other.name), string.lower(expect), 1, true) then
                        found = true
                        break
                    end
                end
                expectResult = { expected = expect, passed = found }
            end
        end
    end

    return ok({
        clicked = item,
        expect = expectResult,
        outputAfterClick = recent.lines,
        afterSnapshot = afterSnapshot,
    })
end

tools.set_camera = function(args)
    local lookAt = nil
    if args.lookAt then
        lookAt = decodeValue(args.lookAt)
    elseif args.targetRef then
        local target = resolveRef(args.targetRef)
        local cf = target and getPivotOf(target)
        if cf then lookAt = cf.Position end
    end
    local position = decodeValue(args.position)
    if typeof(position) ~= "Vector3" then
        return failCode("BAD_ARGS", "position must be {x,y,z} (and optionally lookAt {x,y,z} or targetRef).")
    end
    local response, err = callClient("camera", { position = position, lookAt = lookAt }, 8)
    if response == nil then return failCode("NO_PLAYER", err) end
    return ok({ camera = "moved (client agent marks this as AI-driven for 4 seconds, so user-action events stay clean)" })
end

tools.gui_set_text = function(args)
    local response, err = callClient("set_text", { query = args.query or args.name, text = args.text }, 8)
    if response == nil then return fail(err) end
    return ok(response)
end

tools.send_input = function(args)
    local results = {}
    if args.keys then
        local keys = args.keys
        if type(keys) == "string" then keys = { keys } end
        for _, key in ipairs(keys) do
            local keyName = key
            local duration = tonumber(args.duration) or 0.1
            local modifiers = args.modifiers
            if type(key) == "table" then
                keyName = key.key
                duration = tonumber(key.duration) or duration
                modifiers = key.modifiers or modifiers
            end
            local okKey, keyErr = sendKey(keyName, duration, modifiers)
            table.insert(results, { key = keyName, ok = okKey, error = keyErr })
        end
    end
    if args.click then
        local click = args.click
        local okClick, clickErr = sendClick(tonumber(click.x) or 0, tonumber(click.y) or 0, tonumber(click.button) or 0, tonumber(click.hold) or 0.06)
        table.insert(results, { click = click, ok = okClick, error = clickErr })
    end
    if #results == 0 then
        return fail("Nothing to send. Use keys=['W'] or click={x=..,y=..}.")
    end
    if VirtualInputManager == nil then
        return fail("VirtualInputManager is not available, so real input cannot be simulated. Use move_character with a position instead.")
    end
    task.wait(tonumber(args.settleSeconds) or 0.2)
    return ok({ sent = results, output = readOutput({ limit = 25 }).lines })
end

tools.wait = function(args)
    local seconds = tonumber(args.seconds) or 1
    if seconds > 60 then seconds = 60 end
    local startSeq = outputSeq
    task.wait(seconds)
    return ok({ waited = seconds, output = readOutput({ since = startSeq, limit = 200 }).lines })
end

-- ------------------------- Verlauf ------------------------------------------
tools.undo = function()
    if ChangeHistoryService == nil then return fail("ChangeHistoryService unavailable.") end
    local okRun = pcall(function() ChangeHistoryService:Undo() end)
    if not okRun then return fail("Undo failed.") end
    return ok({ undone = true })
end

tools.redo = function()
    if ChangeHistoryService == nil then return fail("ChangeHistoryService unavailable.") end
    local okRun = pcall(function() ChangeHistoryService:Redo() end)
    if not okRun then return fail("Redo failed.") end
    return ok({ redone = true })
end

tools.set_waypoint = function(args)
    waypoint(args.name or "manual")
    return ok({ waypoint = args.name or "manual" })
end

-- ---------------------------------------------------------------------------
-- SCHUTZ IM PLAY-MODUS
-- Alles, was den gespeicherten Place veraendert, wird im Testmodus
-- blockiert - dort gehen Aenderungen beim Stoppen verloren.
-- ---------------------------------------------------------------------------
local PERSISTENT_WRITE_TOOLS = {
    create_instance = true, bulk_create = true, clone_instance = true,
    delete_instance = true, bulk_delete = true, rename_instance = true,
    move_instance = true, set_property = true, set_properties = true,
    bulk_set_properties = true, set_attribute = true, add_tag = true, remove_tag = true,
    group_instances = true, ungroup = true,
    insert_script = true, bulk_insert_scripts = true, set_script_source = true, patch_script = true,
    place_on = true, align = true, stack = true, grid_arrange = true, distribute = true,
    snap_to_ground = true, look_at = true, rotate_around = true, move_relative = true,
    resize_part = true, fit_between = true,
    union = true, subtract = true, negate = true, intersect = true, separate = true,
    insert_asset = true, apply_asset = true,
    point_at = true, fill_region = true,
    undo = true, redo = true,
}

local WRITE_TOOLS = {}
for name, value in pairs(PERSISTENT_WRITE_TOOLS) do WRITE_TOOLS[name] = value end
WRITE_TOOLS.run_lua = true
WRITE_TOOLS.select_instance = true
WRITE_TOOLS.play_start = true
WRITE_TOOLS.play_stop = true
WRITE_TOOLS.send_input = true
WRITE_TOOLS.gui_click = true
WRITE_TOOLS.gui_set_text = true
WRITE_TOOLS.move_character = true
WRITE_TOOLS.teleport_character = true

local function takeNotices()
    local list = {}
    for _, notice in ipairs(notices) do
        if notice.delivered ~= true then
            notice.delivered = true
            table.insert(list, { kind = notice.kind, message = notice.message, time = notice.time, data = notice.data })
        end
    end
    return list
end

tools.get_notices = function(args)
    if args and args.all == true then
        return ok({ notices = notices })
    end
    return ok({ notices = takeNotices() })
end

-- ---------------------------------------------------------------------------
-- AUSFUEHRUNG
-- ---------------------------------------------------------------------------

local function toolNames()
    local names = {}
    for name, _ in pairs(tools) do table.insert(names, name) end
    table.sort(names)
    return names
end

tools.list_tools = function()
    return ok({ tools = toolNames(), count = #toolNames(), pluginVersion = ARENA_VERSION })
end

tools.batch = function(args)
    local commands = args.commands or args.items or {}
    local parallel = args.parallel == true
    local stopOnError = args.stopOnError == true
    local results = {}

    if parallel then
        local finished = 0
        local total = #commands
        for index, item in ipairs(commands) do
            task.spawn(function()
                local okRun, result = pcall(function()
                    return executeTool(item.tool, item.args or {}, true)
                end)
                if okRun then
                    results[index] = result
                else
                    results[index] = { ok = false, error = tostring(result) }
                end
                finished = finished + 1
            end)
        end
        local waited = 0
        local limit = tonumber(args.timeoutSeconds) or 90
        while finished < total and waited < limit do
            task.wait(0.05)
            waited = waited + 0.05
        end
        local list = {}
        for index = 1, total do
            list[index] = results[index] or { ok = false, error = "Timed out inside the batch." }
        end
        local failures = 0
        for _, item in ipairs(list) do
            if item.ok ~= true then failures = failures + 1 end
        end
        return ok({ results = list, count = #list, failed = failures, mode = "parallel" })
    end

    local failures = 0
    for index, item in ipairs(commands) do
        local okRun, result = pcall(function()
            return executeTool(item.tool, item.args or {}, true)
        end)
        if not okRun then
            result = { ok = false, error = tostring(result) }
        end
        results[index] = result
        if result.ok ~= true then
            failures = failures + 1
            if stopOnError then
                return ok({ results = results, count = #results, failed = failures, stoppedAt = index, mode = "sequential" })
            end
        end
    end
    return ok({ results = results, count = #results, failed = failures, mode = "sequential" })
end

tools.parallel = function(args)
    local copy = {}
    for key, value in pairs(args) do copy[key] = value end
    copy.parallel = true
    return tools.batch(copy)
end

executeTool = function(tool, args, insideBatch)
    args = args or {}
    local handler = tools[tool]
    if handler == nil then
        return failCode("UNKNOWN_TOOL", "Unknown tool: " .. tostring(tool), {
            hint = "Call list_tools to see everything this bridge can do.",
        })
    end

    if accessMode == "readonly" and WRITE_TOOLS[tool] then
        return failCode("READONLY_TOKEN", "This place is in read-only mode (switched in the Arena Roblox Bridge app).")
    end

    local warnings = nil
    if RunService:IsRunning() and PERSISTENT_WRITE_TOOLS[tool] then
        if userPlaytestActive then
            return failCode("USER_PLAYTEST_ACTIVE",
                "IMPORTANT: The user is currently in Roblox Studio " .. currentMode() .. " mode. STOP your current response and do not edit anything: test-mode changes would be temporary and could disrupt the user while they are playing.", {
                assistantAction = "STOP_CURRENT_RESPONSE",
                howToFix = "Tell the user that you can see their playtest is active and politely ask them to leave/stop the playtest in Roblox Studio. Wait for the user to confirm they are back in Edit mode before continuing. Do NOT call play_stop on the user's behalf.",
                userMessage = "Ich sehe, dass du Roblox Studio gerade im Playtest benutzt. Bitte beende den Playtest, damit ich sicher weiterarbeiten kann.",
                state = playState(),
            })
        elseif args.allowInPlayMode ~= true then
            return failCode("PLAY_MODE_ACTIVE",
                "Studio is currently in " .. currentMode() .. " mode. '" .. tostring(tool)
                .. "' would change the place, but every change made during a test is thrown away when the test stops.", {
                howToFix = "Call play_stop first, do the real work, then play_start again. If you only want a throw-away change for this assistant-owned test run, repeat the call with allowInPlayMode=true.",
                state = playState(),
            })
        end
        warnings = { "allowInPlayMode was used: this change only exists during the running test and disappears when it stops." }
    end

    local okRun, result = pcall(handler, args)
    if not okRun then
        result = failCode("RUNTIME_ERROR", "Tool crashed: " .. tostring(result))
    end
    if type(result) ~= "table" then
        result = { ok = true, result = result }
    end
    -- SCHWEIGENDER FEHLER WIRD ZUM FEHLER: eine Antwort ohne ok, ohne Ergebnis
    -- und ohne Fehler ist kein gueltiges Antwort - die KI muss es merken.
    if result.ok == nil and result.error == nil then
        local isEmpty = true
        for _ in pairs(result) do isEmpty = false break end
        if isEmpty then
            result = failCode("RUNTIME_ERROR",
                "Tool '" .. tostring(tool) .. "' returned an empty answer (no result, no error). Check get_errors / get_output for what happened.")
        else
            result.ok = true
        end
    end
    if warnings then
        result.warnings = result.warnings or {}
        for _, warning in ipairs(warnings) do table.insert(result.warnings, warning) end
    end

    if not insideBatch then
        result.studio = playState()
        local pending = takeNotices()
        if #pending > 0 then
            result.notices = pending
        end
    end
    return result
end

-- ---------------------------------------------------------------------------
-- ERGEBNISSE ZURUECKSCHICKEN (grosse Daten in Stuecken)
-- ---------------------------------------------------------------------------
local function postResult(commandId, payload)
    local okEncode, json = pcall(function()
        return HttpService:JSONEncode(payload)
    end)
    if not okEncode then
        json = HttpService:JSONEncode({ ok = false, error = "Result could not be encoded: " .. tostring(json) })
    end

    if #json <= CHUNK_SIZE then
        post("/plugin/result", { sessionId = sessionId, commandId = commandId, json = json })
        return
    end

    local total = math.ceil(#json / CHUNK_SIZE)
    for index = 1, total do
        local from = (index - 1) * CHUNK_SIZE + 1
        local piece = string.sub(json, from, from + CHUNK_SIZE - 1)
        local attempt = 0
        local delivered = nil
        while attempt < 3 and delivered == nil do
            attempt = attempt + 1
            delivered = post("/plugin/result", {
                sessionId = sessionId,
                commandId = commandId,
                chunkIndex = index,
                chunkCount = total,
                chunk = piece,
                totalBytes = #json,
            })
            if delivered == nil then task.wait(0.2) end
        end
    end
end

local function handleCommand(command)
    if command == nil or command.id == nil then return end
    local startedAt = os.clock()
    local result
    local args = command.args or {}
    if args.asJob == true and command.tool ~= "start_job" then
        -- Langer Lauf: geht in den Hintergrund, der Befehl selbst antwortet sofort.
        local okJob, jobId = pcall(newJob, command.tool, function(job)
            local jobArgs = {}
            for key, value in pairs(args) do jobArgs[key] = value end
            jobArgs._job = { progress = job.progress, cancelled = job.cancelled }
            return executeTool(command.tool, jobArgs, true)
        end)
        if not okJob then
            result = failCode("RUNTIME_ERROR", "Could not start job: " .. tostring(jobId))
        else
            result = ok({
                jobId = jobId,
                status = "running",
                note = "This command runs in the background - it survives any timeout. Poll with job_status { jobId: '" .. tostring(jobId) .. "' } and fetch the result later with job_result.",
            })
        end
    else
        local okRun, r = pcall(function()
            return executeTool(command.tool, args, false)
        end)
        if not okRun then
            r = failCode("RUNTIME_ERROR", tostring(r))
        end
        result = r
    end
    if type(result) == "table" then
        result.durationSeconds = math.floor((os.clock() - startedAt) * 1000) / 1000
    end
    postResult(command.id, result)
end

-- ---------------------------------------------------------------------------
-- FIFO-DISPATCHER
-- Studio fuehrt Befehle strikt EINE NACH DER ANDEREN aus - es wird nie gegen
-- ein noch laufendes Skript gemessen. Lange Arbeit geht als Job in den
-- Hintergrund (asJob), der Dispatcher bleibt also frei.
-- ---------------------------------------------------------------------------
local commandQueue = {}
local dispatcherBusy = false

local function pumpCommandQueue()
    if dispatcherBusy then return end
    dispatcherBusy = true
    task.spawn(function()
        while #commandQueue > 0 do
            local nextCommand = table.remove(commandQueue, 1)
            local okRun, err = pcall(handleCommand, nextCommand)
            if not okRun then
                postResult(nextCommand and nextCommand.id, failCode("RUNTIME_ERROR", "Command crashed: " .. tostring(err)))
            end
        end
        dispatcherBusy = false
    end)
end

local function enqueueCommand(command)
    table.insert(commandQueue, command)
    pumpCommandQueue()
end

-- ---------------------------------------------------------------------------
-- VERBINDUNG
-- ---------------------------------------------------------------------------
local function statePayload()
    return {
        sessionId    = sessionId,
        instanceGuid = instanceGuid,
        placeName    = game.Name,
        placeId      = game.PlaceId,
        gameId       = game.GameId,
        creatorId    = game.CreatorId,
        state        = playState(),
        pluginVersion = ARENA_VERSION,
        outputCursor = outputSeq,
        errorCount   = errorCount,
    }
end

local function handshake()
    local payload = statePayload()
    payload.capabilities = capabilities
    local response = post("/plugin/hello", payload)
    if response and response.sessionId then
        sessionId = response.sessionId
        accessMode = response.accessMode or "readwrite"
        connected = true
        return true
    end
    connected = false
    return false
end

-- Zustandswaechter: merkt, wenn der BENUTZER Play startet oder stoppt,
-- UND meldet, wenn der BENUTZER selbst im Test spielt (Avatar bewegt).
task.spawn(function()
    local lastRunning = RunService:IsRunning()
    local lastMode = currentMode()
    local lastCharPos = nil
    local lastCharReport = 0
    while running do
        task.wait(0.4)
        local nowRunning = RunService:IsRunning()
        local nowMode = currentMode()
        if nowRunning ~= lastRunning or nowMode ~= lastMode then
            local byAi = (os.time() - (aiPlayIntent.at or 0)) <= 20
            local who = byAi and "assistant" or "user"
            if nowRunning then
                userPlaytestActive = not byAi
                addNotice("play_started",
                    "The " .. nowMode .. " test was started by the " .. who .. ". Studio is running now: changes to the place are temporary until it is stopped.",
                    { mode = nowMode, startedBy = who })
                task.spawn(function()
                    task.wait(0.8)
                    ensureRuntimeHelpers()
                end)
            else
                userPlaytestActive = false
                addNotice("play_stopped",
                    "The test was stopped by the " .. who .. ". Studio is back in edit mode - this is NOT a crash and nothing went wrong. Everything that happened during the test is gone; permanent edits are allowed again.",
                    { mode = nowMode, stoppedBy = who })
                cleanupRuntimeHelpers()
            end
            aiPlayIntent = { action = nil, at = 0 }
            lastRunning = nowRunning
            lastMode = nowMode
            lastCharPos = nil
        end

        -- Benutzer bewegt seinen Avatar waehrend des Playtests?
        if nowRunning and nowMode == "play" then
            local player = Players:GetPlayers()[1]
            local character = player and player.Character
            local root = character and character:FindFirstChild("HumanoidRootPart")
            if root then
                if lastCharPos then
                    local dist = (root.Position - lastCharPos).Magnitude
                    if dist > 1.5 and os.clock() - lastCharReport > 5 and os.clock() > aiMoveUntil then
                        userPlaytestActive = true
                        addNotice("user_moving_character",
                            "The USER is moving their avatar right now - this is the user playing, NOT your script. Do not hunt for movement bugs in your own code because of this.",
                            { movedStuds = math.floor(dist * 10) / 10 })
                        lastCharReport = os.clock()
                    end
                end
                lastCharPos = root.Position
            else
                lastCharPos = nil
            end
        else
            lastCharPos = nil
        end
    end
end)

-- Heartbeat: haelt die Anzeige im Programm aktuell (kleine Pakete)
task.spawn(function()
    while running do
        if sessionId ~= nil and os.clock() - lastHeartbeat > HEARTBEAT_EVERY then
            lastHeartbeat = os.clock()
            local response = post("/plugin/heartbeat", statePayload())
            if response then
                if response.unknownSession == true then
                    sessionId = nil
                elseif response.accessMode then
                    accessMode = response.accessMode
                end
            end
        end
        task.wait(1)
    end
end)

-- Long-Poll: Befehle kommen ohne Wartezeit an und erzeugen kaum Last.
task.spawn(function()
    local backoff = 0.5
    while running do
        if sessionId == nil then
            if handshake() then
                backoff = 0.5
                addNotice("connected", "Bridge connected. Place '" .. tostring(game.Name) .. "' is ready.", { placeId = game.PlaceId })
            else
                task.wait(backoff)
                backoff = math.min(backoff * 1.6, 5)
            end
        else
            local payload = statePayload()
            payload.wait = POLL_WAIT
            local response = post("/plugin/poll", payload)
            if response == nil then
                task.wait(0.5)
            elseif response.unknownSession == true then
                sessionId = nil
            else
                backoff = 0.5
                if response.accessMode then accessMode = response.accessMode end
                if response.commands ~= nil then
                    for _, command in ipairs(response.commands) do
                        enqueueCommand(command)
                    end
                elseif response.command ~= nil then
                    enqueueCommand(response.command)
                end
            end
        end
    end
end)

game:GetPropertyChangedSignal("Name"):Connect(function()
    lastHeartbeat = 0
end)

plugin.Unloading:Connect(function()
    running = false
    pcall(cleanupRuntimeHelpers)
    if sessionId then
        post("/plugin/disconnect", { sessionId = sessionId, reason = "unloading" })
    end
end)

'@
}


function Install-RobloxPlugin {
    $pluginDir = Join-Path $env:LOCALAPPDATA 'Roblox\Plugins'
    New-Item -ItemType Directory -Path $pluginDir -Force | Out-Null
    $pluginPath = Join-Path $pluginDir 'ArenaStudioBridge.lua'
    $source = (Get-PluginSource).Replace('__BASE_URL__', $script:LocalBaseUrl)
    [System.IO.File]::WriteAllText($pluginPath, $source, [System.Text.UTF8Encoding]::new($false))
    $script:PluginInstalled = Test-Path $pluginPath
    return $pluginPath
}

function Test-PortAvailable {
    param([int]$Port)
    try {
        $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Parse('127.0.0.1'), $Port)
        $listener.Start()
        $listener.Stop()
        return $true
    } catch {
        return $false
    }
}

function Test-PortListening {
    param([int]$Port)
    $client = $null
    try {
        $client = [System.Net.Sockets.TcpClient]::new()
        $client.Connect('127.0.0.1', $Port)
        return $client.Connected
    } catch {
        return $false
    } finally {
        if ($client) {
            try { $client.Close() } catch {}
        }
    }
}

# ----------------------------------------------------------------------------
# PORT AUTOMATISCH FREIGEBEN (Version 3.4, repariert in 3.5)
# Ist der lokale Port schon belegt (z.B. eine alte Bridge-Instanz, die noch
# im Hintergrund laeuft), wird der Verursacher gesucht und automatisch
# beendet. Systemkritische Prozesse werden nie angeruehrt.
#
# WICHTIG (Grund fuer den 3.5-Bugfix): Der HTTP-Server der Bridge nutzt
# http.sys - Windows zeigt dafuer im Port-Table PID 4 (System) an, NICHT den
# echten Verursacher. Und auf deutschen Windows heisst der netstat-Status
# "ABHOEREN" statt "LISTENING". Deshalb werden andere Arena-Bridge-Prozesse
# ZUSAETZLICH ueber den Prozessnamen erkannt:
#   1) EXE-Modus: andere Prozesse mit dem gleichen Namen wie dieser Prozess
#      (z.B. weitere ArenaBridge.exe)
#   2) Skript-Modus: PowerShell-Prozesse, die ArenaBridge.ps1 ausfuehren
# Das findet die Geister-Instanz auch dann, wenn der Port-Table nur
# "System" verraet.
# ----------------------------------------------------------------------------
function Get-PortOwnerPids {
    param([int]$Port)
    $owners = New-Object 'System.Collections.Generic.HashSet[int]'
    try {
        $connections = @(Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue)
        foreach ($connection in $connections) {
            if ($connection.OwningProcess) { [void]$owners.Add([int]$connection.OwningProcess) }
        }
    } catch {}
    if ($owners.Count -eq 0) {
        # Fallback ohne NetTCPIP-Modul: netstat-Ausgabe auswerten.
        # Der Status wird BEWUSST nicht gefiltert: netstat ist lokalisiert
        # (deutsch: "ABHOEREN" statt "LISTENING").
        try {
            $netstatLines = @(netstat.exe -ano -p tcp 2>$null)
            foreach ($netstatLine in $netstatLines) {
                $text = ([string]$netstatLine).Trim()
                if ($text -match ('^TCP\s+\S+:' + $Port + '\s+\S+\s+\S+\s+(\d+)$')) {
                    [void]$owners.Add([int]$matches[1])
                }
            }
        } catch {}
    }
    return @($owners)
}

function Get-BridgeGhostProcesses {
    # Findet ANDERE Arena-Bridge-Instanzen (nie den eigenen Prozess):
    #  1) Prozesse mit gleichem Namen wie dieser Prozess (EXE-Modus) -
    #     ausser der Name ist ein generischer wie powershell/pwsh.
    #  2) PowerShell-Prozesse mit ArenaBridge.ps1 in der Befehlszeile.
    $ghosts = New-Object 'System.Collections.Generic.HashSet[int]'
    try {
        $myName = (Get-Process -Id $PID -ErrorAction Stop).Name
        if ($myName -and $myName -notmatch '^(powershell|pwsh|cmd|conhost|wscript|cscript)') {
            foreach ($p in @(Get-Process -Name $myName -ErrorAction SilentlyContinue)) {
                if ($p.Id -ne $PID) { [void]$ghosts.Add([int]$p.Id) }
            }
        }
    } catch {}
    try {
        $candidates = @()
        try {
            $candidates = @(Get-CimInstance Win32_Process -Filter "Name='powershell.exe' OR Name='pwsh.exe'" -ErrorAction SilentlyContinue)
        } catch {}
        if ($candidates.Count -eq 0) {
            try { $candidates = @(Get-WmiObject Win32_Process -Filter "Name='powershell.exe' OR Name='pwsh.exe'" -ErrorAction SilentlyContinue) } catch {}
        }
        foreach ($candidate in $candidates) {
            if ([int]$candidate.ProcessId -eq $PID) { continue }
            if ([string]$candidate.CommandLine -match 'ArenaBridge\.ps1') {
                [void]$ghosts.Add([int]$candidate.ProcessId)
            }
        }
    } catch {}
    return @($ghosts)
}

function Stop-ProcessSafe {
    param([int]$TargetPid, [string]$Reason)
    if ($TargetPid -eq $PID -or $TargetPid -le 4) { return $false }
    try {
        $proc = Get-Process -Id $TargetPid -ErrorAction Stop
        $procName = [string]$proc.Name
        $protected = @('system','idle','registry','smss','csrss','wininit','winlogon','services','lsass','svchost','fontdrvhost','dwm','explorer','conhost','dllhost','sihost','taskhostw','ctfmon')
        if ($protected -contains $procName.ToLowerInvariant()) {
            Write-RuntimeLog "Free-Port: '$procName' (PID $TargetPid) ist systemkritisch und wird NICHT beendet ($Reason)."
            return $false
        }
        Write-RuntimeLog "Free-Port: Beende Prozess '$procName' (PID $TargetPid) - $Reason."
        Stop-Process -Id $TargetPid -Force -ErrorAction Stop
        return $true
    } catch {
        Write-RuntimeLog "Free-Port: Prozess $TargetPid konnte nicht beendet werden: $($_.Exception.Message)"
        return $false
    }
}

function Free-Port {
    param([int]$Port)
    Write-RuntimeLog "Free-Port: Port $Port ist belegt - Verursacher werden gesucht ..."

    # Welle 1: Port-Besitzer (ausser System) + andere Bridge-Instanzen beenden
    $ownerPids = Get-PortOwnerPids -Port $Port
    $ghostPids = Get-BridgeGhostProcesses
    foreach ($ownerPid in $ownerPids) {
        if ($ownerPid -le 4) {
            Write-RuntimeLog "Free-Port: Port $Port wird von PID $ownerPid (System/http.sys) gehalten - der echte Verursacher wird ueber den Prozessnamen gesucht."
            continue
        }
        [void](Stop-ProcessSafe -TargetPid $ownerPid -Reason "haelt Port $Port")
    }
    foreach ($ghostPid in $ghostPids) {
        [void](Stop-ProcessSafe -TargetPid $ghostPid -Reason 'andere Arena-Bridge-Instanz')
    }

    $deadline = (Get-Date).AddSeconds(8)
    while ((Get-Date) -lt $deadline) {
        if (Test-PortAvailable -Port $Port) {
            Write-RuntimeLog "Free-Port: Port $Port ist jetzt frei."
            return $true
        }
        Start-Sleep -Milliseconds 250
    }

    # Welle 2: nochmals scannen (Prozesse koennen dazwischen neu gestartet sein)
    Write-RuntimeLog "Free-Port: Port $Port immer noch belegt - zweite Runde."
    foreach ($ownerPid in (Get-PortOwnerPids -Port $Port)) {
        if ($ownerPid -gt 4) { [void](Stop-ProcessSafe -TargetPid $ownerPid -Reason "haelt Port $Port (2. Versuch)") }
    }
    foreach ($ghostPid in (Get-BridgeGhostProcesses)) {
        [void](Stop-ProcessSafe -TargetPid $ghostPid -Reason 'andere Arena-Bridge-Instanz (2. Versuch)')
    }

    $deadline2 = (Get-Date).AddSeconds(5)
    while ((Get-Date) -lt $deadline2) {
        if (Test-PortAvailable -Port $Port) {
            Write-RuntimeLog "Free-Port: Port $Port ist nach der zweiten Runde frei."
            return $true
        }
        Start-Sleep -Milliseconds 250
    }

    # Immer noch belegt: genaue Diagnose ins Protokoll schreiben
    $finalOwners = Get-PortOwnerPids -Port $Port
    foreach ($finalOwner in $finalOwners) {
        $procName = '(unbekannt)'
        try { $procName = (Get-Process -Id $finalOwner -ErrorAction Stop).Name } catch {}
        Write-RuntimeLog "Free-Port: Port $Port wird weiterhin von '$procName' (PID $finalOwner) gehalten."
    }
    if ($finalOwners.Count -eq 0) {
        Write-RuntimeLog "Free-Port: Kein Besitzer ermittelbar (moeglicherweise http.sys/System)."
    }
    return $false
}

# ----------------------------------------------------------------------------
# Hilfstyp für Screenshots (wird nur im Notfall benutzt - siehe Manifest).
# Add-Type gilt für den ganzen Prozess, also auch in den Server-Runspaces.
# ----------------------------------------------------------------------------
try {
    if (-not ('Arena.ScreenHelper' -as [type])) {
        Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
namespace Arena {
    [StructLayout(LayoutKind.Sequential)]
    public struct RECT { public int Left; public int Top; public int Right; public int Bottom; }
    public static class ScreenHelper {
        [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);
        [DllImport("user32.dll")] public static extern bool IsIconic(IntPtr hWnd);
        [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
        [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
    }
}
'@ -ErrorAction Stop
    }
} catch {
    Write-RuntimeLog "Screenshot-Hilfstyp konnte nicht geladen werden: $($_.Exception.Message)"
}

# ============================================================================
# HTTP-SERVER
# Eine Anfrage = ein Runspace aus einem Pool. Der Pool begrenzt die Last,
# auch wenn mehrere Studio-Fenster gleichzeitig verbunden sind.
# ============================================================================
$script:BridgeHandlerScript = {
    param($Context, $Shared)

    $LogFile   = $Shared.LogFile
    $MaxInline = 180000     # Bytes, die direkt in einer Antwort stehen dürfen
    $ChunkSize = 90000      # Größe eines abholbaren Teilstücks

    function Write-BridgeLog {
        param([string]$Text)
        try {
            Add-Content -LiteralPath $LogFile -Value ('{0:u} {1}' -f (Get-Date), $Text) -Encoding UTF8
        } catch {}
    }

    function To-Json($obj, [int]$Depth = 30) {
        $obj | ConvertTo-Json -Depth $Depth -Compress
    }

    function Get-UnixSeconds {
        [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    }

    # --- WICHTIG: Anfragen IMMER als UTF-8 lesen. -------------------------
    # Vorher wurde $request.ContentEncoding benutzt. Ohne "charset" im
    # Content-Type liefert das unter Windows ANSI (CP1252) - genau dadurch
    # wurde aus "BöseElla" ein "BÃ¶seElla".
    function Read-Body($request) {
        $memory = New-Object System.IO.MemoryStream
        try {
            $request.InputStream.CopyTo($memory)
            $bytes = $memory.ToArray()
        } finally {
            $memory.Dispose()
        }
        if ($bytes.Length -eq 0) { return $null }
        $text = [System.Text.Encoding]::UTF8.GetString($bytes)
        $text = $text.TrimStart([char]0xFEFF)
        if ([string]::IsNullOrWhiteSpace($text)) { return $null }
        try {
            return $text | ConvertFrom-Json
        } catch {
            return $null
        }
    }

    function Send-RawJson($context, [int]$status, [string]$json) {
        $response = $context.Response
        $response.StatusCode = $status
        $response.ContentType = 'application/json; charset=utf-8'
        $response.Headers['Access-Control-Allow-Origin'] = '*'
        $response.Headers['Access-Control-Allow-Headers'] = 'content-type, authorization, x-arena-token'
        $response.Headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        $response.Headers['Cache-Control'] = 'no-store'
        $buffer = [System.Text.Encoding]::UTF8.GetBytes($json)
        $response.ContentLength64 = $buffer.Length
        $response.OutputStream.Write($buffer, 0, $buffer.Length)
        $response.OutputStream.Close()
    }

    function Send-Json($context, [int]$status, $obj) {
        Send-RawJson $context $status (To-Json $obj 40)
    }

    # Hängt Zusatzinformationen an eine fertige JSON-Antwort an, ohne sie
    # neu zu serialisieren (kein Datenverlust bei großen Ergebnissen).
    function Merge-Envelope([string]$json, $envelope) {
        $envJson = To-Json $envelope 20
        $trimmed = $json.TrimStart()
        if ($trimmed.StartsWith('{')) {
            $rest = $trimmed.Substring(1)
            if ($rest.TrimStart().StartsWith('}')) {
                return '{"_bridge":' + $envJson + $rest
            }
            return '{"_bridge":' + $envJson + ',' + $rest
        }
        return '{"_bridge":' + $envJson + ',"ok":true,"result":' + $json + '}'
    }

    # Hängt ein fertiges JSON-Objekt unter einem Namen in eine JSON-Antwort
    # ein, ohne sie neu zu serialisieren (für die Start-Doku).
    function Merge-ExtraJson([string]$json, [string]$key, [string]$valueJson) {
        if ([string]::IsNullOrWhiteSpace($valueJson)) { return $json }
        $extra = '"' + $key + '":' + $valueJson
        $trimmed = $json.TrimStart()
        if ($trimmed.StartsWith('{')) {
            $rest = $trimmed.Substring(1)
            if ($rest.TrimStart().StartsWith('}')) {
                return '{' + $extra + $rest
            }
            return '{' + $extra + ',' + $rest
        }
        return $json
    }

    function Get-Token($request, $body) {
        $auth = $request.Headers['Authorization']
        if ($auth -and $auth -match '^Bearer\s+(.+)$') {
            return $matches[1].Trim()
        }
        $header = $request.Headers['X-Arena-Token']
        if ($header) { return $header.Trim() }
        if ($body -and ($body.PSObject.Properties.Name -contains 'token')) { return [string]$body.token }
        $queryToken = $request.QueryString['token']
        if ($queryToken) { return $queryToken }
        return $null
    }

    function Get-SessionForToken($token) {
        if (-not $token) { return $null }
        $sessionId = $null
        if ($Shared.TokenSessions.TryGetValue($token, [ref]$sessionId)) {
            return $sessionId
        }
        return $null
    }

    function Ensure-Queue($sessionId) {
        $queue = $null
        if (-not $Shared.CommandQueues.TryGetValue($sessionId, [ref]$queue)) {
            $queue = [System.Collections.Concurrent.ConcurrentQueue[string]]::new()
            [void]$Shared.CommandQueues.TryAdd($sessionId, $queue)
            [void]$Shared.CommandQueues.TryGetValue($sessionId, [ref]$queue)
        }
        return , $queue
    }

    function Ensure-Signal($sessionId) {
        $signal = $null
        if (-not $Shared.CommandSignals.TryGetValue($sessionId, [ref]$signal)) {
            $signal = New-Object System.Threading.ManualResetEventSlim($false)
            [void]$Shared.CommandSignals.TryAdd($sessionId, $signal)
            [void]$Shared.CommandSignals.TryGetValue($sessionId, [ref]$signal)
        }
        return $signal
    }

    function Ensure-EventQueue($sessionId) {
        $queue = $null
        if (-not $Shared.Events.TryGetValue($sessionId, [ref]$queue)) {
            $queue = [System.Collections.Concurrent.ConcurrentQueue[string]]::new()
            [void]$Shared.Events.TryAdd($sessionId, $queue)
            [void]$Shared.Events.TryGetValue($sessionId, [ref]$queue)
        }
        return , $queue
    }

    function Add-BridgeEvent($sessionId, $kind, $message, $data) {
        $queue = Ensure-EventQueue $sessionId
        $event = @{
            kind    = $kind
            message = $message
            time    = (Get-Date).ToString('u')
            data    = $data
        }
        $queue.Enqueue((To-Json $event 12))
        # Nur die letzten 60 Ereignisse behalten
        while ($queue.Count -gt 60) {
            $dropped = $null
            [void]$queue.TryDequeue([ref]$dropped)
        }
        Write-BridgeLog "Ereignis [$kind] $message"
    }

    function Take-Events($sessionId, [int]$max = 12) {
        $queue = Ensure-EventQueue $sessionId
        $items = New-Object System.Collections.Generic.List[object]
        $itemJson = $null
        while ($items.Count -lt $max -and $queue.TryDequeue([ref]$itemJson)) {
            try { $items.Add(($itemJson | ConvertFrom-Json)) } catch {}
        }
        return , $items
    }

    # ------------------------------------------------------------------
    # LAUFENDE BEFEHLE: Ein Timeout tötet keinen Befehl im Studio.
    # Der Befehl läuft zu Ende, das Ergebnis kommt später an. Diese
    # Funktionen merken pro Sitzung, was gerade in Studio läuft, und
    # liefern späte Ergebnisse wieder aus (im _bridge-Envelope).
    # ------------------------------------------------------------------
    function Ensure-PendingBag($sessionId) {
        $bag = $null
        if (-not $Shared.PendingCommands.TryGetValue([string]$sessionId, [ref]$bag)) {
            $bag = [System.Collections.Concurrent.ConcurrentDictionary[string,string]]::new()
            [void]$Shared.PendingCommands.TryAdd([string]$sessionId, $bag)
            [void]$Shared.PendingCommands.TryGetValue([string]$sessionId, [ref]$bag)
        }
        return , $bag
    }

    function Add-PendingCommand($sessionId, $commandId, $tool) {
        $bag = Ensure-PendingBag $sessionId
        $bag[[string]$commandId] = (To-Json @{ tool = [string]$tool; startedAt = (Get-Date).ToString('u') } 5)
    }

    function Remove-PendingCommand($sessionId, $commandId) {
        $bag = Ensure-PendingBag $sessionId
        $null = $bag.TryRemove([string]$commandId, [ref]$null)
    }

    function Get-PendingCommands($sessionId) {
        $bag = Ensure-PendingBag $sessionId
        $now = [DateTime]::UtcNow
        $items = New-Object System.Collections.Generic.List[object]
        foreach ($pair in $bag.GetEnumerator()) {
            try {
                $info = $pair.Value | ConvertFrom-Json
                $started = [DateTime]::Parse([string]$info.startedAt)
                $ageSeconds = [int]($now - $started).TotalSeconds
                # Nach 15 Minuten gilt ein "laufender" Befehl als erledigt
                # (Studio war weg oder hat ohne Ergebnis neu gestartet).
                if ($ageSeconds -gt 900) {
                    $null = $bag.TryRemove([string]$pair.Key, [ref]$null)
                    continue
                }
                $items.Add(@{
                    commandId = [string]$pair.Key
                    tool      = [string]$info.tool
                    seconds   = $ageSeconds
                })
            } catch {}
        }
        return , $items
    }

    # Ergebnisse, die nach einem Timeout erst jetzt eingetroffen sind.
    function Take-LateResults($sessionId) {
        $items = New-Object System.Collections.Generic.List[object]
        foreach ($pending in (Get-PendingCommands $sessionId)) {
            $json = $null
            if ($Shared.CommandResults.TryRemove([string]$pending.commandId, [ref]$json)) {
                Remove-PendingCommand $sessionId $pending.commandId
                try {
                    $parsed = $json | ConvertFrom-Json
                    $items.Add(@{ tool = $pending.tool; commandId = $pending.commandId; seconds = $pending.seconds; result = $parsed })
                } catch {
                    $items.Add(@{ tool = $pending.tool; commandId = $pending.commandId; seconds = $pending.seconds; rawResult = $json })
                }
            }
        }
        return , $items
    }

    function Get-SessionEntry($sessionId) {
        $json = $null
        if ($Shared.Sessions.TryGetValue($sessionId, [ref]$json)) {
            try { return $json | ConvertFrom-Json } catch { return $null }
        }
        return $null
    }

    function Save-SessionEntry($entry) {
        $Shared.Sessions[[string]$entry.sessionId] = (To-Json $entry 12)
    }

    function New-BridgeToken {
        $bytes = New-Object byte[] 24
        [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
        [Convert]::ToBase64String($bytes).TrimEnd('=').Replace('+', '-').Replace('/', '_')
    }

    function Get-StateObject($body) {
        $state = @{ running = $false; mode = 'edit'; context = 'edit' }
        if ($body -and $body.state) {
            $state = @{
                running = [bool]$body.state.running
                mode    = [string]$body.state.mode
                context = [string]$body.state.context
                players = $body.state.playerCount
                userPlaytestActive = [bool]$body.state.userPlaytestActive
            }
        }
        return $state
    }

    # ------------------------------------------------------------------
    # ANMELDUNG EINES STUDIO-FENSTERS
    # Jedes Fenster ist eine eigene Sitzung mit eigenem Token.
    # Startet Studio den Testmodus neu, meldet sich dasselbe Fenster mit
    # einer neuen instanceGuid - dann wird die alte, verwaiste Sitzung
    # wiederverwendet, damit der Token der KI gültig bleibt.
    # ------------------------------------------------------------------
    function Register-Session($body) {
        if (-not $body) { return $null }
        $guid    = [string]$body.instanceGuid
        $placeId = [string]$body.placeId
        $placeName = [string]$body.placeName
        $now = Get-UnixSeconds

        $reusable = $null
        $reuseReason = $null
        foreach ($pair in $Shared.Sessions.GetEnumerator()) {
            $entry = $null
            try { $entry = $pair.Value | ConvertFrom-Json } catch { $entry = $null }
            if (-not $entry) { continue }
            if ([string]$entry.instanceGuid -eq $guid -and $guid -ne '') {
                $reusable = $entry
                $reuseReason = 'same-instance'
                break
            }
        }

        if (-not $reusable) {
            $best = $null
            foreach ($pair in $Shared.Sessions.GetEnumerator()) {
                $entry = $null
                try { $entry = $pair.Value | ConvertFrom-Json } catch { $entry = $null }
                if (-not $entry) { continue }
                $age = $now - [int64]$entry.lastSeen
                $samePlace = ([string]$entry.placeId -eq $placeId)
                if ($placeId -eq '0' -or [string]::IsNullOrWhiteSpace($placeId)) {
                    $samePlace = $samePlace -and ([string]$entry.placeName -eq $placeName)
                }
                # Wann darf eine alte Sitzung samt Token weiterbenutzt werden?
                #   a) Das Plugin hat sich sauber abgemeldet (Testmodus, Neuladen,
                #      Studio geschlossen)  ->  sofort.
                #   b) Kein offener Long-Poll und seit 10 Sekunden nichts gehört
                #      (Absturz)  ->  ebenfalls.
                # Ein zweites, LEBENDES Fenster desselben Place wird dadurch
                # niemals übernommen - es behält seinen eigenen Token.
                $openPolls = 0
                [void]$Shared.Pollers.TryGetValue([string]$entry.sessionId, [ref]$openPolls)
                $isOrphan = ($entry.orphan -eq $true)
                $looksDead = ($openPolls -le 0 -and $age -ge 10)
                if ($samePlace -and ($isOrphan -or $looksDead) -and $age -le 900) {
                    if (-not $best -or [int64]$entry.lastSeen -gt [int64]$best.lastSeen) { $best = $entry }
                }
            }
            if ($best) {
                $reusable = $best
                $reuseReason = 'reconnect'
            }
        }

        if ($reusable) {
            $sessionId = [string]$reusable.sessionId
            $token = $null
            if (-not $Shared.SessionTokens.TryGetValue($sessionId, [ref]$token)) {
                $token = New-BridgeToken
                $Shared.SessionTokens[$sessionId] = $token
                $Shared.TokenSessions[$token] = $sessionId
            }
            $mode = $null
            if (-not $Shared.AccessModes.TryGetValue($sessionId, [ref]$mode)) {
                $mode = 'readwrite'
                $Shared.AccessModes[$sessionId] = $mode
            }
            $entry = @{
                sessionId     = $sessionId
                instanceGuid  = $guid
                placeName     = $placeName
                placeId       = $placeId
                gameId        = [string]$body.gameId
                token         = $token
                accessMode    = $mode
                lastSeen      = $now
                connectedAt   = $reusable.connectedAt
                state         = (Get-StateObject $body)
                pluginVersion = [string]$body.pluginVersion
                capabilities  = $body.capabilities
                reconnects    = ([int]$reusable.reconnects + 1)
                orphan        = $false
            }
            Save-SessionEntry $entry
            $Shared.Presence[$sessionId] = $now
            if ($reuseReason -eq 'reconnect') {
                Add-BridgeEvent $sessionId 'studio_reconnected' 'The Studio plugin reconnected (this happens when a playtest starts or stops, or when Studio reloads plugins). Nothing crashed and your token stays valid.' @{ placeName = $placeName }
            }
            return $entry
        }

        $sessionId = [guid]::NewGuid().ToString('N')
        $token = New-BridgeToken
        $Shared.SessionTokens[$sessionId] = $token
        $Shared.TokenSessions[$token] = $sessionId
        $Shared.AccessModes[$sessionId] = 'readwrite'
        $entry = @{
            sessionId     = $sessionId
            instanceGuid  = $guid
            placeName     = $placeName
            placeId       = $placeId
            gameId        = [string]$body.gameId
            token         = $token
            accessMode    = 'readwrite'
            lastSeen      = $now
            connectedAt   = $now
            state         = (Get-StateObject $body)
            pluginVersion = [string]$body.pluginVersion
            capabilities  = $body.capabilities
            reconnects    = 0
            orphan        = $false
        }
        Save-SessionEntry $entry
        $Shared.Presence[$sessionId] = $now
        [void](Ensure-Queue $sessionId)
        [void](Ensure-Signal $sessionId)
        Add-BridgeEvent $sessionId 'connected' "Place '$placeName' is connected." @{ placeId = $placeId }
        Write-BridgeLog "Neue Sitzung $sessionId fuer Place '$placeName' (placeId $placeId)."
        return $entry
    }

    # Aktualisiert eine bestehende Sitzung (Heartbeat / Poll).
    function Update-Session($body) {
        if (-not $body) { return $null }
        $sessionId = [string]$body.sessionId
        if ([string]::IsNullOrWhiteSpace($sessionId)) { return $null }
        $entry = Get-SessionEntry $sessionId
        if (-not $entry) { return $null }

        $now = Get-UnixSeconds
        $mode = $null
        if (-not $Shared.AccessModes.TryGetValue($sessionId, [ref]$mode)) {
            $mode = 'readwrite'
            $Shared.AccessModes[$sessionId] = $mode
        }
        $token = $null
        if (-not $Shared.SessionTokens.TryGetValue($sessionId, [ref]$token)) {
            $token = New-BridgeToken
            $Shared.SessionTokens[$sessionId] = $token
            $Shared.TokenSessions[$token] = $sessionId
        }

        $oldState = $entry.state
        $newState = Get-StateObject $body
        $newName = [string]$body.placeName
        if ([string]::IsNullOrWhiteSpace($newName)) { $newName = [string]$entry.placeName }

        $updated = @{
            sessionId     = $sessionId
            instanceGuid  = [string]$entry.instanceGuid
            placeName     = $newName
            placeId       = [string]$body.placeId
            gameId        = [string]$body.gameId
            token         = $token
            accessMode    = $mode
            lastSeen      = $now
            connectedAt   = $entry.connectedAt
            state         = $newState
            pluginVersion = [string]$entry.pluginVersion
            capabilities  = $entry.capabilities
            reconnects    = $entry.reconnects
            orphan        = $false
        }
        Save-SessionEntry $updated
        $Shared.Presence[$sessionId] = $now

        if ($oldState -and ([bool]$oldState.running -ne [bool]$newState.running)) {
            if ($newState.running) {
                Add-BridgeEvent $sessionId 'play_started' "Studio switched into $($newState.mode) mode." $newState
            } else {
                Add-BridgeEvent $sessionId 'play_stopped' 'Studio returned to edit mode.' $newState
            }
        }
        return $updated
    }


    # ------------------------------------------------------------------
    # GROSSE ANTWORTEN: als Blob ablegen und in Stücken herausgeben
    # ------------------------------------------------------------------
    function New-Blob([string]$json, [string]$tool) {
        $blobId = 'blob_' + [guid]::NewGuid().ToString('N').Substring(0, 12)
        $Shared.Blobs[$blobId] = $json
        $chunkCount = [Math]::Ceiling($json.Length / [double]$ChunkSize)
        $info = @{
            blobId     = $blobId
            tool       = $tool
            totalChars = $json.Length
            chunkSize  = $ChunkSize
            chunkCount = [int]$chunkCount
            created    = (Get-Date).ToString('u')
        }
        $Shared.BlobInfo[$blobId] = (To-Json $info 8)
        # Alte Blobs (älter als 30 Minuten) aufräumen
        foreach ($pair in $Shared.BlobInfo.GetEnumerator()) {
            try {
                $old = $pair.Value | ConvertFrom-Json
                if (((Get-Date) - [DateTime]::Parse($old.created)).TotalMinutes -gt 30) {
                    $removed = $null
                    [void]$Shared.Blobs.TryRemove($pair.Key, [ref]$removed)
                    [void]$Shared.BlobInfo.TryRemove($pair.Key, [ref]$removed)
                }
            } catch {}
        }
        return $info
    }

    function Get-BlobChunk([string]$blobId, [int]$index) {
        $json = $null
        if (-not $Shared.Blobs.TryGetValue($blobId, [ref]$json)) {
            return @{ ok = $false; error = "Unknown or expired blobId '$blobId'. Blobs live for 30 minutes - run the tool again." }
        }
        $infoJson = $null
        [void]$Shared.BlobInfo.TryGetValue($blobId, [ref]$infoJson)
        $info = $null
        if ($infoJson) { $info = $infoJson | ConvertFrom-Json }
        $chunkCount = [int][Math]::Ceiling($json.Length / [double]$ChunkSize)
        if ($index -lt 1) { $index = 1 }
        if ($index -gt $chunkCount) {
            return @{ ok = $false; error = "Chunk $index does not exist (chunkCount = $chunkCount)." }
        }
        $start = ($index - 1) * $ChunkSize
        $length = [Math]::Min($ChunkSize, $json.Length - $start)
        return @{
            ok         = $true
            blobId     = $blobId
            index      = $index
            chunkCount = $chunkCount
            totalChars = $json.Length
            isLast     = ($index -eq $chunkCount)
            data       = $json.Substring($start, $length)
            note       = 'Concatenate data of all chunks in order, then parse the result as JSON. Nothing is truncated.'
        }
    }

    # ------------------------------------------------------------------
    # ASSET-CACHE (lokale Datei): Suchergebnisse und Asset-Details werden
    # nicht jede Session neu von Roblox geladen, sondern aus dem Cache
    # bedient (Suche 7 Tage, Details 30 Tage). refresh=true erzwingt Neu.
    # ------------------------------------------------------------------
    function Read-AssetCache {
        try {
            $path = [string]$Shared.AssetCachePath
            if (Test-Path -LiteralPath $path) {
                $raw = Get-Content -LiteralPath $path -Raw
                if ($raw) { return ($raw | ConvertFrom-Json) }
            }
        } catch {
            Write-BridgeLog "Asset-Cache lesen fehlgeschlagen: $($_.Exception.Message)"
        }
        return $null
    }

    function Save-AssetCache($cache) {
        try {
            $path = [string]$Shared.AssetCachePath
            $json = $cache | ConvertTo-Json -Depth 14 -Compress
            [System.IO.File]::WriteAllText($path, $json, (New-Object System.Text.UTF8Encoding($false)))
        } catch {
            Write-BridgeLog "Asset-Cache speichern fehlgeschlagen: $($_.Exception.Message)"
        }
    }

    function Get-CacheEntry($cache, [string]$key, [double]$maxAgeDays) {
        if ($null -eq $cache) { return $null }
        if (-not $cache.PSObject.Properties.Name -contains $key) { return $null }
        try {
            $cached = $cache.PSObject.Properties[$key].Value
            $age = (Get-Date) - [DateTime]::Parse([string]$cached.fetchedAt)
            if ($age.TotalDays -lt $maxAgeDays) { return $cached.result }
        } catch {}
        return $null
    }

    function Add-CacheEntry([string]$key, $value) {
        $cache = Read-AssetCache
        if ($null -eq $cache) { $cache = @{} }
        $cache | Add-Member -NotePropertyName $key -NotePropertyValue (@{
            fetchedAt = (Get-Date).ToUniversalTime().ToString('o')
            result    = $value
        }) -Force
        Save-AssetCache $cache
    }

    # typeId -> wofuer man es verwenden kann (fuer die Tyvalidierung)
    function Get-AssetTypeUsage([int]$typeId) {
        switch ($typeId) {
            1  { return @{ typeName = 'Image';     usableAs = 'Texture / Image / Decal-Texture'; properties = @('Texture', 'Image') } }
            3  { return @{ typeName = 'Audio';     usableAs = 'Sound';                          properties = @('SoundId') } }
            4  { return @{ typeName = 'Mesh';      usableAs = 'SpecialMesh (MeshId)';           properties = @('MeshId') } }
            10 { return @{ typeName = 'Model';     usableAs = 'insert_asset (Model)';           properties = @() } }
            13 { return @{ typeName = 'Decal';     usableAs = 'Decal / Texture / Image';        properties = @('Texture', 'Image') } }
            24 { return @{ typeName = 'Animation'; usableAs = 'Animation';                      properties = @('AnimationId') } }
            40 { return @{ typeName = 'MeshPart';  usableAs = 'insert_asset (MeshPart)';        properties = @() } }
            62 { return @{ typeName = 'Video';     usableAs = 'VideoFrame';                     properties = @('VideoId') } }
            default { return @{ typeName = ('Unknown(' + [string]$typeId + ')'); usableAs = ''; properties = @() } }
        }
    }

    function Invoke-AssetSearch($toolArgs) {
        # TYP-NORMALISIERUNG: Die Roblox-Marketplace-API kennt NICHT 'image'
        # und NICHT 'mesh' - genau deshalb liefen Texturen/Meshes vorher ins
        # Leere. Jetzt wird auf das gemappt, was wirklich da ist.
        $type = ([string]$toolArgs.type).ToLowerInvariant()
        if ([string]::IsNullOrWhiteSpace($type)) { $type = 'audio' }
        $typeMap = @{
            'audio'     = 'audio'
            'sound'     = 'audio'
            'music'     = 'music'
            'model'     = 'model'
            'decal'     = 'decal'
            'video'     = 'video'
            'animation' = 'animation'
            'image'     = 'decal'
            'texture'   = 'decal'
            'mesh'      = 'meshpart'
            'meshpart'  = 'meshpart'
        }
        if (-not $typeMap.ContainsKey($type)) {
            return @{
                ok = $false
                code = 'CATALOG_TYPE_NOT_SUPPORTED'
                error = "Asset type '$type' cannot be searched in the catalog."
                supportedTypes = @('audio', 'music', 'decal', 'image', 'texture', 'mesh', 'model', 'video', 'animation')
            }
        }
        $apiType = $typeMap[$type]
        $typeNote = $null
        if ($apiType -ne $type) {
            if ($apiType -eq 'decal') {
                $typeNote = "The catalog API has no '$type' search - I searched DECALS instead. Decal assets are textures: use them on 'Texture' (Part/Decal) or 'Image' (ImageLabel/ImageButton)."
            } else {
                $typeNote = "The catalog API has no '$type' search - I searched MESHPARTS instead (meshes with texture, insert with insert_asset). For a bare mesh use insert_asset too."
            }
        }
        if (($type -eq 'model') -and ($toolArgs.allowModels -ne $true)) {
            return @{
                ok = $false
                code = 'ASSET_BLOCKED'
                error = 'Searching for free MODELS is disabled on purpose.'
                why = 'Free models and free systems from the toolbox often contain hidden scripts, broken parts or huge unoptimised meshes. Build the object yourself with create_instance / clone_instance / unions - that stays clean and you can edit every part.'
                allowedTypes = @('decal', 'image', 'audio', 'mesh', 'meshpart', 'video', 'animation')
                override = 'If the user explicitly asked for a toolbox model, repeat the call with allowModels=true. The bridge blocks the insert while it contains scripts (ASSET_HAS_SCRIPTS) - pass acceptScripts=true to override and inspect the content immediately afterwards.'
            }
        }

        $keyword = [string]$toolArgs.query
        if ([string]::IsNullOrWhiteSpace($keyword)) { $keyword = [string]$toolArgs.keyword }
        $limit = 20
        if ($toolArgs.limit) { $limit = [Math]::Min([int]$toolArgs.limit, 50) }
        $page = 0
        if ($toolArgs.page) { $page = [int]$toolArgs.page }
        $sortType = 0
        if ($toolArgs.sortType) { $sortType = [int]$toolArgs.sortType }
        $sortNames = @{ 0 = 'relevance'; 1 = 'favorited'; 3 = 'updated'; 4 = 'priceAsc'; 5 = 'priceDesc' }

        # ---------------- Cache (7 Tage) ----------------
        $cacheKey = "search|${apiType}|${keyword}|${page}|${sortType}"
        if ($toolArgs.refresh -ne $true) {
            $cached = Get-CacheEntry (Read-AssetCache) $cacheKey 7
            if ($null -ne $cached) {
                return @{
                    ok = $true
                    catalogAvailable = $true
                    cached = $true
                    cachedNote = 'Served from the local cache (fetched earlier - not reloaded from the catalog). Pass refresh=true to force a new catalog query.'
                    result = $cached
                }
            }
        }

        $searchUrl = 'https://apis.roblox.com/toolbox-service/v1/marketplace/' + $apiType +
            '?keyword=' + [uri]::EscapeDataString($keyword) +
            '&limit=' + $limit + '&pageNumber=' + $page + '&sortType=' + $sortType

        $searchResult = $null
        $lastError = $null
        for ($attempt = 1; $attempt -le 2; $attempt++) {
            try {
                $searchResult = Invoke-RestMethod -Uri $searchUrl -Method Get -TimeoutSec 20 -UseBasicParsing
                break
            } catch {
                $lastError = $_.Exception.Message
                Start-Sleep -Milliseconds 1500
            }
        }
        if ($null -eq $searchResult) {
            return @{
                ok = $false
                code = 'CATALOG_UNAVAILABLE'
                catalogAvailable = $false
                error = "The Roblox catalog is NOT available right now ($lastError)."
                protocol = 'Say this clearly to the user right away: "Katalog nicht verfuegbar". Then continue PROCEDURALLY: textures = colored parts / SurfaceGui / decal-less design, sounds = a short procedural beep in a script (or skip), models = build them with create_instance / clone_instance / unions. Do NOT guess asset ids and do NOT stay silent.'
                checkAgain = 'Call the catalog_status tool whenever you want to know if the catalog is back.'
            }
        }

        $ids = @()
        foreach ($item in @($searchResult.data)) {
            if ($item.id) { $ids += [string]$item.id }
        }

        $assets = @()
        $detailsFailed = $false
        if ($ids.Count -gt 0) {
            try {
                $detailUrl = 'https://apis.roblox.com/toolbox-service/v1/items/details?assetIds=' + ($ids -join ',')
                $details = Invoke-RestMethod -Uri $detailUrl -Method Get -TimeoutSec 20 -UseBasicParsing
                $freshDetails = @{}
                foreach ($entry in @($details.data)) {
                    $asset = $entry.asset
                    $creator = $entry.creator
                    $item = @{
                        assetId     = $asset.id
                        name        = $asset.name
                        typeId      = $asset.typeId
                        typeName    = (Get-AssetTypeUsage ([int]$asset.typeId)).typeName
                        description = $asset.description
                        duration    = $asset.duration
                        created     = $asset.createdUtc
                        updated     = $asset.updatedUtc
                        endorsed    = $asset.isEndorsed
                        hasScripts  = $asset.hasScripts
                        creator     = $creator.name
                        creatorVerified = $creator.isVerifiedCreator
                        useAs       = 'rbxassetid://' + [string]$asset.id
                    }
                    if ($asset.audioDetails) {
                        $item.audioType = $asset.audioDetails.audioType
                        $item.artist = $asset.audioDetails.artist
                    }
                    $assets += $item
                    $freshDetails[[string]$asset.id] = $entry
                }
                # Details in EINEM Zug cachen (eine Datei, kein Schreibsturm)
                $cache = Read-AssetCache
                if ($null -eq $cache) { $cache = @{} }
                foreach ($key in $freshDetails.Keys) {
                    $cache | Add-Member -NotePropertyName ('detail|' + $key) -NotePropertyValue (@{
                        fetchedAt = (Get-Date).ToUniversalTime().ToString('o')
                        result    = $freshDetails[$key]
                    }) -Force
                }
                Save-AssetCache $cache
            } catch {
                $detailsFailed = $true
                foreach ($id in $ids) {
                    $assets += @{ assetId = $id; useAs = 'rbxassetid://' + $id; note = 'Details could not be loaded - verify with validate_asset before applying.' }
                }
            }
        }

        $note = 'Apply an asset with apply_asset (sets Texture/SoundId/Image/MeshId automatically and validates the type BEFORE applying) or set the property to the useAs value. Meshes/MeshParts/Models need insert_asset.'
        if ($type -eq 'model') {
            $note = 'WARNING: this is a toolbox model. The bridge refuses inserting while it contains scripts (ASSET_HAS_SCRIPTS). If you override, inspect the content immediately (search for Script/LocalScript inside it).'
        }
        $resultObject = @{
            assets      = $assets
            count       = $assets.Count
            type        = $type
            apiType     = $apiType
            keyword     = $keyword
            page        = $page
            sortType    = $sortType
            sortName    = $sortNames[[int]$sortType]
            totalResults = if ($searchResult.totalResults) { [int]$searchResult.totalResults } else { $null }
            typeNote    = $typeNote
            note        = $note
        }
        if ($detailsFailed) {
            $resultObject.detailsWarning = 'The detail lookup failed, so names/types above are incomplete. Verify ids with validate_asset before applying them.'
        }
        if ($ids.Count -eq 0) {
            $resultObject.note = "No results for '$keyword'. Try a shorter or more common (English) keyword, or another sort type (sortType 3 = recently updated)."
        }

        Add-CacheEntry $cacheKey $resultObject
        return @{
            ok = $true
            catalogAvailable = $true
            cached = $false
            result = $resultObject
        }
    }

    function Invoke-AssetDetails($toolArgs) {
        $ids = @()
        foreach ($id in @($toolArgs.assetIds)) { if ($id) { $ids += [string]$id } }
        if ($toolArgs.assetId) { $ids += [string]$toolArgs.assetId }
        if ($ids.Count -eq 0) { return @{ ok = $false; code = 'REF_NOT_FOUND'; error = 'assetIds missing.' } }
        $uniqueIds = @($ids | Select-Object -Unique)
        $results = @()
        $missing = @()
        foreach ($id in $uniqueIds) {
            $cached = Get-CacheEntry (Read-AssetCache) ('detail|' + $id) 30
            if ($null -ne $cached) {
                $results += $cached
            } else {
                $missing += $id
            }
        }
        if ($missing.Count -gt 0) {
            try {
                $detailUrl = 'https://apis.roblox.com/toolbox-service/v1/items/details?assetIds=' + ($missing -join ',')
                $details = Invoke-RestMethod -Uri $detailUrl -Method Get -TimeoutSec 20 -UseBasicParsing
                foreach ($entry in @($details.data)) {
                    $results += $entry
                    Add-CacheEntry ('detail|' + [string]$entry.asset.id) $entry
                }
            } catch {
                if ($_.Exception.Message -match '404') {
                    # Batch fehlgeschlagen, weil MINDESTENS eine Id unbekannt ist:
                    # einzeln nachfragen und klar melden, welche.
                    $unknown = @()
                    foreach ($id in $missing) {
                        try {
                            $single = Invoke-RestMethod -Uri ('https://apis.roblox.com/toolbox-service/v1/items/details?assetIds=' + $id) -Method Get -TimeoutSec 20 -UseBasicParsing
                            $results += @($single.data)
                            Add-CacheEntry ('detail|' + $id) (@($single.data))[0]
                        } catch {
                            $unknown += $id
                        }
                    }
                    $unknownNote = @()
                    foreach ($id in $unknown) {
                        $unknownNote += "Asset $id does NOT exist or is not public (404) - do not use it."
                    }
                    return @{
                        ok = $true
                        catalogAvailable = $true
                        result = @{ assets = $results; unknownAssets = $unknown }
                        warnings = $unknownNote
                    }
                }
                return @{
                    ok = $false
                    code = 'CATALOG_UNAVAILABLE'
                    catalogAvailable = $false
                    error = "Details could not be loaded: $($_.Exception.Message)"
                    protocol = 'The catalog is not reachable right now. Say so clearly to the user and do not guess asset ids - build procedurally or retry later (catalog_status).'
                }
            }
        }
        return @{ ok = $true; catalogAvailable = $true; result = @{ assets = $results } }
    }

    # ------------------------------------------------------------------
    # ASSET-TYpVALIDIERUNG: passt die Id wirklich zum Typ, BEVOR eingebaut?
    # ------------------------------------------------------------------
    function Invoke-AssetValidation($toolArgs) {
        $id = $null
        if ($toolArgs.assetId) { $id = [string]$toolArgs.assetId }
        if ([string]::IsNullOrWhiteSpace($id) -and $toolArgs.assetIds -and @($toolArgs.assetIds).Count -ge 1) {
            $id = [string](@($toolArgs.assetIds))[0]
        }
        if ([string]::IsNullOrWhiteSpace($id)) { return @{ ok = $false; code = 'REF_NOT_FOUND'; error = 'assetId missing.' } }
        $expect = ([string]$toolArgs.expectType).ToLowerInvariant()

        $entry = Get-CacheEntry (Read-AssetCache) ('detail|' + $id) 30
        if ($null -eq $entry) {
            try {
                $detailUrl = 'https://apis.roblox.com/toolbox-service/v1/items/details?assetIds=' + $id
                $details = Invoke-RestMethod -Uri $detailUrl -Method Get -TimeoutSec 20 -UseBasicParsing
                $entry = @($details.data)[0]
                Add-CacheEntry ('detail|' + $id) $entry
            } catch {
                if ($_.Exception.Message -match '404') {
                    return @{
                        ok = $false
                        code = 'ASSET_NOT_FOUND'
                        verified = $false
                        assetId = $id
                        error = "Asset $id does not exist or is not public (catalog answered 404). This id MUST NOT be used - it would fail at runtime."
                    }
                }
                return @{
                    ok = $true
                    verified = $false
                    assetId = $id
                    code = 'CATALOG_UNAVAILABLE'
                    catalogAvailable = $false
                    note = 'Could not verify the asset because the catalog is not reachable. Applying is still allowed, but it may fail at runtime - prefer verified ids or build procedurally.'
                }
            }
        }
        if ($null -eq $entry) {
            return @{ ok = $false; code = 'ASSET_NOT_FOUND'; verified = $false; assetId = $id; error = "Asset $id was not found in the catalog. This id MUST NOT be used." }
        }
        $asset = $entry.asset
        $typeId = [int]$asset.typeId
        $usage = Get-AssetTypeUsage $typeId
        $matchesExpect = $null
        if ($expect -ne '') {
            $expectedIds = @()
            switch ($expect) {
                'audio'     { $expectedIds = @(3) }
                'music'     { $expectedIds = @(3) }
                'sound'     { $expectedIds = @(3) }
                'image'     { $expectedIds = @(1, 13) }
                'texture'   { $expectedIds = @(1, 13) }
                'decal'     { $expectedIds = @(13, 1) }
                'mesh'      { $expectedIds = @(4, 40) }
                'model'     { $expectedIds = @(10, 4, 40) }
                'animation' { $expectedIds = @(24) }
                'video'     { $expectedIds = @(62) }
                default     { $expectedIds = @() }
            }
            $matchesExpect = ($expectedIds -contains $typeId)
        }
        $note = 'Verified: the id exists and matches the expected type.'
        if ($null -ne $matchesExpect -and -not $matchesExpect) {
            $note = "TYPE MISMATCH: asset $id is a $($usage.typeName) (typeId $typeId), but '$expect' was expected. Do not apply it - search_assets for the right type or pick another id."
        }
        return @{
            ok = $true
            verified = $true
            catalogAvailable = $true
            assetId = $id
            assetName = [string]$asset.name
            typeId = $typeId
            typeName = $usage.typeName
            usableAs = $usage.usableAs
            hasScripts = [bool]$asset.hasScripts
            creator = [string]$entry.creator.name
            matchesExpect = $matchesExpect
            note = $note
        }
    }

    # ------------------------------------------------------------------
    # KATALOG-ERREICHBARKEIT (Schnelltest)
    # ------------------------------------------------------------------
    function Invoke-CatalogStatus($toolArgs) {
        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        try {
            Invoke-RestMethod -Uri 'https://apis.roblox.com/toolbox-service/v1/items/details?assetIds=155016084' -Method Get -TimeoutSec 15 -UseBasicParsing | Out-Null
            $sw.Stop()
            return @{ ok = $true; result = @{ catalogAvailable = $true; latencyMs = [int]$sw.ElapsedMilliseconds } }
        } catch {
            $sw.Stop()
            return @{
                ok = $true
                result = @{
                    catalogAvailable = $false
                    latencyMs = [int]$sw.ElapsedMilliseconds
                    protocol = 'The catalog is NOT reachable. Say so clearly to the user ("Katalog nicht verfuegbar") and build assets procedurally instead of guessing ids. Retry later - this test is cheap.'
                }
            }
        }
    }

    # ------------------------------------------------------------------
    # SCREENSHOT (bewusst unbeliebt gemacht - siehe Manifest)
    # ------------------------------------------------------------------
    function Invoke-Screenshot($toolArgs) {
        $advice = 'Screenshots are the WORST way for you to understand a place: image analysis is unreliable, slow and easy to misread. Use describe_scene, get_tree, get_bounds, get_instance or get_output instead - they give exact numbers.'
        if ($toolArgs.confirm -ne $true) {
            return @{
                ok = $false
                error = 'Screenshot refused. It needs confirm=true.'
                advice = $advice
                betterTools = @('describe_scene', 'get_bounds', 'get_tree', 'viewport_info', 'get_output')
            }
        }
        # Der eigentliche Code steckt in einem erst bei Bedarf erzeugten
        # Block. Grund: PowerShell löst Typangaben wie [System.Drawing...]
        # schon beim Übersetzen einer Funktion auf. Fehlt oder klemmt
        # System.Drawing, würden sonst ALLE Werkzeuge ausfallen - nur wegen
        # der Screenshot-Funktion, von der ohnehin abgeraten wird.
        $shotCode = [scriptblock]::Create(@'
param($toolArgs, $shotFolder, $advice)
Add-Type -AssemblyName System.Drawing -ErrorAction Stop
$process = Get-Process -Name 'RobloxStudioBeta', 'RobloxStudio' -ErrorAction SilentlyContinue |
    Where-Object { $_.MainWindowHandle -ne 0 } | Select-Object -First 1
if (-not $process) {
    return @{ ok = $false; error = 'No visible Roblox Studio window found.'; advice = $advice }
}
$rect = New-Object Arena.RECT
[void][Arena.ScreenHelper]::GetWindowRect($process.MainWindowHandle, [ref]$rect)
$width = $rect.Right - $rect.Left
$height = $rect.Bottom - $rect.Top
if ($width -le 0 -or $height -le 0) {
    return @{ ok = $false; error = 'The Studio window is minimised or hidden.'; advice = $advice }
}
$bitmap = New-Object System.Drawing.Bitmap $width, $height
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.CopyFromScreen($rect.Left, $rect.Top, 0, 0, (New-Object System.Drawing.Size $width, $height))
$graphics.Dispose()

$maxWidth = 1100
if ($toolArgs.maxWidth) { $maxWidth = [int]$toolArgs.maxWidth }
$final = $bitmap
if ($width -gt $maxWidth) {
    $scale = $maxWidth / [double]$width
    $newWidth = [int]($width * $scale)
    $newHeight = [int]($height * $scale)
    $resized = New-Object System.Drawing.Bitmap $newWidth, $newHeight
    $resizeGraphics = [System.Drawing.Graphics]::FromImage($resized)
    $resizeGraphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $resizeGraphics.DrawImage($bitmap, 0, 0, $newWidth, $newHeight)
    $resizeGraphics.Dispose()
    $bitmap.Dispose()
    $final = $resized
}

$fileName = 'studio_' + (Get-Date).ToString('yyyyMMdd_HHmmss') + '.png'
$filePath = Join-Path $shotFolder $fileName
$final.Save($filePath, [System.Drawing.Imaging.ImageFormat]::Png)
$shotWidth = $final.Width
$shotHeight = $final.Height
$final.Dispose()
return @{ ok = $true; file = $filePath; width = $shotWidth; height = $shotHeight }
'@)

        try {
            $shot = & $shotCode $toolArgs $Shared.ShotFolder $advice
        } catch {
            return @{ ok = $false; error = "Screenshot failed: $($_.Exception.Message)"; advice = $advice }
        }
        if (-not $shot.ok) { return $shot }

        $result = @{
            ok = $true
            result = @{
                file = $shot.file
                width = $shot.width
                height = $shot.height
                advice = $advice
            }
        }
        if ($toolArgs.includeBase64 -eq $true) {
            try {
                $bytes = [System.IO.File]::ReadAllBytes([string]$shot.file)
                $blob = New-Blob ([Convert]::ToBase64String($bytes)) 'capture_screenshot'
                $result.result.base64Blob = $blob
                $result.result.base64Note = 'Fetch the picture with get_chunk and decode base64. Seriously: describe_scene is better.'
            } catch {
                $result.result.base64Error = $_.Exception.Message
            }
        }
        return $result
    }

    # ------------------------------------------------------------------
    # BEFEHL AN DAS STUDIO-PLUGIN SCHICKEN
    # Der wartende Long-Poll wird sofort geweckt -> keine Verzögerung.
    # ------------------------------------------------------------------
    function Invoke-PluginTool($sessionId, $tool, $toolArgs, [int]$timeoutSeconds) {
        $commandId = [guid]::NewGuid().ToString('N')
        $signal = New-Object System.Threading.ManualResetEventSlim($false)
        [void]$Shared.ResultSignals.TryAdd($commandId, $signal)

        $command = @{ id = $commandId; tool = $tool; args = $toolArgs }
        $queue = Ensure-Queue $sessionId
        $queue.Enqueue((To-Json $command 40))
        # Als "im Studio laeuft" erfassen - ueberlebt ein Timeout (es wird nichts getoetet).
        Add-PendingCommand $sessionId $commandId $tool
        $wake = Ensure-Signal $sessionId
        [void]$wake.Set()

        $deadline = [DateTime]::UtcNow.AddSeconds($timeoutSeconds)
        $resultJson = $null
        $got = $false
        while ([DateTime]::UtcNow -lt $deadline) {
            if ($Shared.CommandResults.TryRemove($commandId, [ref]$resultJson)) { $got = $true; break }
            [void]$signal.Wait(100)
            $signal.Reset()
        }

        $removed = $null
        [void]$Shared.ResultSignals.TryRemove($commandId, [ref]$removed)
        [void]$Shared.ResultChunks.TryRemove($commandId, [ref]$removed)
        try { $signal.Dispose() } catch {}

        if (-not $got) { return $null }
        return $resultJson
    }

    # ==================================================================
    # TOOL-DOKUMENTATION: vollstaendig pro Tool - Beschreibung, alle
    # Parameter (Typ + Default + Bedeutung), Rueckgabewert, lauffaehiges
    # Beispiel und Fehlerfaelle. Wird automatisch mit dem ersten Call der
    # Sitzung ausgeliefert und laesst sich ueber /api/docs + get_docs
    # pro Tool, pro Kategorie oder komplett abrufen.
    # ==================================================================
    function Get-ToolDocs {
        $t = New-Object System.Collections.Generic.List[object]

        # ---------------- INFO ----------------
        $t.Add(@{ name = 'get_place_info'; category = 'info'; summary = 'Place, Play-Zustand, Faehigkeiten.';
            description = 'Was fuer ein Place ist verbunden, welche Id hat er, laeuft gerade ein Test (edit/run/play), welche Faehigkeiten hat das Plugin. Immer der erste sinnvolle Call.';
            params = @{};
            returns = '{ name, placeId, gameId, creatorId, state: { running, mode, context, playerCount }, capabilities, pluginVersion }';
            example = @{};
            errors = @('REF_NOT_FOUND: kein Studio-Fenster verbunden (Token ungültig oder Place geschlossen).') })
        $t.Add(@{ name = 'get_tree'; category = 'info'; summary = 'Instanz-Baum mit Ids.';
            description = 'Liest die Hierarchie ab der Wurzel mit allen Ids (#42), Klassennamen und (optional) Eigenschaften/Quellcode. Nutze rootRef, um grosse Baume in Stuecken zu lesen.';
            params = @{ rootRef = @{ type = 'ref'; required = $false; default = "'game'"; description = 'Wurzel: Id (#42) oder Pfad (game.Workspace).' }; maxDepth = @{ type = 'int'; required = $false; default = '6'; description = 'Ebenen tief.' }; maxNodes = @{ type = 'int'; required = $false; default = '3000'; description = 'Obergrenze der Knoten - bei Erreichung truncated=true.' }; includeProperties = @{ type = 'bool'; required = $false; default = 'false'; description = 'Eigenschaften mitliefern (teuer).' }; includeSource = @{ type = 'bool'; required = $false; default = 'false'; description = 'Quelltext von Skripten mitliefern.' } };
            returns = '{ tree: { id, name, className, path, children: [...] }, nodeCount, truncated }';
            example = @{ rootRef = 'game.Workspace'; maxDepth = 2 };
            errors = @('REF_NOT_FOUND: rootRef existiert nicht.') })
        $t.Add(@{ name = 'search'; category = 'info'; summary = 'Instanzen suchen (Name/Klasse/Tag).';
            description = 'Sucht in der Wurzel nach Namen (Teil-/Gleich), Class (IsA) oder CollectionService-Tag. Liefert Ids - nutze IMMER die Ids zurueck, Namen sind nicht eindeutig.';
            params = @{ query = @{ type = 'string'; required = $false; default = "''"; description = 'Namenssuche (lowercase, Teilstring).' }; className = @{ type = 'string'; required = $false; default = 'null'; description = 'z.B. BasePart, Script, Model (IsA).' }; tag = @{ type = 'string'; required = $false; default = 'null'; description = 'CollectionService-Tag.' }; rootRef = @{ type = 'ref'; required = $false; default = "'game'"; description = 'Suchbereich.' }; limit = @{ type = 'int'; required = $false; default = '200'; description = 'Maximale Treffer.' }; exact = @{ type = 'bool'; required = $false; default = 'false'; description = 'Nur exakte Namenstreffer.' } };
            returns = '{ matches: [ { id, name, className, path, position?, size?, sourceLines? } ], totalMatches, returned }';
            example = @{ query = 'wall'; className = 'BasePart'; rootRef = 'game.Workspace' };
            errors = @() })
        $t.Add(@{ name = 'get_instance'; category = 'info'; summary = 'Ein Objekt im Detail.';
            description = 'Eigenschaften, Attribute, Tags und Kinder eines Objekts. Bei Skripten nur Groesse (nutze get_script fuer den Text).';
            params = @{ ref = @{ type = 'ref'; required = $true; default = '-'; description = 'Id (#42) oder Pfad.' }; includeSource = @{ type = 'bool'; required = $false; default = 'false'; description = 'Skriptquelle mitliefern.' }; includeAllProperties = @{ type = 'bool'; required = $false; default = 'false'; description = 'Hinweis auf exotische Eigenschaften.' } };
            returns = '{ id, name, className, path, parent, properties, attributes (in properties.Attributes), children, childCount }';
            example = @{ ref = '#42'; includeSource = $true };
            errors = @('REF_NOT_FOUND: Id unbekannt (geloescht oder Plugin neu geladen) - neu suchen mit search/get_tree.') })
        $t.Add(@{ name = 'get_children'; category = 'info'; summary = 'Kinder paginieren.';
            params = @{ ref = @{ type = 'ref'; required = $false; default = "'game'"; description = 'Vater-Objekt.' }; offset = @{ type = 'int'; required = $false; default = '0'; description = 'Erstes Kind.' }; limit = @{ type = 'int'; required = $false; default = '500'; description = 'Seite-Groesse.' } };
            returns = '{ children: [ { id, name, className, path, childCount } ], total, offset, returned }';
            example = @{ ref = '#50'; offset = 0; limit = 100 };
            errors = @() })
        $t.Add(@{ name = 'get_properties'; category = 'info'; summary = 'Dieselben Eigenschaften von vielen.';
            params = @{ refs = @{ type = 'ref[]'; required = $true; default = '-'; description = 'Liste von Ids/Selektoren.' }; properties = @{ type = 'string[]'; required = $false; default = 'all common'; description = 'z.B. ["Position","Size"].' }; includeSource = @{ type = 'bool'; required = $false; default = 'false'; description = '' } };
            returns = '{ items: [ { id, name, className, path, properties: {...} } ], errors }';
            example = @{ refs = @('#42','#43'); properties = @('Position','Size') };
            errors = @('REF_NOT_FOUND: einzelne Ids fehlen (siehe errors).') })
        $t.Add(@{ name = 'resolve_ref'; category = 'info'; summary = 'Pfad zu stabiler Id.';
            params = @{ ref = @{ type = 'ref'; required = $true; default = '-'; description = 'Pfad oder Id.' } };
            returns = '{ id, name, className, path }';
            example = @{ ref = 'game.Workspace.Part[3]' };
            errors = @('REF_NOT_FOUND') })
        $t.Add(@{ name = 'get_selection'; category = 'info'; summary = 'Wahl des Benutzers.';
            description = 'Was der BENUTZER gerade in Studio markiert hat - oft sein direkter Hinweis, worum es geht.';
            params = @{};
            returns = '{ selection: [ { id, name, className, path } ], count }';
            example = @{};
            errors = @() })
        $t.Add(@{ name = 'select_instance'; category = 'info'; summary = 'Objekte im Studio markieren.';
            description = 'Markiert Objekte im Studio-Fenster, damit der Benutzer sieht, worauf du dich beziehst.';
            params = @{ refs = @{ type = 'ref[]'; required = $true; default = '-'; description = '' }; add = @{ type = 'bool'; required = $false; default = 'false'; description = 'Zur aktuellen Markierung hinzufuegen.' } };
            returns = '{ selected: [...], errors }';
            example = @{ refs = @('#42','#43') };
            errors = @() })
        $t.Add(@{ name = 'describe_scene'; category = 'info'; summary = 'TEXT-Beschreibung der Szene (statt Screenshot).';
            description = 'Kamera + Objekte mit Position/Groesse/Material/Transparenz als Text. DEUTLICH zuverlaessiger fuer dich als ein Bild. Das Standard-Werkzeug zum "Sehen".';
            params = @{ rootRef = @{ type = 'ref'; required = $false; default = "'game.Workspace'"; description = '' }; maxItems = @{ type = 'int'; required = $false; default = '120'; description = '' }; maxDepth = @{ type = 'int'; required = $false; default = '2'; description = '' } };
            returns = '{ text (menschenlesbar), items, classSummary, truncated, hint }';
            example = @{ rootRef = 'game.Workspace'; maxItems = 60 };
            errors = @() })
        $t.Add(@{ name = 'viewport_info'; category = 'info'; summary = 'Kamera + Blickziel.';
            params = @{};
            returns = '{ camera (CFrame), fieldOfView, viewportSize, lookingAt: { instance, position, distance } }';
            example = @{};
            errors = @() })
        $t.Add(@{ name = 'get_bounds'; category = 'info'; summary = 'Zentrum/Groesse/Ecken.';
            params = @{ refs = @{ type = 'ref[]'; required = $true; default = '-'; description = '' } };
            returns = 'pro Objekt: { id, name, center, size, min, max, top, bottom, cframe }';
            example = @{ refs = @('#42') };
            errors = @() })
        $t.Add(@{ name = 'scene_stats'; category = 'info'; summary = 'Performance-ueberblick des Places.';
            description = 'Zaehlt Teile, Unions, MeshParts, Skripte, schätzt Dreiecke und gibt konkrete Tipps fuer grosse Places (z.B. 17.000+ Teile): CanCollide bei Deko aus, in Models gruppieren, Unions klein halten.';
            params = @{};
            returns = '{ partCount, unionCount, meshPartCount, scriptCount, topLevel: [...], triangleEstimate, tips: [...] }';
            example = @{};
            errors = @() })
        $t.Add(@{ name = 'list_tools'; category = 'info'; summary = 'Alle Tools mit Kategorie + Kurzbeschreibung.';
            params = @{};
            returns = '{ tools: [ { name, category, summary } ], count, pluginVersion, docsVersion, docs }';
            example = @{};
            errors = @() })
        $t.Add(@{ name = 'bridge_status'; category = 'info'; summary = 'Zustand der Bridge.';
            description = 'Version, Place, Warteschlange, was grade in Studio laeuft (ueberlebte Timeouts), Asset-Cache-Groesse.';
            params = @{};
            returns = '{ bridgeVersion, docsVersion, place, studio, queuedCommands, runningInStudio, connectedPlaces, assetCacheEntries }';
            example = @{};
            errors = @() })

        # ---------------- SPATIAL ----------------
        $t.Add(@{ name = 'raycast'; category = 'spatial'; summary = 'Einen Strahl schieessen.';
            description = 'Raycast ab origin in direction. Fuer HÖHEN IMMER raycast/ground_height benutzen - niemals Y aus Indizes berechnen.';
            params = @{ origin = @{ type = '{x,y,z}'; required = $true; default = '-'; description = 'Startpunkt.' }; direction = @{ type = '{x,y,z}'; required = $true; default = '-'; description = 'Richtung (Länge = max. Reichweite).' }; ignore = @{ type = 'ref[]'; required = $false; default = 'null'; description = 'Objekte ignorieren.' } };
            returns = '{ hit: bool, instance?, position?, normal?, distance?, material? } - bei kein Treffer NUR { hit: false }';
            example = @{ origin = @{ x = 0; y = 50; z = 0 }; direction = @{ x = 0; y = -100; z = 0 } };
            errors = @('REF_NOT_FOUND: ignore-Id unbekannt.') })
        $t.Add(@{ name = 'raycast_many'; category = 'spatial'; summary = 'Batch: viele Strahlen in einem Call.';
            description = 'Bis zu 200 Rays gleichzeitig - damit kein 60-mal-einzelner-Call mehr.';
            params = @{ rays = @{ type = 'array of { origin, direction, length? }'; required = $true; default = '-'; description = 'length (default 1000) wird auf direction gewirkt.' }; ignore = @{ type = 'ref[]'; required = $false; default = 'null'; description = '' } };
            returns = '{ results: [ { index, hit, instance?, position?, distance?, normal? } ], hitCount }';
            example = @{ rays = @(@{ origin = @{ x = 0; y = 20; z = 0 }; direction = @{ x = 0; y = -1; z = 0 }; length = 40 }, @{ origin = @{ x = 5; y = 20; z = 0 }; direction = @{ x = 0; y = -1; z = 0 }; length = 40 }) };
            errors = @('TOO_MANY: mehr als 200 Rays - in Runden aufteilen.') })
        $t.Add(@{ name = 'ground_height'; category = 'spatial'; summary = 'Höhen per Raycast (Batch).';
            description = 'Fuer jeden Punkt: nach unten raycasten und die Boden-Höhe (Welt-Y) zurueckgeben. DAS ist die einzige erlaubte Art, Hoehenzu bestimmen.';
            params = @{ points = @{ type = 'array of {x,y,z}'; required = $true; default = '-'; description = 'Ausgangspunkte (muenueber dem Boden sein).' }; ignore = @{ type = 'ref[]'; required = $false; default = 'null'; description = '' } };
            returns = '{ results: [ { point, hit, y?, distance?, instance? } ] }';
            example = @{ points = @(@{ x = 0; y = 30; z = 0 }, @{ x = 4; y = 30; z = 4 }) };
            errors = @() })
        $t.Add(@{ name = 'measure'; category = 'spatial'; summary = 'Distanz zwischen zwei Objekten.';
            params = @{ refA = @{ type = 'ref'; required = $true; default = '-'; description = '' }; refB = @{ type = 'ref'; required = $true; default = '-'; description = '' } };
            returns = '{ distance, delta: {x,y,z}, from, to }';
            example = @{ refA = '#42'; refB = '#43' };
            errors = @('REF_NOT_FOUND') })
        $t.Add(@{ name = 'measure_height'; category = 'spatial'; summary = 'Distanz zu Boden/Himmel.';
            description = 'Raycast ab einem Punkt/Objekt nach unten (Boden) oder oben (Himmel) - die freie Hoehe.';
            params = @{ ref = @{ type = 'ref'; required = $false; default = 'null'; description = 'Oder point.' }; point = @{ type = '{x,y,z}'; required = $false; default = 'null'; description = 'Oder ref.' }; direction = @{ type = "'down'|'up'"; required = $false; default = "'down'"; description = '' }; ignore = @{ type = 'ref[]'; required = $false; default = 'null'; description = '' } };
            returns = '{ from, hit, y?, distance?, instance? }';
            example = @{ point = @{ x = 0; y = 10; z = 0 }; direction = 'down' };
            errors = @('REF_NOT_FOUND') })
        $t.Add(@{ name = 'parts_in_box'; category = 'spatial'; summary = 'Alle Teile in einer Box.';
            description = 'Räumliche Abfrage: alle BaseParts, deren Bounds die Box beruehren. Box als min/max, center/size oder zwei Eck-Objekte. BaseParts (Parts, MeshParts, Unions) - andere Klassen mit search.';
            params = @{ min = @{ type = '{x,y,z}'; required = $false; default = 'null'; description = 'Untere Ecke. (alternativ center+size oder refA+refB)' }; max = @{ type = '{x,y,z}'; required = $false; default = 'null'; description = 'Obere Ecke.' }; center = @{ type = '{x,y,z}'; required = $false; default = 'null'; description = 'Mitte (mit size).' }; size = @{ type = '{x,y,z}'; required = $false; default = 'null'; description = 'Ausdehnung (mit center).' }; refA = @{ type = 'ref'; required = $false; default = 'null'; description = 'Ecke 1 (mit refB).' }; refB = @{ type = 'ref'; required = $false; default = 'null'; description = 'Ecke 2.' }; tolerance = @{ type = 'number'; required = $false; default = '0'; description = 'Box um so viel Studs aufwaechsen lassen.' }; className = @{ type = 'string'; required = $false; default = 'null'; description = 'z.B. Part, MeshPart.' }; tag = @{ type = 'string'; required = $false; default = 'null'; description = 'Nur Objekte mit Tag.' }; excludeRefs = @{ type = 'ref[]'; required = $false; default = 'null'; description = 'Ausschliessen.' }; limit = @{ type = 'int'; required = $false; default = '200'; description = '' } };
            returns = '{ items: [ { id, name, className, position, size, distanceFromCenter } ], count, empty, hint (wenn empty) }';
            example = @{ min = @{ x = -10; y = 0; z = -10 }; max = @{ x = 10; y = 20; z = 10 }; tolerance = 1 };
            errors = @('REF_NOT_FOUND: Box-Ecken nicht auflasbar.', 'BAD_ARGS: min/max, center/size oder refA/refB angeben.') })
        $t.Add(@{ name = 'parts_in_sphere'; category = 'spatial'; summary = 'Alle Teile in einem Kugelumfeld.';
            params = @{ center = @{ type = '{x,y,z}'; required = $false; default = 'null'; description = 'Oder ref.' }; ref = @{ type = 'ref'; required = $false; default = 'null'; description = 'Oder center.' }; radius = @{ type = 'number'; required = $true; default = '-'; description = 'Studs.' }; tolerance = @{ type = 'number'; required = $false; default = '0'; description = 'Radius aufwaechsen.' }; className = @{ type = 'string'; required = $false; default = 'null'; description = '' }; tag = @{ type = 'string'; required = $false; default = 'null'; description = '' }; excludeRefs = @{ type = 'ref[]'; required = $false; default = 'null'; description = '' }; limit = @{ type = 'int'; required = $false; default = '200'; description = '' } };
            returns = '{ items: [ { id, name, className, position, size, distance } ], count, empty }';
            example = @{ center = @{ x = 0; y = 5; z = 0 }; radius = 10 };
            errors = @('REF_NOT_FOUND', 'BAD_ARGS: center oder ref erforderlich.') })
        $t.Add(@{ name = 'nearest_parts'; category = 'spatial'; summary = 'Nächste Objekte (sortiert nach Distanz).';
            description = '"Was ist in 10 Studs?" - Kugel-Abfrage, aufsteigend nach Distanz sortiert.';
            params = @{ origin = @{ type = '{x,y,z}'; required = $false; default = 'null'; description = 'Oder ref.' }; ref = @{ type = 'ref'; required = $false; default = 'null'; description = 'Oder origin.' }; radius = @{ type = 'number'; required = $true; default = '-'; description = '' }; limit = @{ type = 'int'; required = $false; default = '20'; description = '' }; className = @{ type = 'string'; required = $false; default = 'null'; description = '' }; tag = @{ type = 'string'; required = $false; default = 'null'; description = '' } };
            returns = '{ items: [ { id, name, className, position, distance, size } ], count, empty, nearest: (erstes Item oder null) }';
            example = @{ ref = '#42'; radius = 10; limit = 5 };
            errors = @('REF_NOT_FOUND') })
        $t.Add(@{ name = 'what_is_in_the_way'; category = 'spatial'; summary = 'Was steht zwischen A und B?';
            description = 'Baumt eine Box entlang der Strecke zwischen zwei Punkten/Objekten und listet alles, was drin liegt (A und B selbst werden ausgeschlossen).';
            params = @{ fromRef = @{ type = 'ref'; required = $false; default = 'null'; description = 'Oder origin.' }; toRef = @{ type = 'ref'; required = $false; default = 'null'; description = 'Oder target.' }; origin = @{ type = '{x,y,z}'; required = $false; default = 'null'; description = '' }; target = @{ type = '{x,y,z}'; required = $false; default = 'null'; description = '' }; width = @{ type = 'number'; required = $false; default = '2'; description = 'Box-Breite/Höhe um die Linie.' } };
            returns = '{ items: [ { id, name, className, position, distanceFromLine } ], count, clear (true = nichts im Weg) }';
            example = @{ fromRef = '#42'; toRef = '#43'; width = 2 };
            errors = @('REF_NOT_FOUND', 'BAD_ARGS: von+nach angeben.') })
        $t.Add(@{ name = 'overlap_check'; category = 'spatial'; summary = 'Stosst ein Objekt mit etwas zusammen?';
            description = 'Prueft die Bounds eines Objekts (mit Toleranz aufgeweitet) gegen die Welt.';
            params = @{ ref = @{ type = 'ref'; required = $true; default = '-'; description = '' }; tolerance = @{ type = 'number'; required = $false; default = '0'; description = 'Box aufwaechsen (Studs).' }; excludeRefs = @{ type = 'ref[]'; required = $false; default = 'null'; description = '' }; className = @{ type = 'string'; required = $false; default = 'null'; description = '' }; limit = @{ type = 'int'; required = $false; default = '50'; description = '' } };
            returns = '{ overlapping: [ { id, name, className, position } ], count, clear }';
            example = @{ ref = '#42'; tolerance = 0.5 };
            errors = @('REF_NOT_FOUND') })
        $t.Add(@{ name = 'snap_to_ground'; category = 'spatial'; summary = 'Auf das legen, was darunter ist.';
            description = 'Raycast nach unten pro Objekt und hinuntersetzen. Wartet automatisch, bis die Welt wieder antwortet, und verifiziert per Gegen-Raycast.';
            params = @{ refs = @{ type = 'ref[]'; required = $true; default = '-'; description = '' }; offset = @{ type = 'number'; required = $false; default = '0'; description = 'Zusaetzlicher Abstand ueber dem Boden.' }; maxFall = @{ type = 'number'; required = $false; default = '2000'; description = 'Toleranz: hoechstens so tief fallen; darueber = nicht bewegen + Hinweis.' }; ignore = @{ type = 'ref[]'; required = $false; default = 'null'; description = '' }; waitForMeasurable = @{ type = 'bool'; required = $false; default = 'true'; description = 'Nach dem Setzen per Raycast verifizieren.' } };
            returns = '{ results: [ { instance, y, ground, verified } ], count, geometry }';
            example = @{ refs = @('#42','#43'); offset = 0.1 };
            errors = @('REF_NOT_FOUND', 'GEOMETRY_NOT_READY (Warning): Welt nach dem Setzen nicht sofort messbar.') })
        $t.Add(@{ name = 'verify_measurable'; category = 'spatial'; summary = 'Warten, bis Geometrie raycastbar ist.';
            description = 'Nach create/fill ist neue Geometrie manchemal erst ab dem naechsten Frame messbar. Dieses Tool wartet aktiv, bis alle refs per Raycast antworten (oder die Zeit abgelaufen ist).';
            params = @{ refs = @{ type = 'ref[]'; required = $true; default = '-'; description = '' }; maxSeconds = @{ type = 'number'; required = $false; default = '5'; description = '' } };
            returns = '{ ready, frames, waitedSeconds, notReady: [ { id, name } ] (wenn nicht ready) }';
            example = @{ refs = @('#60','#61') };
            errors = @('REF_NOT_FOUND') })

        # ---------------- ORIENTATION / ROTATION ----------------
        $t.Add(@{ name = 'coordinate_guide'; category = 'orientation'; summary = 'Koordinatensystem + formbewusste Achsen (gemessen).';
            description = 'Die WICHTIGSTE Referenz fuer Rotation: welche Achse was heisst, wie Yaw/Pitch/Roll wirken (mit Formeln), UND wie Block/Ball/Cylinder/Wedge standardmaessig ausgerichtet sind - das wird live im Place gemessen (mit temporaren Probedeilen), NICHT geraten. Vor dem ersten Drehen eines Zylinders/Wedges IMMER hier nachschauen.';
            params = @{ reprobe = @{ type = 'bool'; required = $false; default = 'false'; description = 'Geometrie neu messen.' } };
            returns = '{ axes: {x,y,z}, yawRule, shapeDefaults: { block, ball, cylinder, wedge: { description, measured } }, howToRotate }';
            example = @{};
            errors = @() })
        $t.Add(@{ name = 'describe_orientation'; category = 'orientation'; summary = 'Wohin zeigen die Seiten dieses Parts?';
            description = 'Gibt in Klartext und als Vektoren, wohin top/bottom/front/back/left/right des Objekts in Welt-Koordinaten zeigen. Damit "welche Seite zeigt nach vorne?" nie mehr geraten werden muss.';
            params = @{ ref = @{ type = 'ref'; required = $true; default = '-'; description = '' } };
            returns = '{ top, bottom, front, back, left, right (je {x,y,z}), yawDegrees, pitchDegrees, rollDegrees, human: [ "front face points to the left (-X)", ... ] }';
            example = @{ ref = '#42' };
            errors = @('REF_NOT_FOUND', 'BAD_ARGS: Objekt hat keine Position.') })
        $t.Add(@{ name = 'point_at'; category = 'orientation'; summary = 'Part formbewusst auf Ziel ausrichten.';
            description = 'Dreht den Part SO, dass die gewählte lokale Achse exakt auf das Ziel zeigt - mit der moeglichst kleinen Rotation. Fuer Zylinder: axis="top" (die Lange-Achse). Fuer Wedges: coordinate_guide zuerst lesen. Ersetzt alle manuellen CFrame-Rechnungen.';
            params = @{ ref = @{ type = 'ref'; required = $true; default = '-'; description = '' }; targetRef = @{ type = 'ref'; required = $false; default = 'null'; description = 'Ziel-Objekt. (alternativ targetPosition)' }; targetPosition = @{ type = '{x,y,z}'; required = $false; default = 'null'; description = 'Ziel-Punkt.' }; axis = @{ type = "'front'|'back'|'top'|'bottom'|'left'|'right'"; required = $false; default = "'front'"; description = 'Welche lokale Achse aufs Ziel zeigen soll (front = -Z).' }; keepUpright = @{ type = 'bool'; required = $false; default = 'true'; description = 'Objekt senkrecht lassen (kein Kippen).' } };
            returns = '{ instance, cframe (neu), target, axis, yawDegrees }';
            example = @{ ref = '#42'; targetRef = '#43'; axis = 'front' };
            errors = @('REF_NOT_FOUND', 'BAD_ARGS: targetRef oder targetPosition fehlt.') })
        $t.Add(@{ name = 'look_at'; category = 'orientation'; summary = 'Auf Ziel drehen (klassisch, -Z nach vorn).';
            description = 'Wie point_at mit axis="front" (die "Vorderseite" -Z zeigt aufs Ziel).';
            params = @{ ref = @{ type = 'ref'; required = $true; default = '-'; description = '' }; targetRef = @{ type = 'ref'; required = $false; default = 'null'; description = 'Oder position.' }; position = @{ type = '{x,y,z}'; required = $false; default = 'null'; description = 'Oder targetRef.' }; keepUpright = @{ type = 'bool'; required = $false; default = 'true'; description = '' }; axis = @{ type = 'string'; required = $false; default = "'front'"; description = 'Andere Achse -> gleich wie point_at.' } };
            returns = '{ instance, cframe }';
            example = @{ ref = '#42'; targetRef = '#43' };
            errors = @('REF_NOT_FOUND') })
        $t.Add(@{ name = 'rotate_around'; category = 'orientation'; summary = 'Um einen Punkt drehen.';
            params = @{ refs = @{ type = 'ref[]'; required = $true; default = '-'; description = '' }; axis = @{ type = "'x'|'y'|'z'"; required = $false; default = "'y'"; description = '' }; degrees = @{ type = 'number'; required = $false; default = '0'; description = 'Drehwinkel (grad, + = gegen Uhrzeiger um die Achse).' }; pivot = @{ type = '{x,y,z}'; required = $false; default = 'null'; description = 'Drehzentrum. (alternativ pivotRef)' }; pivotRef = @{ type = 'ref'; required = $false; default = 'null'; description = 'Oder pivot. Default: Position des ersten Objekts.' } };
            returns = '{ rotated: [...], count, degrees, axis }';
            example = @{ refs = @('#42'); pivotRef = '#43'; axis = 'y'; degrees = 90 };
            errors = @('REF_NOT_FOUND') })
        $t.Add(@{ name = 'move_relative'; category = 'orientation'; summary = 'Lokal oder weltbezogen verschieben.';
            params = @{ refs = @{ type = 'ref[]'; required = $true; default = '-'; description = '' }; right = @{ type = 'number'; required = $false; default = '0'; description = '' }; up = @{ type = 'number'; required = $false; default = '0'; description = '' }; forward = @{ type = 'number'; required = $false; default = '0'; description = 'Positive forward = in die Blickrichtung des Objekts (lokal -Z).' }; space = @{ type = "'world'|'local'"; required = $false; default = "'world'"; description = '' } };
            returns = '{ moved: [ { instance, position } ], count }';
            example = @{ refs = @('#42'); right = 4; forward = 2; space = 'local' };
            errors = @('REF_NOT_FOUND') })
        $t.Add(@{ name = 'resize_part'; category = 'orientation'; summary = 'Groesse aendern, Kante halten.';
            params = @{ ref = @{ type = 'ref'; required = $true; default = '-'; description = 'BasePart.' }; size = @{ type = '{x,y,z}'; required = $true; default = '-'; description = 'Neue Groesse.' }; anchor = @{ type = "'center'|'bottom'|'top'"; required = $false; default = "'center'"; description = 'Welche Kante stehen bleibt.' } };
            returns = '{ instance, size, position }';
            example = @{ ref = '#42'; size = @{ x = 4; y = 8; z = 4 }; anchor = 'bottom' };
            errors = @('REF_NOT_FOUND', 'BAD_ARGS: kein BasePart.') })
        $t.Add(@{ name = 'fit_between'; category = 'orientation'; summary = 'Zwei Punkte verbinden (Tragwerk/Kabel/Schiene).';
            params = @{ ref = @{ type = 'ref'; required = $true; default = '-'; description = 'BasePart, das gestreckt wird.' }; fromRef = @{ type = 'ref'; required = $false; default = 'null'; description = 'Oder from {x,y,z}.' }; toRef = @{ type = 'ref'; required = $false; default = 'null'; description = 'Oder to.' }; from = @{ type = '{x,y,z}'; required = $false; default = 'null'; description = '' }; to = @{ type = '{x,y,z}'; required = $false; default = 'null'; description = '' }; thickness = @{ type = 'number'; required = $false; default = '1'; description = 'Dicke quer zur Verbindung.' } };
            returns = '{ instance, length }';
            example = @{ ref = '#42'; fromRef = '#43'; toRef = '#44'; thickness = 0.5 };
            errors = @('REF_NOT_FOUND', 'BAD_ARGS: from/to fehlt.') })
        $t.Add(@{ name = 'place_on'; category = 'orientation'; summary = 'A auf eine Flaeeche von B legen.';
            description = 'Setzt Objekt A auf/an eine Flaeeche von B (top/bottom/front/back/left/right), mit Versatz zur Mitte. Keine manuelle Mathematik.';
            params = @{ ref = @{ type = 'ref'; required = $true; default = '-'; description = 'Das zu bewegende Objekt (A).' }; targetRef = @{ type = 'ref'; required = $true; default = '-'; description = 'Das Ziel (B).' }; face = @{ type = "'top'|'bottom'|'front'|'back'|'left'|'right'"; required = $false; default = "'top'"; description = '' }; offsetX = @{ type = 'number'; required = $false; default = '0'; description = 'Seitlicher Versatz (Studs) zur Mitte.' }; offsetZ = @{ type = 'number'; required = $false; default = '0'; description = 'Versatz entlang der Flaeeche.' }; gap = @{ type = 'number'; required = $false; default = '0'; description = 'Lichtspalt.' }; matchRotation = @{ type = 'bool'; required = $false; default = 'false'; description = 'A orientiert sich an B.' }; inside = @{ type = 'bool'; required = $false; default = 'false'; description = 'A in B hinein (z.B. Tuer in Wand) statt davor.' } };
            returns = '{ moved, target, face, newPosition, gap }';
            example = @{ ref = '#42'; targetRef = '#43'; face = 'top'; offsetX = 2; gap = 0.1 };
            errors = @('REF_NOT_FOUND', 'BAD_ARGS: unbekannte face.') })
        $t.Add(@{ name = 'align'; category = 'orientation'; summary = 'Aliase für place_on.';
            description = 'Gleicher Befehl wie place_on (anderer Name).';
            params = @{ ref = @{ type = 'ref'; required = $true; default = '-'; description = '' }; targetRef = @{ type = 'ref'; required = $true; default = '-'; description = '' }; face = @{ type = 'string'; required = $false; default = "'top'"; description = 'Siehe place_on.' } };
            returns = 'wie place_on';
            example = @{ ref = '#42'; targetRef = '#43'; face = 'left' };
            errors = @() })
        $t.Add(@{ name = 'stack'; category = 'orientation'; summary = 'Objekte stapeln.';
            params = @{ refs = @{ type = 'ref[]'; required = $true; default = '-'; description = 'In der Reihenfolge der Stapel.' }; axis = @{ type = "'x'|'y'|'z'"; required = $false; default = "'y'"; description = '' }; gap = @{ type = 'number'; required = $false; default = '0'; description = 'Abstand zwischen den Stuecken.' }; baseRef = @{ type = 'ref'; required = $false; default = 'null'; description = 'Darauf starten.' }; alignToBase = @{ type = 'bool'; required = $false; default = 'false'; description = 'Querachsen am Basisteil ausrichten.' } };
            returns = '{ stacked: [ { instance, position } ], count, axis }';
            example = @{ refs = @('#42','#43','#44'); axis = 'y'; gap = 0.2 };
            errors = @('REF_NOT_FOUND') })
        $t.Add(@{ name = 'grid_arrange'; category = 'orientation'; summary = 'Im Raster anordnen.';
            params = @{ refs = @{ type = 'ref[]'; required = $true; default = '-'; description = '' }; columns = @{ type = 'int'; required = $false; default = 'sqrt(n)'; description = 'Spalten.' }; spacingX = @{ type = 'number'; required = $false; default = '10'; description = 'Abstand X.' }; spacingZ = @{ type = 'number'; required = $false; default = '10'; description = 'Abstand Z.' }; origin = @{ type = '{x,y,z}'; required = $false; default = 'Position des ersten'; description = 'Startzelle.' } };
            returns = '{ placed: [ { instance, position } ], count, columns }';
            example = @{ refs = @('#1','#2','#3','#4'); columns = 2; spacingX = 6; spacingZ = 6 };
            errors = @('REF_NOT_FOUND') })
        $t.Add(@{ name = 'distribute'; category = 'orientation'; summary = 'Gleichmaessig verteilen.';
            params = @{ refs = @{ type = 'ref[]'; required = $true; default = '-'; description = '' }; axis = @{ type = "'x'|'y'|'z'"; required = $false; default = "'x'"; description = '' }; spacing = @{ type = 'number'; required = $false; default = 'null'; description = 'Fest -> gleichmaessige Schritte. Nicht gesetzt -> Lerp zwischen erstem und letztem.' } };
            returns = '{ placed: [...], count }';
            example = @{ refs = @('#42','#43','#44'); axis = 'x'; spacing = 5 };
            errors = @('REF_NOT_FOUND') })

        # ---------------- CREATE ----------------
        $t.Add(@{ name = 'create_instance'; category = 'create'; summary = 'Ein (oder mehrere gleiche) Instanz(en).';
            params = @{ parentRef = @{ type = 'ref'; required = $false; default = "'game.Workspace'"; description = '' }; className = @{ type = 'string'; required = $false; default = "'Part'"; description = 'Part, MeshPart, Model, Script, ScreenGui, ...' }; name = @{ type = 'string'; required = $false; default = 'className'; description = '' }; properties = @{ type = 'table'; required = $false; default = '{}'; description = 'z.B. { Size={x=4,y=8,z=1}, Anchored=true, Material="Neon", Color={255,80,0} }' }; count = @{ type = 'int'; required = $false; default = '1'; description = 'N x gleiches (mit offset).' }; offset = @{ type = '{x,y,z}'; required = $false; default = '0'; description = 'Versatz pro Nummer (bei count>1).' }; waitForMeasurable = @{ type = 'bool'; required = $false; default = 'true'; description = 'Warten, bis die neuen Teile raycastbar sind.' } };
            returns = 'einzel: { id, name, className, path, propertyProblems? }; mehrere: { created: [...], count, geometry }';
            example = @{ parentRef = 'game.Workspace'; className = 'Part'; name = 'Wall'; properties = @{ Size = @{ x = 4; y = 8; z = 1 }; Anchored = $true; Material = 'Neon' } };
            errors = @('REF_NOT_FOUND: parent fehlt.', 'BAD_ARGS: unbekannte className.') })
        $t.Add(@{ name = 'bulk_create'; category = 'create'; summary = 'Viele VERSCHIEDENE Instanzen in einem Call.';
            description = 'Entweder items=[...] (eine Spezifikation pro Teil) oder Template+Raster: template=... + count + grid erzeugt automatisch die Anordnung. Ersetzt jede Lua-Schleife zum Bauen.';
            params = @{ items = @{ type = 'array of { parentRef, className, name, properties }'; required = $false; default = 'null'; description = 'Variante 1: explizite Liste.' }; template = @{ type = '{ className, properties, parentRef? }'; required = $false; default = 'null'; description = 'Variante 2: Vorlage (mit count+grid).' }; count = @{ type = 'int'; required = $false; default = 'null'; description = 'Anzahl bei template.' }; grid = @{ type = '{ rows, columns, spacingX, spacingZ, origin }'; required = $false; default = 'null'; description = 'Raster bei template. Ohne grid: nur count mit offset (origin + offset). grid.columns (= grid.cols) bestimmt die Spalten.' }; offset = @{ type = '{x,y,z}'; required = $false; default = '0'; description = 'Versatz pro Nummer (ohne grid).' }; nameTemplate = @{ type = "string mit {n}"; required = $false; default = 'Name{n}'; description = 'z.B. "Crate{n}".' } };
            returns = '{ created: [ { id, name, className, path, position? } ], count, errors: ["item 3: ..."], geometry }';
            example = @{ template = @{ className = 'Part'; properties = @{ Size = @{ x = 4; y = 4; z = 4 }; Anchored = $true } }; count = 20; grid = @{ columns = 10; spacingX = 6; spacingZ = 6; origin = @{ x = 0; y = 2; z = 0 } }; nameTemplate = 'Crate{n}' };
            errors = @('REF_NOT_FOUND', 'BAD_ARGS: items ODER template angeben.') })
        $t.Add(@{ name = 'clone_instance'; category = 'create'; summary = 'Klonen statt nachbauen.';
            description = 'Kopiert ein fertiges Objekt (mit Kindern, Farben, Skripten) n-mal, mit beliebigem Versatz und/oder Dreh-Schritt. Das schnellste Werkzeug fuer Wiederholungen.';
            params = @{ ref = @{ type = 'ref'; required = $true; default = '-'; description = 'Vorlage.' }; count = @{ type = 'int'; required = $false; default = '1'; description = 'Max. 500.' }; parentRef = @{ type = 'ref'; required = $false; default = 'gleicher Parent'; description = '' }; offset = @{ type = '{x,y,z}'; required = $false; default = '0'; description = 'Versatz pro Kopie.' }; rotateStep = @{ type = 'number'; required = $false; default = '0'; description = 'Y-Drehung pro Kopie (Grad).' }; nameTemplate = @{ type = 'string'; required = $false; default = 'null'; description = 'z.B. "Crate{n}".' } };
            returns = '{ clones: [...], count, source, geometry }';
            example = @{ ref = '#42'; count = 60; offset = @{ x = 6; y = 0; z = 0 }; nameTemplate = 'Crate{n}' };
            errors = @('REF_NOT_FOUND', 'BAD_ARGS: max. 500 Kopien pro Call.') })
        $t.Add(@{ name = 'delete_instance'; category = 'create'; summary = 'Ein Objekt loeschen.';
            params = @{ ref = @{ type = 'ref'; required = $true; default = '-'; description = '' } };
            returns = '{ deleted: { id, name, className, path } }';
            example = @{ ref = '#42' };
            errors = @('REF_NOT_FOUND') })
        $t.Add(@{ name = 'bulk_delete'; category = 'create'; summary = 'Viele Objekte loeschen.';
            params = @{ refs = @{ type = 'ref[] | Selektoren'; required = $true; default = '-'; description = 'Ids UND Selektoren wie {tag="Wall"}.' } };
            returns = '{ deleted: [...], count, errors }';
            example = @{ refs = @('#42','#43','#44') };
            errors = @('REF_NOT_FOUND') })
        $t.Add(@{ name = 'rename_instance'; category = 'create'; summary = 'Umbenennen.';
            params = @{ ref = @{ type = 'ref'; required = $true; default = '-'; description = '' }; name = @{ type = 'string'; required = $true; default = '-'; description = '' } };
            returns = '{ id, name, className, path }';
            example = @{ ref = '#42'; name = 'NewName' };
            errors = @('REF_NOT_FOUND') })
        $t.Add(@{ name = 'move_instance'; category = 'create'; summary = 'Reparenten.';
            params = @{ refs = @{ type = 'ref[]'; required = $true; default = '-'; description = '' }; parentRef = @{ type = 'ref'; required = $true; default = '-'; description = 'Neuer Parent.' } };
            returns = '{ moved: [...], parent, errors }';
            example = @{ refs = @('#42'); parentRef = 'game.ReplicatedStorage' };
            errors = @('REF_NOT_FOUND') })
        $t.Add(@{ name = 'group_instances'; category = 'create'; summary = 'In Model/Folder gruppieren.';
            params = @{ refs = @{ type = 'ref[] | Selektoren'; required = $true; default = '-'; description = '' }; name = @{ type = 'string'; required = $false; default = "'Group'"; description = '' }; className = @{ type = "'Model'|'Folder'"; required = $false; default = "'Model'"; description = '' }; parentRef = @{ type = 'ref'; required = $false; default = 'Parent des ersten'; description = '' } };
            returns = '{ group: { id, name, className, path }, count }';
            example = @{ refs = @('#42','#43'); name = 'House'; className = 'Model' };
            errors = @('REF_NOT_FOUND') })
        $t.Add(@{ name = 'ungroup'; category = 'create'; summary = 'Model aufloesen, Kinder behalten.';
            params = @{ ref = @{ type = 'ref'; required = $true; default = '-'; description = 'Das Model.' } };
            returns = '{ moved: [...], count }';
            example = @{ ref = '#50' };
            errors = @('REF_NOT_FOUND') })

        # ---------------- PROPERTIES ----------------
        $t.Add(@{ name = 'set_property'; category = 'properties'; summary = 'Eine Eigenschaft an 1..n Objekten.';
            description = 'Versteht Kurzformen: Material="Neon", Color={255,0,0}, "#FF0000", Enums als Text.';
            params = @{ refs = @{ type = 'ref[] | Selektoren'; required = $true; default = '-'; description = '' }; property = @{ type = 'string'; required = $true; default = '-'; description = 'z.B. Anchored, Transparency, Material.' }; value = @{ type = 'any'; required = $true; default = '-'; description = 'Typ passend zur Eigenschaft (auch Kurzformen).' } };
            returns = '{ changed: [...], count, property, errors }';
            example = @{ refs = @('#42','#43'); property = 'Anchored'; value = $true };
            errors = @('REF_NOT_FOUND', 'RUNTIME_ERROR: Wert passt nicht zum Typ der Eigenschaft.') })
        $t.Add(@{ name = 'set_properties'; category = 'properties'; summary = 'Mehrere Eigenschaften an 1..n Objekten.';
            params = @{ refs = @{ type = 'ref[] | Selektoren'; required = $true; default = '-'; description = '' }; properties = @{ type = 'table'; required = $true; default = '-'; description = '{ Material="Neon", Color={255,80,0}, Transparency=0.3 }' } };
            returns = '{ changed: [...], count, errors }';
            example = @{ ref = '#42'; properties = @{ Material = 'Neon'; Color = @(255, 80, 0) } };
            errors = @('REF_NOT_FOUND') })
        $t.Add(@{ name = 'bulk_set_properties'; category = 'properties'; summary = 'UNTERSCHIEDLICHE Eigenschaften fuer viele Objekte.';
            description = 'Ein Eintrag pro Ziel - jedes mit seinen eigenen Werten. refs koennen Selektoren sein: { tag="Door" } trifft alle Tueren.';
            params = @{ items = @{ type = 'array of { ref|Selektor, properties }'; required = $true; default = '-'; description = '' } };
            returns = '{ changed: [...], count, errors }';
            example = @{ items = @(@{ ref = @{ tag = 'Door' }; properties = @{ Transparency = 0.5 } }, @{ ref = '#42'; properties = @{ Material = 'Neon' } }) };
            errors = @('REF_NOT_FOUND') })
        $t.Add(@{ name = 'set_attribute'; category = 'properties'; summary = 'Attribut setzen.';
            params = @{ refs = @{ type = 'ref[]'; required = $true; default = '-'; description = '' }; name = @{ type = 'string'; required = $true; default = '-'; description = '' }; value = @{ type = 'any'; required = $true; default = '-'; description = 'number/string/bool/Vector3.' } };
            returns = '{ count, attribute, errors }';
            example = @{ refs = @('#42'); name = 'Speed'; value = 16 };
            errors = @('REF_NOT_FOUND') })
        $t.Add(@{ name = 'add_tag'; category = 'properties'; summary = 'CollectionService-Tag.';
            params = @{ refs = @{ type = 'ref[]'; required = $true; default = '-'; description = '' }; tag = @{ type = 'string'; required = $true; default = '-'; description = '' } };
            returns = '{ count, tag }';
            example = @{ refs = @('#42'); tag = 'Door' };
            errors = @() })
        $t.Add(@{ name = 'remove_tag'; category = 'properties'; summary = 'Tag entfernen.';
            params = @{ refs = @{ type = 'ref[]'; required = $true; default = '-'; description = '' }; tag = @{ type = 'string'; required = $true; default = '-'; description = '' } };
            returns = '{ count, tag }';
            example = @{ refs = @('#42'); tag = 'Door' };
            errors = @() })

        # ---------------- SCRIPTS ----------------
        $t.Add(@{ name = 'get_script'; category = 'scripts'; summary = 'Quelltext mit Zeilen + Hash.';
            description = 'Liest ein Skript mit Zeilennummern, Gesamthaenge und Hash. Den Hash als expectHash an patch/set_script_source rueckgeben, damit niemand dazwischen aendert.';
            params = @{ ref = @{ type = 'ref'; required = $true; default = '-'; description = 'Script/LocalScript/ModuleScript.' }; startLine = @{ type = 'int'; required = $false; default = '1'; description = '' }; endLine = @{ type = 'int'; required = $false; default = 'Ende'; description = '' }; withLineNumbers = @{ type = 'bool'; required = $false; default = 'true'; description = '' } };
            returns = '{ id, path, className, totalLines, totalBytes, startLine, endLine, hash, source }';
            example = @{ ref = '#77'; startLine = 1; endLine = 200 };
            errors = @('REF_NOT_FOUND', 'BAD_ARGS: kein Skript.') })
        $t.Add(@{ name = 'find_in_script'; category = 'scripts'; summary = 'Ausschnitt im Skript finden.';
            params = @{ ref = @{ type = 'ref'; required = $true; default = '-'; description = '' }; query = @{ type = 'string'; required = $true; default = '-'; description = 'Text oder (regex=true) Lua-Pattern.' }; regex = @{ type = 'bool'; required = $false; default = 'false'; description = '' }; contextLines = @{ type = 'int'; required = $false; default = '2'; description = 'Zeilen drumherum.' }; limit = @{ type = 'int'; required = $false; default = '40'; description = '' } };
            returns = '{ matches: [ { line, offset, preview } ], count, totalLines, hash }';
            example = @{ ref = '#77'; query = 'WalkSpeed' };
            errors = @('REF_NOT_FOUND') })
        $t.Add(@{ name = 'patch_script'; category = 'scripts'; summary = 'Punktgenaue Aenderungen (DAS Standardwerkzeug).';
            description = 'NUR die betroffene Stelle wird ersetzt - nie die ganze Datei. Mehrere Edits pro Call, in Reihenfolge angewendet. Zweideutige Snippets werden abgelehnt (mit allen Trefferzeilen). dryRun=true zeigt vorher, was passiert.';
            params = @{ ref = @{ type = 'ref'; required = $true; default = '-'; description = '' }; edits = @{ type = 'array'; required = $true; default = '-'; description = 'Liste von Edit-Objekten (siehe ops).' }; expectHash = @{ type = 'string'; required = $false; default = 'null'; description = 'Hash aus get_script - Schutz vor Ueberschreiben.' }; dryRun = @{ type = 'bool'; required = $false; default = 'false'; description = 'Nur zeigen, nicht aendern.' } };
            returns = '{ id, path, operations: [ { op, line, ... } ], oldLines, newLines, bytes, hash, preview } - bei dryRun: { dryRun, wouldChange, operations, preview }';
            example = @{ ref = '#77'; edits = @(@{ op = 'replace'; find = 'WalkSpeed = 16'; replace = 'WalkSpeed = 24' }, @{ op = 'insertAfter'; find = 'local function onJoin()'; text = 'print("join")' }) };
            errors = @('REF_NOT_FOUND', 'BAD_ARGS: Text nicht gefunden / zweideutig (alle Trefferzeilen stehen im Fehler) / unbekannte op.') })
        $t.Add(@{ name = 'set_script_source'; category = 'scripts'; summary = 'GANZEN Quelltext ersetzen (fuer neue/kleine Dateien).';
            description = 'Existiert noch, aber fuer grosse Dateien ist patch_script ueberlegener. Fuer > 50 KB vorher upload_text + sourceRef.';
            params = @{ ref = @{ type = 'ref'; required = $true; default = '-'; description = '' }; source = @{ type = 'string'; required = $false; default = "''"; description = 'Volle neue Quelle (unverändert übernommen - kein String-Schneidwerk, keine %-Kollisionen).' }; sourceRef = @{ type = 'string'; required = $false; default = 'null'; description = 'uploadId aus upload_text.' }; expectHash = @{ type = 'string'; required = $false; default = 'null'; description = '' } };
            returns = '{ id, path, bytes, lines, previousBytes, hash }';
            example = @{ ref = '#77'; source = 'print("hi")' };
            errors = @('REF_NOT_FOUND', 'RUNTIME_ERROR: Hash-Mismatch (Skript wurde zwischendurch geaendert).') })
        $t.Add(@{ name = 'insert_script'; category = 'scripts'; summary = 'Neues Script/LocalScript/ModuleScript.';
            description = 'Erzeugt ein Skript mit Quelle. ModuleScripte einfach mit "return M" am Ende beenden - die Bridge greift in den Text NICHT ein.';
            params = @{ parentRef = @{ type = 'ref'; required = $false; default = "'game.ServerScriptService'"; description = '' }; className = @{ type = "'Script'|'LocalScript'|'ModuleScript'"; required = $false; default = "'Script'"; description = '' }; name = @{ type = 'string'; required = $false; default = 'className'; description = '' }; source = @{ type = 'string'; required = $false; default = "''"; description = 'Oder sourceRef.' }; sourceRef = @{ type = 'string'; required = $false; default = 'null'; description = 'uploadId.' }; properties = @{ type = 'table'; required = $false; default = '{}'; description = 'z.B. { Disabled=false }.' } };
            returns = '{ id, path, className, lines, hash }';
            example = @{ parentRef = 'game.ServerScriptService'; className = 'Script'; name = 'Main'; source = 'print("hi")' };
            errors = @('REF_NOT_FOUND', 'BAD_ARGS: className ohne Source-Eigenschaft.') })
        $t.Add(@{ name = 'bulk_insert_scripts'; category = 'scripts'; summary = 'Mehrere Skripte in einem Call.';
            params = @{ items = @{ type = 'array'; required = $true; default = '-'; description = 'Wie insert_script: [ { parentRef, className, name, source }, ... ].' } };
            returns = '{ created: [...], count, errors }';
            example = @{ items = @(@{ parentRef = 'game.ServerScriptService'; name = 'A'; source = '-- a' }, @{ parentRef = 'game.ServerScriptService'; name = 'B'; source = '-- b' }) };
            errors = @() })
        $t.Add(@{ name = 'compile_check'; category = 'scripts'; summary = 'Syntax pruefen, OHNE auszufuehren.';
            description = 'Lädt den Code nur zum Kompilieren. Damit ist COMPILE_ERROR bekannt, BEVOR das Skript laeuft - und es ist kein "Raten und Abwarten" mehr.';
            params = @{ source = @{ type = 'string'; required = $true; default = '-'; description = 'Oder sourceRef.' }; name = @{ type = 'string'; required = $false; default = "'@arena_check'"; description = 'Name im Fehler.' } };
            returns = '{ ok=true, compilable=true } oder { ok=false, code="COMPILE_ERROR", error, line }';
            example = @{ source = 'local x = 1 + ' };
            errors = @('COMPILE_ERROR: mit Zeilennummer.') })
        $t.Add(@{ name = 'run_lua'; category = 'scripts'; summary = 'Lua im Server-/Edit-Kontext ausfuehren (persistent!).';
            description = 'Fuehrt Lua aus und gibt Rueckgabe + alles, was gedruckt wurde, zurueck. WICHTIG: Die Umgebung ist PERSISTENT - ein Helfer aus einem frueheren Call (z.B. "M = {...}" ohne local) ist im naechsten Call weiter da (lua_state zeigt alle persiste Variablen). Fuer Läufe ueber 60s: asJob=true oder start_job.';
            params = @{ source = @{ type = 'string'; required = $true; default = '-'; description = 'Oder sourceRef.' }; context = @{ type = "'server'|'auto'"; required = $false; default = "'auto'"; description = 'client ist NICHT moeglich (loadstring gesperrt) - fuer den Client: client_action/gui_*/move_character/send_input.' }; asJob = @{ type = 'bool'; required = $false; default = 'false'; description = 'Im Hintergrund als Job laufen lassen (rueckgibt jobId).' } };
            returns = '{ returned, output: [ { seq, message, type } ], context, environment="persistent", persistentKeys } oder (asJob) { ok, jobId, status="running" }';
            example = @{ source = 'local p = workspace:FindFirstChild("Part"); return p and p.Position' };
            errors = @('COMPILE_ERROR: Syntax (Zeile im Fehler).', 'RUNTIME_ERROR: Laufzeit (Mitteilung + Output).', 'NO_PLAYER / PLAY_NOT_RUNNING: falscher Kontext.') })
        $t.Add(@{ name = 'lua_state'; category = 'scripts'; summary = 'Was lebt in der persistenten Lua-Umgebung?';
            params = @{};
            returns = '{ keys: [ "M", "helpers", ... ], count, jobs: [ { id, name, status } ] }';
            example = @{};
            errors = @() })
        $t.Add(@{ name = 'clear_lua_state'; category = 'scripts'; summary = 'Persistente Variablen + Jobs zuruecksetzen.';
            params = @{ confirm = @{ type = 'bool'; required = $true; default = '-'; description = 'Muss true sein.' } };
            returns = '{ cleared = true }';
            example = @{ confirm = $true };
            errors = @() })

        # ---------------- FILL (Voxel/Geometrie aufmassen + fuellen) ----------------
        $t.Add(@{ name = 'probe_world'; category = 'fill'; summary = 'WELT MESSEN: Raster-Schritt, Wasserhoehe, Füllhöhen-Regel.';
            description = 'Raycast-Raster ueber den Boden (nie Index-Rechnung!), bestimmt den Raster-Schritt (z.B. 4 Studs), die Wasserhoehe und prüft die Füllhöhen-Regel gegen die gemessenen Oberflächen. Das Ergebnis (worldProfile) wird gespeichert und von fill_region verwandt. Nach grossen Terrain-Änderungen erneut aufrufen.';
            params = @{ center = @{ type = '{x,y,z}'; required = $false; default = '{0,0,0}'; description = 'Mittelpunkt der Messung.' }; radius = @{ type = 'number'; required = $false; default = '40'; description = 'Messradius (Studs).' }; step = @{ type = 'number'; required = $false; default = '10'; description = 'Rasterabstand der Messpunkte.' } };
            returns = '{ measuredAt, center, radius, sampleCount, gridStep, waterY, heights: [...], fillRule: { formula, matched, samples }, stored = true }';
            example = @{ center = @{ x = 0; y = 0; z = 0 }; radius = 40 };
            errors = @('BAD_ARGS: zu wenige Messpunkte gefunden (leerer Place?).') })
        $t.Add(@{ name = 'fill_region'; category = 'fill'; summary = 'Bereich fuellen - nach GEMESSENER Regel, in Chunks, resume-fähig.';
            description = 'Fuellt eine Box aus Gitterzellen (gridStep) mit Air oder einem Teil-Template. Zielhoehe: explizite Zahl, "rule" (Fuehlhoehe-Regel aus probe_world: frisch y1 wenn durch gridStep teilbar, sonst ceil(y1/gridStep)*gridStep+2; Wasser y1-2) oder "top" (bis max.Y). TIEFER ueberschreiben geht NICHT stillschweigend: wird erst mit Air geleert (clearBelowFirst, nur mit confirmClear=true, sonst Spalten = skippedNeedClear). Laeuft in kleinen Chunks mit Fortschritt; bei Abbruch: gleiches resumeToken zurueckgeben = WITTERMACHEN, nicht von vorn. Jeder Zellfehler betrifft nur diese Zelle (failedCells).';
            params = @{ min = @{ type = '{x,y,z}'; required = $true; default = '-'; description = 'Untere Ecke der Box.' }; max = @{ type = '{x,y,z}'; required = $true; default = '-'; description = 'Obere Ecke.' }; with = @{ type = "'Air' | { className, properties, name }"; required = $false; default = "'Air'"; description = "'Air' loescht Zellen (Raum freimachen). Template legt Teile." }; gridStep = @{ type = 'number'; required = $false; default = 'worldProfile.gridStep'; description = 'Zellgroesse. Ohne probe_world wird NICHT geraten (Fehler WORLD_NOT_PROBED).' }; fillTo = @{ type = 'number | "rule" | "top"'; required = $false; default = "'rule'"; description = 'Zielhoehe der Saeule.' }; fillFrom = @{ type = 'number'; required = $false; default = 'min.Y'; description = 'Untergrenze des Fuellens.' }; clearBelowFirst = @{ type = 'bool'; required = $false; default = 'true'; description = 'Saeulen, die tiefer fuellen muessen, erst mit Air leeren.' }; confirmClear = @{ type = 'bool'; required = $false; default = 'false'; description = 'OHNE true werden Saeulen mit existing parts nur als skippedNeedClear gemeldet, nichts wird geloescht.' }; chunkBudget = @{ type = 'int'; required = $false; default = '200'; description = 'Zellen pro Chunk (konservativ; Job meldet partsPerSecond).' }; resumeToken = @{ type = 'table'; required = $false; default = 'null'; description = 'Aus dem letzten (abgebrochenen) Ergebnis - naemlicher Aufruf damit = weitermachen.' }; stopOnError = @{ type = 'bool'; required = $false; default = 'false'; description = 'Bei Zellfehler anhalten.' }; asJob = @{ type = 'bool'; required = $false; default = 'false'; description = 'EMPFOEHLEN bei > 150 Zellen: true.' } };
            returns = '{ created, cleared, skippedExisting, skippedNeedClear, failedCells: [ { x, y, z, error } ], totalColumns, chunks, partsPerSecond, geometry: { ready, frames }, resumeToken (null = fertig), usedProfile: { gridStep, fillRule } }';
            example = @{ min = @{ x = -20; y = -10; z = -20 }; max = @{ x = 20; y = 10; z = 20 }; with = @{ className = 'Part'; properties = @{ Anchored = $true }; name = 'Fill' }; fillTo = 'rule'; asJob = $true };
            errors = @('WORLD_NOT_PROBED: probe_world zuerst.', 'REGION_LIMIT: Box zu gross - kleiner aufteilen (empirische Obergrenze im Fehler).', 'BAD_ARGS: min/max fehlt.') })

        # ---------------- UNION / CSG ----------------
        $t.Add(@{ name = 'union'; category = 'union'; summary = 'Teile zu EINEM Teil verschmelzen (mit Vorpruefung und Budget).';
            description = 'Mergt BaseParts zu einem PartOperation. VORPRUEFUNG: alle BaseParts, anchored, gleicher Parent, Größe; Komplexitaets-Budget (Dreiecke geschätzt) mit Warnung und konkretem Vorschlag (z.B. "einen Part statt 40"). Vorher wird automatisch ein Undo-Punkt gesetzt (undoPoint). Roblox-Verweigerung kommt als SOLID_REFUSED mit Roblox-Ursache und Tipps. groups=... verarbeitet mehrere Gruppen in einem Call.';
            params = @{ refs = @{ type = 'ref[]'; required = $false; default = 'null'; description = 'Die zu mergenden Teile (min. 2). (alternativ groups)' }; groups = @{ type = 'array of { refs, name?, keepOriginals?, ... }'; required = $false; default = 'null'; description = 'Batch: mehrere Unions in einem Call.' }; name = @{ type = 'string'; required = $false; default = "'Union'"; description = 'Name des Ergebnisses.' }; parentRef = @{ type = 'ref'; required = $false; default = 'Parent des ersten'; description = '' }; keepOriginals = @{ type = 'bool'; required = $false; default = 'false'; description = 'Originalteile behalten (liegen unsichtbar im Ergebnis).' }; collisionFidelity = @{ type = "'Default'|'Fast'|'Extreme'"; required = $false; default = "'Default'"; description = '' }; renderFidelity = @{ type = "'Automatic'|'Fast'|'Extreme'"; required = $false; default = "'Automatic'"; description = '' }; force = @{ type = 'bool'; required = $false; default = 'false'; description = 'Harte Obergrenzen (24 Teile / Dreiecksbudget) ueberschreiben.' }; fixAnchored = @{ type = 'bool'; required = $false; default = 'false'; description = 'Nicht anker Teile vorher ankeren.' }; undoPoint = @{ type = 'bool'; required = $false; default = 'true'; description = 'Undo-Punkt "vor Union <name>" setzen ( Rueckgaengig-Machen als eigener Schritt: 1x undo).' } };
            returns = '{ result: { id, name, ... }, partsUsed, bounds, triangleEstimate, undoPoint, canBeUndone } oder (groups) { results: [...], count }';
            example = @{ refs = @('#42','#43'); name = 'Wall'; collisionFidelity = 'Default' };
            errors = @('UNION_BUDGET: zu viele Teile/zugleich - kleiner gruppieren oder force=true.', 'UNION_COSTLY (Warning): Komplexitaet hoch - Vorschlag im Feld suggestion (z.B. ein einziger Part).', 'SOLID_REFUSED: Roblox hat abgelehnt (robloxMessage + hints), nichts wurde geaendert.', 'REF_NOT_FOUND', 'UNION_PRECHECK (Warning): nicht anker / verschiedene Parente - Liste im Fehlerfeld.') })
        $t.Add(@{ name = 'subtract'; category = 'union'; summary = 'Form aus einem Teil herausstechen.';
            description = 'baseRef minus negativeRefs. Die Negativteile MUSSSEN sich ueberschneiden, sonst lehnt Roblox ab (SOLID_REFUSED). Vorher mit overlap_check pruefen.';
            params = @{ baseRef = @{ type = 'ref'; required = $true; default = '-'; description = 'Das Teil, das behalten wird.' }; negativeRefs = @{ type = 'ref[]'; required = $true; default = '-'; description = 'Die Form(en), die herauskommen.' }; name = @{ type = 'string'; required = $false; default = "'SubtractResult'"; description = '' }; keepOriginals = @{ type = 'bool'; required = $false; default = 'false'; description = '' }; force = @{ type = 'bool'; required = $false; default = 'false'; description = '' }; undoPoint = @{ type = 'bool'; required = $false; default = 'true'; description = '' } };
            returns = '{ result, partsUsed, bounds, triangleEstimate, undoPoint }';
            example = @{ baseRef = '#42'; negativeRefs = @('#43'); name = 'WallWithDoor' };
            errors = @('SOLID_REFUSED: Negativteil ueberschneidet das Basis-Teil nicht (overlap_check pruefen!).', 'UNION_BUDGET', 'REF_NOT_FOUND') })
        $t.Add(@{ name = 'intersect'; category = 'union'; summary = 'Nur den gemeinsamen Teil behalten.';
            params = @{ refs = @{ type = 'ref[]'; required = $true; default = '-'; description = 'min. 2, muessen sich ueberschneiden.' }; name = @{ type = 'string'; required = $false; default = "'Intersection'"; description = '' }; keepOriginals = @{ type = 'bool'; required = $false; default = 'false'; description = '' }; force = @{ type = 'bool'; required = $false; default = 'false'; description = '' }; undoPoint = @{ type = 'bool'; required = $false; default = 'true'; description = '' } };
            returns = '{ result, partsUsed, bounds, triangleEstimate, undoPoint }';
            example = @{ refs = @('#42','#43') };
            errors = @('SOLID_REFUSED: keine Ueberschneidung.', 'REF_NOT_FOUND') })
        $t.Add(@{ name = 'separate'; category = 'union'; summary = 'Union wieder in Teile zerlegen.';
            description = 'Das "Rueckgaengig-machen" von union/subtract/intersect: das Ergebnis wird wieder zu normalen, editierbaren Teilen (Farben sind danach nicht mehr garantiet).';
            params = @{ ref = @{ type = 'ref'; required = $true; default = '-'; description = 'Das PartOperation.' } };
            returns = '{ pieces: [ { id, name, className, path } ], count }';
            example = @{ ref = '#50' };
            errors = @('BAD_ARGS: kein PartOperation.', 'SOLID_REFUSED: SeparateAsync fehlgeschlagen.') })
        $t.Add(@{ name = 'union_info'; category = 'union'; summary = 'Ist das eine Union? Wie komplex?';
            params = @{ ref = @{ type = 'ref'; required = $true; default = '-'; description = '' } };
            returns = '{ instance, isUnion, collisionFidelity, renderFidelity, triangleEstimate, bounds, performance, advice }';
            example = @{ ref = '#50' };
            errors = @('REF_NOT_FOUND') })

        # ---------------- ASSETS ----------------
        $t.Add(@{ name = 'search_assets'; category = 'assets'; summary = 'Katalogsuche (zouverlaessig, mit Cache).';
            description = 'Sucht im Roblox-Katalog. Typen: audio, music, decal, image, texture, mesh, model (GESPERRT ohne allowModels=true), video, animation. WICHTIG: image/texture werden als DECALs durchgesucht (Katalog-API hat keine "image"-Suche), mesh als MESHPART - die Antwort erklärt das (typeNote). Ergebnisse werden lokal gecacht (cached=true bei Treffer). Wenn der Katalog nicht erreichbar ist: code CATALOG_UNAVAILABLE mit klarem Protokoll ("Katalog nicht verfuegbar -> prozedual bauen") - NICHT schweigen.';
            params = @{ type = @{ type = 'string'; required = $false; default = "'audio'"; description = 'audio, music, decal, image, texture, mesh, model, video, animation.' }; query = @{ type = 'string'; required = $true; default = '-'; description = 'Suchbegriff (englisch funktioniert am besten).' }; limit = @{ type = 'int'; required = $false; default = '20'; description = 'max 50.' }; page = @{ type = 'int'; required = $false; default = '0'; description = '' }; sortType = @{ type = 'int'; required = $false; default = '0'; description = '0 Relevanz, 1 Favoriten, 3 Neuere, 4/5 Preis.' }; allowModels = @{ type = 'bool'; required = $false; default = 'false'; description = 'Free Models freigeben (unempfohlen - versteckte Skripte).' }; refresh = @{ type = 'bool'; required = $false; default = 'false'; description = 'Cache umgehen.' } };
            returns = '{ assets: [ { assetId, name, typeId, typeName, useAs="rbxassetid://...", hasScripts, creator, ... } ], count, type, apiType, typeNote, note, cached, totalResults }';
            example = @{ type = 'audio'; query = 'door creak'; limit = 10 };
            errors = @('ASSET_BLOCKED: model ohne allowModels.', 'CATALOG_UNAVAILABLE: Katalog nicht erreichbar - sagen Sie dem Nutzer es klar und bauen Sie prozedual.', 'CATALOG_TYPE_NOT_SUPPORTED: unbekannter Typ.') })
        $t.Add(@{ name = 'asset_details'; category = 'assets'; summary = 'Details zu Asset-Ids (gecacht).';
            params = @{ assetIds = @{ type = 'number[]'; required = $true; default = '-'; description = 'Oder assetId.' } };
            returns = '{ assets: [ { asset: {...}, creator: {...} } ], unknownAssets? (404-Ids klar gemeldet) }';
            example = @{ assetIds = @(1234567) };
            errors = @('CATALOG_UNAVAILABLE', 'ASSET_NOT_FOUND (als unknownAssets mit Hinweis).') })
        $t.Add(@{ name = 'validate_asset'; category = 'assets'; summary = 'Passt die Id wirklich zum Typ? (BEVOR eingebaut.)';
            description = 'Prüft eine Asset-Id gegen den Katalog: existiert sie? Welcher Typ? Passt sie zum erwarteten Typ? Das ist der Schutz gegen rbxassetid://9046578614 als Audio - das waere sonst erst Laufzeitfehler geworden.';
            params = @{ assetId = @{ type = 'number'; required = $true; default = '-'; description = '' }; expectType = @{ type = 'string'; required = $false; default = "''"; description = 'audio, image, texture, decal, mesh, model, animation, video.' } };
            returns = '{ verified, assetId, assetName, typeId, typeName, usableAs, hasScripts, creator, matchesExpect, note }';
            example = @{ assetId = 1838833093; expectType = 'audio' };
            errors = @('ASSET_NOT_FOUND: Id existiert nicht / ist nicht oeffentlich - NICHT verwenden.', 'CATALOG_UNAVAILABLE: konnte nicht verifiziert werden (verified=false) - Anwenden erlaubt, aber mit Risiko.') })
        $t.Add(@{ name = 'insert_asset'; category = 'assets'; summary = 'Mesh/Model/MeshPart in den Place einfuegen.';
            description = 'Lädt das Asset in den Place. Wird VORHER automatisch validiert (Typ + Skript-Pruefung: ASSET_HAS_SCRIPTS). unpack=true zerlegt das Model in seine Kinder.';
            params = @{ assetId = @{ type = 'number'; required = $true; default = '-'; description = '' }; parentRef = @{ type = 'ref'; required = $false; default = "'game.Workspace'"; description = '' }; unpack = @{ type = 'bool'; required = $false; default = 'true'; description = 'Model zerlegen.' }; name = @{ type = 'string'; required = $false; default = 'null'; description = 'Name (bei unpack).' }; acceptScripts = @{ type = 'bool'; required = $false; default = 'false'; description = 'Skripte im Asset akzeptieren (gefahr! pruefen danach).' }; skipValidation = @{ type = 'bool'; required = $false; default = 'false'; description = 'Tyvalidierung ueberspringen (nur im Notfall).' } };
            returns = '{ inserted: [ { id, name, className, path } ], assetId, count }';
            example = @{ assetId = 1234567; parentRef = 'game.Workspace' };
            errors = @('ASSET_TYPE_MISMATCH: Id passt nicht zu Model/Mesh (actual.typeName wird gemeldet).', 'ASSET_NOT_FOUND', 'ASSET_HAS_SCRIPTS: enthält Skripte - acceptScripts=true nur mit Vorsicht.', 'CATALOG_UNAVAILABLE.') })
        $t.Add(@{ name = 'apply_asset'; category = 'assets'; summary = 'Asset auf Objekt legen (eigenschaft automatisch).';
            description = 'Setzt Texture/SoundId/Image/MeshId automatisch passend zur Zielklasse - und validiert VORHER, dass die Id wirklich zum Typ passt (ASSET_TYPE_MISMATCH, sonst nie eingebaut).';
            params = @{ refs = @{ type = 'ref[]'; required = $true; default = '-'; description = 'Decal, Texture, Sound, ImageLabel, SpecialMesh, MeshPart, Animation.' }; assetId = @{ type = 'number'; required = $true; default = '-'; description = '' }; property = @{ type = 'string'; required = $false; default = 'auto'; description = 'Nur wenn Auto nicht geht: Texture/SoundId/Image/MeshId/AnimationId.' }; skipValidation = @{ type = 'bool'; required = $false; default = 'false'; description = '' } };
            returns = '{ applied: [ { instance, property, value } ], count, errors }';
            example = @{ refs = @('#42'); assetId = 1234567 };
            errors = @('ASSET_TYPE_MISMATCH: Id ist z.B. ein Decal, aber Sound erwartet - nichts wurde gesetzt.', 'ASSET_NOT_FOUND', 'REF_NOT_FOUND', 'CATALOG_UNAVAILABLE (Warning im Ergebnis: unverifiziert).') })
        $t.Add(@{ name = 'catalog_status'; category = 'assets'; summary = 'Ist der Katalog gerade erreichbar?';
            description = 'Billiger Test (eine bekannte Id abfragen). Vor Asset-Arbeit gut fragen - und wenn catalogAvailable=false: dem Nutzer klar sagen "Katalog nicht verfuegbar" und prozedual bauen.';
            params = @{};
            returns = '{ catalogAvailable, latencyMs }';
            example = @{};
            errors = @() })

        # ---------------- OUTPUT ----------------
        $t.Add(@{ name = 'get_output'; category = 'output'; summary = 'Ausgabefenster lesen (Edit+Server+Client).';
            description = 'Zeilen seit dem letzten Cursor, filterbar (Text/Regex/Typen). "since" = cursor aus dem letzten Call, dann kommen nur NEUE Zeilen.';
            params = @{ limit = @{ type = 'int'; required = $false; default = '200'; description = 'max 2000.' }; since = @{ type = 'int'; required = $false; default = '0'; description = 'Cursor (cursor aus vorigem Call).' }; filter = @{ type = 'string'; required = $false; default = "''"; description = 'Teilstring (lowercase) oder Pattern bei regex=true.' }; regex = @{ type = 'bool'; required = $false; default = 'false'; description = '' }; types = @{ type = 'string[]'; required = $false; default = 'all'; description = 'z.B. ["MessageError","MessageWarning","Output"].' }; onlyErrors = @{ type = 'bool'; required = $false; default = 'false'; description = '' } };
            returns = '{ lines: [ { seq, time, message, type, source } ], returned, matched, cursor, errorCount, warningCount }';
            example = @{ since = 1234; limit = 100; filter = 'error' };
            errors = @() })
        $t.Add(@{ name = 'wait_for_output'; category = 'output'; summary = 'Bis eine Zeile erscheint warten.';
            description = 'Ideal nach play_start oder run_lua: blockiert im Studio, bis ein Muster auftaucht (oder die Zeit abgelaufen ist).';
            params = @{ pattern = @{ type = 'string'; required = $true; default = '-'; description = 'Suchtext.' }; timeoutSeconds = @{ type = 'number'; required = $false; default = '15'; description = 'max 110.' }; since = @{ type = 'int'; required = $false; default = 'jetzt'; description = 'Ab welchem Cursor.' }; regex = @{ type = 'bool'; required = $false; default = 'false'; description = '' }; types = @{ type = 'string[]'; required = $false; default = 'all'; description = '' } };
            returns = '{ found, lines?, cursor, waited? }';
            example = @{ pattern = 'loaded'; timeoutSeconds = 20 };
            errors = @() })
        $t.Add(@{ name = 'clear_output'; category = 'output'; summary = 'Ausgabefenster leeren.';
            params = @{};
            returns = '{ cleared, cursor }';
            example = @{};
            errors = @() })
        $t.Add(@{ name = 'get_errors'; category = 'output'; summary = 'Nur Fehlerzeilen + Zaehler.';
            params = @{ limit = @{ type = 'int'; required = $false; default = '100'; description = '' }; since = @{ type = 'int'; required = $false; default = '0'; description = '' }; filter = @{ type = 'string'; required = $false; default = "''"; description = '' } };
            returns = '{ lines, returned, cursor, errorCount, warningCount, note (wenn leer) }';
            example = @{ limit = 50 };
            errors = @() })

        # ---------------- PLAY / TEST ----------------
        $t.Add(@{ name = 'play_status'; category = 'play'; summary = 'Läuft ein Test? Welcher? Ist ein Player da?';
            description = 'laufender Zustand: edit / run / play, Kontext, Player-Zahl, Player- + Charakter-Details, Client-Agent-Status, was grade vom BENUTZER passiert (Kamera, Avatar, GUI).';
            params = @{};
            returns = '{ running, mode, context, playerCount, modeInfo: { kind, hasPlayer, hasClient, explanation }, player: { name, character, clientAgent }, recentUserEvents }';
            example = @{};
            errors = @() })
        $t.Add(@{ name = 'play_start'; category = 'play'; summary = 'Test starten: mode="play" (echt, mit Player) oder "run" (nur Simulation).';
            description = 'WICHTIG VERSTEHEN: mode="play" = echtes Spiel: ein Test-Player mit Charakter, GUI und Client-Agent (dieser Call wartet, bis alles da ist - sonst PLAY_NO_PLAYER mit Diagnose). mode="run" = NUR Server-Skripte + Physik, KEIN Player, KEIN Charakter, KEIN Client, KEINE GUI - das ist NICHT kaputt, sondern genau so definiert; fuer Charakter/GUI-Tests IMMER "play" nehmen. Der Benutzer kann jederzeit selbst Play/Stop druocken - das kommt als Ereignis (play_started/play_stopped, startedBy="user").';
            params = @{ mode = @{ type = "'play'|'run'"; required = $false; default = "'play'"; description = '' } };
            returns = '{ state: { running, mode, context, playerCount }, modeInfo: { kind, hasPlayer, hasClient, explanation }, player? { name, character, clientAgent }, warnings }';
            example = @{ mode = 'play' };
            errors = @('PLAY_NO_PLAYER: Play-Modus aktiv, aber nach 20s kein Charakter (recentErrors mitgeliefert).', 'STUDIO_TIMEOUT: Studio hat nicht geantwortet (Fenster nicht fokussiert? Dialog offen?).', 'PLAY_FALLBACK_RUN (Warning): Shortcut nicht moeglich, Run-Modus statt Play.') })
        $t.Add(@{ name = 'play_stop'; category = 'play'; summary = 'Test stoppen (platz wird wiederhergestellt).';
            description = 'Stoppt ueber den echten Stopp-Knopf, damit der Place-Zustand von vorher zurueckkommt. Alle Aenderungen aus dem Test sind danach weg.';
            params = @{};
            returns = '{ state, warnings }';
            example = @{};
            errors = @('STUDIO_TIMEOUT: Studio stoppt nicht innerhalb 15s.') })
        $t.Add(@{ name = 'play_pause'; category = 'play'; summary = 'Simulation pausieren.';
            description = 'Bleibt stehen, aber laeuft weiter (State bleibt erhalten). Im Run-Modus nur Physik, im Play-Modus auch der Charakter.';
            params = @{};
            example = @{};
            returns = '{ paused, state }';
            errors = @('PLAY_NOT_RUNNING') })
        $t.Add(@{ name = 'play_resume'; category = 'play'; summary = 'Simulation fortsetzen.';
            description = 'Setzt eine pausierte Simulation (play_pause) wieder in Gang.';
            params = @{};
            example = @{};
            returns = '{ resumed, state }';
            errors = @() })
        $t.Add(@{ name = 'set_context'; category = 'play'; summary = 'Seite wechseln: server oder client.';
            description = 'Bestimmt, welche Seite Laufzeit-Werkzeuge (run_lua) treffen. run_lua selbst laeuft IMMER nur auf der Server/Seite - fuer den Client die client_-Werkzeuge.';
            params = @{ context = @{ type = "'server'|'client'"; required = $true; default = '-'; description = '' } };
            returns = '{ context, note }';
            example = @{ context = 'client' };
            errors = @('BAD_ARGS: context muss server oder client sein.') })
        $t.Add(@{ name = 'character_state'; category = 'play'; summary = 'Charakter: Position, Gesundheit, Zustand.';
            params = @{};
            returns = '{ hasCharacter, player, position, cframe, health, maxHealth, walkSpeed, jumpPower, state }';
            example = @{};
            errors = @('PLAY_NOT_RUNNING', 'NO_PLAYER: mode="run" hat keinen Charakter - play_start mit mode="play".') })
        $t.Add(@{ name = 'move_character'; category = 'play'; summary = 'Charakter gehen lassen (zum Punkt oder per Tasten).';
            description = 'position/targetRef: Humanoid.MoveTo (mit warten). keys=["W"]: echte Tasten. ACHTUNG: Der Benutzer kann den Charakter SELBST gleichzeitig bewegen - das kommt als Ereignis user_moving_character.';
            params = @{ position = @{ type = '{x,y,z}'; required = $false; default = 'null'; description = 'Ziel. (alternativ targetRef oder keys)' }; targetRef = @{ type = 'ref'; required = $false; default = 'null'; description = 'Objekt, zu dem gegangen wird.' }; keys = @{ type = 'string[]'; required = $false; default = 'null'; description = "z.B. ['W'] oder ['W','LeftShift']." }; duration = @{ type = 'number'; required = $false; default = '1'; description = 'Haltedauer der Tasten (s).' }; waitForArrival = @{ type = 'bool'; required = $false; default = 'true'; description = 'Bis zum Ziel warten.' }; timeoutSeconds = @{ type = 'number'; required = $false; default = '12'; description = '' } };
            returns = '{ reached, position, distanceLeft } oder { pressed, position } oder { moving }';
            example = @{ position = @{ x = 10; y = 5; z = 0 }; waitForArrival = $true };
            errors = @('PLAY_NOT_RUNNING', 'NO_PLAYER', 'BAD_ARGS: position, targetRef oder keys angeben.') })
        $t.Add(@{ name = 'teleport_character'; category = 'play'; summary = 'Charakter sofort setzen.';
            params = @{ position = @{ type = '{x,y,z}'; required = $false; default = 'null'; description = 'Oder targetRef.' }; targetRef = @{ type = 'ref'; required = $false; default = 'null'; description = 'Setzt 5 Studs ueber das Objekt.' } };
            returns = '{ position }';
            example = @{ targetRef = '#42' };
            errors = @('PLAY_NOT_RUNNING', 'NO_PLAYER', 'BAD_ARGS') })
        $t.Add(@{ name = 'respawn_character'; category = 'play'; summary = 'Charakter neu laden.';
            description = 'Killt und neu-spawnt den Test-Player (nach Crashes oder festgefahrenem Avatar). Nur im Play-Modus.';
            params = @{};
            example = @{};
            returns = '{ respawned }';
            errors = @('PLAY_NOT_RUNNING', 'NO_PLAYER') })
        $t.Add(@{ name = 'wait'; category = 'play'; summary = 'Im Place warten + Output mitlesen.';
            params = @{ seconds = @{ type = 'number'; required = $false; default = '1'; description = 'max 60.' } };
            returns = '{ waited, output: [...] }';
            example = @{ seconds = 2 };
            errors = @() })

        # ---------------- GUI / CLIENT ----------------
        $t.Add(@{ name = 'gui_dump'; category = 'gui'; summary = 'ALLE GUI-Elemente des Players.';
            description = 'Jedes GuiObject mit Position, Groesse, Text, Sichtbarkeit und Klickrarigkeit (viewport-Koordinaten, mit GUI-Inset korrigiert). Damit ist "wird mein HUD angezeigt?" endlich beantwortbar.';
            params = @{ limit = @{ type = 'int'; required = $false; default = '200'; description = 'max 600.' } };
            returns = '{ items: [ { name, className, path, text, visible, clickable, x, y, width, height, centerX, centerY } ] }';
            example = @{ limit = 100 };
            errors = @('PLAY_NOT_RUNNING: nur waehrend eines Tests.', 'NO_PLAYER', 'STUDIO_TIMEOUT: Client-Agent laedt noch.') })
        $t.Add(@{ name = 'gui_check'; category = 'gui'; summary = 'GUI-Test: Elemente finden + erwartete Werte pruefen.';
            description = 'Fuehrt gui_dump einmal aus und prueft jede Check: gefunden? sichtbar? Text richtig? Das ist der "erwartete Ergebnis"-Check fuer das GUI-Test-Harness. allPassed zusammenfaessend.';
            params = @{ checks = @{ type = 'array'; required = $true; default = '-'; description = '[ { query, expectVisible?, expectText?, expectTextContains?, expectMissing? } ].' }; limit = @{ type = 'int'; required = $false; default = '400'; description = '' } };
            returns = '{ checks: [ { query, found, element?, pass_visible?, pass_text?, passed, reason? } ], allPassed, guiCount }';
            example = @{ checks = @(@{ query = 'HealthBar'; expectVisible = $true }, @{ query = 'ScoreLabel'; expectTextContains = '100' }) };
            errors = @('PLAY_NOT_RUNNING', 'NO_PLAYER') })
        $t.Add(@{ name = 'gui_click'; category = 'gui'; summary = 'GUI-Element WIRKLICH anklicken (mit Ergebnis-Check).';
            description = 'Findet das Element (Name/Text/Pfad), schickt einen echten Maus-Klick in die Mitte und gibt die folgende Output-Zeilen zurueck. Mit expect=... wird NACH dem Klick automatisch geprueft, ob das erwartete Element/Text da ist (expectationMet).';
            params = @{ query = @{ type = 'string'; required = $true; default = '-'; description = 'Name/Text/Pfad-Ausschnitt des Elements.' }; holdSeconds = @{ type = 'number'; required = $false; default = '0.06'; description = 'Klick-Haltedauer.' }; settleSeconds = @{ type = 'number'; required = $false; default = '0.35'; description = 'Warten nach dem Klick.' }; expect = @{ type = '{ query, textContains?, text?, visible? }'; required = $false; default = 'null'; description = 'Erwartetes Ergebnis (wird geprueft).' }; waitSeconds = @{ type = 'number'; required = $false; default = '1.5'; description = 'Warten vor der Erwartungs-Pruefung.' } };
            returns = '{ clicked: { element... }, outputAfterClick, expectationMet?, expectation? }';
            example = @{ query = 'PlayButton'; expect = @{ query = 'ResultLabel'; textContains = 'Won' } };
            errors = @('PLAY_NOT_RUNNING', 'NO_PLAYER', 'REF_NOT_FOUND: Element nicht gefunden (gui_dump zeigt was da ist).', 'GUI_HIDDEN: Element nicht sichtbar.') })
        $t.Add(@{ name = 'gui_set_text'; category = 'gui'; summary = 'In ein TextBox schreiben.';
            params = @{ query = @{ type = 'string'; required = $true; default = '-'; description = '' }; text = @{ type = 'string'; required = $true; default = '-'; description = '' } };
            returns = '{ ok, path }';
            example = @{ query = 'NameBox'; text = 'Hello' };
            errors = @('PLAY_NOT_RUNNING', 'NO_PLAYER', 'REF_NOT_FOUND') })
        $t.Add(@{ name = 'send_input'; category = 'gui'; summary = 'Roh-Eingabe: Tasten + Maus.';
            description = 'Sendet echte Tastatur/Maus-Eingaben an den laufenden Test (VirtualInputManager). Der Client-Agent merkt sich die Fenster, damit nicht mit "User klickt" verwechselt wird.';
            params = @{ keys = @{ type = 'string[]'; required = $false; default = 'null'; description = 'z.B. ["Space"] oder [{key="W", duration=1, modifiers=["LeftShift"]}]' }; click = @{ type = '{ x, y, button?, hold? }'; required = $false; default = 'null'; description = 'Mausklick in Viewport-Koordinaten.' }; duration = @{ type = 'number'; required = $false; default = '0.1'; description = 'Standard-Haltedauer.' }; modifiers = @{ type = 'string[]'; required = $false; default = 'null'; description = '' }; settleSeconds = @{ type = 'number'; required = $false; default = '0.2'; description = '' } };
            returns = '{ sent: [ { key|click, ok, error? } ], output }';
            example = @{ keys = @('Space'); click = @{ x = 400; y = 300 } };
            errors = @('BAD_ARGS: keys oder click angeben.', 'RUNTIME_ERROR: VirtualInputManager nicht verfuegbar.') })
        $t.Add(@{ name = 'client_action'; category = 'gui'; summary = 'Niedrigebenen-Client-Zugriff.';
            description = 'Direkter Zugriff auf den Client-Agent: state (Player/Kamera/GUI-Inset), gui_dump, gui_find, set_text, move, jump, camera (position+lookAt), ping. Fuer alles, was gui_* nicht direkt abdeckt.';
            params = @{ action = @{ type = 'string'; required = $true; default = '-'; description = 'state, gui_dump, gui_find, set_text, move, jump, camera, ping.' }; args = @{ type = 'table'; required = $false; default = '{}'; description = 'z.B. camera: { position={x,y,z}, lookAt={x,y,z} }.' }; timeoutSeconds = @{ type = 'number'; required = $false; default = '8'; description = '' } };
            returns = 'abhaengig von action (immer ok=true + Inhalt)';
            example = @{ action = 'camera'; args = @{ position = @{ x = 0; y = 20; z = 30 }; lookAt = @{ x = 0; y = 5; z = 0 } } };
            errors = @('PLAY_NOT_RUNNING', 'NO_PLAYER', 'STUDIO_TIMEOUT: Agent antwortet nicht.') })
        $t.Add(@{ name = 'set_camera'; category = 'gui'; summary = 'Kamera setzen (Position + Blickziel).';
            description = 'Setzt die Player-Kamera (Scriptable) auf position und blickt auf lookAt. Kurzform fuer client_action camera.';
            params = @{ position = @{ type = '{x,y,z}'; required = $true; default = '-'; description = '' }; lookAt = @{ type = '{x,y,z}'; required = $false; default = 'null'; description = 'Ziel des Blicks.' } };
            returns = '{ ok }';
            example = @{ position = @{ x = 0; y = 20; z = 30 }; lookAt = @{ x = 0; y = 5; z = 0 } };
            errors = @('PLAY_NOT_RUNNING', 'NO_PLAYER') })

        # ---------------- JOBS ----------------
        $t.Add(@{ name = 'start_job'; category = 'jobs'; summary = 'Arbeit im Hintergrund starten (keine 60s-Grenze).';
            description = 'Startet Lua-Code ODER einen Tool-Call als Job im Studio. Laeuft unabhaengig weiter, auch wenn der HTTP-Call timet-out. Fortschritt: job kann job.progress(percent, message) rufen (im Code als job-Parameter: job:progress(...)). Ergebnis: job_result. Abbruch: cancel_job (kooperativ).';
            params = @{ name = @{ type = 'string'; required = $false; default = "'job'"; description = 'Merkname.' }; source = @{ type = 'string'; required = $false; default = 'null'; description = 'Lua-Code (in der persistenten Umgebung). (alternativ tool+args)' }; tool = @{ type = 'string'; required = $false; default = 'null'; description = 'Tool-Name, der im Job laufen soll.' }; args = @{ type = 'table'; required = $false; default = '{}'; description = 'Argumente fuer tool.' } };
            returns = '{ ok, jobId, status="running", poll = "job_status / job_result" }';
            example = @{ name = 'build wall'; source = 'for i=1,500 do ... end; return "done"' };
            errors = @('BAD_ARGS: source oder tool+args angeben.', 'COMPILE_ERROR: bei source.') })
        $t.Add(@{ name = 'job_status'; category = 'jobs'; summary = 'Läuft der Job? Wie weit?';
            params = @{ jobId = @{ type = 'string'; required = $true; default = '-'; description = '' } };
            returns = '{ status: "running"|"done"|"error", progress (0..1), progressMessage, secondsElapsed, hasResult }';
            example = @{ jobId = 'job_3' };
            errors = @('JOB_NOT_FOUND') })
        $t.Add(@{ name = 'job_result'; category = 'jobs'; summary = 'Ergebnis eines fertigen Jobs holen.';
            params = @{ jobId = @{ type = 'string'; required = $true; default = '-'; description = '' }; keep = @{ type = 'bool'; required = $false; default = 'false'; description = 'true = Ergebnis behalten, sonst wird es nach dem Hohlen entfernt.' } };
            returns = '{ ok, result (Rueckgabewert), output (gedrucktes waehrend des Jobs), durationSeconds, error? { code, message } }';
            example = @{ jobId = 'job_3' };
            errors = @('JOB_NOT_FOUND', 'JOB_RUNNING: noch nicht fertig - job_status warten.') })
        $t.Add(@{ name = 'list_jobs'; category = 'jobs'; summary = 'Alle Jobs (aktiv + erledigt).';
            params = @{};
            returns = '{ jobs: [ { id, name, status, progress, secondsElapsed } ], activeCount }';
            example = @{};
            errors = @() })
        $t.Add(@{ name = 'cancel_job'; category = 'jobs'; summary = 'Job abbrechen (kooperativ).';
            description = 'Setzt ein Flag, das der Job-Code ueber job:cancelled() pruefen kann. Lua-Threads lassen sich nicht hart toeten - der Code sollte in Schlingen job:cancelled() pruefen.';
            params = @{ jobId = @{ type = 'string'; required = $true; default = '-'; description = '' } };
            returns = '{ cancelled = true, note }';
            example = @{ jobId = 'job_3' };
            errors = @('JOB_NOT_FOUND') })
        $t.Add(@{ name = 'get_pending'; category = 'jobs'; summary = 'Was laeuft noch in Studio? (ueberlebte Timeouts).';
            description = 'Listet Befehle, die im Studio noch laufen (z.B. nach einem HTTP-Timeout) und späte Ergebnisse, die seitdem eingetroffen sind. Der naechste Tool-Call wartet automatisch darauf - nichts muss getoetet werden.';
            params = @{};
            returns = '{ runningInStudio: [ { commandId, tool, seconds } ], lateResults: [ { tool, commandId, result } ] }';
            example = @{};
            errors = @() })

        # ---------------- SYSTEM ----------------
        $t.Add(@{ name = 'batch'; category = 'system'; summary = 'Viele Tools in einer Anfrage.';
            description = 'sequenziell (Standard) oder parallel=true. stopOnError=true bricht beim ersten Fehler ab. ACHTUNG: parallel=true fuehrt die Calls GLEICHZEITIG im Studio aus - nur fuer echte Unabhaengigkeiten.';
            params = @{ commands = @{ type = 'array'; required = $true; default = '-'; description = '[ { tool, args }, ... ].' }; parallel = @{ type = 'bool'; required = $false; default = 'false'; description = '' }; stopOnError = @{ type = 'bool'; required = $false; default = 'false'; description = '' }; timeoutSeconds = @{ type = 'number'; required = $false; default = '90'; description = 'parallel-Modus.' } };
            returns = '{ results: [ ...je Call... ], count, failed, mode }';
            example = @{ commands = @(@{ tool = 'create_instance'; args = @{ className = 'Part'; name = 'A' } }, @{ tool = 'create_instance'; args = @{ className = 'Part'; name = 'B' } }) };
            errors = @() })
        $t.Add(@{ name = 'parallel'; category = 'system'; summary = 'Kurzform: batch mit parallel=true.';
            params = @{ commands = @{ type = 'array'; required = $true; default = '-'; description = '' } };
            returns = 'wie batch';
            example = @{ commands = @(@{ tool = 'clone_instance'; args = @{ ref = '#42'; count = 10 } }) };
            errors = @() })
        $t.Add(@{ name = 'undo'; category = 'system'; summary = 'Letzte Aenderung rueckgaengig (Studio-History).';
            description = 'Nimmt den letzten Schritt in der Studio-History zurueck (wie Strg+Z). Unions setzen vorher automatisch einen Punkt.';
            params = @{};
            example = @{};
            returns = '{ undone }';
            errors = @('RUNTIME_ERROR: Undo nicht moeglich.') })
        $t.Add(@{ name = 'redo'; category = 'system'; summary = 'Wiederholen.';
            description = 'Macht den letzten undo wieder gueltig (wie Strg+Y).';
            params = @{};
            example = @{};
            returns = '{ redone }';
            errors = @() })
        $t.Add(@{ name = 'set_waypoint'; category = 'system'; summary = 'Undo-Punkt setzen.';
            description = 'Setzt einen sichtbaren Punkt in der Studio-History, damit der Benutzer deine Arbeit in EINEM Schritt rueckgaengig machen kann. Die Bridge setzt vor union, create, delete & Co. automatisch welche.';
            params = @{ name = @{ type = 'string'; required = $false; default = "'manual'"; description = '' } };
            returns = '{ waypoint }';
            example = @{ name = 'Before the wall' };
            errors = @() })
        $t.Add(@{ name = 'get_notices'; category = 'system'; summary = 'Was ist passiert, ohne dass du es getan hast?';
            description = 'Meldungen wie "Benutzer hat den Test gestartet/stoppt", "Plugin neu verbunden" etc. Kommen auch automatisch als notices in fast jeder Antwort.';
            params = @{ all = @{ type = 'bool'; required = $false; default = 'false'; description = 'true = auch schon gelieferte.' } };
            returns = '{ notices: [ { seq, kind, message, time, data } ] }';
            example = @{};
            errors = @() })
        $t.Add(@{ name = 'get_events'; category = 'system'; summary = 'Ereignisse von der Bridge-Seite.';
            description = 'Dasselbe wie get_notices, aber uebersteht Plugin-Reloads (wird im Programm gespeichert).';
            params = @{};
            returns = '{ events: [...], count }';
            example = @{};
            errors = @() })
        $t.Add(@{ name = 'get_chunk'; category = 'system'; summary = 'Stueck eines grossen Ergebnisses holen.';
            description = 'Wenn eine Antwort zu gross ist, liegt sie im Programm: blobId + chunkCount. Alle Chunks in Reihe holen und zusammenfuegen = komplettes Ergebnis (nie abgeschnitten).';
            params = @{ blobId = @{ type = 'string'; required = $true; default = '-'; description = '' }; index = @{ type = 'int'; required = $true; default = '-'; description = '1..chunkCount.' } };
            returns = '{ data, index, chunkCount, isLast, totalChars }';
            example = @{ blobId = 'blob_abc'; index = 1 };
            errors = @('REF_NOT_FOUND: unbekanntes/abgelaufenes blobId (30 Min).') })
        $t.Add(@{ name = 'upload_text'; category = 'system'; summary = 'Grossen Text in Stuecken hochladen.';
            description = 'Fuer Skriptquellen > 50 KB: in Chunks hierher, danach sourceRef=<uploadId> an set_script_source/insert_script. Der Text wird unverändert übernommen (kein String-Schneidwerk, keine %-Kollisionen).';
            params = @{ text = @{ type = 'string'; required = $true; default = '-'; description = 'Stueck (oder alles).' }; uploadId = @{ type = 'string'; required = $false; default = 'neu'; description = 'Fuer mehrere Chunks: gleicher Wert.' }; chunkIndex = @{ type = 'int'; required = $false; default = '1'; description = '' }; chunkCount = @{ type = 'int'; required = $false; default = '1'; description = '' } };
            returns = '{ uploadId, chars, complete, useAs }';
            example = @{ text = 'local M = {}'; chunkIndex = 1; chunkCount = 3; uploadId = 'myScript' };
            errors = @() })
        $t.Add(@{ name = 'get_docs'; category = 'system'; summary = 'Doku holen: pro Tool, pro Kategorie oder komplett.';
            description = 'Dasselbe wie GET /api/docs - als Tool. Ohne Argumente: komplett.';
            params = @{ tool = @{ type = 'string'; required = $false; default = 'null'; description = 'Einzelnes Tool (z.B. "union").' }; category = @{ type = 'string'; required = $false; default = 'null'; description = 'info, spatial, orientation, create, properties, scripts, fill, union, assets, output, play, gui, jobs, system.' }; full = @{ type = 'bool'; required = $false; default = 'false'; description = 'Komplette Doku.' } };
            returns = 'Doku-JSON (siehe /api/docs)';
            example = @{ tool = 'fill_region' };
            errors = @('REF_NOT_FOUND: unbekanntes Tool/Kategorie (Liste im Fehler).') })
        $t.Add(@{ name = 'capture_screenshot'; category = 'system'; summary = 'Screenshot (NICHT EMPFOEHLEN).';
            description = 'Existiert, aber BILDANALYSE ist unzuverlaessig und langsam. Nutze describe_scene / get_bounds / get_tree / get_output - die geben exakte Zahlen. Benötigt confirm=true.';
            params = @{ confirm = @{ type = 'bool'; required = $true; default = '-'; description = 'Muss true sein.' }; includeBase64 = @{ type = 'bool'; required = $false; default = 'false'; description = 'Bild als Base64-Blob.' }; maxWidth = @{ type = 'int'; required = $false; default = '1100'; description = '' } };
            returns = '{ file, width, height, advice }';
            example = @{ confirm = $true };
            errors = @('RUNTIME_ERROR: Studio-Fenster nicht sichtbar.') })

        return $t
    }


    # ------------------------------------------------------------------
    # MANIFEST: die Bedienungsanleitung für die KI
    # ------------------------------------------------------------------
    # ==================================================================
    # GELEITINFORMATIONEN: Regeln, Koordinaten, Play-Modi, Jobs, Fehler-
    # Codes, Workflows. Stecken in Manifest, /api/docs und _sessionStart.
    # ==================================================================
    function Get-BridgeGuides {
        return @{
            importantRules = @(
                'IDS FIRST: every object has an id like "#42". Names are NOT unique - 55 parts can all be called "Part". Every read tool returns the id; always pass ids back in "ref"/"refs". A path like game.Workspace.Part[3] also works, but ids are safer.',
                'SELECTORS: most "refs" arguments also accept a selector table: { tag = "Door" }, { className = "Part", rootRef = "#50" }, { query = "crate" }. Use selectors instead of long id lists.',
                'SCRIPTS: never rewrite an 800 line script to change one line. Read with get_script (line numbers + hash), then patch_script (replace / replaceAll / insertAfter / replaceFunction / replaceLines ...). Check the result with compile_check BEFORE running it. set_script_source (full replace) still exists for new or tiny files. Pass expectHash to be safe.',
                'NO STRING SURGERY: the bridge never modifies your source text (no trimming, no "return M" removal, no %-reformatting). A ModuleScript simply ends with "return M". If you need to change text, use patch_script ops - never .replace() across languages.',
                'PLAY MODES (know the difference or tests fail): edit = permanent building; run = simulation only (server scripts + physics, NO player, NO client, NO GUI - by design); play = full game with test player, character, GUI and client agent. For anything with a character or GUI: play_start mode="play". "No player" errors in run mode are NOT bugs.',
                'THE USER IS THERE TOO: the user can press Play/Stop and PLAY in the game at any moment (moving the camera, walking the avatar, clicking the GUI). You will see it in _bridge.events / notices (user_rotating_camera, user_moving_character, user_clicked_gui, play_started with startedBy="user"). That is normal: nothing crashed and it is NOT a bug in your scripts - do not go searching for errors because of it.',
                'USER PLAYTEST HAS PRIORITY: if Studio is in Play/Run and you are about to make persistent edits, STOP_CURRENT_RESPONSE. Tell the user you can see the active playtest, politely ask them to leave it, and wait for confirmation that Studio is back in Edit mode. Never stop a user-owned playtest yourself.',
                'PERSISTENT LUA: run_lua runs in a persistent environment. Helpers you define (without "local") survive to the next call - see lua_state. You never have to re-paste helper code.',
                'TIMEOUTS NEVER KILL WORK: a timed-out call is still running in Studio. The next call automatically waits for it (Studio executes strictly one command at a time), and the late result arrives in _bridge.lateResults. For long work use asJob=true / start_job and poll job_status / job_result.',
                'HEIGHTS BY RAYCAST ONLY: use ground_height / raycast / measure_height. NEVER compute world Y from voxel indices or formulas - it is wrong by design in this place.',
                'WAIT FOR MEASURABLE: after create/fill the bridge waits (verify_measurable) until new geometry answers raycasts. If you still see "nothing there": call verify_measurable on the new ids.',
                'FILLING: call probe_world once (it measures the grid step, water level and the fill-height rule and stores them). fill_region then fills by the MEASURED rule, in chunks, with a resumeToken (abort = continue, not restart). Lower overwrites need clearing with Air first (confirmClear=true) - they are reported as skippedNeedClear otherwise.',
                'UNIONS: one-way and expensive. The bridge pre-checks (anchored/parent/size), sets an undo point, budgets the triangle count and tells you a cheaper alternative when one exists (e.g. one part instead of 40). Roblox refusals come back as SOLID_REFUSED with the Roblox message. Use separate to get the parts back.',
                'BULK INSTEAD OF LOOPS: bulk_create (template+grid builds whole arrangements), clone_instance count=60, bulk_delete, bulk_set_properties, bulk_insert_scripts, grid_arrange/distribute/stack/place_on/snap_to_ground/fit_between. Never 60 single calls, never Lua loops for layout.',
                'ASSETS: search_assets (cached locally; image/texture search runs through decals, mesh through meshparts - the answer explains it). apply_asset/insert_asset VALIDATE the id against its type BEFORE touching Studio (ASSET_TYPE_MISMATCH / ASSET_NOT_FOUND). If the catalog is unreachable: CATALOG_UNAVAILABLE - say clearly "Katalog nicht verfügbar" and build procedurally. Free models stay blocked (allowModels=true overrides; script assets need acceptScripts=true).',
                'BIG DATA IS NEVER TRUNCATED: if an answer is too big it is stored on the PC and you get blobId + chunkCount. Fetch every chunk with get_chunk and glue them together.',
                'SCREENSHOTS ARE A LAST RESORT: capture_screenshot exists but you are strongly advised NOT to use it - reading images is unreliable. describe_scene, get_bounds, get_tree, get_output and the gui_* tools give you exact facts.',
                'ROTATION: before rotating cylinders or wedges, call coordinate_guide (it MEASURES the shape geometry in the place, it does not guess) and then use point_at / describe_orientation. "Which way does this part face?" is answered by describe_orientation - not by trial and error.',
                'ERRORS HAVE CLASSES: every error response carries a code (STUDIO_TIMEOUT, PLAY_MODE_ACTIVE, COMPILE_ERROR, RUNTIME_ERROR, REF_NOT_FOUND, REGION_LIMIT, WORLD_NOT_PROBED, UNION_BUDGET, SOLID_REFUSED, CATALOG_UNAVAILABLE, ASSET_TYPE_MISMATCH, ...). React on the code, do not string-match error text.'
            )
            coordinateGuide = @(
                'AXES: +X = right, +Y = up, +Z = toward the viewer. The default Studio camera looks toward -Z. The "front" face of a part is its -Z face.',
                'YAW: rotation around +Y in degrees, positive = counter-clockwise seen from above. A yaw of d turns the front face to direction (-sin d, 0, -cos d) - so positive yaw turns the front toward -X (left).',
                'CFrame orientation comes back in degrees (orientation) and radians (orientationRadians); pitch is around X, roll around Z.',
                'SHAPE DEFAULTS (reported measured by coordinate_guide - never guess): Block = axis aligned. Ball = sphere. Cylinder = length axis is VERTICAL (Y), flat caps on top and bottom (so "the cylinder points up" by default). Wedge = a ramp: coordinate_guide tells you the exact high edge and slope direction.',
                'WORKFLOW: coordinate_guide (once) -> describe_orientation (where do the faces point now?) -> point_at or rotate_around (with the measured axis) -> describe_orientation again to verify.'
            )
            playModes = @{
                edit = 'No test: everything you build is PERMANENT. This is where building and script editing happens.'
                run = 'Simulation only: server scripts + physics run, but there is NO player, NO character, NO client and NO GUI. Use it for physics/server-logic tests. A tool answering "No player" in run mode is working as designed - switch to play for characters/GUI.'
                play = 'Full game: one test player with character, PlayerGui and a client agent (installed automatically). play_start mode="play" WAITS until the character exists and reports PLAY_NO_PLAYER with recent errors otherwise. The USER can play in the same game at the same time - you get events (user_rotating_camera, user_moving_character, user_clicked_gui) and must not read those as script bugs.'
            }
            jobsGuide = @(
                'Any tool call can run in the background: pass asJob=true in args (or use start_job with source or tool+args). You get a jobId immediately - no 60-second wall.'
                'An HTTP timeout NEVER kills the work: the command keeps running in Studio, the result arrives later in _bridge.lateResults, and every following call automatically waits for the running command to finish (you can never measure against a still-running script).'
                'Inside job code: call job:progress(percent, message) for progress and check job:cancelled() in loops (cancel_job is cooperative - Lua threads cannot be killed hard).'
                'fill_region is resumable: it returns a resumeToken - repeat the same call with resumeToken to continue where it stopped instead of starting over.'
            )
            errorCodes = @{
                STUDIO_TIMEOUT = 'HTTP call timed out, but the command is STILL RUNNING in Studio - nothing is lost. The next call waits for it automatically. Long work should use asJob=true.'
                PLAY_MODE_ACTIVE = 'Building/editing is blocked while a test runs (changes are thrown away at stop). play_stop first, work, then play_start. allowInPlayMode=true for throw-away test changes.'
                READONLY_TOKEN = 'This place is set to read-only in the bridge window. The user can switch it back.'
                COMPILE_ERROR = 'Lua does not compile (line number included). Fix and check with compile_check before running.'
                RUNTIME_ERROR = 'Lua ran and failed (message + context).'
                NO_PLAYER = 'No player/character - you are probably in run mode. Use play_start mode="play".'
                PLAY_NOT_RUNNING = 'A playtest tool was called while nothing is running.'
                PLAY_NO_PLAYER = 'Play mode started but no character appeared within 20s (recentErrors included for diagnosis).'
                PLAY_FALLBACK_RUN = 'The Studio Play shortcut could not be pressed, so Run mode started instead (no player) - try again with the Studio window focused.'
                REF_NOT_FOUND = 'An id/path/selector could not be resolved (object deleted, or the plugin reloaded - get fresh ids with search/get_tree).'
                BAD_ARGS = 'Arguments missing or invalid (the message says what exactly).'
                REGION_LIMIT = 'A region/box was too large - the message contains the measured limit; split the region up. Only the failing slice is reported, the rest continues.'
                WORLD_NOT_PROBED = 'fill_region needs probe_world first (fill heights are measured, never guessed).'
                UNION_BUDGET = 'Union input exceeds the part/complexity limits - build smaller groups or pass force=true.'
                UNION_COSTLY = 'Warning: the union estimate is expensive - the suggestion field offers a cheaper alternative (e.g. one part instead of 40).'
                SOLID_REFUSED = 'Roblox refused the solid operation (robloxMessage + hints). Nothing was changed.'
                UNION_PRECHECK = 'Warning from the pre-check (not anchored / different parents / ...) with the exact list.'
                ASSET_BLOCKED = 'Free models are blocked on purpose (allowModels=true overrides - build instead).'
                ASSET_HAS_SCRIPTS = 'The asset contains scripts. acceptScripts=true overrides; inspect the inserted content immediately.'
                ASSET_TYPE_MISMATCH = 'The asset id does not match the expected type (actual type is reported). Nothing was applied.'
                ASSET_NOT_FOUND = 'The id does not exist or is not public (404). Do not use it.'
                CATALOG_UNAVAILABLE = 'The Roblox catalog is not reachable right now. Say clearly to the user: "Katalog nicht verfügbar" - then build procedurally. Do not guess ids, do not stay silent. Retry later with catalog_status.'
                CATALOG_TYPE_NOT_SUPPORTED = 'That asset type cannot be searched in the catalog (list of supported types included).'
                JOB_NOT_FOUND = 'Unknown jobId (it may have been removed after job_result).'
                JOB_RUNNING = 'The job is not finished yet - poll job_status and fetch the result later.'
                GEOMETRY_NOT_READY = 'Warning: new geometry was not immediately raycastable; verify_measurable waited for it (see geometry in the result).'
            }
            typedValues = 'Complex values are typed JSON: {"type":"Vector3","x":0,"y":5,"z":0}, {"type":"Color3","rgb":[255,0,0]}, {"type":"CFrame","position":{...},"orientation":{...}}, {"type":"EnumItem","enum":"Material","name":"Neon"}. Short forms work too: [0,5,0] for a Vector3, "Neon" for an enum, "#FF0000" for a colour, [255,0,0] for a Color3.'
            workflows = @{
                buildSomething = @('play_status (must be edit mode)', 'describe_scene / search for context', 'create_instance or bulk_create (template+grid)', 'place_on / stack / snap_to_ground / grid_arrange instead of maths', 'select_instance so the user sees it')
                editAScript = @('search className=Script', 'get_script (note the hash)', 'patch_script with a unique snippet', 'compile_check the result', 'set/patch with expectHash', 'play_start mode=play', 'wait_for_output / get_errors', 'play_stop')
                testAGame = @('play_start mode=play (it waits for the character)', 'character_state / move_character / set_camera', 'gui_dump -> gui_check -> gui_click with expect', 'get_output since=<cursor> / get_errors', 'play_stop')
                manyObjects = @('clone_instance count=60 offset={x:8} nameTemplate="Crate{n}"', 'or bulk_create with template+grid', 'or batch (parallel=true only for independent calls)')
                longBuild = @('fill_region with asJob=true (or start_job)', 'job_status (progress + partsPerSecond)', 'job_result when done (geometry.ready included)', 'verify_measurable on a sample if in doubt')
                rotationCorrect = @('coordinate_guide (once per session)', 'describe_orientation on the part', 'point_at (axis="top" for cylinder length) or rotate_around with measured axes', 'describe_orientation again to verify')
                assets = @('catalog_status (is it up?)', 'search_assets (type, keyword) - cached locally', 'validate_asset if unsure', 'apply_asset (auto-validated) / insert_asset', 'if CATALOG_UNAVAILABLE: say so and build procedurally')
            }
        }
    }

    # ==================================================================
    # /api/docs: Doku pro Tool, pro Kategorie oder komplett.
    # ==================================================================
    function Get-DocsResponse([string]$tool, [string]$category, [string]$full) {
        $all = Get-ToolDocs
        if (-not [string]::IsNullOrWhiteSpace($tool)) {
            $found = @()
            foreach ($d in $all) { if ($d.name -eq $tool.ToLowerInvariant()) { $found += $d } }
            if ($found.Count -eq 1) {
                return @{ ok = $true; docsVersion = [string]$Shared.DocsVersion; tool = $found[0] }
            }
            $names = @()
            foreach ($d in $all) { $names += $d.name }
            return @{ ok = $false; code = 'REF_NOT_FOUND'; error = "Unknown tool '$tool'."; knownTools = $names }
        }
        if (-not [string]::IsNullOrWhiteSpace($category)) {
            $found = @()
            foreach ($d in $all) { if ($d.category -eq $category.ToLowerInvariant()) { $found += $d } }
            if ($found.Count -eq 0) {
                $cats = @{}
                foreach ($d in $all) { $cats[[string]$d.category] = 1 }
                return @{ ok = $false; code = 'REF_NOT_FOUND'; error = "Unknown category '$category'."; knownCategories = @($cats.Keys) }
            }
            return @{ ok = $true; docsVersion = [string]$Shared.DocsVersion; category = $category; count = $found.Count; tools = $found }
        }
        $categories = @{}
        foreach ($d in $all) { $categories[[string]$d.category] = [int]$categories[[string]$d.category] + 1 }
        $result = @{
            ok = $true
            docsVersion = [string]$Shared.DocsVersion
            toolCount = $all.Count
            categories = $categories
            tools = $all
        }
        $guides = Get-BridgeGuides
        foreach ($key in $guides.Keys) { $result[[string]$key] = $guides[$key] }
        return $result
    }

    # ==================================================================
    # START-DOKU: wird automatisch mit der ERSTEN Tool-Antwort der Sitzung
    # ausgeliefert (_sessionStart) - die KI bekommt also ohne Extra-Call
    # ALLE Informationen (Doku pro Tool, Regeln, Fehlercodes, Workflows).
    # ==================================================================
    function Get-SessionStartPackage {
        $out = @{
            docsVersion = [string]$Shared.DocsVersion
            welcome = 'Welcome - this is your FIRST tool response on this place, so the complete documentation follows right here in _sessionStart. Keep it in mind for the whole session. Anything on demand: GET /api/docs (or ?tool= / ?category=) or the get_docs tool.'
            quickStart = @(
                '1. get_place_info - which place, which mode (edit/run/play), capabilities.',
                '2. describe_scene - the textual description of the scene (positions, sizes, materials) - use it INSTEAD of screenshots.',
                '3. play_status - is a test running?',
                '4. For a single tool whenever you need it: get_docs { tool: "..." }.'
            )
        }
        $guides = Get-BridgeGuides
        foreach ($key in $guides.Keys) { $out[[string]$key] = $guides[$key] }
        $out.tools = (Get-ToolDocs)
        return $out
    }

    # ------------------------------------------------------------------
    # MANIFEST: die Bedienungsanleitung für die KI
    # ------------------------------------------------------------------
    function Get-Manifest {
        $docs = Get-ToolDocs
        $toolIndex = New-Object System.Collections.Generic.List[object]
        foreach ($d in $docs) {
            $toolIndex.Add(@{ name = $d.name; category = $d.category; description = $d.summary })
        }
        $guides = Get-BridgeGuides
        $manifest = @{
            name = 'Arena Roblox Studio Bridge'
            version = '3.7'
            docsVersion = [string]$Shared.DocsVersion
            role = 'You are connected to exactly ONE live Roblox Studio place through a local plugin. Every token belongs to one Studio window only - if several windows are open, each one has its own token and you can never touch the wrong place. Send every request as POST /api/tool with JSON body { "token": "...", "tool": "...", "args": { ... } }.'
            firstCallBehavior = 'The complete documentation (every tool: description, all parameters with type+default, return value, runnable example, error cases) is delivered automatically with the FIRST tool response of this session as _sessionStart. You do not need any extra call to get it. On demand: GET /api/docs (no param = everything, ?tool=<name>, ?category=<name>) or the get_docs tool.'
            authentication = @{
                headers = @('Authorization: Bearer <token>', 'X-Arena-Token: <token>')
                query = '?token=<token>'
            }
            endpoints = @{
                manifest    = 'GET /api/manifest'
                docs        = 'GET /api/docs  (no param = everything; ?tool=<name>; ?category=<name>; ?full=true)'
                place       = 'GET /api/place'
                callTool    = 'POST /api/tool  { token, tool, args }  (args.asJob=true = run in background, get jobId)'
                callMany    = 'POST /api/tools/parallel  { token, calls: [ { tool, args } ] }  - runs several tools at the same time'
                events      = 'GET /api/events?token=...  - what the user did (started/stopped a playtest, plays in the game, ...)'
                blob        = 'GET /api/blob?token=...&id=<blobId>&index=<n>  - fetch one chunk of a huge answer'
                upload      = 'POST /api/upload  { token, text, uploadId?, chunkIndex?, chunkCount? }  - send a huge script in pieces, then use args.sourceRef = uploadId'
                status      = 'GET /api/status'
            }
            toolCount = $docs.Count
            toolsIndex = $toolIndex
            tools = $docs
        }
        foreach ($key in $guides.Keys) { $manifest[[string]$key] = $guides[$key] }
        return $manifest
    }


    # ------------------------------------------------------------------
    # Mehrere Befehle gleichzeitig an das Plugin schicken
    # ------------------------------------------------------------------
    function Invoke-PluginToolsParallel($sessionId, $calls, [int]$timeoutSeconds) {
        $pending = New-Object System.Collections.Generic.List[object]
        $queue = Ensure-Queue $sessionId
        foreach ($call in $calls) {
            $commandId = [guid]::NewGuid().ToString('N')
            $signal = New-Object System.Threading.ManualResetEventSlim($false)
            [void]$Shared.ResultSignals.TryAdd($commandId, $signal)
            $command = @{ id = $commandId; tool = [string]$call.tool; args = $call.args }
            $queue.Enqueue((To-Json $command 40))
            Add-PendingCommand $sessionId $commandId ([string]$call.tool)
            $pending.Add(@{ id = $commandId; tool = [string]$call.tool; signal = $signal; result = $null })
        }
        $wake = Ensure-Signal $sessionId
        [void]$wake.Set()

        $deadline = [DateTime]::UtcNow.AddSeconds($timeoutSeconds)
        $open = $pending.Count
        while ($open -gt 0 -and [DateTime]::UtcNow -lt $deadline) {
            $open = 0
            foreach ($item in $pending) {
                if ($item.result -eq $null) {
                    $resultJson = $null
                    if ($Shared.CommandResults.TryRemove($item.id, [ref]$resultJson)) {
                        $item.result = $resultJson
                    } else {
                        $open = $open + 1
                    }
                }
            }
            if ($open -gt 0) { Start-Sleep -Milliseconds 40 }
        }

        $parts = New-Object System.Collections.Generic.List[string]
        foreach ($item in $pending) {
            $removed = $null
            [void]$Shared.ResultSignals.TryRemove($item.id, [ref]$removed)
            [void]$Shared.ResultChunks.TryRemove($item.id, [ref]$removed)
            try { $item.signal.Dispose() } catch {}
            if ($item.result) {
                $parts.Add('{"tool":' + (To-Json $item.tool 3) + ',"response":' + $item.result + '}')
            } else {
                $parts.Add('{"tool":' + (To-Json $item.tool 3) + ',"response":{"ok":false,"code":"STUDIO_TIMEOUT","error":"Roblox Studio did not answer in time. The command may still be running in Studio - nothing is lost. The next call waits for it to finish."}}')
            }
        }
        return '[' + ($parts -join ',') + ']'
    }

    function New-Envelope($sessionId) {
        $entry = Get-SessionEntry $sessionId
        $events = Take-Events $sessionId 12
        $envelope = @{
            bridgeVersion = '3.7'
            place         = if ($entry) { $entry.placeName } else { $null }
            sessionId     = $sessionId
            studio        = if ($entry) { $entry.state } else { $null }
            serverTime    = (Get-Date).ToString('u')
            docsVersion   = [string]$Shared.DocsVersion
            docs          = 'Full tool documentation (parameters, types, defaults, returns, examples, error codes): GET /api/docs, or ?tool=<name>, or ?category=<name>. It was also delivered automatically with the first tool call of this session (_sessionStart).'
        }
        if ($entry -and $entry.state -and [bool]$entry.state.running -and [bool]$entry.state.userPlaytestActive) {
            $envelope.playtestWarning = @{
                severity = 'critical'
                code = 'USER_PLAYTEST_ACTIVE'
                assistantAction = 'STOP_CURRENT_RESPONSE'
                message = 'Roblox Studio is in Play/Run mode. If the user started or is using this playtest, stop your current response, do not edit, and ask the user to leave the playtest before you continue.'
                userRequest = 'Tell the user you can see the active playtest and politely ask them to stop it in Roblox Studio. Wait for confirmation; do not stop their test yourself.'
            }
            $envelope.attention = 'CRITICAL PLAYTEST NOTICE: STOP_CURRENT_RESPONSE. The user may be playing right now. Do not make persistent edits; ask them to leave the Roblox Studio playtest first.'
        }
        # In Studio läuft noch etwas (z.B. nach einem Timeout). Studio arbeitet
        # Befehle strikt nacheinander ab - der nächste Call wartet automatisch.
        $pending = Get-PendingCommands $sessionId
        if ($pending.Count -gt 0) {
            $envelope.studioBusy = $pending
            $busyNote = 'One or more commands are still running inside Roblox Studio (they survived a timeout - the work is NOT lost). Studio executes commands strictly one after another, so this and every following call automatically wait for them to finish before doing anything - you can never measure against a still-running script. Results that already arrived in the meantime are in _bridge.lateResults.'
            if ($envelope.attention) {
                $envelope.attention = $envelope.attention + ' ' + $busyNote
            } else {
                $envelope.attention = $busyNote
            }
        }
        $late = Take-LateResults $sessionId
        if ($late.Count -gt 0) {
            $envelope.lateResults = $late
            $envelope.lateResultsNote = 'These results finished in Studio AFTER their HTTP call had timed out. They are final - do not rerun the work.'
        }
        if ($events.Count -gt 0) {
            $envelope.events = $events
            $eventNote = 'Something happened outside of your control (see events) - for example the user started or stopped the playtest, or the user is playing in the game right now. This is normal, nothing crashed, and it is NOT a bug in your scripts.'
            if ($envelope.attention) {
                $envelope.attention = $envelope.attention + ' ' + $eventNote
            } else {
                $envelope.attention = $eventNote
            }
        }
        return $envelope
    }

    # ------------------------------------------------------------------
    # Werkzeuge, die das Programm selbst beantwortet (ohne Roblox)
    # ------------------------------------------------------------------
    function Invoke-ServerTool($sessionId, [string]$tool, $toolArgs) {
        switch ($tool) {
            'search_assets'      { return (Invoke-AssetSearch $toolArgs) }
            'asset_details'      { return (Invoke-AssetDetails $toolArgs) }
            'validate_asset'     { return (Invoke-AssetValidation $toolArgs) }
            'catalog_status'     { return (Invoke-CatalogStatus $toolArgs) }
            'get_docs' {
                $qTool = if ($toolArgs.tool) { [string]$toolArgs.tool } else { $null }
                $qCategory = if ($toolArgs.category) { [string]$toolArgs.category } else { $null }
                $qFull = if ($toolArgs.full -eq $true) { 'true' } else { $null }
                return (Get-DocsResponse $qTool $qCategory $qFull)
            }
            'get_pending' {
                $pending = Get-PendingCommands $sessionId
                $late = Take-LateResults $sessionId
                return @{
                    ok = $true
                    result = @{
                        runningInStudio = $pending
                        lateResults     = $late
                        count           = $pending.Count
                        note = 'Commands in runningInStudio are still executing inside Studio (they survive timeouts). Your next tool call automatically waits for them - nothing needs to be killed.'
                    }
                }
            }
            'capture_screenshot' { return (Invoke-Screenshot $toolArgs) }
            'get_chunk' {
                $index = 1
                if ($toolArgs.index) { $index = [int]$toolArgs.index }
                return (Get-BlobChunk ([string]$toolArgs.blobId) $index)
            }
            'upload_text' {
                $uploadId = [string]$toolArgs.uploadId
                if ([string]::IsNullOrWhiteSpace($uploadId)) {
                    $uploadId = 'up_' + [guid]::NewGuid().ToString('N').Substring(0, 12)
                }
                $existing = ''
                [void]$Shared.Uploads.TryGetValue($uploadId, [ref]$existing)
                $chunkIndex = 1
                if ($toolArgs.chunkIndex) { $chunkIndex = [int]$toolArgs.chunkIndex }
                if ($chunkIndex -le 1) { $existing = '' }
                $Shared.Uploads[$uploadId] = $existing + [string]$toolArgs.text
                $chunkCount = 1
                if ($toolArgs.chunkCount) { $chunkCount = [int]$toolArgs.chunkCount }
                $complete = ($chunkIndex -ge $chunkCount)
                return @{
                    ok = $true
                    result = @{
                        uploadId = $uploadId
                        chars = $Shared.Uploads[$uploadId].Length
                        complete = $complete
                        useAs = 'Pass sourceRef = "' + $uploadId + '" instead of source in set_script_source / insert_script.'
                    }
                }
            }
            'get_events' {
                $events = Take-Events $sessionId 40
                return @{ ok = $true; result = @{ events = $events; count = $events.Count } }
            }
            'bridge_status' {
                $entry = Get-SessionEntry $sessionId
                $queue = Ensure-Queue $sessionId
                $pending = Get-PendingCommands $sessionId
                $assetCacheEntries = 0
                try {
                    if (Test-Path -LiteralPath [string]$Shared.AssetCachePath) {
                        $cache = Get-Content -LiteralPath [string]$Shared.AssetCachePath -Raw | ConvertFrom-Json
                        $assetCacheEntries = @($cache.PSObject.Properties).Count
                    }
                } catch {}
                return @{
                    ok = $true
                    result = @{
                        bridgeVersion = '3.7'
                        docsVersion = [string]$Shared.DocsVersion
                        place = if ($entry) { $entry.placeName } else { $null }
                        placeId = if ($entry) { $entry.placeId } else { $null }
                        studio = if ($entry) { $entry.state } else { $null }
                        pluginVersion = if ($entry) { $entry.pluginVersion } else { $null }
                        accessMode = if ($entry) { $entry.accessMode } else { $null }
                        queuedCommands = $queue.Count
                        runningInStudio = $pending
                        connectedPlaces = $Shared.Sessions.Count
                        storedBlobs = $Shared.Blobs.Count
                        assetCacheEntries = $assetCacheEntries
                        docs = 'GET /api/docs for the complete tool documentation (or ?tool= / ?category=).'
                        note = 'Each Studio window has its own token. This token only ever reaches the place shown above.'
                    }
                }
            }
        }
        return $null
    }

    $context = $Context

    do {
        try {
            if ($context.Request.HttpMethod -eq 'OPTIONS') {
                Send-Json $context 200 @{ ok = $true }
                continue
            }

            $path = $context.Request.Url.AbsolutePath.TrimEnd('/')
            if ($path -eq '') { $path = '/' }
            $body = $null
            if ($context.Request.HttpMethod -in @('POST', 'PUT', 'PATCH')) {
                $body = Read-Body $context.Request
            }

            # ---------------- Manifest -------------------------------------
            if ($path -eq '/' -or $path -eq '/api/manifest' -or $path -eq '/api/tools') {
                Send-Json $context 200 (Get-Manifest)
                continue
            }

            # ---------------- Plugin ---------------------------------------
            if ($path -eq '/plugin/hello') {
                $entry = Register-Session $body
                if (-not $entry) {
                    Send-Json $context 400 @{ ok = $false; error = 'Ungültige Anmeldung.' }
                } else {
                    Send-Json $context 200 @{
                        ok = $true
                        sessionId = $entry.sessionId
                        token = $entry.token
                        accessMode = $entry.accessMode
                        serverVersion = '3.7'
                        docsVersion = [string]$Shared.DocsVersion
                    }
                }
                continue
            }

            if ($path -eq '/plugin/heartbeat') {
                $entry = Update-Session $body
                if (-not $entry) {
                    Send-Json $context 200 @{ ok = $false; unknownSession = $true }
                } else {
                    Send-Json $context 200 @{ ok = $true; token = $entry.token; accessMode = $entry.accessMode }
                }
                continue
            }

            if ($path -eq '/plugin/poll') {
                $entry = Update-Session $body
                if (-not $entry) {
                    Send-Json $context 200 @{ ok = $false; unknownSession = $true }
                    continue
                }
                $sid = [string]$entry.sessionId
                $queue = Ensure-Queue $sid
                $signal = Ensure-Signal $sid

                $waitSeconds = 20
                if ($body.wait) {
                    $waitSeconds = [Math]::Min([double]$body.wait, 25)
                }
                $deadline = [DateTime]::UtcNow.AddSeconds($waitSeconds)
                $collected = New-Object System.Collections.Generic.List[string]

                # Offene Long-Polls werden gezählt. Daran erkennt die Anmeldung,
                # ob ein Studio-Fenster wirklich noch lebt.
                [void]$Shared.Pollers.AddOrUpdate($sid, 1, { param($key, $old) $old + 1 })
                try {
                    while ($true) {
                        $itemJson = $null
                        while ($collected.Count -lt 16 -and $queue.TryDequeue([ref]$itemJson)) {
                            $collected.Add($itemJson)
                        }
                        if ($collected.Count -gt 0) { break }
                        if ([DateTime]::UtcNow -ge $deadline) { break }
                        [void]$signal.Wait(250)
                        $signal.Reset()
                    }
                } finally {
                    [void]$Shared.Pollers.AddOrUpdate($sid, 0, { param($key, $old) [Math]::Max(0, $old - 1) })
                }

                $mode = 'readwrite'
                [void]$Shared.AccessModes.TryGetValue($sid, [ref]$mode)
                $json = '{"ok":true,"accessMode":' + (To-Json $mode 3) + ',"commands":[' + ($collected -join ',') + ']}'
                Send-RawJson $context 200 $json
                continue
            }

            if ($path -eq '/plugin/result') {
                if ($body -and $body.commandId) {
                    $commandId = [string]$body.commandId
                    # Ergebnis ist da -> Befehl ist im Studio erledigt (Timeout überlebt).
                    Remove-PendingCommand ([string]$body.sessionId) $commandId
                    if ($body.chunkCount) {
                        $bag = $null
                        if (-not $Shared.ResultChunks.TryGetValue($commandId, [ref]$bag)) {
                            $bag = [System.Collections.Concurrent.ConcurrentDictionary[int,string]]::new()
                            [void]$Shared.ResultChunks.TryAdd($commandId, $bag)
                            [void]$Shared.ResultChunks.TryGetValue($commandId, [ref]$bag)
                        }
                        $bag[[int]$body.chunkIndex] = [string]$body.chunk
                        $expected = [int]$body.chunkCount
                        if ($bag.Count -ge $expected) {
                            $builder = New-Object System.Text.StringBuilder
                            for ($i = 1; $i -le $expected; $i++) {
                                $piece = $null
                                if ($bag.TryGetValue($i, [ref]$piece)) {
                                    [void]$builder.Append($piece)
                                }
                            }
                            $Shared.CommandResults[$commandId] = $builder.ToString()
                            $signal = $null
                            if ($Shared.ResultSignals.TryGetValue($commandId, [ref]$signal)) {
                                [void]$signal.Set()
                            }
                        }
                    } elseif ($body.json) {
                        $Shared.CommandResults[$commandId] = [string]$body.json
                        $signal = $null
                        if ($Shared.ResultSignals.TryGetValue($commandId, [ref]$signal)) {
                            [void]$signal.Set()
                        }
                    } elseif ($body.result) {
                        $Shared.CommandResults[$commandId] = (To-Json $body.result 40)
                        $signal = $null
                        if ($Shared.ResultSignals.TryGetValue($commandId, [ref]$signal)) {
                            [void]$signal.Set()
                        }
                    }
                }
                Send-Json $context 200 @{ ok = $true }
                continue
            }

            if ($path -eq '/plugin/event') {
                if ($body -and $body.sessionId -and $body.event) {
                    Add-BridgeEvent ([string]$body.sessionId) ([string]$body.event.kind) ([string]$body.event.message) $body.event.data
                    $entry = Get-SessionEntry ([string]$body.sessionId)
                    if ($entry) {
                        $entry.state = (Get-StateObject $body)
                        $entry.lastSeen = (Get-UnixSeconds)
                        Save-SessionEntry $entry
                    }
                }
                Send-Json $context 200 @{ ok = $true }
                continue
            }

            if ($path -eq '/plugin/disconnect') {
                if ($body -and $body.sessionId) {
                    $sid = [string]$body.sessionId
                    Add-BridgeEvent $sid 'studio_disconnected' 'The Studio plugin disconnected (Studio closed, place closed or plugins reloading).' @{ reason = [string]$body.reason }
                    $entry = Get-SessionEntry $sid
                    if ($entry) {
                        # Als "verwaist" markieren: meldet sich dasselbe Fenster
                        # wieder (Testmodus, Plugins neu geladen), bekommt es
                        # genau diese Sitzung und denselben Token zurück.
                        $entry | Add-Member -NotePropertyName 'orphan' -NotePropertyValue $true -Force
                        Save-SessionEntry $entry
                    }
                    $removed = $null
                    [void]$Shared.Presence.TryRemove($sid, [ref]$removed)
                    $Shared.Pollers[$sid] = 0
                    # Studio ist weg: weiter "laufende" Befehle koennen nicht mehr
                    # ausgefuehrt werden - also der KI nicht mehr als laufend melden.
                    [void]$Shared.PendingCommands.TryRemove($sid, [ref]$removed)
                }
                Send-Json $context 200 @{ ok = $true }
                continue
            }

            # ---------------- Zugriff prüfen -------------------------------
            $token = Get-Token $context.Request $body
            $sessionId = Get-SessionForToken $token
            if (-not $sessionId) {
                Send-Json $context 401 @{
                    ok = $false
                    error = 'Token ungültig oder Place nicht verbunden.'
                    hint = 'Open the place in Roblox Studio and copy the prompt again from the Arena Roblox Bridge window. Every Studio window has its own token.'
                }
                continue
            }
            $sessionEntry = Get-SessionEntry $sessionId
            $accessMode = 'readwrite'
            [void]$Shared.AccessModes.TryGetValue($sessionId, [ref]$accessMode)

            if ($path -eq '/api/place') {
                Send-Json $context 200 @{ ok = $true; place = $sessionEntry }
                continue
            }

            if ($path -eq '/api/status') {
                Send-Json $context 200 @{
                    ok = $true
                    bridgeVersion = '3.7'
                    docsVersion = [string]$Shared.DocsVersion
                    place = $sessionEntry
                    connectedPlaces = $Shared.Sessions.Count
                    accessMode = $accessMode
                }
                continue
            }

            if ($path -eq '/api/events') {
                $events = Take-Events $sessionId 40
                Send-Json $context 200 @{ ok = $true; events = $events; count = $events.Count }
                continue
            }

            if ($path -eq '/api/blob') {
                $blobId = $context.Request.QueryString['id']
                $indexText = $context.Request.QueryString['index']
                $index = 1
                if ($indexText) { $index = [int]$indexText }
                Send-Json $context 200 (Get-BlobChunk $blobId $index)
                continue
            }

            if ($path -eq '/api/upload') {
                $result = Invoke-ServerTool $sessionId 'upload_text' $body
                Send-Json $context 200 $result
                continue
            }

            # ---------------- Doku (Tool / Kategorie / komplett) ----------------
            if ($path -eq '/api/docs') {
                $qTool = [string]$context.Request.QueryString['tool']
                $qCategory = [string]$context.Request.QueryString['category']
                $qFull = [string]$context.Request.QueryString['full']
                Send-Json $context 200 (Get-DocsResponse $qTool $qCategory $qFull)
                continue
            }

            # ---------------- Werkzeuge ------------------------------------
            if ($path -eq '/api/tools/parallel') {
                if (-not $body -or -not $body.calls) {
                    Send-Json $context 400 @{ ok = $false; error = 'calls fehlt: { "calls": [ { "tool": "...", "args": {} } ] }' }
                    continue
                }
                $timeout = 90
                if ($body.timeoutSeconds) { $timeout = [Math]::Min([int]$body.timeoutSeconds, 180) }
                $resultsJson = Invoke-PluginToolsParallel $sessionId $body.calls $timeout
                $envelope = New-Envelope $sessionId
                Send-RawJson $context 200 ('{"_bridge":' + (To-Json $envelope 20) + ',"ok":true,"results":' + $resultsJson + '}')
                continue
            }

            if ($path -eq '/api/tool') {
                if (-not $body) {
                    Send-Json $context 400 @{ ok = $false; error = 'JSON Body fehlt.' }
                    continue
                }
                $tool = [string]$body.tool
                if ([string]::IsNullOrWhiteSpace($tool)) {
                    Send-Json $context 400 @{ ok = $false; error = 'Tool fehlt.' }
                    continue
                }
                $toolArgs = $null
                if ($body.PSObject.Properties.Name -contains 'args') { $toolArgs = $body.args }
                if ($null -eq $toolArgs) { $toolArgs = New-Object PSObject }

                # Große Texte, die vorher hochgeladen wurden, einsetzen
                if ($toolArgs.PSObject.Properties.Name -contains 'sourceRef') {
                    $uploaded = $null
                    if ($Shared.Uploads.TryGetValue([string]$toolArgs.sourceRef, [ref]$uploaded)) {
                        $toolArgs | Add-Member -NotePropertyName 'source' -NotePropertyValue $uploaded -Force
                    } else {
                        Send-Json $context 400 @{ ok = $false; error = "Unknown sourceRef '$($toolArgs.sourceRef)'. Upload the text again with upload_text." }
                        continue
                    }
                }

                # ---------------- ASSET-VORPRUEFUNG ------------------------
                # Die Id muss zum Typ passen, BEVOR Studio angefasst wird.
                # (Vorher lief ein falsches rbxassetid erst als Laufzeitfehler auf.)
                if (($tool -eq 'apply_asset' -or $tool -eq 'insert_asset') -and $toolArgs.assetId -and $toolArgs.skipValidation -ne $true) {
                    $expectType = $null
                    if ($tool -eq 'insert_asset') {
                        $expectType = 'model'
                    } elseif ($toolArgs.property) {
                        $prop = ([string]$toolArgs.property).ToLowerInvariant()
                        if ($prop -eq 'soundid') { $expectType = 'audio' }
                        elseif ($prop -eq 'animationid') { $expectType = 'animation' }
                        elseif ($prop -eq 'texture' -or $prop -eq 'textureid') { $expectType = 'texture' }
                        elseif ($prop -eq 'image') { $expectType = 'image' }
                        elseif ($prop -eq 'meshid') { $expectType = 'mesh' }
                        elseif ($prop -eq 'videoid') { $expectType = 'video' }
                    }
                    if ($expectType) {
                        $validation = Invoke-AssetValidation @{ assetId = [string]$toolArgs.assetId; expectType = $expectType }
                        if ($validation.ok -eq $false) {
                            $validation._bridge = (New-Envelope $sessionId)
                            Send-Json $context 200 $validation
                            continue
                        }
                        if ($validation.verified -eq $true -and $validation.matchesExpect -eq $false) {
                            $mismatch = @{
                                ok = $false
                                code = 'ASSET_TYPE_MISMATCH'
                                error = "Asset $($toolArgs.assetId) is a $($validation.typeName) (typeId $($validation.typeId)), but '$expectType' was expected. It was NOT applied."
                                actual = @{ typeId = $validation.typeId; typeName = $validation.typeName; usableAs = $validation.usableAs; assetName = [string]$validation.assetName }
                                howToFix = "Run search_assets with type='$expectType' and apply a matching id from the result. If the catalog is unavailable, say so and build procedurally - never guess ids."
                            }
                            $mismatch._bridge = (New-Envelope $sessionId)
                            Send-Json $context 200 $mismatch
                            continue
                        }
                        if ($tool -eq 'insert_asset' -and $validation.verified -eq $true -and $validation.hasScripts -eq $true -and $toolArgs.acceptScripts -ne $true) {
                            $hasScripts = @{
                                ok = $false
                                code = 'ASSET_HAS_SCRIPTS'
                                error = "Asset $($toolArgs.assetId) ('$($validation.assetName)') CONTAINS SCRIPTS. It was not inserted."
                                howToFix = 'If you trust this asset, repeat the call with acceptScripts=true - and inspect the inserted content immediately afterwards (search for Script/LocalScript inside it and delete what you did not expect).'
                            }
                            $hasScripts._bridge = (New-Envelope $sessionId)
                            Send-Json $context 200 $hasScripts
                            continue
                        }
                    }
                }

                $serverResult = Invoke-ServerTool $sessionId $tool $toolArgs
                if ($null -ne $serverResult) {
                    $serverResult['_bridge'] = (New-Envelope $sessionId)
                    Send-Json $context 200 $serverResult
                    continue
                }

                $writeTools = @('set_property','set_properties','bulk_set_properties','set_attribute','create_instance','bulk_create',
                    'clone_instance','delete_instance','bulk_delete','rename_instance','move_instance','set_script_source','patch_script',
                    'insert_script','bulk_insert_scripts','select_instance','run_lua','batch','parallel','union','subtract','negate','intersect',
                    'separate','insert_asset','apply_asset','group_instances','ungroup','add_tag','remove_tag','place_on','align','stack',
                    'grid_arrange','distribute','snap_to_ground','look_at','rotate_around','move_relative','resize_part','fit_between','point_at',
                    'play_start','play_stop','play_pause','play_resume','send_input','gui_click','gui_set_text','move_character',
                    'teleport_character','respawn_character','undo','redo','clear_output','fill_region','probe_world','start_job',
                    'cancel_job','clear_lua_state','set_camera')
                $persistentEditTools = @('set_property','set_properties','bulk_set_properties','set_attribute','create_instance','bulk_create',
                    'clone_instance','delete_instance','bulk_delete','rename_instance','move_instance','set_script_source','patch_script',
                    'insert_script','bulk_insert_scripts','run_lua','batch','parallel','union','subtract','negate','intersect','separate',
                    'insert_asset','apply_asset','group_instances','ungroup','add_tag','remove_tag','place_on','align','stack','grid_arrange',
                    'distribute','snap_to_ground','look_at','rotate_around','move_relative','resize_part','fit_between','point_at','fill_region')
                if ($sessionEntry -and $sessionEntry.state -and [bool]$sessionEntry.state.running -and [bool]$sessionEntry.state.userPlaytestActive -and $persistentEditTools -contains $tool) {
                    $blocked = @{
                        ok = $false
                        code = 'USER_PLAYTEST_ACTIVE'
                        severity = 'critical'
                        assistantAction = 'STOP_CURRENT_RESPONSE'
                        error = "IMPORTANT: Roblox Studio is currently in $([string]$sessionEntry.state.mode) mode. The requested edit '$tool' was NOT sent to Studio."
                        why = 'The user is playing/testing the game. Editing now would interrupt them and persistent changes would be discarded when the test ends.'
                        requiredResponse = 'Stop your current response now. Tell the user you can see that Roblox Studio is in a playtest and politely ask them to leave/stop the playtest. Wait until they confirm Edit mode before continuing. Do not call play_stop for them.'
                        suggestedUserMessage = 'Ich sehe, dass du Roblox Studio gerade im Playtest benutzt. Bitte beende den Playtest, damit ich sicher weiterarbeiten kann.'
                    }
                    $blocked._bridge = (New-Envelope $sessionId)
                    Send-Json $context 200 $blocked
                    continue
                }

                if ($accessMode -eq 'readonly' -and $writeTools -contains $tool) {
                    Send-Json $context 200 @{
                        ok = $false
                        code = 'READONLY_TOKEN'
                        error = "The tool '$tool' changes the place, but this token is set to read only."
                        hint = 'The user can switch this place to "Vollzugriff" in the Arena Roblox Bridge window. Until then only reading tools work.'
                    }
                    continue
                }

                $timeout = 60
                if ($toolArgs.timeoutSeconds) {
                    $timeout = [Math]::Min([int]$toolArgs.timeoutSeconds + 25, 180)
                }
                if ($body.timeoutSeconds) {
                    $timeout = [Math]::Min([int]$body.timeoutSeconds, 180)
                }

                # Langer Lauf? Als Job in den Hintergrund - läuft sicher über 60 s hinaus.
                $isJobCall = ($toolArgs.asJob -eq $true) -or ($tool -eq 'start_job')

                $resultJson = Invoke-PluginTool $sessionId $tool $toolArgs $timeout
                if ($null -eq $resultJson) {
                    $entryNow = Get-SessionEntry $sessionId
                    $stillRunning = Get-PendingCommands $sessionId
                    # Bewusst Status 200: die KI soll den Hinweistext lesen können.
                    $timeoutBody = @{
                        ok = $false
                        code = 'STUDIO_TIMEOUT'
                        error = "Roblox Studio did not answer within $timeout seconds."
                        workIsLost = $false
                        hint = 'The command is STILL RUNNING inside Studio - nothing was lost and nothing was killed. Studio executes commands strictly one after another: your next call automatically waits until this one finished (you will never measure against a still-running script). When the result arrives it is delivered in _bridge.lateResults of your next response.'
                        studio = if ($entryNow) { $entryNow.state } else { $null }
                        betterWay = 'For work that takes longer than 60 seconds: repeat this call with args.asJob=true (or use the start_job tool). You get a jobId back immediately and poll it with job_status / job_result - there is no timeout to hit.'
                    }
                    if ($stillRunning.Count -gt 0) {
                        $timeoutBody.pendingInStudio = $stillRunning
                    }
                    if ($isJobCall) {
                        $timeoutBody.note = 'This call was a job call. If it was accepted before the timeout the job is running - use list_jobs / job_status to find it.'
                    }
                    Send-Json $context 200 $timeoutBody
                    continue
                }

                $envelope = New-Envelope $sessionId

                # Start-Doku: nur bei der ersten Tool-Antwort dieser Sitzung,
                # damit die KI ohne Extra-Call ALLE Informationen hat.
                $docsSent = $false
                [void]$Shared.DocsSent.TryGetValue([string]$sessionId, [ref]$docsSent)
                if (-not $docsSent) {
                    $docsSent = $true
                    [void]$Shared.DocsSent.TryAdd([string]$sessionId, $true)
                }

                if ($resultJson.Length -gt $MaxInline) {
                    $blob = New-Blob $resultJson $tool
                    $summary = @{
                        ok = $true
                        delivery = 'chunked'
                        reason = "The answer is $($resultJson.Length) characters long - too big for one response, but nothing was cut off."
                        blobId = $blob.blobId
                        chunkCount = $blob.chunkCount
                        chunkSize = $blob.chunkSize
                        totalChars = $blob.totalChars
                        howTo = "Call the tool get_chunk with { blobId: '$($blob.blobId)', index: 1 } ... up to index $($blob.chunkCount) and concatenate the 'data' fields, then parse the JSON."
                        preview = $resultJson.Substring(0, [Math]::Min(1500, $resultJson.Length))
                        '_bridge' = $envelope
                    }
                    if (-not $docsSent) {
                        $summary._sessionStart = (Get-SessionStartPackage)
                    }
                    Send-Json $context 200 $summary
                    continue
                }

                $merged = Merge-Envelope $resultJson $envelope
                if (-not $docsSent) {
                    $merged = Merge-ExtraJson $merged '_sessionStart' (To-Json (Get-SessionStartPackage) 40)
                }
                Send-RawJson $context 200 $merged
                continue
            }

            Send-Json $context 404 @{ ok = $false; error = 'Route nicht gefunden.' }
        } catch {
            try {
                Send-Json $context 500 @{ ok = $false; error = $_.Exception.Message }
            } catch {}
            try {
                Add-Content -LiteralPath $LogFile -Value ('{0:u} Server Anfrage Fehler: {1}' -f (Get-Date), $_.Exception.Message) -Encoding UTF8
            } catch {}
        }
    } while ($false)
}


# ----------------------------------------------------------------------------
# Listener-Schleife. Jede Anfrage läuft in einem Runspace aus einem Pool.
# Der Pool sorgt dafür, dass mehrere Studio-Fenster (jedes hält einen
# Long-Poll offen) das Programm nicht ausbremsen.
# ----------------------------------------------------------------------------
$script:BridgeListenerScript = {
    param($Port, $Shared, $HandlerScript)

    function Write-BridgeLog {
        param([string]$Text)
        try {
            Add-Content -LiteralPath $Shared.LogFile -Value ('{0:u} {1}' -f (Get-Date), $Text) -Encoding UTF8
        } catch {}
    }

    $listener = [System.Net.HttpListener]::new()
    $listener.Prefixes.Add("http://127.0.0.1:$Port/")
    try {
        $listener.Start()
    } catch {
        Write-BridgeLog "Server: Port $Port konnte nicht geöffnet werden: $($_.Exception.Message)"
        return
    }
    Write-BridgeLog "Server: lauscht auf http://127.0.0.1:$Port/"

    $pool = $null
    try {
        $initialState = [System.Management.Automation.Runspaces.InitialSessionState]::CreateDefault()
        $pool = [runspacefactory]::CreateRunspacePool(2, 32, $initialState, $Host)
        $pool.ApartmentState = 'MTA'
        $pool.Open()
        Write-BridgeLog 'Server: Runspace-Pool bereit (2 bis 32 gleichzeitige Anfragen).'
    } catch {
        Write-BridgeLog "Server: Runspace-Pool konnte nicht geöffnet werden: $($_.Exception.Message)"
        $pool = $null
    }

    $workers = [System.Collections.Generic.List[object]]::new()
    while ($listener.IsListening) {
        $context = $null
        try { $context = $listener.GetContext() } catch { break }

        $ps = [PowerShell]::Create()
        if ($pool) { $ps.RunspacePool = $pool }
        [void]$ps.AddScript($HandlerScript).AddArgument($context).AddArgument($Shared)
        $handle = $ps.BeginInvoke()
        $workers.Add([pscustomobject]@{ Shell = $ps; Handle = $handle })

        if ($workers.Count -ge 24) {
            $remaining = [System.Collections.Generic.List[object]]::new()
            foreach ($worker in $workers) {
                if ($worker.Handle.IsCompleted) {
                    try { $worker.Shell.EndInvoke($worker.Handle) } catch {}
                    try { $worker.Shell.Dispose() } catch {}
                } else {
                    $remaining.Add($worker)
                }
            }
            $workers = $remaining
        }
    }
    foreach ($worker in $workers) {
        try { $worker.Shell.Dispose() } catch {}
    }
    if ($pool) {
        try { $pool.Close() } catch {}
        try { $pool.Dispose() } catch {}
    }
}

function Start-BridgeServer {
    param([int]$Port)

    $handlerText = [string]$script:BridgeHandlerScript
    $ps = [PowerShell]::Create()
    [void]$ps.AddScript([string]$script:BridgeListenerScript).AddArgument($Port).AddArgument($script:Shared).AddArgument($handlerText)
    [void]$ps.BeginInvoke()
    $script:ServerPowerShell = $ps
    Write-RuntimeLog "Lokaler Bridge Server wird auf Port $Port gestartet."
}

# ----------------------------------------------------------------------------
# Tunnel (cloudflared)
# ----------------------------------------------------------------------------
$script:TunnelStreamReaderScript = {
    param($Process, $StreamName, $Queue, $LogFile)
    try {
        $stream = if ($StreamName -eq 'Out') { $Process.StandardOutput } else { $Process.StandardError }
        while ($true) {
            $line = $stream.ReadLine()
            if ($null -eq $line) { break }
            $Queue.Enqueue($line)
            try {
                Add-Content -LiteralPath $LogFile -Value ('{0:u} cloudflared: {1}' -f (Get-Date), $line) -Encoding UTF8
            } catch {}
        }
    } catch {}
}

# ----------------------------------------------------------------------------
# CLOUDFLARED AUTOMATISCH INSTALLIEREN (Version 3.3)
# Fehlt cloudflared, wird es ohne Nachfrage installiert:
#   Weg 1: Download der neuesten offiziellen Version von GitHub (Cloudflare)
#          nach %LOCALAPPDATA%\ArenaRobloxBridge\bin\cloudflared.exe.
#          Braucht keine Admin-Rechte.
#   Weg 2: Klappt der Download nicht, wird winget versucht (falls vorhanden).
# Der Fortschritt wird in der Datei install.status festgehalten. Die
# Oberflaeche (Refresh-Ui) prueft sie regelmaessig, zeigt den Status an und
# startet den Tunnel automatisch, sobald cloudflared verfuegbar ist.
# ----------------------------------------------------------------------------
function Get-CloudflaredPath {
    # 1) Bereits im PATH?
    $command = Get-Command cloudflared -ErrorAction SilentlyContinue
    if ($command) { return $command.Source }
    # 2) Bereits automatisch heruntergeladen (fruehere Starts)?
    $localCopy = Join-Path $script:BinFolder 'cloudflared.exe'
    if (Test-Path -LiteralPath $localCopy) { return $localCopy }
    # 3) Klassische Installation (z.B. per winget/MSI in Program Files)?
    $installRoots = @(${env:ProgramFiles(x86)}, $env:ProgramFiles) | Where-Object { $_ }
    foreach ($root in $installRoots) {
        $candidate = Join-Path $root 'cloudflared\cloudflared.exe'
        if (Test-Path -LiteralPath $candidate) { return $candidate }
    }
    return $null
}

function Update-ProcessPath {
    # PATH aus der Registry neu einlesen. Installationen von aussen (z.B.
    # winget) aktualisieren den PATH eines bereits laufenden Programms nicht
    # von selbst.
    try {
        $machinePath = [System.Environment]::GetEnvironmentVariable('Path', 'Machine')
        $userPath = [System.Environment]::GetEnvironmentVariable('Path', 'User')
        $pathParts = @($machinePath, $userPath) | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
        if ($pathParts.Count -gt 0) { $env:Path = ($pathParts -join ';') }
    } catch {}
}

function Start-CloudflaredInstall {
    # Stoesst die vollautomatische Installation an (lauft im Hintergrund
    # weiter, das Fenster bleibt bedienbar). Refresh-Ui ueberwacht den
    # Fortschritt und startet den Tunnel, sobald die Installation fertig ist.
    if ($script:TunnelInstalling) { return }
    $script:TunnelInstalling = $true
    $script:TunnelInstallFailed = $false
    $script:TunnelInstallMessage = ''
    $script:TunnelInstallStartedAt = Get-Date
    try { New-Item -ItemType Directory -Path $script:BinFolder -Force | Out-Null } catch {}

    $targetPath = Join-Path $script:BinFolder 'cloudflared.exe'
    $statusPath = Join-Path $script:BinFolder 'install.status'

    Write-RuntimeLog 'Cloudflared fehlt - automatische Installation wird gestartet (Download von GitHub, Fallback winget).'
    try {
        if ($script:ToastHost) {
            Show-Toast -Message 'Cloudflared fehlt und wird jetzt automatisch installiert. Der Tunnel startet danach von selbst.' -Kind 'Info' -Seconds 8
        } else {
            Add-PendingToast 'Cloudflared fehlt und wird jetzt automatisch installiert. Der Tunnel startet danach von selbst.' 'Info' 8
        }
    } catch {}

    $installerScript = {
        param([string]$TargetPath, [string]$StatusPath)
        function Write-InstallStatus([string]$Text) {
            try { Set-Content -LiteralPath $StatusPath -Value $Text -Encoding UTF8 } catch {}
        }
        try {
            try { [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.SecurityProtocolType]::Tls12 } catch {}
            $oldProgress = $ProgressPreference
            $ProgressPreference = 'SilentlyContinue'
            $tempPath = "$TargetPath.download"
            if (Test-Path -LiteralPath $tempPath) { Remove-Item -LiteralPath $tempPath -Force }
            Write-InstallStatus 'downloading'
            Invoke-WebRequest -Uri 'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe' -OutFile $tempPath -UseBasicParsing -TimeoutSec 600
            $downloaded = Get-Item -LiteralPath $tempPath
            $head = [byte[]]::new(2)
            $stream = [System.IO.File]::OpenRead($tempPath)
            try { [void]$stream.Read($head, 0, 2) } finally { $stream.Dispose() }
            if ($head[0] -ne 0x4D -or $head[1] -ne 0x5A -or $downloaded.Length -lt 5242880) {
                throw ("Heruntergeladene Datei ist keine gueltige cloudflared.exe ($($downloaded.Length) Bytes).")
            }
            if (Test-Path -LiteralPath $TargetPath) { Remove-Item -LiteralPath $TargetPath -Force }
            Move-Item -LiteralPath $tempPath -Destination $TargetPath -Force
            Write-InstallStatus 'ok'
        } catch {
            $downloadError = $_.Exception.Message
            # Fallback: winget, falls vorhanden
            $wingetCommand = Get-Command winget -ErrorAction SilentlyContinue
            if ($wingetCommand) {
                try {
                    Write-InstallStatus 'winget'
                    $wingetOutput = & $wingetCommand.Source install --id Cloudflare.cloudflared -e --silent --disable-interactivity --accept-source-agreements --accept-package-agreements 2>&1
                    if ($LASTEXITCODE -eq 0) {
                        Write-InstallStatus 'ok'
                    } else {
                        Write-InstallStatus ('error: winget: ' + (($wingetOutput | Out-String).Trim()) + ' / Download: ' + $downloadError)
                    }
                } catch {
                    Write-InstallStatus ('error: winget: ' + $_.Exception.Message + ' / Download: ' + $downloadError)
                }
            } else {
                Write-InstallStatus ('error: ' + $downloadError)
            }
        }
    }

    $installer = [PowerShell]::Create()
    [void]$installer.AddScript($installerScript).AddArgument($targetPath).AddArgument($statusPath)
    [void]$installer.BeginInvoke()
    $script:TunnelInstaller = $installer
}

function Start-CloudflareTunnel {
    param([string]$Protocol = 'auto')
    try {
        $cloudflaredPath = Get-CloudflaredPath
        if (-not $cloudflaredPath) {
            # Nicht installiert: komplett automatische Installation anstossen.
            # Der Tunnel startet sich selbst, sobald der Download fertig ist
            # (siehe Refresh-Ui / Start-CloudflaredInstall).
            Start-CloudflaredInstall
            return
        }

        $arguments = "tunnel --url $script:LocalBaseUrl --no-autoupdate"
        if ($Protocol -and $Protocol -ne 'auto') { $arguments = "$arguments --protocol $Protocol" }

        $psi = [System.Diagnostics.ProcessStartInfo]::new()
        $psi.FileName = $cloudflaredPath
        $psi.Arguments = $arguments
        $psi.UseShellExecute = $false
        $psi.CreateNoWindow = $true
        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError = $true
        $psi.StandardOutputEncoding = [System.Text.Encoding]::UTF8
        $psi.StandardErrorEncoding = [System.Text.Encoding]::UTF8
        $process = [System.Diagnostics.Process]::new()
        $process.StartInfo = $psi
        [void]$process.Start()

        foreach ($streamName in @('Out', 'Err')) {
            $reader = [PowerShell]::Create()
            [void]$reader.AddScript([string]$script:TunnelStreamReaderScript).AddArgument($process).AddArgument($streamName).AddArgument($script:TunnelLines).AddArgument($script:RuntimeLog)
            [void]$reader.BeginInvoke()
            $script:TunnelReaders += $reader
        }
        $script:TunnelProcess = $process
        $script:TunnelStartedAt = Get-Date
        $script:TunnelFailed = $false
        Write-RuntimeLog "Cloudflare-Tunnel-Prozess gestartet (PID $($process.Id), Datei: $cloudflaredPath, Argumente: $arguments)."
    } catch {
        $script:TunnelFailed = $true
        $script:LastTunnelMessage = "Cloudflare-Tunnel-Fehler: $($_.Exception.Message)"
        Write-RuntimeLog $script:LastTunnelMessage
    }
}

function Restart-CloudflareTunnel {
    param([string]$Protocol = 'auto')
    try {
        if ($script:TunnelProcess -and -not $script:TunnelProcess.HasExited) {
            $script:TunnelProcess.Kill()
            Start-Sleep -Milliseconds 600
        }
    } catch {}
    $script:TunnelUrl = $null
    Start-CloudflareTunnel -Protocol $Protocol
}

function Get-StartupEnabled {
    $runKey = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run'
    $props = Get-ItemProperty -Path $runKey -Name 'ArenaRobloxBridge' -ErrorAction SilentlyContinue
    if (-not $props) { return $false }
    $property = $props.PSObject.Properties['ArenaRobloxBridge']
    if (-not $property) { return $false }
    $value = [string]$property.Value
    return -not [string]::IsNullOrWhiteSpace($value)
}

function Set-StartupEnabled {
    param([bool]$Enabled)
    $runKey = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run'
    if ($Enabled) {
        if ($script:IsExeMode -and $script:ExePath) {
            # EXE-Modus: die EXE selbst starten (kein PowerShell-Aufruf noetig).
            $value = "`"$($script:ExePath)`""
        } else {
            $value = "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -STA -File `"$($script:AppRoot)\ArenaBridge.ps1`""
        }
        New-Item -Path $runKey -Force | Out-Null
        Set-ItemProperty -Path $runKey -Name 'ArenaRobloxBridge' -Value $value
    } else {
        Remove-ItemProperty -Path $runKey -Name 'ArenaRobloxBridge' -ErrorAction SilentlyContinue
    }
}

# ----------------------------------------------------------------------------
# SITZUNGEN (ein Studio-Fenster = eine Sitzung = ein Token)
# ----------------------------------------------------------------------------
function Get-ActiveStudios {
    $now = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    $items = New-Object System.Collections.Generic.List[object]
    foreach ($pair in $script:Shared.Sessions.GetEnumerator()) {
        try {
            $item = $pair.Value | ConvertFrom-Json
            $lastSeen = [int64]$item.lastSeen
            $presence = [int64]0
            if ($script:Shared.Presence.TryGetValue([string]$item.sessionId, [ref]$presence)) {
                if ($presence -gt $lastSeen) { $lastSeen = $presence }
            }
            $age = $now - $lastSeen
            if ($age -lt 25) {
                # Sicherheitsnetz gegen kaputte Umlaute in der Anzeige
                $item.placeName = Repair-Mojibake ([string]$item.placeName)
                $items.Add($item)
            } elseif ($age -gt 600) {
                # Alte Sitzungen samt Token aufräumen
                $removedJson = $null
                [void]$script:Shared.Sessions.TryRemove([string]$item.sessionId, [ref]$removedJson)
                $token = $null
                if ($script:Shared.SessionTokens.TryRemove([string]$item.sessionId, [ref]$token)) {
                    $removedSession = $null
                    [void]$script:Shared.TokenSessions.TryRemove($token, [ref]$removedSession)
                }
            }
        } catch {}
    }
    $items | Sort-Object placeName, sessionId
}

function Reset-SessionToken {
    param([string]$SessionId)
    $old = $null
    if ($script:Shared.SessionTokens.TryRemove($SessionId, [ref]$old)) {
        $removed = $null
        [void]$script:Shared.TokenSessions.TryRemove($old, [ref]$removed)
    }
    $new = New-Token
    $script:Shared.SessionTokens[$SessionId] = $new
    $script:Shared.TokenSessions[$new] = $SessionId
    Write-RuntimeLog "Token fuer Sitzung $SessionId neu vergeben."
}

function Set-SessionMode {
    param([string]$SessionId, [string]$Mode)
    $script:Shared.AccessModes[$SessionId] = $Mode
}

# ----------------------------------------------------------------------------
# HILFSFUNKTIONEN FUER DIE OBERFLAECHE
# ----------------------------------------------------------------------------
$script:BrushCache = @{}
function Get-Brush {
    param([string]$Hex)
    $key = $Hex.ToUpperInvariant()
    if (-not $script:BrushCache.ContainsKey($key)) {
        $color = [System.Windows.Media.ColorConverter]::ConvertFromString($Hex)
        $brush = [System.Windows.Media.SolidColorBrush]::new($color)
        $brush.Freeze()
        $script:BrushCache[$key] = $brush
    }
    return $script:BrushCache[$key]
}

function New-Shadow {
    param([double]$Blur = 20, [double]$Opacity = 0.5, [string]$Color = '#000000')
    $shadow = [System.Windows.Media.Effects.DropShadowEffect]::new()
    $shadow.Color = [System.Windows.Media.ColorConverter]::ConvertFromString($Color)
    $shadow.BlurRadius = $Blur
    $shadow.ShadowDepth = 0
    $shadow.Opacity = $Opacity
    $shadow.Direction = 270
    return $shadow
}

function New-CheckPath {
    param([string]$Color = '#FFFFFF')
    $path = [System.Windows.Shapes.Path]::new()
    $path.Data = [System.Windows.Media.Geometry]::Parse('M 4,10.4 L 8,14.4 L 16,5.2')
    $path.Stroke = Get-Brush $Color
    $path.StrokeThickness = 2.2
    $path.StrokeStartLineCap = 'Round'
    $path.StrokeEndLineCap = 'Round'
    $path.HorizontalAlignment = 'Center'
    $path.VerticalAlignment = 'Center'
    return $path
}

function Set-Text {
    param($Element, [string]$Value)
    if ($null -eq $Element) { return }
    if ([string]$Element.Text -ne $Value) { $Element.Text = $Value }
}

function Set-Dot {
    param($Element, [string]$Hex)
    if ($null -eq $Element) { return }
    if ([string]$Element.Tag -ne $Hex) {
        $Element.Tag = $Hex
        $Element.Fill = Get-Brush $Hex
    }
}

$script:ColorGreen  = '#22C55E'
$script:ColorAmber  = '#F5A524'
$script:ColorRed    = '#F2565B'
$script:ColorBlue   = '#FF4FA3'
$script:ColorGray   = '#746A70'


# ----------------------------------------------------------------------------
# OBERFLAECHE (XAML)
# ----------------------------------------------------------------------------
$xaml = @'
<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
        Title="Arena Roblox Bridge"
        Width="900" Height="600"
        MinWidth="900" MinHeight="600" MaxWidth="900" MaxHeight="600"
        ResizeMode="NoResize"
        WindowStyle="None"
        AllowsTransparency="True"
        Background="Transparent"
        WindowStartupLocation="CenterScreen"
        FontFamily="Segoe UI">
    <Window.Resources>
        <SolidColorBrush x:Key="TextMain" Color="#F7F1F5"/>
        <SolidColorBrush x:Key="TextSoft" Color="#D8CDD4"/>
        <SolidColorBrush x:Key="TextMuted" Color="#A99DA5"/>
        <SolidColorBrush x:Key="TextFaint" Color="#80767D"/>
        <SolidColorBrush x:Key="Line" Color="#443740"/>

        <LinearGradientBrush x:Key="AppBg" StartPoint="0,0" EndPoint="1,1">
            <GradientStop Color="#171417" Offset="0"/>
            <GradientStop Color="#0D0B0D" Offset="1"/>
        </LinearGradientBrush>
        <LinearGradientBrush x:Key="TitleBg" StartPoint="0,0" EndPoint="1,0">
            <GradientStop Color="#21191F" Offset="0"/>
            <GradientStop Color="#120F12" Offset="1"/>
        </LinearGradientBrush>
        <LinearGradientBrush x:Key="LogoBrush" StartPoint="0,0" EndPoint="1,1">
            <GradientStop Color="#FF4FA3" Offset="0"/>
            <GradientStop Color="#C42D79" Offset="1"/>
        </LinearGradientBrush>
        <LinearGradientBrush x:Key="SweepBrush" StartPoint="0,0" EndPoint="1,0">
            <GradientStop Color="#00000000" Offset="0"/>
            <GradientStop Color="#FF70B5" Offset="0.5"/>
            <GradientStop Color="#00000000" Offset="1"/>
        </LinearGradientBrush>
        <LinearGradientBrush x:Key="BtnBg" StartPoint="0,0" EndPoint="0,1">
            <GradientStop Color="#B82970" Offset="0"/>
            <GradientStop Color="#7D1D4D" Offset="1"/>
        </LinearGradientBrush>

        <Style TargetType="Button">
            <Setter Property="Foreground" Value="#FFF7FB"/>
            <Setter Property="Background" Value="{StaticResource BtnBg}"/>
            <Setter Property="BorderBrush" Value="#FF4FA3"/>
            <Setter Property="BorderThickness" Value="1"/>
            <Setter Property="Padding" Value="14,9"/>
            <Setter Property="FontSize" Value="12.5"/>
            <Setter Property="FontWeight" Value="SemiBold"/>
            <Setter Property="Cursor" Value="Hand"/>
            <Setter Property="Template">
                <Setter.Value>
                    <ControlTemplate TargetType="Button">
                        <Border x:Name="bd" CornerRadius="9"
                                Background="{TemplateBinding Background}"
                                BorderBrush="{TemplateBinding BorderBrush}"
                                BorderThickness="{TemplateBinding BorderThickness}">
                            <ContentPresenter HorizontalAlignment="Center" VerticalAlignment="Center" Margin="{TemplateBinding Padding}"/>
                        </Border>
                        <ControlTemplate.Triggers>
                            <Trigger Property="IsMouseOver" Value="True">
                                <Setter TargetName="bd" Property="Background" Value="#D93E88"/>
                                <Setter TargetName="bd" Property="BorderBrush" Value="#FF9DCC"/>
                            </Trigger>
                            <Trigger Property="IsPressed" Value="True">
                                <Setter TargetName="bd" Property="Background" Value="#741A47"/>
                            </Trigger>
                            <Trigger Property="IsEnabled" Value="False">
                                <Setter TargetName="bd" Property="Opacity" Value="0.45"/>
                            </Trigger>
                        </ControlTemplate.Triggers>
                    </ControlTemplate>
                </Setter.Value>
            </Setter>
        </Style>

        <Style x:Key="TitleButtonStyle" TargetType="Button">
            <Setter Property="Foreground" Value="#C8BBC3"/>
            <Setter Property="Background" Value="#292329"/>
            <Setter Property="BorderBrush" Value="#4C3A45"/>
            <Setter Property="BorderThickness" Value="1"/>
            <Setter Property="Padding" Value="0"/>
            <Setter Property="Cursor" Value="Hand"/>
            <Setter Property="Template">
                <Setter.Value>
                    <ControlTemplate TargetType="Button">
                        <Border x:Name="bd" CornerRadius="10"
                                Background="{TemplateBinding Background}"
                                BorderBrush="{TemplateBinding BorderBrush}"
                                BorderThickness="{TemplateBinding BorderThickness}">
                            <ContentPresenter HorizontalAlignment="Center" VerticalAlignment="Center"/>
                        </Border>
                        <ControlTemplate.Triggers>
                            <Trigger Property="IsMouseOver" Value="True">
                                <Setter TargetName="bd" Property="Background" Value="#3A2C35"/>
                                <Setter TargetName="bd" Property="BorderBrush" Value="#DA4B91"/>
                                <Setter Property="Foreground" Value="#FFFFFF"/>
                            </Trigger>
                            <Trigger Property="IsPressed" Value="True">
                                <Setter TargetName="bd" Property="Background" Value="#241B21"/>
                            </Trigger>
                        </ControlTemplate.Triggers>
                    </ControlTemplate>
                </Setter.Value>
            </Setter>
        </Style>

        <Style x:Key="CloseButtonStyle" TargetType="Button">
            <Setter Property="Foreground" Value="#F0A7B4"/>
            <Setter Property="Background" Value="#2A1220"/>
            <Setter Property="BorderBrush" Value="#7F244D"/>
            <Setter Property="BorderThickness" Value="1"/>
            <Setter Property="Padding" Value="0"/>
            <Setter Property="Cursor" Value="Hand"/>
            <Setter Property="Template">
                <Setter.Value>
                    <ControlTemplate TargetType="Button">
                        <Border x:Name="bd" CornerRadius="10"
                                Background="{TemplateBinding Background}"
                                BorderBrush="{TemplateBinding BorderBrush}"
                                BorderThickness="{TemplateBinding BorderThickness}">
                            <ContentPresenter HorizontalAlignment="Center" VerticalAlignment="Center"/>
                        </Border>
                        <ControlTemplate.Triggers>
                            <Trigger Property="IsMouseOver" Value="True">
                                <Setter TargetName="bd" Property="Background" Value="#E0365A"/>
                                <Setter TargetName="bd" Property="BorderBrush" Value="#FF7A94"/>
                                <Setter Property="Foreground" Value="#FFFFFF"/>
                            </Trigger>
                            <Trigger Property="IsPressed" Value="True">
                                <Setter TargetName="bd" Property="Background" Value="#B01B3D"/>
                            </Trigger>
                        </ControlTemplate.Triggers>
                    </ControlTemplate>
                </Setter.Value>
            </Setter>
        </Style>

        <Style x:Key="StatCardStyle" TargetType="Border">
            <Setter Property="Background" Value="#211C20"/>
            <Setter Property="BorderBrush" Value="#443740"/>
            <Setter Property="BorderThickness" Value="1"/>
            <Setter Property="CornerRadius" Value="11"/>
            <Setter Property="Padding" Value="15,13"/>
            <Style.Triggers>
                <Trigger Property="IsMouseOver" Value="True">
                    <Setter Property="Background" Value="#30262C"/>
                    <Setter Property="BorderBrush" Value="#6B485B"/>
                </Trigger>
            </Style.Triggers>
        </Style>

        <Style TargetType="CheckBox">
            <Setter Property="Foreground" Value="#F7F1F5"/>
            <Setter Property="FontSize" Value="13"/>
            <Setter Property="Cursor" Value="Hand"/>
            <Setter Property="Template">
                <Setter.Value>
                    <ControlTemplate TargetType="CheckBox">
                        <Grid>
                            <Grid.ColumnDefinitions>
                                <ColumnDefinition Width="Auto"/>
                                <ColumnDefinition Width="*"/>
                            </Grid.ColumnDefinitions>
                            <Border x:Name="box" Width="20" Height="20" CornerRadius="6"
                                    Background="#181417" BorderBrush="#6B485B" BorderThickness="1">
                                <Path x:Name="tick"
                                      Data="M 4,10.4 L 8,14.4 L 16,5.2"
                                      Stroke="#FFFFFF" StrokeThickness="2.2"
                                      StrokeStartLineCap="Round" StrokeEndLineCap="Round"
                                      HorizontalAlignment="Center" VerticalAlignment="Center"
                                      Visibility="Collapsed"/>
                            </Border>
                            <ContentPresenter Grid.Column="1" Margin="11,0,0,0" VerticalAlignment="Center" RecognizesAccessKey="True"/>
                        </Grid>
                        <ControlTemplate.Triggers>
                            <Trigger Property="IsChecked" Value="True">
                                <Setter TargetName="box" Property="Background" Value="#FF4FA3"/>
                                <Setter TargetName="box" Property="BorderBrush" Value="#FF70B5"/>
                                <Setter TargetName="tick" Property="Visibility" Value="Visible"/>
                            </Trigger>
                        </ControlTemplate.Triggers>
                    </ControlTemplate>
                </Setter.Value>
            </Setter>
        </Style>

        <Style TargetType="ScrollBar">
            <Setter Property="Width" Value="10"/>
            <Setter Property="MinWidth" Value="10"/>
            <Setter Property="Background" Value="Transparent"/>
            <Setter Property="BorderBrush" Value="Transparent"/>
            <Setter Property="SnapsToDevicePixels" Value="True"/>
            <Setter Property="Template">
                <Setter.Value>
                    <ControlTemplate TargetType="ScrollBar">
                        <Grid Margin="2,3,2,3">
                            <Border CornerRadius="5" Background="#0A1428"/>
                            <Track x:Name="PART_Track" IsDirectionReversed="True" Focusable="False">
                                <Track.DecreaseRepeatButton>
                                    <RepeatButton Command="ScrollBar.PageUpCommand" Focusable="False" IsTabStop="False">
                                        <RepeatButton.Template>
                                            <ControlTemplate TargetType="RepeatButton">
                                                <Border Background="Transparent"/>
                                            </ControlTemplate>
                                        </RepeatButton.Template>
                                    </RepeatButton>
                                </Track.DecreaseRepeatButton>
                                <Track.Thumb>
                                    <Thumb Focusable="False" IsTabStop="False">
                                        <Thumb.Template>
                                            <ControlTemplate TargetType="Thumb">
                                                <Border CornerRadius="4" Background="#6B485B" Margin="1,0,1,0"/>
                                            </ControlTemplate>
                                        </Thumb.Template>
                                    </Thumb>
                                </Track.Thumb>
                                <Track.IncreaseRepeatButton>
                                    <RepeatButton Command="ScrollBar.PageDownCommand" Focusable="False" IsTabStop="False">
                                        <RepeatButton.Template>
                                            <ControlTemplate TargetType="RepeatButton">
                                                <Border Background="Transparent"/>
                                            </ControlTemplate>
                                        </RepeatButton.Template>
                                    </RepeatButton>
                                </Track.IncreaseRepeatButton>
                            </Track>
                        </Grid>
                    </ControlTemplate>
                </Setter.Value>
            </Setter>
        </Style>
    </Window.Resources>

    <Border CornerRadius="22" Background="{StaticResource AppBg}" BorderBrush="#684154" BorderThickness="1" ClipToBounds="True">
        <Grid>
            <Grid.RowDefinitions>
                <RowDefinition Height="72"/>
                <RowDefinition Height="*"/>
            </Grid.RowDefinitions>

            <Border x:Name="TitleBar" Grid.Row="0" Background="{StaticResource TitleBg}" BorderBrush="#3B3036" BorderThickness="0,0,0,1" CornerRadius="21,21,0,0" ClipToBounds="True">
                <Grid Margin="24,0">
                    <Grid.ColumnDefinitions>
                        <ColumnDefinition Width="*"/>
                        <ColumnDefinition Width="Auto"/>
                    </Grid.ColumnDefinitions>

                    <StackPanel Orientation="Horizontal" VerticalAlignment="Center">
                        <Grid Width="38" Height="38" Margin="0,0,13,0">
                            <Border Width="38" Height="38" CornerRadius="12" Background="{StaticResource LogoBrush}"/>
                            <Ellipse Width="7" Height="7" Fill="#FFF7FB" HorizontalAlignment="Left" VerticalAlignment="Center" Margin="6,0,0,0"/>
                            <Ellipse Width="7" Height="7" Fill="#FFF7FB" HorizontalAlignment="Right" VerticalAlignment="Center" Margin="0,0,6,0"/>
                            <Rectangle Height="2.6" Fill="#F5D9E8" Margin="13,0,13,0" RadiusX="1.3" RadiusY="1.3"/>
                            <Ellipse x:Name="PulseDot" Width="9" Height="9" Fill="#FF85BE"
                                     HorizontalAlignment="Right" VerticalAlignment="Bottom" Margin="0,0,-1,-1">
                                <Ellipse.Effect>
                                    <DropShadowEffect Color="#FF70B5" BlurRadius="10" ShadowDepth="0" Opacity="0.9"/>
                                </Ellipse.Effect>
                            </Ellipse>
                        </Grid>
                        <StackPanel VerticalAlignment="Center">
                            <TextBlock Text="Arena Roblox Bridge" Foreground="{StaticResource TextMain}" FontSize="18.5" FontWeight="Bold"/>
                            <TextBlock x:Name="SubtitleText" Text="Verbindung zu Roblox Studio wird vorbereitet" Foreground="{StaticResource TextMuted}" FontSize="11.5" Margin="0,3,0,0"/>
                        </StackPanel>
                    </StackPanel>

                    <StackPanel Grid.Column="1" Orientation="Horizontal" VerticalAlignment="Center">
                        <Border x:Name="LiveBadge" CornerRadius="11" Background="#12233F" BorderBrush="#6B485B" BorderThickness="1" Padding="12,6" Margin="0,0,12,0" VerticalAlignment="Center">
                            <StackPanel Orientation="Horizontal" VerticalAlignment="Center">
                                <Ellipse x:Name="LiveDot" Width="8" Height="8" Fill="#F5A524" Margin="0,0,8,0" VerticalAlignment="Center"/>
                                <TextBlock x:Name="LiveText" Text="Startet" Foreground="{StaticResource TextSoft}" FontSize="11.5" FontWeight="SemiBold" VerticalAlignment="Center"/>
                            </StackPanel>
                        </Border>
                        <Grid Width="40" Height="36" Margin="0,0,8,0">
                            <Button x:Name="SettingsButton" Style="{StaticResource TitleButtonStyle}" Width="40" Height="36" FontFamily="Segoe MDL2 Assets" FontSize="15" Content="&#xE713;"/>
                            <!-- Rote "1" fuer Update-Fehler (Version 3.7) -->
                            <Border x:Name="UpdateBadge" Width="16" Height="16" CornerRadius="8"
                                    Background="#F2565B" BorderBrush="#171417" BorderThickness="2"
                                    HorizontalAlignment="Right" VerticalAlignment="Top" Margin="0,-4,-4,0"
                                    Visibility="Collapsed" Panel.ZIndex="90" IsHitTestVisible="False"
                                    ToolTip="Update-Problem - klicke auf die Einstellungen für Details">
                                <TextBlock Text="1" Foreground="#FFFFFF" FontSize="9.5" FontWeight="Bold"
                                           HorizontalAlignment="Center" VerticalAlignment="Center"/>
                            </Border>
                        </Grid>
                        <Button x:Name="MinimizeButton" Style="{StaticResource TitleButtonStyle}" Width="40" Height="36" Margin="0,0,8,0" FontFamily="Segoe MDL2 Assets" FontSize="12" Content="&#xE921;"/>
                        <Button x:Name="CloseButton" Style="{StaticResource CloseButtonStyle}" Width="40" Height="36" FontFamily="Segoe MDL2 Assets" FontSize="12" Content="&#xE8BB;"/>
                    </StackPanel>

                    <Border Grid.ColumnSpan="2" VerticalAlignment="Bottom" Height="2" Margin="-24,0,-24,0" ClipToBounds="True">
                        <Rectangle x:Name="SweepRect" Width="260" Height="2" HorizontalAlignment="Left" Fill="{StaticResource SweepBrush}">
                            <Rectangle.RenderTransform>
                                <TranslateTransform X="-320"/>
                            </Rectangle.RenderTransform>
                            <Rectangle.Triggers>
                                <EventTrigger RoutedEvent="Loaded">
                                    <BeginStoryboard>
                                        <Storyboard>
                                            <DoubleAnimation Storyboard.TargetName="SweepRect"
                                                             Storyboard.TargetProperty="(UIElement.RenderTransform).(TranslateTransform.X)"
                                                             From="-320" To="1180" Duration="0:0:4" RepeatBehavior="Forever"/>
                                        </Storyboard>
                                    </BeginStoryboard>
                                </EventTrigger>
                            </Rectangle.Triggers>
                        </Rectangle>
                    </Border>
                </Grid>
            </Border>

            <Grid Grid.Row="1" Margin="26,20,26,22">

                <Border CornerRadius="14" Background="#091321" BorderBrush="#193463" BorderThickness="1" ClipToBounds="True">
                    <Grid>
                        <Grid.RowDefinitions>
                            <RowDefinition Height="Auto"/>
                            <RowDefinition Height="*"/>
                        </Grid.RowDefinitions>

                        <Border Grid.Row="0" Background="#0D1A2E" BorderBrush="#3B3036" BorderThickness="0,0,0,1" Padding="18,12">
                            <Grid>
                                <StackPanel Orientation="Horizontal" VerticalAlignment="Center">
                                    <TextBlock Text="Verbundene Places" Foreground="{StaticResource TextMain}" FontSize="13.5" FontWeight="SemiBold"/>
                                    <Border x:Name="PlacesCountBadge" CornerRadius="8" Background="#12305C" Padding="9,3" Margin="10,0,0,0" VerticalAlignment="Center">
                                        <TextBlock x:Name="PlacesCountText" Text="0" Foreground="#FF9DCC" FontSize="11" FontWeight="Bold"/>
                                    </Border>
                                </StackPanel>
                                <TextBlock HorizontalAlignment="Right" VerticalAlignment="Center" Text="Automatisch verbunden" Foreground="{StaticResource TextFaint}" FontSize="11"/>
                            </Grid>
                        </Border>

                        <Grid Grid.Row="1">
                            <StackPanel x:Name="EmptyState" HorizontalAlignment="Center" VerticalAlignment="Center" Width="430">
                                <Border Width="76" Height="76" CornerRadius="22" Background="#211A1E" BorderBrush="#4C3A45" BorderThickness="1" HorizontalAlignment="Center">
                                    <Grid>
                                        <Ellipse Width="10" Height="10" Fill="#FF4FA3" HorizontalAlignment="Left" VerticalAlignment="Center" Margin="15,0,0,0"/>
                                        <Ellipse Width="10" Height="10" Fill="#C42D79" HorizontalAlignment="Right" VerticalAlignment="Center" Margin="0,0,15,0"/>
                                        <Rectangle Height="3" Fill="#D94B8E" Margin="30,0,30,0" RadiusX="1.5" RadiusY="1.5"/>
                                    </Grid>
                                </Border>
                                <TextBlock x:Name="EmptyTitle" Text="Öffne ein Place in Roblox Studio" Foreground="{StaticResource TextMain}" FontSize="21" FontWeight="Bold" TextAlignment="Center" Margin="0,22,0,0"/>
                                <TextBlock x:Name="EmptyBody" Text="Sobald sich ein Studio-Fenster mit einem geladenen Place verbindet, erscheint es hier automatisch." Foreground="{StaticResource TextMuted}" FontSize="13.5" TextAlignment="Center" TextWrapping="Wrap" Margin="0,10,0,0"/>
                            </StackPanel>
                            <ScrollViewer VerticalScrollBarVisibility="Auto" HorizontalScrollBarVisibility="Disabled" Padding="14" Margin="0,0,0,0">
                                <StackPanel x:Name="PlaceList"/>
                            </ScrollViewer>
                        </Grid>
                    </Grid>
                </Border>

                <!-- ============================================================ -->
                <!-- STARTBILDSCHIRM (Version 3.4): Ladekreisel mit Fortschritt.  -->
                <!-- Ersetzt die drei frueheren Status-Kaerten. Die Spieleliste  -->
                <!-- dahinter erscheint erst, wenn alles bereit ist.             -->
                <!-- ============================================================ -->
                <Border x:Name="SplashScreen" Panel.ZIndex="70" Background="#141114" CornerRadius="14" ClipToBounds="True">
                    <Grid>
                        <StackPanel HorizontalAlignment="Center" VerticalAlignment="Center" Width="400" Margin="0,-10,0,0">
                            <Grid Width="86" Height="86" Margin="0,0,0,24" HorizontalAlignment="Center">
                                <Ellipse Stroke="#4A3541" StrokeThickness="6"/>
                                <Ellipse x:Name="SplashSpinnerArc" Stroke="#FF4FA3" StrokeThickness="6" StrokeDashArray="44 158" StrokeDashCap="Round" RenderTransformOrigin="0.5,0.5">
                                    <Ellipse.RenderTransform>
                                        <RotateTransform Angle="0"/>
                                    </Ellipse.RenderTransform>
                                    <Ellipse.Triggers>
                                        <EventTrigger RoutedEvent="Loaded">
                                            <BeginStoryboard>
                                                <Storyboard>
                                                    <DoubleAnimation Storyboard.TargetName="SplashSpinnerArc"
                                                                     Storyboard.TargetProperty="(UIElement.RenderTransform).(RotateTransform.Angle)"
                                                                     From="0" To="360" Duration="0:0:1.05" RepeatBehavior="Forever"/>
                                                </Storyboard>
                                            </BeginStoryboard>
                                        </EventTrigger>
                                    </Ellipse.Triggers>
                                </Ellipse>
                                <Grid Width="32" Height="30" HorizontalAlignment="Center" VerticalAlignment="Center">
                                    <Ellipse Width="7" Height="7" Fill="#FF70B5" HorizontalAlignment="Left" VerticalAlignment="Center" Margin="1,0,0,0"/>
                                    <Ellipse Width="7" Height="7" Fill="#FF91C7" HorizontalAlignment="Right" VerticalAlignment="Center" Margin="0,0,1,0"/>
                                    <Rectangle Height="2.6" Fill="#E65A9C" Margin="11,0,11,0" RadiusX="1.3" RadiusY="1.3"/>
                                </Grid>
                            </Grid>
                            <TextBlock x:Name="SplashHeadline" Text="Arena Roblox Bridge startet …" Foreground="{StaticResource TextMain}" FontSize="19" FontWeight="Bold" TextAlignment="Center"/>
                            <TextBlock x:Name="SplashSub" Text="Alles wird automatisch vorbereitet - du musst nichts tun." Foreground="{StaticResource TextMuted}" FontSize="12.5" TextAlignment="Center" TextWrapping="Wrap" Margin="0,9,0,24"/>
                            <Border CornerRadius="13" Background="#211C20" BorderBrush="#443740" BorderThickness="1" Padding="18,14">
                                <StackPanel>
                                    <Grid>
                                        <Grid.ColumnDefinitions>
                                            <ColumnDefinition Width="Auto"/>
                                            <ColumnDefinition Width="*"/>
                                            <ColumnDefinition Width="Auto"/>
                                        </Grid.ColumnDefinitions>
                                        <Ellipse x:Name="SplashStudioDot" Grid.Column="0" Width="9" Height="9" Fill="#746A70" Margin="0,0,12,0" VerticalAlignment="Center"/>
                                        <TextBlock Grid.Column="1" Text="Roblox Studio" Foreground="#D8CDD4" FontSize="13.5" VerticalAlignment="Center"/>
                                        <TextBlock x:Name="SplashStudioState" Grid.Column="2" Text="Wird geprüft …" Foreground="#A99DA5" FontSize="12" VerticalAlignment="Center"/>
                                    </Grid>
                                    <Border Height="1" Background="#3B3036" Margin="0,11,0,11"/>
                                    <Grid>
                                        <Grid.ColumnDefinitions>
                                            <ColumnDefinition Width="Auto"/>
                                            <ColumnDefinition Width="*"/>
                                            <ColumnDefinition Width="Auto"/>
                                        </Grid.ColumnDefinitions>
                                        <Ellipse x:Name="SplashPluginDot" Grid.Column="0" Width="9" Height="9" Fill="#746A70" Margin="0,0,12,0" VerticalAlignment="Center"/>
                                        <TextBlock Grid.Column="1" Text="Studio-Plugin" Foreground="#D8CDD4" FontSize="13.5" VerticalAlignment="Center"/>
                                        <TextBlock x:Name="SplashPluginState" Grid.Column="2" Text="Wartet …" Foreground="#A99DA5" FontSize="12" VerticalAlignment="Center"/>
                                    </Grid>
                                    <Border Height="1" Background="#3B3036" Margin="0,11,0,11"/>
                                    <Grid>
                                        <Grid.ColumnDefinitions>
                                            <ColumnDefinition Width="Auto"/>
                                            <ColumnDefinition Width="*"/>
                                            <ColumnDefinition Width="Auto"/>
                                        </Grid.ColumnDefinitions>
                                        <Ellipse x:Name="SplashTunnelDot" Grid.Column="0" Width="9" Height="9" Fill="#746A70" Margin="0,0,12,0" VerticalAlignment="Center"/>
                                        <TextBlock Grid.Column="1" Text="Cloudflare-Tunnel" Foreground="#D8CDD4" FontSize="13.5" VerticalAlignment="Center"/>
                                        <TextBlock x:Name="SplashTunnelState" Grid.Column="2" Text="Wartet …" Foreground="#A99DA5" FontSize="12" VerticalAlignment="Center"/>
                                    </Grid>
                                </StackPanel>
                            </Border>
                        </StackPanel>
                    </Grid>
                </Border>

            </Grid>

            <Border x:Name="SettingsPanel" Grid.Row="1" Visibility="Collapsed" Panel.ZIndex="60"
                    HorizontalAlignment="Right" VerticalAlignment="Top" Width="300"
                    CornerRadius="14" Background="#211A1F" BorderBrush="#FF4FA3" BorderThickness="1"
                    Padding="18" Margin="0,6,54,0">
                <Border.Effect>
                    <DropShadowEffect Color="#000000" Opacity="0.55" BlurRadius="22" ShadowDepth="0"/>
                </Border.Effect>
                <StackPanel>
                    <TextBlock Text="Einstellungen" Foreground="{StaticResource TextMain}" FontSize="16" FontWeight="Bold"/>
                    <TextBlock Text="Programmoptionen für diese Bridge" Foreground="{StaticResource TextMuted}" FontSize="11.5" Margin="0,4,0,0"/>
                    <Border Height="1" Background="{StaticResource Line}" Margin="0,15,0,15"/>
                    <CheckBox x:Name="StartupCheckBox" Content="Beim PC-Start automatisch öffnen"/>
                    <TextBlock Text="Startet Arena Roblox Bridge automatisch mit Windows und verbindet Places im Hintergrund." Foreground="{StaticResource TextFaint}" FontSize="11" TextWrapping="Wrap" Margin="31,7,0,0"/>
                    <Border Height="1" Background="{StaticResource Line}" Margin="0,16,0,13"/>
                    <TextBlock x:Name="UpdateInfoTitle" Text="UPDATES" Foreground="{StaticResource TextMuted}" FontSize="10.5" FontWeight="Bold"/>
                    <TextBlock x:Name="UpdateInfoText" Text="Version 3.7" Foreground="{StaticResource TextFaint}" FontSize="11" TextWrapping="Wrap" Margin="0,7,0,0"/>
                    <Border Height="1" Background="{StaticResource Line}" Margin="0,14,0,13"/>
                    <TextBlock Text="Arena Roblox Bridge - Version 3.7" Foreground="{StaticResource TextFaint}" FontSize="11"/>
                </StackPanel>
            </Border>
        </Grid>
    </Border>
</Window>
'@

$reader = [System.Xml.XmlNodeReader]::new([xml]$xaml)
$window = [Windows.Markup.XamlReader]::Load($reader)

$window.Dispatcher.add_UnhandledException({
    param($sender, $eventArgs)
    try {
        Write-RuntimeLog "UI Fehler: $($eventArgs.Exception.Message)"
    } catch {}
    $eventArgs.Handled = $true
})

$TitleBar        = $window.FindName('TitleBar')
$SubtitleText    = $window.FindName('SubtitleText')
$SplashScreen    = $window.FindName('SplashScreen')
$SplashHeadline  = $window.FindName('SplashHeadline')
$SplashSub       = $window.FindName('SplashSub')
$SplashStudioDot    = $window.FindName('SplashStudioDot')
$SplashStudioState  = $window.FindName('SplashStudioState')
$SplashPluginDot    = $window.FindName('SplashPluginDot')
$SplashPluginState  = $window.FindName('SplashPluginState')
$SplashTunnelDot    = $window.FindName('SplashTunnelDot')
$SplashTunnelState  = $window.FindName('SplashTunnelState')
$PlaceList       = $window.FindName('PlaceList')
$EmptyState      = $window.FindName('EmptyState')
$EmptyTitle      = $window.FindName('EmptyTitle')
$EmptyBody       = $window.FindName('EmptyBody')
$PlacesCountText = $window.FindName('PlacesCountText')
$LiveBadge       = $window.FindName('LiveBadge')
$LiveDot         = $window.FindName('LiveDot')
$LiveText        = $window.FindName('LiveText')
$SettingsPanel   = $window.FindName('SettingsPanel')
$StartupCheckBox = $window.FindName('StartupCheckBox')
$SettingsButton  = $window.FindName('SettingsButton')
$UpdateBadge     = $window.FindName('UpdateBadge')
$UpdateInfoTitle = $window.FindName('UpdateInfoTitle')
$UpdateInfoText  = $window.FindName('UpdateInfoText')
$MinimizeButton  = $window.FindName('MinimizeButton')
$CloseButton     = $window.FindName('CloseButton')
$PulseDot        = $window.FindName('PulseDot')

# ----------------------------------------------------------------------------
# KLEINE MITTEILUNGEN (ersetzen die alte Fusszeile)
# Jede Mitteilung hat einen Balken, der zeigt, wann sie wieder verschwindet.
# ----------------------------------------------------------------------------
$script:ToastMax = 4

function Remove-Toast {
    param($Card)
    try {
        $state = $Card.Tag
        if ($state.Removing) { return }
        $state.Removing = $true
        $fade = [System.Windows.Media.Animation.DoubleAnimation]::new(1, 0, [System.TimeSpan]::FromMilliseconds(240))
        $move = [System.Windows.Media.Animation.DoubleAnimation]::new(0, 10, [System.TimeSpan]::FromMilliseconds(240))
        $Card.BeginAnimation([System.Windows.UIElement]::OpacityProperty, $fade)
        if ($Card.RenderTransform -is [System.Windows.Media.TranslateTransform]) {
            $Card.RenderTransform.BeginAnimation([System.Windows.Media.TranslateTransform]::YProperty, $move)
        }
        $cleanup = [System.Windows.Threading.DispatcherTimer]::new()
        $cleanup.Interval = [System.TimeSpan]::FromMilliseconds(320)
        # WICHTIG: KeineClosure auf lokale Variablen - Event-Handler in
        # PowerShell sehen lokale Variablen einer Funktion nicht. Alles wird
        # ueber den Sender ($s) und dessen Tag uebergeben.
        $cleanup.Tag = $Card
        $cleanup.Add_Tick({
            param($s, $e)
            $s.Stop()
            try { $script:ToastHost.Children.Remove($s.Tag) } catch {}
        })
        $cleanup.Start()
    } catch {}
}

function Show-Toast {
    # Version 3.7: Popup-Nachrichten unten rechts sind ENTFERNT.
    # Die Funktion bleibt als leerer Stummel erhalten, damit alle alten
    # Aufrufstellen weiterlaufen, ohne etwas anzuzeigen.
    param(
        [string]$Message,
        [string]$Kind = 'Info',
        [double]$Seconds = 4.5
    )
    return
    try {
        if ($null -eq $script:ToastHost) { return }

        switch ($Kind) {
            'Success' { $accent = '#22C55E'; $edge = '#1F6B45' }
            'Warn'    { $accent = '#F5A524'; $edge = '#7A5A16' }
            'Error'   { $accent = '#F2565B'; $edge = '#7F244D' }
            default   { $accent = '#FF4FA3'; $edge = '#6B485B' }
        }

        while ($script:ToastHost.Children.Count -ge $script:ToastMax) {
            Remove-Toast $script:ToastHost.Children[0]
            $script:ToastHost.Children.RemoveAt(0)
        }

        $card = [System.Windows.Controls.Border]::new()
        $card.Width = 336
        $card.CornerRadius = [System.Windows.CornerRadius]::new(13)
        $card.Background = Get-Brush '#0E1C34'
        $card.BorderBrush = Get-Brush $edge
        $card.BorderThickness = [System.Windows.Thickness]::new(1)
        $card.Padding = [System.Windows.Thickness]::new(14, 12, 14, 11)
        $card.Margin = [System.Windows.Thickness]::new(0, 9, 0, 0)
        $card.Effect = New-Shadow -Blur 18 -Opacity 0.45
        $card.Opacity = 0
        $transform = [System.Windows.Media.TranslateTransform]::new(0, 16)
        $card.RenderTransform = $transform
        $card.Tag = [pscustomobject]@{ Removing = $false }

        $grid = [System.Windows.Controls.Grid]::new()
        $r1 = [System.Windows.Controls.RowDefinition]::new(); $r1.Height = [System.Windows.GridLength]::Auto
        $r2 = [System.Windows.Controls.RowDefinition]::new(); $r2.Height = [System.Windows.GridLength]::Auto
        $grid.RowDefinitions.Add($r1)
        $grid.RowDefinitions.Add($r2)

        $top = [System.Windows.Controls.Grid]::new()
        $dotCol = [System.Windows.Controls.ColumnDefinition]::new(); $dotCol.Width = [System.Windows.GridLength]::Auto
        $textCol = [System.Windows.Controls.ColumnDefinition]::new()
        $top.ColumnDefinitions.Add($dotCol)
        $top.ColumnDefinitions.Add($textCol)

        $dot = [System.Windows.Shapes.Ellipse]::new()
        $dot.Width = 9
        $dot.Height = 9
        $dot.Fill = Get-Brush $accent
        $dot.VerticalAlignment = 'Top'
        $dot.Margin = [System.Windows.Thickness]::new(0, 4, 11, 0)
        [System.Windows.Controls.Grid]::SetColumn($dot, 0)

        $text = [System.Windows.Controls.TextBlock]::new()
        $text.Text = $Message
        $text.Foreground = Get-Brush '#EEE5EA'
        $text.FontSize = 12.5
        $text.TextWrapping = 'Wrap'
        $text.Width = 286
        [System.Windows.Controls.Grid]::SetColumn($text, 1)

        $top.Children.Add($dot) | Out-Null
        $top.Children.Add($text) | Out-Null
        [System.Windows.Controls.Grid]::SetRow($top, 0)
        $grid.Children.Add($top) | Out-Null

        $track = [System.Windows.Controls.Border]::new()
        $track.Height = 3
        $track.Width = 296
        $track.CornerRadius = [System.Windows.CornerRadius]::new(1.5)
        $track.Background = Get-Brush '#3B3036'
        $track.HorizontalAlignment = 'Left'
        $track.Margin = [System.Windows.Thickness]::new(0, 11, 0, 0)
        [System.Windows.Controls.Grid]::SetRow($track, 1)

        $fill = [System.Windows.Controls.Border]::new()
        $fill.Height = 3
        $fill.Width = 296
        $fill.CornerRadius = [System.Windows.CornerRadius]::new(1.5)
        $fill.Background = Get-Brush $accent
        $fill.HorizontalAlignment = 'Left'
        $scale = [System.Windows.Media.ScaleTransform]::new(1, 1)
        $fill.RenderTransform = $scale
        $fill.RenderTransformOrigin = [System.Windows.Point]::new(0, 0.5)
        $track.Child = $fill
        $grid.Children.Add($track) | Out-Null

        $card.Child = $grid
        $script:ToastHost.Children.Add($card) | Out-Null

        # Einblenden
        $ease = [System.Windows.Media.Animation.CubicEase]::new()
        $ease.EasingMode = 'EaseOut'
        $inOpacity = [System.Windows.Media.Animation.DoubleAnimation]::new(0, 1, [System.TimeSpan]::FromMilliseconds(220))
        $inMove = [System.Windows.Media.Animation.DoubleAnimation]::new(16, 0, [System.TimeSpan]::FromMilliseconds(280))
        $inMove.EasingFunction = $ease
        $card.BeginAnimation([System.Windows.UIElement]::OpacityProperty, $inOpacity)
        $transform.BeginAnimation([System.Windows.Media.TranslateTransform]::YProperty, $inMove)

        # Balken leert sich - danach verschwindet die Mitteilung
        $bar = [System.Windows.Media.Animation.DoubleAnimation]::new(1, 0, [System.TimeSpan]::FromSeconds($Seconds))
        $scale.BeginAnimation([System.Windows.Media.ScaleTransform]::ScaleXProperty, $bar)

        $timer = [System.Windows.Threading.DispatcherTimer]::new()
        $timer.Interval = [System.TimeSpan]::FromSeconds($Seconds)
        $timer.Tag = $card
        $timer.Add_Tick({
            param($s, $e)
            $s.Stop()
            Remove-Toast $s.Tag
        })
        $timer.Start()
    } catch {}
}

# Mitteilungen, die beim Start angezeigt werden sollen (Fenster ist dann sichtbar)
$script:PendingToasts = New-Object System.Collections.Generic.List[object]

function Add-PendingToast {
    # Version 3.7: Popup-Nachrichten sind entfernt - Stummel ohne Funktion.
    param([string]$Message, [string]$Kind = 'Info', [double]$Seconds = 5)
    # (bewusst leer)
}

# ----------------------------------------------------------------------------
# AUSWAHLMENUE ("..." Button)
# ----------------------------------------------------------------------------
function Set-MenuChecked {
    param($Item, [bool]$Checked)
    if (-not $Item.Checkable) { return }
    if ($Checked) {
        $Item.Box.Background = Get-Brush '#FF4FA3'
        $Item.Box.BorderBrush = Get-Brush '#FF9DCC'
        $Item.Tick.Visibility = 'Visible'
    } else {
        $Item.Box.Background = Get-Brush '#181417'
        $Item.Box.BorderBrush = Get-Brush '#6B485B'
        $Item.Tick.Visibility = 'Collapsed'
    }
}

function New-MenuRow {
    param(
        [string]$Glyph,
        [string]$Title,
        [string]$Subtitle,
        [string]$Accent = '#FF8EC4',
        [bool]$Checkable = $false,
        [bool]$Checked = $false
    )

    $item = [pscustomobject]@{
        Checkable = $Checkable
        Box       = $null
        Tick      = $null
        Title     = $null
        Sub       = $null
    }

    $root = [System.Windows.Controls.Border]::new()
    $root.CornerRadius = [System.Windows.CornerRadius]::new(10)
    $root.Background = [System.Windows.Media.Brushes]::Transparent
    $root.Padding = [System.Windows.Thickness]::new(9, 8, 9, 8)
    $root.Cursor = [System.Windows.Input.Cursors]::Hand

    $grid = [System.Windows.Controls.Grid]::new()
    $c0 = [System.Windows.Controls.ColumnDefinition]::new(); $c0.Width = [System.Windows.GridLength]::new(32)
    $c1 = [System.Windows.Controls.ColumnDefinition]::new()
    $c2 = [System.Windows.Controls.ColumnDefinition]::new(); $c2.Width = [System.Windows.GridLength]::Auto
    $grid.ColumnDefinitions.Add($c0)
    $grid.ColumnDefinitions.Add($c1)
    $grid.ColumnDefinitions.Add($c2)

    $iconBox = [System.Windows.Controls.Border]::new()
    $iconBox.Width = 32
    $iconBox.Height = 32
    $iconBox.CornerRadius = [System.Windows.CornerRadius]::new(9)
    $iconBox.Background = Get-Brush '#2B2026'
    $iconBox.BorderBrush = Get-Brush '#4C3A45'
    $iconBox.BorderThickness = [System.Windows.Thickness]::new(1)
    $iconText = [System.Windows.Controls.TextBlock]::new()
    $iconText.Text = $Glyph
    $iconText.FontFamily = [System.Windows.Media.FontFamily]::new('Segoe MDL2 Assets')
    $iconText.FontSize = 14
    $iconText.Foreground = Get-Brush $Accent
    $iconText.HorizontalAlignment = 'Center'
    $iconText.VerticalAlignment = 'Center'
    $iconBox.Child = $iconText

    $texts = [System.Windows.Controls.StackPanel]::new()
    $texts.VerticalAlignment = 'Center'
    $texts.Margin = [System.Windows.Thickness]::new(11, 0, 8, 0)
    $titleBlock = [System.Windows.Controls.TextBlock]::new()
    $titleBlock.Text = $Title
    $titleBlock.Foreground = Get-Brush '#F7F1F5'
    $titleBlock.FontSize = 13
    $titleBlock.FontWeight = 'SemiBold'
    $subBlock = [System.Windows.Controls.TextBlock]::new()
    $subBlock.Text = $Subtitle
    $subBlock.Foreground = Get-Brush '#A99DA5'
    $subBlock.FontSize = 11
    $subBlock.Margin = [System.Windows.Thickness]::new(0, 3, 0, 0)
    $texts.Children.Add($titleBlock) | Out-Null
    $texts.Children.Add($subBlock) | Out-Null
    $item.Title = $titleBlock
    $item.Sub = $subBlock

    [System.Windows.Controls.Grid]::SetColumn($iconBox, 0)
    [System.Windows.Controls.Grid]::SetColumn($texts, 1)
    $grid.Children.Add($iconBox) | Out-Null
    $grid.Children.Add($texts) | Out-Null

    if ($Checkable) {
        $box = [System.Windows.Controls.Border]::new()
        $box.Width = 20
        $box.Height = 20
        $box.CornerRadius = [System.Windows.CornerRadius]::new(6)
        $tick = New-CheckPath
        $box.Child = $tick
        $box.VerticalAlignment = 'Center'
        $item.Box = $box
        $item.Tick = $tick
        Set-MenuChecked $item $Checked
        [System.Windows.Controls.Grid]::SetColumn($box, 2)
        $grid.Children.Add($box) | Out-Null
    }

    $root.Child = $grid
    $root.Add_MouseEnter({ param($s, $e) $s.Background = Get-Brush '#38262F' })
    $root.Add_MouseLeave({ param($s, $e) $s.Background = [System.Windows.Media.Brushes]::Transparent })

    $item | Add-Member -MemberType NoteProperty -Name 'Root' -Value $root -Force
    return $item
}

function New-Separator {
    $sep = [System.Windows.Controls.Border]::new()
    $sep.Height = 1
    $sep.Background = Get-Brush '#443740'
    $sep.Margin = [System.Windows.Thickness]::new(9, 5, 9, 5)
    return $sep
}


# ----------------------------------------------------------------------------
# NAMEN DER PLACES
# Roblox Studio meldet direkt nach dem Start häufig nur den Standardnamen
# eines leeren Place ("place4", "Baseplate"), obwohl der Fenstertitel schon
# den echten Namen zeigt. Deshalb gilt:
#   1. Ein vom Plugin gemeldeter, vollständiger Name hat immer Vorrang.
#   2. Ist der gemeldete Name nur ein Standardname, wird der Titel eines
#      Roblox-Studio-Fensters benutzt - und dieser Titel gehört danach fest
#      zu dieser Sitzung (kein Hin- und Herspringen zwischen zwei Fenstern).
#   3. Die Fenstertitel werden nur alle 4 Sekunden gelesen (weniger Last).
# ----------------------------------------------------------------------------
function Test-StandardPlaceName {
    param([string]$Name)
    if ([string]::IsNullOrWhiteSpace($Name)) { return $true }
    $value = $Name.Trim()
    if ($value -match '^place\s*\d*$') { return $true }
    if ($value -match '^(baseplate|untitled.*|unbenannt.*|new place|neues place|my place|mein place)$') { return $true }
    if ($value -match '^\d+$') { return $true }
    return $false
}

function Get-StudioWindowName {
    if (((Get-Date) - $script:WindowNameCacheAt).TotalSeconds -lt 4) {
        return , $script:WindowNameCache
    }
    $names = New-Object System.Collections.Generic.List[string]
    try {
        $studioProcesses = @()
        foreach ($processName in @('RobloxStudioBeta', 'RobloxStudio')) {
            $studioProcesses += @(Get-Process -Name $processName -ErrorAction SilentlyContinue)
        }
        foreach ($proc in $studioProcesses) {
            $title = [string]$proc.MainWindowTitle
            if ([string]::IsNullOrWhiteSpace($title)) { continue }
            $clean = ($title -replace '\s*[-–]\s*Roblox Studio\s*$', '').Trim()
            if ([string]::IsNullOrWhiteSpace($clean)) { continue }
            if ($clean -match 'Roblox\s*Studio') { continue }
            if (Test-StandardPlaceName $clean) { continue }
            $names.Add((Repair-Mojibake $clean))
        }
    } catch {}
    $script:WindowNameCache = @($names)
    $script:WindowNameCacheAt = Get-Date
    return , $script:WindowNameCache
}

function Get-PlaceName {
    param($Studio, $WindowNames)

    $sessionId = [string]$Studio.sessionId
    $reported = Repair-Mojibake ([string]$Studio.placeName)

    # 1) Vollständiger Name vom Plugin
    if (-not (Test-StandardPlaceName $reported)) {
        $script:PlaceNames[$sessionId] = $reported.Trim()
        return $script:PlaceNames[$sessionId]
    }

    # 2) Ein einmal zugeordneter Titel bleibt bei dieser Sitzung
    if ($script:PlaceNames.ContainsKey($sessionId)) {
        return $script:PlaceNames[$sessionId]
    }

    # 3) Titel eines Studio-Fensters übernehmen, der noch frei ist
    if ($WindowNames) {
        foreach ($candidate in $WindowNames) {
            if (Test-StandardPlaceName $candidate) { continue }
            $alreadyUsed = $false
            foreach ($key in @($script:PlaceNames.Keys)) {
                if ($key -ne $sessionId -and $script:PlaceNames[$key] -eq $candidate) { $alreadyUsed = $true; break }
            }
            if (-not $alreadyUsed) {
                $script:PlaceNames[$sessionId] = $candidate
                return $candidate
            }
        }
    }

    if (-not [string]::IsNullOrWhiteSpace($reported)) { return $reported }
    return 'Unbenanntes Roblox Place'
}

function Copy-Prompt {
    param([string]$SessionId)
    $token = $null
    if (-not $script:Shared.SessionTokens.TryGetValue($SessionId, [ref]$token)) {
        Show-Toast -Message 'Token konnte nicht gelesen werden.' -Kind 'Error' -Seconds 5
        return
    }
    if ([string]::IsNullOrWhiteSpace($script:TunnelUrl)) {
        Show-Toast -Message 'Der Cloudflare-Tunnel ist noch nicht bereit.' -Kind 'Warn' -Seconds 5
        return
    }
    try {
        [System.Windows.Clipboard]::SetText("URL=$script:TunnelUrl`r`nTOKEN=$token")
        Show-Toast -Message 'Prompt in die Zwischenablage kopiert.' -Kind 'Success'
    } catch {
        Show-Toast -Message "Zwischenablage blockiert: $($_.Exception.Message)" -Kind 'Error' -Seconds 6
    }
}

function Set-RowMode {
    param($Row, [string]$Mode, [switch]$Silent)

    $Row.Mode = $Mode
    $readonly = ($Mode -eq 'readonly')
    Set-MenuChecked $Row.Toggle $readonly
    $subtitle = if ($readonly) { 'Aktiv - Änderungen sind gesperrt' } else { 'Inaktiv - Änderungen sind erlaubt' }
    Set-Text $Row.Toggle.Sub $subtitle

    if (-not $Silent) {
        $message = if ($readonly) { 'Nur Lesezugriff ist aktiv.' } else { 'Lese- und Schreibzugriff ist aktiv.' }
        Show-Toast -Message $message -Kind 'Success'
    }
}

function New-Row {
    param($Studio, $WindowNames)

    $sessionId = [string]$Studio.sessionId

    $row = [pscustomobject]@{
        SessionId  = $sessionId
        Root       = $null
        Title      = $null
        Copy       = $null
        Menu       = $null
        Popup      = $null
        Toggle     = $null
        Mode       = $null
        ModeUntil  = [DateTime]::MinValue
    }

    $border = [System.Windows.Controls.Border]::new()
    $border.CornerRadius = [System.Windows.CornerRadius]::new(12)
    $border.Background = Get-Brush '#211A1E'
    $border.BorderBrush = Get-Brush '#4C3A45'
    $border.BorderThickness = [System.Windows.Thickness]::new(1)
    $border.Padding = [System.Windows.Thickness]::new(15, 0, 15, 0)
    $border.Margin = [System.Windows.Thickness]::new(0, 0, 0, 10)
    $border.MinHeight = 62
    $border.Tag = $sessionId
    $border.Add_MouseEnter({
        param($s, $e)
        $s.Background = Get-Brush '#2E2228'
        $s.BorderBrush = Get-Brush '#FF4FA3'
    })
    $border.Add_MouseLeave({
        param($s, $e)
        $s.Background = Get-Brush '#211A1E'
        $s.BorderBrush = Get-Brush '#4C3A45'
    })

    $grid = [System.Windows.Controls.Grid]::new()
    $nameCol = [System.Windows.Controls.ColumnDefinition]::new()
    $copyCol = [System.Windows.Controls.ColumnDefinition]::new(); $copyCol.Width = [System.Windows.GridLength]::Auto
    $menuCol = [System.Windows.Controls.ColumnDefinition]::new(); $menuCol.Width = [System.Windows.GridLength]::Auto
    $grid.ColumnDefinitions.Add($nameCol)
    $grid.ColumnDefinitions.Add($copyCol)
    $grid.ColumnDefinitions.Add($menuCol)

    $namePanel = [System.Windows.Controls.Grid]::new()
    $namePanel.VerticalAlignment = 'Center'
    $dotCol2 = [System.Windows.Controls.ColumnDefinition]::new(); $dotCol2.Width = [System.Windows.GridLength]::Auto
    $titleCol = [System.Windows.Controls.ColumnDefinition]::new()
    $namePanel.ColumnDefinitions.Add($dotCol2)
    $namePanel.ColumnDefinitions.Add($titleCol)
    $dot = [System.Windows.Shapes.Ellipse]::new()
    $dot.Width = 9
    $dot.Height = 9
    $dot.Fill = Get-Brush '#22C55E'
    $dot.Margin = [System.Windows.Thickness]::new(0, 0, 12, 0)
    $dot.VerticalAlignment = 'Center'
    [System.Windows.Controls.Grid]::SetColumn($dot, 0)
    $title = [System.Windows.Controls.TextBlock]::new()
    $title.Text = Get-PlaceName $Studio $WindowNames
    $title.Foreground = Get-Brush '#F7F1F5'
    $title.FontSize = 16
    $title.FontWeight = 'SemiBold'
    $title.VerticalAlignment = 'Center'
    $title.Margin = [System.Windows.Thickness]::new(0, 0, 14, 0)
    $title.TextTrimming = 'CharacterEllipsis'
    [System.Windows.Controls.Grid]::SetColumn($title, 1)
    $namePanel.Children.Add($dot) | Out-Null
    $namePanel.Children.Add($title) | Out-Null
    [System.Windows.Controls.Grid]::SetColumn($namePanel, 0)
    $grid.Children.Add($namePanel) | Out-Null
    $row.Title = $title

    $copyContent = [System.Windows.Controls.StackPanel]::new()
    $copyContent.Orientation = 'Horizontal'
    $copyGlyph = [System.Windows.Controls.TextBlock]::new()
    $copyGlyph.Text = [char]0xE8C8
    $copyGlyph.FontFamily = [System.Windows.Media.FontFamily]::new('Segoe MDL2 Assets')
    $copyGlyph.FontSize = 13
    $copyGlyph.Foreground = Get-Brush '#F1DFE8'
    $copyGlyph.VerticalAlignment = 'Center'
    $copyGlyph.Margin = [System.Windows.Thickness]::new(0, 0, 8, 0)
    $copyLabel = [System.Windows.Controls.TextBlock]::new()
    $copyLabel.Text = 'Prompt kopieren'
    $copyLabel.VerticalAlignment = 'Center'
    $copyContent.Children.Add($copyGlyph) | Out-Null
    $copyContent.Children.Add($copyLabel) | Out-Null

    $copy = [System.Windows.Controls.Button]::new()
    $copy.Content = $copyContent
    $copy.MinWidth = 150
    $copy.Height = 38
    $copy.Margin = [System.Windows.Thickness]::new(16, 0, 8, 0)
    $copy.IsEnabled = -not [string]::IsNullOrWhiteSpace($script:TunnelUrl)
    $copy.Tag = $sessionId
    $copy.Add_Click({
        param($s, $e)
        Copy-Prompt ([string]$s.Tag)
    })
    [System.Windows.Controls.Grid]::SetColumn($copy, 1)
    $grid.Children.Add($copy) | Out-Null
    $row.Copy = $copy

    $menuButton = [System.Windows.Controls.Button]::new()
    $menuGlyph = [System.Windows.Controls.TextBlock]::new()
    $menuGlyph.Text = [char]0xE712
    $menuGlyph.FontFamily = [System.Windows.Media.FontFamily]::new('Segoe MDL2 Assets')
    $menuGlyph.FontSize = 15
    $menuGlyph.HorizontalAlignment = 'Center'
    $menuGlyph.VerticalAlignment = 'Center'
    $menuButton.Content = $menuGlyph
    $menuButton.Width = 40
    $menuButton.Height = 38
    $menuButton.Padding = [System.Windows.Thickness]::new(0)
    $menuButton.ToolTip = 'Weitere Optionen'
    [System.Windows.Controls.Grid]::SetColumn($menuButton, 2)
    $grid.Children.Add($menuButton) | Out-Null
    $row.Menu = $menuButton

    # --- Auswahlmenue -------------------------------------------------------
    $popup = [System.Windows.Controls.Primitives.Popup]::new()
    $popup.PlacementTarget = $menuButton
    $popup.Placement = [System.Windows.Controls.Primitives.PlacementMode]::Bottom
    $popup.AllowsTransparency = $true
    $popup.PopupAnimation = [System.Windows.Controls.Primitives.PopupAnimation]::Fade
    # Version 3.7: StaysOpen=$true - das Menue schliesst nur noch gezielt:
    # Klick auf "..." schaltet es um, Klick ausserhalb schliesst es (siehe
    # PreviewMouseDown des Fensters). So ist ein echtes Umschalten moeglich.
    $popup.StaysOpen = $true
    $popup.HorizontalOffset = -232
    $popup.VerticalOffset = 6

    $menuShell = [System.Windows.Controls.Border]::new()
    $menuShell.Width = 272
    $menuShell.CornerRadius = [System.Windows.CornerRadius]::new(15)
    $menuShell.Background = Get-Brush '#211A1F'
    $menuShell.BorderBrush = Get-Brush '#6B485B'
    $menuShell.BorderThickness = [System.Windows.Thickness]::new(1)
    $menuShell.Padding = [System.Windows.Thickness]::new(7)
    $menuShell.Margin = [System.Windows.Thickness]::new(0, 0, 14, 14)
    $menuShell.Effect = New-Shadow -Blur 24 -Opacity 0.6

    $menuStack = [System.Windows.Controls.StackPanel]::new()
    $menuHeader = [System.Windows.Controls.TextBlock]::new()
    $menuHeader.Text = 'OPTIONEN'
    $menuHeader.Foreground = Get-Brush '#80767D'
    $menuHeader.FontSize = 10.5
    $menuHeader.FontWeight = 'Bold'
    $menuHeader.Margin = [System.Windows.Thickness]::new(9, 7, 9, 5)
    $menuStack.Children.Add($menuHeader) | Out-Null
    $menuStack.Children.Add((New-Separator)) | Out-Null

    $copyItem = New-MenuRow -Glyph ([char]0xE8C8) -Title 'Prompt kopieren' -Subtitle 'URL und Token für Arena' -Accent '#FF8EC4'
    $resetItem = New-MenuRow -Glyph ([char]0xE72C) -Title 'Token zurücksetzen' -Subtitle 'Neuen Zugang für dieses Place' -Accent '#F0A3CA'
    $toggleItem = New-MenuRow -Glyph ([char]0xE72E) -Title 'Nur Lesezugriff' -Subtitle 'Inaktiv - Änderungen sind erlaubt' -Accent '#FFB4D5' -Checkable $true -Checked $false

    # Alle Daten haengen am Element selbst (Tag). Lokale Variablen einer
    # Funktion sind in Event-Handlern nicht verfuegbar.
    $itemTag = [pscustomobject]@{
        Popup     = $popup
        SessionId = $sessionId
        Row       = $row
    }
    $copyItem.Root.Tag = $itemTag
    $resetItem.Root.Tag = $itemTag
    $toggleItem.Root.Tag = $itemTag

    $copyItem.Root.Add_MouseLeftButtonUp({
        param($s, $e)
        $info = $s.Tag
        $info.Popup.IsOpen = $false
        Copy-Prompt $info.SessionId
    })
    $resetItem.Root.Add_MouseLeftButtonUp({
        param($s, $e)
        $info = $s.Tag
        $info.Popup.IsOpen = $false
        Reset-SessionToken $info.SessionId
        Show-Toast -Message 'Token wurde zurückgesetzt.' -Kind 'Success'
    })
    $toggleItem.Root.Add_MouseLeftButtonUp({
        param($s, $e)
        $info = $s.Tag
        # Version 3.7: Das Menue bleibt bei "Nur Lesezugriff" OFFEN, damit
        # weitere Optionen direkt danach eingestellt werden koennen.
        $targetRow = $info.Row
        $newMode = if ($targetRow.Mode -eq 'readonly') { 'readwrite' } else { 'readonly' }
        Set-SessionMode $info.SessionId $newMode
        $targetRow.ModeUntil = [DateTime]::UtcNow.AddSeconds(3)
        Set-RowMode $targetRow $newMode
    })

    $menuStack.Children.Add($copyItem.Root) | Out-Null
    $menuStack.Children.Add($resetItem.Root) | Out-Null
    $menuStack.Children.Add((New-Separator)) | Out-Null
    $menuStack.Children.Add($toggleItem.Root) | Out-Null

    $menuShell.Child = $menuStack
    $popup.Child = $menuShell
    $grid.Children.Add($popup) | Out-Null

    # Version 3.7: Klick auf "..." schaltet das Menue um (offen -> zu, zu -> offen).
    $menuButton.Tag = [pscustomobject]@{ Popup = $popup }
    $menuButton.Add_Click({
        param($s, $e)
        try {
            $target = $s.Tag.Popup
            if ($null -eq $target) { return }
            $target.IsOpen = -not $target.IsOpen
        } catch {}
    })

    $row.Toggle = $toggleItem
    $row.Popup = $popup
    $row.Root = $border
    $border.Child = $grid

    $startMode = if ([string]$Studio.accessMode -eq 'readonly') { 'readonly' } else { 'readwrite' }
    Set-RowMode $row $startMode -Silent
    $row.ModeUntil = [DateTime]::MinValue

    return $row
}

function Update-Row {
    param($Row, $Studio, $WindowNames)

    Set-Text $Row.Title (Get-PlaceName $Studio $WindowNames)
    $Row.Copy.IsEnabled = -not [string]::IsNullOrWhiteSpace($script:TunnelUrl)

    $mode = if ([string]$Studio.accessMode -eq 'readonly') { 'readonly' } else { 'readwrite' }
    # Kurz nach einem Klick hat der lokale Wert Vorrang (verhindert Flackern)
    if ([DateTime]::UtcNow -lt $Row.ModeUntil) { return }
    if ($Row.Mode -ne $mode) { Set-RowMode $Row $mode -Silent }
}


# ----------------------------------------------------------------------------
# AKTUALISIERUNG DER OBERFLAECHE
# ----------------------------------------------------------------------------
function Set-LiveBadge {
    param([string]$Text, [string]$Hex, [string]$Bg, [string]$Border)
    Set-Text $LiveText $Text
    Set-Dot $LiveDot $Hex
    if ([string]$LiveBadge.Tag -ne $Bg) {
        $LiveBadge.Tag = $Bg
        $LiveBadge.Background = Get-Brush $Bg
        $LiveBadge.BorderBrush = Get-Brush $Border
    }
}

# ----------------------------------------------------------------------------
# STARTBILDSCHIRM (Version 3.4)
# Ladekreisel mit Fortschritt. Die Spieleliste erscheint erst, wenn alles
# bereit ist (oder ein Fehler/Timeout den Start beendet).
# ----------------------------------------------------------------------------
function Hide-Splash {
    if ($script:SplashDismissed) { return }
    $script:SplashDismissed = $true
    try {
        $fade = [System.Windows.Media.Animation.DoubleAnimation]::new(1, 0, [System.TimeSpan]::FromMilliseconds(420))
        $SplashScreen.BeginAnimation([System.Windows.UIElement]::OpacityProperty, $fade)
        $collapseTimer = [System.Windows.Threading.DispatcherTimer]::new()
        $collapseTimer.Interval = [System.TimeSpan]::FromMilliseconds(460)
        $collapseTimer.Tag = $SplashScreen
        $collapseTimer.Add_Tick({
            param($s, $e)
            $s.Stop()
            try { $s.Tag.Visibility = 'Collapsed' } catch {}
        })
        $collapseTimer.Start()
    } catch {
        try { $SplashScreen.Visibility = 'Collapsed' } catch {}
    }
}

function Update-SplashScreen {
    if ($script:SplashDismissed) { return }
    if ($null -eq $SplashScreen) { return }

    # 3.5: StartupBlocked = der Start wurde abgebrochen (z.B. Port belegt).
    # In dem Fall ist "Plugin nicht installiert" KEIN Fehler, sondern Folge
    # des Abbruchs - der Startbildschirm muss sichtbar bleiben und den
    # Grund zeigen (genau das machte die 3.4 kaputt: sie blendete sofort aus).
    $studioFound = [bool]$script:RobloxStudioPath
    $blocked = [bool]$script:StartupBlocked
    $pluginFailed = ($studioFound -and -not $blocked -and -not $script:PluginInstalled)
    $tunnelFailed = ((-not $blocked) -and ($script:TunnelInstallFailed -or $script:TunnelFailed -or $script:TunnelMissing))
    $tunnelActive = ($script:TunnelInstalling -or $script:TunnelProcess)

    # Zeile: Roblox Studio
    if ($studioFound) {
        Set-Dot $SplashStudioDot $script:ColorGreen
        Set-Text $SplashStudioState 'Gefunden'
    } else {
        Set-Dot $SplashStudioDot $script:ColorRed
        Set-Text $SplashStudioState 'Nicht gefunden'
    }

    # Zeile: Studio-Plugin
    if ($blocked) {
        Set-Dot $SplashPluginDot $script:ColorGray
        Set-Text $SplashPluginState 'Übersprungen'
    } elseif (-not $studioFound) {
        Set-Dot $SplashPluginDot $script:ColorGray
        Set-Text $SplashPluginState 'Wartet'
    } elseif ($script:PluginInstalled) {
        Set-Dot $SplashPluginDot $script:ColorGreen
        Set-Text $SplashPluginState 'Installiert'
    } else {
        Set-Dot $SplashPluginDot $script:ColorRed
        Set-Text $SplashPluginState 'Fehler'
    }

    # Zeile: Cloudflare-Tunnel (der aktive Punkt pulsiert)
    if ($blocked) {
        Set-Dot $SplashTunnelDot $script:ColorGray
        Set-Text $SplashTunnelState 'Nicht gestartet'
    } elseif ($script:TunnelUrl) {
        Set-Dot $SplashTunnelDot $script:ColorGreen
        Set-Text $SplashTunnelState 'Verbunden'
    } elseif ($tunnelFailed) {
        Set-Dot $SplashTunnelDot $script:ColorRed
        Set-Text $SplashTunnelState 'Fehler'
    } elseif ($script:TunnelInstalling) {
        Set-Dot $SplashTunnelDot $script:ColorAmber
        Set-Text $SplashTunnelState 'Wird installiert'
    } elseif ($script:TunnelProcess) {
        Set-Dot $SplashTunnelDot $script:ColorAmber
        Set-Text $SplashTunnelState 'Verbindet'
    } else {
        Set-Dot $SplashTunnelDot $script:ColorGray
        Set-Text $SplashTunnelState 'Wartet'
    }
    if ($tunnelActive -and -not $script:TunnelUrl) {
        if (-not $script:SplashTunnelPulse) {
            $script:SplashTunnelPulse = $true
            $pulse = [System.Windows.Media.Animation.DoubleAnimation]::new(0.3, 1, [System.TimeSpan]::FromMilliseconds(650))
            $pulse.AutoReverse = $true
            $pulse.RepeatBehavior = [System.Windows.Media.Animation.RepeatBehavior]::Forever
            $SplashTunnelDot.BeginAnimation([System.Windows.UIElement]::OpacityProperty, $pulse)
        }
    } elseif ($script:SplashTunnelPulse) {
        $script:SplashTunnelPulse = $false
        $SplashTunnelDot.BeginAnimation([System.Windows.UIElement]::OpacityProperty, $null)
        try { $SplashTunnelDot.Opacity = 1 } catch {}
    }

    # Ueberschrift + Untertext
    if ($blocked) {
        Set-Text $SplashHeadline 'Start fehlgeschlagen'
        Set-Text $SplashSub "Der lokale Port $($script:Port) konnte nicht freigegeben werden. Bitte schließe dieses Programm und starte es erneut - dabei wird die blockierende Instanz jetzt zuverlässig beendet. Hilft das nicht: PC einmal neu starten. Details: Protokoll (runtime.log) im Ordner %LOCALAPPDATA%\ArenaRobloxBridge."
    } elseif (-not $studioFound) {
        Set-Text $SplashHeadline 'Roblox Studio wurde nicht gefunden'
        Set-Text $SplashSub 'Bitte installiere Roblox Studio und starte dieses Programm danach neu.'
    } elseif ($pluginFailed) {
        Set-Text $SplashHeadline 'Studio-Plugin konnte nicht installiert werden'
        Set-Text $SplashSub 'Details stehen im Protokoll: %LOCALAPPDATA%\ArenaRobloxBridge\runtime.log'
    } elseif ($script:TunnelUrl) {
        Set-Text $SplashHeadline 'Alles bereit!'
        Set-Text $SplashSub 'Öffne ein Place in Roblox Studio - es erscheint automatisch in der Liste.'
    } elseif ($script:TunnelInstalling) {
        Set-Text $SplashHeadline 'Cloudflared wird installiert …'
        Set-Text $SplashSub 'Der Cloudflare-Tunnel wird automatisch heruntergeladen (dauert je nach Verbindung 1-3 Minuten).'
    } elseif ($tunnelFailed) {
        Set-Text $SplashHeadline 'Cloudflare-Tunnel fehlgeschlagen'
        $hint = if ($script:TunnelInstallMessage) { $script:TunnelInstallMessage } elseif ($script:LastTunnelMessage) { $script:LastTunnelMessage } else { 'Details stehen im Protokoll.' }
        if ($hint.Length -gt 220) { $hint = $hint.Substring(0, 220) + ' …' }
        Set-Text $SplashSub $hint
    } else {
        Set-Text $SplashHeadline 'Cloudflare-Tunnel wird verbunden …'
        Set-Text $SplashSub 'Das dauert normalerweise nur wenige Sekunden.'
    }

    # Ausblenden, wenn alles fertig ist (kurz "Alles bereit!" zeigen).
    # Bei einem endgueltigen Fehler bleibt der Startbildschirm ZUERST 10
    # Sekunden stehen (3.5: damit die Fehlermeldung auch gelesen werden
    # kann), danach blendet er aus und gibt die Oberflaeche frei.
    $allDone = ($studioFound -and $script:PluginInstalled -and $script:TunnelUrl)
    $terminal = ((-not $studioFound) -or $blocked -or $pluginFailed -or $tunnelFailed)
    $timedOut = (((Get-Date) - $script:StartTime).TotalSeconds -gt 150)
    if ($allDone) {
        if (-not $script:SplashReadyAt) { $script:SplashReadyAt = Get-Date }
        if (((Get-Date) - $script:SplashReadyAt).TotalMilliseconds -ge 700) { Hide-Splash }
    } elseif ($terminal -or $timedOut) {
        if (-not $script:SplashTerminalAt) { $script:SplashTerminalAt = Get-Date }
        if (((Get-Date) - $script:SplashTerminalAt).TotalMilliseconds -ge 10000) { Hide-Splash }
    }
}

function Refresh-Ui {
    $line = $null
    while ($script:TunnelLines.TryDequeue([ref]$line)) {
        $script:LastTunnelMessage = $line
        if ($line -match 'https?://[A-Za-z0-9._-]+\.trycloudflare\.com') {
            $script:TunnelUrl = $matches[0]
            Write-RuntimeLog "Tunnel URL erkannt: $script:TunnelUrl"
            if (-not $script:TunnelReadyNotified) {
                $script:TunnelReadyNotified = $true
                Show-Toast -Message 'Tunnel ist bereit. Places können sich jetzt verbinden.' -Kind 'Success'
            }
        }
    }

    # Startbildschirm aktualisieren (Ladekreisel, Fortschritt, Ausblenden)
    Update-SplashScreen

    if (-not $script:RobloxStudioPath) {
        Set-Text $SubtitleText 'Bitte installiere Roblox Studio und öffne dieses Programm danach neu.'
        Set-LiveBadge 'OFFLINE' $script:ColorRed '#2C1218' '#7F244D'
        Set-Text $EmptyTitle 'Roblox Studio wurde nicht gefunden'
        Set-Text $EmptyBody 'Installiere Roblox Studio, schließe dieses Fenster und öffne Arena Roblox Bridge danach erneut.'
        $EmptyState.Visibility = 'Visible'
        Sync-PlaceList @()
        return
    }

    if ($script:TunnelUrl) {
        Set-Text $SubtitleText 'Bereit für verbundene Places'
        Set-LiveBadge 'LIVE' $script:ColorGreen '#0E2A1C' '#1F6B45'
    } elseif ($script:TunnelInstalling) {
        # Cloudflared wird gerade automatisch heruntergeladen bzw. installiert.
        # Die Oberflaeche prueft den Fortschritt und startet den Tunnel
        # automatisch, sobald cloudflared verfuegbar ist.
        $installReady = $false
        $installError = $null
        if (Get-CloudflaredPath) {
            $installReady = $true
        } else {
            $installStatusPath = Join-Path $script:BinFolder 'install.status'
            if (Test-Path -LiteralPath $installStatusPath) {
                $installStatus = ''
                try { $installStatus = ([string](Get-Content -LiteralPath $installStatusPath -Raw)).Trim() } catch {}
                if ($installStatus -eq 'ok') {
                    # Installation fertig gemeldet, aber noch nicht gefunden:
                    # PATH neu einlesen (winget aendert den PATH eines laufenden
                    # Programms nicht von selbst) und erneut suchen.
                    Update-ProcessPath
                    if (Get-CloudflaredPath) { $installReady = $true }
                } elseif ($installStatus.StartsWith('error:')) {
                    $installError = $installStatus.Substring(6).Trim()
                }
            }
        }
        if ($installError) {
            $script:TunnelInstalling = $false
            $script:TunnelInstallFailed = $true
            $script:TunnelInstallMessage = $installError
            Write-RuntimeLog "Automatische Cloudflared-Installation fehlgeschlagen: $installError"
            Show-Toast -Message 'Cloudflared konnte nicht automatisch installiert werden. Details stehen im Protokoll.' -Kind 'Error' -Seconds 10
        } elseif ($installReady) {
            $script:TunnelInstalling = $false
            Write-RuntimeLog 'Cloudflared wurde automatisch installiert - Tunnel wird jetzt gestartet.'
            Show-Toast -Message 'Cloudflared wurde automatisch installiert. Der Tunnel wird jetzt gestartet ...' -Kind 'Success' -Seconds 6
            Start-CloudflareTunnel
        } else {
            $installSeconds = 0
            if ($script:TunnelInstallStartedAt) { $installSeconds = [int](((Get-Date) - $script:TunnelInstallStartedAt).TotalSeconds) }
            Set-Text $SubtitleText "Cloudflared wird automatisch heruntergeladen (dauert je nach Verbindung 1-3 Minuten, seit $installSeconds Sekunden)"
            Set-LiveBadge 'INSTALL' $script:ColorAmber '#2A200C' '#7A5A16'
        }
    } elseif ($script:TunnelInstallFailed) {
        Set-Text $SubtitleText 'Cloudflared konnte nicht automatisch installiert werden'
        Set-LiveBadge 'FEHLER' $script:ColorRed '#2C1218' '#7F244D'
        if (-not $script:TunnelInstallErrorNotified) {
            $script:TunnelInstallErrorNotified = $true
            $message = if ($script:TunnelInstallMessage) { $script:TunnelInstallMessage } else { 'Unbekannter Fehler.' }
            if ($message.Length -gt 300) { $message = $message.Substring(0, 300) + ' ...' }
            Write-RuntimeLog "Cloudflared-Installation endgueltig fehlgeschlagen: $($script:TunnelInstallMessage)"
            Show-Toast -Message "Cloudflared konnte nicht automatisch installiert werden: $message" -Kind 'Error' -Seconds 12
        }
    } elseif ($script:TunnelMissing) {
        Set-Text $SubtitleText 'Cloudflared fehlt: winget install --id Cloudflare.cloudflared -e'
        Set-LiveBadge 'FEHLT' $script:ColorRed '#2C1218' '#7F244D'
        if ($script:LastTunnelMessage -and -not $script:TunnelMissingNotified) {
            $script:TunnelMissingNotified = $true
            Show-Toast -Message $script:LastTunnelMessage -Kind 'Warn' -Seconds 7
        }
    } elseif ($script:TunnelFailed -or ($script:TunnelProcess -and $script:TunnelProcess.HasExited)) {
        Set-Text $SubtitleText 'Cloudflare-Tunnel konnte nicht gestartet werden'
        Set-LiveBadge 'FEHLER' $script:ColorRed '#2C1218' '#7F244D'
        if (-not $script:TunnelErrorNotified) {
            $script:TunnelErrorNotified = $true
            $message = if ($script:LastTunnelMessage) { $script:LastTunnelMessage } else { 'Cloudflared hat sich sofort wieder beendet.' }
            Write-RuntimeLog "Tunnel ohne Adresse beendet: $message"
            Show-Toast -Message $message -Kind 'Error' -Seconds 8
        }
    } else {
        $seconds = 0
        if ($script:TunnelStartedAt) { $seconds = [int](((Get-Date) - $script:TunnelStartedAt).TotalSeconds) }
        Set-Text $SubtitleText "Cloudflare-Tunnel wird aufgebaut (seit $seconds Sekunden)"
        Set-LiveBadge 'VERBINDEN' $script:ColorAmber '#2A200C' '#7A5A16'

        if ($script:TunnelProcess -and -not $script:TunnelHttp2Tried -and $seconds -gt 20) {
            $script:TunnelHttp2Tried = $true
            Write-RuntimeLog "Tunnel nach $seconds Sekunden ohne Adresse - Neustart mit HTTP/2."
            Show-Toast -Message 'Tunnel braucht ungewoehnlich lange. Cloudflared wird mit HTTP/2 neu gestartet ...' -Kind 'Warn' -Seconds 6
            Restart-CloudflareTunnel -Protocol 'http2'
        } elseif ($script:TunnelProcess -and -not $script:TunnelSlowNotified -and $seconds -gt 55) {
            $script:TunnelSlowNotified = $true
            $hint = if ($script:LastTunnelMessage) { $script:LastTunnelMessage } else { 'Cloudflared liefert keine Adresse.' }
            Write-RuntimeLog "Tunnel weiter ohne Adresse: $hint"
            Show-Toast -Message "Tunnel weiter ohne Adresse: $hint" -Kind 'Warn' -Seconds 10
        }
    }

    if (-not $script:ServerCheckDone -and ((Get-Date) - $script:StartTime).TotalMilliseconds -gt 1500) {
        $script:ServerCheckDone = $true
        if (Test-PortListening $script:Port) {
            $script:ServerStarted = $true
            Write-RuntimeLog "Server OK: Port $($script:Port) antwortet."
        } else {
            Write-RuntimeLog "ACHTUNG: Der lokale Server antwortet nicht auf Port $($script:Port)."
            Show-Toast -Message "Lokaler Server konnte nicht gestartet werden (Port $($script:Port)). Details: $script:RuntimeLog" -Kind 'Error' -Seconds 8
        }
    }

    Sync-PlaceList @(Get-ActiveStudios)
}

# Baut die Liste nur um, wenn sich etwas geaendert hat -> kein Flackern.
function Sync-PlaceList {
    param($Studios)

    $windowNames = $null
    foreach ($studio in $Studios) {
        if (Test-StandardPlaceName ([string]$studio.placeName)) {
            $windowNames = @(Get-StudioWindowName)
            break
        }
    }

    $desired = New-Object System.Collections.Generic.List[string]
    foreach ($studio in $Studios) {
        $sid = [string]$studio.sessionId
        if ([string]::IsNullOrWhiteSpace($sid)) { continue }
        $desired.Add($sid)

        if ($script:UiRows.ContainsKey($sid)) {
            try { Update-Row $script:UiRows[$sid] $studio $windowNames } catch {
                Write-RuntimeLog "Place-Zeile konnte nicht aktualisiert werden: $($_.Exception.Message)"
            }
        } else {
            try {
                $row = New-Row $studio $windowNames
                $script:UiRows[$sid] = $row
                $PlaceList.Children.Add($row.Root) | Out-Null
                $row.Root.Opacity = 0
                $fade = [System.Windows.Media.Animation.DoubleAnimation]::new(0, 1, [System.TimeSpan]::FromMilliseconds(260))
                $row.Root.BeginAnimation([System.Windows.UIElement]::OpacityProperty, $fade)
            } catch {
                Write-RuntimeLog "Place-Zeile konnte nicht erstellt werden: $($_.Exception.Message)"
            }
        }
    }

    foreach ($sid in @($script:UiRows.Keys)) {
        if (-not $desired.Contains($sid)) {
            $row = $script:UiRows[$sid]
            try { $row.Popup.IsOpen = $false } catch {}
            $PlaceList.Children.Remove($row.Root) | Out-Null
            $script:UiRows.Remove($sid)
            $script:PlaceNames.Remove($sid)
        }
    }

    $current = New-Object System.Collections.Generic.List[string]
    foreach ($child in $PlaceList.Children) { $current.Add([string]$child.Tag) }
    $reorder = $false
    if ($current.Count -ne $desired.Count) {
        $reorder = $true
    } else {
        for ($i = 0; $i -lt $desired.Count; $i++) {
            if ($desired[$i] -ne $current[$i]) { $reorder = $true; break }
        }
    }
    if ($reorder) {
        $PlaceList.Children.Clear()
        foreach ($sid in $desired) {
            if ($script:UiRows.ContainsKey($sid)) {
                $PlaceList.Children.Add($script:UiRows[$sid].Root) | Out-Null
            }
        }
    }

    $count = $desired.Count
    Set-Text $PlacesCountText ([string]$count)
    if ($count -eq 0) {
        $EmptyState.Visibility = 'Visible'
    } else {
        $EmptyState.Visibility = 'Collapsed'
    }
}

# ----------------------------------------------------------------------------
# FENSTERSTEUERUNG
# ----------------------------------------------------------------------------
$TitleBar.Add_MouseLeftButtonDown({
    if ($_.ButtonState -eq [System.Windows.Input.MouseButtonState]::Pressed) {
        $window.DragMove()
    }
})
$CloseButton.Add_Click({ $window.Close() })
$MinimizeButton.Add_Click({ $window.WindowState = 'Minimized' })
$SettingsButton.Add_Click({
    $SettingsPanel.Visibility = if ($SettingsPanel.Visibility -eq 'Visible') { 'Collapsed' } else { 'Visible' }
})

$window.Add_PreviewMouseDown({
    param($s, $e)
    try {
        # Version 3.7: Klick ausserhalb schliesst offene Auswahlmenues der
        # Places. Klicks INS Menue oder auf den "..."-Button zaehlen nicht
        # als "ausserhalb" (das Umschalten uebernimmt der Klick-Handler).
        $insideMenu = $false
        foreach ($uiRow in @($script:UiRows.Values)) {
            try {
                if ($uiRow.Popup.IsOpen -and ($uiRow.Popup.IsMouseOver -or $uiRow.Menu.IsMouseOver)) {
                    $insideMenu = $true
                    break
                }
            } catch {}
        }
        if (-not $insideMenu) {
            foreach ($uiRow in @($script:UiRows.Values)) {
                try { if ($uiRow.Popup.IsOpen) { $uiRow.Popup.IsOpen = $false } } catch {}
            }
        }
    } catch {}
    try {
        if ($SettingsPanel.Visibility -ne 'Visible') { return }
        $node = $e.OriginalSource
        while ($null -ne $node) {
            if ($node -eq $SettingsPanel -or $node -eq $SettingsButton) { return }
            if ($node -is [System.Windows.Media.Visual]) {
                $node = [System.Windows.Media.VisualTreeHelper]::GetParent($node)
            } elseif ($node -is [System.Windows.Media.Visual3D]) {
                $node = [System.Windows.Media.VisualTreeHelper]::GetParent($node)
            } else {
                break
            }
        }
        $SettingsPanel.Visibility = 'Collapsed'
    } catch {}
})

$StartupCheckBox.IsChecked = Get-StartupEnabled
$StartupCheckBox.Add_Click({
    try {
        Set-StartupEnabled ([bool]$StartupCheckBox.IsChecked)
        if ($StartupCheckBox.IsChecked) {
            Show-Toast -Message 'Autostart ist aktiviert.' -Kind 'Success'
        } else {
            Show-Toast -Message 'Autostart ist deaktiviert.' -Kind 'Info'
        }
    } catch {
        Show-Toast -Message "Der Autostart konnte nicht geändert werden: $($_.Exception.Message)" -Kind 'Error' -Seconds 6
        $StartupCheckBox.IsChecked = Get-StartupEnabled
    }
})

$window.Add_Loaded({
    $window.Opacity = 0
    $fade = [System.Windows.Media.Animation.DoubleAnimation]::new(0, 1, [System.TimeSpan]::FromMilliseconds(380))
    $window.BeginAnimation([System.Windows.Window]::OpacityProperty, $fade)

    $pulseGrow = [System.Windows.Media.Animation.DoubleAnimation]::new(0.35, 1.0, [System.TimeSpan]::FromMilliseconds(1000))
    $pulseGrow.AutoReverse = $true
    $pulseGrow.RepeatBehavior = [System.Windows.Media.Animation.RepeatBehavior]::Forever
    $PulseDot.BeginAnimation([System.Windows.UIElement]::OpacityProperty, $pulseGrow)

    foreach ($toast in $script:PendingToasts) {
        Show-Toast -Message $toast.Message -Kind $toast.Kind -Seconds $toast.Seconds
    }
    $script:PendingToasts.Clear()
})

# ----------------------------------------------------------------------------
# UPDATE-HINWEIS (Version 3.7)
# Bei 'update-erfolgreich' und 'erster-start' zeigt das Programm ZUERST
# dieses Fenster (was ist neu + OK-Button). Erst danach erscheinen das
# Hauptfenster und der Startbildschirm.
# ----------------------------------------------------------------------------
function Show-UpdateNotice {
    $isNewInstall = ($UpdateStatus -eq 'erster-start')
    $versionText = '3.7'
    $notesText = 'Keine Details verfuegbar.'
    try {
        if ($script:UpdateDetails) {
            if ($script:UpdateDetails.version) { $versionText = [string]$script:UpdateDetails.version }
            if ($script:UpdateDetails.notes) { $notesText = [string]$script:UpdateDetails.notes }
        }
    } catch {}

    if ($isNewInstall) {
        $titleText = 'Willkommen bei Arena Roblox Bridge!'
        $subText = 'Das Programm wurde zum ersten Mal geladen (Version ' + $versionText + '). Alles Weitere passiert automatisch.'
    } else {
        $titleText = 'Update installiert!'
        $subText = 'Version ' + $versionText + ' ist jetzt aktiv. Das ist neu:'
    }

    $noticeXaml = @'
<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
        Title="Arena Roblox Bridge - Update"
        Width="520" Height="440" MinWidth="520" MinHeight="440" MaxWidth="520" MaxHeight="440"
        ResizeMode="NoResize" WindowStyle="None" AllowsTransparency="True"
        Background="Transparent" WindowStartupLocation="CenterScreen" FontFamily="Segoe UI">
    <Border CornerRadius="20" Background="#171316" BorderBrush="#684154" BorderThickness="1" Padding="30,26" ClipToBounds="True">
        <Grid>
            <Grid.RowDefinitions>
                <RowDefinition Height="Auto"/>
                <RowDefinition Height="Auto"/>
                <RowDefinition Height="*"/>
                <RowDefinition Height="Auto"/>
            </Grid.RowDefinitions>
            <StackPanel Grid.Row="0" Orientation="Horizontal" Margin="0,0,0,16">
                <Grid Width="44" Height="44" Margin="0,0,14,0">
                    <Border Width="44" Height="44" CornerRadius="13">
                        <Border.Background>
                            <LinearGradientBrush StartPoint="0,0" EndPoint="1,1">
                                <GradientStop Color="#FF4FA3" Offset="0"/>
                                <GradientStop Color="#C42D79" Offset="1"/>
                            </LinearGradientBrush>
                        </Border.Background>
                    </Border>
                    <Ellipse Width="8" Height="8" Fill="#FFF7FB" HorizontalAlignment="Left" VerticalAlignment="Center" Margin="7,0,0,0"/>
                    <Ellipse Width="8" Height="8" Fill="#FFF7FB" HorizontalAlignment="Right" VerticalAlignment="Center" Margin="0,0,7,0"/>
                    <Rectangle Height="3" Fill="#F5D9E8" Margin="15,0,15,0" RadiusX="1.5" RadiusY="1.5"/>
                </Grid>
                <StackPanel VerticalAlignment="Center">
                    <TextBlock Text="ARENA ROBLOX BRIDGE" Foreground="#80767D" FontSize="10.5" FontWeight="Bold"/>
                    <TextBlock x:Name="NoticeTitle" Foreground="#F7F1F5" FontSize="19" FontWeight="Bold" Margin="0,3,0,0"/>
                </StackPanel>
            </StackPanel>
            <TextBlock Grid.Row="1" x:Name="NoticeSub" Foreground="#A99DA5" FontSize="13" TextWrapping="Wrap" Margin="0,0,0,16"/>
            <Border Grid.Row="2" CornerRadius="12" Background="#211C20" BorderBrush="#443740" BorderThickness="1" Padding="16">
                <ScrollViewer VerticalScrollBarVisibility="Auto">
                    <TextBlock x:Name="NoticeNotes" Foreground="#D8CDD4" FontSize="12.5" TextWrapping="Wrap" LineHeight="21"/>
                </ScrollViewer>
            </Border>
            <Button Grid.Row="3" x:Name="NoticeOk" Content="OK" Width="150" Height="40"
                    HorizontalAlignment="Center" Margin="0,20,0,2" Cursor="Hand">
                <Button.Template>
                    <ControlTemplate TargetType="Button">
                        <Border x:Name="bd" CornerRadius="11">
                            <Border.Background>
                                <LinearGradientBrush StartPoint="0,0" EndPoint="0,1">
                                    <GradientStop Color="#B82970" Offset="0"/>
                                    <GradientStop Color="#7D1D4D" Offset="1"/>
                                </LinearGradientBrush>
                            </Border.Background>
                            <Border.BorderBrush>#FF4FA3</Border.BorderBrush>
                            <Border.BorderThickness>1</Border.BorderThickness>
                            <ContentPresenter HorizontalAlignment="Center" VerticalAlignment="Center" Margin="14,0"/>
                        </Border>
                        <ControlTemplate.Triggers>
                            <Trigger Property="IsMouseOver" Value="True">
                                <Setter TargetName="bd" Property="Background" Value="#D93E88"/>
                            </Trigger>
                        </ControlTemplate.Triggers>
                    </ControlTemplate>
                </Button.Template>
                <Button.Foreground>#FFF7FB</Button.Foreground>
                <Button.FontWeight>SemiBold</Button.FontWeight>
                <Button.FontSize>13.5</Button.FontSize>
            </Button>
        </Grid>
    </Border>
</Window>
'@
    $noticeReader = [System.Xml.XmlNodeReader]::new([xml]$noticeXaml)
    $noticeWindow = [Windows.Markup.XamlReader]::Load($noticeReader)
    $noticeTitleEl = $noticeWindow.FindName('NoticeTitle')
    $noticeSubEl = $noticeWindow.FindName('NoticeSub')
    $noticeNotesEl = $noticeWindow.FindName('NoticeNotes')
    $noticeOkEl = $noticeWindow.FindName('NoticeOk')
    $noticeTitleEl.Text = $titleText
    $noticeSubEl.Text = $subText + ' Das Programm startet erst, wenn du OK drückst.'
    $noticeNotesEl.Text = $notesText
    $script:UpdateNoticeAccepted = $false
    $noticeWindow.Add_Closing({
        param($sender, $eventArgs)
        if (-not $script:UpdateNoticeAccepted) { $eventArgs.Cancel = $true }
    })
    $noticeOkEl.Add_Click({
        param($s, $e)
        $script:UpdateNoticeAccepted = $true
        $noticeWindow.DialogResult = $true
    })
    $noticeOkEl.Focus() | Out-Null
    [void]$noticeWindow.ShowDialog()
    $script:UpdateNoticeAccepted = $false
}

# Version 3.7: Rote "1" am Einstellungs-Button + Text in den Einstellungen
if (Test-UpdateError) {
    try { $UpdateBadge.Visibility = 'Visible' } catch {}
    try {
        $UpdateInfoTitle.Text = 'UPDATES - PROBLEM'
        $UpdateInfoTitle.Foreground = Get-Brush '#F2565B'
        $updateErrorText = Get-UpdateStatusText
        if ($script:UpdateDetails -and $script:UpdateDetails.error) {
            $updateErrorText = $updateErrorText + ': ' + [string]$script:UpdateDetails.error
        }
        $UpdateInfoText.Text = $updateErrorText
        $UpdateInfoText.Foreground = Get-Brush '#F0A7B4'
    } catch {}
} elseif ($UpdateStatus -in @('update-erfolgreich', 'erster-start', 'kein-update')) {
    try {
        $verText = '3.7'
        if ($script:UpdateDetails -and $script:UpdateDetails.version) { $verText = [string]$script:UpdateDetails.version }
        $UpdateInfoText.Text = "Version $verText - aktuell. Beim naechsten Start wird automatisch nach Updates gesucht."
    } catch {}
}

# ----------------------------------------------------------------------------
# START
# ----------------------------------------------------------------------------
if (-not $script:EncodingOk) {
    Add-PendingToast 'Achtung: Die Skriptdatei ist nicht als "UTF-8 mit BOM" gespeichert. Umlaute koennen falsch aussehen.' 'Warn' 9
    Write-RuntimeLog 'ACHTUNG: Skriptdatei ist falsch codiert - Umlaute werden ggf. falsch angezeigt.'
}

# Update/Willkommen blockiert bewusst den eigentlichen Programmstart. Es gibt
# keinen Timer: Studio-Suche, Plugin, Server und Tunnel beginnen erst nach OK.
if ($UpdateStatus -eq 'update-erfolgreich' -or $UpdateStatus -eq 'erster-start') {
    try { Show-UpdateNotice } catch { Write-RuntimeLog "Update-Hinweis konnte nicht angezeigt werden: $($_.Exception.Message)" }
}

$script:RobloxStudioPath = Find-RobloxStudio
if ($script:RobloxStudioPath) {
    Write-RuntimeLog "Roblox Studio gefunden: $($script:RobloxStudioPath.FullName)"
    $portFree = Test-PortAvailable $script:Port
    if (-not $portFree) {
        # Port ist belegt: den belegenden Prozess automatisch beenden,
        # damit diese Instanz starten kann (vorher musste der Nutzer das
        # selbst im Task-Manager tun - das war irritierend).
        Write-RuntimeLog "Port $($script:Port) ist belegt - der belegende Prozess wird gesucht und automatisch beendet."
        Add-PendingToast "Der lokale Port $($script:Port) war belegt. Das blockierende Programm wird automatisch geschlossen ..." 'Info' 6
        $portFree = Free-Port -Port $script:Port
        if ($portFree) {
            Add-PendingToast "Port $($script:Port) wurde freigegeben - die Bridge startet jetzt." 'Success' 5
            Write-RuntimeLog "Port $($script:Port) wurde automatisch freigegeben."
        }
    }
    if (-not $portFree) {
        $script:StartupBlocked = $true
        Add-PendingToast "Der lokale Port $($script:Port) konnte nicht freigegeben werden. Bitte dieses Programm schließen und erneut starten. Details: $script:RuntimeLog" 'Error' 10
        Write-RuntimeLog "Port $($script:Port) konnte nicht freigegeben werden. Es wird kein Server und kein Tunnel gestartet."
    } else {
        try {
            $pluginPath = Install-RobloxPlugin
            Write-RuntimeLog "Studio Plugin installiert: $pluginPath"
            Start-BridgeServer -Port $script:Port
            Start-CloudflareTunnel
            Add-PendingToast 'Plugin installiert. Öffne nun ein Place in Roblox Studio - es erscheint automatisch hier.' 'Info' 6
        } catch {
            Add-PendingToast "Startfehler: $($_.Exception.Message)" 'Error' 8
            Write-RuntimeLog "Startfehler: $($_.Exception.Message)"
        }
    }
} else {
    Add-PendingToast 'Roblox Studio ist nicht installiert oder wurde nicht gefunden.' 'Warn' 7
    Write-RuntimeLog 'Roblox Studio wurde nicht gefunden.'
}

$timer = [System.Windows.Threading.DispatcherTimer]::new()
$timer.Interval = [System.TimeSpan]::FromMilliseconds(900)
$timer.Add_Tick({
    try {
        Refresh-Ui
    } catch {
        Write-RuntimeLog "Refresh Fehler: $($_.Exception.Message)"
        try { Show-Toast -Message "Fehler abgefangen: $($_.Exception.Message)" -Kind 'Error' -Seconds 6 } catch {}
    }
})
$timer.Start()
Refresh-Ui

$window.Add_Closed({
    try { $timer.Stop() } catch {}
    foreach ($row in @($script:UiRows.Values)) {
        try { $row.Popup.IsOpen = $false } catch {}
    }
    try {
        if ($script:TunnelProcess -and -not $script:TunnelProcess.HasExited) {
            $script:TunnelProcess.Kill()
        }
    } catch {}
    try { Write-RuntimeLog 'Fenster geschlossen - Programm wird vollstaendig beendet.' } catch {}
    # WIRKLICH BEENDEN (Version 3.4): Der Prozess wird hart beendet. Vorher
    # konnte das Programm nach dem Schliessen im Hintergrund weiterlaufen und
    # den Port blockieren, weil blockierende Hintergrund-Runspaces (HTTP-
    # Server, Cloudflared-Ausgaben) das regulaere Ende verhindern konnten.
    # Environment.Exit schliesst den Prozess garantiert - der Port ist sofort
    # wieder frei. Offene Hintergrund-Runspaces sterben mit dem Prozess.
    [System.Environment]::Exit(0)
})

Write-RuntimeLog 'Fenster wird geöffnet.'
[void]$window.ShowDialog()
# Sicherheitsnetz (Version 3.4): Falls das Closed-Ereignis doch nicht zum
# Exit gefuehrt haben sollte, wird der Prozess hier garantiert beendet.
try { Write-RuntimeLog '=== Programmende ===' } catch {}
[System.Environment]::Exit(0)
