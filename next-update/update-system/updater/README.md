# Neuer Updater — eigenständig, Integration noch offen

`Update-Bridge.ps1` ist der neue, geplante Updater für `next-update/`. Er ist
**noch nicht in `app/ArenaBridge.ps1` oder in `release/ArenaBridge.exe`
eingebunden** und wird weder beim normalen Build noch beim Start aufgerufen.
Alle Channel-Manifeste sind deaktiviert. Deshalb darf diese Datei nicht als
Beleg für bereits funktionierende automatische Nutzer-Updates gelten.

## Sicherheitsverhalten

- Windows-only; Kanal muss explizit `beta` oder `stable` sein.
- Manifest und Artefakt müssen über genehmigte HTTPS-GitHub-Hosts geladen
  werden. Credentials, fremde Ports und nicht genehmigte Redirects werden
  abgelehnt.
- Größe, Versionsformat, Kanal, Mindest-Updater-Version und SHA-256 werden
  geprüft. Deaktivierte Manifeste laden kein Artefakt.
- Lokaler Update-Status wird validiert. Downgrades und ein ungültiger Status
  führen zu einem Abbruch statt einer ungeprüften Neuinstallation.
- Die laufende EXE wird niemals beendet. Der Updater wartet; danach lädt und
  prüft er im Staging-Ordner, ersetzt atomar mit Backup/Rollback und kann die
  aktualisierte EXE starten.

## Voraussetzungen vor einer Veröffentlichung

Eine separate Release-Session muss vor dem Aktivieren von Stable:

1. den Updater sicher in den echten Startpfad der neuen EXE integrieren;
2. den Installationsordner, Zustandsdatei, Kanalwahl, Ausfall-/Offline-Verhalten,
   Start nach erfolgreichem und erfolglosem Check sowie Mehrfachstarts testen;
3. den Bootstrap-Weg für bereits installierte Nutzer nachweisen. Falls diese
   Installationen den neuen Updater nicht enthalten, erst eine sichere
   Migration/Erstinstallation klären — nicht auf das alte Root-System
   zurückfallen und nicht behaupten, ein Update sei automatisch angekommen;
4. nur nach ausdrücklicher Nutzerfreigabe das geprüfte Artefakt
   `next-update/release/ArenaBridge.exe` mit exakter Versionsnummer, Dateigröße
   und SHA-256 im Stable-Manifest veröffentlichen.

Für die endgültige Datei ist der Repository-Pfad `next-update/release/ArenaBridge.exe`
vorgesehen. Ein Manifest kann nach Upload zum Beispiel auf die öffentliche
Raw-Datei zeigen:

```text
https://raw.githubusercontent.com/merta-studios/arenarobloxbridge/main/next-update/release/ArenaBridge.exe
```

Der Hash und `sizeBytes` dürfen nicht geschätzt oder aus einer anderen EXE
übernommen werden. Sie müssen mit der tatsächlich hochgeladenen, getesteten
Datei übereinstimmen. Diagnose-EXE/BAT und lokale Metadaten sind kein Update-
Artefakt. Die Manifeste liegen unter `../channels/` und bleiben bis zur
abgeschlossenen Integration, Tests und Freigabe `enabled: false`.
