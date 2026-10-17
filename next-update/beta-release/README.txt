beta-release/ ist der Ausgabeordner fuer den automatischen RELEASE-KANDIDATEN.

Was hier liegt:
- ArenaRobloxBridge.exe - vom GitHub-Actions-Workflow "Exe Builder
  (Release-Kandidat)" gebaut, sobald sich app/ oder builder/ auf main aendert.
- Der Kandidat traegt EXAKT die Version aus app/version.json (z. B. 8.0.5,
  kein "-beta.1") und dieselbe Dateiversion (8.0.5.0). Er ist damit 1:1 die
  spaetere Release-Datei.

So wird daraus die oeffentliche Version:
- Datei herunterladen und auf dem eigenen PC testen.
- Danach genau diese Datei nach next-update/release/ kopieren (ersetzen) und
  auf main speichern. Alternativ den Workflow "Release freigeben
  (Kandidat -> release)" starten; er prueft den Kandidaten und uebernimmt ihn.
- publish-bridge.yml erzeugt daraus latest.json; alle Bridges bieten dann das
  Update an.

Wichtig:
- Dieser Ordner veroeffentlicht NICHTS von selbst. release/ und latest.json
  bleiben unveraendert, bis der Kandidat bewusst uebernommen wird.
- Ein alter Kandidat kann nicht versehentlich veroeffentlicht werden:
  publish_latest.py vergleicht die Dateiversion der EXE mit app/version.json
  und bricht bei Abweichung ab.
