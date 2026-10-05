# Update-Plan 7.2.0

**Stand: umgesetzt (05.10.2026).** Alle sieben Arbeitspakete AP1–AP7 sind auf
dem Branch `arena/01a10aec-arenarobloxbridge` implementiert, je Paket ein
Commit:

| AP | Commit-Inhalt | Zustand |
|---|---|---|
| AP1 | Fundament: `$Shared`-Zustaende, Umschlag-Injektion, Stationen, Kanal-Zaehler, `ack_user_message`/`wait_for_user` | umgesetzt |
| AP2 | Fortschritt: keine erfundene 0 %, keine Verdraengung, invariant geparst, Nachfolger-Aufloesung, `progress-diagnose.txt` | umgesetzt |
| AP3 | Fertig-Meldung: Plattform-Messung, App-Id-Registrierung, `notify.sweep`, Testknopf, ehrliche Antwort, `notify-diagnose.txt` | umgesetzt |
| AP4 | Zwischen-Prompt: Menuepunkt + eigenes Fenster mit ehrlichen Zustaenden, „Laufenden Befehl abbrechen" im Menue | umgesetzt |
| AP5 | `ask_user`-Entscheidungsbaum + `confirm_action` + Fenster am Mauszeiger, Zurueck, Copy-Prompt | umgesetzt |
| AP6 | Qualitaet: `finishScore`/`grade`/`draftRisk`, erklaerte Einfachheit, Bau-Register, `DRAFT_GRADE_RISK` | umgesetzt |
| AP7 | GUI-Vertrag: `codeLayoutReport`, `MONOLITH_RISK`, `uiStructureRules`, `scaffold_ui_scripts` | umgesetzt |

**Abweichungen vom Plan (bewusst und begruendet):**

- **Kein harter Block ab 400 Zeilen.** Der Plan wollte das groesste Skript
  blockieren; ein Block haette auch legitime lange Skripte getroffen und war
  ohne Live-Test nicht abzusichern. Stattdessen: harte Warnung `MONOLITH_RISK`
  mit Zahlen in jeder Antwort plus `scaffold_ui_scripts`. Die Entwurfs-Sperre
  (`DRAFT_GRADE_RISK`) ist dagegen ein harter Block - dort haengt die Qualitaet
  des Ergebnisses direkt daran.
- **Audit-Pflicht als Hinweis, nicht als Block.** `report_done` nennt jedes
  gebaute, aber ungemessene Modell (`buildRegister`/`buildRegisterNote`) und
  verweigert die Arbeit NICHT allein deshalb. Ein harter Zwang haette auch
  einfache, gewollte Bauten blockiert; die Entwurfs-Sperre greift dort, wo eine
  Messung tatsaechlich stattgefunden hat.
- **`build_surface mode='extend'`** aus AP7 wurde nicht umgesetzt (der
  bestehende Builder wird dafuer in Lua umgebaut und braucht einen Live-Test).
  Als 7.2.1 nachziehbar; `uiStructureRules` beschreibt die Regel schon jetzt,
  und der Menuepunkt „Nachricht an Arena senden" erlaubt dem Nutzer, das
  waehrend der Arbeit einzufordern.

Alles Weitere unten ist der Plan, wie er am 05.10.2026 abgestimmt wurde.

# Update-Plan 7.2.x – Arbeitsdokument (Stand 05.10.2026)

Diskussionsgrundlage für das nächste Update der Arena Roblox Bridge.

## Fest entschieden (05.10.2026, vom Owner)

| # | Entscheidung |
|---|---|
| D1 | **Ein großes Release 7.2.0** mit allen fünf Themen – keine Aufteilung in 7.2/7.3/7.4/7.5 |
| D2 | **Ein neues Bridge-Fenster (Popup) ist erlaubt.** Die alte Regel bezog sich auf die hässlichen Toasts ab Version 3, nicht auf eigene Fenster. Die feste Regel in `GANZ WICHTIG…` wird entsprechend präzisiert |
| D3 | **`ask_user` muss verzweigte Fragen können** – nicht nur Frage 1/2/3 hintereinander, sondern „wenn Frage 1 so beantwortet wird, dann Frage 2", beliebig tief (Entscheidungsbaum) |
| D4 | **Kein neuer Benachrichtigungskanal.** Es bleibt beim Windows-Toast – aber verifiziert, diagnostiziert, mit Testknopf, Wächter und ehrlichem `delivered` statt stiller Erfolgsmeldung |
| D5 | **Fortschritt ohne Prozentzahl: Warnung an die KI verschärfen und den Balken erst gar nicht anzeigen** – keine erfundene 0 %, kein pulsierender Ersatz |
| D6 | Konkret zu D5: **Textzeile ohne Balken und ohne Zahl** (`Arena arbeitet · build_polygon_model · vor 3 s`) – die Zeile bleibt sichtbar, es wird nur nichts erfunden |
| D7 | **Der Fortschritt darf nicht mehr verdrängt werden.** Heute ersetzt ein offener Studio-Befehl Balken + „Arena arbeitet gerade…" durch `Befehl: <tool> - <status> seit X s` **plus Abbrechen-Knopf** (`ArenaBridge.ps1:23100-23121`). Das kommt weg: Balken/Text bleiben immer, Befehlsinfo wandert in den Tooltip, Abbrechen ins „…“-Menü |
| D8 | **Zwischen-Prompt über das „…“-Menü** (kein Eingabefeld in der Zeile) **mit eigenem Fenster** und ehrlichen Zuständen: `wird gesendet` + **Abbrechen** → `bei der nächsten Arena-Anfrage mitgesendet` → `angekommen – du kannst das Fenster jetzt schließen` |
| D9 | **Kein AP0 (CI/Parse-Gate), keine AP8-Extras** in 7.2.0 – Umfang ist genau: Fundament + deine fünf Themen |

Ausgangspunkt: `main` @ `f7416aa` (Version **7.1.5**), alle 7 Offline-Regressionen
grün (Struktur, 7.1.0/7.1.1-Zustellung, 7.1.2-Toolbox, 7.1.3-Qualität,
7.1.4-Organic, 7.0.7-Wächter).

Dieses Dokument ist bewusst **kein** Changelog: es nennt zu jedem Thema den
Befund mit Belegstelle im Quellcode, die Ursache, den Vorschlag, das Risiko und
die Abnahme. Entschieden wird gemeinsam – die offenen Punkte stehen ganz unten.

---

## Thema 1 – „Immer mit Qualität arbeiten"

### Befund (belegt, nicht vermutet)

Die Qualitätssicherung aus 7.1.3/7.1.4 hat **drei Lücken**, und dein
Baum-Beispiel fällt exakt durch alle drei:

1. **Die Primitiv-Erkennung ist zu grob.** `model_audit` markiert eine Gruppe
   nur dann als `primitiveOnly`, wenn
   `parts >= 6 AND sphereCount >= 6 AND sphereCount >= 0.5*parts AND solid == 0`
   gilt (`ArenaBridge.ps1:11146-11148`).
   Dein Beispiel – *1 Cylinder Stamm + 1 Cylinder Ast + 3 Bälle* – hat
   **5 Teile** und **3 Kugeln**: beide Schwellen werden verfehlt, das Audit
   meldet `verdict = "clean"`. Die Regel fängt große Kugelhaufen (das
   7.1.3-Katzen-Tier), aber keinen kleinen Pfusch.
2. **Die Sperre ist freiwillig.** `report_done` prüft `primitiveAbuse` /
   `cylinderProblemCount` **nur**, wenn für die Sitzung ein Audit-Eintrag in
   `$Shared.AuditFlags` liegt (`ArenaBridge.ps1:18828`). Ruft die KI
   `model_audit` gar nicht auf, gibt es gar keine Qualitätsprüfung – der
   „fail-closed"-Pfad greift nur beim Organic-Vertrag, nicht beim allgemeinen.
3. **Der harte Vertrag gilt nur für `organic=true`.** Die frischen
   per-Modell-Belege (`ORGANIC_AUDIT_REQUIRED`, `ArenaBridge.ps1:18887 ff.`)
   hängen an `$Shared.OrganicBuilds`. Ein Baum, den die KI nicht als organisch
   deklariert, braucht überhaupt keinen Nachweis.

Dazu: `buildQuality` misst heute **negativ** („ist es ein Kugelhaufen?") statt
**positiv** („hat es Silhouette, Sekundärstruktur, Details, Palette?"). Der
Finish-Standard aus `modelBuildRules` ist Prosa in der Session-Antwort – er wird
nicht gemessen und hat deshalb keine Konsequenz.

### Vorschlag

**A. Build-Register (automatisch, nicht freiwillig).**
Jeder erfolgreiche Schreibaufruf, der Geometrie anlegt oder ändert
(`build_polygon_model`, `build_assembly`, `create_instance`/`bulk_create` mit
Part-/Mesh-Klassen, `insert_asset`, `run_lua` mit Part-Erzeugung), registriert
das Zielmodell mit `path`, `id`, `kind`, `lastWriteAtTicks` – genau die
Struktur, die `OrganicBuilds` heute schon hat. Verallgemeinert zu
`$Shared.SessionBuilds`.

**B. Audit-Pflicht für jedes registrierte Build.**
`report_done` antwortet `BUILD_AUDIT_REQUIRED`, wenn ein registriertes Build
kein frisches `model_audit` **nach** dem letzten Schreibaufruf hat. Dieselbe
Frische-Logik wie beim Organic-Vertrag, nur für alle Builds. Damit ist die
Qualitätsprüfung nicht mehr freiwillig.

**C. Finish-Score statt Kugel-Heuristik (positiv messen).**
`buildQuality` bekommt pro Gruppe/Modell:
`partCount`, `polygonTriangles`, `meshCount`, `unionCount`, `detailParts`
(ArenaDetail), `shapeVariety`, `primitiveShare`, `uniqueColors`, `motionScripts`
und daraus `finishScore` (0..1) plus `grade`:

| Grad | Bedingung (gemessen) | Konsequenz |
|---|---|---|
| `draft` | ≤ 12 Teile **und** keine Polygon-/Mesh-/Union-/Detailgeometrie **und** `primitiveShare > 0.6` | `report_done` → `DRAFT_BUILD` |
| `model` | Silhouette aus Polygon/Mesh **oder** ≥ 3 Formfamilien, ≥ 2 Farben | ok |
| `refined` / `polished` | zusätzlich Details bzw. Licht/Atmosphäre | ok |

Dein 5-Teile-Baum landet damit sicher in `draft` – ohne dass die Regel
Modellnamen kennt.

**D. Deklarierte Einfachheit als ehrlicher Ausweg.**
Nicht jedes Objekt darf ein Modell sein müssen (Kiste, Laternenpfahl,
Low-Poly-Fels auf ausdrücklichen Wunsch). Deshalb: beim Bauen kann
`grade = 'simple' | 'lowpoly' | 'blockout'` **deklariert** werden. Dann ist es
erlaubt, wird aber (i) im Arena-Verlauf sichtbar als „einfach (deklariert)"
geführt und (ii) in der Place-Zeile gezählt. Raten durch Namen bleibt verboten –
es ist eine ausdrückliche Ansage, keine Heuristik. `handoff` bleibt der zweite
Ausweg.

**E. Shift-left statt End-Sperre.**
Die Korrektur muss **im selben Response** kommen, in dem der Fehler passiert –
nicht erst bei `report_done`. Jeder Schreibaufruf, der ein `draft`-Build anlegt,
antwortet sofort mit `qualityWarning: DRAFT_GRADE_RISK` + der konkreten Regel +
dem Verweis auf `build_polygon_model` und die `cylinderBetween`-Referenz.
(Der Mechanismus existiert schon: `_bridge.buildQuality` wird heute bereits in
Antworten mitgeführt, `ArenaBridge.ps1:18671`.)

**F. Qualität by construction (optional, aber der eigentliche Hebel).**
Streuung („mal top, mal drei Bälle") bekämpft man am zuverlässigsten, indem die
Engine die schweren Fälle selbst besitzt – wie sie es bei `build_polygon_model`,
`ui_glow` und `ui_radial` schon tut. Vorschlag: `build_flora`
(Baum/Busch/Blume/Pilz: Stamm mit Taper, rekursive Äste, Blattcluster,
Farbvariation, seed-deterministisch, `variation`-kompatibel) und
`build_creature_rig` (Silhouette + Gelenke + Muskel-/Fellschicht als Gerüst,
das die KI dann ausarbeitet). Beide liefern `finishScore >= model` per
Konstruktion.

### Risiko / Aufwand

C+B sind der Kern und mittelgroß (Lua-Messung + PowerShell-Gate + Tests).
A ist klein, weil `OrganicBuilds` die Vorlage liefert. F ist groß
(neue Lua-Generatoren) und sollte ein eigener Schritt sein.
Falsch-Positiv-Risiko bei C: wird über D (Deklaration) und über die Schwelle
„keine Polygon-/Mesh-/Detailgeometrie" abgefangen – ein Modell mit echten
Wedges kann nie `draft` werden.

---

## Thema 2 – GUI wirklich in StarterGui, viele kleine Skripte

### Befund

- Es gibt **kein einziges Maß** für Skriptstruktur im ganzen Programm: keine
  Zeilenzählung, keine `Instance.new`-Zählung, keine Prüfung, ob eine GUI zur
  Editierzeit echte Kinder hat. `ui_audit` misst ausschließlich Optik
  (Kontrast, Anker, Geräte, Blandness – `ArenaBridge.ps1:17420`).
- `uiEngineRules` regeln sehr detailliert, **wie eine Oberfläche aussehen
  muss**, aber nicht, **wo Struktur lebt** und **wie Logik aufgeteilt wird**.
- Die Werkzeuge dafür wären da: `build_surface` kann in jedes `parentRef`
  bauen, `bulk_insert_scripts` legt mehrere Skripte an, `patch_script` ist das
  Standardwerkzeug für punktuelle Änderung. Es fehlt die Regel + die Messung +
  die Konsequenz – also genau das Muster, das bei 3D seit 7.1.3 funktioniert.

### Vorschlag – „GUI-Vertrag" (`uiStructureRules`), Spiegelbild des Organic-Vertrags

**Regel 1 – Struktur ist Instanz, nicht Code.**
Der sichtbare Aufbau einer GUI lebt als echte Instanzen in `StarterGui`
(ScreenGui → Frames/TextLabels/TextButtons/ImageLabels + UICorner/UIStroke/
UIGradient/UIPadding/Layouts). Skripte machen Verhalten, Zustand und
Choreografie – sie **erzeugen keine Struktur**. Laufzeit-`Instance.new` ist
erlaubt für genau zwei Fälle: (a) Klonen eines vorhandenen Item-Templates für
dynamische Listen, (b) Elemente, die es zur Editierzeit prinzipiell nicht geben
kann (z. B. schwebende Tooltip-Instanz). Beides muss im Skript kommentiert sein.

**Regel 2 – Ein System = ein Skript.**
Pro Verantwortung ein eigenes Skript mit sprechendem Namen
(`ShopOpen.client`, `ShopItems.client`, `ShopEffects.client`), gemeinsame Logik
als `ModuleScript` (`ShopConfig`, `ShopService`) statt Copy-Paste. Harte Grenzen:
**Warnung ab 250 Zeilen, Sperre ab 400 Zeilen** pro Skript und
**≥ 15 `Instance.new(` in einem GUI-Skript = Struktur-im-Code-Verdacht**.

**Regel 3 – Bestehende GUIs werden erweitert, nicht umgebaut.**
Wenn der Nutzer eine GUI in `StarterGui` hat, wird **in diesem Baum**
weitergearbeitet (`build_surface { parentRef = <bestehender Frame> }`,
`create_instance`, `set_property`, `patch_script`). Die bestehende GUI
stehen zu lassen und daneben einen 10k-Zeilen-LocalScript zu stellen, der alles
zur Laufzeit nachbaut, ist der konkrete Fehlerfall – und wird gemessen.

**Messung – `codeLayout` in `ui_audit` (oder eigenes `ui_structure_audit`):**
pro ScreenGui: `structuralInstances`, `depth`, `scripts: [{ name, runContext,
lines, instanceNewCount, createsStructure, parentIsGui }]`,
`editTimeChildCount`, `runtimeBuiltShare`, `longestScript`,
`verdict: structured | runtime_built | monolith`, `issues[]`.

**Konsequenz – `report_done`:** `UI_STRUCTURE_REQUIRED`, wenn
`verdict = monolith` (ein Skript > 400 Zeilen **und** ≥ 15 `Instance.new`
**und** die GUI < 5 Kinder zur Editierzeit hat). Ausweg: aufteilen oder ehrlich
`handoff`.

**Werkzeug, das es richtig macht – `scaffold_ui_scripts`:**
`{ screenGui, systems: ['Open','Items','Effects'] }` erzeugt engine-owned die
kleinen LocalScripts + ein gemeinsames ModuleScript mit korrektem Header,
`require`-Pfaden und klarer Schnittstelle. Die KI füllt danach Verhalten mit
`patch_script` – Struktur kommt nie wieder aus `Instance.new`.
Zusätzlich: `build_surface`/`build_interface` bekommen einen
**`mode = 'extend'`** mit `targetRef`, damit „GUI weiterdesignen" ein
Erstklass-Werkzeug ist.

**Shift-left:** `insert_script` / `set_script_source` antworten bei
> 400 Zeilen oder ≥ 15 `Instance.new` sofort mit `codeSmell: MONOLITH_RISK`
+ Regel + Aufteilungsvorschlag – im selben Response.

---

## Thema 3 – Zwischennachricht an die KI („halt, mach das anders")

### Technischer Rahmen (wichtig, ehrlich)

Die Bridge kann **nicht** in den Arena-Chat hineinschreiben – es gibt keinen
Push-Kanal zur KI. Die KI holt sich alles über HTTP ab. Deshalb ist der einzig
zuverlässige Weg: **jede Antwort trägt die Nachricht mit**. Genau dafür gibt es
den Umschlag `New-Envelope` (`ArenaBridge.ps1:18528`), der ohnehin in jeder
Antwort hängt.

Konsequenz, die man wissen muss: Die Nachricht kommt **beim nächsten
Bridge-Aufruf** an. Arbeitet die KI gerade 40 s in einem Studio-Befehl, kommt
sie danach; denkt sie gerade ohne Aufruf, kommt sie beim nächsten Aufruf.
Typische Latenz in einer aktiven Bauphase: unter 5 s (im 7.1.4-Log folgt ein
Aufruf meist im 1–5-s-Takt).

### Vorschlag

1. **Einstieg über das „…“-Menü (D8), nicht über ein Feld in der Zeile.**
   Neuer Menüpunkt **„Nachricht an Arena senden"** unter den bestehenden
   (`Prompt kopieren`, `Token zurücksetzen`, `Nur Lesezugriff`,
   `Arena-Verlauf anzeigen`) – gleicher Look über `New-MenuRow`, kein neues
   Design. Die Zeile selbst bleibt unverändert aufgeräumt.
2. **Eigenes Nachricht-Fenster mit ehrlichem Zustand (D8).** Aufbau wie das
   bestehende Handoff-/Einstellungen-Fenster (Border + Grid, Anthrazit/Pink),
   aber klein und ohne Taskbar-Eintrag:
   - Eingabefeld (mehrzeilig) + **„Senden"** + **„Abbrechen"**.
   - Nach dem Senden: Statuszeile **„wird gesendet – bei der nächsten
     Arena-Anfrage wird deine Nachricht mitgeschickt"**, dazu ein laufender
     Sekundenanzeiger. **„Abbrechen"** ist in diesem Zustand scharf und nimmt
     die Nachricht **wirklich** aus der Queue zurück (`ZURUECKGEZOGEN`), weil sie
     technisch noch nicht weg ist.
   - Sobald eine Arena-Anfrage die Nachricht mitgenommen hat: **„angekommen –
     du kannst das Fenster jetzt schließen"** (mit Uhrzeit und Werkzeugnamen des
     Aufrufs, der sie abgeholt hat). Ab hier ist Zurückziehen ehrlich
     ausgeschlossen – der Knopf wird zu „Schließen".
   - Ruft die KI `ack_user_message` auf: **„von Arena bestätigt"** + ihre
     Kurzantwort, falls sie eine mitgibt.
   - Funkstille > 3 min: **„Arena hat seit X keine Anfrage gestellt – die
     Nachricht liegt bereit"** (kein vorgetäuschter Erfolg).
3. **Zustellung:** `$Shared.UserMessages[sessionId]` als Queue mit
   `{ id, text, kind, createdAt, deliveredAt, ackAt, attempts, state }`.
   `New-Envelope` hängt `_bridge.userMessages` (max. 3, älteste zuerst) **und**
   `_bridge.userMessageContract` an: *„Das ist eine Anweisung des Nutzers mitten
   in der Arbeit. Höre sofort auf, den bisherigen Plan abzuarbeiten, setze diese
   Anweisung um, bestätige mit `ack_user_message` und sage dem Nutzer in deiner
   Antwort, was du änderst."*
4. **Zustellgarantie:** at-least-once. Eine Nachricht wird bis zu 3 Antworten
   lang wiederholt, bis die KI `ack_user_message { id }` aufruft (billiges
   Server-Tool, kein Studio-Umlauf). Bleibt die Bestätigung aus, steht im Fenster
   und in der Zeile ehrlich „angekommen, nicht bestätigt".
5. **Harte Bremse bleibt das, was es schon gibt:** der Menüpunkt
   **„Nur Lesezugriff"** (`Set-SessionMode`, `ArenaBridge.ps1:21509`). Kein neuer
   Stopp-Knopf in der Zeile – der würde genau das verdrängen, was D7 schützen
   soll. Wer wirklich anhalten will, schaltet auf Nur-Lesen; der Umschlag sagt
   der KI dann `WRITE_LOCKED_BY_USER` und warum.
   Zusätzlich ins „…“-Menü: **„Laufenden Befehl abbrechen"** (nutzt das
   vorhandene `Invoke-PlaceRowCancel`, `ArenaBridge.ps1:23015`) – als Menüpunkt
   statt als Knopf, der den Fortschritt ersetzt.
6. **`wait_for_user { maxSeconds }`:** blockierendes Server-Tool (wartet auf ein
   `ManualResetEvent`, max. 50 s wegen der HTTP-Grenze), damit die KI an einer
   Entscheidungsstelle aktiv auf den Nutzer warten kann. Dieselbe Infrastruktur
   wie Thema 5 – und der Weg, auf dem deine Nachricht die KI **sofort** erreicht,
   wenn sie gerade wartet, statt erst beim nächsten Aufruf.
7. **Sichtbarkeit in der Zeile (dezent):** ein kleines Zählzeichen
   „2 Nachrichten übermittelt · zuletzt 14:32" als Text im Tooltip/Untertitel –
   kein eigenes Bedienelement, das den Fortschritt verdrängt.

### Risiko

Klein. Der Eingriff in `New-Envelope` ist zentral – hier muss der
Strukturtest wachen, dass der Umschlag bei leerer Queue **byte-identisch** zum
heutigen bleibt (keine neue Nutzlast, keine neuen Ablehnungen wegen Größe).

---

## Thema 4 – Fortschritt bleibt bei 0 % und Benachrichtigungen kommen nicht an

Das ist der Punkt, bei dem ich am meisten gefunden habe – und beides hat eine
**gemeinsame Wurzel**: beide Systeme hängen vollständig davon ab, was die KI
freiwillig meldet, und **beide behaupten Erfolg, ohne ihn zu messen**.

### Befund Fortschritt

1. **Prozent kommt nur, wenn die KI eine Zahl schickt.**
   `Update-ArenaProgressState` setzt `percent` ausschließlich bei
   `$reported = true` (`ArenaBridge.ps1:13256 ff.`). Der Vertrag im Umschlag
   sagt wörtlich: *„Missing percent = 0, never an error."*
   (`ArenaBridge.ps1:18548`) – die KI darf die Zahl also weglassen, und dann
   steht der Balken auf 0 %.
2. **Dein 7.1.4-Log beweist den Fall:** dort sind Dutzende
   `Ereignis [progress] …`-Zeilen mit **Text**, aber das Protokoll enthält
   **keine einzige Prozentangabe** – Prozent wird nirgends geloggt. Der Balken
   hat also eine Nachricht, aber keine Zahl: exakt „grau/blau, korrekt, aber 0 %".
3. **Die Nachricht ist unsichtbar.** `Update-PlaceProgressVisual` zeigt
   `Prozent % • Arena arbeitet gerade...` und steckt die echte Nachricht der KI
   nur in den **Tooltip** (`ArenaBridge.ps1:23083 ff.`). Du siehst also 0 % und
   einen Standardtext, obwohl die KI „Die Waldlichtung mit Pfad, Moos, Felsen …"
   gemeldet hat.
4. **Zwei kleinere echte Fehler:**
   - `Clamp-ProgressPercent` nutzt `[double]$value` (`:13236`) – unter
     deutscher Kultur wird aus dem String `"45.5"` die Zahl `455` → 100 %.
     (Zahlen aus JSON sind sicher, Strings nicht.) → invariant parsen.
   - `Get-ProgressStateSnapshot` liest die **rohe** `sessionId`, während der
     offene Befehl über `Get-UiDeliverySession` (Nachfolger-Auflösung) geholt
     wird (`:23083` vs. `:23088`). Nach einer Sitzungsübergabe zeigt die Zeile
     deshalb den Fortschritt der alten Sitzung = 0 %.

### Befund Benachrichtigung

1. **„angezeigt" wird nicht gemessen.** `Show-ArenaDoneNotification` setzt
   `$shown = $true` **direkt nach** `Show($toast)` (`ArenaBridge.ps1:26624 ff.`).
   Ob Windows die Meldung wirklich gezeichnet hat, prüft niemand.
2. **Dein Log beweist genau das:** `runtimelog V.7.1.4`, Zeilen **3986** und
   **5172**: „Arena-Fertig-Meldung angezeigt: …". Die Bridge war also überzeugt,
   du hast nichts gesehen. Damit ist der Fehler nicht „die KI hat nicht
   gesendet", sondern „Windows hat verworfen und die Bridge hat es nicht
   gemerkt".
3. **`report_done` lügt nach oben:** die Antwort enthält
   `delivered = $true` (`:19069`) – die KI darf dir also wahrheitsgemäß
   versichern, sie habe benachrichtigt, obwohl nichts sichtbar war.
4. **Bekannte stille Verwerfer auf Windows-Seite:** Benachrichtigungen für die
   App-Id „Windows PowerShell" sind ausgeschaltet (die Bridge toastet unter
   dieser AUMID), „Nicht stören" ist an – Windows 11 schaltet es **automatisch
   bei Vollbild-/Spiel-Apps**, also gern mitten im Playtest –, oder die
   Systemlautstärke/App-Priorität. Alles Fälle ohne Exception.
5. **Zweite Falle:** `notifyOnDone` ist standardmäßig **AUS**. Dann antwortet
   `report_done` mit `NOTIFICATIONS_DISABLED` und dem Hinweis „Nothing is
   wrong – simply finish your answer normally". Die KI beendet also sauber und
   sagt dir auf Nachfrage „ich habe es gemeldet". Aus deiner Sicht: kommt nie an.

### Gemeinsame Wurzel

Beide Systeme haben **keinen Beleg** und **keinen Wächter**. Die Vorschau-Kachel
hatte dasselbe Problem – und wurde in 6.0.4/6.0.5 mit genau dem Muster gelöst,
das wir jetzt brauchen: Stationen im Log, Selbsttest, Wächter nach 400 ms,
kleine Diagnose-Datei. Dasselbe Muster auf Fortschritt und Meldung anwenden.

### Vorschlag

**Fortschritt (nach D5: keine erfundene Zahl, lieber gar kein Balken)**

1. **Der Balken erscheint nur, wenn eine echte Zahl da ist (D5/D6).** Zustände:
   `percent` (von der KI gemeldet) → Balken + Zahl wie heute.
   `unknown` (keine Zahl gemeldet, aber messbar Arbeit) → **kein Balken, keine
   0 %**; die Zeile zeigt nur den Klartext `Arena arbeitet · <Tool> · vor 3 s`.
   `waiting` (60 s Funkstille) → grau, wie heute. `done` → 100 %, wie heute.
   Damit ist die 0 % ab jetzt *unmöglich*, statt nur seltener.
1b. **Der Fortschritt wird nicht mehr verdrängt (D7).** `Update-PlaceProgressVisual`
   hat heute einen eigenen Zweig für offene Befehle: `$Row.ProgressBar.Visibility
   = 'Collapsed'`, stattdessen `Befehl: <tool> - <status> seit X s` und ein
   sichtbarer Abbrechen-Knopf (`:23100-23121`). Genau das ist dein „der schöne
   Balken wird durch irgendeine Abbrechen-Taste ersetzt". Neu: Balken/Text
   bleiben **immer** der Hauptinhalt der Zeile; der offene Befehl erscheint als
   Zusatzinformation im Tooltip (und im „…“-Menü als
   „Laufenden Befehl abbrechen"), niemals anstelle des Fortschritts.
2. **Vertrag verschärfen (die eigentliche Ursache):** „Missing percent = 0,
   never an error" (`:18548`) wird ersetzt durch „**percent wird erwartet**;
   fehlt er, zeigt der Nutzer keinen Balken und jede Antwort meldet
   `PERCENT_MISSING`". Die Warnung kommt als eigenes Feld im Umschlag – in
   **jeder** Antwort, bis die KI eine Zahl liefert, plus Zähler
   `callsWithoutProgress`. Das ist derselbe Nudge-Mechanismus, der bei
   `buildQuality` schon funktioniert.
3. **Optional Plan-Prozent:** `plan { steps: [...] }` + `plan_step { index }`,
   damit die Bridge Prozent selbst rechnen kann (erledigt/gesamt, monoton).
   Kostet die KI einen Aufruf zu Beginn und macht den Balken unabhängig davon,
   ob sie bei jedem Call an die Zahl denkt. (Klein, kann im selben Release
   mitziehen – ist aber kein Muss.)
4. **Nachricht sichtbar:** die Meldung der KI steht als Text in der Zeile
   (gekürzt, Volltext im Tooltip) statt nur im Tooltip.
5. **Stationen + Diagnose:** `PROGRESS [p-N] REPORTED → STORED → UI_READ →
   UI_PAINTED` (je Zeile sid/percent/state/tool/alter) und eine kleine
   `progress-diagnose.txt` nach dem Vorbild von `preview-diagnose.txt` –
   vollständig weitergebbar, ohne die große `runtime.log`. Ohne diese Zeilen
   war dein „bleibt bei 0 %" nicht beweisbar; ab 7.2.0 ist es zwei Zeilen Log.
6. **Zwei echte Nebenfehler:** Nachfolger-Auflösung auch für den Fortschritt
   (`Get-UiDeliverySession`, heute liest `:23083` die rohe `sessionId`) und
   **invariantes Parsen** in `Clamp-ProgressPercent` (`:13236`, deutsche Kultur
   macht aus `"45.5"` sonst 455 → 100 %).

**Benachrichtigung**

7. **Kein neuer Kanal (D4) – der Windows-Toast wird vermessen statt behauptet.**
   `$shown = $true` direkt nach `Show($toast)` (`:26624`) ist der Kernfehler:
   die Bridge glaubt sich selbst. Ab 7.2.0 gibt es eine
   **Plattform-Vorprüfung** `Test-NotifyPlatform` mit Stationen im Log
   (`NOTIFY [n-N] ENQUEUED → DEQUEUED → PLATFORM_CHECK → TOAST_CALL →
   VERDICT`), und das Urteil ist eines von:
   `SHOWN`, `SUPPRESSED_APP_DISABLED`, `SUPPRESSED_QUIET_HOURS`,
   `SUPPRESSED_FULLSCREEN_RULE`, `AUMID_UNREGISTERED`, `CALL_FAILED (Exception)`.
8. **Plattform-Diagnose, die den Grund wirklich kennt:** gelesen werden
   `HKCU\Software\Microsoft\Windows\CurrentVersion\Notifications\Settings\<AUMID>`
   (`Enabled` = 0 → App-Benachrichtigungen für „Windows PowerShell" aus),
   die globalen Benachrichtigungs-/„Nicht stören"-Einstellungen und die
   Vollbild-Automatik. Ergebnis steht in den Einstellungen unter
   „UPDATES - PROBLEM"-Artigem Klartext: **„Deine Meldung würde aktuell von
   Windows verworfen, weil …"** plus dem Weg zum Ausschalter.
9. **Knopf „Benachrichtigung testen"** in den Einstellungen, direkt neben dem
   bestehenden Schalter (der bleibt exakt dort, wo er ist): sendet eine
   Testmeldung, zeigt die gemessene Vorprüfung **und** fragt mit zwei Knöpfen
   „Gesehen? Ja / Nein". Bei „Nein" trotz `SHOWN`-Prognose nennt das Fenster die
   verbleibenden Verdächtigen. Das beendet das Raten – ohne neuen Popup-Kanal.
10. **`report_done` wird ehrlich:** statt `delivered = $true` (`:19069`) ein
    gemessenes `{ notification: { platformCheck, state, reason,
    userWillSeeIt: true|false } }`. Ist `userWillSeeIt` falsch → Code
    `NOTIFICATION_UNVERIFIED` mit der Pflicht, dir **zu sagen**, dass die
    Meldung nicht sichtbar ankommt, statt „ich habe benachrichtigt".
11. **Wächter `notify.sweep`:** meldet im Log, wenn eine Meldung länger als 10 s
    in der Queue liegt oder ohne Urteil verworfen wurde (Muster: `queue.sweep`).
    Dazu Zähler im Status (`notify.enqueued/shown/suppressed/failed`) – damit
    „kam nicht an" beim nächsten Mal eine Zahl hat und keine Vermutung ist.
12. **`NOTIFICATIONS_DISABLED` entschärfen:** die Antwort nennt den exakten Weg
    (Einstellungen → Schalter „Benachrichtigung, wenn Arena fertig ist") und die
    KI muss dir sagen, dass die Meldung ausgeschaltet ist – statt „Nothing is
    wrong". Ergänzend zeigt die Einstellungszeile neben dem Schalter den
    Status: `AUS – Arena kann dich nicht benachrichtigen`.

### Was ich von dir brauche

Für den Fall, in dem **beide** Systeme gleichzeitig hingen: die
`runtime.log`-Zeilen dieser Sitzung (oder ab 7.2.x einfach die beiden
Diagnose-Dateien). Im vorliegenden 7.1.4-Log ist der Fortschritt aktiv und die
Meldung wurde zweimal „angezeigt" – den Gleichzeit-Ausfall kann ich darin nicht
sehen. Mit den Stationen ist er beim nächsten Mal in zwei Zeilen bewiesen.

---

## Thema 5 – Fragen über die Bridge (Fenster am Mauszeiger)

### Harte Randbedingung

Eine HTTP-Anfrage darf nicht länger als **55 s (max. 85 s)** warten, sonst
schneidet Cloudflare mit 524 ab (`ArenaBridge.ps1:20037`). „Sleep-Modus" muss
also **wiederaufnehmbar** sein: die KI stellt die Frage, wartet ~50 s, bekommt
`state: waiting` und ruft erneut auf – von außen sieht das wie Schlafen aus,
technisch ist es ein Long-Poll in Runden.

### Vorschlag – `ask_user` mit Entscheidungsbaum (D3)

**Der Aufruf trägt den ganzen Baum in EINER Anfrage.** Das ist der wichtigste
Entwurfspunkt: Verzweigung darf **keinen** zusätzlichen HTTP-Umlauf kosten, weil
jede Runde an der 55/85-s-Grenze nagt. Die KI liefert alle Fragen und ihre
Bedingungen mit, das Fenster läuft den Baum **lokal** ab und schickt am Ende alle
Antworten in einem Paket zurück.

```json
{ "tool": "ask_user",
  "args": {
    "title": "Shop-GUI",
    "timeoutSeconds": 240,
    "questions": [
      { "id": "art", "text": "Was soll ich mit dem Shop-GUI machen?",
        "options": [ { "id": "neu",  "label": "Neu bauen" },
                     { "id": "umbau","label": "Bestehendes umbauen" },
                     { "id": "logik","label": "Nur Logik/Skripte" } ] },

      { "id": "stil", "text": "Welche Kunstrichtung?",
        "when": [ { "questionId": "art", "anyOf": ["neu", "umbau"] } ],
        "options": [ { "id": "sticker", "label": "Sticker" },
                     { "id": "glass",   "label": "Glass" },
                     { "id": "arcade",  "label": "Arcade" } ],
        "allowCustomResponse": true },

      { "id": "umfang", "text": "Wie viele Oberflächen?",
        "when": [ { "questionId": "art", "anyOf": ["neu"] } ],
        "options": [ { "id": "eine", "label": "Eine" },
                     { "id": "bis5", "label": "2-5" } ] },

      { "id": "mobile", "text": "Auch für Handy optimieren?",
        "when": [ { "questionId": "umfang", "anyOf": ["bis5"] } ],
        "options": [ { "id": "ja", "label": "Ja" }, { "id": "nein", "label": "Nein" } ] },

      { "id": "bestand", "text": "Was darf ich am bestehenden GUI ändern?",
        "when": [ { "questionId": "art", "anyOf": ["umbau"] } ],
        "options": [ { "id": "alles", "label": "Alles umbauen" },
                     { "id": "nur_optik", "label": "Nur Optik, Struktur bleibt" } ] }
    ] } }
```

**Bedingungsmodell (klein, aber vollständig):**

- `when` ist eine Liste von Bedingungen, die **alle** erfüllt sein müssen
  (UND). Jede Bedingung nennt `questionId` und `anyOf` (ODER über die
  Options-Ids) – bei Bedarf zusätzlich `allOf` für Mehrfachauswahl und
  `custom: true`, falls eine Freitextantwort die Frage auslösen soll.
- Eine Frage ohne `when` ist immer sichtbar. Tiefe ist **nicht begrenzt** –
  Bedingungen dürfen auf Bedingungen verweisen (`umfang` → `mobile`), genau wie
  in deinem Beispiel „wenn Frage 1 so beantwortet wird, dann Frage 2 … und noch
  mehr".
- **Reihenfolge im Fenster = Reihenfolge im Payload.** Die KI sortiert den Baum
  also so, dass Eltern vor Kindern kommen; das Fenster zeigt nur, was gerade
  erreichbar ist, und zählt dynamisch „Frage 2 von 3".
- **Zurück ist erlaubt:** ändert man eine frühere Antwort, wird der betroffene
  Teilbaum neu ausgewertet und alle dadurch ungültig gewordenen Antworten werden
  sichtbar verworfen (mit Hinweis, welche). Kein stiller Widerspruch im
  Antwortpaket.
- **Grenzen (fail closed, wie überall in der Bridge):** max. 12 Fragen,
  max. 6 Optionen je Frage, max. 400 Zeichen Fragetext. Verstöße →
  `ASK_TOO_MANY_QUESTIONS`. Unbekannte `questionId` in `when` →
  `ASK_GRAPH_INVALID`. Zyklus (`a when b`, `b when a`) oder Selbstbezug →
  `ASK_CYCLE`. Unerreichbare Frage (Bedingung kann nie wahr werden) →
  Warnung `ASK_UNREACHABLE`, kein Abbruch.

**Antwort an die KI (mit lesbarem Pfad, damit die Verzweigung nachvollziehbar
bleibt):**

```json
{ "ok": true, "result": {
    "askId": "ask_9f2c…", "state": "answered", "elapsedSeconds": 41,
    "answers": { "art": { "optionId": "umbau", "label": "Bestehendes umbauen" },
                 "stil": { "optionId": "__custom__", "custom": "wie mein Inventar" },
                 "bestand": { "optionId": "nur_optik", "label": "Nur Optik, Struktur bleibt" } },
    "path": ["art=umbau", "stil=__custom__", "bestand=nur_optik"],
    "notShown": ["umfang", "mobile"],
    "note": "These answers outrank your earlier assumptions. Restate them in your reply and act on them immediately." } }
```

`notShown` ist wichtig: die KI sieht, welche Fragen die Verzweigung
übersprungen hat, und rät nicht, ob du sie verweigert oder nie gesehen hast.

**Ablauf (unverändert zu oben, nur mit Baum):**

1. Server legt `$Shared.AskRequests[askId]` an (`open`, `expiresAt`,
   `ManualResetEvent`). Die UI sieht ihn im nächsten Tick (eigener 250-ms-Takt
   solange Fragen offen sind).
2. **Fenster am Mauszeiger + Versatz** (+140/+100 px, auf den Bildschirm
   geklemmt, auf dem der Zeiger steht – `VirtualScreen`-Grenzen): Topmost, ohne
   Taskbar-Eintrag, `ShowActivated = false` (klaut dir den Fokus nicht, wenn du
   tippst), weiches Einblenden, Countdown-Ring, Fragen als Karten mit
   Ankreuz-Optionen + Freitextfeld, „Zurück", „Antwort senden".
3. Antwort → Event gesetzt → der wartende Aufruf antwortet **sofort**. Läuft die
   Wartezeit ab → `{ state: 'waiting', askId, waitedSeconds,
   nextCall: 'ask_user { askId }' }`, die KI ruft erneut auf (= Sleep-Runde).
4. **Lebt die KI noch?** Aus `lastCallAt` der Sitzung:
   - arbeitet sie ohne die Antwort weiter → **„Agent arbeitet weiter – du kannst
     dieses Fenster schließen"**; die Antwort geht **nicht** verloren, sie kommt
     als `_bridge.userAnswers` im nächsten Umschlag nach.
   - **> 90 s** kein Aufruf → **„Agent ist mittlerweile offline"** +
     **„Prompt kopieren"**: kopiert einen fertigen Arena-Text mit Titel,
     **allen Fragen des Baums inklusive Bedingungen**, deinen bisherigen
     Antworten, Place, URL und Token – direkt in den Chat pastbar.
5. **Ohne Antwort:** nach `timeoutSeconds` → `expired`, und der Umschlag sagt
   der KI `USER_DID_NOT_ANSWER – triff eine begründete Annahme und sage sie dem
   Nutzer`. Die KI darf nie endlos hängen.
6. **Ableger fast gratis:** derselbe Mechanismus als `confirm_action` für
   kritische Eingriffe (GUI ersetzen, viele Instanzen löschen, Union, Playtest
   starten) – eine Ja/Nein-Karte am Zeiger, die bei „Nein" `DENIED_BY_USER`
   zurückgibt.

### Randbedingungen

Max. **ein** Fragenfenster je Sitzung (weitere werden gequeued, nie gestapelt),
nie modal zur Bridge, kein Zugriff des Handler-Runspaces auf den UI-Thread (nur
`$Shared`), Countdown und Zustandswechsel über einen eigenen `DispatcherTimer`,
Baumauswertung rein in der UI (kein Lua, kein Studio). Nach D2 ist das Fenster
erlaubt; die feste Regel in `GANZ WICHTIG…` Abschnitt 4 wird präzisiert zu:
*„Verboten bleiben Toasts/Popups unten rechts als Dauerberieselung. Erlaubt sind
die Fertig-Meldung (bestehender Schalter) und das `ask_user`-/`confirm_action`-
Fenster am Mauszeiger, das ausschließlich auf ausdrücklichen Aufruf der KI
erscheint."*

---

## Meine zusätzlichen Vorschläge

**6. Parse-Gate + CI (höchster Nutzen je Aufwand).**
7.1.4 hat die Bridge mit **einer überzähligen Klammer** komplett lahmgelegt, und
7.1.5 war der reine Reparatur-Release. PowerShell parst die ganze Datei, bevor
irgendetwas sichtbar wird – ein Tippfehler ist damit ein Totalausfall. Vorschlag:
GitHub-Action, die bei jedem Push/PR `test_v398_structure.py` + alle
Regressionen ausführt (Klammer-/String-Balance, Lua via `luaparser`, XAML) und
einen Merge blockiert, wenn die Datei nicht parsebar ist. Kostet einmalig eine
`.github/workflows/ci.yml` und verhindert die nächste „Bridge startet nicht"-Nacht.

**7. Baustelle „eine Datei, 27.328 Zeilen" entschärfen (optional, Workflow-Änderung).**
Middle Ground ohne Risiko für den Starter: das veröffentlichte Artefakt bleibt
**eine** `ArenaBridge.ps1`, aber sie wird aus `src/*.ps1`-Teilen
**zusammengesetzt** (`build.ps1`), und die Tests laufen gegen das fertige
Artefakt. Bearbeitung passiert in kleinen Dateien (Handler, UI, Lua-Plugin,
Guides), ein Klammerfehler fällt beim Zusammensetzen auf und nicht erst beim
Nutzer. Das ist der einzige Vorschlag hier, der deine Arbeitsweise ändert –
deshalb ausdrücklich als Frage.

**8. Automatische Undo-Wegpunkte + „Rückgängig" in der Zeile.**
`set_waypoint` existiert, wird aber von der KI benutzt – oder nicht. Vorschlag:
die Bridge setzt **vor jedem Schreibaufruf** selbst einen benannten Wegpunkt
(`Arena: <tool> <Zeit>`, Ringpuffer max. 20) und die Place-Zeile bekommt
„Letzte Änderung rückgängig". Gegen tollpatschige Fehler ist das die billigste
Versicherung überhaupt: ein Klick, und Studio stellt den Zustand wieder her.

**9. Build-Register und Qualität sichtbar in der UI.**
Die Place-Zeile bzw. der Arena-Verlauf zeigen
`3 Modelle · 1 Entwurf · Audit frisch vor 12 s` und den `buildQuality`-Verdict.
Damit siehst **du** ohne Log-Lesen, ob die KI gerade pfuscht – heute steht das
nur in `runtime.log` und in der Antwort an die KI.

**10. Sitzungs-Wächter „Arena inaktiv".**
Wenn `lastCallAt` einer Sitzung > 3 Minuten zurückliegt und kein Befehl offen
ist: Zeile auf „Arena inaktiv seit X" (ehrlich, grau), optional mit Meldung.
Beendet den Zustand „Balken hängt, niemand sagt was".

**11. Kontext-Kopie statt nur URL+Token.**
„Prompt kopieren" legt heute `URL=…`/`TOKEN=…` ab (`ArenaBridge.ps1:24776`).
Optional zusätzlich: ein Kontextblock mit Place, Bridge-Version, Build-Register,
offenen Fragen, letztem Handoff und den letzten Warnungen – damit ein neuer Chat
nicht bei null anfängt. Passt direkt zum „Prompt kopieren"-Knopf im
Offline-Fenster aus Thema 5.

**12. Diagnose-Paket auf Knopfdruck.**
Ein Knopf „Diagnose kopieren", der `preview-diagnose.txt`,
`progress-diagnose.txt`, `notify-diagnose.txt`, die letzten 200
`runtime.log`-Zeilen und die Laufzeit-Identität (Version/SHA/LanguageMode) als
**einen** Textblock in die Zwischenablage legt. Damit ist jede Live-Abnahme in
einer Nachricht erledigt – wir haben beide gemerkt, wie teuer das sonst ist.

---

## Release 7.2.0 – ein Release, sieben Arbeitspakete (D1, D9)

Umfang nach D9: **Fundament + deine fünf Themen**, kein CI, keine Extras.
Das Risiko ist nicht die Menge, sondern die **eine Datei mit 27.328 Zeilen**, die
PowerShell komplett parst, bevor irgendetwas sichtbar wird – genau daran ist
7.1.4 gestorben. Deshalb: feste Reihenfolge, **jedes Paket endet mit einem
parsebaren Skript und grünen Tests**, ein Commit pro Paket, ein PR am Ende.

| AP | Inhalt | Größe | Risiko |
|---|---|---|---|
| **AP1** | Gemeinsames Fundament: `$Shared`-Zustände (`UserMessages`, `AskRequests`, `SessionBuilds`), Umschlag-Injektion in `New-Envelope`, Stationen-Rahmen (`Write-FlowTrace`), Diagnose-Datei-Rahmen, wiederaufnehmbarer Long-Poll (`wait_for_user`) | mittel | mittel – zentral; der Umschlag muss bei leerem Zustand byte-identisch bleiben |
| **AP2** | Thema 4a Fortschritt: Balken **nur** mit echter Zahl (D5), sonst Textzeile ohne Zahl (D6), Fortschritt wird nicht mehr vom Befehl verdrängt (D7), `PERCENT_MISSING`-Nudge, Nachricht sichtbar, `PROGRESS`-Stationen, `progress-diagnose.txt`, Nachfolger-Auflösung, invariantes Parsen | mittel | klein |
| **AP3** | Thema 4b Benachrichtigung: `Test-NotifyPlatform`, `NOTIFY`-Stationen, Diagnose + Testknopf in den Einstellungen (Schalter bleibt wo er ist), `notify.sweep`, Zähler im Status, ehrliches `notification`-Objekt statt `delivered = $true` (D4: kein neuer Kanal) | mittel | klein |
| **AP4** | Thema 3 Nutzer-Kanal: „Nachricht an Arena senden" im „…“-Menü, **Nachricht-Fenster** mit `wird gesendet` / `Abbrechen` (wirkliches Zurückziehen) / `angekommen` / `von Arena bestätigt` (D8), `_bridge.userMessages`, at-least-once mit `ack_user_message`, „Laufenden Befehl abbrechen" als Menüpunkt statt Zeilen-Knopf (D7) | mittel | klein |
| **AP5** | Thema 5 `ask_user`: Baum-Validierung serverseitig (`ASK_GRAPH_INVALID`/`ASK_CYCLE`/`ASK_TOO_MANY_QUESTIONS`), Fragenfenster am Mauszeiger + Versatz mit Verzweigung, Zurück, Countdown, Zustände „Agent arbeitet weiter" / „Agent ist offline" + Prompt-Kopie, `confirm_action` | **groß** | **höchstes** – neues Fenster, WPF, Zeiger-/Monitorlogik, Zeitverhalten |
| **AP6** | Thema 1 Qualität: `SessionBuilds`-Register (automatisch bei jedem Schreibaufruf), Audit-Pflicht `BUILD_AUDIT_REQUIRED`, Finish-Score + `grade` in `model_audit`, neue `draft`-Schwelle (fängt deinen 5-Teile-Baum), deklarierte Einfachheit, Shift-left-`qualityWarning` | groß | mittel – Lua-Messung + Gate |
| **AP7** | Thema 2 GUI-Vertrag: `uiStructureRules`, `codeLayout`-Messung (Zeilen, `Instance.new`, Editierzeit-Kinder), `scaffold_ui_scripts`, `mode='extend'` für `build_surface`, `UI_STRUCTURE_REQUIRED`, `MONOLITH_RISK`-Warnung im selben Response | groß | mittel |

**Reihenfolge mit Absicht:** AP1 legt das Fundament, das AP4 und AP5 beide
brauchen (sonst baut man Queue, Umschlag-Injektion und Long-Poll zweimal).
AP2/AP3 sind klein, sofort sichtbar und liefern die Messbasis (Stationen +
Diagnose-Dateien), mit der wir AP5–AP7 überhaupt abnehmen können statt zu raten.
AP5 kommt vor AP6/AP7, weil es dein Korrekturwerkzeug ist: wenn beim Testen der
Qualitäts-Gates etwas schiefgeht, greifst du ein, statt Antworten neu generieren
zu lassen.

**Explizit nicht drin (D9):** Parse-Gate/CI, Undo-Wegpunkte, Qualitätsanzeige in
der Zeile, „Arena inaktiv"-Wächter, Kontext-Kopie, Diagnose-Paket-Knopf,
`build_flora`/`build_creature_rig`. Alles jederzeit als 7.2.1 nachziehbar –
`AP1`-Stationen-Rahmen und Diagnose-Dateien machen sie später billiger, nicht
teurer.

**Abnahme vor dem Merge:** du testest die Branch-Fassung direkt im Skript-Modus
(`%LOCALAPPDATA%\ArenaRobloxBridge\app\ArenaBridge.ps1` ersetzen, Bridge
starten – so steht es auch in deinem 7.1.4-Log), bevor `version.json` erhöht und
nach `main` gemergt wird. Damit bekommt kein anderer Nutzer eine Fassung, die du
nicht selbst gestartet hast. `bridge_live_check.py` bekommt für 7.2.0 neue
Stationen: Balkenverhalten ohne Prozent, `PERCENT_MISSING`, Notify-Plattform-
Urteil, Interjection-Zustellung inkl. Zurückziehen, `ask_user`-Baum (auch
Zyklus-/Unerreichbar-Fehlerfälle) und die Qualitäts-/GUI-Gates.

## Arbeitsweise (wie bisher, nur konsequenter)

- Jede Version: Changelog-Kommentar oben, **alle** Versionsstellen
  (`DocsVersion`, `ARENA_VERSION`, `version = '7.x'`, `bridgeVersion` ×3,
  `serverVersion`, Plugin-Kommentar, Einstellungs-Fußzeile,
  Fallback-Literal in `Show-UpdateNotice`, `version.json`).
- UTF-8 **mit BOM** erhalten; größere Änderungen per Python-String-Replacement
  und danach mit `grep` gegenprüfen.
- Keine der festen Nutzerregeln antasten (kein Toast unten rechts, Farben/Design
  der Liste, Einstellungen als großes Fenster mit AN/AUS-Schaltern,
  `notifyOnDone`-Schalter bleibt genau dort, wo er ist).
- Neue Offline-Tests je Version (`test_v720_*.py` …) + neue Stationen in
  `bridge_live_check.py`, damit die Windows-Abnahme eine Checkliste ist und kein
  Raten.
- Nachbardokumente mitziehen: `ORGANIC_BUILD_CONTRACT.md` bei Qualitätsregeln,
  neues `UI_STRUCTURE_CONTRACT.md` bei Thema 2, `GANZ WICHTIG…` bei jeder neuen
  festen Regel.

## Stand der Entscheidungen

Alles geklärt – D1 bis D9 oben. Keine offenen Punkte mehr.

**Nächster Schritt:** AP1 (Fundament) auf dem Branch
`arena/01a10aec-arenarobloxbridge`, mit erweitertem Strukturtest, danach AP2
und AP3 (beide sichtbar und klein), dann AP4, AP5, AP6, AP7. Versionierung erst
am Ende: `7.1.5 → 7.2.0` an allen elf Stellen plus `version.json` mit den
Neuigkeiten fürs Update-Fenster.
