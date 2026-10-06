#!/usr/bin/env python3
"""Offline-Abnahme fuer Arena Roblox Bridge 7.3.1.

Dieser Test braucht KEIN Windows und keinen PowerShell-Prozess. Er prueft genau
die fuenf Themen des Owners plus das Fundament:

  1. Nutzer-Kanal (Zwischennachricht) .......... _bridge.userMessages + ack/wait
  2. Fortschritt ohne erfundene Zahl (D5-D7) ... Textzeile statt 0 %, nichts verdeckt
  3. Fertig-Meldung mit Messung (D4) ........... Urteile, sweep, ehrliche Antwort ohne Test-Popup
  4. Fragen ueber die Bridge (D3) .............. ask_user-Baum + Fenster + Resume
  5. Qualitaet und GUI ......................... finishScore/grade/draft, codeLayout
  6. Fundament ................................. Stationen, Zaehler, echter PowerShell-Parser

Tree-sitter ist nur ein Struktur-Zusatzcheck, kein Windows-PowerShell-Parser.
parse-gate.ps1 nutzt den echten Parser, wenn PowerShell installiert ist.
Ohne PowerShell wird dieser Check explizit uebersprungen.

Aufruf:
    .venv/bin/python test_v720_bridge.py
"""
from __future__ import annotations

import json
import re
import sys
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PS1 = ROOT / "ArenaBridge.ps1"
VERSION = "7.3.1"

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
    """Zwei PowerShell-5.1-Sammlungsfallen auf einmal finden.

    Falle 1 (seit 7.2.3): `return $list` entpackt 0/1/n Elemente in die
    Pipeline (null / ein Objekt / ein Array). Der Aufrufer braucht aber die
    Liste selbst, also muss dort `return ,$list` stehen.

    Falle 2 (P0-Blocker 7.2.4, live belegt): `@($list)` um eine
    System.Collections.Generic.List wirft in Windows PowerShell 5.1 den
    Binderfehler "Die Argumenttypen stimmen nicht ueberein." - egal ob die
    Liste leer oder gefuellt ist. In 7.2.3 stand hinter einem korrekten
    `return ,$items` trotzdem `@($items)` am Umschlag; dadurch scheiterte
    JEDER Werkzeugaufruf, solange eine Frage offen war. Richtig ist
    `$list.ToArray()` (ergibt auch leer ein Array, nie $null).

    Beide Regeln werden ueber dieselbe Zuordnungstabelle geprueft: eine
    Variable gilt als Sammlung, wenn sie direkt aus `New-Object
    ...Generic.List/Queue/Stack/Dictionary[...]` stammt ODER aus dem Aufruf
    einer Funktion, die ihrerseits `return ,$...` auf so eine Sammlung macht.
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
    assigns: dict[tuple[str, str], list[tuple[int, str]]] = {}
    for i, line in enumerate(lines):
        who = owner_of(i)
        for match in re.finditer(r"([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)", line):
            assigns.setdefault((who, match.group(1)), []).append((i, match.group(2)))

    # Funktionen, die eine Generic-Sammlung per Komma-Operator zurueckgeben.
    collection_funcs: set[str] = set()
    for i, line in enumerate(lines):
        match = re.match(r"\s*return\s+,?\s*\$([A-Za-z_][A-Za-z0-9_]*)\s*(\}.*)?$", line.rstrip())
        if not match:
            continue
        who, var = owner_of(i), match.group(1)
        if any(collection.search(value) for _, value in assigns.get((who, var), [])):
            collection_funcs.add(who)

    def origins(who: str, var: str) -> list[str]:
        found: list[str] = []
        for line_no, value in assigns.get((who, var), []):
            if collection.search(value):
                found.append(f"Zeile {line_no + 1} (New-Object Generic-Sammlung)")
                continue
            call = re.match(r"\s*([A-Za-z_][A-Za-z0-9_\-]+)\b", value)
            if call and call.group(1) in collection_funcs:
                found.append(f"Zeile {line_no + 1} ({call.group(1)}() liefert ,${var})")
        return found

    problems: list[str] = []
    for i, line in enumerate(lines):
        who = owner_of(i)
        bare = re.match(r"\s*return\s+\$([A-Za-z_][A-Za-z0-9_]*)\s*$", line.rstrip())
        if bare:
            var = bare.group(1)
            if any(collection.search(value) for _, value in assigns.get((who, var), [])):
                problems.append(
                    f"Zeile {i + 1}: {who}() gibt ${var} entpackbar zurueck - richtig ist ,${var}"
                )
        # Falle 2: @($var) um eine Sammlung.
        for wrapped in re.finditer(r"@\(\s*\$([A-Za-z_][A-Za-z0-9_]*)\s*\)", line):
            var = wrapped.group(1)
            why = origins(who, var)
            if why:
                problems.append(
                    f"Zeile {i + 1}: {who}() legt @() um ${var} "
                    f"({'; '.join(why)}) - PowerShell-5.1-Binderfehler; "
                    f"richtig ist ${var}.ToArray()"
                )
    return problems



def without_comments(text: str) -> str:
    """PowerShell-Kommentarzeilen entfernen.

    Erklaerende Kommentare duerfen die verbotenen Altfarben beim Namen nennen
    ("kein #F50B1030 mehr"); geprueft werden muss der echte XAML-/Code-Anteil.
    """
    return "\n".join(line for line in text.split("\n")
                      if not line.lstrip().startswith("#"))


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
    # 7.2.4 (P0): .ToArray() statt @() - @( List[object] ) ist der
    # PowerShell-5.1-Binderfehler, der in 7.2.3 jeden Werkzeugaufruf toetete.
    check("$envelope.userMessages = $pendingUserMessages.ToArray()" in envelope_rules
          and "$envelope.userMessageContract" in envelope_rules
          and "@($pendingUserMessages)" not in envelope_rules,
          "Jede Antwort normalisiert die wartenden Nutzernachrichten samt Vertrag (ohne @())")
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
    # 7.2.4 (3a): Das Nachrichten-Fenster ist aus dem gemeinsamen XAML-
    # Ressourcenblock gebaut - dasselbe Design wie Haupt-/Einstellungsfenster.
    message_window = region(source, "function Get-UserMessageWindowXaml", "function Get-AskStateForUi")
    check('Width="480" Height="470"' in message_window,
          "Das Nachricht-Fenster startet kompakt (480 x 470)")
    message_markup = without_comments(message_window)
    check('Background="{StaticResource SwAppBg}"' in message_markup
          and '#F50B1030' not in message_markup
          and '#5CFFEF' not in message_markup,
          "Das Fenster sitzt auf dem SwAppBg-Verlauf des Programms (kein #F50B1030, kein Mint)")
    check('Style="{StaticResource ArenaTextField}"' in message_window
          and 'Style="{StaticResource ArenaPrimaryButton}"' in message_window
          and 'Style="{StaticResource ArenaCloseButton}"' in message_window,
          "Textfeld, Senden-Knopf und Kreuz kommen aus dem gemeinsamen Ressourcenblock")
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
    # 3c: kurzer echter Grund im Fenster, VOLLER Grund im runtime.log.
    check("Write-RuntimeLog ('Nachricht-Fenster: Speichern abgelehnt - ' + $reason)" in message_window
          and "Write-UiErrorLog 'Nachricht konnte nicht gesendet werden' $_" in message_window,
          "Der volle Fehlergrund wird zusaetzlich ins runtime.log geschrieben")
    # 3d: Add-UserMessage darf nie $list.Add() auf $null ausfuehren.
    add_msg = region(source, "function Add-UserMessage", "function Withdraw-UserMessage")
    check("if ($null -eq $list) { $list = New-Object System.Collections.Generic.List[object] }" in add_msg,
          "Add-UserMessage legt eine fehlende Nachrichtenliste an, statt auf $null zu schreiben")
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
    check("$envelope.userAnswers = $lateAnswers.ToArray()" in envelope_rules
          and "$envelope.openQuestions = $openAsks.ToArray()" in envelope_rules
          and "@($lateAnswers)" not in envelope_rules
          and "@($openAsks)" not in envelope_rules,
          "Antworten und offene Fragen werden am Umschlag per .ToArray() normalisiert (nie @())")

    ui = region(source, "function Update-AskWindow", "function Retarget-AskWindow")
    ask_xaml = region(source, "function Get-AskWindowXaml", "function New-AskWindowInfo")
    open_ask = region(source, "function Open-AskWindow", "function Sync-AskWindows")
    check("function Open-AskWindow" in source and "function Sync-AskWindows" in source,
          "Das Fragenfenster oeffnet sich aus dem Anzeige-Takt")
    # 2a: Design = Programm-Design (XAML + gemeinsamer Ressourcenblock).
    check('Width="480" Height="420"' in ask_xaml
          and 'SizeToContent="Height"' in ask_xaml
          and 'WindowStyle="None"' in ask_xaml
          and 'AllowsTransparency="True"' in ask_xaml
          and 'Background="Transparent"' in ask_xaml,
          "Fragen-Fenster ist XAML-basiert, rahmenlos, transparent und hoehenbasiert (480 x 420)")
    ask_markup = without_comments(ask_xaml)
    check('Background="{StaticResource SwAppBg}"' in ask_markup
          and '{StaticResource SwCardBg}' in ask_markup
          and '{StaticResource SwTextMain}' in ask_markup
          and '#F50B1030' not in ask_markup
          and '#5CFFEF' not in ask_markup,
          "Fragen-Fenster nutzt SwAppBg/SwCardBg/SwTextMain - kein #F50B1030-Shell, kein Mint")
    # Der Platzhalter steht einmal in der Vorlage und einmal im Replace-Aufruf.
    # Der Platzhalter steht zweimal: einmal als Luecke in der Vorlage, einmal
    # als Suchbegriff im Replace-Aufruf. Beides muss da sein - und der
    # Ressourcenblock selbst genau einmal definiert.
    check("$script:ArenaDialogStyles" in source
          and ask_markup.count('<!--ARENA_DIALOG_STYLES-->') == 2
          and "Replace('<!--ARENA_DIALOG_STYLES-->', [string]$script:ArenaDialogStyles)" in ask_xaml
          and source.count("$script:ArenaDialogStyles = @'") == 1
          and message_window.count("Replace('<!--ARENA_DIALOG_STYLES-->', [string]$script:ArenaDialogStyles)") == 1,
          "EIN gemeinsamer XAML-Ressourcenblock versorgt Fragen- UND Nachrichten-Fenster")
    check("[System.Windows.Forms.Cursor]::Position" in open_ask
          and "[System.Windows.Forms.Screen]::FromPoint" in open_ask
          and "$windowMaxHeight = [Math]::Min(560, [Math]::Floor($area.Height * 0.70))" in open_ask,
          "Fenster startet am Mauszeiger und bleibt innerhalb von 70 % der Bildschirmhoehe")
    check('x:Name="QuestionScroll"' in ask_xaml and '<RowDefinition Height="*"/>' in ask_xaml,
          "Der ScrollViewer liegt in der eigenen *-Zeile")
    check('x:Name="CopyPanel"' in ask_xaml and 'x:Name="DonePanel"' in ask_xaml
          and 'x:Name="ButtonRow"' in ask_xaml,
          "Kopier-, Endzustand- und Knopfzeile sind getrennte Bereiche und ueberlappen nicht")
    # 2e: genau drei Aktionen, farblich eindeutig.
    check('x:Name="BackButton" Content="Zurück"' in ask_xaml
          and 'x:Name="CancelButton" Content="Abbrechen"' in ask_xaml
          and 'x:Name="NextButton" Content="Weiter"' in ask_xaml
          and 'Style="{StaticResource ArenaQuietButton}"' in ask_xaml
          and 'Style="{StaticResource ArenaDangerButton}"' in ask_xaml
          and 'Style="{StaticResource ArenaPrimaryButton}"' in ask_xaml,
          "Unten stehen genau Zurueck (grau), Abbrechen (rot) und Weiter/Fertig (gruen)")
    check('Color="#F238D16C"' in source and 'Color="#F2FF5C77"' in source
          and 'Color="#0E1428"' in source,
          "Gruen #38D16C, Crimson #FF5C77 und Grau #0E1428 sind die einzigen Aktionsfarben")
    check("$nextButton.Content" not in open_ask and "$cancelButton.Background" not in open_ask,
          "Die Knopffarben stehen nicht mehr als Code, sondern im gemeinsamen XAML")
    check('Visibility="Collapsed"' in ask_xaml
          and 'Content="Antwort als Text kopieren"' in ask_xaml
          and "$Info.CopyPanel.Visibility = 'Visible'" in ui
          and "Agent arbeitet weiter …" in ui
          and "Agent ist offline …" in ui,
          "Der Kopierknopf ist standardmaessig unsichtbar und erscheint nur bei Offline oder Ablauf")
    check("Diese Frage kam ohne Optionen an" in ui
          and "EMPTY_QUESTION" in ui
          and "Write-UiErrorLog ('ASK EMPTY_QUESTION" in ui,
          "Fehlgeformte Altfragen zeigen sichtbar einen Fehler und werden protokolliert")
    # 2h: ziehbar, Kreuz oben rechts als eigener Hover-Knopf.
    check("$titleBar.Add_MouseLeftButtonDown" in open_ask
          and "DragMove()" in open_ask
          and 'x:Name="CloseButton"' in ask_xaml
          and 'x:Key="ArenaCloseButton"' in source
          and '<Setter Property="Width" Value="32"/>' in source
          and '<Setter Property="Height" Value="32"/>' in source
          and 'Trigger Property="IsMouseOver"' in source,
          "Titelzeile ist ziehbar und das Kreuz ist ein 32x32-Knopf mit Hover (>= 28x28)")
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


    print("\n5b) P0-Blocker 7.2.4: Sammlungen toeten keinen Werkzeugaufruf mehr")
    # Live belegt mit 7.2.3: ask_user legte die Frage an, antwortete aber mit
    # {"error":"Die Argumenttypen stimmen nicht ueberein."} - danach scheiterte
    # JEDES Werkzeug. Ursache: @() um eine List[object] hinter einem korrekten
    # "return ,$items".
    envelope_fn = region(source, "function New-Envelope",
                         "\n    # ------------------------------------------------------------------\n    # Werkzeuge, die das Programm selbst beantwortet")
    for field, getter in (("userAnswers", "Get-LateAskAnswers"),
                          ("openQuestions", "Get-PendingAskViews"),
                          ("userMessages", "Get-PendingUserMessageViews")):
        check(f"$envelope.{field} = $" in envelope_fn
              and f"@($" not in envelope_fn.split(f"$envelope.{field} = $")[1].split("\n")[0],
              f"Umschlagfeld {field} wird per .ToArray() und nie per @() geschrieben")
        check(getter in envelope_fn, f"Umschlagfeld {field} liest {getter}")
    check("`.ToArray()`" not in envelope_fn
          and envelope_fn.count(".ToArray()") >= 3,
          "Alle drei Umschlagfelder nutzen .ToArray() (List[object].ToArray() ist erlaubt)")
    # c) Ein Fehler in einem Umschlagfeld darf nie die Werkzeugantwort kosten.
    for station in ("USER_ANSWERS_SKIPPED", "OPEN_QUESTIONS_SKIPPED", "USER_MESSAGES_SKIPPED"):
        check(station in envelope_fn,
              f"Umschlagfeld ist defensiv gekapselt und meldet {station} statt zu scheitern")
    check(envelope_fn.count("} catch {") >= 3
          and "return $envelope" in envelope_fn,
          "New-Envelope liefert den Umschlag auch dann, wenn ein Zierfeld fehlschlaegt")
    # d) Das Gate muss die alte Fehlerklasse wirklich finden (Selbsttest).
    reconstructed = source.replace("$envelope.userAnswers = $lateAnswers.ToArray()",
                                   "$envelope.userAnswers = @($lateAnswers)")
    check(len(collection_return_problems(reconstructed)) == 1
          and not collection_return_problems(source),
          "Das Gate findet @( List[object] ) im nachgebauten 7.2.3-Stand und ist im 7.2.4-Stand leer")

    print("\n5c) Fragen-Fenster 7.2.4: Muss-Kriterien des Owners")
    # 2b: eigene Antwort immer sichtbar und tippbar.
    check("$customBox = [System.Windows.Controls.TextBox]::new()" in ui
          and "$customBox.Style = $Info.Window.FindResource('ArenaTextField')" in ui
          and "$customBox.AcceptsReturn = $true" in ui
          and "$customBox.AcceptsTab = $false" in ui
          and "$customBox.MaxLength = 4000" in ui,
          "Eigene Antwort ist ein echtes Textfeld mit Stil, Caret und Tab-Weitergabe")
    # WPF vergibt ohne expliziten TabIndex int.MaxValue; ein einzelner fester
    # Index wuerde das Feld VOR die Optionen legen. Visuelle Reihenfolge ist
    # hier die richtige - und Tab muss den Fokus weitergeben, nicht einruecken.
    check("$customBox.TabIndex" not in ui,
          "Kein fester TabIndex bricht die visuelle Tab-Reihenfolge der Optionen")
    check("if ($allowCustom) {" not in ui,
          "Das Textfeld haengt nicht mehr an allowCustomResponse - es ist immer da")
    check("$customBox.Add_TextChanged" in ui
          and "hier darf KEIN Neuzeichnen angestossen werden" in ui,
          "Tippen schreibt in die Antwort, ohne das Feld neu aufzubauen (Caret bleibt)")
    # 2c: ruhiges Einblenden.
    check("[TimeSpan]::FromMilliseconds(180)" in open_ask
          and "$win.Opacity = 0" in open_ask
          and "$win.Add_ContentRendered" in open_ask,
          "Das Fenster blendet in 180 ms ein, erst nachdem der Inhalt gerendert ist")
    # 2c/2d: kein Flackern - der Fragenbaum wird nur bei Strukturwechsel gebaut.
    check("$Info.RenderSignature = $signature" in ui
          and "if ($signature -eq [string]$Info.RenderSignature) {" in ui,
          "Der Fragenbereich wird nur bei echter Strukturänderung neu aufgebaut")
    # 2d: kein Auto-Schliessen, Restzeit sichtbar, zweite Anfrage aktualisiert.
    check("function Set-AskCountdownText" in source
          and "Set-AskCountdownText $Info $secondsLeft $askState" in ui
          and "Noch " in source,
          "Die Restzeit steht sichtbar in der Fusszeile")
    check("function Retarget-AskWindow" in source
          and "[void](Retarget-AskWindow $script:AskWindow.Tag $askId" in open_ask,
          "Eine zweite Anfrage aktualisiert dasselbe Fenster statt es zu schliessen")
    check("$script:AskWindowShownIds" in source
          and "if ($script:AskWindowShownIds.Contains($askId)) { return }" in open_ask,
          "Fuer dieselbe askId wird das Fenster nie erneut geoeffnet")
    # 2f: gruener Endzustand statt stillem Verschwinden.
    check("function Show-AskDoneState" in source
          and "Show-AskDoneState $data $path.Count" in open_ask
          and "Show-AskDoneState $Info $answeredCount" in ui,
          "Nach Fertig bleibt das Fenster offen und zeigt den gruenen Endzustand")
    done_fn = region(source, "function Show-AskDoneState", "function Update-AskWindow")
    check("gespeichert - Arena holt sie ab." in done_fn
          and "Stop-AskModal $Info" in done_fn
          and "Content=\"Schließen\"" in ask_xaml
          and "$info.DoneCloseButton.Add_Click" in open_ask,
          "Der Endzustand nennt die Zahl der Antworten, gibt die Oberflaeche frei und hat Schliessen")
    check("$Info.Window.Close()" not in done_fn,
          "Der Endzustand schliesst das Fenster nicht von allein")
    # 2e: kein Schliessen/Kopieren im normalen Ablauf.
    check("$Info.CopyPanel.Visibility = 'Collapsed'" in ui
          and "$Info.DonePanel.Visibility = 'Collapsed'" in ui,
          "Im normalen Ablauf sind Kopier- und Endzustandbereich unsichtbar")
    # 2h: modal mit Notausgaengen.
    check("Start-AskModal $info" in open_ask
          and "$window.IsEnabled = $false" in source
          and "Stop-AskModal $data" in open_ask,
          "Das Fenster sperrt die Hauptoberflaeche und gibt sie bei Antwort/Abbruch/Ablauf frei")
    check("$titleBar.Add_MouseLeftButtonDown" in open_ask and "DragMove()" in open_ask,
          "Die Titelzeile zieht das Fenster (DragMove)")
    # 2i: Groesse.
    check('Width="480" Height="420"' in ask_xaml
          and 'SizeToContent="Height"' in ask_xaml
          and "$win.MaxHeight = $windowMaxHeight" in open_ask,
          "Startgroesse 480 x 420, hoehenbasiert, gedeckelt auf 70 % der Bildschirmhoehe")
    check('x:Name="QuestionScroll"' in ask_xaml
          and 'VerticalScrollBarVisibility="Auto"' in ask_xaml,
          "Lange Texte scrollen in der Karte, nicht das Fenster")
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
    check(version["version"] == VERSION, "version.json identifiziert 7.3.1")
    notes = "\n".join(str(note) for note in version.get("notes", []))
    for word in ("7.2.4", "P0-BLOCKER", ".ToArray()",
                 "gemeinsamen XAML-Ressourcenblock",
                 "Eigene Antwort", "runtime.log",
                 "7.2.3", "LIVE-SAMMLUNGEN", "ASK_CANCELLED", "Strg+Enter",
                 "NOTIFICATION_UNVERIFIED", "notify-diagnose.txt"):
        check(word in notes, f"version.json beschreibt: {word}")
    check("DocsVersion     = '7.3.1'" in source and 'local ARENA_VERSION  = "7.3.1"' in source,
          "Alle funktionalen Versionsstellen stehen auf 7.3.1")
    for marker in ("Set-StartupStage", "startup-trace.txt", "START-NETZ KOMPLETT",
                   "$script:WindowShown", "function Start-BridgeRuntime",
                   "$window.Add_ContentRendered({", "Start fehlgeschlagen"):
        check(marker in source, f"7.2.7-Startnetz-Marker vorhanden: {marker}")

    # 7.2.9 (START-BLOCKER): Der Start starb nicht an einer Ausnahme, sondern
    # blieb stecken - dafuer hilft kein try/catch. Zwei Stellen sind gesichert:
    # das modale Hinweisfenster VOR dem Hauptfenster und der ungeschuetzte
    # Bereich vor dem Fensterbau.
    trap_head = source.index("$ErrorActionPreference = 'Stop'")
    trap_at = source.index("trap {")
    window_build_at = source.index("Set-StartupStage 'Fensteraufbau: XAML wird geladen'")
    check(trap_head < trap_at < window_build_at,
          "7.3.0: trap auf Skriptebene sitzt VOR dem Fensterbau und faengt jeden nicht abgefangenen Fehler")
    check("trap {\n    $trapMessage = ''" in source
          and "startup-diagnose.txt" in source[trap_at:trap_at + 6000]
          and "notepad.exe" in source[trap_at:trap_at + 6000]
          and "\n    break\n}\n" in source[trap_at:trap_at + 6000],
          "7.3.0: Der trap sichert den Fehler (startup-diagnose.txt), zeigt ihn notfalls in "
          "Notepad und beendet danach sauber")
    notice = region(source, "function Show-UpdateNotice", "# ----------------------------------------------------------------------------\n# EINSTELLUNGSFENSTER")
    check("NOTICE_OPACITY_RESCUE" in notice and "NOTICE_WATCHDOG" in notice,
          "7.3.0: Hinweisfenster hat Rettungs-Timer UND Waechter (unsichtbar = Start-Blocker)")
    rescue_at = notice.index("FromMilliseconds(700)")
    fade_at = notice.index("FromMilliseconds(240)")
    dialog_at = notice.index("[void]$noticeWindow.ShowDialog()")
    check(rescue_at < fade_at < dialog_at,
          "7.3.0: Der 700-ms-Rettungstimer startet VOR der Einblend-Animation und vor ShowDialog")
    watchdog_at = notice.index("FromMilliseconds(2500)")
    check(watchdog_at < dialog_at and "IsLoaded" in notice and "IsVisible" in notice
          and "damit das Programm starten kann" in notice,
          "7.3.0: Der Waechter schliesst ein unsichtbares Hinweisfenster, statt den Start zu blockieren")
    check("[System.Windows.Input.Key]::Escape" in notice,
          "7.3.0: Esc ist ein Notausgang aus dem modalen Hinweisfenster")
    for guarded in ("if ($noticeTitleEl)", "if ($noticeSubEl)",
                    "if ($noticeNotesEl)", "if ($noticeOkEl)"):
        check(guarded in notice, f"7.3.0: FindName-Ergebnis wird geprueft: {guarded}")
    check("$noticeNoteItems.ToArray()" in notice and "[string]::Join(" in notice
          and "6000" in notice,
          "7.3.0: Die notes-LISTE erscheint als Absaetze (mit Umbruechen) und ist gedeckelt")
    check("[string]$script:UpdateDetails.notes" not in source,
          "7.3.0: notes wird nicht mehr mit [string] zu einer Zeile ohne Umbruch gepresst")
    check("$script:UpdateNoticeWindow" in notice,
          "7.3.0: Hinweisfenster liegt im Skriptbereich (Timer/Handler erreichen es sicher)")
    try:
        start_area = region(source, "# START: Ereignisse stehen VOR ShowDialog",
                            "# Sicherheitsnetz (Version 3.4): Falls das Closed-Ereignis")
        rendered_at = start_area.index("$window.Add_ContentRendered({")
        dialog_at = start_area.index("[void]$window.ShowDialog()")
        closed_at = start_area.index("$window.Add_Closed({")
        handler = region(start_area, "$window.Add_ContentRendered({", "    })\n    Set-StartupStage")
        timer_at = handler.index("FromMilliseconds(500)")
        opacity_clear_at = handler.index("OpacityProperty, $null")
        opacity_visible_at = handler.index("$window.Opacity = 1")
        init_at = handler.index("Start-BridgeRuntime")
        check(rendered_at < dialog_at and closed_at < dialog_at,
              "ShowDialog/cleanup stehen bereit, bevor ContentRendered die Initialisierung ausloest")
        # 7.3.0 (STARTGARANTIE): Der Update-/Willkommenshinweis laeuft NICHT
        # mehr vor dem Hauptfenster (ein modales Fenster dort konnte den ganzen
        # Start unsichtbar festhalten), sondern in genau derselben
        # Einmal-Initialisierung direkt nach dem sichtbaren Fenster und VOR den
        # Diensten. Damit ist die Bridge in jedem Fall sichtbar.
        notice_call = "if ($UpdateStatus -eq 'update-erfolgreich' -or $UpdateStatus -eq 'erster-start')"
        check(notice_call in handler and "Show-UpdateNotice" in handler
              and notice_call not in start_area[:rendered_at],
              "7.3.0: Der Update-/Willkommenshinweis laeuft erst nach dem sichtbaren Hauptfenster (nie davor)")
        notice_at = handler.index("Show-UpdateNotice")
        check(opacity_visible_at < notice_at < init_at,
              "7.3.0: Hinweis erscheint nach der harten Deckkraft-Sicherung und vor Start-BridgeRuntime")
        check(timer_at < opacity_clear_at < opacity_visible_at < init_at,
              "WPF bekommt 500 ms zum Rendern; die Deckkraft wird vor jedem potenziell blockierenden Startschritt hart auf 1 gesetzt")
        runtime_function = region(source, "function Start-BridgeRuntime", "# ----------------------------------------------------------------------------\n# START: Ereignisse stehen VOR ShowDialog")
        check("Show-UpdateNotice" not in runtime_function
              and source.count("Show-UpdateNotice }") == 1,
              "7.3.0: Der Update-Hinweis wird genau einmal geoeffnet (im Einmal-Timer, nicht in Start-BridgeRuntime)")
        check("if ($script:StartupRuntimeStarted) { return }" in handler
              and "$script:StartupRuntimeStarted = $true" in handler,
              "ContentRendered startet den Runtime-Start genau einmal")
    except ValueError as exc:
        check(False, f"Window-first-Startsequenz nicht auswertbar: {exc}")
    check("$splash.Visibility = 'Visible'" in source
          and "$headline.Text = 'Start fehlgeschlagen'" in source,
          "Startfehler nach dem ersten Rendern bleiben im sichtbaren Splash erklaert")
    # 7.3.0 (STARTGARANTIE): Diese fuenf Pruefungen halten die Ursachenklassen
    # fest, die "es passiert gar nichts" erzeugen - sie duerfen nicht
    # zurueckgebaut werden.
    loaded_handler = region(source, "$window.Add_Loaded({", "Set-StartupStage 'Ereignisse verdrahtet")
    check("$window.Opacity = 0" not in loaded_handler
          and "$window.Opacity = 1" in loaded_handler
          and "[System.Windows.Media.Animation.FillBehavior]::Stop" in loaded_handler,
          "7.3.0: Hauptfenster startet mit sichtbarem Grundwert (Opacity 1), Einblendung ist nur Verzierung")
    notice_region = region(source, "function Show-UpdateNotice", "# EINSTELLUNGSFENSTER")
    check("$noticeWindow.Opacity = 1" in notice_region
          and "$noticeWindow.Opacity = 0" not in notice_region
          and "$noticeWindow.Owner = $script:MainWindow" in notice_region
          and "CenterOwner" in notice_region,
          "7.3.0: Hinweisfenster ist sofort sichtbar und gehoert dem Hauptfenster (Owner/CenterOwner)")
    check("foreach ($bridgeAssembly in @('PresentationFramework', 'PresentationCore', 'WindowsBase', 'System.Web'))" in source
          and "\nAdd-Type -AssemblyName PresentationFramework\n" not in source
          and "\nAdd-Type -AssemblyName System.Web\n" not in source,
          "7.3.0: Die vier Assembly-Aufrufe am Skriptanfang sind einzeln gesichert (kein lautloser Tod vor dem Fenster)")
    check("START-CHECK.txt" in source and "Letzte erreichte Startstufe" in source
          and "Fenster sichtbar" in source,
          "7.3.0: %LOCALAPPDATA%\\START-CHECK.txt belegt bei jeder Startstufe, wie weit der Start kam")
    check(source.count("notepad.exe") >= 2 and "Start-Process -FilePath 'notepad.exe'" in source,
          "7.3.0: Letzter sichtbarer Weg (Diagnosedatei in Notepad) fehlt in trap und Startdiagnose nicht")
    check("-WorkingDirectory $script:AppFolder -PassThru" in source
          and "$restartProc.HasExited" in source and "$restartTry -le 2" in source,
          "7.3.0: Der Neustart nach einem Autostart-Update wird geprueft und genau einmal wiederholt "
          "(kein stilles Ende nach dem Update)")
    problems = collection_return_problems(source)
    for problem in problems:
        print(f"    {problem}")
    check(not problems,
          "Keine Generic-Sammlung wird entpackbar zurueckgegeben (return ,$liste) "
          "und keine wird in @() gelegt (Binderfehler - .ToArray() statt @())")
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

    # 7.3.1-Regressionstor: Auf Windows PowerShell 5.1 darf ein Operator (+, *,
    # /, %, -binary) NICHT am Anfang einer Fortsetzungszeile stehen. Der Parser
    # behandelt einen Zeilenumbruch direkt vor einem Operator als
    # Anweisungsende - das erzeugte in 7.3.0 9 Parse-Fehler ab Zeile 27432.
    # Operatoren gehoeren an das Ende der vorherigen Zeile.
    # Wir filtern hier-strings (@'...'@ / @"..."@) und Kommentare heraus, da
    # dort fuehrende Operatoren Teil des eingebetteten Codes (Lua, Bullet-
    # Listen in Beschreibungen) sind und von PowerShell nicht als Operator
    # interpretiert werden.
    def operator_at_line_start_problems(text: str) -> list[str]:
        import re
        problems: list[str] = []
        lines_t = text.split("\n")
        in_hs_single = False
        in_hs_double = False
        # Matches a binary operator at line start (after indentation).
        op_re = re.compile(r"^(\s+)(\+|\*|/|%|-(?:replace|match|eq|ne|gt|lt|ge|le|like|notmatch|notlike|contains|in|is|as|join|split|f|and|or|band|bor|bxor)?)(?=\s)")
        safe_end_tokens = ("`", "|", ",", "+", "-", "*", "/", "%", "=", "(", "{", "[", "@(", "@{", "$(", "::", ".", "\\",
                           "-and", "-or", "-replace", "-join", "-split", "-f", "-is", "-as", "-eq", "-ne", "-gt", "-lt")
        for i, line_t in enumerate(lines_t):
            stripped_end = line_t.rstrip()
            if in_hs_single:
                if line_t.lstrip().startswith("'@"):
                    in_hs_single = False
                continue
            if in_hs_double:
                if line_t.lstrip().startswith('"@'):
                    in_hs_double = False
                continue
            if stripped_end.endswith("@'"):
                in_hs_single = True
                continue
            if stripped_end.endswith('"@'):
                in_hs_double = True
                continue
            m = op_re.match(line_t)
            if not m:
                continue
            op = m.group(2)
            cur_lstrip = line_t.lstrip()
            if cur_lstrip.startswith("#") or cur_lstrip.startswith("--"):
                continue
            if i == 0:
                problems.append(f"Zeile {i+1}: Operator {op!r} am Zeilenanfang ohne vorherige Zeile")
                continue
            prev_rstrip = lines_t[i-1].rstrip()
            if not prev_rstrip or prev_rstrip.lstrip().startswith("#"):
                continue
            if prev_rstrip.endswith(safe_end_tokens):
                continue
            problems.append(
                f"Zeile {i+1}: Operator {op!r} steht am Zeilenanfang "
                f"(Windows-PowerShell-5.1-Parse-Fehler!); vorherige Zeile endet mit "
                f"...{prev_rstrip[-60:]!r}"
            )
        return problems

    op_problems = operator_at_line_start_problems(source)
    for problem in op_problems:
        print(f"    {problem}")
    check(not op_problems,
          "Kein Operator (+, *, /, %, -bin.) steht am Anfang einer Fortsetzungszeile "
          "(Parse-Fehler auf Windows PowerShell 5.1)")

    check((ROOT / "parse-gate.ps1").is_file(), "Echtes Parser-Gate vorhanden")
    check("PROOF_OF_LIFE Version=7.3.1" in source,
          "Proof-of-Life mit aktueller Version vorhanden")
    engine = shutil.which("powershell") or shutil.which("pwsh")
    if engine:
        result = subprocess.run([engine, "-NoProfile", "-ExecutionPolicy", "Bypass",
                                 "-File", str(ROOT / "parse-gate.ps1")],
                                capture_output=True, text=True, timeout=120)
        print(result.stdout)
        print(result.stderr)
        check(result.returncode == 0, "Echter PowerShell-Parser (siehe Engine-Version oben)")
    else:
        print("  UEBERSPRUNGEN: echter PowerShell-Parser; powershell/pwsh fehlen. "
              "Windows-PowerShell-5.1-Gate vor Freigabe erforderlich.")

    print()
    if failures:
        print(f"ROT: {len(failures)} Pruefung(en) fehlgeschlagen:")
        for entry in failures:
            print(f"  - {entry}")
        return 1
    print("OK: Offline-Pruefungen abgeschlossen. Kein Nachweis eines Windows-Fensterstarts.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
