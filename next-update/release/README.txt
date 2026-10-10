ARENA ROBLOX BRIDGE — EINZIGER BUILD-/RELEASE-ORDNER
====================================================

Build-EXE.bat legt die zu testende EXE hier ab:

    release\ArenaBridge.exe

Das ist der einzige normale Programm-Build und spaeter genau der einzige
EXE-Pfad, der nach ausdruecklicher Freigabe ins Repository uebernommen wird.
Es gibt keine beta/stable-Unterordner und keinen zusaetzlichen
release-inbox-Ordner.

Waehrend PR-Pruefung und privatem Test bleibt ArenaBridge.exe lokal. Ein Merge
oder ein lokaler Build aktualisiert KEINE Nutzer. Wenn der Test fehlschlaegt
oder nicht gefaellt, die Datei nicht hochladen; stattdessen im neuen Chat einen
Korrektur-PR anfordern und den Build nach dem Merge neu testen.

Erst nach ausdruecklicher Release-Freigabe wird genau die bereits getestete
ArenaBridge.exe an diesem Pfad in das Repository hochgeladen. Die neue
update-system-Freigabe (stable-Manifest, SHA-256 und Installationspfad) erfolgt
separat und erst nach Pruefung/Integration des neuen Updaters. Die Dateien
ArenaBridge-Diagnose.exe, Start-Diagnostic.bat, SHA256-Dateien,
release-metadata.json und temporaere Build-Dateien sind lokale Hilfsdateien;
nicht hochladen.
