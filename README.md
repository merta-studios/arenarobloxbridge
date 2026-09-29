# Arena Roblox Bridge

Dieses Repository enthält das Programm **Arena Roblox Bridge** – die Brücke
zwischen einer KI und Roblox Studio:

- Verbindet jedes geöffnete Roblox-Studio-Fenster automatisch
- Installiert das Studio-Plugin und den Cloudflare-Tunnel vollständig
  automatisch (keine Admin-Rechte, keine Eingaben)
- Stellt für jedes Place einen Prompt (URL + Token) bereit

Die **ArenaBridge.exe** (der Starter) wird einmalig gebaut und an Freunde
weitergegeben. Sie lädt das Programm **aus diesem Repository** herunter und
hält es automatisch aktuell – deshalb muss dieses Repository **öffentlich**
sein.

## Dateien

| Datei | Zweck |
|---|---|
| `ArenaBridge.ps1` | Das komplette Programm |
| `version.json` | Aktuelle Version + Neuigkeiten (wird im Update-Fenster angezeigt) |
| `README.md` | Diese Datei |
| `test_v398_structure.py` | Python-Strukturtest für 6.1.3 (Versionen, Lua via luaparser, XAML-XML; kein PowerShell nötig) |
| `test-v39.ps1` | Ergänzende Windows-PowerShell-Mock-Tests für 5.2 (optional; wird NICHT vom Starter geladen) |

## So wird ein Update veröffentlicht

1. `ArenaBridge.ps1` im Repository durch die neue Version ersetzen.
2. In `version.json` die `version` erhöhen (z. B. `3.6` → `3.7`) und die
   `notes` mit den Neuigkeiten füllen – genau dieser Text erscheint den
   Nutzern nach dem Update im Update-Fenster.
3. Änderungen committen und pushen. Fertig!

Beim nächsten Start der ArenaBridge.exe wird das Update automatisch erkannt,
heruntergeladen und mit dem Hinweis-Fenster („Update installiert!“) gestartet.

## Versionsverlauf

## 6.1.4
- **Polygon Engine 2.0 – dauerhafte KI-Regel gegen 90°-Drehfehler & Nahtspalten.** `build_polygon_model` trianguliert Dreiecke seit 6.1.3 korrekt (siehe unten), aber die richtige `WedgePart`-Achsenkonvention war nirgends als feste, sitzungsübergreifende Regel für die KI hinterlegt. Schrieb Arena statt des Tools eigenen Lua-Code für Polygone/Wedges (z. B. über `run_lua`), konnte sie versehentlich Dicke, Höhe und Basiskante auf die falschen lokalen Achsen legen – genau das erzeugt die gemeldeten 90°-Drehfehler und klaffenden Nahtstellen.
- **Harte Achsen-Regel jetzt Teil jeder Session.** `Get-BridgeGuides` liefert automatisch bei Sessionstart, `get_docs` und `/api/docs` die unverletzliche Regel (lokal X = Dicke/Flächennormale, lokal Y = Höhe/Orthogonale zur Basiskante, lokal Z = Basiskanten-Richtung, `CFrame.fromMatrix(position, normal, up, dir)`) sowie eine fertige, geprüfte Referenz-Lua-Funktion `drawSeamlessTriangle` (längste Kante als Basis, Lotfußpunkt-Teilung in zwei rechtwinklige Keile, nach innen versetzter Skin-Offset gegen Nahtspalten).
- **Kein Verhaltenswechsel an `build_polygon_model` selbst.** Das Tool bleibt unverändert die stark empfohlene erste Wahl für Polygon-Modelle inklusive Retry/Fallback-Triangulierung und Vertex-Welding; die neue Regel greift nur, wenn Arena bewusst eigene Wedge-/Dreieck-Logik über `run_lua` schreibt.
- Nach dem Update Roblox Studio einmal neu starten, damit das Plugin **6.1.4** geladen wird.

## 6.1.3
- **Polygon-Builder: sichtbare Lücken geschlossen.** `build_polygon_model` hat einzelne Flächen kommentarlos weggelassen – besonders bei Bäumen, Stämmen, Tieren und anderen runden oder organischen Formen. Ursache war ein Punktreihenfolge-Bug in `MASTER_BUILD.triangleWedges`: Beim internen Umsortieren (längste Kante nach unten) wurden nur zwei der drei Dreieckspunkte neu gesetzt, sodass zwei Ecken auf denselben Punkt zeigten und ein völlig korrektes Dreieck als „entartet“ verworfen wurde. Ob eine Fläche entstand, hing damit allein von der zufälligen Reihenfolge der gelieferten Punkte ab – bei einem achteckigen Stamm fielen so alle 16 Wedges aus.
- **Offene Nähte werden wieder verschweißt.** `MASTER_BUILD.pointKey` erzeugte aus winzigen negativen Rundungsresten (z. B. `sin(2*pi)`) den Schlüssel `-0.00000` statt `0.00000`. Derselbe Punkt bekam dadurch zwei verschiedene Schlüssel, und runde Querschnitte konnten ihre eigene Anfangs-/End-Naht nicht schließen. Negative Null wird jetzt normalisiert.
- **Robustere Triangulierung mit Retry und Fallback.** `cleanPolygonPoints` entfernt vorab Beinahe-Duplikate und exakt kollineare Zwischenpunkte; scheitert eine Fläche trotzdem, versucht `triangulate` es mit gelockerter Toleranz, danach mit umgekehrter Orientierung und zuletzt mit einer Fan-Triangulierung. `weldEntryVertices` verschweißt praktisch identische Vertices eines Untermodells, bevor `closeOpenings` die Ränder sucht.
- **Ehrliche Diagnose statt stiller Lücken.** `build_polygon_model` liefert jetzt `facesTotal`, `facesBuilt`, `facesSkipped`, `incomplete` und einen lesbaren `warnings`-Text. Ein Modell mit übersprungenen Flächen sieht nicht mehr wie ein voller Erfolg aus; jeder Eintrag in `skipped` und `fallbackFaces` nennt Untermodell, Polygonname und Grund. Bestehende Felder bleiben unverändert.
- Nach dem Update Roblox Studio einmal neu starten, damit das Plugin **6.1.3** geladen wird.

## 6.1.2
- **Kritischer Start-Hotfix.** Die 6.1.1-Datei enthielt nach dem vorgesehenen letzten `Exit(0)` versehentlich sieben beschädigte Textfragmente, darunter eine alleinstehende schließende Klammer. Windows PowerShell parst das gesamte Skript vor dem ersten Fenster; deshalb konnte die Bridge nach dem funktionierenden EXE-Updater gar nicht mehr starten.
- **Behebung ohne Funktionsrückbau.** Der fehlerhafte Dateianhang ist entfernt. Oberfläche, Update-Hinweis und alle 6.1.1-Funktionen bleiben erhalten.
- **Dauerhafter Regressionstest.** `test_v398_structure.py` prüft jetzt die feste, beabsichtigte Schlusssequenz der PowerShell-Datei. Jede angehängte Zeile – ob unvollständig oder nicht – lässt den Release-Test fehlschlagen.

## 6.1.1
- **Polygon-Modelling wie in Blender – ausdrücklich stark empfohlen.** `build_polygon_model` kann jetzt in einem Call sehr große, vollständig untergeordnete Modelle aus mehreren Foldern/Untermodellen erstellen. Ein Baum kann etwa aus Stamm und drei Kronen bestehen; jedes Untermodell erhält eigene Farbe, Material-, Kollisions-, Transparenz- und normale Part-Eigenschaften. Optionale Auto-Welds halten jedes Untermodell zusammen, klassische benannte Haupt-Welds verbinden sie animierbar miteinander.
- **Nahtlose Wedge-Haut.** Die Dicke wird standardmäßig von der sichtbaren Polygonseite nach innen aufgebaut statt um die Flächenmitte. Dadurch bleiben die gelieferten Polygonpunkte die exakte Außenhaut und stark gegeneinander gedrehte Flächen erzeugen keine wachsenden Rillen mehr; die Innenseiten überlappen sauber. `thicknessPlacement=center` erhält bei Bedarf das alte Verhalten.
- **Offene Modelle automatisch schließen.** `closeOpenings=true` erkennt offene Rand-Loops eines Untermodells und erzeugt triangulierte `AutoCap`-Flächen – etwa wenn an einem Baumstamm die Oberseite vergessen wurde.
- **Toolbox-Säuberung vor dem Einfügen.** `insert_asset { sanitize=true }` entfernt bereits im noch nicht untergeordneten Asset alle Lua-Skripte, Remote-/Bindable-Events und Functions. So kann Arena Modelle bewusst als reine Geometrie ohne Skripte oder typischen Viren-Müll einsetzen.
- **Editor-Vorschau-Icons abschaltbar.** Ein neuer dauerhafter Schalter in den Einstellungen blendet die Live-Vorschau-Icons aus und stoppt sofort alle weiteren Fensteraufnahmen, um Leistung zu sparen.

## 6.1.0
- **Kurze, lebendige Windows-Mitteilungen.** `report_done` besitzt jetzt getrennte Felder für einen von Arena formulierten Titel (maximal 70 Zeichen) und Inhalt (maximal 140 Zeichen). Die Bridge validiert diese konservativen Windows-11-Anzeigebudgets, damit Toasts nicht zu langen Änderungslisten werden. Microsoft setzt bei adaptiven Toast-Textfeldern keine feste Zeichenzahl pro Feld; die Darstellung hängt von Layout, Breite und Skalierung ab (Titel bis zu 2 Zeilen, Beschreibungen zusammen bis zu 4 Zeilen). Deshalb verwendet die Bridge bewusst feste Vollanzeige-Budgets. Quellen: [Microsoft – App notification content](https://learn.microsoft.com/en-us/windows/apps/develop/notifications/app-notifications/adaptive-interactive-toasts) und [Notifications Visualizer](https://learn.microsoft.com/en-us/windows/apps/develop/notifications/notifications-visualizer) (5-KB-Payloadlimit).
- **Live-Vorschauen alle drei Sekunden.** Solange das Bridge-Fenster geöffnet und nicht minimiert ist, werden alle Place-Vorschauen weiter aktualisiert. Ein minimiertes Roblox-Studio-Fenster wird nicht mehr durch `IsIconic` vorab ausgeschlossen; die direkten `PrintWindow`-Aufnahmewege dürfen es weiterhin rendern.
- **Toolbox vollständig geöffnet.** Arena kann nach 3D-Modellen, Models, Meshes/MeshParts, Plugins, Fonts, Audio, Bildern/Decals, Video und Animation suchen. Der frühere `allowModels`-Freigabeschalter ist aus Vertrag und Anleitung entfernt. Typ-, Rechte- und Skriptprüfungen beim tatsächlichen Einfügen bleiben als transparente Rückmeldung erhalten.
- **Arena-Verlauf repariert.** Die History-Funktion gab alle Einträge durch ein überflüssiges unäres Komma als ein verschachteltes Array zurück. Die UI erhält nun eine flache Liste; Aktionen erscheinen wieder pro Place und in „Alle Places“.
- **Neue Meister-Bautools.** `build_assembly` erstellt bis zu 2.000 Instanzen einschließlich linearer oder radialer Wiederholungen direkt in einem Model. `build_polygon_model` akzeptiert Punktlisten oder kompakte `POLYGON … END`-Skripte. Die Bridge berechnet Newell-Normale, 3D-Projektion, Orientierung, Ear-Clipping für konkave Polygone, Triangulation und Wedge-CFrames. Jede Fläche wird ausschließlich aus ultradünnen WedgeParts gebaut (zwei pro Dreieck) und strukturiert gruppiert.
- **Freier arbeitende Arena.** Die lange Vorschriftenliste der Sitzungsdokumentation wurde durch eine kurze Fähigkeitenübersicht ersetzt. Arena kann Bau-, Asset-, Skript-, Batch- und Testwerkzeuge passend zur Aufgabe kombinieren. Dedizierte Bautools werden klar angeboten; `run_lua` bleibt für echte Speziallogik verfügbar.

## 6.0.6
- **Laufzeitursache aus 6.0.5 nachgewiesen.** Die ausgelieferte Datei lief mit
  Version `6.0.5`, SHA-256
  `7433925B060FDD21A699936B3B8267E899EF1BB80A1673119D1DDFFB9B20E588`,
  `LanguageMode=FullLanguage` und geladenem C#-Helfer. Trotzdem brach
  `New-PlacePreviewVisual` schon beim UI-Aufbau mit
  `MethodException: Für "new" und die folgende Argumenteanzahl kann keine
  Überladung gefunden werden: "1"` ab (Laufzeitzeile 16101). Der nachfolgende
  Selbsttest belegte die direkte Folge:
  `IMAGE_ASSIGN_SKIPPED ... grund=Zeile/IconImage fehlt`.
- **Gezielte Änderung in `New-PlacePreviewVisual`.** Der belegte
  Ein-Argument-Aufruf
  `[System.Windows.Media.DoubleCollection]::new(@(4.0, 8.0))` wurde ersetzt:
  parameterlos konstruieren, `4.0` und `8.0` einzeln per `Add` eintragen, dann
  erst `StrokeDashArray` zuweisen. Damit wird das von Windows PowerShell 5.1
  nicht bindbare `object[]` vermieden. Kein UI-Umbau und keine Änderung an
  Fensterzuordnung oder Aufnahmewegen.
- **Regressionstest erweitert.** `test_v398_structure.py` verbietet genau den
  fehlgeschlagenen Konstruktoraufruf, prüft die Reihenfolge
  Konstruktor → `Add(4.0)` → `Add(8.0)` → Zuweisung und kontrolliert alle
  funktionalen Versionsliterale mit exakten Anzahlen.
- **Live-Abnahme offen.** Die Änderung ist statisch geprüft, aber noch nicht
  auf dem Nutzer-PC bestätigt. Maßgeblich sind erst eine 6.0.6-Identität und
  `PREVIEW_UI_VERIFY`/`PREVIEW_UI_SELFTEST_OK` sowie danach die `cap-N`- und
  PNG-Nachweise. Keine Erfolgsmeldung vor diesen Laufzeitbelegen.

## 6.0.5
- **Fenster-Vorschau: zugewiesen, aber unsichtbar – Einblendung repariert.**
  Zwei Messbefunde vom Nutzer-PC haben die Ursache eingekreist:
  (1) Die Einstellungen zeigten „Version 6.0.4“, es lief also tatsächlich die
  neue Fassung – der Verdacht „Updater liefert nie aus“ ist damit widerlegt.
  (2) Die pinke Selbsttest-Kachel aus 6.0.4 erschien nie. Da ein einmal
  gesetztes Vorschaubild im Programm durch nichts mehr entfernt werden kann
  (`PreviewHasFrame = $true` sperrt das Platzhalter-Symbol, und
  `IconImage.Source` wird nirgends zurückgesetzt), hätte das Testbild dauerhaft
  stehen bleiben müssen. Es war also nie sichtbar – der Fehler lag im
  Anzeigepfad, nicht in der Fensteraufnahme.
- **Ursache und Fix (`Set-PlacePreviewImage`).** Das erste Bild einer Zeile
  wurde mit `Opacity = 0` eingesetzt; sichtbar wurde es ausschließlich durch
  eine `DoubleAnimation` (0 → 1). Läuft diese Animation nicht an, bleibt die
  Kachel dauerhaft leer, obwohl Bildquelle, `Visibility` und Layout korrekt
  sind. Genau dieser Ausfall ist in diesem Programm für die Place-Zeile selbst
  belegt – sie hat deshalb seit 5.0.2 einen Einblend-Wächter
  („Einblend-Animation kam nie an“); das Vorschaubild hatte keinen. Jetzt ist
  der Grundwert sofort `Opacity = 1`, die Animation ist nur noch Verzierung
  (`FillBehavior = Stop`), und ein Wächter korrigiert eine hängende
  Einblendung nach 400 ms hart (`PREVIEW_OPACITY_RESCUE`).
- **Ehrliches Selbsttest-Urteil.** `PREVIEW_UI_SELFTEST_OK` wurde bisher
  geschrieben, sobald das Zuweisen nicht geworfen hat – auch bei Deckkraft 0.
  Das Urteil fällt jetzt erst 1,5 s später und nur, wenn das Bild wirklich
  sichtbar ist (im Baum sichtbar, effektive Deckkraft > 0,05, Fläche > 0,
  Bildquelle gesetzt); sonst `PREVIEW_UI_SELFTEST_FAILED` mit konkretem Grund.
- **Neue Station `PREVIEW_UI_VERIFY`.** Misst Bild, Rahmen und Zeile
  (Visibility/Opacity/ActualSize/Source) und rechnet die effektive Deckkraft
  der Kette aus. Fehlt die Zeile ganz, laufen im Prozess weder
  Dispatcher-Timer noch Animationen – auch das wäre damit bewiesen.
- **Kleiner Kurzbericht zum Weitergeben:**
  `%LOCALAPPDATA%\ArenaRobloxBridge\preview-diagnose.txt` mit
  Laufzeit-Identität (Version/SHA-256), Aufnahme-Modus, Selbsttest-Urteil,
  Inhalt der PNG-Ablage und den letzten Vorschau-Stationen.
- Aufnahmewege, Fensterzuordnung, Design, Bedienung, Einstellungen, Server und
  Plugin-Protokolle bleiben unverändert. Keine Toast-/Popup-Meldungen.

## 6.0.4
- **Ende des Ratens: Laufzeit-Diagnose für die Fenster-Vorschau.** In den
  Place-Zeilen erschien trotz 6.0.1–6.0.3 weiterhin kein Vorschaubild – ohne
  dass ein einziger Aufnahmeversuch im Log belegt gewesen wäre. Jeder Versuch
  trägt jetzt eine kompakte Ablauf-ID und protokolliert die Stationen
  `CAPTURE_START` → `WINDOWS_ENUMERATED` → `HANDLE_RESOLVED` → `WORKER_STARTED`
  → `WORKER_COMPLETED` → `RESULT_RECEIVED` → `PNG_DECODED` → `IMAGE_ASSIGNED`
  → `IMAGE_VISIBLE` – jeweils mit Sitzung, Prozess-ID, Fensterhandle
  (HWND), Fenstertitel, Datentyp, Byte-Anzahl, Bildgröße und Fehlertext.
  Kein `catch`-Block im Vorschaupfad bleibt mehr still.
- **Sichtbarer UI-Selbsttest.** Beim ersten Place wird ein im Speicher
  gezeichnetes, unverwechselbar pink-limettenfarbenes Testbild durch exakt
  denselben `Set-PlacePreviewImage`-Pfad in die Kachel geschickt
  (`PREVIEW_UI_SELFTEST_OK`/`PREVIEW_UI_SELFTEST_FAILED` im Log). Erscheint
  das Testbild nicht, liegt der Fehler in WPF/UI; erscheint es, aber kein
  echtes Fensterbild, blockiert allein die Fensteraufnahme – und das Log
  nennt den blockierten Weg.
- **Robuste Bilddaten-Übergabe.** Die Aufnahme läuft über den kompilierten
  C#-Helfer `Arena.PreviewCapture` direkt im Hauptprozess. Das Ergebnis ist
  ein unveränderliches `byte[]` und durchquert keine PowerShell-Runspace-
  Grenze mehr (bei Kompilier-Fehlern, z. B. Sprachmodus ConstrainedLanguage,
  greift begründet geloggt der 6.0.3-Runspace-Fallback). Die UI-Zuweisung
  läuft ausschließlich über den WPF-Dispatcher.
- **Vier Aufnahmewege für GPU-/verdeckte Fenster.** `PrintWindow` mit
  `PW_RENDERFULLCONTENT` → `PrintWindow` ohne Flag → `WindowDcBitBlt`
  (DWM-Umleitfläche) → `CopyFromScreen` als letzter Fallback. Ein Weg gilt
  nur als erfolgreich, wenn die Bitmap nicht schwarz/transparent ist – der
  benutzte Weg und jeder Zwischenbefund stehen im Log. Jede Aufnahme liegt
  zusätzlich atomar als `%LOCALAPPDATA%\ArenaRobloxBridge\preview-cache\
  <sid>.png` vor (mit SHA-256-Kurzhash im Log, eindeutig prüfbar).
- **Laufzeit-Identität.** Beim Start protokolliert das Programm Version,
  absoluten Pfad und SHA-256 der wirklich laufenden Datei sowie den
  PowerShell-Sprachmodus – der Beleg, ob der Starter tatsächlich 6.0.4
  installiert hat oder weiter eine alte Kopie startet.
- **Keine neuen Blocker.** Kein synchroner Netzwerkzugriff im UI-Thread,
  kein `Worker.Stop`/`Dispose` auf dem UI-Thread (Task-Jobs werden bei
  Zeitüberschreitung nur fallengelassen). Design, Bedienung, Einstellungen,
  Server und Plugin-Protokolle bleiben unverändert.

## 6.0.3
- **Mehrfenster-Vorschau wirklich repariert.** Die Fensterliste wurde durch ein
  überflüssiges PowerShell-Komma als verschachteltes Array zurückgegeben. Bei
  mehreren Studio-Fenstern versuchte die Bridge deshalb, ein ganzes
  Handle-Array als einzelnes Fenster zu behandeln; die Aufnahme startete nie.
  Fenster- und Titellisten werden jetzt garantiert flach zurückgegeben.
- **Direkte Fensteraufnahme statt Bildschirmfoto.** `PrintWindow` mit
  `PW_RENDERFULLCONTENT` rendert das zugeordnete Studio-Fenster auch dann, wenn
  die Bridge oder ein anderes Fenster davor liegt. `CopyFromScreen` bleibt als
  automatischer Fallback für Systeme, die `PrintWindow` ablehnen.
- **Sofortiger Start ohne Web-Blockade.** Die synchrone Roblox-Thumbnail-
  Abfrage wurde aus dem WPF-Thread entfernt. Die Kachel ist wieder
  ausschließlich eine echte Studio-Fenster-Vorschau.
- **Selbstheilung und Diagnose.** Blockierte Aufnahme-Worker werden nach zehn
  Sekunden beendet und neu versucht. Auch eine bereits vor dem Worker
  gescheiterte Fensterzuordnung steht nun mit Ursache in `runtime.log`.

## 6.0.2
- **Spiel-Icon-/Vorschau-System repariert (der lang ersehnte Fix).** In 6.0.1
  blieb bei *jedem* gescheiterten Aufnahmeversuch des Studio-Fensters (z. B.
  Studio minimiert, Fenster mehreren Zeilen nicht eindeutig zuordbar, Fehler
  beim Aufnehmen) der Ladekreis endlos stehen – nie ein Bild, nie eine
  Fehlermeldung. Jetzt: Nach 3 gescheiterten Versuchen erscheint das
  Platzhalter-Symbol, die Aufnahmen laufen im Hintergrund weiter, und sobald
  eine klappt, blendet die Live-Vorschau ein. Jede fehlgeschlagene Aufnahme
  wird außerdem mit Grund in `runtime.log` protokolliert (gedrosselt), und
  die erste erfolgreiche Aufnahme je Sitzung wird einmalig bestätigt.
- **Zuordnung bei mehreren Studio-Fenstern robuster.** Der Zeilentitel musste
  bisher exakt dem bereinigten Fenstertitel entsprechen – der angehängte
  Hinweis „Studio neu starten (Plugin veraltet)“ oder Leerraum-/Groß-/Klein-
  Schreibabweichungen brachen die Zuordnung. Jetzt: exakter Treffer, danach
  toleranter Treffer (Leerraum, Groß-/Kleinschreibung, Anfangs-
  Übereinstimmung), danach der zuletzt bekannte Handle.
- **Null- und Type-Sicherheit.** Ein nicht auflösbarer Fenster-Handle kann
  nicht mehr still bis zur Aufnahme durchreichen; der Aufnahme-Worker bringt
  zudem seinen eigenen ScreenHelper-Fallback mit (Add-Type im Worker), falls
  der Typ im Haupt-Runspace nicht geladen werden konnte.
- **Update-Sicherheitsnetz (wichtigster Fix).** Startet der Starter (EXE) das
  Programm mit einem Status, der nicht beweist, dass er gerade frisch
  installiert hat („kein Update“, „keine Verbindung“, „Update-Fehler“,
  „Update-Suche-Fehler“), prüft das Programm jetzt selbst kurz gegen
  `version.json` im Repository und zieht ein Update notfalls direkt (kurzes
  Zeitlimit, stilles Scheitern, Neustart mit Hinweisfenster). Grund: Ein
  hängender oder defekter Starter ließ sonst jedes im Repository
  veröffentlichte Fix für immer beim Nutzer nicht ankommen – die plausibelste
  Erklärung dafür, dass mehrere Icon-Reparaturen der letzten Versionen beim
  Nutzer „nie ankamen“.
- Alles Weitere bleibt wie 6.0/6.0.1 (Design, Bedienung, Einstellungen,
  Server, Plugin-Protokolle).

## 6.0.1
- **Spiel-Icons ersetzt durch eine Live-Vorschau.** Statt eines von Roblox
  heruntergeladenen Spiel-Icons (das bei unveröffentlichten Places nie ein
  echtes Bild zeigen konnte, weil `game.GameId` dort 0 ist) macht die Bridge
  jetzt direkt einen Live-Screenshot des jeweiligen Roblox-Studio-Fensters –
  ohne Internetverbindung zu Roblox und unabhängig davon, ob das Place
  veröffentlicht ist. Aufnahmen laufen im Hintergrund (nie auf dem UI-Thread),
  sind pro Sitzung auf höchstens eine alle ~2,5 s gedrosselt und werden sofort
  auf Kachelgröße verkleinert. Ist das Studio-Fenster minimiert, wird die
  Vorschau bewusst nicht aktualisiert – das zuletzt gezeigte Bild bleibt
  stehen. Die „Alle Places“-Sammelzeile zeigt bewusst keine Vorschau.

## 6.0
- **Komplett neues Design: „Liquid Glass“.** Die gesamte Oberfläche ist nach
  dem Entwurf (grafik.png) neu gestaltet: ein tiefblau-violettes Fenster mit
  langsam driftenden Farblichtern (Aurora) hinter durchscheinendem Glas.
  Place-Zeilen sind Teal-Glaskarten, „Prompt kopieren“ und der
  Einstellungs-Knopf sind grüne Glas-Knöpfe, das „…“-Menü ist ein violettes
  Glas-Panel, Minimieren/Schließen sind runde Crimson-Knöpfe. Ein echter
  Rundungs-Beschchnitt sorgt dafür, dass die Farblichter nie über die
  Fensterecken hinausragen.
- **Animationen überall.** Das Fenster wächst beim Öffnen sanft auf;
  Place-Zeilen blenden ein (der bewährte Fade samt Watchdog aus 5.0.2 bleibt),
  heben sich beim Hover um 2 Pixel an und leuchten auf; das „…“-Menü blendet
  ein und gleitet hoch; alle Knöpfe tragen einen weichen Glas-Schein, der beim
  Hover aufleuchtet, und ziehen sich beim Drücken sanft zusammen; Spiel-Icons
  blenden weich ein; die Kopier-Bestätigung gleitet nach oben; An/Aus-Schalter
  (Einstellungen und „…“-Menü) gleiten weich; Verlaufs-Karten blenden ein; der
  Leerzustand schwebt leicht.
- **Auch die weiteren Fenster im neuen Design:** Einstellungen, Update-Hinweis
  und Arena-Verlauf tragen dasselbe Glas-Design mit Aurora-Lichtern und weicher
  Fenster-Einblendung. Der Startbildschirm ist halbtransparent geworden, sodass
  die Farblichter während des Starts hindurchscheinen.
- **Nichts Funktionales hat sich geändert.** Gleiche Knöpfe, gleiches Verhalten
  („…“-Toggle, „Nur Lesezugriff“ lässt das Menü offen, rot/grün-Schalter in den
  Einstellungen, keine Popups unten rechts). Server, Plugin, Tools und alle
  Protokolle sind nicht angefasst.
- Nach dem Update Roblox Studio einmal neu starten, damit das Plugin **6.0**
  geladen wird.

## 5.2
- **„Alle Places“ aufgeräumt.** Die Zeile zeigt jetzt wie alle anderen nur noch „Prompt kopieren“ und „…“. „Token zurücksetzen“ und der Sammelschalter „Nur Lesezugriff“ (wirkt auf alle verbundenen Places) bleiben im „…“-Menü erreichbar.
- **Spiel-Icons repariert.** Die bisherige Adresse des Studio-Ersatzbildes war tot (HTTP-Fehler), Fehlversuche wurden nie wiederholt, und als „Icon“ gecachte Fehlerseiten vergifteten den Cache dauerhaft – deshalb blieben die Rahmen leer. Jetzt: PNG-Signaturprüfung für jeden Download, kaputte Cache-Reste werden verworfen, Fehlversuche wiederholen sich mit ansteigender Pause (45 s …), nach dem dritten Versuch wird ein Ersatz-Icon lokal gezeichnet, und jeder Ladevorgang samt Fehlergrund steht in `runtime.log`. Das „Alle Places“-Mosaik wird nur noch bei echten Änderungen neu gebaut.
- **Arena-Verlauf überarbeitet.** Löschen- und Schließen-Knopf tragen das normale Titelleisten-Design (vorher ungestyltes Windows-Grau). Das Fenster lässt sich an Titelzeile und Hintergrund frei über den Bildschirm schieben; der Verlauf wird währenddessen nicht mehr neu aufgebaut und bei unverändertem Inhalt gar nicht mehr neu gerendert. Jede Aktionskarte ist deutlich flacher. Alle „[PLATZHALTER]“-Stellen zeigen jetzt echte Werte aus den Werkzeug-Ergebnissen (Zeilenzahlen, Kopien, Objekte), und jedes einzelne Werkzeug hat einen eigenen verständlichen deutschen Text. Dazu liefert das Plugin bei `set_script_source` jetzt auch `previousLines` mit.
- **Einstellungen schlanker.** Der Abschnitt „Letzte Arena-Meldung“ ist entfernt; die Fertig-Benachrichtigung (wenn eingeschaltet) bleibt unverändert.
- **„Alle Places“-Prompt kürzer.** Die Zeilen `MODE=ALLE_PLACES` und `HINWEIS=…` sind entfernt – die Mehr-Place-Anleitung bekommt Arena automatisch von der Bridge: Die erste Anfrage mit dem Sammel-Token beantwortet der Server direkt mit Place-Liste und Anleitung (`MULTI_PLACE_SELECTION_REQUIRED`).
- **Place-Liste räumt schneller auf – ohne Geister.** Geschlossene Places verschwinden nach ca. 15 statt 25 Sekunden (sauber abgemeldete nach ca. 4). „Geister-Places“, die unendlich hängen blieben, sind ausgeschlossen: Die Sichtbarkeit hängt nur noch am Presence-Lebenszeichen des Edit-Plugins (vorher reichte ein verklemmter Session-Reporter, der `lastSeen` weiterfütterte). Nach 120 Sekunden ohne Lebenszeichen wird eine Sitzung samt Token und allem Nebenzustand restlos entfernt (vorher 600 s).
- Nach dem Update Roblox Studio einmal neu starten, damit das Plugin **5.2** geladen wird.

## 5.0.2
- **Diagnose statt Rätselraten: Die Place-Liste wird hart überwacht.** Der Bug aus 5.0.0/5.0.1 (Anzahl oben stimmte, darunter blieb die Liste leer) wird nicht mehr geraten, sondern gemessen: Jeder catch-Block der Place-Liste schreibt jetzt Exception-Typ, Meldung, Skriptzeile und Stacktrace in `runtime.log` – vorher stand dort nur die nackte Meldung, die Ursache war damit praktisch verschluckt.
- **Nach jeder eingefügten Zeile misst das Programm den echten Fensterzustand** (Anzahl Kinder, Größe der Liste, Visibility/IsVisible/Höhe/Opacity der Zeile) und protokolliert ihn. Der Log trennt damit sauber die drei Fehlerbilder „Zeile nie gebaut“, „Zeile gebaut aber unsichtbar“ und „Layout ohne Platz“.
- **Sicherheitsnetz:** Icon, Auswahlmenü, Arena-Verlauf und die Einblend-Animation einer Zeile sind einzeln in try/catch gekapselt. Schlägt eines davon fehl, erscheint die Zeile trotzdem mindestens mit Name und „Prompt kopieren“-Knopf. Schlägt die Animation fehl oder startet sie nie, wird die Zeile hart auf sichtbar gestellt (Watchdog nach 1,5 s).
- Auch der Neu-Anordnungs-Block von `Sync-PlaceList` (`Children.Clear()` + neu anordnen) ist gekapselt und loggt Fehler – ein Fehler dort konnte die Liste zuvor spurlos leeren.
- Nach dem Update Roblox Studio einmal neu starten, damit das Plugin **5.0.2** geladen wird.

## 5.0.1
- **Spieleliste wird wieder angezeigt.** Die Anzahl der verbundenen Places oben stimmte, darunter blieb die Liste jedoch immer leer. Grund: `New-PlaceIconVisual` (und das Verlaufsfenster) legten ihr Panel in der Variablen `$host` ab – das ist in PowerShell die schreibgeschützte automatische Host-Variable. Die Zuweisung warf „Cannot overwrite variable Host because it is read-only or constant“, der Fehler wurde von `Sync-PlaceList` abgefangen und geloggt, und keine Zeile wurde je hinzugefügt. Die Panels heißen jetzt `$iconHost`, `$historyHost` bzw. der Parameter `$HostPanel`.
- Dadurch öffnet auch der Arena-Verlauf (pro Place und „Alle Places“) wieder zuverlässig.
- Nach dem Update Roblox Studio einmal neu starten, damit das Plugin **5.0.1** geladen wird.

## 5.0.0
- **Playtest-Steuerung erneut gehärtet.** Vor jedem Test registriert das Edit-Plugin den frischen, kurzlebigen Sitzungsschlüssel bei der Bridge. Ein Schlüssel aus einem älteren Playtest kann `move_character` oder `play_stop` damit nicht mehr mit einer 403-Antwort blockieren.
- **Bewegung und Stop funktionieren über die komplette Sitzung.** Die Session-Reporter senden `Humanoid:Move` über jeden Heartbeat während der gewünschten Dauer statt nur für einen Frame. `play_stop` wartet länger auf `StudioTestService:EndTest` und legt einen erneuten Reporter-Versuch ein, bevor der sichere Edit-Fallback greift.
- **„Alle Places“ ab zwei Verbindungen.** Der Sammel-Prompt besitzt einen pro Programmstart stabilen Token; Place-Zugänge kommen und gehen, ohne ihn zu ändern. Arena ruft `GET /api/places` auf und gibt anschließend für jeden Tool-Aufruf einen eindeutigen `targetPlace` an. Ohne Auswahl verweigert die Bridge die Aktion bewusst, statt ein falsches Spiel zu verändern.
- **Place-Icons und Verlauf.** Die Liste lädt abgerundete Roblox-Game-Icons mit einer Halbkreis-Ladeanimation und einem Roblox-Studio-Fallback für unveröffentlichte Places. Im neuen Verlauf sieht man laufende Aktionen blau, fertige Abfragen grau, Änderungen grün, Konsolenläufe gelb und Fehler mit Warnung rot. Der Verlauf ist pro Place oder gesammelt einsehbar und temporär.
- **Temporärer Lesezugriff.** „Nur Lesezugriff“ ist jetzt ein echter An/Aus-Schalter im Optionsmenü. Die Einstellung wird nicht gespeichert; jede Place-Registrierung beginnt wieder mit Lese- und Schreibzugriff.
- Nach dem Update Roblox Studio einmal neu starten, damit das Plugin **5.0.0** geladen wird.

## 4.0.5
- **Playtest-Stop repariert (echte Ursache, live gemessen).** Ein gestarteter
  Test liess sich nicht mehr automatisch beenden: `play_stop` und
  `move_character` meldeten `REPORTER_NOT_CONNECTED`, obwohl der Testspieler
  samt Charakter sichtbar war, und die Befehle stauten sich in Studio.
- **Der Fehler lag im Bridge-Server, nicht in Roblox.** Verräterischer
  Messwert: `reporterLoopCount` 501 bei `reporterPostFailCount` 500 – die
  Reporter-Schleife lief also einwandfrei, aber nur der allererste Heartbeat
  wurde je beantwortet. Grund: Der Heartbeat-Zustand kommt als
  `PSCustomObject` aus `ConvertFrom-Json`; `Update-PlayStateTracking` wies
  darauf `$newState.userPlaytestActive = …` zu. Auf einem `PSCustomObject`
  wirft das, sobald die Eigenschaft noch nicht existiert – jeder weitere
  Heartbeat endete im 500er-Handler. Dadurch enthielt die Antwort nie das
  Feld `commands`, und der Session-Reporter bekam `end_test` schlicht nie zu
  sehen.
- **Vier Absicherungen:** (1) neuer Setter `Set-StateField` beherrscht
  Hashtable *und* PSCustomObject; (2) der Heartbeat-Handler kapselt die
  Zustands-Übernahme in `try/catch` – Befehle werden ab jetzt **immer**
  zugestellt; (3) `sessionChannelCommand` nutzt den Session-Kanal, sobald ein
  Sitzungsschlüssel existiert (ein veraltetes `agentMode` sperrte vorher den
  einzigen funktionierenden Stop aus); (4) `play_stop` legt als letzte Stufe
  `end_test` fire-and-forget in die Warteschlange – der Reporter muss den
  Befehl nur noch abholen, nicht rechtzeitig beantworten.
- Der Session-Reporter sendet in seinem Snapshot jetzt `running=true` /
  `editModeActive=false` mit, damit der Server einen laufenden Test nicht aus
  einem unvollständigen Heartbeat als beendet verbucht.
- `PLAY_STOP_NEEDS_USER` („Bitte Shift+F5 drücken“) ist damit wieder der
  echte Ausnahmefall statt der Normalzustand.
- Nach diesem Update Roblox Studio einmal neu starten, damit das Plugin 4.0.5
  geladen wird.

## 4.0.4
- Live-Fehleranalyse: Nach dem Stop wurden alte Session-Reporter-Daten im Edit-Status weitergereicht. Aktive Sessions sind jetzt die Voraussetzung für Reporter-Snapshot, Spielerzahl und Agent-Status; EditModeActive=true zeigt wieder zuverlässig einen sauberen Edit-Zustand.
- `reporterSeenInOutput` zählt nur echte `#ARENA#`-Zeilen aus LogService. Der funktionierende Session-Plugin-Kanal wird separat diagnostiziert, statt Output-Zeilen vorzutäuschen.
- Der injizierte No-HTTP-Reporter hat eine fehlertolerante, überwachte Schleife und unterstützt `move_character` als Fallback im Session-DataModel.
- Nach diesem Update Roblox Studio einmal neu starten, damit das Plugin 4.0.4 geladen wird.


## 4.0.0
- Playtest-Rückkanal repariert: Das Plugin verwendet jetzt Roblox `SharedTableRegistry` korrekt und liest Reporter-Snapshots direkt aus der isolierten Test-Session. Dadurch funktionieren Play, `character_state`, Bewegung und Stop auch bei `HttpEnabled=false`, ohne sich auf eine Cross-DataModel-`MessageOut`-Brücke zu verlassen.
- `play_start` meldet erst Erfolg, wenn der Session-Reporter mit Spieler/Charakter erreichbar ist. `play_stop` nutzt bevorzugt `StudioTestService:EndTest` im Session-DataModel und räumt die temporären Reporter zombie-frei auf.
- UI komplett auf Tech-Dark umgestellt: Deep Slate, Neon-Cyan, Indigo und subtile Glassmorphism-Flächen. Einstellungen sind kompakt und enthalten keine langen Switch-Beschreibungen mehr.


> ⚠️ **Nach JEDEM Programm-Update Roblox Studio einmal neu starten**, damit
> das neue Studio-Plugin geladen wird. Die Bridge erkennt veraltete Plugins
> selbst (`pluginVersion` ≠ Programmversion) und meldet es in der
> Programm-Oberfläche sowie über `/api/status` als `versionMismatch`.

### 3.9.8
- **Kritischer Fix – das Autostart-Selbst-Update lud seit 3.9 nie etwas
  herunter.** `Get-RawGitHubText` rief immer
  `[System.Text.Encoding]::UTF8.GetString($response.Content)` auf – aber
  `raw.githubusercontent.com` liefert `text/plain; charset=utf-8`, sodass
  `Invoke-WebRequest` `.Content` bereits als String dekodiert. `GetString()`
  akzeptiert nur Bytes, der Aufruf landete still im `catch` → Rückgabe
  `$null` → „Branch nicht erreichbar“ → es startete immer die lokale
  Fassung (nur im Runtime-Log sichtbar). `Get-RawGitHubText` verarbeitet
  jetzt **beide Rückgabetypen** (Bytes und String) und entfernt ein
  mitdekodiertes BOM-Zeichen (U+FEFF), bevor die Datei mit UTF-8-BOM neu
  geschrieben wird – das verhindert ein doppeltes BOM am Dateianfang.
- **Der Rest der Update-Kette war bereits korrekt und wurde verifiziert:**
  Autostart-Registrierung (HKCU `Run`), Erkennung „Start ohne
  `-UpdateStatus`“, TLS 1.2, Branch-Kette (`update-config.json` → `main` →
  `master`), `[version]`-Vergleich, atomarer `.new`/`.old`-Tausch mit
  Rück-Sicherung, Hinweisfenster mit den Neuigkeiten aus
  `update-status.json` und kein Update-Loop (der neue Prozess bekommt
  `-UpdateStatus update-erfolgreich`).

### 3.9.7
- **Der Playtest-Reporter kommt jetzt garantiert IN der Test-Session an**
  (Live-Befund B1 aus 3.9.6: `reporterActive:false`, null `#ARENA#`-Zeilen –
  die Archivable-false-Injektion plus Sofort-Löschung im Edit-DataModel war
  ein Lösch-Race, der Reporter existierte in der Session nie). Ab jetzt wird
  als **normales, klon-sicheres Script** injiziert (`reporterVariant=2`,
  Standard); die Edit-Kopien werden erst gelöscht, **nachdem**
  `editModeActive=false` den Snapshot bewiesen hat (+1,5 s), plus
  Sicherheits-Sweeps bei `play_stop` und Plugin-Unload – im gespeicherten
  Place landet weiterhin nichts. Variante 1 (Archivable=false-Probe) bleibt
  per `play_start { reporterVariant=1 }` zum empirischen Gegentest erhalten.
- **Injektions-Beweis in Echtzeit.** Der Server-Reporter druckt sofort
  `#ARENA# hello`, der Client-Reporter ebenfalls. `startDiagnostics` enthält
  jetzt `reporterInjected` und `reporterSeenInOutput`; `play_status` zeigt
  die Reporter-Frische (`reporterLastKind`, `reporterLastAgeSeconds`,
  `arenaLineCount`, `reporterVariantUsed`).
- **Stop-Leiter statt Sackgasse** (Live-Befund B2: Sessions aus
  `ExecutePlayModeAsync` ließen sich aus dem Edit-DataModel weder per
  `RunService:Stop()` noch per Shift+F5/VirtualInputManager beenden;
  `StudioTestService:EndTest` funktioniert nur im Session-Server-DataModel).
  `play_stop` versucht jetzt geordnet: **(1)** `end_test`-Befehl an den
  Reporter über den Befehlskanal (s. u.), der die Session selbst per
  `EndTest("stopped_by_arena_bridge")` beendet; **(2)** Fallback
  `RunService:Stop()` aus dem Edit-DataModel; **(3)** sauberer Fehler
  **`PLAY_STOP_NEEDS_USER`** mit deutscher `userMessage` („Bitte in Studio
  Stop drücken (Shift+F5)“) statt Endlosschleife. Nach jedem erfolgreichen
  Stop wird zombie-frei aufgeräumt – ein sofortiger zweiter `play_start`
  klappt wieder.
- **Befehlskanal in die Session – ohne irgendwelche Einstellungen.**
  Priorität: (1) optionaler HTTP-Agent (nur bei `HttpEnabled=true`);
  (2) **SharedTableRegistry** als Cross-DM-Speicher zwischen Edit-Plugin und
  Session-Reporter (volle Argumente + echte Antworten; `session_diag`
  prüft per Live-Echo-Probe, ob die Tabelle wirklich über beide DataModels
  reicht); (3) **VirtualInputManager-Kombos** Strg+Alt+Umschalt+E/R/P auf dem
  Client-Reporter (antwortfrei, für `end_test`/Respawn/Zustand); (4)
  `GetTestArgs` beim (Neu-)Start (`arenaSpawn`). `teleport_character`,
  `respawn_character` und `set_camera` nutzen zur Laufzeit denselben Kanal;
  `move_character`/`gui_click` bleiben echte VIM-Eingaben aus dem Edit-DM.
- **Neues Diagnose-Werkzeug `session_diag`** (read-only): Reporter-Status
  (aktiv, letzte `#ARENA#`-Zeile + Alter, Injektions-Variante in der
  Session), Kanal-Status inkl. SharedTable-Cross-DM-Live-Probe mit Echo,
  Output-Cursor und Fehler-/Warnungszähler. Bei jedem Playtest-Problem zuerst
  `session_diag` und danach `get_output` mit Filter `ARENA` lesen.
- **Alle Play-Werkzeug-Guards kennen jetzt den Sessions-Zustand** (B3/B4):
  gültig bei `editModeActive=false` **oder** `IsRunning()`. Aktive Session
  ohne Reporter beantworten sie mit **`REPORTER_NOT_CONNECTED`** samt
  `sessionDiag`-Daten statt des falschen „No test running“. Auch dauerhafte
  Bearbeitungen werden jetzt bei getrennter Session korrekt blockiert.
- **UTF-8-GET-Dekodierung verifiziert** (Umlaute/Pfeile per GET bleiben
  korrekt, explizite UTF-8-Dekodierung der Roh-Query).

### 3.9.6
- **Playtest ohne Konfiguration – auch bei `HttpEnabled=false`.** Vor jedem
  `play_start` injiziert das Plugin einen temporären Server-Reporter in
  `ServerScriptService` sowie einen Client-Reporter in
  `StarterPlayerScripts`. Beide werden in den Test-Snapshot übernommen,
  sofort wieder aus dem Edit-DataModel entfernt und speichern somit nichts im
  Place. Sie drucken strukturierte `#ARENA#`-JSON-Zeilen über `LogService`:
  echte Spielerzahl, Charakterposition, Gesundheit, Humanoid-Zustand sowie
  GUI-Baum, Bildschirmkoordinaten und Klickziele. Das Edit-Plugin empfängt
  diese Zeilen auch dann, wenn die Test-Session keinerlei HTTP-Fähigkeit hat.
- **Getrennte DataModels richtig erkannt.** In aktuellem Studio bleiben
  `RunService:IsRunning()` und `Players` im Edit-DataModel leer, obwohl eine
  Session läuft. Der einzige Start-/Lauf-Orakel ist deshalb
  `StudioTestService.EditModeActive`: `true → false` innerhalb von 20 Sekunden
  ist Erfolg. Der Service-Fehler „previous one is still in progress“ bedeutet
  bei `EditModeActive=false`, dass eine vorhandene Session weiterverwendet
  wird – nicht, dass der Start fehlgeschlagen ist.
- **Steuerung ohne HTTP.** `character_state` und `play_status` verwenden den
  letzten LogStream-Snapshot (`agentMode: "logStream"`, echte
  `sessionPlayers`). `move_character` sendet echte W/A/S/D-/Shift-Tasten über
  `VirtualInputManager`, `gui_click` echte Mausereignisse an die vom
  Client-Reporter gemeldeten Koordinaten. Teleportieren erfolgt nur vor dem
  Spawn über `play_start { arenaSpawn={x,y,z} }` und `GetTestArgs`; das ersetzt
  den alten Laufzeit-Teleport/Play-Here-Sonderweg.
- **Stop ist kein HTTP-Sonderfall mehr.** `play_stop` ruft standardmäßig
  `RunService:Stop()` aus dem Edit-DataModel auf und wartet auf
  `EditModeActive=true`. Das beendet auch vom Nutzer gestartete getrennte
  Sessions. `PLAY_SERVICE_STUCK` entsteht nur nach einem echten
  Service-Fehler, `EditModeActive=false`, `IsRunning=false` und einem
  erfolglosen Stop-/3-Sekunden-Wiederherstellungsversuch.
- **Belegbare Diagnose und Protokollreparaturen.** `startDiagnostics` bei
  Start/Stop enthält `editModeActiveBefore/After`, den wörtlichen
  Service-Fehler, Pfad, `sessionPlayers`, `reporterActive`, `agentMode` und
  `httpEnabled`. Pending-Befehle nutzen Unix-Zeitstempel, verspätete Ergebnisse
  werden zuverlässig zugestellt, GET-Parameter werden explizit als UTF-8
  dekodiert und gleiche Play-Start/Stop-Retries innerhalb von drei Sekunden
  werden dedupliziert.
- **Versionsschutz.** Bei Plugin-/Bridge-Mismatch zeigt die UI „Studio neu
  starten“, `/api/status` meldet die Abweichung, und der KI-Umschlag enthält
  `plugin outdated - Tests warten`. HTTP bleibt bei aktiviertem HttpEnabled als
  schneller Zusatzpfad erhalten, ist aber niemals eine Voraussetzung.


### 3.9
- **Komplette Steuerung per HTTP GET (wichtigste Neuerung).** Die Bridge lässt
  sich jetzt vollständig über ganz normale GET-Anfragen bedienen – exakt
  gleichwertig zu POST. Hintergrund: Manche KI-Umgebungen dürfen keine direkte
  Verbindung zu `trycloudflare.com` aufbauen und erreichen den Tunnel nur über
  ihren Web-Abruf-Dienst, der ausschließlich GET ohne Datenkörper kann. Neu:
  - `GET /api/tool?token=…&tool=NAME&args=<URL-kodiertes JSON>&timeoutSeconds=N`
  - `GET /api/tools/parallel?token=…&calls=<URL-kodiertes JSON-Array>`
  - `GET /api/upload?token=…&uploadId=…&chunkIndex=N&chunkCount=M&text=<URL-kodiert>`

  Der Server baut aus den Abfrage-Parametern denselben Körper, den ein POST
  geschickt hätte, und schickt ihn durch **denselben Programmpfad**. Dadurch
  sind `_bridge`-Umschlag, `_sessionStart`, Stückelung/Blobs, die
  `SELF_TEST_DISABLED`-Sperre, Play-Absichten und `report_done` identisch.
  Dokumentation, Manifest (Endpunkt-Liste) und die Sitzungsstart-Hinweise sagen
  Arena ausdrücklich, dass sie **ausschließlich über GET** arbeiten kann
- **Kopier-Bestätigung**: Nach „Prompt kopieren“ im „…“-Menü erscheint ein
  dezenter Hinweis im Fenster („Prompt wurde in die Zwischenablage kopiert“),
  der nach wenigen Sekunden von allein ausblendet – kein Popup
- **Autostart sucht selbst nach Updates**: Ist „Beim PC-Start automatisch
  öffnen“ aktiv, startet Windows das Skript ohne den Starter. Die Bridge prüft
  deshalb jetzt selbst: `version.json` von GitHub laden (Branch-Kette
  konfiguriert → `main` → `master`), bei neuerer Version `ArenaBridge.ps1`
  herunterladen, sauber austauschen (`.new`-Datei, alte Instanzen beenden),
  neu starten und das Update-Hinweisfenster zeigen. Netzprobleme blockieren den
  Start **nie** – kurze Zeitlimits, im Zweifel still weiter mit der lokalen
  Fassung

### 3.8
- Große eigenes Einstellungsfenster: alle An/Aus-Optionen sind jetzt echte
  Schalter mit **rot = aus** und **grün = an** statt Kontrollkästchen
- **Alle Einstellungen werden dauerhaft gespeichert** (settings.json):
  Autostart, Selbst-Tests, Fertig-Meldung und auch „Nur Lesezugriff“ je Place
- Neue Einstellung **„Arena darf sich selbst testen“** (Standard: an). Aus:
  Run, Play und Play Here sind für Arena gesperrt – nur die Editor-
  Simulationen bleiben. Arena wird in Doku/Manifest/jeder Antwort informiert,
  dass der Nutzer das bewusst ausgeschaltet hat (SELF_TEST_DISABLED) – es
  hält die Bridge nicht für kaputt
- Neue Einstellung **„Benachrichtigung, wenn Arena fertig ist“** (Standard:
  aus). An: Arena ruft am Ende seiner Arbeit den neuen Befehl `report_done`
  mit einer eigenen deutschen Meldung – der Nutzer bekommt eine echte
  Windows-Benachrichtigung mit eigenem Titel und kurzem Inhalt
- Playtests deutlich zuverlässiger: Start/Stop über den offiziellen
  StudioTestService (neue Studio-API), gestaffelte Stop-Versuche, und der
  alte fehlerhafte Run-Fallback („kein Charakter spawnt“) ist entfernt
- Der Server verfolgt selbst, wer einen Test gestartet hat – merkt sich also
  auch zuverlässig, wenn der **Nutzer** einen Playtest startet/stoppt (selbst
  wenn das Plugin währenddessen neu lädt). Arena sieht bei jedem Aufruf,
  dass ein Test läuft, und kann ihn beenden (play_stop) oder seine Antwort
  beenden und um Ruhe bitten
- Neuer Modus **play_here** (Play Here = Charakter spawnt an der Edit-
  Kamera): wird erkannt und kann von Arena gestartet werden; Run / Play /
  Play Here / Editor-Simulation sind klar in der Doku getrennt
- Nutzer-Aktivität im Studio (Auswahl, Kamera) erreicht Arena als
  user_active-Ereignisse + userWorking-Hinweis

### 3.7
- Neue Anthrazit-/Grau-/Pink-Oberfläche mit stärkeren Kontrasten
- Update-/Willkommensfenster bleibt ohne Zeitlimit offen und startet das
  eigentliche Programm erst nach einem bewussten Klick auf OK
- Aktiver Play-/Run-Test blockiert dauerhafte Bearbeitungen schon in der
  Bridge; Arena erhält eine kritische Stop-Anweisung und bittet den Nutzer,
  den Playtest selbst zu beenden

### 3.6
- Automatische Updates über GitHub (Starter prüft bei jedem Start)
- Update-Fenster mit Neuigkeiten nach jedem Update, Willkommens-Fenster beim
  ersten Start
- Rote „1“ am Einstellungs-Button, wenn die Update-Suche oder das Update
  fehlschlug (Details stehen dann in den Einstellungen)
- Popup-Nachrichten unten rechts entfernt
- Auswahlmenü „…“: erneuter Klick schließt es wieder; „Nur Lesezugriff“
  lässt es offen

### 3.5
- Port-Freigabe repariert (http.sys/PID 4, deutsches netstat)
- Startbildschirm blieb bei abgebrochenem Start unsichtbar – behoben

### 3.4
- Kompletter Startbildschirm mit Ladekreisel und Fortschritts-Anzeige
- Belegten Port automatisch freigeben
- Kreuz oben rechts beendet das Programm garantiert komplett
- Eigenes EXE-Symbol (Logo)

### 3.3
- cloudflared wird vollautomatisch installiert (Download von GitHub,
  Fallback winget)
- EXE-fähig (ps2exe)

### 3.2 / 3.1 / 3.0
- Siehe Kommentarblock am Anfang von `ArenaBridge.ps1`.
