# 8.0.3 – Implementierung und Abnahme

**Stand: 2026-10-16. Quellstand vorbereitet, nicht veröffentlicht.** Änderungen ausschließlich unter `next-update/`. Der alte Root-Bridge-Code, die veröffentlichte EXE und `release/latest.json` bleiben unverändert.

## Umgesetzter Umfang

- **Privatsphäre:** Screenshots und Vorschauen verwenden nur `PrintWindow` für ein eindeutig zugeordnetes Roblox-Studio-Fenster. PID/HWND/Titel und Sitzungsidentität werden geprüft; späte Bilder nach Identitätswechsel werden verworfen. Kein Desktop-, Bildschirmregion- oder Window-DC-Fallback. Minimierte, geschlossene, geschützte oder nicht eindeutig zuordenbare Studio-Fenster liefern ausdrücklich kein Bild. Ein minimiertes Bridge-Fenster beendet nicht die Gültigkeit einer ansonsten live validierten Bindung.
- **Place-Zuordnung:** keine freie/erste Fensterzuweisung. Veröffentlichte Namen werden im Plugin über `MarketplaceService:GetProductInfo(placeId, Enum.InfoType.Asset)` zwischengespeichert ermittelt. Skript-Suffixe werden entfernt. Bereits belegte PID/HWND-Paare bleiben nur bei passendem Titel erhalten; gleiche/mehrdeutige Namen werden nicht geraten.
- **Uploads:** bei Gruppenbesitz wird die Gruppe als Asset-Creator verwendet. Roblox prüft die Rolle und die Rechte des API-Keys; eine Ablehnung führt nicht zu einem persönlichen Ersatz-Upload.
- **Asset-Rechte:** direkte `insert_asset`-/`apply_asset`-Aufrufe können nach einer bestätigten `ASSET_PERMISSION_DENIED`-Antwort über den geprüften Open-Cloud-Katalog ausschließlich `Use` für das Universe dieser Sitzung anfordern und genau einmal erneut versuchen. Keine Wiederholung nach Timeout/unbekanntem Ausgang. `apply_asset` meldet bereits erfolgte Teiländerungen. Read-only, Freigaben, Key-Scopes und Rollen bleiben verbindlich. Asynchrone Roblox-Content-Warnungen sind nicht immer beim Setzen einer Property beobachtbar; verschachtelte Plugin-Batches besitzen keinen Desktop-API-Key. Für die Reparatur direkte Aufrufe verwenden; der explizite Katalog-Endpunkt steht in der Tool-Dokumentation.
- **Place-Liste:** Aktivitätsbalken auch ohne Prozentmeldung, ohne erfundene Prozentzahl. Nur einfacher Status unter dem Namen, kein letzter Arbeitsschritt. Nach über einer Minute ohne Bridge-Aufruf endet die Animation. Ausführlicher Verlauf bleibt separat erhalten; dessen expliziter `hidden`-Fortschritt darf weiterhin ausgeblendet werden.
- **Sprache:** ein aufklappbarer Schalter mit aktueller Sprache, Deutsch/English-Auswahl und Vektorflaggen. Übersetzungskatalog mit 920 Einträgen, einschließlich Dialogen, Scope-Erklärungen, ausführlichen Aktivitätsmeldungen und Versionshistorie. Englische historische Versionsnotizen sind zum Teil ausdrücklich Zusammenfassungen. Fenster werden auch vor `ShowDialog` lokalisiert; Benutzereingaben und Place-Namen sind keine UI-Vokabeln. Sprachwahl wird atomar unter dem versionsunabhängigen `%LOCALAPPDATA%\ArenaRobloxBridge` gespeichert.
- **Autostart:** die laufende neue EXE hat Vorrang vor alten gespeicherten Pfaden. Bereinigung/Migration erfolgt vor dem Duplicate-Instance-Exit. Nur Bridge-Einträge des aktuellen Windows-Nutzers werden angefasst, keine fremden Programme oder HKLM-Systemeinträge. Ein bereits laufender alter Prozess wird nicht gewaltsam beendet.
- **Konten:** ab zwei unterschiedlichen aktiven Studio-Anmeldungen nur „2 Accounts“ usw.; Tooltip mit Kontoliste statt eines beliebigen Einzelavatars. Mehrere Places desselben Kontos zählen einmal.
- **Eingaben:** deklarierte numerische/Bool-/Enum-Werte und Roblox-Komponenten akzeptieren passende Strings. Ungültige, nicht endliche oder übergroße Werte werden nicht heimlich zu gültigen Geometriedimensionen gemacht. Opaque IDs und Skriptquellen bleiben Daten.
- **Normale Parts:** 20 native/virtuelle Formen plus `Dome`-Alias, relative Anker, lokale/Welt-Offsets, Wiederholungen, Defaults, Attribute, Pivot sowie Primitive-/CSG-Budgets und Rollback. Kein Umbau des Polygon- oder Blender-Werkzeugs. Siehe [PART_BUILDER_8_0_3.md](PART_BUILDER_8_0_3.md) sowie die vollständigen dynamischen Docs für `build_assembly`.
- **8.0.1 bleibt erhalten:** das X im Update-Fenster beendet weiterhin die gesamte Bridge; kein Umgehen eines Pflicht-Updates.

## Hier ausführbare Prüfungen

Vom Ordner `next-update`:

```text
python -m pip install -r developer/tests/requirements-test.txt
python developer/tools/sync_ui_translations.py --check
python developer/tests/run_offline_tests.py
```

Die Part-Tests führen den tatsächlichen eingebetteten Lua-Builder mit Roblox-Testdoubles aus. Zusätzlich wird das gesamte Plugin ohne Ausführung kompiliert. Das prüft Rezepte, Referenzen, wiederholte Anker, lokale/Welt-Koordinaten, Stringzahlen, fehlerhafte Vektoren, Budgets und das Aufräumen nach Fehlern. Es ist **kein Beweis für die echte Roblox-CSG-Geometrie**. Die anderen Offline-Tests prüfen Quellen, Verträge, Katalogdeckung, XAML-Struktur, Lua und die bekannten PowerShell-Strukturfallen. Ein Tree-sitter-Check ersetzt nicht den nativen PowerShell-5.1-Parser.

## Validierungsprotokoll dieses Quellstands (Linux, 2026-10-16)

- Gesamte Offline-Suite: **28/28 Python-Testskripte erfolgreich**, Exitcode 0.
- Neue 8.0.3-Prüfungen: **11 Bridge-Vertragstests** und **10 Part-/Lua-Tests** erfolgreich (in der Gesamtsuite enthalten).
- Vollständiges eingebettetes Lua-Plugin kompiliert; Katalog synchron mit dem eingebetteten Ein-Datei-Stand; `git diff --check` sauber.
- Die Suite meldet selbst ausdrücklich, dass kein `powershell.exe`/`pwsh` verfügbar ist. Ihr grüner Exitcode ist **kein** nativer PowerShell-, WPF-, EXE- oder Live-Roblox-Nachweis. Der unten genannte PS-5.1-Funktionstest wurde nicht ausgeführt.

## Vor Build/Freigabe zwingend auf Windows

Vom Ordner `next-update` in **Windows PowerShell 5.1**:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File builder\parse-gate.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File developer\tests\test_v803_runtime.ps1
```

Der zweite Test lädt nur einzelne Funktions-ASTs und verwendet Mocks für Fenster, Startup und Cloud. Keine echte Registry, keine APIs und kein GUI-Start. Er ist in der Linux-Umgebung **nicht ausgeführt** worden. Danach den normalen privaten EXE-Build/Smoke-Test nach `RELEASE-ABLAUF.md` durchführen; nicht als Veröffentlichung behandeln.

### Manuelle Windows-/Studio-Matrix (noch offen)

- [ ] Zwei verschiedene veröffentlichte Places, vertauschte Fensterreihenfolge: Titel und Vorschauen passen. A schließen: B behält seine Identität. Nur B schließen: A bleibt korrekt. Gleiche Titel, neue Studio-Prozesse, Reconnect, `Place1`/`Place4` und offene Local Scripts prüfen.
- [ ] Screenshot bei TikTok/Browser im Vordergrund und bei überdecktem Studio: ausschließlich Studio oder klare Nichtverfügbarkeit. Minimiertes/geschlossenes Studio: kein Desktopbild. Bridge minimieren, später Screenshot anfordern. Titel/Place während laufender Aufnahme wechseln: altes Bild wird verworfen.
- [ ] Deutsches und englisches GUI einschließlich Start, Update, Einstellungen, Berechtigungen, Rückfragen, Nachrichten, Verlauf, Popups und Tooltips durchgehen. Mehrfach hin- und herschalten. Eingaben, Place-Namen und Skripte unverändert. Flaggen sichtbar; Auswahl nach Neustart und aus anderem Versionsordner erhalten.
- [ ] Read-only-Aufruf und Aufruf ohne Prozent: sichtbare Aktivität, keine fiktive Zahl. Echte 0/37/100 Prozent, Fehler, Abschluss und >60 Sekunden Pause prüfen. Unter Place-Namen kein letzter Schritt. Nutzer-Schalter zum Ausblenden weiterhin wirksam.
- [ ] Ein Konto/zwei Places zählt einmal. Zwei verschiedene Konten zeigen nur die Anzahl und beim Hover beide Anmeldungen. Konto abmelden/Place schließen: Liste aktualisiert sich.
- [ ] Alte Run/RunOnce-Einträge und Startup-Wrapper anlegen. Neue/versionsbenannte/„(1)“-EXE starten: genau ein aktueller Start-Eintrag; fremde Einträge unverändert. Test auch bei bereits laufender alter Bridge. Fehlender EXE-Pfad wird nicht durch einen kaputten PowerShell-Autostart ersetzt.
- [ ] Gruppen-Place mit uploadberechtigtem Nicht-Eigentümer und passendem Gruppen-Key: Roblox-Asset gehört wirklich der Gruppe. Fehlende Gruppenrolle/Key-Ressource bleibt Fehler; kein persönlicher Upload. Persönlicher Place bleibt persönlicher Upload.
- [ ] Eigenes Asset ohne Universe-Freigabe einfügen: scoped Grant und maximal ein Retry. Fehlender `asset-permissions:write`-Scope, fremdes Asset, Read-only, unveröffentlichter Place, Roblox-403 und Timeout bleiben ehrlich Fehler; keine Duplikate. `apply_asset` einschließlich Teilfehler und nachgeladener Content-Warnungen prüfen.
- [ ] Alle 20 Formen mit echtem Roblox-CSG visuell prüfen: Schnittseiten/Achsen, Dimensionen, offene Rohrenden, Kurvenübergänge und Kollision. Halb-/Viertelkugel, Torus, Capsule, Kurve, Treppen und gestufter Cone besonders prüfen. Relative Positionierung an gedrehten Parts/Models, wiederholte Anker und Fehler-Rollback testen.
- [ ] X/Alt+F4 am Pflicht-Update beendet alles; „Später“ bleibt nach Pflichtgrenze gesperrt.

**Freigabestatus:** keine EXE gebaut, keine Veröffentlichung, keine Live-Roblox-/Windows-Abnahme in dieser Umgebung. Erst nach dieser Matrix ausdrücklich freigeben.
