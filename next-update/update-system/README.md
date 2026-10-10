# Neues Update-System — Veröffentlichung nur nach Testfreigabe

Dieser Ordner ist die **einzige** Update-/Verteilungsstrecke für `next-update`.
Die alte Update-Struktur im Repository-Hauptordner wird nicht verwendet und
bleibt unverändert.

## Jetztiger Zustand

- `channels/stable.json` und `channels/beta.json` stehen auf
  `enabled: false`. Beide enthalten absichtlich keine Artefakt-URL, Größe oder
  SHA-256. Code-Merges und lokale Builds lösen deshalb keine geplanten Updates
  über dieses System aus.
- `updater/Update-Bridge.ps1` ist derzeit ein eigenständiger PowerShell-Updater.
  Er prüft GitHub-HTTPS-Host, Größenlimit, Versionsnummer und SHA-256 und tauscht
  die EXE mit Backup/Rollback aus. **Er ist aktuell noch nicht in die
  ArenaBridge-EXE integriert.** Das ist eine harte Sperre: erst Integration,
  tatsächlicher Startpfad und Bootstrap bestehender Installationen prüfen und
  testen, dann darf Stable aktiviert werden.
- Private PR-/ZIP-/Build-/Test-Zyklen verwenden keinen öffentlichen Beta-Kanal.
  `beta.json` bleibt ausgeschaltet; die lokale EXE liegt direkt in
  `../release/ArenaBridge.exe`, nicht in einem Kanal-Unterordner.

## Freigabe an alle Nutzer

Nach dem privaten Test und der ausdrücklichen Freigabe durch den Nutzer gilt:

1. Die **identische, getestete** `ArenaBridge.exe` kommt an den einen
   Repository-Pfad `next-update/release/ArenaBridge.exe`. Diagnose-EXE,
   Diagnose-BAT, Prüfsummen und lokale Build-Metadaten kommen nicht mit.
2. Die Release-Session verifiziert Versionsnummer, Dateigröße und SHA-256 der
   vorhandenen Datei; sie baut nicht stillschweigend eine andere EXE.
3. Vor der Aktivierung muss sie den neuen Updater in die gebaute Anwendung
   integrieren und durch echte Tests absichern. Zusätzlich muss klar sein,
   wie bereits installierte Benutzer auf die neue Updater-fähige EXE kommen.
   Wenn dafür ein einmaliger Bootstrap nötig ist, darf die Session keine
   vollautomatische Auslieferung versprechen, bevor dieser Weg geklärt ist.
4. Erst dann wird `channels/stable.json` für die endgültige Version mit
   tatsächlichem Veröffentlichungszeitpunkt, stabiler Version und geprüftem
   Artefakt befüllt. Die URL zeigt auf die öffentliche Datei im Repository,
   beispielsweise `https://raw.githubusercontent.com/merta-studios/arenarobloxbridge/main/next-update/release/ArenaBridge.exe`.
   Die SHA-256 und `sizeBytes` müssen exakt zur hochgeladenen Datei passen.
5. Änderungen an Quelle/Manifest werden als PR vorbereitet und erst nach dem
   Merge öffentlich wirksam. Stable niemals während des privaten Tests
   aktivieren. Es gibt keinen separaten `release-inbox/`- oder
   `user-builds/`-Kanalordner.

Die neue Session muss das **neue** `update-system/` prüfen und verwenden; sie
muss die alte Root-Update-Struktur ignorieren. Sicherheitsgrenzen und
Parameter: [`updater/README.md`](updater/README.md).
