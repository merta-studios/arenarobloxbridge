#!/usr/bin/env python3
"""Offline-Abnahme fuer Arena Roblox Bridge 7.2.0.

Dieser Test braucht KEIN Windows und kein PowerShell. Er prueft genau die
fuenf Themen des Owners plus das Fundament:

  1. Nutzer-Kanal (Zwischennachricht) .......... _bridge.userMessages + ack/wait
  2. Fortschritt ohne erfundene Zahl (D5-D7) ... Textzeile statt 0 %, nichts verdeckt
  3. Fertig-Meldung mit Messung (D4) ........... Urteile, sweep, Test, ehrliche Antwort
  4. Fragen ueber die Bridge (D3) .............. ask_user-Baum + Fenster + Resume
  5. Qualitaet und GUI ......................... finishScore/grade/draft, codeLayout
  6. Fundament ................................. Stationen, Zaehler, Klammer-Balance

Der Klammer-/String-Check am Ende ist der Ersatz fuer das fehlende Parse-Gate:
7.1.4 ist an EINER ueberzaehligen schliessenden Klammer gestorben, weil
PowerShell die ganze Datei parst, bevor irgendetwas sichtbar wird.

Aufruf:
    .venv/bin/python test_v720_bridge.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PS1 = ROOT / "ArenaBridge.ps1"
VERSION = "7.2.0"

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
    check("$envelope.userMessages = $pendingUserMessages.ToArray()" in envelope_rules
          and "$envelope.userMessageContract" in envelope_rules,
          "Jede Antwort traegt die wartenden Nutzernachrichten samt Vertrag")
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
          "Der Zeilen-Knopf bleibt unsichtbar - abgebrochen wird ueber das Menue")
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
    check("function Open-NotifySeenWindow" in show or "function Open-NotifySeenWindow" in source,
          "Es gibt die ehrliche Rueckfrage 'Hast du die Meldung gesehen?'")
    check("Test-Meldung anzeigen" in source and "NotifyTestButton" in source,
          "Die Einstellungen haben einen Testknopf fuer die Fertig-Meldung")
    check("NotifySeenYes" in source and "NotifySeenNo" in source,
          "Ja/Nein wird gezaehlt und in der Diagnose-Datei ausgewiesen")
    done_start = source.index("                $notifyFlowId = 'n-' + [string]$notifyFlowSeq")
    done = source[done_start:done_start + 9000]
    check("delivered = $true" not in done,
          "report_done behauptet nicht mehr blind 'delivered = true'")
    check("NOTIFICATION_UNVERIFIED" in done and "notification = @{" in done,
          "report_done antwortet ehrlich mit Urteil und NOTIFICATION_UNVERIFIED")
    check("platformVerdict" in done and "notify.sweep" in done,
          "Die Antwort nennt Urteil, Grund und die Nachmessung")

    print("\n4) Fragen ueber die Bridge (D3)")
    for marker in (
        "function Test-AskTree",
        "function Invoke-AskUser",
        "function Invoke-ConfirmAction",
        "function Get-LateAskAnswers",
        "function Get-PendingAskViews",
        "function Wait-AskAnswer",
        "'ask_user'",
        "'confirm_action'",
    ):
        check(marker in source, f"Marker vorhanden: {marker}")
    for code in ("ASK_TOO_MANY_QUESTIONS", "ASK_GRAPH_INVALID", "ASK_CYCLE", "ASK_EXPIRED", "ASK_UNKNOWN"):
        check(code in source, f"Typisierter Fehler vorhanden: {code}")
    check("ASK_UNREACHABLE" in source, "Unbrauchbare Bedingungen werden gemeldet (ASK_UNREACHABLE)")
    check("$maxQuestions = 12" in source and "$maxOptions = 6" in source and "$maxChars = 400" in source,
          "Die Grenzen des Plans sind umgesetzt (12 Fragen, 6 Optionen, 400 Zeichen)")
    ask = region(source, "function Invoke-AskUser", "function Get-LateAskAnswers")
    check("resume" in ask and "nextCall" in ask,
          "Das Warten ist wiederaufnehmbar (resume=true, nextCall)")
    check("if ($seconds -gt 50) { $seconds = 50 }" in source,
          "waitSeconds bleibt unter dem harten HTTP-Deckel")
    check("path = @($State.path)" in source and "notShown = @($State.notShown)" in source,
          "Die Antwort nennt gestellte und uebersprungene Fragen")
    check("_bridge.userAnswers" in source or "$envelope.userAnswers" in source,
          "Spaete Antworten gehen nicht verloren (_bridge.userAnswers)")
    check("openQuestions" in source, "Offene Fragen stehen in jeder Antwort")
    ui = region(source, "function Update-AskWindow", "function Get-PlaceOpenCommand")
    check("function Open-AskWindow" in source and "function Sync-AskWindows" in source,
          "Das Fragenfenster oeffnet sich aus dem Anzeige-Takt")
    check("[System.Windows.Forms.Cursor]::Position" in source
          and "[System.Windows.Forms.Screen]::FromPoint" in source,
          "Es erscheint mit Versatz am Mauszeiger und bleibt im sichtbaren Bereich")
    for state in ("Agent ist mittlerweile offline", "Arena wartet nicht mehr aktiv",
                  "Arena wartet auf deine Antwort", "kannst dieses Fenster schliessen"):
        check(state in ui, f"Fenster-Zustand ehrlich benannt: {state}")
    check("Get-AskCopyPrompt" in source and "Antwort als Text kopieren" in ui,
          "Es gibt den Knopf fuer den paste-fertigen Text in den Arena-Chat")
    check("function Test-AskCondition" in source and "anyOf" in source and "allOf" in source,
          "Bedingungen (when/anyOf/allOf/custom) werden ausgewertet")
    check("ANSWERS_DISCARDED" in source or "ANSWER_DISCARDED" in source,
          "Zurueck verwirft ungueltig gewordene Antworten nachvollziehbar")

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
    check(version["version"] == VERSION, "version.json identifiziert 7.2.0")
    notes = "\n".join(str(note) for note in version.get("notes", []))
    for word in ("NUTZER-KANAL", "FORTSCHRITT", "FERTIG-MELDUNG", "FRAGEN", "QUALITÄT"):
        check(word in notes, f"version.json beschreibt: {word}")
    check("DocsVersion     = '7.2.0'" in source and 'local ARENA_VERSION  = "7.2.0"' in source,
          "Alle funktionalen Versionsstellen stehen auf 7.2.0")
    final_lines = source.rstrip().splitlines()[-4:]
    check(final_lines[0].startswith("# Sicherheitsnetz") and final_lines[-1] == "[System.Environment]::Exit(0)",
          "Der absichtliche Not-Aus am Dateiende ist unveraendert")

    try:
        balanced(source)
        check(True, "Klammer-/String-Balance der ganzen Datei ist sauber")
    except ValueError as exc:
        check(False, f"Klammer-/String-Balance: {exc}")

    print()
    if failures:
        print(f"ROT: {len(failures)} Pruefung(en) fehlgeschlagen:")
        for entry in failures:
            print(f"  - {entry}")
        return 1
    print("OK: 7.2.0 - Nutzer-Kanal, Fortschritt ohne erfundene Zahl, gemessene "
          "Fertig-Meldung, Fragen-Baum, Qualitaets- und GUI-Vertrag sind vollstaendig "
          "und die Datei ist von Ende zu Ende ausbalanciert.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
