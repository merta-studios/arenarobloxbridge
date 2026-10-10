# Mini-Update: Polygon Engine 2.0 – kanonische WedgePart-Achsenregel als
# dauerhafte KI-System-Regel

Kein Architekturwechsel, kein neues Tool, keine Verhaltensänderung an
`build_polygon_model`. Dieses Update macht die korrekte `WedgePart`-Achsen-
konvention zu einer **fest in jeder Session verankerten AI-Regel** statt sie
nur einmalig im Changelog zu erwähnen.

> **Ausgeliefert als Version 6.1.4.**

## Warum dieses Update?

`build_polygon_model` triangulierte Dreiecke bereits seit Version 6.1.3
korrekt (siehe `POLYGON_BUILDER_FIX.md`: der Punktreihenfolge-Bug in
`MASTER_BUILD.triangleWedges` und die "negative Null" in `pointKey` sind seit
6.1.3 behoben). Das Problem, das dieses Update adressiert, liegt woanders:

Eine neue KI-Session hat kein Gedächtnis an frühere Sessions. Solange die
korrekte `WedgePart`-Achsenkonvention nirgends als **verbindliche, bei jedem
Sessionstart automatisch ausgelieferte Regel** dokumentiert war, konnte Arena
in einer neuen Session – sobald sie bewusst eigenen Lua-Code für Polygone/
Wedges schreibt (z. B. über `run_lua` für einen Spezialfall, den
`build_polygon_model` nicht abdeckt) – versehentlich die falsche lokale Achse
für Dicke, Höhe oder Basiskante verwenden. Genau das erzeugt die gemeldeten
90°-Drehfehler und klaffenden Nahtstellen bei prozeduralen Low-Poly-
Geometrien, Terrains und Modellen – unabhängig davon, ob der eingebaute
Builder selbst fehlerfrei ist.

## Die unverletzliche Regel

Bei einem `WedgePart` liegt die Schräge **niemals** in der lokalen X-Ebene:

- Lokale **X-Achse** = Dicke / Flächennormale (`normal`)
- Lokale **Y-Achse** = Höhe / Orthogonale zum Basisschenkel (`up`)
- Lokale **Z-Achse** = Basisschenkel-Richtung (`dir` bzw. `-dir`)

`CFrame.fromMatrix(position, normal, up, dir)` hält diese Zuordnung exakt
ein. Seamlose Kanten entstehen, wenn die gelieferten Dreieckspunkte als
exakte Außenhaut behandelt werden und die gesamte Keildicke per
`skinOffset = -normal * (thickness * 0.5)` nach innen verschoben wird –
dieselbe Technik, die `build_polygon_model` intern bereits als
Standardplatzierung nutzt (`thicknessPlacement`, seit 6.1.1).

## Was sich geändert hat

- `Get-BridgeGuides` liefert jetzt einen neuen Schlüssel
  `polygonEngineRules` (Titel, Geltungsbereich, Achsen-Regel, Nahtstellen-
  Regel, geprüfte Referenz-Lua-Funktion `drawSeamlessTriangle`). Dieser
  Guide erreicht **jede** neue Session automatisch über den
  Sessionstart-Payload, `get_docs` und `GET /api/docs` – ganz ohne
  Extra-Aufruf.
- `importantRules` enthält einen neuen, kurzen Hard-Constraint-Hinweis, der
  auf `polygonEngineRules` verweist und klarstellt: `build_polygon_model`
  macht das bereits richtig und bleibt erste Wahl; die Regel gilt für
  echte, handgeschriebene `run_lua`-Geometrie.
- Die `run_lua`-Tool-Beschreibung verweist zusätzlich direkt auf die Regel,
  damit sie im Moment der Werkzeugwahl sichtbar ist.
- Die Referenz-Lua-Funktion wurde vor der Übernahme geometrisch geprüft
  (korrekte volle 3-Zyklus-Punktrotation auf die längste Kante, garantierter
  Lotfußpunkt innerhalb der Basis, konsistente Normalen-Orientierung bei
  zyklischer Vertauschung, korrekter Half-Thickness-Skin-Offset) – sie ist
  mit der bereits produktiven, getesteten Technik in
  `MASTER_BUILD.triangleWedges` konsistent.
- Keine Änderung an `MASTER_BUILD.triangleWedges`, `build_polygon_model`
  selbst, dessen Parametern oder Rückgabewerten.

## Geänderte Dateien

- `ArenaBridge.ps1` – `Get-BridgeGuides` (neuer `polygonEngineRules`-Block,
  ergänzter `importantRules`-Eintrag), `run_lua`-Tooldoku (Hinweis
  ergänzt), Versionsliterale 6.1.3 → 6.1.4, neuer Changelog-Block oben in
  der Datei.
- `version.json` – Versionssprung + Notes.
- `README.md` – Versionsverlauf ergänzt.
- `test_v398_structure.py` – Versionssprung, neue Marker für
  `polygonEngineRules`/Referenzformel, aktualisierte Stale-Literal-Prüfung
  für 6.1.3 → 6.1.4.
- `GANZ WICHTIG LESEN VOR JEDER BEARBEITUNG` – Versionsstand + Kurzeintrag.
- `POLYGON_ENGINE_2_0.md` – dieses Update-Dokument.

Nicht angefasst: Asset-Suche, Playtest-System, Script-Tools, sonstige Tools,
`build_assembly`, Wedges/Teile-Architektur, API-Parameter-Namen,
`MASTER_BUILD.triangleWedges`/`pointKey`/`triangulate` (funktional
unverändert seit 6.1.3).

## Wie ich es geprüft habe

- `python3 test_v398_structure.py` (mit `pip install luaparser`) läuft
  fehlerfrei durch: parst weiterhin alle eingebetteten Lua-Quellen und
  XAML-Fenster der Datei und bestätigt zusätzlich, dass die neue
  `polygonEngineRules`-Doku und ihre Referenzformel im Quelltext vorhanden
  sind, während alle 6.1.3-Versionsliterale sauber auf 6.1.4 migriert sind
  (keine stehengebliebenen alten Literale, exakte Vorkommenszählung).
- Die Referenz-Lua-Funktion wurde von Hand gegen dieselbe Mathematik
  geprüft, die `MASTER_BUILD.triangleWedges` bereits produktiv verwendet
  (siehe oben) – keine neue Laufzeit-Lua-Ausführung nötig, da kein
  Lua-Verhalten des Builders geändert wurde, nur Text-Dokumentation.

**Empfehlung für den Test in Roblox Studio:** Nach dem Update `get_docs`
(oder den Sessionstart-Payload) einmal ansehen und prüfen, dass
`polygonEngineRules` mit der Achsen-Regel und der Referenzfunktion
erscheint. Funktional bleibt alles wie in 6.1.3 getestet (Dreieck/Viereck,
achteckiger Stamm mit `closeOpenings`, organische Formen).
