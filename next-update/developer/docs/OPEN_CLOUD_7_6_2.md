# Mini-Update 7.6.2 – Roblox Open Cloud

## Für den Nutzer

Die Freigabeliste ist verbindlich: **41 einzelne Berechtigungen**, jede mit eigener
Erklärung und eigener Prüfung. Ein Key mit zusätzlichen Rechten schaltet **keine**
zusätzlichen Bridge-Funktionen frei. Die Berechtigungsanzeige und das Tutorial lesen
denselben Katalog wie die Tools.

- `asset:read` und `asset:write` sind getrennt; genauso alle DataStore-Einzelrechte.
- „Lesen“ bedeutet nicht automatisch „Auflisten“ oder „Schreiben“.
- `universe-places:write` braucht kein erfundenes `universe-places:read`.
- `universe.user-restriction:read` erlaubt das Ansehen von Sperren, **nicht** das
  Sperren/Entsperren von Spielern.
- `universe.thumbnail:*` ist von der gesperrten allgemeinen `thumbnail:read` getrennt.
- `asset-permissions:write` wird nicht mehr mit `asset:write` verwechselt.
- `universe.analytics.alert:*` gewährt keinen Analytics-Zugriff.
- Schreibweisen korrigiert: `snapchot` → `snapshot`, `bage` → `badge`;
  Groß-/Kleinschreibung vereinheitlicht. Keine zusätzlichen Rechte hinzuerfunden.

### Warum die Prüfung mit vielen Rechten scheiterte

`Invoke-OpenCloudIntrospect` benutzte die Standardgrenze von **600 Zeichen** des
HTTP-Helfers. Bei vielen Scopes wurde die erfolgreiche JSON-Antwort abgeschnitten.
`ConvertFrom-Json` konnte sie nicht mehr lesen und zeigte einen Prüfungsfehler an.

Die Introspektion erhält jetzt bis zu **2.000.000 Zeichen**, und beide Transportwege
melden eine überschrittene Grenze ausdrücklich. Keine abgeschnittene Antwort wird
als Rechtebeweis verwendet. Das asynchrone Fenster entnimmt dem Runspace-Ergebnis
ausdrücklich das Ergebnisobjekt. Bei einer fehlgeschlagenen erneuten Prüfung bleibt
der gespeicherte Key unverändert; der Hinweis behauptet nicht mehr, es sei nichts
gespeichert. Eine erfolgreiche erneute Prüfung aktualisiert den Rechte-Cache.

### Was „voller Zugriff“ hier bedeutet

Das neue Werkzeug `open_cloud` stellt **172 geprüfte API-Key-Endpunkte** bereit,
nicht nur ein paar voreingestellte Textfelder. Es unterstützt die dokumentierten
Pfad-/Query-Parameter, JSON-Bodies, fachlichen Header, Multipart-Felder, mehrere
Dateien und rohe Binärdaten. Alle dokumentierten Request-Felder können übergeben
werden; Roblox validiert deren Werte, Ressourcen, Rollen, Moderation und Kontingente.

Wichtige Beispiele: Asset-Metadaten/Versionen/Archivierung, DataStore-Versionen und
Snapshots, Ordered DataStores, Spiel-Events, Analytics-Abfragen, Inventar,
Creator-Store-Produkte und -Sammlungen, erlaubte Legacy-Verwaltung, Asset-Freigaben
und das Veröffentlichen einer RBXL/RBXLX-Version. Das ist **kein automatischer Export
des aktuell geöffneten Studio-Datenmodells**: Für Publishing muss eine gültige
Spieldatei vorliegen.

`upload_asset`, `creator_dashboard` und `datastore` bleiben als bequemere Werkzeuge
erhalten. Die beiden letzteren bleiben auf die aktive Studio-Sitzung begrenzt.
`open_cloud` erlaubt explizite dokumentierte Ressourcen-IDs, damit auch andere
freigegebene Assets, Gruppen-Erlebnisse und Inventare erreichbar sind. Jede Mutation
prüft weiterhin den Vollzugriff der aufrufenden Bridge-Sitzung.

### Ehrliche Grenzen

- **`universe.analytics:write`:** In deiner Liste freigegeben und in der Anzeige
  vorhanden, aber ohne zugeordneten API-Key-Endpunkt in der geprüften offiziellen
  Spezifikation. Dafür wird keine Schreibaktion erfunden. Analytics-Alarme bleiben
  gesperrt.
- Badge-Konfiguration hat laut Spezifikation alternative Rechte. Die Bridge erlaubt
  ausschließlich `PATCH /legacy-badges/v1/badges/{badgeId}` über
  `legacy-universe.badge:write`. Das Recht zum Verwalten **und Ausgeben von Robux**
  wird weder verlangt noch angeboten. Name, Beschreibung, Aktivierung – nicht
  kostenpflichtige Badge-Erstellung oder zusätzliche Badge-Icon-Funktionen.
- Die Subscription-API ist ausgeschlossen, obwohl `universe:write` dort ebenfalls
  als Zugriffsrecht dokumentiert ist. Die ausdrückliche Sperre hat Vorrang.
- Das Bridge-Dateilimit beträgt derzeit **20 MiB pro Datei**, bei Place-Publishing
  **10 MiB** entsprechend dem dokumentierten Endpunkt, bei Multipart insgesamt
  **64 MiB**. Das ist keine Behauptung, dass Roblox bei jedem Asset-Typ dieselben
  Grenzen hat. Insbesondere Videos haben in Roblox weitere/andere Limits.
- Audio: MP3/OGG/WAV/FLAC; Animationen: RBXM/RBXMX mit explizitem Typ `Animation`;
  Modelle: FBX/GLTF/GLB/RBXM/RBXMX; Bilder: PNG/JPEG/BMP/TGA; Video: MP4/MOV.
  Originale Roblox-Mesh-Binärdaten sind über `open_cloud` mit Typ `Mesh` und
  `model/x-file-mesh-data` übertragbar, nicht als beliebiges OBJ.
- Audio-, Bild-, Mesh- und Video-Inhalte sind laut Asset-Guide nicht per Content-
  Update ersetzbar; Metadatenänderungen sind davon getrennt. Kontoprüfung,
  Upload-Kontingente, Moderation, Auflösung und Dauer bleiben Roblox-Regeln.
- API-Betas/Legacy-Endpunkte können sich ändern. Ein gelisteter Endpunkt ist keine
  Garantie, dass ein konkretes Konto ihn bereits nutzen darf.

## Für Arena: Tool-Ablauf

1. `open_cloud {"action":"list","scope":"asset-permissions:write"}`
2. Eine **tatsächlich zurückgegebene** Operations-ID auswählen.
3. `open_cloud {"action":"describe","operation":"<ID aus list>"}`
4. `call` mit den dort dokumentierten Parametern ausführen.

`describe` liefert Request-Schemas einschließlich referenzierter Definitionen,
Quellen und Stabilitätsstatus. Bei Multipart gehören Textfelder nach `form`,
Dateien nach `files` (`field`, `fileName`, `contentType`, `contentBase64`). Für Asset-
Uploads steht das Metadatenobjekt unter `form.request`. Rohe Place-Dateien kommen
in `contentBase64` mit `contentType=application/xml` (RBXLX) oder
`application/octet-stream` (RBXL); `query.versionType` ist `Saved` oder `Published`.
Pagination und Update-Masks sind normale `query`-Parameter. Query-Arrays werden
entsprechend `explode` als wiederholte Parameter bzw. kommagetrennt kodiert.

Keine erfundenen Ziel-IDs. Vor Änderungen Nutzerdaten lesen und den Auftrag beachten.
Keine automatischen Wiederholungen von Schreibaktionen nach Timeout: Der Server
könnte die Änderung bereits durchgeführt haben. Asynchrone Operationen über den
passenden dokumentierten Status-Endpunkt nachverfolgen.

## Schlüssel-Schutz

- Bestehende DPAPI-CurrentUser-Speicherung bleibt erhalten.
- Der Key ist weder Tool-Argument noch Tool-Ergebnis.
- Kein beliebiger URL-/Methoden-Proxy, kein API-Key-Introspect-Tool für Arena.
- Feste Operation → fester HTTPS-Host `apis.roblox.com` → fester Pfad/HTTP-Methode.
- Pfadsegmente/Query-Werte werden validiert und kodiert; Auth-Header nicht akzeptiert.
- Beide HTTP-Transporte folgen **keinen Redirects** mit dem API-Key.
- Transportantworten und Fehlermeldungen maskieren den Key, falls er gespiegelt wird.
- Fehlgeschlagene Key-Prüfung, deaktivierter Key, Ablaufdatum oder fehlendes
  Einzelrecht blockieren die Aktion. Lesen erfordert nicht pauschal Schreiben.
- Roblox bleibt für Ressourcenbindung und Rollen zuständig; ein grünes Häkchen
  bedeutet nicht „Zugriff auf jedes Spiel/jede Gruppe“.

## Quellen und Reproduzierbarkeit

Die offizielle Dokumentation wurde über das öffentliche Repository
[Roblox/creator-docs](https://github.com/Roblox/creator-docs) recherchiert, Stand
`af5f853c78b58c4ea86d62ac2345f881ac11fcec`:

- [OpenAPI: Endpunkte, Scopes, API-Key-Unterstützung, Parameter und Request-Schemas](https://github.com/Roblox/creator-docs/blob/af5f853c78b58c4ea86d62ac2345f881ac11fcec/content/en-us/reference/cloud/openapi.json)
- [API-Key-Introspektion: Antwortformat und Ressourcen](https://github.com/Roblox/creator-docs/blob/af5f853c78b58c4ea86d62ac2345f881ac11fcec/content/en-us/cloud/auth/api-keys.md)
- [Asset-Typen, Formate, Grenzen und Update-Einschränkungen](https://github.com/Roblox/creator-docs/blob/af5f853c78b58c4ea86d62ac2345f881ac11fcec/content/en-us/cloud/guides/usage-assets.md)

`app/opencloud/permissions.json` ist die redaktionell gepflegte Freigabeliste.
`app/opencloud/catalog.json` enthält nur die freigegebenen Operationen sowie deren
Request-Definitionen und Quellen. `developer/ci/generate_opencloud_catalog.py` erzeugt daraus
auch den identischen eingebetteten Katalog in `app/ArenaBridge.ps1`.

**Der Updater benötigt weiterhin nur app/ArenaBridge.ps1 und app/version.json.** Zur
Laufzeit gibt es keinen Zusatzdownload und keine automatische Freigabe neuer
Roblox-Funktionen. Änderungen am Generator oder an der Upstream-Spezifikation
müssen erneut geprüft werden.

```sh
python developer/ci/generate_opencloud_catalog.py /pfad/zur/geprüften/openapi.json
python developer/tests/test_v762_opencloud_policy.py
```

## Abnahme

Offline ausführbar: exakte 41er-Freigabeliste; gesperrte Funktionen; 172 eindeutige
Operationen; Schema-/Pfadreferenzen; identischer eingebetteter Katalog; Regression
mit Assets-only-/Alle-Rechte-/Unbekanntes-Recht-Antworten; Schutz vor dem alten
600-Zeichen-Fehler; Gate-/Dispatch-/UI-Wiring; bestehende Cloud-Tests; Lua-/XAML-
Strukturprüfung und Tree-sitter-PowerShell-Parse-Gate.

**Noch erforderlich vor produktiver Freigabe:** Windows PowerShell 5.1 und Roblox
live. Diese Sandbox kann weder WPF/DPAPI noch echte API-Key-Rechte bestätigen.

```powershell
powershell -NoProfile -File .\builder\parse-gate.ps1 -Path .\app\ArenaBridge.ps1
powershell -NoProfile -File .\developer\tests\test_v762_runtime.ps1
```

Der neue Windows-Test lädt nur die Cloud-Funktionen aus dem AST und ersetzt
Netzwerk und Key-Konfiguration durch Mocks. Er prüft die tatsächlichen PowerShell-
Funktionen für große Introspektion, exakte Rechte, Sperrlisten, Read-only,
Pfad-/Header-Injektion, Multipart, Binär-Publishing und Key-Redaktion. **In dieser
Sandbox nicht ausgeführt.** Danach manuell:

1. Assets-only-Key prüfen und speichern; anschließend Rechte erweitern und erneut
   prüfen. Alle 41 Zeilen bleiben sichtbar, nur echte Rechte werden grün.
2. Gespeicherten Key bei Offline-/401-/403-/429-Antwort erneut prüfen: kein Verlust,
   verständlicher Fehler, keine Aktion bei gescheiterter Gate-Prüfung.
3. Key mit verbotenen Rechten: keine entsprechenden Aktionen unter `list`, auch
   erratene Operations-IDs dürfen keine Anfrage auslösen.
4. Read-only-Sitzung: lesende Aufrufe funktionieren mit passendem Recht;
   Veröffentlichungen, Uploads, Änderungen und Löschungen werden blockiert.
5. In einem **Test-Erlebnis** Leseaufrufe und gezielte Schreib-/Rücklese-Tests prüfen,
   insbesondere DataStores, Asset-Berechtigungen und Place-Veröffentlichung.
   Niemals produktive Spielerdaten für einen Smoke-Test löschen.

## Einzelberechtigungen

### `asset:read`

Asset-Informationen, Versionen, Upload-Ergebnisse und Upload-Kontingente ansehen. Lesen lädt keine neue Datei hoch.

Zugeordnete Endpunkte: **11**.

### `asset:write`

Assets erstellen, unterstützte Inhalte und Metadaten ändern, Versionen zurücksetzen, archivieren und wiederherstellen. Uploads: Audio, Bilder/Decals, Modelle/Meshes, Animationen und Videos nach Roblox-Format-, Konto- und Größenlimits. Einige Aktionen benötigen zusätzlich asset:read; keine freie Auswahl beliebiger Dateiformate.

Zugeordnete Endpunkte: **6**.

### `developer-product:read`

Developer-Produkte (mehrfach kaufbare Dinge wie Coins) und ihre Einstellungen ansehen und auflisten.

Zugeordnete Endpunkte: **2**.

### `developer-product:write`

Developer-Produkte erstellen sowie Namen, Beschreibungen, Preise und Icons über die dokumentierten Endpunkte ändern.

Zugeordnete Endpunkte: **2**.

### `game-pass:read`

Gamepässe (einmal gekaufte Vorteile) und ihre Verkaufseinstellungen ansehen und auflisten.

Zugeordnete Endpunkte: **2**.

### `game-pass:write`

Gamepässe erstellen sowie Namen, Beschreibungen, Preise, Verkauf und Icons ändern.

Zugeordnete Endpunkte: **2**.

### `universe.place:read`

Place-Versionsgeschichte und Mitwirkende ansehen. Öffentliche Place-Metadaten sind ebenfalls über die Tools lesbar.

Zugeordnete Endpunkte: **3**.

### `universe.place:write`

Einstellungen einzelner Places ändern. Eine neue Spieldatei veröffentlichen ist das separate Recht universe-places:write.

Zugeordnete Endpunkte: **2**.

### `universe:read`

Erlebnis-Konfigurationen, Entwürfe, veröffentlichte Revisionen und Experimente ansehen. Öffentliche Erlebnis-Metadaten sind ebenfalls lesbar.

Zugeordnete Endpunkte: **15**.

### `universe:write`

Erlebnis-Einstellungen ändern, Server neu starten, Konfigurationsentwürfe und Experimente verwalten sowie dokumentierte Übersetzungs- und Spracherzeugungsfunktionen nutzen. Ausdrücklich gesperrte Funktionen wie Abonnements bleiben ausgeschlossen.

Zugeordnete Endpunkte: **16**.

### `universe-datastores.objects:read`

Den gespeicherten Wert eines DataStore-Eintrags lesen, zum Beispiel den Spielstand eines Spielers.

Zugeordnete Endpunkte: **3**.

### `universe-datastores.objects:create`

Neue DataStore-Einträge anlegen. Kombinierte Setzen-/Erhöhen-Endpunkte können zusätzlich update benötigen.

Zugeordnete Endpunkte: **6**.

### `universe-datastores.objects:update`

Vorhandene DataStore-Werte ändern oder Zahlen erhöhen. Kombinierte Endpunkte können zusätzlich create benötigen.

Zugeordnete Endpunkte: **6**.

### `universe-datastores.objects:delete`

Einzelne DataStore-Einträge löschen. Das ist nicht dasselbe wie einen ganzen Store zu löschen.

Zugeordnete Endpunkte: **3**.

### `universe-datastores.objects:list`

Schlüssel und Einträge eines DataStores auflisten; die gespeicherten Werte separat mit read lesen.

Zugeordnete Endpunkte: **3**.

### `universe-datastores.versions:read`

Eine bestimmte ältere Version eines gespeicherten Eintrags lesen.

Zugeordnete Endpunkte: **1**.

### `universe-datastores.versions:list`

Die verfügbaren Versionen beziehungsweise Revisionen eines Eintrags auflisten.

Zugeordnete Endpunkte: **3**.

### `universe-datastores.control:create`

Beim ersten Schreiben einen neuen Standard-DataStore entstehen lassen. Die v1-Endpunkte zum Setzen und Erhöhen benötigen zusätzlich objects:create und objects:update.

Zugeordnete Endpunkte: **2**.

### `universe-datastores.control:delete`

Einen ganzen DataStore zum Löschen markieren oder innerhalb der Roblox-Frist wiederherstellen.

Zugeordnete Endpunkte: **2**.

### `universe-datastores.control:list`

Die DataStores eines Erlebnisses auflisten, einschließlich gelöschter Stores, wenn angefordert.

Zugeordnete Endpunkte: **2**.

### `universe-datastores.control:snapshot`

Einen Snapshot der DataStores des Erlebnisses anstoßen. Das sichert deren Stand nach den Roblox-Snapshot-Regeln; es ist kein lokaler Download.

Zugeordnete Endpunkte: **1**.

### `universe-places:write`

Eine RBXL-/RBXLX-Spieldatei als neue Place-Version speichern oder veröffentlichen. Published macht das Update live, Saved speichert nur die Version.

Zugeordnete Endpunkte: **1**.

### `universe.analytics:read`

Analyse-Messwerte und Filterwerte des Erlebnisses abfragen und Ergebnisse länger laufender Abfragen abholen.

Zugeordnete Endpunkte: **4**.

### `universe.analytics:write`

Von dir freigegebenes Analytics-Schreibrecht. In der geprüften offiziellen Spezifikation ist dafür kein API-Key-Endpunkt dokumentiert; deshalb wird keine Schreibaktion erfunden. Analytics-Alarme bleiben gesperrt.

Zugeordnete Endpunkte: **0**.

### `universe.user-restriction:read`

Nutzersperren eines Erlebnisses oder Places und deren Änderungshistorie ansehen. Arena darf keine Sperren setzen, ändern oder aufheben.

Zugeordnete Endpunkte: **5**.

### `universe.thumbnail:read`

Startseiten-Vorschaubilder des Erlebnisses, deren Verarbeitung und Personalisierungs-Einstellungen ansehen. Kein allgemeiner Thumbnail-Zugriff.

Zugeordnete Endpunkte: **3**.

### `universe.thumbnail:write`

Startseiten-Vorschaubilder hochladen und löschen sowie deren Personalisierungs-Auswahl erstellen und ändern.

Zugeordnete Endpunkte: **4**.

### `universe.event:read`

Spiel-Events und ihre Details ansehen und auflisten.

Zugeordnete Endpunkte: **2**.

### `universe.event:write`

Spiel-Events erstellen, ändern und löschen.

Zugeordnete Endpunkte: **3**.

### `universe.ordered-data-store.scope.entry:read`

Sortierte DataStore-Einträge und Ranglistenwerte lesen und auflisten.

Zugeordnete Endpunkte: **4**.

### `universe.ordered-data-store.scope.entry:write`

Sortierte DataStore-Einträge anlegen, ändern, erhöhen und löschen, etwa Punkte einer Rangliste.

Zugeordnete Endpunkte: **8**.

### `creator-store-save:read`

Gespeicherte Creator-Store-Assets einer Sammlung auflisten.

Zugeordnete Endpunkte: **1**.

### `creator-store-save:write`

Creator-Store-Assets in Sammlungen speichern und einzelne oder mehrere gespeicherte Verweise entfernen. Das löscht nicht das Original-Asset.

Zugeordnete Endpunkte: **3**.

### `legacy-universe:manage`

Erlebnisse aktivieren/deaktivieren, eigene Verwaltungsrechte ansehen und die dokumentierten älteren Übersetzungsfunktionen für Namen, Beschreibungen, Icons, Vorschaubilder und Lokalisierungstabellen nutzen. Keine Teamverwaltung oder Follower-Funktionen.

Zugeordnete Endpunkte: **29**.

### `legacy-game-pass:manage`

Übersetzte Gamepass-Namen, Beschreibungen und Icons lesen, ändern und entfernen über die älteren Verwaltungs-Endpunkte.

Zugeordnete Endpunkte: **8**.

### `legacy-developer-product:manage`

Übersetzte Developer-Produkt-Namen, Beschreibungen und Icons lesen, ändern und entfernen über die älteren Verwaltungs-Endpunkte.

Zugeordnete Endpunkte: **8**.

### `legacy-universe.badge:write`

Name, Beschreibung und Aktivierungszustand vorhandener Badges ändern. Keine Badge-Erstellung mit Robux-Ausgaben und kein Zugriff über legacy-badge:manage.

Zugeordnete Endpunkte: **1**.

### `user.inventory-item:read`

Erlaubte Inventargegenstände eines Roblox-Nutzers auflisten. Keine Gegenstände vergeben, verschieben oder löschen; Roblox-Datenschutz gilt weiterhin.

Zugeordnete Endpunkte: **1**.

### `creator-store-product:read`

Creator-Store-Produkte und Asset-Details ansehen und den Creator Store durchsuchen.

Zugeordnete Endpunkte: **4**.

### `creator-store-product:write`

Creator-Store-Produkte erstellen und ihre dokumentierten Verkaufs-/Vertriebs-Einstellungen ändern. Ein Produkt ist nicht der eigentliche Asset-Dateiupload.

Zugeordnete Endpunkte: **2**.

### `asset-permissions:write`

Unterstützten Empfängern die Nutzung von Assets erlauben, zum Beispiel einem Gruppen-Erlebnis Zugriff auf dein hochgeladenes Asset geben. Roblox prüft Eigentum, Empfängertyp und deine Rolle; dieses Recht überträgt kein Eigentum.

Zugeordnete Endpunkte: **1**.

## Endpunkt-Matrix

Die technischen Namen stammen aus der offiziellen Spezifikation; jede Zeile ist über `open_cloud` erreichbar.

| Operation | Methode/Pfad | Erforderliche Rechte |
|---|---|---|
| `post__analytics_query_api_v1_universes_universeId_dimension_values` | `POST /analytics-query-api/v1/universes/{universeId}/dimension-values` | `universe.analytics:read` |
| `post__analytics_query_api_v1_universes_universeId_metrics` | `POST /analytics-query-api/v1/universes/{universeId}/metrics` | `universe.analytics:read` |
| `get__analytics_query_api_v1_universes_universeId_operations_dimension_values_operationId` | `GET /analytics-query-api/v1/universes/{universeId}/operations/dimension-values/{operationId}` | `universe.analytics:read` |
| `get__analytics_query_api_v1_universes_universeId_operations_metrics_operationId` | `GET /analytics-query-api/v1/universes/{universeId}/operations/metrics/{operationId}` | `universe.analytics:read` |
| `patch__asset_permissions_api_v1_assets_permissions` | `PATCH /asset-permissions-api/v1/assets/permissions` | `asset-permissions:write` |
| `Assets_CreateAsset` | `POST /assets/v1/assets` | `asset:read`, `asset:write` |
| `Assets_GetAsset` | `GET /assets/v1/assets/{assetId}` | `asset:read` |
| `Assets_UpdateAsset` | `PATCH /assets/v1/assets/{assetId}` | `asset:read`, `asset:write` |
| `listAssetVersions` | `GET /assets/v1/assets/{assetId}/versions` | `asset:read` |
| `Assets_GetAssetVersion` | `GET /assets/v1/assets/{assetId}/versions/{versionNumber}` | `asset:read` |
| `Assets_RollbackAssetVersion` | `POST /assets/v1/assets/{assetId}/versions:rollback` | `asset:read`, `asset:write` |
| `Assets_ArchiveAsset` | `POST /assets/v1/assets/{assetId}:archive` | `asset:read`, `asset:write` |
| `Assets_RestoreAsset` | `POST /assets/v1/assets/{assetId}:restore` | `asset:read`, `asset:write` |
| `Assets_GetOperation` | `GET /assets/v1/operations/{operationId}` | `asset:read` |
| `Cloud_CreateCreatorStoreProduct` | `POST /cloud/v2/creator-store-products` | `creator-store-product:write` |
| `Cloud_GetCreatorStoreProduct` | `GET /cloud/v2/creator-store-products/{creator_store_product_id}` | `creator-store-product:read` |
| `Cloud_UpdateCreatorStoreProduct` | `PATCH /cloud/v2/creator-store-products/{creator_store_product_id}` | `creator-store-product:write` |
| `Cloud_GetUniverse` | `GET /cloud/v2/universes/{universe_id}` | Öffentliche Metadaten; Key-Gültigkeit wird geprüft. |
| `Cloud_UpdateUniverse` | `PATCH /cloud/v2/universes/{universe_id}` | `universe:write` |
| `Cloud_ListDataStores` | `GET /cloud/v2/universes/{universe_id}/data-stores` | `universe-datastores.control:list` |
| `Cloud_DeleteDataStore` | `DELETE /cloud/v2/universes/{universe_id}/data-stores/{data_store_id}` | `universe-datastores.control:delete` |
| `Cloud_ListDataStoreEntries__Using_Universes` | `GET /cloud/v2/universes/{universe_id}/data-stores/{data_store_id}/entries` | `universe-datastores.objects:list` |
| `Cloud_CreateDataStoreEntry__Using_Universes` | `POST /cloud/v2/universes/{universe_id}/data-stores/{data_store_id}/entries` | `universe-datastores.objects:create` |
| `Cloud_DeleteDataStoreEntry__Using_Universes_DataStores` | `DELETE /cloud/v2/universes/{universe_id}/data-stores/{data_store_id}/entries/{entry_id}` | `universe-datastores.objects:delete` |
| `Cloud_GetDataStoreEntry__Using_Universes_DataStores` | `GET /cloud/v2/universes/{universe_id}/data-stores/{data_store_id}/entries/{entry_id}` | `universe-datastores.objects:read` |
| `Cloud_UpdateDataStoreEntry__Using_Universes_DataStores` | `PATCH /cloud/v2/universes/{universe_id}/data-stores/{data_store_id}/entries/{entry_id}` | `universe-datastores.objects:update` |
| `Cloud_IncrementDataStoreEntry__Using_Universes_DataStores` | `POST /cloud/v2/universes/{universe_id}/data-stores/{data_store_id}/entries/{entry_id}:increment` | `universe-datastores.objects:create`, `universe-datastores.objects:update` |
| `Cloud_ListDataStoreEntryRevisions__Using_Universes_DataStores` | `GET /cloud/v2/universes/{universe_id}/data-stores/{data_store_id}/entries/{entry_id}:listRevisions` | `universe-datastores.versions:list` |
| `Cloud_ListDataStoreEntries__Using_Universes_DataStores` | `GET /cloud/v2/universes/{universe_id}/data-stores/{data_store_id}/scopes/{scope_id}/entries` | `universe-datastores.objects:list` |
| `Cloud_CreateDataStoreEntry__Using_Universes_DataStores` | `POST /cloud/v2/universes/{universe_id}/data-stores/{data_store_id}/scopes/{scope_id}/entries` | `universe-datastores.objects:create` |
| `Cloud_DeleteDataStoreEntry__Using_Universes_DataStores_Scopes` | `DELETE /cloud/v2/universes/{universe_id}/data-stores/{data_store_id}/scopes/{scope_id}/entries/{entry_id}` | `universe-datastores.objects:delete` |
| `Cloud_GetDataStoreEntry__Using_Universes_DataStores_Scopes` | `GET /cloud/v2/universes/{universe_id}/data-stores/{data_store_id}/scopes/{scope_id}/entries/{entry_id}` | `universe-datastores.objects:read` |
| `Cloud_UpdateDataStoreEntry__Using_Universes_DataStores_Scopes` | `PATCH /cloud/v2/universes/{universe_id}/data-stores/{data_store_id}/scopes/{scope_id}/entries/{entry_id}` | `universe-datastores.objects:update` |
| `Cloud_IncrementDataStoreEntry__Using_Universes_DataStores_Scopes` | `POST /cloud/v2/universes/{universe_id}/data-stores/{data_store_id}/scopes/{scope_id}/entries/{entry_id}:increment` | `universe-datastores.objects:create`, `universe-datastores.objects:update` |
| `Cloud_ListDataStoreEntryRevisions__Using_Universes_DataStores_Scopes` | `GET /cloud/v2/universes/{universe_id}/data-stores/{data_store_id}/scopes/{scope_id}/entries/{entry_id}:listRevisions` | `universe-datastores.versions:list` |
| `Cloud_UndeleteDataStore` | `POST /cloud/v2/universes/{universe_id}/data-stores/{data_store_id}:undelete` | `universe-datastores.control:delete` |
| `Cloud_SnapshotDataStores` | `POST /cloud/v2/universes/{universe_id}/data-stores:snapshot` | `universe-datastores.control:snapshot` |
| `Cloud_ListOrderedDataStoreEntries` | `GET /cloud/v2/universes/{universe_id}/ordered-data-stores/{ordered_data_store_id}/scopes/{scope_id}/entries` | `universe.ordered-data-store.scope.entry:read` |
| `Cloud_CreateOrderedDataStoreEntry` | `POST /cloud/v2/universes/{universe_id}/ordered-data-stores/{ordered_data_store_id}/scopes/{scope_id}/entries` | `universe.ordered-data-store.scope.entry:write` |
| `Cloud_DeleteOrderedDataStoreEntry` | `DELETE /cloud/v2/universes/{universe_id}/ordered-data-stores/{ordered_data_store_id}/scopes/{scope_id}/entries/{entry_id}` | `universe.ordered-data-store.scope.entry:write` |
| `Cloud_GetOrderedDataStoreEntry` | `GET /cloud/v2/universes/{universe_id}/ordered-data-stores/{ordered_data_store_id}/scopes/{scope_id}/entries/{entry_id}` | `universe.ordered-data-store.scope.entry:read` |
| `Cloud_UpdateOrderedDataStoreEntry` | `PATCH /cloud/v2/universes/{universe_id}/ordered-data-stores/{ordered_data_store_id}/scopes/{scope_id}/entries/{entry_id}` | `universe.ordered-data-store.scope.entry:write` |
| `Cloud_IncrementOrderedDataStoreEntry` | `POST /cloud/v2/universes/{universe_id}/ordered-data-stores/{ordered_data_store_id}/scopes/{scope_id}/entries/{entry_id}:increment` | `universe.ordered-data-store.scope.entry:write` |
| `Cloud_GetPlace` | `GET /cloud/v2/universes/{universe_id}/places/{place_id}` | Öffentliche Metadaten; Key-Gültigkeit wird geprüft. |
| `Cloud_UpdatePlace` | `PATCH /cloud/v2/universes/{universe_id}/places/{place_id}` | `universe.place:write` |
| `Cloud_ListUserRestrictions__Using_Universes` | `GET /cloud/v2/universes/{universe_id}/places/{place_id}/user-restrictions` | `universe.user-restriction:read` |
| `Cloud_GetUserRestriction__Using_Universes_Places` | `GET /cloud/v2/universes/{universe_id}/places/{place_id}/user-restrictions/{user_restriction_id}` | `universe.user-restriction:read` |
| `Cloud_ListUserRestrictions` | `GET /cloud/v2/universes/{universe_id}/user-restrictions` | `universe.user-restriction:read` |
| `Cloud_GetUserRestriction__Using_Universes` | `GET /cloud/v2/universes/{universe_id}/user-restrictions/{user_restriction_id}` | `universe.user-restriction:read` |
| `Cloud_ListUserRestrictionLogs` | `GET /cloud/v2/universes/{universe_id}/user-restrictions:listLogs` | `universe.user-restriction:read` |
| `Cloud_GenerateSpeechAsset` | `POST /cloud/v2/universes/{universe_id}:generateSpeechAsset` | `asset:read`, `asset:write`, `universe:write` |
| `Cloud_RestartUniverseServers` | `POST /cloud/v2/universes/{universe_id}:restartServers` | `universe:write` |
| `Cloud_TranslateText` | `POST /cloud/v2/universes/{universe_id}:translateText` | `universe:write` |
| `Cloud_ListAssetQuotas` | `GET /cloud/v2/users/{user_id}/asset-quotas` | `asset:read` |
| `Cloud_ListInventoryItems` | `GET /cloud/v2/users/{user_id}/inventory-items` | `user.inventory-item:read` |
| `CreatorConfigsPublicApi_GetConfigRepositoryValues` | `GET /creator-configs-public-api/v1/configs/universes/{universeId}/repositories/{repository}` | `universe:read` |
| `CreatorConfigsPublicApi_DeleteDraft` | `DELETE /creator-configs-public-api/v1/configs/universes/{universeId}/repositories/{repository}/draft` | `universe:write` |
| `CreatorConfigsPublicApi_GetConfigRepositoryDraft` | `GET /creator-configs-public-api/v1/configs/universes/{universeId}/repositories/{repository}/draft` | `universe:read` |
| `CreatorConfigsPublicApi_UpdateDraft` | `PATCH /creator-configs-public-api/v1/configs/universes/{universeId}/repositories/{repository}/draft` | `universe:write` |
| `CreatorConfigsPublicApi_OverwriteDraft` | `PUT /creator-configs-public-api/v1/configs/universes/{universeId}/repositories/{repository}/draft:overwrite` | `universe:write` |
| `CreatorConfigsPublicApi_GetConfigRepositoryFull` | `GET /creator-configs-public-api/v1/configs/universes/{universeId}/repositories/{repository}/full` | `universe:read` |
| `CreatorConfigsPublicApi_PublishDraft` | `POST /creator-configs-public-api/v1/configs/universes/{universeId}/repositories/{repository}/publish` | `universe:write` |
| `CreatorConfigsPublicApi_ListRevisions` | `GET /creator-configs-public-api/v1/configs/universes/{universeId}/repositories/{repository}/revisions` | `universe:read` |
| `CreatorConfigsPublicApi_RestoreRevision` | `POST /creator-configs-public-api/v1/configs/universes/{universeId}/repositories/{repository}/revisions/{revisionId}/restore` | `universe:write` |
| `PublicExperimentation_ListExperiments` | `GET /creator-configs-public-api/v1/experimentation/universes/{universeId}/experiments` | `universe:read` |
| `PublicExperimentation_CreateExperiment` | `POST /creator-configs-public-api/v1/experimentation/universes/{universeId}/experiments` | `universe:write` |
| `PublicExperimentation_DiscardExperiment` | `DELETE /creator-configs-public-api/v1/experimentation/universes/{universeId}/experiments/{experimentId}` | `universe:write` |
| `PublicExperimentation_GetExperiment` | `GET /creator-configs-public-api/v1/experimentation/universes/{universeId}/experiments/{experimentId}` | `universe:read` |
| `PublicExperimentation_UpdateExperiment` | `PATCH /creator-configs-public-api/v1/experimentation/universes/{universeId}/experiments/{experimentId}` | `universe:write` |
| `PublicExperimentation_GetExperimentStats` | `GET /creator-configs-public-api/v1/experimentation/universes/{universeId}/experiments/{experimentId}/stats` | `universe:read` |
| `PublicExperimentation_CompleteExperiment` | `POST /creator-configs-public-api/v1/experimentation/universes/{universeId}/experiments/{experimentId}:complete` | `universe:write` |
| `PublicExperimentation_ScheduleExperiment` | `POST /creator-configs-public-api/v1/experimentation/universes/{universeId}/experiments/{experimentId}:schedule` | `universe:write` |
| `PublicExperimentation_StartExperiment` | `POST /creator-configs-public-api/v1/experimentation/universes/{universeId}/experiments/{experimentId}:start` | `universe:write` |
| `PublicExperimentation_CalculateExperimentMde` | `POST /creator-configs-public-api/v1/experimentation/universes/{universeId}/experiments:calculateMde` | `universe:read` |
| `PublicExperimentation_GetExperimentOperationStatus` | `GET /creator-configs-public-api/v1/experimentation/universes/{universeId}/operations/{operationId}` | `universe:read` |
| `Datastores_ListDatastoresAsync` | `GET /datastores/v1/universes/{universeId}/standard-datastores` | `universe-datastores.control:list` |
| `Entries_ListKeysAsync` | `GET /datastores/v1/universes/{universeId}/standard-datastores/datastore/entries` | `universe-datastores.objects:list` |
| `Entries_DeleteEntryAsync` | `DELETE /datastores/v1/universes/{universeId}/standard-datastores/datastore/entries/entry` | `universe-datastores.objects:delete` |
| `Entries_GetEntryAsync` | `GET /datastores/v1/universes/{universeId}/standard-datastores/datastore/entries/entry` | `universe-datastores.objects:read` |
| `Entries_SetEntryAsync` | `POST /datastores/v1/universes/{universeId}/standard-datastores/datastore/entries/entry` | `universe-datastores.control:create`, `universe-datastores.objects:create`, `universe-datastores.objects:update` |
| `Entries_IncrementEntryAsync` | `POST /datastores/v1/universes/{universeId}/standard-datastores/datastore/entries/entry/increment` | `universe-datastores.control:create`, `universe-datastores.objects:create`, `universe-datastores.objects:update` |
| `Entries_ListEntryVersionsAsync` | `GET /datastores/v1/universes/{universeId}/standard-datastores/datastore/entries/entry/versions` | `universe-datastores.versions:list` |
| `Entries_GetEntryVersionAsync` | `GET /datastores/v1/universes/{universeId}/standard-datastores/datastore/entries/entry/versions/version` | `universe-datastores.versions:read` |
| `DeveloperProducts_CreateDeveloperProductV2` | `POST /developer-products/v2/universes/{universeId}/developer-products` | `developer-product:write` |
| `DeveloperProducts_ListDeveloperProductConfigsByUniverseV2` | `GET /developer-products/v2/universes/{universeId}/developer-products/creator` | `developer-product:read` |
| `DeveloperProducts_UpdateDeveloperProductV2` | `PATCH /developer-products/v2/universes/{universeId}/developer-products/{productId}` | `developer-product:write` |
| `DeveloperProducts_GetDeveloperProductConfigV2` | `GET /developer-products/v2/universes/{universeId}/developer-products/{productId}/creator` | `developer-product:read` |
| `GamePasses_CreateGamePass` | `POST /game-passes/v1/universes/{universeId}/game-passes` | `game-pass:write` |
| `GamePasses_ListGamePassConfigsByUniverse` | `GET /game-passes/v1/universes/{universeId}/game-passes/creator` | `game-pass:read` |
| `GamePasses_UpdateGamePass` | `PATCH /game-passes/v1/universes/{universeId}/game-passes/{gamePassId}` | `game-pass:write` |
| `GamePasses_GetGamePassConfig` | `GET /game-passes/v1/universes/{universeId}/game-passes/{gamePassId}/creator` | `game-pass:read` |
| `patch__legacy_badges_v1_badges_badgeId` | `PATCH /legacy-badges/v1/badges/{badgeId}` | `legacy-universe.badge:write` |
| `get__legacy_develop_v1_universes_multiget_permissions` | `GET /legacy-develop/v1/universes/multiget/permissions` | `legacy-universe:manage` |
| `post__legacy_develop_v1_universes_universeId_activate` | `POST /legacy-develop/v1/universes/{universeId}/activate` | `legacy-universe:manage` |
| `post__legacy_develop_v1_universes_universeId_deactivate` | `POST /legacy-develop/v1/universes/{universeId}/deactivate` | `legacy-universe:manage` |
| `get__legacy_develop_v1_universes_universeId_permissions` | `GET /legacy-develop/v1/universes/{universeId}/permissions` | `legacy-universe:manage` |
| `patch__legacy_game_internationalization_v1_developer_products_developerProductId_description_language_codes_languageCode` | `PATCH /legacy-game-internationalization/v1/developer-products/{developerProductId}/description/language-codes/{languageCode}` | `legacy-developer-product:manage` |
| `get__legacy_game_internationalization_v1_developer_products_developerProductId_icons` | `GET /legacy-game-internationalization/v1/developer-products/{developerProductId}/icons` | `legacy-developer-product:manage` |
| `delete__legacy_game_internationalization_v1_developer_products_developerProductId_icons_language_codes_languageCode` | `DELETE /legacy-game-internationalization/v1/developer-products/{developerProductId}/icons/language-codes/{languageCode}` | `legacy-developer-product:manage` |
| `post__legacy_game_internationalization_v1_developer_products_developerProductId_icons_language_codes_languageCode` | `POST /legacy-game-internationalization/v1/developer-products/{developerProductId}/icons/language-codes/{languageCode}` | `legacy-developer-product:manage` |
| `get__legacy_game_internationalization_v1_developer_products_developerProductId_name_description` | `GET /legacy-game-internationalization/v1/developer-products/{developerProductId}/name-description` | `legacy-developer-product:manage` |
| `delete__legacy_game_internationalization_v1_developer_products_developerProductId_name_description_language_codes_languageCode` | `DELETE /legacy-game-internationalization/v1/developer-products/{developerProductId}/name-description/language-codes/{languageCode}` | `legacy-developer-product:manage` |
| `patch__legacy_game_internationalization_v1_developer_products_developerProductId_name_description_language_codes_languageCode` | `PATCH /legacy-game-internationalization/v1/developer-products/{developerProductId}/name-description/language-codes/{languageCode}` | `legacy-developer-product:manage` |
| `patch__legacy_game_internationalization_v1_developer_products_developerProductId_name_language_codes_languageCode` | `PATCH /legacy-game-internationalization/v1/developer-products/{developerProductId}/name/language-codes/{languageCode}` | `legacy-developer-product:manage` |
| `get__legacy_game_internationalization_v1_game_icon_games_gameId` | `GET /legacy-game-internationalization/v1/game-icon/games/{gameId}` | `legacy-universe:manage` |
| `delete__legacy_game_internationalization_v1_game_icon_games_gameId_language_codes_languageCode` | `DELETE /legacy-game-internationalization/v1/game-icon/games/{gameId}/language-codes/{languageCode}` | `legacy-universe:manage` |
| `post__legacy_game_internationalization_v1_game_icon_games_gameId_language_codes_languageCode` | `POST /legacy-game-internationalization/v1/game-icon/games/{gameId}/language-codes/{languageCode}` | `legacy-universe:manage` |
| `patch__legacy_game_internationalization_v1_game_passes_gamePassId_description_language_codes_languageCode` | `PATCH /legacy-game-internationalization/v1/game-passes/{gamePassId}/description/language-codes/{languageCode}` | `legacy-game-pass:manage` |
| `get__legacy_game_internationalization_v1_game_passes_gamePassId_icons` | `GET /legacy-game-internationalization/v1/game-passes/{gamePassId}/icons` | `legacy-game-pass:manage` |
| `delete__legacy_game_internationalization_v1_game_passes_gamePassId_icons_language_codes_languageCode` | `DELETE /legacy-game-internationalization/v1/game-passes/{gamePassId}/icons/language-codes/{languageCode}` | `legacy-game-pass:manage` |
| `post__legacy_game_internationalization_v1_game_passes_gamePassId_icons_language_codes_languageCode` | `POST /legacy-game-internationalization/v1/game-passes/{gamePassId}/icons/language-codes/{languageCode}` | `legacy-game-pass:manage` |
| `get__legacy_game_internationalization_v1_game_passes_gamePassId_name_description` | `GET /legacy-game-internationalization/v1/game-passes/{gamePassId}/name-description` | `legacy-game-pass:manage` |
| `delete__legacy_game_internationalization_v1_game_passes_gamePassId_name_description_language_codes_languageCode` | `DELETE /legacy-game-internationalization/v1/game-passes/{gamePassId}/name-description/language-codes/{languageCode}` | `legacy-game-pass:manage` |
| `patch__legacy_game_internationalization_v1_game_passes_gamePassId_name_description_language_codes_languageCode` | `PATCH /legacy-game-internationalization/v1/game-passes/{gamePassId}/name-description/language-codes/{languageCode}` | `legacy-game-pass:manage` |
| `patch__legacy_game_internationalization_v1_game_passes_gamePassId_name_language_codes_languageCode` | `PATCH /legacy-game-internationalization/v1/game-passes/{gamePassId}/name/language-codes/{languageCode}` | `legacy-game-pass:manage` |
| `post__legacy_game_internationalization_v1_game_thumbnails_games_gameId_language_codes_languageCode_alt_text` | `POST /legacy-game-internationalization/v1/game-thumbnails/games/{gameId}/language-codes/{languageCode}/alt-text` | `legacy-universe:manage` |
| `post__legacy_game_internationalization_v1_game_thumbnails_games_gameId_language_codes_languageCode_image` | `POST /legacy-game-internationalization/v1/game-thumbnails/games/{gameId}/language-codes/{languageCode}/image` | `legacy-universe:manage` |
| `post__legacy_game_internationalization_v1_game_thumbnails_games_gameId_language_codes_languageCode_images_order` | `POST /legacy-game-internationalization/v1/game-thumbnails/games/{gameId}/language-codes/{languageCode}/images/order` | `legacy-universe:manage` |
| `delete__legacy_game_internationalization_v1_game_thumbnails_games_gameId_language_codes_languageCode_images_imageId` | `DELETE /legacy-game-internationalization/v1/game-thumbnails/games/{gameId}/language-codes/{languageCode}/images/{imageId}` | `legacy-universe:manage` |
| `post__legacy_game_internationalization_v1_name_description_games_translation_history` | `POST /legacy-game-internationalization/v1/name-description/games/translation-history` | `legacy-universe:manage` |
| `patch__legacy_game_internationalization_v1_name_description_games_gameId` | `PATCH /legacy-game-internationalization/v1/name-description/games/{gameId}` | `legacy-universe:manage` |
| `patch__legacy_game_internationalization_v1_source_language_games_gameId` | `PATCH /legacy-game-internationalization/v1/source-language/games/{gameId}` | `legacy-universe:manage` |
| `patch__legacy_game_internationalization_v1_supported_languages_games_gameId` | `PATCH /legacy-game-internationalization/v1/supported-languages/games/{gameId}` | `legacy-universe:manage` |
| `get__legacy_game_internationalization_v1_supported_languages_games_gameId_automatic_translation_status` | `GET /legacy-game-internationalization/v1/supported-languages/games/{gameId}/automatic-translation-status` | `legacy-universe:manage` |
| `patch__legacy_game_internationalization_v1_supported_languages_games_gameId_languages_languageCode_automatic_translation_status` | `PATCH /legacy-game-internationalization/v1/supported-languages/games/{gameId}/languages/{languageCode}/automatic-translation-status` | `legacy-universe:manage` |
| `patch__legacy_game_internationalization_v1_supported_languages_games_gameId_languages_languageCode_universe_display_info_automatic_translation_settings` | `PATCH /legacy-game-internationalization/v1/supported-languages/games/{gameId}/languages/{languageCode}/universe-display-info-automatic-translation-settings` | `legacy-universe:manage` |
| `get__legacy_game_internationalization_v1_supported_languages_games_gameId_universe_display_info_automatic_translation_settings` | `GET /legacy-game-internationalization/v1/supported-languages/games/{gameId}/universe-display-info-automatic-translation-settings` | `legacy-universe:manage` |
| `post__legacy_localization_tables_v1_autolocalization_games_gameId_autolocalizationtable` | `POST /legacy-localization-tables/v1/autolocalization/games/{gameId}/autolocalizationtable` | `legacy-universe:manage` |
| `patch__legacy_localization_tables_v1_autolocalization_games_gameId_settings` | `PATCH /legacy-localization-tables/v1/autolocalization/games/{gameId}/settings` | `legacy-universe:manage` |
| `get__legacy_localization_tables_v1_autolocalization_metadata` | `GET /legacy-localization-tables/v1/autolocalization/metadata` | `legacy-universe:manage` |
| `get__legacy_localization_tables_v1_localization_table_limits` | `GET /legacy-localization-tables/v1/localization-table/limits` | `legacy-universe:manage` |
| `get__legacy_localization_tables_v1_localization_table_tables_assetId` | `GET /legacy-localization-tables/v1/localization-table/tables/{assetId}` | `legacy-universe:manage` |
| `get__legacy_localization_tables_v1_localization_table_tables_tableId` | `GET /legacy-localization-tables/v1/localization-table/tables/{tableId}` | `legacy-universe:manage` |
| `patch__legacy_localization_tables_v1_localization_table_tables_tableId` | `PATCH /legacy-localization-tables/v1/localization-table/tables/{tableId}` | `legacy-universe:manage` |
| `get__legacy_localization_tables_v1_localization_table_tables_tableId_entries` | `GET /legacy-localization-tables/v1/localization-table/tables/{tableId}/entries` | `legacy-universe:manage` |
| `post__legacy_localization_tables_v1_localization_table_tables_tableId_entries_translation_history` | `POST /legacy-localization-tables/v1/localization-table/tables/{tableId}/entries/translation-history` | `legacy-universe:manage` |
| `get__legacy_localization_tables_v1_localization_table_tables_tableId_entry_count` | `GET /legacy-localization-tables/v1/localization-table/tables/{tableId}/entry-count` | `legacy-universe:manage` |
| `OrderedDataStores_ListEntries` | `GET /ordered-data-stores/v1/universes/{universeId}/orderedDataStores/{orderedDataStore}/scopes/{scope}/entries` | `universe.ordered-data-store.scope.entry:read` |
| `OrderedDataStores_CreateEntry` | `POST /ordered-data-stores/v1/universes/{universeId}/orderedDataStores/{orderedDataStore}/scopes/{scope}/entries` | `universe.ordered-data-store.scope.entry:write` |
| `OrderedDataStores_DeleteEntry` | `DELETE /ordered-data-stores/v1/universes/{universeId}/orderedDataStores/{orderedDataStore}/scopes/{scope}/entries/{entry}` | `universe.ordered-data-store.scope.entry:write` |
| `OrderedDataStores_GetEntry` | `GET /ordered-data-stores/v1/universes/{universeId}/orderedDataStores/{orderedDataStore}/scopes/{scope}/entries/{entry}` | `universe.ordered-data-store.scope.entry:read` |
| `OrderedDataStores_UpdateEntry` | `PATCH /ordered-data-stores/v1/universes/{universeId}/orderedDataStores/{orderedDataStore}/scopes/{scope}/entries/{entry}` | `universe.ordered-data-store.scope.entry:write` |
| `OrderedDataStores_IncrementEntry` | `POST /ordered-data-stores/v1/universes/{universeId}/orderedDataStores/{orderedDataStore}/scopes/{scope}/entries/{entry}:increment` | `universe.ordered-data-store.scope.entry:write` |
| `PlaceVersion_GetPlaceContributors` | `GET /place-version-history-api/v1/{placeId}/contributors` | `universe.place:read` |
| `PlaceVersion_GetPlaceVersionHistory` | `GET /place-version-history-api/v1/{placeId}/history` | `universe.place:read` |
| `PlaceVersion_UpdatePlaceVersionNotes` | `POST /place-version-history-api/v1/{placeId}/version/{version}/notes` | `universe.place:write` |
| `GameServers_GetFilterOptions` | `GET /server-management/v1/universes/{universeId}/places/{placeId}/game-servers:filter-options` | `universe:read` |
| `GameServers_ListGameServers` | `GET /server-management/v1/universes/{universeId}/places/{placeId}/versions/{versionNumber}/game-servers` | `universe:read` |
| `GameServers_ListGameServerLogs` | `GET /server-management/v1/universes/{universeId}/places/{placeId}/versions/{versionNumber}/game-servers/{jobId}/logs` | `universe:read` |
| `Restarts_ListRestartStatuses` | `GET /server-management/v1/universes/{universeId}/restarts` | `universe:read` |
| `Restarts_LaunchRestart` | `POST /server-management/v1/universes/{universeId}/restarts` | `universe:write` |
| `Restarts_ForecastRestart` | `GET /server-management/v1/universes/{universeId}/restarts:forecast` | `universe:read` |
| `ThumbnailPersonalizationApi.HomepageThumbnail_FindThumbnailPersonalizations` | `GET /thumbnail-personalization-api/v1/universes/{universeId}/personalization` | `universe.thumbnail:read` |
| `ThumbnailPersonalizationApi.HomepageThumbnail_CreateThumbnailPersonalization` | `POST /thumbnail-personalization-api/v1/universes/{universeId}/personalization/create` | `universe.thumbnail:write` |
| `ThumbnailPersonalizationApi.HomepageThumbnail_UpdateThumbnailPersonalization` | `POST /thumbnail-personalization-api/v1/universes/{universeId}/personalization/update` | `universe.thumbnail:write` |
| `ThumbnailPersonalizationApi.HomepageThumbnail_DeleteHomepageThumbnails` | `DELETE /thumbnail-personalization-api/v1/universes/{universeId}/thumbnails` | `universe.thumbnail:write` |
| `ThumbnailPersonalizationApi.HomepageThumbnail_GetHomepageThumbnails` | `GET /thumbnail-personalization-api/v1/universes/{universeId}/thumbnails` | `universe.thumbnail:read` |
| `ThumbnailPersonalizationApi.HomepageThumbnail_UploadHomepageThumbnails` | `POST /thumbnail-personalization-api/v1/universes/{universeId}/thumbnails/uploads` | `universe.thumbnail:write` |
| `ThumbnailPersonalizationApi.HomepageThumbnail_GetHomepageThumbnailsStatus` | `GET /thumbnail-personalization-api/v1/universes/{universeId}/thumbnails/uploads/status` | `universe.thumbnail:read` |
| `Saves_DeleteSave` | `DELETE /toolbox-service/v1/saves` | `creator-store-save:write` |
| `Saves_GetSaves` | `GET /toolbox-service/v1/saves` | `creator-store-save:read` |
| `Saves_CreateSave` | `POST /toolbox-service/v1/saves` | `creator-store-save:write` |
| `Saves_BulkDeleteSaves` | `POST /toolbox-service/v1/saves:bulkDelete` | `creator-store-save:write` |
| `Toolbox_GetAssetDetails` | `GET /toolbox-service/v2/assets/{id}` | `creator-store-product:read` |
| `Toolbox_SearchCreatorStoreAssetsDeprecated` | `GET /toolbox-service/v2/assets:search` | `creator-store-product:read` |
| `Toolbox_SearchCreatorStoreAssets` | `POST /toolbox-service/v2/assets:search` | `creator-store-product:read` |
| `Places_CreatePlaceVersionApiKey` | `POST /universes/v1/{universeId}/places/{placeId}/versions` | `universe-places:write` |
| `GameEvent_Delete` | `DELETE /virtual-events/v3/game-events/{eventId}` | `universe.event:write` |
| `GameEvent_Get` | `GET /virtual-events/v3/game-events/{eventId}` | `universe.event:read` |
| `GameEvent_Update` | `PATCH /virtual-events/v3/game-events/{eventId}` | `universe.event:write` |
| `GameEvents_List` | `GET /virtual-events/v3/universes/{universeId}/game-events` | `universe.event:read` |
| `GameEvents_Create` | `POST /virtual-events/v3/universes/{universeId}/game-events` | `universe.event:write` |
