beta-release/ ist der Ausgabeordner fuer Test- und Beta-Builds der Arena Roblox Bridge.

- Hier legt der automatische GitHub Actions Workflow (und der lokale Test-Build mit Ziel beta-release)
  die neu gebaute ArenaRobloxBridge.exe ab.
- Du kannst die Datei hier herunterladen und auf deinem PC testen.
- Wenn alles einwandfrei laeuft, kopierst du diese ArenaRobloxBridge.exe in den Ordner next-update/release/
  (oder ersetzt die release/ArenaRobloxBridge.exe) und uebertraegst sie auf main.
- Der bestehende Workflow publish-bridge.yml kuemmert sich dann wie gewohnt um das Erstellen von latest.json
  und das Ausrollen des Updates an alle Nutzer.
