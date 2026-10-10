# Neues Beta-/Stable-Update-System (vorbereitet, noch nicht aktiv)

Dieser Ordner enthält ausschließlich die vorbereitete Update-Infrastruktur:

- `channels/` — Beispielmanifeste für Beta und Stable; beide sind
  `enabled: false`, ohne Download-URL, Hash oder echtes Release-Artefakt.
- `updater/` — isolierter PowerShell-Updater mit Größen-/Hashprüfung,
  Staging, Backup und Rollback.

Der Updater ist **nicht** in `app/ArenaBridge.ps1` oder die alte Bridge im
Repository-Hauptordner integriert. `Build-EXE.bat` verwendet ihn nicht und
startet ihn nicht. Bitte hier nichts aktivieren oder manuell veröffentlichen,
bevor der Beta-Build auf Windows getestet und eine spätere Integration
separat freigegeben wurde. Die alte Update-Struktur im Repository-Hauptordner
bleibt unangetastet.

Details und Sicherheitsgrenzen: [`updater/README.md`](updater/README.md).
