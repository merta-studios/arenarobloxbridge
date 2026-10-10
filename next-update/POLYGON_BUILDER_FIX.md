# Mini-Update: Polygon-Builder – Lücken-Fix (build_polygon_model)

Kleiner, gezielter Fix für den Wedge-basierten Polygon-Builder. Keine
Architekturänderung, keine neuen Tools, Wedges bleiben wie bisher die
Baueinheit.

> **Ausgeliefert als Version 6.1.3.** Der Code-Fix selbst kam mit PR #31 in
> `main`; veröffentlicht (und damit für den Auto-Updater der `ArenaBridge.exe`
> sichtbar) wurde er mit dem Versionssprung 6.1.2 → 6.1.3 in `version.json`
> und `ArenaBridge.ps1`. Nach dem Update Roblox Studio einmal neu starten,
> damit das neue Plugin geladen wird.

## Ursache der Lücken (reproduziert und behoben)

**Hauptursache — Punktreihenfolge-Bug in `MASTER_BUILD.triangleWedges`:**
Die Funktion sortiert die drei Dreieckspunkte so um, dass `BC` die längste
Kante ist (damit das Lot von `A` sicher innerhalb von `BC` landet). Der
bisherige Code hat bei dieser Umsortierung aber nur zwei der drei
Lua-Variablen neu zugewiesen (`c,a=b,c` bzw. `a,b=b,c`), wodurch `B` und `C`
in bestimmten Fällen versehentlich auf denselben Punkt zeigten. Das erzeugte
eine künstliche Kante der Länge 0 und ließ das Dreieck fälschlich als
"degenerate triangle" durchfallen – **rein abhängig davon, welche Kante in
der Eingabereihenfolge zufällig am längsten war**, nicht von der tatsächlichen
Geometrie. Mit einem einfachen Reproduktionstest (identisches Dreieck, nur
andere Punktreihenfolge) schlugen 2 von 3 Reihenfolgen fehl; bei einem
achteckigen Baumstamm aus 8 Seitenflächen (16 Wedges) fielen dadurch **alle
16 Wedges** aus – exakt das gemeldete Lückenproblem bei Bäumen/Stämmen.

**Zweite Ursache — „negative Null“ beim Vertex-Abgleich (`pointKey`):**
Trigonometrisch erzeugte Koordinaten (z. B. `sin(2*pi)`) landen numerisch
oft bei einer winzigen negativen Zahl statt exakt `0`. Beim Formatieren auf
5 Nachkommastellen wurde daraus `"-0.00000"` statt `"0.00000"` – zwei
unterschiedliche Schlüssel für denselben Punkt. Dadurch konnten runde
Querschnitte (Stämme, Baumkronen, Tierkörper) ihre eigene Anfangs-/End-Naht
nicht verschweißen und blieben offen.

Beide Bugs sind unabhängig von der grundsätzlichen Architektur und wurden
direkt an der Quelle repariert.

## Was sich geändert hat

1. **`triangleWedges`-Umsortierung korrekt implementiert** (alle 3 Variablen
   werden jetzt richtig rotiert), plus Toleranzen, die sich an der
   Dreiecksgröße orientieren statt an einem einzigen festen Wert.
2. **Neue Vorverarbeitung `cleanPolygonPoints`**: entfernt Beinahe-Duplikate
   und exakt kollineare Zwischenpunkte, bevor trianguliert wird – häufige
   Ursache für „No valid ear found“ bei organischen Meshes.
3. **`triangulate` mit internem Retry** (Punkt 4 der Anforderung): bei
   Fehlschlag wird zuerst mit gelockerter Tolerenz erneut versucht, danach
   mit umgekehrter Punktreihenfolge/Orientierung, und als letzte Instanz mit
   einer Fan-Triangulierung – damit eine Fläche lieber mit einer
   dokumentierten Fallback-Strategie entsteht, statt komplett zu fehlen.
4. **Neues `MASTER_BUILD.weldEntryVertices`**: verschweißt praktisch
   identische Vertices innerhalb eines Submodels auf dieselbe Instanz, bevor
   `closeOpenings`/Triangulierung laufen – lässt Nachbarflächen sauberer
   aneinanderliegen und macht die Randerkennung für `closeOpenings`
   zuverlässiger.
5. **`pointKey` normalisiert negative Null**, siehe oben.
6. **Ehrlichere, aussagekräftigere Rückgabe** von `build_polygon_model`:
   - `facesTotal` / `facesBuilt` / `facesSkipped` zeigen jetzt klar, wie
     viele Flächen erzeugt bzw. übersprungen wurden.
   - `incomplete` ist `true`, sobald mindestens eine Fläche übersprungen
     wurde – ein Build mit Lücken sieht nicht mehr wie ein voller Erfolg aus.
   - Ein lesbarer `warnings`-Text fasst das zusammen ("3 of 42 face(s) were
     skipped and are MISSING from the model – see result.skipped ...").
   - Jeder Eintrag in `skipped` (und neu `fallbackFaces`) nennt jetzt
     **Submodel-Name, Polygon-Name und Fehlergrund**.
   - Bestehende Felder (`model`, `triangles`, `wedges`, `skipped`, …) bleiben
     unverändert erhalten; es wurde nur ergänzt, nichts entfernt.

## Geänderte Dateien

- `ArenaBridge.ps1` — einziger Codeeingriff, beschränkt auf den
  `MASTER_BUILD`-Abschnitt (Triangulierung/WedgeParts) und
  `tools.build_polygon_model`:
  - `MASTER_BUILD.pointInTri2` (Toleranz-Parameter ergänzt)
  - `MASTER_BUILD.cleanPolygonPoints` (neu)
  - `MASTER_BUILD.earClip` (neu, aus `triangulate` herausgezogen)
  - `MASTER_BUILD.triangulate` (Retry-Logik, Fallbacks)
  - `MASTER_BUILD.pointKey` (negative Null normalisiert)
  - `MASTER_BUILD.weldEntryVertices` (neu)
  - `MASTER_BUILD.triangleWedges` (Reorder-Bug behoben, skalierende Toleranzen)
  - `tools.build_polygon_model` (Vertex-Welding eingebunden, Diagnose/Zähler
    erweitert)
- `POLYGON_BUILDER_FIX.md` — dieses Update-Dokument.

Nicht angefasst: Asset-Suche, Playtest-System, Script-Tools, sonstige Tools,
`build_assembly`, Wedges/Teile-Architektur, API-Parameter-Namen.

## Wie ich es getestet habe

Da im Sandbox keine Roblox-Studio-Laufzeit verfügbar ist, wurde die
extrahierte Lua-Logik über eine eingebettete Lua-VM (fengari, Node.js) mit
minimalen `Vector3`/`CFrame`/`Instance`-Stubs ausgeführt – inklusive der
tatsächlich in `ArenaBridge.ps1` stehenden Codezeilen (nicht nur einer
Kopie). Insgesamt 31 automatisierte Prüfungen, u. a.:

- Ein Dreieck (Kathetenlänge 3/4) in drei verschiedenen Punktreihenfolgen →
  alle drei bauen jetzt korrekt 2 Wedges (vorher: 2 von 3 fielen mit
  „degenerate triangle“ aus).
- Ein echt entartetes Dreieck (Duplikatpunkt) wird weiterhin korrekt
  abgelehnt.
- Einfaches Dreieck, einfaches Viereck.
- Achteckiger „Baumstamm“ aus 8 Seiten-Vierecken + `closeOpenings`: erzeugt
  jetzt zuverlässig 8 Seiten + 2 automatische Kappen (oben/unten) ohne einen
  einzigen übersprungenen Wedge (vorher: alle 16 Seiten-Wedges fielen aus).
- Viereck mit Beinahe-Duplikatpunkt und mit exakt kollinearem Zwischenpunkt.
- Leicht nicht-planares Viereck (z-Jitter).
- Konkaves, organisch anmutendes Polygon (Blatt-/Stein-Umriss).
- Gemischtes Submodel aus einer gültigen organischen Fläche + einer
  tatsächlich entarteten (kollinearen) Fläche: Build bleibt erfolgreich,
  meldet aber `incomplete=true`, `facesSkipped=1` und nennt Submodel-,
  Polygon-Name und Fehlergrund.

Zusätzlich läuft die im Repo vorhandene Offline-Struktur-/Lua-Prüfung
(`python3 test_v398_structure.py`, benötigt `pip install luaparser`)
weiterhin fehlerfrei durch – sie parst `ArenaBridge.ps1` u. a. mit einem
echten Lua-Parser.

**Empfehlung für den Test in Roblox Studio:** `build_polygon_model` einmal
mit einem einfachen Dreieck/Viereck aufrufen, danach mit einem zylindrischen
"Stamm" (z. B. 8–12 Seitenflächen + `closeOpenings=true`) und einem
komplexeren organischen Modell (Baum/Tier/Fels). Im Ergebnis auf
`result.facesSkipped`, `result.incomplete` und `result.warnings` achten –
bei 0 übersprungenen Flächen sollten keine sichtbaren Lücken mehr auftreten.
