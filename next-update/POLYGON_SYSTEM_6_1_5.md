# Update 6.1.5 – Polygon-System verbunden und geometriesicher

Version 6.1.5 behebt zwei Laufzeitursachen hinter dem Fehlerbild „Teile liegen
zunächst ungefähr richtig, sind aber nicht verbunden und rotieren kreuz und
quer“.

## Behobene Ursachen

### 1. Wedges waren standardmäßig unabhängige Physikkörper

`build_polygon_model` erzeugt jede triangulierte Fläche aus zwei
`WedgePart`s. Bis 6.1.4 war `autoWeld` standardmäßig aus. Bei
`anchored=false` simulierte Roblox deshalb jeden Wedge einzeln. Die Teile
starteten an der berechneten Position, konnten danach aber auseinanderfallen
und unabhängig rotieren.

Ab 6.1.5 gilt:

- `autoWeld` ist standardmäßig `true`.
- Alle Wedges eines Untermodells werden über `WeldConstraint`s mit dessen
  Root-Part verbunden.
- Nur ein ausdrücklich gesetztes `autoWeld=false` erzeugt bewusst getrennte
  Teile.
- Mehrere Untermodelle bleiben weiterhin getrennt oder werden wie bisher über
  `mainWeld`/`mainWelds` verbunden.

### 2. Freie Style-Properties konnten die Polygon-Geometrie überschreiben

Der Builder setzte zuerst das berechnete `Size` und `CFrame`, wandte danach
aber `style.properties` an. Enthielt diese Tabelle versehentlich eines der
Geometriefelder, wurde die korrekte Lage wieder überschrieben. Das betraf:

- `Position`
- `Orientation`
- `Rotation`
- `CFrame`
- `Size`
- `PivotOffset`

Diese Felder gehören nun ausschließlich dem Polygon-Builder. Sie werden aus
`style.properties` gefiltert, als `ignoredGeometryProperties` gemeldet, und
`Size`/`CFrame` werden garantiert zuletzt gesetzt. Farben, Materialien,
Kollision, Transparenz und andere normale Part-Eigenschaften bleiben frei
konfigurierbar.

## Arena-Routing und Diagnose

Die Session-Anleitung verlangt für Polygon- und Freiformflächen jetzt
`build_polygon_model`, sofern der Nutzer nicht ausdrücklich selbst
programmierte Low-Level-Wedges verlangt. Die Rückgabe des Builders enthält
zusätzlich:

- `autoWeldDefault=true`
- `weldedSubmodels`
- `ignoredGeometryProperties`
- `geometryInvariant="Size/CFrame applied after safe style properties"`

Damit kann Arena direkt erkennen, ob die erzeugte Haut verbunden wurde und ob
eine Eingabe versucht hat, berechnete Frames zu überschreiben.

## Kompatibilität

Die API bleibt rückwärtskompatibel. Einziger bewusster Default-Wechsel ist
`autoWeld: false -> true`, weil ein Polygonmodell standardmäßig ein
zusammenhängendes Objekt sein muss. Nutzer, die absichtlich unabhängige Teile
benötigen, können weiterhin `autoWeld=false` setzen.

## Prüfung

`test_v398_structure.py` prüft unter anderem:

- alle Runtime-, Plugin-, Server-, UI- und Updater-Versionen auf 6.1.5,
- syntaktisch gültiges Plugin-Lua und eingebettete Lua-Quellen,
- gültige XAML-Blöcke,
- Default-on-Welding und den expliziten `false`-Opt-out,
- die vollständige Sperrliste der sechs Geometriefelder,
- dass sichere Style-Properties **vor** dem finalen `Size`/`CFrame` gesetzt
  werden,
- die neuen Diagnosefelder und die verbindliche Tool-Routing-Regel.

Ausgeführt mit:

```text
.venv/bin/python test_v398_structure.py
OK: 6.1.5 structure, Lua and XAML validation passed
```

Nach dem automatischen Update Roblox Studio einmal neu starten, damit das
Plugin 6.1.5 geladen wird.
