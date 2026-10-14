#!/usr/bin/env python3
"""Offline-Regressionsgate für den 8.0.0-Auftrag "weniger Viren-Fehlalarme".

Der Nutzer hat gemeldet, dass VirusTotal die veröffentlichte
ArenaRobloxBridge.exe mit 15/58 Engines als schädlich meldet (u. a.
Trojan:Win32/Wacatac.B!ml, Gen:Variant.MSILHeracles.270602, Ti!AE365B8A2D5B).
Das sind Fehlalarme: Die Bridge ist ein PowerShell-Programm, das mit ps2exe in
eine EXE gepackt wird - dieses Bau-Muster verdächtigen Scanner systematisch.

Dieses Gate prüft auf Quellebene, dass die dagegen umgesetzten Maßnahmen
vorhanden und gefahrlos sind:

  1. Der Bau bleibt OHNE Zertifikat exakt wie vorher (unsigniert).
  2. Mit Zertifikat wird VOR dem Smoke-Test signiert, und eine ungültige
     Signatur bricht den Bau ab (nie eine "halb signierte" EXE veröffentlichen).
  3. Die Dateiinformationen (Copyright/Warenzeichen) sind vollständig.
  4. Die Meldedokumentation für die Scanner-Hersteller existiert und nennt
     Meldewege, Textvorlage und Zertifikatswege.

Windows-Verhalten (ps2exe-Bau, signtool/Set-AuthenticodeSignature, SmartScreen,
VirusTotal-Ergebnis) ist hier NICHT ausführbar und bleibt ein Windows-Test.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]          # next-update/
BUILDER = ROOT / "builder" / "Build-EXE.ps1"
BAT = ROOT / "Build-EXE.bat"
DOCS = ROOT / "developer" / "docs"
FP_DOC = DOCS / "FALSE-POSITIVE-MELDUNG.md"
START_TEXT = ROOT / "START-HIER.txt"
UPDATE_SYSTEM = DOCS / "UPDATE-SYSTEM.md"
HANDOFF = DOCS / "GANZ WICHTIG LESEN VOR JEDER BEARBEITUNG"
DOWNLOAD_PAGE = "https://arena-rblx-bridge.netlify.app/"

BUILD_TEXT = BUILDER.read_text(encoding="utf-8")
BUILD_LINES = BUILD_TEXT.splitlines()
FAILURES: list[str] = []


def check(condition: bool, label: str) -> None:
    print(("  ok   " if condition else "  FAIL ") + label)
    if not condition:
        FAILURES.append(label)


def function_block(name: str) -> str:
    """Quelltext einer PowerShell-Funktion (bis zur schließenden Klammer in Spalte 0)."""
    start = BUILD_TEXT.find(f"function {name} {{")
    if start < 0:
        return ""
    end = BUILD_TEXT.find("\n}\n", start)
    return BUILD_TEXT[start:end + 3] if end > start else ""


def line_of(needle: str, start: int = 0) -> int:
    for index in range(start, len(BUILD_LINES)):
        if needle in BUILD_LINES[index]:
            return index
    return -1


def test_signing_stays_optional() -> None:
    print("\n-- Signatur bleibt optional: ohne Zertifikat baut die Bridge wie vorher")
    for parameter in ("[string]$SignCertificatePath = ''",
                      "[string]$SignCertificateThumbprint = ''",
                      "[string]$SignCertificatePassword = ''",
                      "[string]$SignTimestampUrl = 'http://timestamp.digicert.com'"):
        check(parameter in BUILD_TEXT, f"Builder kennt {parameter.split('=')[0].strip()}")
    check("$env:ARENABRIDGE_SIGN_PFX" in BUILD_TEXT
          and "$env:ARENABRIDGE_SIGN_PFX_PASSWORD" in BUILD_TEXT,
          "Zertifikat und Passwort können auch über Umgebungsvariablen kommen "
          "(Build-EXE.bat bleibt der eine Startknopf)")
    bat = BAT.read_text(encoding="ascii")
    check("-Channel stable -NonInteractive" in bat
          and "SignCertificate" not in bat and "ARENABRIDGE_SIGN" not in bat,
          "Build-EXE.bat bleibt unverändert (Signatur über Umgebungsvariablen, kein zweiter Knopf)")
    guard = function_block("Resolve-BridgeSigningCertificate")
    check(guard != "", "Die Funktion Resolve-BridgeSigningCertificate ist vorhanden")
    check("if ([string]::IsNullOrWhiteSpace($CertificatePath) -and [string]::IsNullOrWhiteSpace($CertificateThumbprint)) {\n        return $null\n    }" in guard,
          "Ohne Zertifikatsangabe passiert nichts (Rückgabe $null)")
    check("ContainsKey('copyright')" in BUILD_TEXT and "ContainsKey('trademark')" in BUILD_TEXT,
          "Copyright/Warenzeichen werden nur übergeben, wenn die installierte ps2exe-Version sie kennt")


def test_signing_fails_loudly() -> None:
    print("\n-- Signiert wird vor dem Smoke-Test, und nur mit gültigem Ergebnis")
    sign = function_block("Invoke-BridgeCodeSign")
    check(sign != "", "Die Funktion Invoke-BridgeCodeSign ist vorhanden")
    check("Set-AuthenticodeSignature @signParameters" in sign
          and "HashAlgorithm = 'SHA256'" in sign
          and "Confirm = $false" in sign,
          "Signiert wird per Set-AuthenticodeSignature (SHA256, ohne Rückfrage)")
    check("LiteralPath = $ExecutablePath" in sign,
          "Der Pfad wird ohne Platzhalter-Übersetzung benutzt (LiteralPath)")
    check("$signParameters['TimestampServer'] = $TimestampUrl" in sign
          and "without internet the timestamp server is unreachable" in sign,
          "Zeitstempel-Server ist gesetzt und der Hinweis für Offline-Rechner steht dabei")
    check("throw ('Code signing failed; the EXE was not published. '" in sign,
          "Eine fehlgeschlagene Signatur bricht den Bau ab (nichts wird veröffentlicht)")
    check("Get-AuthenticodeSignature -LiteralPath $ExecutablePath" in sign
          and "$verifiedStatus -ne 'Valid'" in sign,
          "Die fertige Signatur wird unabhängig nachgeprüft (Status muss Valid sein)")
    check("X509Certificate2]::new($CertificatePath,$CertificatePassword,$flags)"
          in function_block("Resolve-BridgeSigningCertificate"),
          "Ein .pfx mit privatem Schlüssel wird geladen (Passwort über Parameter/Variable/Abfrage)")
    check("The .pfx does not contain a private key" in BUILD_TEXT
          and "and a private key was found in Cert:" in BUILD_TEXT,
          "Ein Zertifikat ohne privaten Schlüssel wird mit klarer Meldung abgelehnt")
    resolve_line = line_of("Resolve-BridgeSigningCertificate -CertificatePath $SignCertificatePath")
    compile_line = line_of("Invoke-BridgeCompiler -InputPath", start=0)
    check(0 <= resolve_line < compile_line,
          "Das Zertifikat wird VOR dem teuren Kompilieren aufgelöst (schneller, klarer Abbruch)")
    sign_line = line_of("$signatureInfo = Invoke-BridgeCodeSign -ExecutablePath $stagingExePath")
    smoke_line = line_of("Test-StagedExecutable -ExecutablePath $stagingExePath")
    publish_line = line_of("Publish-LocalBuild -StagingPath $stagingExePath")
    check(0 <= compile_line < sign_line < smoke_line < publish_line,
          "Reihenfolge stimmt: kompilieren -> signieren -> Smoke-Test -> einsetzen")


def test_file_information_complete() -> None:
    print("\n-- Vollständige Dateiinformationen gegen Heuristiken")
    check("-Copyright 'Copyright (C) 2026 MertaStudios' -Trademark 'Arena Roblox Bridge'"
          in BUILD_TEXT,
          "Copyright und Warenzeichen gehen an den Compiler")
    for field in ("signedWithAuthenticode", "signerSubject", "signerThumbprint",
                  "signTimestampUrl", "fileCopyright", "fileTrademark"):
        check(field + " = " in BUILD_TEXT, f"release-metadata.json notiert {field}")
    check("Code signing is NOT enabled" in BUILD_TEXT
          and "FALSE-POSITIVE-MELDUNG.md" in BUILD_TEXT,
          "Der Bau nennt im Klartext, dass ohne Zertifikat keine Signatur entsteht, und verweist auf die Meldedoku")


def test_false_positive_documentation() -> None:
    print("\n-- Meldedokumentation für die Scanner-Hersteller")
    check(FP_DOC.is_file(), "developer/docs/FALSE-POSITIVE-MELDUNG.md existiert")
    doc = FP_DOC.read_text(encoding="utf-8") if FP_DOC.is_file() else ""
    for marker, label in (
            ("15 von 58", "Das gemeldete Ergebnis 15/58 ist dokumentiert"),
            ("MSILHeracles", "Die gemeldete Schadfamilie ist dokumentiert"),
            ("ps2exe", "Die Ursache (ps2exe-Bau-Muster) ist dokumentiert"),
            ("https://www.microsoft.com/en-us/wdsi/filesubmission", "Microsoft-Meldeweg"),
            ("fp@emsisoft.com", "Emsisoft-Meldeweg"),
            ("https://www.vipre.com/support/submit-false-positive/", "VIPRE-Meldeweg"),
            ("https://www.trendmicro.com/en_us/about/legal/detection-reevaluation.html", "Trend-Micro-Meldeweg"),
            ("report@sentinelone.com", "SentinelOne-Meldeweg"),
            ("https://docs.virustotal.com/docs/false-positive-contacts", "VirusTotal-Sammelliste"),
            ("SHA-256:", "Fertige Textvorlage für die Meldung"),
            (DOWNLOAD_PAGE, "Die Download-Seite steht in der Vorlage"),
            ("ARENABRIDGE_SIGN_PFX", "Der Signatur-Weg über den Builder ist dokumentiert"),
            ("Azure Trusted Signing", "Bezugsquellen für Zertifikate sind dokumentiert"),
            ("Obfuskation", "Was NICHT hilft, steht ausdrücklich drin")):
        check(marker in doc, f"FALSE-POSITIVE-MELDUNG.md nennt {label}")

    start = START_TEXT.read_text(encoding="utf-8")
    check("FALSE-POSITIVE-MELDUNG.md" in start and "Fehlalarme" in start
          and "ps2exe" in start,
          "START-HIER.txt erklärt dem Nutzer die Fehlalarme und verweist auf die Doku")
    check("setx ARENABRIDGE_SIGN_PFX" in start,
          "START-HIER.txt nennt den Ein-Zeiler für ein Signaturzertifikat")
    index = (ROOT / "website" / "index.html").read_text(encoding="utf-8")
    check("Fehlalarm" in index and "unbekannter Herausgeber" in index,
          "Die Download-Seite ordnet SmartScreen-/Scanner-Warnungen als Fehlalarm ein")
    check("FALSE-POSITIVE-MELDUNG.md" in (ROOT / "website" / "README.md").read_text(encoding="utf-8"),
          "website/README.md verweist auf die Meldedoku")
    update_system = UPDATE_SYSTEM.read_text(encoding="utf-8")
    check("FALSE-POSITIVE-MELDUNG.md" in update_system
          and "-SignCertificatePath" in update_system
          and "ARENABRIDGE_SIGN_PFX" in update_system,
          "UPDATE-SYSTEM.md beschreibt die optionale Signatur und verweist auf die Doku")
    handoff = HANDOFF.read_text(encoding="utf-8")
    check("NACHTRAG 8.0.0" in handoff
          and "DuplicateKeyInHashLiteral" in handoff
          and "FALSE-POSITIVE-MELDUNG.md" in handoff,
          "Das Übergabedokument hat den Nachtrag 8.0.0 (Parserfehler-Fix + Fehlalarm-Maßnahmen)")


def main() -> int:
    print("8.0.0 offline checks: Viren-Fehlalarme")
    test_signing_stays_optional()
    test_signing_fails_loudly()
    test_file_information_complete()
    test_false_positive_documentation()
    print()
    if FAILURES:
        print(f"FAILED: {len(FAILURES)} check(s).")
        return 1
    print("OK: Signaturmaßnahmen und Meldedokumentation sind auf dieser Prüfebene in Ordnung.")
    print("Windows/signtool, SmartScreen und das echte VirusTotal-Ergebnis bleiben ein Windows-Test.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
