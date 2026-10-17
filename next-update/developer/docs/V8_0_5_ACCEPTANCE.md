# 8.0.5 – Implementierung und Abnahme

**Stand: 2026-10-17. Quellstand vorbereitet, nicht veröffentlicht.** Änderungen ausschließlich unter `next-update/`. Der alte Root-Bridge-Code, die veröffentlichte EXE und `release/latest.json` bleiben unverändert.

## Umgesetzter Umfang

- **Terrain-Werkzeuge (8):** `terrain_heightmap`, `terrain_sculpt`, `terrain_paint`, `terrain_water`, `terrain_feature`, `terrain_carve`, `terrain_measure` und `terrain_clear`. Die Bridge rechnet Höhen, Materialschichten und Wasser selbst; das Plugin schreibt nur noch Voxel. Presets: `plains`, `hills`, `mountains`, `islands`, `archipelago`, `dunes`, `canyon`, `plateau`, `swamp`, `volcano`, `custom`. `terrain_feature` kennt 13 Formen: Berg, Grat, Hügel, Insel, Archipel, Düne, Canyon, Plateau, Krater, Vulkan, Klippe, Tal und Terrasse.
- **Grenzen und Messen:** `ReadVoxels`/`WriteVoxels` höchstens 4.194.304 Voxel, `FillRegion` höchstens 67.108.864 Voxel, Höhenkarten höchstens 20.000 Rasterzellen (Anforderung wird auf 512 × 508 Studs geklemmt), 4-Stud-Voxel über `ExpandToGrid(4)`. Große Karten laufen in Chunks mit `resumeToken{chunk,total}` und `maxChunks`; derselbe Seed ergibt dieselbe Welt. `terrain_measure` misst Höhen, Profile, Wasserstand (LiquidOccupancy) und Volumen, statt nach dem Bau zu raten.
- **Zerstörendes Verhalten:** `terrain_clear` verlangt ausdrücklich `confirm=true` und meldet vorher Fläche und Voxelzahl. Jeder Schreibvorgang läuft in genau einem `ChangeHistoryService`-Schritt; `undo` stellt das vorherige Gelände wieder her.
- **Kamera (4 Werkzeuge + Selbstheilung):** `camera_state` meldet Zustand samt `stuck=true`, `camera_reset` stellt im Edit-Modus `CameraType.Fixed` und im Play-Modus `Custom` wieder her, `camera_focus` rahmt ein Objekt ein und lässt die Kamera bedienbar, `camera_guard` prüft/installiert ein Reparaturskript in `StarterPlayerScripts` und scannt bis zu 400 Skripte nach `CameraType.Scriptable`, `MouseBehavior.Lock` und `MouseIconEnabled=false`. Zusätzlich heilt die Bridge nach **jedem** `handleCommand` (`CAMERA.afterCommand`) sowie bei `sim_stop`/`plugin_unloading`; ein festsitzender Skript-Zustand wird als Fehler gemeldet, nicht als Studio-Eigenheit entschuldigt.
- **GUI-Design 3.0:** Kontur, Glanz und Dekor sind echte Engine-Schichten (`UI_ENGINE.outlineLayer`, `glossLayer`, `decorLayer`) mit den Attributen `ArenaOutline`, `ArenaOutlineKeyline`, `ArenaGloss`, `ArenaGlossSpecular`, `ArenaDecor` und `ArenaDecorCount`. Sieben Konturstile (comic/sticker/chunky/marker/neon/engraved/tape), Glanz auf der oberen Hälfte, Dekor (Wolken, Funken, Konfetti, Blasen, Striche, Strahlen) mit Budget 24 Teile pro Fläche. Zeichenreihenfolge: Dekor 3, Inhalt 4.
- **40 Stile, 18 Widgets:** 16 neue Stile (pop, cloud, gel, neon, gold, inkwash, blueprint, pirate, medieval, scifi, sports, gothic, tropical, desert, dreamcore, toybox) ergänzen die bisherigen 24; alle Klassiker bleiben unverändert. `ui_widget` baut 18 fertige Gerüste (shop, inventory, battlepass, quests, settings, leaderboard, profile, dailyrewards, gacha, currency, hud, dialog, tooltip, hotbar, map, codex, tiers, social) über `UI_ENGINE.ensureScreen/buildNode/newContext`; `build_interface`/`build_surface` melden Kontur-, Glanz- und Dekorwerte, `ui_audit` prüft das Dekor-Budget (`decorOveruse`).
- **Desktop-Verknüpfung mit Selbstheilung:** Die EXE legt beim Start `Desktop\Arena Roblox Bridge.lnk` an und biegt eine vorhandene Verknüpfung nach jedem Update auf die neue EXE um. Eine gelöschte Verknüpfung ist beim nächsten Start wieder da. Angefasst werden ausschließlich Ziele, die `ArenaRobloxBridge*.exe` oder `ArenaBridge*.exe` heißen; fremde Programme und systemweite Einträge bleiben unberührt. Im Skriptmodus (nicht EXE) passiert nichts. Der Schritt läuft vor `Install-RobloxPlugin` in `Start-BridgeRuntime`.
- **Kataloge:** Tool-Dokumentation, Aktivitätslabels und ausführliche Aktivitätstexte enthalten jeweils **159** Werkzeuge (vorher 146). Der Sprachkatalog hat **947** Einträge (vorher 920) und ist mit dem eingebetteten Ein-Datei-Stand synchron. Die 8.0.5-Notiz steht als Stichpunktliste in `version.json` (44 Einträge) und in der Historie.
- **8.0.3/8.0.1 bleiben erhalten:** fenstergebundene Screenshots, Place-Zuordnung, Gruppen-Uploads, normale Parts, Sprachumschaltung und das Pflicht-Update-Verhalten sind unverändert.

## Hier ausführbare Prüfungen

Vom Ordner `next-update`:

```text
python -m pip install -r developer/tests/requirements-test.txt
python developer/tools/sync_ui_translations.py --check
python developer/tests/run_offline_tests.py
```

Zusätzlich gezielt:

```text
python -m unittest developer.tests.test_v805_bridge developer.tests.test_v805_parts
```

Die Part-Tests führen den tatsächlichen eingebetteten Lua-Terrain- und UI-Builder mit Roblox-Testdoubles aus (Rasterreihenfolge, Presets, Wasser, Materialschichten, Konturen/Glanz/Dekor, Widget-Aufbau). Zusätzlich wird das gesamte Plugin ohne Ausführung kompiliert. Das prüft Rechenwege, Grenzen, Fortsetzungstokens und Fehlercodes — es ist **kein Beweis für echte Roblox-Terrain-Optik oder -Performance**. Die Bridge-Tests prüfen Version, Notizen, Tool-Kataloge, Registrierungen, Skin-/Widget-Verträge, Kamera-Hooks und die Verknüpfung. Die übrigen Offline-Tests prüfen Quellen, Verträge, Katalogdeckung, XAML-Struktur, Lua und die bekannten PowerShell-Strukturfallen. Ein Tree-sitter-Check ersetzt nicht den nativen PowerShell-5.1-Parser.

## Validierungsprotokoll dieses Quellstands (Linux, 2026-10-17)

- Gesamte Offline-Suite: **30/30 Python-Testskripte erfolgreich**, Exitcode 0.
- Neue 8.0.5-Prüfungen: **28 Bridge-Vertragstests** und **12 Terrain-/UI-Lua-Tests** erfolgreich (40 Tests, in der Gesamtsuite enthalten).
- Vollständiges eingebettetes Lua-Plugin kompiliert (14.354 Zeilen); Katalog synchron mit dem eingebetteten Ein-Datei-Stand.
- Die Suite meldet selbst ausdrücklich, dass kein `powershell.exe`/`pwsh` verfügbar ist. Ihr grüner Exitcode ist **kein** nativer PowerShell-, WPF-, EXE- oder Live-Roblox-Nachweis. Der unten genannte PS-5.1-Funktionstest wurde nicht ausgeführt.

## Vor Build/Freigabe zwingend auf Windows

Vom Ordner `next-update` in **Windows PowerShell 5.1**:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File builder\parse-gate.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File developer\tests\test_v803_runtime.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File developer\tests\test_v805_runtime.ps1
```

`test_v805_runtime.ps1` lädt nur einzelne Funktions-ASTs und verwendet einen Wegwerf-Ordner unter `%TEMP%`; er legt keine echte Desktop-Verknüpfung an. Er prüft die Werkzeugkataloge, die 40 Stile, die Widget-Bibliothek sowie Anlegen, Erhalten, Wiederherstellen und die Fremdprogramm-Sperre der Verknüpfung. Er ist in der Linux-Umgebung **nicht ausgeführt** worden. Danach den normalen privaten EXE-Build/Smoke-Test nach `RELEASE-ABLAUF.md` durchführen; nicht als Veröffentlichung behandeln.

### Manuelle Windows-/Studio-Matrix (noch offen)

- [ ] Höhenkarte in einem leeren Place bauen: Höhen, Materialschichten, Wasser und Ränder passen zur Anforderung. Derselbe Seed ergibt dasselbe Ergebnis. `undo` stellt das vorherige Gelände in einem Schritt wieder her.
- [ ] Große Karte (über `maxChunks` hinaus) mit `resumeToken` fortsetzen: keine Lücken, keine doppelt geschriebenen Chunks, Abbruch mitten in der Karte bleibt möglich.
- [ ] Alle 13 `terrain_feature`-Formen (Berg, Grat, Hügel, Insel, Archipel, Düne, Canyon, Plateau, Krater, Vulkan, Klippe, Tal, Terrasse) und die Presets mit echtem Roblox-Terrain visuell prüfen (Berge, Inseln, Archipel, Dünen, Canyon, Plateau, Sumpf, Vulkan). Steilheit, Schneegrenze und Felsübergänge beurteilen.
- [ ] `terrain_carve` (Tunnel, Bogen, Graben, Grube, Kugel) und `terrain_paint` auf gewachsenem Gelände prüfen; Wandfarben und Sandstrände kontrollieren.
- [ ] `terrain_clear` ohne `confirm`: klare Ablehnung mit Fläche/Voxelzahl; mit `confirm=true`: vollständig entfernt, `undo` heilt.
- [ ] `terrain_measure`: Höhen, Profil, Wasserstand und Volumen gegen manuell gesetzte Voxel prüfen; Messwerte müssen plausibel sein, nicht geraten.
- [ ] Kamera festsitzen lassen (Skript setzt `CameraType.Scriptable`): `camera_state` meldet `stuck=true`; `camera_reset` repariert sofort; `camera_guard action=scan` nennt Skriptpfad und Zeile; `install` heilt beim nächsten Play-Start.
- [ ] Nach beliebigen Befehlen (Bauen, Skript, UI) prüfen, dass die Kamera bedienbar bleibt. Ebenso nach `sim_stop` und nach dem Deaktivieren des Plugins.
- [ ] `camera_focus` auf ein Objekt: Objekt vollständig im Bild, Kamera danach weiter drehbar, kein Sprung in eine festsitzende Kamera.
- [ ] Alle 40 GUI-Stile in einer Szene prüfen: dicke Konturen, Glanz, Wolken/Funken, Lesbarkeit auf hellem Hintergrund. Klassische 24 Stile müssen unverändert aussehen.
- [ ] Alle 18 Widgets bauen und mit Maus/Touch testen. Shop, Inventar und Battle Pass besonders auf fehlende Bilder, abgeschnittene Texte und Klickflächen prüfen.
- [ ] `ui_audit` auf einer überladenen Fläche: `decorOveruse` meldet mehr als 24 Dekorteile, ohne den Bau zu blockieren.
- [ ] Desktop-Verknüpfung: erster Start legt sie an; zweiter Start lässt sie unverändert; Löschen und Neustart bringt sie zurück; Update auf eine neue EXE biegt sie um.
- [ ] Fremde Verknüpfung `ArenaBridge.lnk` auf ein anderes Programm: bleibt unverändert. Skriptmodus legt nichts an. Benutzer ohne Schreibrecht auf den Desktop erhält eine Logzeile, keinen Absturz.
- [ ] Deutsches und englisches GUI durchgehen, insbesondere die neuen Tool-Dokumentationen und Aktivitätstexte; echte Umlaute prüfen.
- [ ] Pflicht-Update-Fenster (8.0.1): X beendet alles, „Später“ bleibt nach der Grenze gesperrt.

**Freigabestatus:** keine Release-EXE gebaut, keine Veröffentlichung, keine Live-Roblox-/Windows-Abnahme in dieser Umgebung. Der CI-Beta-Testbuild (`beta-release/`, Stand `8.0.5-beta.1`, Dateiversion 8.0.5.0) ist kein Release. Erst nach dieser Matrix ausdrücklich freigeben.
