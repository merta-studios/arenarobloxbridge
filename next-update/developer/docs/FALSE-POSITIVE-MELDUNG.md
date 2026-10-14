# Viren-Fehlalarme (False Positives) — was wirklich hilft

Stand: 14.10.2026, Version 8.0.0. Gilt für `release\ArenaRobloxBridge.exe`.

## Das Problem in drei Sätzen

Die veröffentlichte `ArenaRobloxBridge.exe` (Version 7.9.5, SHA-256 beginnt mit
`ae365b8a2d5b…`) wurde auf VirusTotal von **15 von 58 Engines** gemeldet
(u. a. `Trojan:Win32/Wacatac.B!ml`, `Gen:Variant.MSILHeracles.270602`,
`Ti!AE365B8A2D5B`). Das sind **Fehlalarme**: Die Bridge ist ein PowerShell-Programm,
das mit **ps2exe** in eine EXE gepackt wird. Genau dieses Bau-Muster
(unsignierte EXE + eingebettetes PowerShell-Skript) wird von Virenscannern
systematisch verdächtigt, weil es auch von Schadsoftware benutzt wird.

## Warum das passiert (und nicht am Programmcode liegt)

- **Eingebettetes Skript + Host-Stub:** ps2exe legt das komplette Skript als
  Ressource in die EXE und startet es über einen Host-Stub. Der Stub ist bei
  **allen** ps2exe-Programmen identisch — also auch bei den vielen
  Schadprogrammen, die damit gebaut wurden. Die Heuristiken greifen den Stub,
  nicht die Bridge.
- **Keine Signatur:** Ohne Authenticode-Signatur fehlt Scannern jeder
  Reputations-Anker. Unsignierte, selbst gebaute EXE = „unbekannt“ = verdächtig.
- **`!ml`-Erkennungen** (z. B. `Wacatac.B!ml`) sind Machine-Learning-Treffer, keine
  Signaturen einer bekannten Schadfamilie. Solche Treffer treffen regelmäßig
  Entwickler-Builds, Installer und Tools wie ps2exe.
- **Bestätigt von außen:** Das ist ein seit Jahren bekanntes, dokumentiertes
  ps2exe-Problem (siehe die False-Positive-Threads im ps2exe-Umfeld und die
  Antworten der Vendor-Support-Teams: „This is a False Positive and it will be
  fixed in the next update.“).

Wichtig: **Kein** bekannter Schadcode in diesem Repository. Wer die Datei
prüfen will, vergleicht die SHA-256 aus `release/latest.json` (bzw. von der
Download-Seite) mit der heruntergeladenen Datei.

## Was WIRKLICH hilft (in dieser Reihenfolge)

### 1. Fehlalarm bei den Vendors melden (sofort, kostenlos, größte Wirkung)

Die meisten der 15 Treffer verschwinden nach einer Meldung innerhalb weniger
Tage, weil die Hersteller die Datei dann echt prüfen. **Wichtig:** immer den
VirusTotal-Link der Datei mitschicken, nicht die EXE als Mail-Anhang an fremde
Adressen.

| Engine/Treffer | Wohin melden |
| --- | --- |
| Microsoft Defender (`Trojan:Win32/Wacatac.B!ml`) | <https://www.microsoft.com/en-us/wdsi/filesubmission> („Software developer“ → Dispute) |
| McAfee (`Ti!AE365B8A2D5B`) | <https://www.mcafee.com/en-us/consumer-support/dispute-detection-allowlisting.html> |
| Trend Micro (`TROJ_GEN.R002H09JC26`) | <https://www.trendmicro.com/en_us/about/legal/detection-reevaluation.html> |
| Emsisoft (`Gen:Variant.MSILHeracles.270602`) | `fp@emsisoft.com` (Betreff: „False Positive“) |
| GData (`Gen:Variant.MSILHeracles.270602`) | <https://www.gdatasoftware.com/securitylabs> |
| VIPRE (`Gen:Variant.MSILHeracles.270602`) | <https://www.vipre.com/support/submit-false-positive/> |
| SentinelOne (`Static AI - Suspicious PE`) | `report@sentinelone.com` |
| SecureAge (`Malicious`) | <https://www.secureage.com/support/report-false-positive> |
| AhnLab-V3 (`Trojan/Win.Generic.C5790344`) | `v3sos@ahnlab.com` |
| ALYac (`Gen:Variant.MSILHeracles.270602`) | <https://en.estsecurity.com/support/report> |
| eScan (`Gen:Variant.MSILHeracles.270602`) | `fp@escanav.com` |
| Rising (`Downloader.Agent!8.B23`) | <http://mailcenter.rising.com.cn/filecheck_en/> |
| Alle übrigen | VirusTotal-Sammelliste: <https://docs.virustotal.com/docs/false-positive-contacts> |

**Textvorlage zum Kopieren** (Englisch, für jedes Formular/Fax-Formular
geeignet; Version, Größe und SHA-256 stehen in `next-update/release/latest.json`,
der VirusTotal-Link auf der VirusTotal-Seite der Datei):

```text
False positive report - legitimate open-source hobby project (Arena Roblox Bridge)

File name:    ArenaRobloxBridge.exe
Version:      <Version, z. B. 8.0.0>
Size (bytes): <sizeBytes>
SHA-256:      <sha256>
Download:     https://arena-rblx-bridge.netlify.app/
Source code:  https://github.com/merta-studios/arenarobloxbridge
VirusTotal:   <VirusTotal-Link der Datei>

Detection:    <Name der Erkennung, z. B. Trojan:Win32/Wacatac.B!ml>

The file is a Windows desktop program (Roblox Studio companion tool) written in
PowerShell and compiled to a single EXE with the open-source PS2EXE tool
(https://github.com/MScholtes/PS2EXE). PS2EXE embeds the script as a resource in
the executable; this build pattern is known to produce false positives across
several engines, and Microsoft's own ML heuristic (the "!ml" suffix) is a
machine-learning hit, not the signature of a known malware family.

The program contains no downloader/persistence payload beyond its documented
feature set: it connects to a local Roblox Studio plugin via localhost, stores
user settings under %LOCALAPPDATA%\ArenaRobloxBridge, and (optionally, on user
request) registers itself in the current user's autostart. The complete source
code is public in the repository above and can be rebuilt with
next-update\Build-EXE.bat.

Please re-evaluate the file. The build is unchanged except for the version
number / embedded assets. Thank you.
```

### 2. Die EXE signieren (die stärkste technische Maßnahme)

Eine gültige Authenticode-Signatur ist der Unterschied zwischen „unbekanntes
Programm“ und „Programm mit Herausgeber“. SmartScreen zeigt dann keinen
Warnbalken mehr, und ein großer Teil der ML-Erkennungen entfällt. Der Builder
kann das seit 8.0.0 direkt:

```powershell
# Einmalig das Zertifikat für den Build-Benutzer hinterlegen:
setx ARENABRIDGE_SIGN_PFX "C:\ArenaBridge-Signatur\zertifikat.pfx"
setx ARENABRIDGE_SIGN_PFX_PASSWORD "passwort-des-pfx"     # nur wenn das .pfx eins hat
# Danach wie gewohnt: Build-EXE.bat - die EXE wird automatisch signiert.
```

Alternativ direkt mit Parametern:

```powershell
powershell -ExecutionPolicy Bypass -File builder\Build-EXE.ps1 `
  -SignCertificatePath "C:\ArenaBridge-Signatur\zertifikat.pfx" `
  -SignCertificatePassword "..." `
  -SignTimestampUrl "http://timestamp.digicert.com"
```

- `-SignCertificateThumbprint <40 Hex-Zeichen>` ist der Weg für Zertifikate, die
  schon in `Cert:\CurrentUser\My` liegen (EV-Zertifikate auf Token/HSM).
- Ohne Internet ist der Zeitstempel-Server nicht erreichbar: dann
  `-SignTimestampUrl ''` setzen (die Signatur bleibt gültig, erlischt aber mit
  dem Zertifikat).
- **Der Bau bricht ab**, wenn die Signatur nicht gültig ist — es wird nie
  versehentlich eine „halb signierte“ EXE veröffentlicht.
- `release-metadata.json` notiert danach `signedWithAuthenticode`, `signerSubject`
  und `signerThumbprint`.

Bezugsquellen (Preise Stand 2026, nur zur Orientierung):

| Weg | Wirkung / Hinweis |
| --- | --- |
| **Azure Trusted Signing** (Microsoft) | günstig, monatlich; Signatur ist sofort vertrauenswürdig für Windows |
| **OV-Zertifikat** (Sectigo, DigiCert, GlobalSign …) | gültige Signatur, SmartScreen-Reputation wächst mit der Zeit |
| **EV-Zertifikat** | sofortige SmartScreen-Reputation, teurer, oft Token/HSM nötig |
| Selbst erstelltes Zertifikat | **bringt nichts** gegen Fehlalarme (nicht öffentlich vertrauenswürdig) |

### 3. Immer dieselbe Identität veröffentlichen

Der Builder setzt seit 8.0.0 alle Dateiangaben
(Titel, Produkt, Firma, Beschreibung, Version, Copyright, Warenzeichen) und
immer denselben Download-Pfad. Reputation entsteht nur, wenn Scanner über
mehrere Versionen dieselbe „Identität“ sehen.

## Was NICHT hilft (und deshalb nicht gemacht wird)

- **Obfuskation, Packer, Base64-Umwege:** macht die Lage *schlechter*, weil genau
  diese Techniken echte Schadsoftware tarnt.
- **Künstlich veränderte Dateien** (Dummy-Strings, Größen-Padding): ändert
  höchstens den Hash, nicht die Heuristik — und wirkt selbst wie Tarnung.
- **Icons/Titel ändern:** kosmetisch, keine Wirkung.
- **„Kauf dir einen Key“-Kram oder Defender-Ausnahmen beim Endnutzer:** Ausnahmen
  muss jeder Nutzer lokal setzen; im Programm darf es keine geben.

## Grenzen dieser Offline-Prüfung

Ob ein gemeldeter Treffer verschwindet, lässt sich **nur außerhalb dieses
Repositorys** feststellen (VirusTotal-Ergebnis eines neuen Builds). Die
Windows-Schritte — ps2exe-Bau, Signatur, SmartScreen — bleiben ein Windows-Test.
