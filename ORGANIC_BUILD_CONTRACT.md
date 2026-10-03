# 7.1.4 – Globaler Polygon-Vorrang und organischer Qualitätsnachweis

Dieses Update beantwortet einen konkreten Nutzerbericht über eine Bau-Session
über die Bridge. Es behebt nicht „einen Fehler“, sondern macht die drei
Ursachen dauerhaft unmöglich – und räumt die Einstellungen auf.

> **Aktueller Vertrag: Version 7.1.4.** Der Polygon-Vorrang gilt jetzt für alle nichttrivialen 3D-Aufgaben, unabhängig vom Modellnamen oder Beispiel. Die strenge serverseitige Proof-Sperre bleibt eine separate Zusatzregel für organische Modelle.

## Der Befund

- Ein Tier war nur ein Haufen **Kugel-Parts**: Körper, Kopf, vier Beine,
  Schwanz = sieben Bälle. Genau das, was man in der ersten Minute selbst baut.
- Ein Baum war **ein `CylinderPart` als Stamm plus eine Kugel als Krone**.
- **Alle Cylinder standen um 90 Grad falsch** – sie lagen als Fass quer,
  obwohl Stamm, Bein oder Säule gemeint war.
- Mitten in der Arbeit brach die Sitzung mit
  „The AI service rejected this request“ ab.
- In den Einstellungen fehlte der Schalter **„Benachrichtigung, wenn Arena
  fertig ist“**, und der deaktivierte `sim_start` stand dort noch als
  Warnkasten.

## 0. 7.1.4: globaler Modellierungsstandard und organischer Auditbeleg

### Globaler Polygon-Vorrang — für alle 3D-Kategorien

`modelBuildRules` wird mit jeder neuen Session ausgeliefert. Es gilt für
**jedes nichttriviale 3D-Modell**, nicht nur für Tiere, Bäume oder ein erkanntes
Beispiel: `build_polygon_model` ist die bevorzugte Wahl für die Hauptsilhouette
und individuelle, freie, gekrümmte oder verjüngte Formen in Figuren, Props,
Architektur, Fahrzeugen, Maschinen, Landmarken, Terrain und Kulissen.
`build_assembly` ergänzt wiederholte oder modulare Struktur; Standard-Parts
bleiben für einfache Formen, Stützen, Gelenke und Details passend.

Der Qualitätsmaßstab ist absichtlich höher als ein erster Primitive-Blockout:
klare Hauptsilhouette, sekundäre Funktionsformen, sorgfältige Details,
absichtsvolle Farb-/Materialrollen und korrekt verbundene/platzierte Teile.
Mehr Teile ohne gestalterischen Zweck sind keine zusätzliche Qualität. Einfache
Objekte und ausdrücklich gewünschte Primitive-/Low-Poly-Aufgaben bleiben
angemessen einfach. Die allgemeine Werkzeugwahl wird **nicht** durch Tier-,
Baum- oder sonstige Modellnamen erzwungen.

### Organischer Qualitätsvertrag — separate, explizite Markierung

Die strenge Organic-Sperre greift, wenn ein Build ausdrücklich mit
`organic=true` markiert ist; sie basiert nicht auf einem Tier-/Baum-Keyword im
Namen. Mit diesem Flag ist `build_polygon_model` der Pflichtweg. Der
HTTP-Guard verlangt mindestens drei explizite `color`-Zuweisungen im Aufruf
(`ORGANIC_COLORS_REQUIRED`) und blockiert einen anderen Builder vor dem
Studio-Aufruf mit `ORGANIC_POLYGON_REQUIRED`. Parallele oder asynchrone
organische Builds werden mit `ORGANIC_SEQUENCE_REQUIRED` abgewiesen. Für
unmarkierte Aufgaben bleibt der allgemeine, nicht blockierende Polygon-Vorrang
oben maßgeblich.

Das Plugin-Ergebnis kommt als `{ ok, result, warnings }`. Die Bridge entpackt
`result` und führt jedes während der organischen Bauarbeit für dieses Place
registrierte Modell als eigenen Nachweisdatensatz — einschließlich seiner
zurückgegebenen Modell-ID, sofern vorhanden. Jeder erfolgreiche spätere
Place-Schreibaufruf entwertet die Audit-Belege **aller** registrierten Modelle;
nach dem letzten Edit müssen sie daher alle erneut geprüft werden.

Ein einzelner, eigenständiger `model_audit` erneuert nur Belege für organische
Modelle, die in seinen per-model Ergebnissen exakt ausgewiesen sind. Ein
Workspace-Audit kann mehrere Modelle belegen, aber nur soweit jedes Modell
separat mit seinen Metriken zurückkommt. Erkennt das Plugin mehr organische
Modelle, als es per-model Details liefert, wird der fehlende Anteil ausdrücklich
als unvollständig gespeichert — ein Aggregat oder die Prüfung eines Geschwister-
modells zählt nicht als Nachweis. Parallel-/Batch-/Job-Antworten gelten nicht als
Audit-Beleg, weil ihre Schreib- und Prüfreihenfolge nicht sicher feststeht.

`report_done` akzeptiert organische Bauarbeit nur, wenn **jeder registrierte
Modell-Datensatz** einen frischen Audit nach dem letzten erfolgreichen
Place-Schreibaufruf, einen exakt passenden Modell-Eintrag und bestandene
Metriken hat. Es prüft unabhängig vom allgemeinen `buildQuality` für jedes
Modell einzeln:

- `polygonTriangles > 0` für tatsächliche `ArenaPolygonTriangle`-Wedges;
- mindestens drei gemessene Part-Farben, höchstens 90 % dominante Farbe und
  höchstens 90 % near-white/defaultartige Teile;
- mindestens ein erkanntes, aktiviertes Bewegungs-Script als Nachfahre genau
  dieses Zielmodells;
- keine vom Plugin-Audit gemeldeten `organicQuality.issues`.

Fehlt auch nur ein frischer oder exakter Modellnachweis oder ist der registrierte
Organic-Zustand unvollständig/unlesbar, kommt `ORGANIC_AUDIT_REQUIRED` (fail
closed); scheitern die Metriken eines Modells, `DETAIL_REQUIRED`. Ein
stiller Validierungsfehler oder erfolgreicher Audit eines einzelnen Modells
reicht also nicht für einen Place mit mehreren registrierten organischen Modellen.
`handoff` überspringt diese separate Organic-Prüfung nicht. Die Entscheidung
basiert auf dem entpackten Plugin-`result`, nicht auf einem selbst formulierten
Qualitätsbericht.

Die Hauptkopfzeile zeigt nun statisch nur noch „Arena Roblox Bridge“ und
„bereit für verbundene Places“. Versions-/SHA-/Wächterdetails bleiben über die
API und das Runtime-Log erreichbar. Die Place-Fortschrittsanzeige behält die
gewünschten Grün/Blau/Grau-Texte und blendet 100 % nach 60 Sekunden aus; ein
Token-Reset zeigt eine kurze In-Fenster-Bestätigung.

## 1. `organicBuildRules` – ein harter Regelblock in jeder Session

`Get-BridgeGuides` liefert den neuen Block `organicBuildRules` (genau wie
`polygonEngineRules` seit 6.1.4). Er erreicht **jede** neue Session
automatisch über den Sessionstart, `get_docs` und `GET /api/docs`.

Enthalten:

| Feld | Inhalt |
|---|---|
| `forbidden` | `FORBIDDEN – BYPASSING THE POLYGON BUILDER` (kein anderes Erstbau-Tool), `FORBIDDEN – BALL ANIMAL` (Tier nur aus Kugeln), `FORBIDDEN – CYLINDER TREE` (Stamm + Kugelkrone), `FORBIDDEN – UNTAPERED LIMBS`, `FORBIDDEN – ONE SINGLE ROTATION AS ANIMATION`, `FORGOTTEN COLOUR OR MOTION`, `CLAIMING DONE WITHOUT A FRESH PROOF` |
| `anatomyMinimum` | Rumpf → Hals → Schädel → Fang → vier Beine mit Ober-/Unterschenkel und Pfote (überlappend in den Rumpf) → Schwanzkette aus 4–8 kleineren Segmenten → Ohren → Augen (Ball + dunkle Pupille + Lichtpunkt), Nase, Mundlinie, Schnurrhaare → Fell-/Plattenstruktur und eigene Farben für Rücken, Bauch, Fang und Pfoten. **30–80 Teile sind normal, unter 15 ist ein Entwurf.** |
| `cylinderRule` | Die Achse eines Roblox-`CylinderPart` ist seine **lokale X-Achse**: `Size.X` = Länge, `Size.Y` = `Size.Z` = Durchmesser. Ohne Rotation liegt der Zylinder quer wie ein Fass. Stehend nur mit `CFrame.new(pos) * CFrame.Angles(0, 0, math.rad(90))`. |
| `cylinderDetection` | Was `model_audit` dazu misst (siehe Abschnitt 3). |
| `animationRule` | Organisch heißt **mehrere kleine Bewegungen mit unterschiedlichen Perioden**: Atmung (Rumpfskalierung ±2–3 %, 3–4 s), Kopf (±4–8°, 2,7 s), Ohrenzucken, Schwanzkette mit ~0,1 s Versatz je Segment (Spitze am weitesten), Gewichtsverlagerung (±1,5°, ~6 s), Blinzeln alle 3–6 s. Niemals eine einzelne Endlos-Rotation. |
| `detailBudget`, `workflow`, `selfCheck` | Detailreihenfolge (grob → fein), Ablauf und der Selbsttest vor `report_done`. |

`importantRules` verweist zusätzlich mit einem eigenen HARTEN Constraint
darauf, und die Werkzeugbeschreibungen von `build_polygon_model`, `run_lua`
und `model_audit` nennen den Block, damit die Regel im Moment der
Werkzeugwahl sichtbar ist.

### Die Referenz-Lua-Funktionen (geprüft)

```lua
-- Achse = LOKALE X-Achse. Size.X ist die Laenge!
local function uprightCylinder(parent, pos, height, diameter, props)
    local p = Instance.new("Part")
    p.Shape = Enum.PartType.Cylinder
    p.Size = Vector3.new(height, diameter, diameter)          -- X = length!
    p.CFrame = CFrame.new(pos) * CFrame.Angles(0, 0, math.rad(90))
    applyProps(p, props, parent)
    return p
end

-- Jede Richtung, immer richtig: Basis AUS der Richtung selbst gebaut.
local function cylinderBetween(parent, a, b, diameter, props)
    local delta = b - a
    local length = delta.Magnitude
    if length < 0.01 then return nil end
    local axis = delta.Unit                                   -- local X
    local ref = (math.abs(axis.Y) > 0.99) and Vector3.new(0, 0, 1) or Vector3.new(0, 1, 0)
    local z = axis:Cross(ref).Unit                            -- local Z
    local y = z:Cross(axis).Unit                              -- local Y (X cross Y = Z)
    local p = Instance.new("Part")
    p.Shape = Enum.PartType.Cylinder
    p.Size = Vector3.new(length, diameter, diameter)
    p.CFrame = CFrame.fromMatrix((a + b) * 0.5, axis, y, z)
    applyProps(p, props, parent)
    return p
end
```

`CFrame.Angles(0, 0, math.rad(90))` dreht die lokale X-Achse exakt auf
Welt-Y; `cylinderBetween` erzeugt für **jede** Richtung eine rechtshändige,
orthonormale Basis (`X × Y = Z`), die `CFrame.fromMatrix` akzeptiert.
Beides wird in `test_v713_quality.py` numerisch nachgerechnet; die organischen Erstbau-/Auditregeln prüft `test_v714_organic.py`.

## 2. Warum die 90-Grad-Dreher passieren

| Absicht | Falsch (klassischer Fehler) | Richtig |
|---|---|---|
| Stehender Stamm, Höhe 12, Durchmesser 2 | `Size = Vector3.new(2, 12, 2)`, keine Rotation → **flache Scheibe/oval** | `Size = Vector3.new(12, 2, 2)` + `CFrame.Angles(0, 0, math.rad(90))` |
| Rohr zwischen zwei Punkten | `Orientation = Vector3.new(0, 90, 0)` „damit es senkrecht steht“ | `cylinderBetween(a, b, d)` |
| Liegender Balken | Rotation um X oder Z | `CFrame.new(pos)` (Achse = Welt-X) |

## 3. Gemessen statt behauptet: `model_audit.buildQuality`

`model_audit` zählt jetzt zusätzlich Kugeln, Blöcke, Zylinder, Keile, Mesh-,
Union-, Polygon-/Assembly- (`ArenaMasterBuild`, `ArenaPolygonTriangle`,
`ArenaPolygonSubmodel`, `ArenaAssembly`) und `ArenaDetail`-Teile und liefert:

- `primitiveOnly` / `primitiveGroups` – Gruppen (unter dem Ziel, je
  Model/Folder), die **nur** aus Kugeln bestehen: ≥ 6 Teile, ≥ 6 Kugeln,
  ≥ 50 % Kugelanteil und **kein** Polygon-/Assembly-/Mesh-/Union-/Detail-Teil.
  Jede Gruppe nennt Name, Pfad, Teile, Kugeln und Ball-Anteil.
- `cylinderProblems` – je Zylinder der harte Befund `discLikeCylinder`:
  die Achse liegt waagerecht (`|X·Y| < 0,3`) **und** das Teil ist quer
  mindestens 1,5-mal so groß wie lang (`max(Size.Y, Size.Z) ≥ 1,5 · Size.X`).
  Genau so sieht der 90-Grad-Dreher aus, wenn die Länge in `Size.Y`/`Size.Z`
  eingetragen wurde.
- `tiltedCylinders` – reine **Info**: die Achse ist schief zu jeder Weltachse
  (`axisSkewDeg`). Bei einem schrägen Ast richtig, bei einem Stamm nicht.
- `verdict`: `clean` | `primitive_abuse` | `cylinder_rotation` |
  `primitive_abuse_and_cylinder_rotation`, dazu `advice` und `counts`.

Das Ergebnis steht in **jeder** Antwort unter `_bridge.buildQuality` (über
`$Shared.AuditFlags`), nicht erst am Ende.

## 4. `report_done` sagt jetzt Nein

Liegt für die Sitzung eine solche Messung vor und wurde kein Handoff
geschrieben, antwortet `report_done` mit **`DETAIL_REQUIRED`** statt „fertig“:

```
model_audit measured a PRIMITIVE-ONLY build: 1 group(s) consist only of Ball
parts - "Wildlife_Cat" (7 balls). report_done does not accept this as finished
work - a ball-only animal or a sideways cylinder is a draft, not a model.

howToFix: Either rebuild it (build_polygon_model + cylinder rule from
organicBuildRules, then model_audit again) OR - if this really is a deliberate
blockout - call handoff { ... }. That is an invitation, not a punishment.
```

Platzhalter behalten wie bisher Vorrang: existieren welche und fehlt der
Handoff, kommt weiterhin `HANDOFF_REQUIRED`. Dieser ältere `buildQuality`-Pfad
ändert nichts am separaten 7.1.4-Organic-Gate aus Abschnitt 0: ein Handoff kann
fehlende Modell-Audits oder nicht bestandene Organic-Metriken nicht übergehen.

## 5. Kleinere Sitzungs-Nutzlast

Die erste Antwort einer Sitzung enthielt bis 7.1.2 die **komplette** Doku aller
129 Werkzeuge – zusammen mit den Regelblöcken weit über 120 KB in einem Paket.
Solche Riesenpakete sind ein bekannter Auslöser für abgelehnte KI-Anfragen.

Jetzt:

- **47 Kernwerkzeuge vollständig** (Bauen, Audit, Lesen, Sitzung: u. a.
  `build_polygon_model`, `build_assembly`, `build_interface`, `build_surface`,
  `ui_capabilities`, `ui_skin`, `ui_audit`, `model_audit`, `world_audit`,
  `run_lua`, `refine`, `prop_place`, `report_done`, `get_docs`, `get_chunk`).
- **Alle übrigen als Index** (Name, Kategorie, Kurztext) mit dem Hinweis, die
  Parameter mit `get_docs { tool = "…" }` oder `GET /api/docs?tool=…` zu holen –
  dort bleibt die Dokumentation vollständig.
- **Harte Obergrenze** `$Shared.SessionPayloadHardBudgetBytes = 300000` (Bytes,
  JSON): wächst das Paket trotzdem darüber, wird auch der Kern nur noch als
  Index verschickt.
- Jede Sitzung nennt **`packageBytes`** (am echten serialisierten Paket
  gemessen), **`budgetBytes`** und **`docsPolicy`** (`core-full` /
  `index-only`).

Ehrliche Einordnung: „The AI service rejected this request“ stammt vom
KI-Dienst, nicht von der Bridge. Die Bridge kann nur dafür sorgen, dass **ihr**
Beitrag nicht mehr zu den Riesenpaketen gehört – genau das tut sie jetzt,
messbar.

## 6. Einstellungen

- **Neu:** „Benachrichtigung, wenn Arena fertig ist“ – direkt unter
  „Fortschritt in der Place-Liste anzeigen“, roter/grüner Schalter wie alle
  anderen, Standard **aus**, dauerhaft in `settings.json`
  (`notifyOnDone`). Aus wirkt sofort: `Clear-NotifyQueue` verwirft wartende
  Meldungen, der Anzeige-Takt überspringt sie, und `Show-ArenaDoneNotification`
  prüft den Schalter unmittelbar vor dem Anzeigen.
- **Entfernt:** der Abschnitt „SIMULATION“ samt `sim_start`-Warnhinweis.
  `sim_start` bleibt deaktiviert und begründet (Doku, Manifest, jede Antwort) –
  nur die Dauerwarnung im Fenster gibt es nicht mehr.

## 7. Prüfung

```text
python3 test_v714_organic.py      # Mehrmodell-Belege, frischer Audit, fail-closed report_done und UI
python3 test_v713_quality.py      # Mathematik, Messung, historisches Gate, Schalter und Sessionbudget
python3 test_v398_structure.py    # 7.1.4-Funktionsversionen, Lua via luaparser, XAML als XML
python3 test_v710_delivery.py
python3 test_v711_delivery.py
python3 test_v712_toolbox.py      # prueft nur noch "mindestens 7.1.2"
python3 test_queue_model_707.py
```

`test_v713_quality.py` rechnet unter anderem die Zylinder-Mathematik nach
(`CFrame.Angles(0, 0, 90°)` → lokale X-Achse exakt nach oben; `cylinderBetween`
rechtshändig für beliebige Richtungen), stellt die Kugel-Erkennung als Modell
nach (7-Bälle-Tier ja; Schneemann aus 3 Bällen, Polygon-Modell und gemischte
Szene nein) und prüft die `report_done`-Wache sowie den Schalter.

Die Bestätigung auf Windows mit laufendem Studio steht noch aus – offline sind
Struktur, Lua-Syntax, XAML und Semantikmodelle geprüft.
