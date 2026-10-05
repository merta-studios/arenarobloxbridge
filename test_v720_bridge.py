#!/usr/bin/env python3
"""Offline-Abnahme fuer Arena Roblox Bridge 7.2.3.

Dieser Test braucht KEIN Windows und keinen PowerShell-Prozess. Er prueft genau
die fuenf Themen des Owners plus das Fundament:

  1. Nutzer-Kanal (Zwischennachricht) .......... _bridge.userMessages + ack/wait
  2. Fortschritt ohne erfundene Zahl (D5-D7) ... Textzeile statt 0 %, nichts verdeckt
  3. Fertig-Meldung mit Messung (D4) ........... Urteile, sweep, ehrliche Antwort ohne Test-Popup
  4. Fragen ueber die Bridge (D3) .............. ask_user-Baum + Fenster + Resume
  5. Qualitaet und GUI ......................... finishScore/grade/draft, codeLayout
  6. Fundament ................................. Stationen, Zaehler, echter PowerShell-Parser

Der Klammer-/String-Check bleibt als schneller Zusatzschutz erhalten. Das
verbindliche Parse-Gate nutzt tree_sitter + tree_sitter_powershell und laesst
nur die sieben bekannten Grammatik-Rauschstellen zu. Das ist wichtig, weil
PowerShell die ganze Datei parst, bevor irgendetwas sichtbar wird.

Aufruf:
    .venv/bin/python test_v720_bridge.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PS1 = ROOT / "ArenaBridge.ps1"
VERSION = "7.2.3"

failures: list[str] = []


def check(condition: bool, message: str) -> None:
    if condition:
        print(f"  ok   {message}")
    else:
        failures.append(message)
        print(f"  ROT  {message}")


def region(source: str, start: str, end: str) -> str:
    begin = source.index(start)
    stop = source.index(end, begin)
    return source[begin:stop]


def collection_return_problems(source: str) -> list[str]:
    """Find generic collections returned through PowerShell's unpacking pipeline.

    `return $list` maps 0/1/n elements to null/a single object/an array. The
    callers need the List instance itself, so every matching return must use
    `return ,$list` instead.
    """
    lines = source.split("\n")
    starts = [(i, m.group(1)) for i, line in enumerate(lines)
              if (m := re.match(r"\s*function\s+([A-Za-z0-9_\-]+)", line))]

    def owner_of(n: int) -> str:
        current = "?"
        for start, name in starts:
            if start <= n:
                current = name
            else:
                break
        return current

    collection = re.compile(
        r"New-Object\s+System\.Collections\.Generic\.(List|Queue|Stack|Dictionary)\[",
        re.I,
    )
    assigns: dict[tuple[str, str], list[str]] = {}
    for i, line in enumerate(lines):
        who = owner_of(i)
        for match in re.finditer(r"([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)", line):
            assigns.setdefault((who, match.group(1)), []).append(match.group(2))
    problems: list[str] = []
    for i, line in enumerate(lines):
        match = re.match(r"\s*return\s+\$([A-Za-z_][A-Za-z0-9_]*)\s*$", line.rstrip())
        if not match:
            continue
        who, var = owner_of(i), match.group(1)
        if any(collection.search(value) for value in assigns.get((who, var), [])):
            problems.append(
                f"Zeile {i + 1}: {who}() gibt ${var} entpackbar zurueck - richtig ist ,${var}"
            )
    return problems


def balanced(source: str) -> tuple[bool, str]:
    """Klammer-/String-Balance ueber die ganze Datei.

    Ueberspringt Kommentare, einfache und doppelte Strings, Here-Strings und
    $-Unterausdruecke in doppelten Strings. Danach muss die Bilanz Null sein.
    """
    n = len(source)
    stack: list[tuple[str, int]] = []
    i = 0

    def line_of(index: int) -> int:
        return source.count("\n", 0, index) + 1

    def scan_double_quoted(start: int) -> int:
        j = start + 1
        while j < n:
            ch = source[j]
            if ch == "`":
                j += 2
                continue
            if ch == "$" and j + 1 < n and source[j + 1] == "(":
                stack.append(("(", line_of(j)))
                j = scan(j + 2, stop_at_paren=True)
                continue
            if ch == '"':
                return j + 1
            j += 1
        raise ValueError(f"String ab Zeile {line_of(start)} wird nie geschlossen")

    def scan(position: int, stop_at_paren: bool = False) -> int:
        nonlocal i
        j = position
        while j < n:
            ch = source[j]
            if stop_at_paren and ch == ")":
                if stack and stack[-1][0] == "(":
                    stack.pop()
                return j + 1
            if ch == "#":
                next_line = source.find("\n", j)
                j = n if next_line == -1 else next_line
                continue
            if ch == "@" and j + 1 < n and source[j + 1] in "'\"":
                quote = source[j + 1]
                k = j + 2
                while k < n and source[k] in " \t\r":
                    k += 1
                if k < n and source[k] == "\n":
                    terminator = "\n" + quote + "@"
                    end = source.find(terminator, k)
                    if end == -1:
                        raise ValueError(f"Here-String ab Zeile {line_of(j)} bleibt offen")
                    j = end + len(terminator)
                    continue
            if ch == "'":
                k = j + 1
                while k < n:
                    if source[k] == "'":
                        if k + 1 < n and source[k + 1] == "'":
                            k += 2
                            continue
                        break
                    k += 1
                if k >= n:
                    raise ValueError(f"String ab Zeile {line_of(j)} wird nie geschlossen")
                j = k + 1
                continue
            if ch == '"':
                j = scan_double_quoted(j)
                continue
            if ch in "{([":
                stack.append((ch, line_of(j)))
            elif ch in "})]":
                pair = {"}": "{", ")": "(", "]": "["}[ch]
                if not stack:
                    raise ValueError(f"Zeile {line_of(j)}: '{ch}' ohne oeffnende Klammer")
                opener, opener_line = stack.pop()
                if opener != pair:
                    raise ValueError(
                        f"Zeile {line_of(j)}: '{ch}' schliesst '{opener}' aus Zeile {opener_line}"
                    )
            j += 1
        if stop_at_paren:
            raise ValueError("$-Unterausdruck wird nie geschlossen")
        return j

    scan(0)
    if stack:
        opener, opener_line = stack[-1]
        raise ValueError(f"{len(stack)} Klammer(n) offen, zuletzt '{opener}' aus Zeile {opener_line}")
    return True, ""


# Tree-sitter's PowerShell grammar reports seven pre-existing parser-noise
# fragments in this large, mixed PowerShell/Lua/XAML source. New ERROR nodes
# are release blockers; keep this allow-list deliberately narrow.
PARSER_NOISE_PREFIXES = (
    "MB",
    "param($Raw) if ([string]::IsNullOrWhiteSpace([string]$Raw))",
    "param($Value)",
    "$deduped | Sort-Object placeName, sessionId",
    ", ContentType",
    "[Windows.UI.Notifications",
    "[Windows.Data.Xml.Dom",
)


def new_powershell_parse_errors(raw: bytes) -> list[tuple[int, str]]:
    """Return non-baseline Tree-sitter ERROR/missing nodes with line numbers."""
    from tree_sitter import Language, Parser
    import tree_sitter_powershell as tsp

    tree = Parser(Language(tsp.language())).parse(raw)
    bad: list[tuple[int, str]] = []

    def walk(node: object) -> None:
        # The parser node API is intentionally used exactly like the standalone
        # release gate so local and CI diagnostics cannot drift apart.
        if node.type == "ERROR" or node.is_missing:
            text = raw[node.start_byte:node.end_byte].decode("utf-8", "replace")
            if not any(text.startswith(prefix) for prefix in PARSER_NOISE_PREFIXES):
                bad.append((raw.count(b"\n", 0, node.start_byte) + 1, text[:70]))
            return
        for child in node.children:
            walk(child)

    walk(tree.root_node)
    return bad


def main() -> int:
    raw = PS1.read_bytes()
    check(raw.startswith(b"\xef\xbb\xbf"), "ArenaBridge.ps1 behaelt die UTF-8-BOM")
    source = raw.decode("utf-8-sig")

    print("\n1) Nutzer-Kanal (Zwischennachricht, D8)")
    for marker in (
        "UserMessages    = [System.Collections.Concurrent.ConcurrentDictionary[string,string]]::new()",
        "UserMessageLock = [System.Object]::new()",
        "UserSignals     = [System.Collections.Concurrent.ConcurrentDictionary[string,object]]::new()",
        "function Add-UserMessage",
        "function Withdraw-UserMessage",
        "function Get-UserMessageUiViews",
        "function Get-UserMessageStateForUi",
        "function Add-UserMessage",
        "function Open-UserMessageWindow",
        "function Get-PendingUserMessageViews",
        "function Mark-UserMessagesDelivered",
        "function Invoke-AckUserMessage",
        "function Invoke-WaitForUser",
        "function Ensure-UserSignal",
    ):
        check(marker in source, f"Marker vorhanden: {marker}")

    envelope_rules = region(source, "function New-Envelope", "\n    # ------------------------------------------------------------------\n    # Werkzeuge, die das Programm selbst beantwortet")
    check("$envelope.userMessages = @($pendingUserMessages)" in envelope_rules
          and "$envelope.userMessageContract" in envelope_rules,
          "Jede Antwort normalisiert die wartenden Nutzernachrichten samt Vertrag")
    check("_bridge.userMessages" in source and "ack_user_message" in source
          and "userMessageContract" in source,
          "Die KI wird auf _bridge.userMessages und ack_user_message hingewiesen")
    check("USER CHANNEL (7.2.0)" in source, "Session-Regel USER CHANNEL ist vorhanden")

    message_ui = source[:source.index("function Get-PlaceOpenCommand")]
    for text in (
        "'wird gesendet'",
        "'angekommen",
        "'von Arena bestaetigt'",
        "ZURUECKGEZOGEN",
        "'Abbrechen'",
        "'Schliessen'",
    ):
        check(text in message_ui,
              f"Nachricht-Fenster kennt den Zustand: {text}")
    check("$withdrawn = Withdraw-UserMessage $data.SessionId $id" in source
          and "function Withdraw-UserMessage" in source,
          "Abbrechen zieht die Nachricht wirklich zurueck (kein vorgetaeuschter Widerruf)")
    check("Zu spaet zum Zurueckziehen" in source,
          "Das Fenster sagt ehrlich, wenn Zurueckziehen nicht mehr geht")
    message_window = region(source, "function Open-UserMessageWindow", "function Get-AskStateForUi")
    check('Width="460" Height="440"' in message_window,
          "Das Nachricht-Fenster startet deutlich kompakter (460 x 440)")
    check('Background="#F50B1030"' in message_window
          and 'Setter Property="Background" Value="#141B33"' in message_window
          and 'Setter Property="Background" Value="#38D16C"' in message_window,
          "Fenster, Texteingabe und Senden-Knopf verwenden die dunkle Fragenfenster-Sprache")
    check("$titleBar.Add_MouseLeftButtonDown" in message_window
          and "$s.Tag.DragMove()" in message_window
          and 'x:Name="CloseButton"' in message_window
          and '$closeButton.Add_Click' in message_window,
          "Das Fenster ist per Titelleiste verschiebbar und hat einen X-Schliesser")
    check("$win.Owner = $window" in message_window
          and "$win.ShowDialog()" in message_window
          and "$win.Show()" not in message_window,
          "Das modale ShowDialog sperrt das Hauptfenster waehrend der Eingabe")
    check("Get-UiShortErrorReason" in source
          and "Die Nachricht konnte nicht gespeichert werden: " in message_window
          and "siehe runtime.log" not in message_window,
          "Speicherfehler nennen den kurzen echten Grund direkt im Fenster")
    check("Add_PreviewKeyDown" in message_window
          and "ModifierKeys]::Control" in message_window
          and "Key]::Escape" in message_window,
          "Nachricht-Fenster unterstuetzt Strg+Enter zum Senden und Esc zum Schliessen")
    place_row_ui = region(source, "function New-Row {", "function New-MinimalPlaceRow {")
    check("-Title 'Laufenden Befehl abbrechen'" not in place_row_ui
          and "$cancelCmdItem" not in place_row_ui,
          "Das Place-Menue bietet keinen Abbruch eines laufenden Befehls mehr an")

    print("\n2) Fortschritt: nichts erfunden, nichts verdraengt (D5-D7)")
    check("function Get-ProgressPercentProvided" in source,
          "Es wird unterschieden zwischen 'keine Zahl' und 'Zahl = 0'")
    check("[System.Globalization.NumberStyles]::Float" in source
          and "[System.Globalization.CultureInfo]::InvariantCulture" in source,
          "Prozentzahlen werden invariant geparst (aus '45.5' wurde unter de-DE 455 -> 100 %)")
    state_fn = region(source, "function Update-ArenaProgressState", "\n    # ==================================================================")
    check("if ($percentProvided)" in state_fn and "percentKnown" in state_fn,
          "percent wird NUR bei einer wirklich mitgeschickten Zahl geschrieben")
    check("ProgressMissingPercent" in state_fn and "PERCENT_MISSING" in state_fn,
          "Fehlende Prozentzahl wird gezaehlt und als Station gemeldet")
    visual = region(source, "function Update-PlaceProgressVisual", "function Get-ProgressDiagnoseLines")
    check("$Row.ProgressBar.Visibility = 'Collapsed'" in visual
          and "$Row.ProgressPercent.Visibility = 'Collapsed'" in visual,
          "Ohne Zahl wird kein Balken und keine erfundene 0 % gezeichnet")
    check("$textLine = $label" in visual and "vor '" in visual,
          "Stattdessen erscheint eine Textzeile (Zustand, Werkzeug, Alter)")
    check("$label = 'Befehl: ' + [string]$openCmd.tool" not in source,
          "Ein offener Befehl verdraengt die Anzeige nicht mehr (D7)")
    check("$Row.CommandCancelButton.Visibility = 'Collapsed'" in visual,
          "Der optionale Zeilen-Knopf bleibt unsichtbar")
    check("Get-PlaceOpenCommand (Get-UiDeliverySession $sessionId)" in visual,
          "Die Zeile liest die Zustellung der richtigen (Nachfolger-)Sitzung")
    snapshot = region(source, "function Get-ProgressStateSnapshot {", "function Format-ProgressMessage")
    check("Get-ProgressStateSnapshotForId" in snapshot
          and "function Get-ProgressStateSnapshotForId" in source
          and "Get-UiDeliverySession" in snapshot,
          "Der Fortschritt wird ueber Vorgaenger/Nachfolger aufgeloest")
    check("progress-diagnose.txt" in source and "function Write-ChannelDiagnoseFile" in source,
          "progress-diagnose.txt wird als kleiner Kurzbericht geschrieben")
    check("progressWarning" in source and "'PERCENT_MISSING'" in source,
          "PERCENT_MISSING steht als Warnung in der Antwort")

    print("\n3) Fertig-Meldung: messen statt behaupten (D4)")
    platform = region(source, "function Test-NotifyPlatform", "function Get-NotifyPlatformLine")
    for verdict in (
        "SUPPRESSED_APP_DISABLED",
        "SUPPRESSED_WINDOWS_DISABLED",
        "SUPPRESSED_APP_NOTIFICATIONS_OFF",
        "SUPPRESSED_QUIET_HOURS",
        "SUPPRESSED_FULLSCREEN_RULE",
        "AUMID_UNREGISTERED",
        "READY",
    ):
        check(verdict in platform, f"Plattform-Urteil vorhanden: {verdict}")
    check("function Register-NotifyAumid" in source and "Arena.ArenaRobloxBridge" in source,
          "Die App-Id wird bei Bedarf registriert (sonst verwirft Windows den Toast still)")
    check("function Invoke-NotifySweep" in source and "'SWEEP'" in source,
          "notify.sweep misst nach dem Anzeigen erneut")
    show = region(source, "function Show-ArenaDoneNotification", "function Set-ArenaSwitchVisualState")
    check("'CALL_RETURNED'" in show and "'CALL_FAILED'" in show,
          "Der Anzeigeaufruf wird als Station verbucht (CALL/CALL_FAILED)")
    check("notify-diagnose.txt" in source and "function Get-NotifyDiagnoseLines" in source,
          "notify-diagnose.txt nennt Plattform, Zaehler und die letzten Meldungen")
    check("function Open-NotifySeenWindow" not in source
          and "function Send-NotifyTestMessage" not in source,
          "Die kuenstliche Test-Benachrichtigung und ihre Rueckfrage sind entfernt")
    settings_ui = region(source, "function Open-SettingsWindow", "# Version 3.8: Die Update-Infos")
    settings_xaml = region(settings_ui, "$settingsXaml = @'", "'@")
    check('Text="DIAGNOSE"' not in settings_xaml
          and 'x:Name="PerfSwitch"' not in settings_xaml
          and "NotifyTestStatus" not in settings_ui,
          "Der Diagnosebereich und die Leistungsdiagnose-Steuerung sind aus den Einstellungen entfernt")
    place_card_start = settings_xaml.index('x:Name="ProgressSwitch"')
    place_card_end = settings_xaml.index("</Border>", place_card_start)
    place_card = settings_xaml[place_card_start:place_card_end]
    check('x:Name="DoneNotifySwitch"' in place_card
          and 'NotifyTestButton' not in settings_ui
          and 'Test-Meldung anzeigen' not in settings_xaml,
          "Der echte Fertig-Meldungs-Schalter bleibt, die Test-Benachrichtigung ist aus Einstellungen entfernt")
    settings_loader = region(source, "function Get-BridgeSettingsFile", "function Save-BridgeSettingsFile")
    check("perfDiagnostics = $false" in settings_loader
          and "$loaded.perfDiagnostics" not in settings_loader
          and "alte opt-ins werden ignoriert" in settings_loader,
          "Ein alter Performance-Diagnose-Opt-in wird nicht still wieder aktiviert")
    check("NotifySeenYes" not in source and "NotifySeenNo" not in source,
          "Die entfernte Test-Rueckfrage hinterlaesst keine toten Diagnose-Zaehler")
    done_start = source.index("                $notifyFlowId = 'n-' + [string]$notifyFlowSeq")
    done = source[done_start:done_start + 9000]
    check("delivered = $true" not in done,
          "report_done behauptet nicht mehr blind 'delivered = true'")
    check("NOTIFICATION_UNVERIFIED" in done and "notification = @{" in done,
          "report_done antwortet ehrlich mit Urteil und NOTIFICATION_UNVERIFIED")
    check("platformVerdict" in done and "notify.sweep" in done,
          "Die Antwort nennt Urteil, Grund und die Nachmessung")

    print("\n4) Fragen ueber die Bridge (D3 / 7.2.3)")
    for marker in (
        "function Test-AskTree",
        "function Invoke-AskUser",
        "function Invoke-ConfirmAction",
        "function Get-LateAskAnswers",
        "function Get-PendingAskViews",
        "function Wait-AskAnswer",
        "function Cancel-AskForUi",
        "function Start-AskModal",
        "function Stop-AskModal",
        "'ask_user'",
        "'confirm_action'",
    ):
        check(marker in source, f"Marker vorhanden: {marker}")
    for code in ("ASK_TOO_MANY_QUESTIONS", "ASK_GRAPH_INVALID", "ASK_CYCLE", "ASK_EXPIRED", "ASK_UNKNOWN", "ASK_CANCELLED"):
        check(code in source, f"Typisierter Fehler vorhanden: {code}")
    check("ASK_UNREACHABLE" in source, "Unbrauchbare Bedingungen werden gemeldet (ASK_UNREACHABLE)")
    tree = region(source, "function Test-AskTree", "function Read-AskState")
    check("if ($options.Count -lt 2)" in tree and "code = 'ASK_GRAPH_INVALID'" in tree,
          "Test-AskTree weist Baeume mit weniger als zwei Optionen vor dem Fenster ab")
    check("$maxQuestions = 12" in source and "$maxOptions = 6" in source and "$maxChars = 400" in source,
          "Die Grenzen des Plans sind umgesetzt (12 Fragen, 6 Optionen, 400 Zeichen)")
    ask = region(source, "function Invoke-AskUser", "function Get-LateAskAnswers")
    check("resume" in ask and "nextCall" in ask and "Get-AskCancelledResponse" in ask,
          "Das Warten ist wiederaufnehmbar und beantwortet Abbruch als ASK_CANCELLED")
    check("if ($seconds -gt 50) { $seconds = 50 }" in source,
          "waitSeconds bleibt unter dem harten HTTP-Deckel")
    check("path = @($State.path)" in source and "notShown = @($State.notShown)" in source,
          "Die Antwort nennt gestellte und uebersprungene Fragen")
    check("cancelled = $wasCancelled" in source
          and "summary = $(if ($wasCancelled) { 'Der Nutzer hat abgebrochen.' }" in source,
          "Spaete Nutzerantworten liefern cancelled:true samt ehrlicher Zusammenfassung")
    check("$answer.confirmed = $false" in source and "ASK_CANCELLED" in region(source, "function Invoke-ConfirmAction", "function Get-LateAskAnswers"),
          "confirm_action behandelt ASK_CANCELLED eindeutig als Nein")
    check("$envelope.userAnswers = @($lateAnswers)" in envelope_rules
          and "$envelope.openQuestions = @($openAsks)" in envelope_rules,
          "Antworten und offene Fragen werden am Umschlag als echte Arrays normalisiert")

    ui = region(source, "function Update-AskWindow", "function Get-PlaceOpenCommand")
    open_ask = region(source, "function Open-AskWindow", "function Sync-AskWindows")
    check("function Open-AskWindow" in source and "function Sync-AskWindows" in source,
          "Das Fragenfenster oeffnet sich aus dem Anzeige-Takt")
    check("[System.Windows.Forms.Cursor]::Position" in open_ask
          and "[System.Windows.Forms.Screen]::FromPoint" in open_ask
          and "$win.SizeToContent = [System.Windows.SizeToContent]::Height" in open_ask
          and "$windowMaxHeight = [Math]::Min(340, [Math]::Floor($area.Height * 0.70))" in open_ask,
          "Fenster startet kompakt am Mauszeiger, hoehenbasiert, maximal 460 x 340 und innerhalb von 70 % des Bildschirms")
    check("$scroll, 2" in open_ask and "GridUnitType]::Star" in open_ask,
          "Der ScrollViewer liegt in der eigenen *-Zeile")
    check("SetRow($copyPanel, 4)" in open_ask and "SetRow($buttonRow, 5)" in open_ask,
          "CopyPanel und ButtonRow haben getrennte Grid-Zeilen und ueberlappen nicht")
    check("$backButton.Content = 'Zurück'" in open_ask
          and "$cancelButton.Content = 'Abbrechen'" in open_ask
          and "$nextButton.Content = 'Weiter'" in open_ask
          and "$nextButton.Background = Get-Brush '#38D16C'" in open_ask
          and "$cancelButton.Background = Get-Brush '#FF5C77'" in open_ask
          and "$backButton.Background = Get-Brush '#0E1428'" in open_ask,
          "Unten stehen genau die drei farblich eindeutigen Aktionen Zurueck/Abbrechen/Weiter")
    check("Antwort als Text kopieren" in open_ask
          and "$copyPanel.Visibility = 'Collapsed'" in ui
          and "Agent arbeitet weiter …" in ui
          and "Agent ist offline …" in ui,
          "Der Kopierknopf erscheint nur als Ausnahme bei Offline oder Ablauf")
    check("Diese Frage kam ohne Optionen an" in ui
          and "EMPTY_QUESTION" in ui
          and "Write-UiErrorLog ('ASK EMPTY_QUESTION" in ui,
          "Fehlgeformte Altfragen zeigen sichtbar einen Fehler und werden protokolliert")
    check("#5CFFEF" not in open_ask
          and "#F50B1030" in open_ask
          and "#141B33" in open_ask
          and "#F4F8FF" in open_ask,
          "Fragenfenster nutzt die dunkle Shell-/Panel-/Text-Palette ohne Mint")
    check("$titleBar.Add_MouseLeftButtonDown" in open_ask
          and "DragMove()" in open_ask
          and "$closeButton.Width = 30" in open_ask
          and "$closeButton.Add_MouseEnter" in open_ask,
          "Titelzeile ist ziehbar und das X ist ein eigener Hover-Schliesser")
    check("$window.IsEnabled = $false" in source
          and "Stop-AskModal $Info" in ui
          and "state.state -ne 'waiting'" in open_ask,
          "Fragen sperren die Hauptoberflaeche nur waehrend waiting und geben im Timer sicher frei")
    check("$win.Add_PreviewKeyDown" in open_ask
          and "Key]::Escape" in open_ask
          and "Cancel-AskForUi $data 'escape'" in open_ask,
          "Esc und X folgen derselben Abbruchsemantik")
    pending = region(source, "function Get-AskPendingForUi", "function Test-AskCondition")
    sync = region(source, "function Sync-AskWindows", "function Get-PlaceOpenCommand")
    check("$askState -eq 'cancelled'" in pending and "pending.state -eq 'cancelled'" in sync,
          "Get-AskPendingForUi und Sync-AskWindows ignorieren cancelled dauerhaft")
    check("cancelledAt" in source and "Set-UiMessageField $state 'state' 'cancelled'" in source,
          "Abbrechen schreibt cancelled und cancelledAt in den gemeinsamen Zustand")
    check("function Test-AskCondition" in source and "anyOf" in source and "allOf" in source,
          "Bedingungen (when/anyOf/allOf/custom) werden ausgewertet")
    check("ANSWER_DISCARDED" in source and "reason = 'back'" in open_ask,
          "Zurueck verwirft Folgeantworten nachvollziehbar")

    print("\n4b) Quick-Tunnel: tote URL niemals als LIVE weitergeben")
    tunnel_start = region(source, "function Start-CloudflareTunnel", "function Restart-CloudflareTunnel")
    tunnel_refresh = region(source, "function Refresh-Ui", "function Add-PlaceRowToPlaceList")
    check("$script:TunnelUrl = $null" in tunnel_start
          and "$script:TunnelProtocol = $effectiveProtocol" in tunnel_start,
          "Jeder neue cloudflared-Prozess verwirft die alte URL und merkt sein Protokoll")
    check("$tunnelEnded" in tunnel_refresh
          and "$script:TunnelUrl = $null" in tunnel_refresh
          and "tote TLS-Adresse" in tunnel_refresh,
          "Ein beendeter cloudflared-Prozess kann keine stale trycloudflare-URL als LIVE hinterlassen")
    check("$recoveryProtocol = if ([string]$script:TunnelProtocol -eq 'auto') { 'http2' }" in tunnel_refresh
          and "Restart-CloudflareTunnel -Protocol $recoveryProtocol" in tunnel_refresh
          and "TunnelNextRestartAt" in tunnel_refresh,
          "Tunnel-Wiederherstellung ist gedrosselt und wechselt nach Auto/QUIC auf HTTP/2")
    check("lineProcessId" in tunnel_refresh and "lineProcessId -ne $activeProcessId" in tunnel_refresh
          and "TunnelLiveSince" in tunnel_refresh,
          "Gepufferte Ausgabe alter Prozesse kann keine neue URL ueberschreiben und ein Kurzstart umgeht den Backoff nicht")

    print("\n5) Qualitaet und GUI")
    check("finishScore = finishScore" in source and "grade = grade" in source,
          "auditBuildQuality liefert finishScore und grade")
    check("draftRisk = draftRisk" in source and "primitiveShare = primitiveShare" in source,
          "Der Entwurfs-Verdacht ist Teil der Messung")
    check('if #parts >= 4 and intentional == 0 and primitiveShare > 0.6 then' in source,
          "Die Entwurfs-Schwelle faengt genau den Fall des Owners ab (5 Teile, keine Gestaltung)")
    check('part:GetAttribute("ArenaDeclaredGrade")' in source
          and 'model:SetAttribute("ArenaDeclaredGrade", tostring(args.grade))' in source,
          "Erklaerte Einfachheit (grade) wird gespeichert und im Audit beruecksichtigt")
    check("DRAFT_GRADE_RISK" in source, "Der Entwurfs-Verdacht wird benannt")
    check("code = 'DRAFT_GRADE_RISK'" in source,
          "report_done sperrt eine Arbeit, die der Audit als Entwurf benotet hat")
    check("function Get-SessionBuildSummary" in source and "buildRegister" in source,
          "Das Bau-Register sagt, was gebaut und was gemessen wurde")
    check("function Register-SessionBuild" in source and "function Update-SessionBuildAudit" in source,
          "Jeder Modell-Bau wird registriert und ein Audit nachgetragen")
    check("UI_ENGINE.codeLayoutReport" in source, "Die Code-Struktur wird gemessen")
    check("MONOLITH_SCRIPT" in source and "RUNTIME_BUILT_UI" in source,
          "Beide Fehlbilder der Oberflaeche werden benannt")
    check("uiStructureRules" in source and "UI STRUCTURE CONTRACT" in source,
          "Der GUI-Vertrag steht im Sessionstart")
    check("scaffold_ui_scripts" in source and "Config" in source and "Input" in source and "Effects" in source,
          "scaffold_ui_scripts liefert die Aufteilung in kleine Skripte")
    check("monolithRisk" in source and "uiStructureWarning" in source,
          "MONOLITH_RISK wiederholt sich in jeder Antwort")

    print("\n6) Fundament, Version und Parse-Sicherheit")
    for marker in (
        "FlowTrace       = [System.Collections.Concurrent.ConcurrentQueue[string]]::new()",
        "Add-ChannelCount",
        "Write-FlowStation",
        "function Write-FlowTrace",
        "function Write-ChannelDiagnoseFile",
        "AskRequests     = [System.Collections.Concurrent.ConcurrentDictionary[string,string]]::new()",
        "SessionBuilds    = [System.Collections.Concurrent.ConcurrentDictionary[string,string]]::new()",
    ):
        check(marker in source, f"Fundament-Marker vorhanden: {marker}")
    version = json.loads((ROOT / "version.json").read_text(encoding="utf-8"))
    check(version["version"] == VERSION, "version.json identifiziert 7.2.3")
    notes = "\n".join(str(note) for note in version.get("notes", []))
    for word in ("7.2.3", "LIVE-SAMMLUNGEN", "ASK_CANCELLED", "Strg+Enter",
                 "Test-Benachrichtigung", "NOTIFICATION_UNVERIFIED", "notify-diagnose.txt"):
        check(word in notes, f"version.json beschreibt: {word}")
    check("DocsVersion     = '7.2.3'" in source and 'local ARENA_VERSION  = "7.2.3"' in source,
          "Alle funktionalen Versionsstellen stehen auf 7.2.3")
    problems = collection_return_problems(source)
    for problem in problems:
        print(f"    {problem}")
    check(not problems,
          "Keine Generic List/Queue/Stack/Dictionary wird entpackbar zurueckgegeben (return ,$liste)")
    final_lines = source.rstrip().splitlines()[-4:]
    check(final_lines[0].startswith("# Sicherheitsnetz") and final_lines[-1] == "[System.Environment]::Exit(0)",
          "Der absichtliche Not-Aus am Dateiende ist unveraendert")

    try:
        balanced(source)
        check(True, "Klammer-/String-Balance der ganzen Datei ist sauber")
    except ValueError as exc:
        check(False, f"Klammer-/String-Balance: {exc}")

    try:
        parse_errors = new_powershell_parse_errors(raw)
    except ImportError as exc:
        check(False, f"Tree-sitter-Parse-Gate fehlt ({exc}); requirements-test.txt installieren")
    else:
        print(f"  Tree-sitter: Neue ERROR-Stellen: {len(parse_errors)}")
        for line, text in parse_errors:
            print(f"    Zeile {line}: {text!r}")
        check(not parse_errors,
              "Tree-sitter-PowerShell-Parse-Gate meldet keine neuen ERROR-Stellen")

    print()
    if failures:
        print(f"ROT: {len(failures)} Pruefung(en) fehlgeschlagen:")
        for entry in failures:
            print(f"  - {entry}")
        return 1
    print("OK: 7.2.3 - Nutzer-Kanal, Fortschritt ohne erfundene Zahl, gemessene "
          "Fertig-Meldung, Fragen-Baum, Qualitaets- und GUI-Vertrag sind vollstaendig; "
          "die Datei ist ausbalanciert und der echte PowerShell-Parser ist gruen.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
