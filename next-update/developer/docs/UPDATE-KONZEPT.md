# Update-Konzept (Arena Roblox Bridge, Stand 7.8.0 / Updater 2.0.0)

Dieses Dokument erklärt **das Warum** des Selbst-Update-Systems: die Regeln, die
Zustandsmaschine, die Fehlerfälle und die ehrlichen Grenzen. Die praktische
Bedienung steht in `update-system/README.md`, der Release-Ablauf in
`RELEASE-ABLAUF.md`.

## 1. Ausgangslage und der alte Fehler

Das alte System konnte technisch **nie** ein Update installieren. Beweis aus dem
Repository:

| Quelle | Version | Größe | SHA-256 |
|---|---|---|---|
| `channels/stable.json` (aktiviert) | 7.7.0 | 5.842.432 B | `19984c19…ec1690` |
| `app/version.json` | 7.7.2 | – | – |
| `release/ArenaBridge.exe` (echte Datei) | 7.7.2.0 | 5.835.776 B | `21c9800f…f63f3a5c` |

Alle drei Angaben widersprachen sich. Der Updater prüfte Größe und Hash, also
musste jeder Versuch scheitern – und zwar still: kein Hinweis, kein Protokoll,
kein Verlauf. Zusätzlich hieß das Ziel immer `release/ArenaBridge.exe`; eine
neue Veröffentlichung hätte die alte Datei überschrieben, wodurch Nutzer mit
älterem Stand eine fremde Version bekommen hätten.

Ursachen, nicht Symptome:

1. **Ein Dateiname für alle Versionen.** Damit ist weder „diese Version“ noch
   „jene Version“ eindeutig adressierbar; Hashes können beliebig veralten.
2. **Keine verbindliche Quelle der Wahrheit.** Manifest, `version.json` und die
   Datei wurden von Hand gepflegt und liefen auseinander.
3. **Keine Diagnosemöglichkeit.** Fehler wurden nur lokal geloggt.
4. **Kein Publikationswerkzeug.** Das Aktivieren eines Kanals war Handarbeit
   ohne Prüfung von Version, Artefakt, Dateikopf oder Freigabe.
5. **Kein Verlauf, kein Fortschritt, kein Abbruch.** Der Nutzer sah nicht, was
   passiert; ein Fehler blieb unsichtbar.

## 2. Grundsätze (gelten für jede Zeile des Systems)

1. **Freiwillig.** Ein Update wird nie erzwungen. `mandatory` existiert im
   Schema bewusst nicht und wird nirgends ausgewertet.
2. **Niemals Prozesse beenden.** Weder App noch Helfer beenden oder töten einen
   Prozess. Die Bridge schließt sich selbst; der Helfer **wartet** auf das
   reguläre Ende (`WaitForProcessId`/Zielerkennung mit Zeitlimit).
3. **Nichts kaputt machen.** Die alte Fassung bleibt bei jedem Fehler
   unverändert oder wird zurückgerollt. Downloads landen in `rejected\`, nie
   über die laufende EXE.
4. **Nur was geprüft ist, wird installiert.** Größe, SHA-256, PE-Kopf (x64) und
   die **eingebaute Dateiversion** müssen zum Manifest passen.
5. **Unveränderliche Artefakte.** Veröffentlichte Dateien heißen
   `ArenaBridge-<Version>.exe` und werden nie überschrieben.
6. **Ein Kanal, eine Datei, eine Wahrheit.** Das Manifest ist die einzige
   Quelle für Version, Größe und Hash; Dateiname und URL werden daraus
   abgeleitet (`ArenaBridge-<Version>.exe`, feste Repository-Basis).
7. **HTTPS-only auf feste Hosts.** `raw.githubusercontent.com` (und die
   genehmigten GitHub-Weiterleitungen `objects.githubusercontent.com`,
   `github-releases.githubusercontent.com`), feste Repository-URL, keine
   frei wählbaren Adressen, keine Zugangsdaten, keine Auto-Redirects.
8. **Ehrlich.** Es wird nur behauptet, was jemand tatsächlich gesehen hat. Der
   Linux-Teil der Werkzeuge testet Strukturen; Windows-Verhalten bestätigt
   ausschließlich der Nutzer.
9. **Umkehrbar.** `release.py disable` deaktiviert einen Kanal sofort;
   `prune` entfernt alte Artefakte, aber nie die letzte veröffentlichte Datei.
10. **Geschützt.** `update-system/`, der App-Block, der Builder und die
    v800-Tests sind per SHA-256 im Guard-Lock festgehalten. Änderungen brauchen
    eine dokumentierte Nutzerfreigabe und ein Rebaseline.

## 3. Bestandteile und Verantwortlichkeiten

| Teil | Verantwortung | Darf nichts anderes |
|---|---|---|
| `app/ArenaBridge.ps1` (Block `ARENA-UPDATE-INTEGRATION`) | Prüfung anstoßen, Hinweisfenster, Bedienung, Fortschritt anzeigen, sich selbst beenden | keine Downloads, keine Kanal-Dateien kennen, keine Prozesse beenden |
| `update-system/updater/Update-Bridge.ps1` | Manifest laden/prüfen, Download, Installationsablauf, Status/Fortschritt/Verlauf, Rollback | keine Kanal-Aktivierung, keine Freigabe, keine Quelle ändern |
| `update-system/channels/*.json` | Zustand je Kanal (aktiviert/deaktiviert + Koordinaten) | nie von Hand im Änderungs-PR ändern |
| `developer/tools/release.py` | Prüfen und Veröffentlichen (`status`, `check`, `stage`, `disable`, `prune`), README-Stempel, Guard-Rebaseline | nichts herunterladen, nichts ohne `--tested-by-user` schreiben |
| `tools/ArenaBridge-Update-Holen.cmd/.ps1` | Einmalige Migration uralter Installationen ohne Updater | nichts löschen, nichts ohne SHA-256-Prüfung starten |
| `developer/tests/*` | Offline-Gates (Struktur, Schema, Schutz) und Windows-Rauchtest | keine echten Veröffentlichungen |

## 4. Der Datenvertrag (Manifest, Schema 2)

```json
{
  "schemaVersion": 2,
  "channel": "stable",
  "enabled": true,
  "testFixture": false,
  "sequence": 2,
  "version": "7.8.0",
  "publishedAtUtc": "2026-10-11T06:30:00Z",
  "minimumUpdaterVersion": "2.0.0",
  "artifact": {
    "fileName": "ArenaBridge-7.8.0.exe",
    "url": "https://raw.githubusercontent.com/merta-studios/arenarobloxbridge/main/next-update/release/ArenaBridge-7.8.0.exe",
    "sha256": "…64 hex…",
    "sizeBytes": 5835776
  },
  "notes": ["…"]
}
```

Regeln, die erzwungen werden (Schema **und** Laufzeit):

- `additionalProperties: false` – unbekannte Felder sind Fehler, kein „wird
  schon ignoriert“.
- Deaktiviert heißt leer: `version`, `publishedAtUtc` leer, `fileName`
  `ArenaBridge.exe`, `url`/`sha256` leer, `sizeBytes` 0. So kann ein
  deaktivierter Kanal unmöglich etwas ausliefern.
- `sequence` ≥ 1 und nie kleiner als der lokale Stand (`update-state.json`).
  Das ist der Schutz gegen einen veralteten Cache-Stand von
  `raw.githubusercontent.com`.
- `version` muss dreiteilig sein (optional `-vorab.n`); `stable` verbietet
  Vorabversionen.
- `minimumUpdaterVersion` darf nicht neuer sein als der eingebettete Updater.
- `testFixture: true` ist in Repository-Dateien verboten; nur der
  Testbau (`-TestFixtureBuild`, Umgebungsvariable) erreicht einen
  lokalen Test-Manifestpfad.
- `notes`: 1–8 Einträge, je ≤ 800 Zeichen (der Builder zerlegt sie).

## 5. Die Zustandsmaschine eines Updates

```
   Start
     │  Kanal aktiviert und Build gültig?
     ├─(nein)────────────────────────────────────────► Ruhe (kein Hinweis)
     │
     ├─ Check (eigener Prozess, blockiert nichts, 150 s Limit)
     │     ├─ disabled / up-to-date / manifest-stale → Ruhe
     │     ├─ Ziel fehlt → Hinweis „Installation prüfen“ (Diagnose)
     │     └─ update-available → Hinweisfenster
     │
     ├─ Nutzer: „Später“ → Merker, beim nächsten Start erneut (max. 1× pro Tag)
     ├─ Nutzer: „Diese Version überspringen“ → dauerhaft in
     │                                        update-preferences.json
     └─ Nutzer: „Jetzt aktualisieren“
           │
           ├─ Install (Hintergrundprozess; Bridge bleibt offen)
           │     1. Manifest frisch laden (Cache-Brecher)
           │     2. Download nach .arena-update\staging
           │     3. Prüfen: Größe, SHA-256, x64-Kopf, Dateiversion
           │     4. Fortschritt schreiben; Abbruchdatei beachten
           │     5. Bridge schließt sich selbst
           │     6. Auf reguläres Ende warten (nie beenden)
           │     7. Atomar ersetzen + Backup (3 behalten)
           │     8. update-state/-status/-history schreiben
           │     9. Neue Fassung startet mit „Update erfolgreich“
           │
           ├─ Fehler vor Schritt 7 → alte Fassung unverändert, Datei in rejected\
           └─ Fehler nach Schritt 7 → Rollback aus dem Backup
```

Statuswerte des Checks: `disabled`, `up-to-date`, `update-available`,
`downgrade-refused`, `version-conflict`, `manifest-stale`, `target-missing`,
`error`. Fortschrittsphasen: `downloading`, `ready-to-install`,
`waiting-for-exit`, `installing`, `restarting`, `done`, `nothing`, `cancelled`,
`error`.

## 6. Fehlerfälle und Antworten

| Fall | Antwort |
|---|---|
| Manifest nicht lesbar / CDN liefert alten Stand | `manifest-stale` bzw. Fehler; nichts ändern, beim nächsten Start erneut versuchen |
| Hash/Datei passt nicht (halb hochgeladene Datei, falsche Version) | Abbruch, Datei nach `rejected\`, Status mit Klartext |
| Dateiversion im Artefakt passt nicht zum Manifest | **neu in 2.0.0:** Abbruch vor dem Ersetzen |
| Nutzer hat schon eine neuere Version | `downgrade-refused` |
| Gleiche Version, andere Datei | `version-conflict` (nie ein zweites Mal mit anderem Inhalt) |
| Netzwerk weg | Fehler protokollieren, nichts ändern |
| Bridge läuft noch | nur warten; nach Zeitlimit Abbruch |
| Nutzer will abbrechen | `cancel.request`, Aufräumen, nichts ändern |
| Ersetzen klappt, Start scheitert | Rollback aus dem Backup, alter Stand läuft mit „Update fehlgeschlagen“ |
| Testbau | `-TestFixtureBuild`: eigene Version, Schreiben nur außerhalb des Repos |

## 7. Selbstheilung und Prüfketten

- **Doppelt geprüft:** Der Release-Kanal wird vom Guard-Lock (zweite
  Implementierung in `test_v800_update_system_guard.py`) und von
  `test_v800_update_manifest.py` unabhängig geprüft.
- **Cache-Versatz:** Cache-Brecher beim Manifest, einmaliger Neuversuch nach
  Hash-Konflikt, `sequence`-Regel gegen den alten Stand.
- **Freigabe-Nachweis:** Ein aktivierter Kanal braucht eine Freigabezeile im
  Guard-Lock mit dem Datum von `publishedAtUtc`; `release.py stage` schreibt sie
  zusammen mit dem Rebaseline.
- **Diagnose ohne Kanaldateien:** `release.py status`, `check`, der
  Doctor-Modus des Updaters und die drei Knöpfe im Einstellungsfenster
  (Suchen, Diagnose, Protokoll) sind reine Leser.

## 8. Was in der Linux-Umgebung geprüft werden kann – und was nicht

Prüfbar offline: Verträge (Schema/Fixtures), Schutz-Hashes, Struktur der App,
Ableitungsregeln, Werkzeugverhalten, XAML-Wohlgeformtheit.

**Nicht** prüfbar offline: echtes WPF-Verhalten, PowerShell-Ausführung,
Dateiversions-Header echter Builds, Windows-Dateisperren. Deshalb gilt: Kein
Dokument und kein Test behauptet Windows-Ergebnisse, die der Nutzer nicht
berichtet hat. `release.py stage` verlangt genau diese Bestätigung
(`--tested-by-user`, `--smoke-test-passed|--smoke-test-skipped`).

## 9. Warum das Fenster (WPF) jetzt so gebaut ist

Der erste Versuch lieferte eine abstürzende Oberfläche: Der XAML-Block verwies
mit `StaticResource` auf Fensterressourcen, die es in diesem Fenster nicht gab
(Parserfehler beim Start → Fenster sofort zu). Regeln daraus:

- Der Update-Block nutzt **ausschließlich** Ressourcen, die er selbst definiert
  (oder gar keine) – geprüft von `test_v800_update_window.py` und vom Guard.
- Jeder Fensterbau liegt in einem `try/catch`; scheitert das Fenster, erscheint
  ein `MessageBox`-Hinweis (kein stiller Ausfall).
- Die Oberfläche bleibt simpel: Text, Fortschrittsbalken, vier Knöpfe,
  Protokollpfad. Keine Vorlagen, keine Bilder, keine Icons.

## 10. Bedienung in einem Satz je Rolle

- **Nutzer:** Nichts tun müssen. Beim Start erscheint höchstens ein Fenster mit
  „Jetzt aktualisieren“, „Später“ oder „Diese Version überspringen“.
- **Owner/Release:** `Build-EXE.bat` → privat testen → `release.py check` →
  `release.py stage …` → Merge.
- **Änderungs-Session:** nur `next-update/` bearbeiten, Kanal-Dateien **nie**
  anfassen; am Ende nur den kopierbaren Release-Session-Prompt ausgeben (siehe
  `RELEASE-SESSION-PROMPT.md`).
