#!/usr/bin/env python3
"""Offline-Abnahme für Arena Roblox Bridge 7.5.9 - ROBLOX OPEN CLOUD UPLOAD.

Was dieses Update ausmacht (und was hier geprüft wird):

1. DAS MESH-FENSTER IST WEG. Kein Fenster "Mesh-Uploads", kein Menüeintrag,
   kein Abtippen von Mesh-Ids durch den Nutzer. (Die Bestandsabnahme des
   Blender-Wegs liegt weiter in test_v740_mesh.py.)
2. DER NUTZER HINTERLEGT SEINEN EIGENEN OPEN-CLOUD-API-SCHLÜSSEL im
   Einstellungsfenster (Abschnitt ROBLOX OPEN CLOUD) - verschlüsselt, nur auf
   diesem PC, nie im Klartext in einer Einstellungsdatei oder im Log.
3. DAS TUTORIAL DORT IST AUFKLAPPBAR UND ANIMIERT und nennt die RECHTE, ohne
   die Roblox jeden Upload mit 403 ablehnt: ASSETS + LESEN + SCHREIBEN.
4. upload_asset lädt MESHES (FBX/GLB aus Blender) und BILDER (auch selbst
   erzeugte, direkt als Base64) über die offizielle Roblox-Schnittstelle hoch
   und antwortet mit der ECHTEN Asset-Id.
5. FEHLT DER SCHLÜSSEL, bleibt das Werkzeug verfügbar und sagt dem Agenten
   einen deutschen Satz, den er dem Nutzer WÖRTLICH weitergibt.
6. ROBLOX-FEHLER (Rate-Limit, abgelehnter Schlüssel, 5xx, 400, Netz) gehen
   unverfälscht an den Agenten weiter - mit Status und Originaltext.

Neben den Strukturprüfungen gibt es einen AUSFÜHRBAREN MODELLTEST: ein
kleiner HTTP-Server spielt die Roblox-Assets-API nach (inklusive
Operations-Polling), und die Status->Fehlercode-Tabelle sowie die
Dateiendungs-Tabelle werden dafür AUS DER PS1 GELESEN - weicht die Bridge
von der dokumentierten Abbildung ab, schlägt der Test rot an.
"""
from __future__ import annotations

import base64
import json
import re
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP_ROOT = ROOT / "app"
def _shipped_build_version() -> str:
    """Version aus app/version.json: so setzt der Builder den Platzhalter im Quelltext."""
    import json
    from pathlib import Path as _P
    return json.loads((_P(__file__).resolve().parents[2] / "app" / "version.json").read_text(encoding="utf-8"))["version"]


PS1 = APP_ROOT / "ArenaBridge.ps1"
VERSION = _shipped_build_version()
FAILURES: list[str] = []


def check(condition: bool, message: str) -> None:
    print(("[GRÜN] " if condition else "[ROT]   ") + message)
    if not condition:
        FAILURES.append(message)


def region(source: str, start: str, end: str) -> str:
    begin = source.index(start)
    stop = source.index(end, begin)
    return source[begin:stop]


# ======================================================================
# Ausführbarer Modelltest: Roblox-Assets-API nachgespielt
# ======================================================================
class FakeRoblox(BaseHTTPRequestHandler):
    """Spielt apis.roblox.com/assets/v1 nach (Upload + Operations-Polling)."""

    mode = "ok"          # ok | ratelimit | rejected
    log: list[dict] = []

    def log_message(self, *args: object) -> None:  # kein Konsolenlärm
        return

    def _send(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:  # noqa: N802 - HTTP-Methodenname
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        FakeRoblox.log.append({
            "path": self.path,
            "apiKey": self.headers.get("x-api-key", ""),
            "contentType": self.headers.get("Content-Type", ""),
            "body": raw,
        })
        if FakeRoblox.mode == "ratelimit":
            self._send(429, {"error": "TooManyRequests"})
            return
        if FakeRoblox.mode == "rejected":
            self._send(403, {"error": "Forbidden"})
            return
        self._send(200, {"path": "operations/op-42", "done": False})

    def do_GET(self) -> None:  # noqa: N802 - HTTP-Methodenname
        FakeRoblox.log.append({"path": self.path, "method": "GET"})
        if self.path.endswith("/operations/op-42"):
            self._send(200, {"done": True, "response": {"assetId": "11833722194"}})
            return
        self._send(404, {"error": "NotFound"})


def parse_status_map(fn: str) -> dict[str, str]:
    """Liest die Status->Code-Abbildung aus ConvertTo-OpenCloudHttpError."""
    mapping: dict[str, str] = {}
    pattern = re.compile(
        r"if \(\$Status -(?P<op>eq|ge) (?P<value>\d+)(?: -or \$Status -eq (?P<second>\d+))?\) \{\s*"
        r"(?:.|\n)*?code = '(?P<code>[A-Z_]+)'")
    for match in pattern.finditer(fn):
        op = match.group("op")
        mapping[("ge" if op == "ge" else "eq") + ":" + match.group("value")] = match.group("code")
        if match.group("second"):
            mapping["eq:" + match.group("second")] = match.group("code")
    tail = re.search(r"return @\{\s*\n\s*ok = \$false; code = '(?P<code>[A-Z_]+)'\s*\n\s*error = \('Roblox hat den '", fn)
    if tail:
        mapping["fallback"] = tail.group("code")
    return mapping


def parse_extension_map(fn: str) -> dict[str, tuple[str, str]]:
    """Liest die Dateiendungs-Tabelle aus Get-OpenCloudAssetSpec."""
    found: dict[str, tuple[str, str]] = {}
    for ext, asset, ctype in re.findall(
            r"'\.(?P<ext>fbx|glb|gltf|png|jpg|jpeg|bmp|tga)'\s*=\s*@\{\s*assetType = '(?P<asset>[A-Za-z]+)';\s*contentType = '(?P<ctype>[^']+)'", fn):
        found["." + ext] = (asset, ctype)
    return found


def model_upload(base_url: str, api_key: str, file_name: str, payload: bytes,
                 asset_type: str, creator_id: str, status_map: dict[str, str]) -> dict:
    """Fährt genau den Weg, den die Bridge fähren muss (Modell, nicht PS-Code)."""
    import urllib.error
    import urllib.request

    meta = json.dumps({
        "assetType": asset_type,
        "displayName": "Modell",
        "description": "Hochgeladen von Arena Roblox Bridge.",
        "creationContext": {"creator": {"userId": creator_id}, "expectedPrice": 0},
    }).encode("utf-8")

    boundary = "----arena-bridge-750"
    parts = b""
    parts += (f"--{boundary}\r\n"
              f"Content-Type: application/json\r\n"
              f'Content-Disposition: form-data; name="request"\r\n\r\n').encode("utf-8")
    parts += meta + b"\r\n"
    parts += (f"--{boundary}\r\n"
              f"Content-Disposition: form-data; name=\"fileContent\"; filename=\"{file_name}\"\r\n\r\n").encode("utf-8")
    parts += payload + b"\r\n"
    parts += f"--{boundary}--\r\n".encode("utf-8")

    request = urllib.request.Request(base_url + "/assets/v1/assets", data=parts, method="POST")
    request.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    request.add_header("x-api-key", api_key)
    try:
        with urllib.request.urlopen(request, timeout=20) as answer:
            status = answer.status
            body = json.loads(answer.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:  # 4xx/5xx tragen den Roblox-Text
        status = exc.code
        body = json.loads(exc.read().decode("utf-8") or "{}")

    if status < 200 or status > 299:
        code = status_map.get("eq:" + str(status))
        if code is None and status >= 500:
            code = status_map.get("ge:500")
        if code is None:
            code = status_map.get("fallback", "")
        return {"ok": False, "code": code, "status": status,
                "robloxResponse": json.dumps(body), "assetId": ""}

    operation = str(body.get("path", "")).rsplit("/", 1)[-1]
    # Operations-Polling: die echte Id kommt erst, wenn Roblox fertig ist.
    with urllib.request.urlopen(base_url + f"/assets/v1/operations/{operation}", timeout=20) as answer:
        final = json.loads(answer.read().decode("utf-8"))
    asset_id = str(((final.get("response") or {}).get("assetId")) or "")
    return {"ok": bool(asset_id), "code": "UPLOADED", "status": 200,
            "operationId": operation, "assetId": asset_id}


def run_model_test(status_map: dict[str, str]) -> None:
    print("\n9) Ausführbarer Modelltest gegen eine nachgespielte Roblox-API")
    server = HTTPServer(("127.0.0.1", 0), FakeRoblox)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        # --- Erfolg: Mesh (FBX) -------------------------------------------
        FakeRoblox.mode = "ok"
        FakeRoblox.log = []
        result = model_upload(base, "RBX-KEY-4711", "drache.fbx", b"FAKE-FBX",
                              "Model", "1234567", status_map)
        check(result["ok"] and result["assetId"] == "11833722194",
              "der Modell-Upload endet mit der ECHTEN Asset-Id aus der Roblox-Antwort")
        check(result["code"] == "UPLOADED", "erfolgreicher Upload meldet UPLOADED")
        post = FakeRoblox.log[0]
        check(post["apiKey"] == "RBX-KEY-4711",
              "der Schlüssel reist im Header x-api-key (nicht in der URL, nicht im Body)")
        check("multipart/form-data" in post["contentType"],
              "die Anfrage ist multipart/form-data")
        body = post["body"].decode("utf-8", "replace")
        check('name="request"' in body and 'name="fileContent"' in body,
              "die Anfrage hat genau die zwei Felder request (Metadaten) und fileContent (Datei)")
        check('filename="drache.fbx"' in body,
              "der Dateiname reist mit (Roblox leitet die Endung daraus ab)")
        check('"assetType":"Model"' in body.replace(" ", ""),
              "die Metadaten nennen den assetType")
        check('"expectedPrice":0' in body.replace(" ", ""),
              "die Metadaten verlangen keinen Robux-Preis (expectedPrice 0)")
        check(any(entry.get("method") == "GET" and "/operations/op-42" in entry["path"]
                  for entry in FakeRoblox.log),
              "die asynchrone Operation wird über GET /assets/v1/operations/<id> abgefragt")

        # --- Rate-Limit ---------------------------------------------------
        FakeRoblox.mode = "ratelimit"
        result = model_upload(base, "RBX-KEY-4711", "bild.png", b"FAKE-PNG",
                              "Decal", "1234567", status_map)
        check(result["code"] == "OPENCLOUD_RATE_LIMITED" and result["status"] == 429,
              "HTTP 429 wird zu OPENCLOUD_RATE_LIMITED (kein Erfinden, kein Verschweigen)")

        # --- Abgelehnter Schlüssel ---------------------------------------
        FakeRoblox.mode = "rejected"
        result = model_upload(base, "RBX-KEY-4711", "drache.fbx", b"FAKE-FBX",
                              "Model", "1234567", status_map)
        check(result["code"] == "OPENCLOUD_KEY_REJECTED" and result["status"] == 403,
              "HTTP 403 wird zu OPENCLOUD_KEY_REJECTED (falsche Rechte -> Upload unmöglich)")
        check("Forbidden" in result["robloxResponse"],
              "die Originalantwort von Roblox bleibt erhalten (robloxResponse)")
    finally:
        server.shutdown()
        server.server_close()


def main() -> int:
    raw = PS1.read_bytes()
    check(raw.startswith(b"\xef\xbb\xbf"), "ArenaBridge.ps1 behält die UTF-8-BOM")
    source = raw.decode("utf-8-sig").replace("__ARENA_BUILD_VERSION__", _shipped_build_version())

    metadata = json.loads((APP_ROOT / "version.json").read_text(encoding="utf-8"))
    notes = "\n".join(str(note) for note in metadata.get("notes", []))
    latest_note = next((str(n) for n in metadata.get("notes", []) if str(n).startswith("• 7.8.0")), "")
    check(metadata.get("version") == VERSION, f"version.json steht auf {VERSION}")
    for phrase in ("Open Cloud", "upload_asset", "MESH-FENSTER", "ASSETS",
                   "creator_dashboard", "game-pass:read", "developer-product:write"):
        check(phrase.casefold() in notes.casefold(), f"Release history retains: {phrase}")
    check("API-Pfade" in latest_note and "Ressourcen-IDs" in latest_note
          and "Antwortwerte" in latest_note,
          "the current release note confirms sensitive Open Cloud paths, IDs and values stay out of history")

    # ------------------------------------------------------------------
    # 1) Das Mesh-Fenster ist entfernt
    # ------------------------------------------------------------------
    print("\n1) Mesh-Fenster ist entfernt (ausdrücklicher Nutzerwunsch)")
    for gone in ("function Get-MeshWindowXaml", "function Open-MeshWindow",
                 "function Update-MeshWindow", "function Update-MeshAutoWindow",
                 "$script:MeshWindow", "$script:MeshAutoOpenPending"):
        check(gone not in source, f"entfernt: {gone}")
    check("upload_asset" in source, "upload_asset ist der neue Weg (kein Fenster)")

    # ------------------------------------------------------------------
    # 2) Der Schlüssel: verschlüsselt, nur lokal, nie im Log
    # ------------------------------------------------------------------
    print("\n2) Open-Cloud-Schlüssel: verschlüsselt abgelegt, nie im Klartext")
    key_fn = region(source, "function Get-OpenCloudKeyPath {", "function Get-OpenCloudConfig {")
    check("'opencloud.key'" in key_fn, "der Schlüssel liegt in einer eigenen Datei opencloud.key")
    check("ProtectedData]::Protect(" in key_fn and "DataProtectionScope]::CurrentUser" in key_fn,
          "der Schlüssel wird per DPAPI im Kontext des angemeldeten Nutzers verschlüsselt")
    check("'dpapi:'" in key_fn and "'plain:'" in key_fn,
          "ohne DPAPI wird der Klartext sichtbar als solcher markiert (keine vorgetäuschte Sicherheit)")
    get_key = region(source, "function Get-OpenCloudKey {", "function Set-OpenCloudKey {")
    check("OpenCloudKeyCache" in get_key,
          "der entschlüsselte Schlüssel liegt nur im Speicher der Bridge (Cache)")
    check("Nie in settings.json, nie im Log" in get_key,
          "der Quelltext sagt ausdrücklich: nie in settings.json, nie im Log")

    settings_block = region(source, "function Get-BridgeSettingsFile {", "function Save-BridgeSettingsFile {")
    save_block = region(source, "function Save-BridgeSettingsFile {", "function Get-MeshSlotData {")
    check("openCloudKey = " not in settings_block and "openCloudKey =" not in save_block,
          "der Schlüssel selbst wird NICHT in settings.json geschrieben")
    for marker in ("openCloudKeySet", "openCloudKeyHint", "openCloudCreatorId",
                   "openCloudCreatorKind", "openCloudCreatorName", "openCloudSavedAt"):
        check(marker in settings_block, f"die Einstellungen tragen {marker} (Zustand ja/nein, kein Schlüssel)")
    leaked = [line.strip() for line in source.splitlines()
              if ("Write-BridgeLog" in line or "Write-RuntimeLog" in line)
              and ("$Key" in line or "config.key" in line or "$keyText" in line)]
    check(not leaked, "kein Log-Aufruf schreibt den Schlüssel mit (weder roh noch entschlüsselt)")

    # ------------------------------------------------------------------
    # 3) Ersteller: Roblox ordnet jedes Asset jemandem zu
    # ------------------------------------------------------------------
    print("\n3) Ersteller: Studio-Anmeldung zuerst, Key-Resource als automatischer Rückfall (kein manuelles Feld)")
    introspect = region(source, "function Invoke-OpenCloudIntrospect {", "function Resolve-OpenCloudCreatorFromKey {")
    check("https://apis.roblox.com/api-keys/v1/introspect" in introspect,
          "die Selbstauskunft nutzt den offiziellen Introspect-Endpunkt")
    check("apiKey = $clean" in introspect,
          "die Selbstauskunft schickt den Schlüssel im JSON-Body (apiKey)")
    check("assetRead" in introspect and "assetWrite" in introspect,
          "die Scopes werden in ASSETS read/write übersetzt")
    check("writeUserIds" in introspect and "writeGroupIds" in introspect,
          "die erlaubten Nutzer-/Gruppen-Ressourcen werden gelesen")
    resolve = region(source, "function Resolve-OpenCloudCreatorFromKey {", "function Test-OpenCloudKeyAuth {")
    check("authorizedUserId" in resolve,
          "als Rückfall dient der autorisierte Nutzer des Schlüssels")
    check("openCloudCreatorId" in resolve and "openCloudCreatorKind" in resolve,
          "der Ersteller wird aus dem Schlüssel in die Einstellungen geschrieben")
    check("Resolve-OpenCloudCreatorId" not in source,
          "der alte Namens-/ID-Pfad ist entfernt (der Nutzer trägt nichts ein)")
    studio = region(source, "function Get-OpenCloudStudioDeveloper {", "function Resolve-OpenCloudCreatorForUpload {")
    creator_for_upload = region(source, "function Resolve-OpenCloudCreatorForUpload {", "function Invoke-OpenCloudUpload {")
    check("$entry.editorUserId" in studio and "creatorKind = 'user'" in studio,
          "StudioService-User-ID wird aus der Sitzung als Nutzer-Creator verwendet")
    check(creator_for_upload.index("Get-OpenCloudStudioDeveloper") < creator_for_upload.index("Resolve-OpenCloudCreatorFromKey"),
          "die in Roblox Studio angemeldete Person hat Vorrang vor der Key-Resource")
    check("StudioService:GetUserId()" in source and "payload.editorUserId" in source,
          "das Plugin meldet die echte Roblox-Studio-Anmeldung")
    for gone in ("openCloudDeveloperId", "openCloudDeveloperName", "CloudDeveloperBox",
                 "CloudDeveloperButton", "CloudDeveloperPanel", "CloudDeveloperStatus"):
        check(gone not in source, f"manuelle Entwickler-Fallback-Eingabe entfernt: {gone}")
    check("'group'" in source and "openCloudCreatorKind" in source,
          "auch eine GRUPPE kann Ersteller sein (wird gemessen)")
    check("$creator['groupId']" in source and "$creator['userId']" in source,
          "der Upload unterscheidet Nutzer- und Gruppen-Ersteller")
    check("creationContext" in source and "creator = $creator" in source,
          "die Metadaten tragen creationContext.creator (so verlangt es die API)")
    upload_catalog = region(source, "$t.Add(@{ name = 'upload_asset'", "# ---------------- JOBS ----------------")
    check("StudioService:GetUserId()" in upload_catalog and "editorUserId" in upload_catalog
          and "Nur wenn keine gültige Studio-ID vorliegt" in upload_catalog,
          "upload_asset dokumentiert die Studio-ID-Priorität und den automatischen Key-Rückfall")
    check("ASSETS write für das angemeldete Studio-Konto" in upload_catalog,
          "upload_asset erklärt das erforderliche Recht für den Studio-Nutzer")

    # ------------------------------------------------------------------
    # 4) Das Protokoll: Endpunkt, Multipart, Polling, Grenzen
    # ------------------------------------------------------------------
    print("\n4) Upload-Protokoll (offizielle Assets-API)")
    upload = region(source, "function Invoke-OpenCloudUpload {", "function Get-OpenCloudOperation {")
    check("https://apis.roblox.com/assets/v1/assets" in upload,
          "hochgeladen wird über POST https://apis.roblox.com/assets/v1/assets")
    transport = region(source, "function Send-OpenCloudHttp {", "function Get-OpenCloudTransportError {")
    client_fn = region(source, "function New-OpenCloudHttpClient {", "function New-OpenCloudMultipartBytes {")
    multipart = region(source, "function New-OpenCloudMultipartBytes {", "function Send-OpenCloudRequestFallback {")
    check("x-api-key" in client_fn and "TryAddWithoutValidation" in client_fn,
          "der Schlüssel reist als Header x-api-key")
    check("Send-OpenCloudHttp" in upload and "config.key" in upload,
          "der Upload übergibt den Schlüssel an den Transport")
    check("'multipart/form-data; boundary='" in transport
          and "New-OpenCloudMultipartBytes" in transport,
          "die Anfrage ist multipart/form-data (für den zweiten Transportweg von Hand gebaut)")
    field_marker = r'''name="' + [string]$FieldName + '"; filename="'''
    check('name="request"' in multipart and field_marker in multipart,
          "die Anfrage hat die zwei Felder request und fileContent")
    check("assets/v1/operations/" in source,
          "die asynchrone Operation wird über /assets/v1/operations/<id> abgefragt")
    check("20971520" in upload, "die 20-MB-Grenze von Roblox wird geprüft (20971520 Bytes)")
    for code in ("FILE_NOT_FOUND", "FILE_UNREADABLE", "FILE_EMPTY", "FILE_TOO_LARGE"):
        check(code in upload, f"Dateifehler werden ehrlich gemeldet: {code}")

    spec = region(source, "function Get-OpenCloudAssetSpec {", "function New-OpenCloudHttpClient {")
    expected_types = {".fbx": ("Model", "model/fbx"),
                      ".glb": ("Model", "model/gltf-binary"),
                      ".gltf": ("Model", "model/gltf+json"),
                      ".png": ("Decal", "image/png"),
                      ".jpg": ("Decal", "image/jpeg"),
                      ".jpeg": ("Decal", "image/jpeg"),
                      ".bmp": ("Decal", "image/bmp"),
                      ".tga": ("Decal", "image/tga")}
    found_types = parse_extension_map(spec)
    check(found_types == expected_types,
          f"die Endungs-Tabelle stimmt ({len(found_types)} Einträge, Meshes=Model, Bilder=Decal)")
    check("'.obj'" in spec and "nimmt KEIN OBJ an" in spec,
          "OBJ wird abgelehnt - mit dem Hinweis auf die FBX-Datei aus mesh_status")
    check("UNSUPPORTED_FORMAT" in spec and "BAD_ARGS" in spec,
          "unpassende Endung und unpassender assetType werden unterschieden")

    # ------------------------------------------------------------------
    # 5) Fehler: unverfälscht an den Agenten, mit einem Satz für den Nutzer
    # ------------------------------------------------------------------
    print("\n5) Fehler und fehlender Schlüssel")
    errors_fn = region(source, "function ConvertTo-OpenCloudHttpError {", "function Invoke-OpenCloudUpload {")
    status_map = parse_status_map(errors_fn)
    check(status_map.get("eq:429") == "OPENCLOUD_RATE_LIMITED", "429 -> OPENCLOUD_RATE_LIMITED")
    check(status_map.get("eq:401") == "OPENCLOUD_KEY_REJECTED", "401 -> OPENCLOUD_KEY_REJECTED")
    check(status_map.get("eq:403") == "OPENCLOUD_KEY_REJECTED", "403 -> OPENCLOUD_KEY_REJECTED")
    check(status_map.get("ge:500") == "OPENCLOUD_SERVER_ERROR", "5xx -> OPENCLOUD_SERVER_ERROR")
    check(status_map.get("fallback") == "OPENCLOUD_UPLOAD_REJECTED", "alles andere -> OPENCLOUD_UPLOAD_REJECTED")
    check("robloxResponse = $Body" in errors_fn,
          "jeder Fehler trägt die unveränderte Roblox-Antwort (robloxResponse)")
    check("Nichts wird schöngeredet, nichts erfunden" in errors_fn,
          "die Regel steht im Quelltext: nichts wird schöngeredet")

    missing = region(source, "function Assert-OpenCloudToolAccess {", "function Get-OpenCloudAssetSpec {")
    check("OPENCLOUD_KEY_MISSING" in missing and "userMessage" in missing,
          "ohne Schlüssel antwortet das Werkzeug OPENCLOUD_KEY_MISSING MIT einem Nutzer-Satz")
    check("Bridge-Einstellungen" in missing and "Roblox Open Cloud API-Key" in missing,
          "der Satz nennt den Weg: Einstellungen -> Roblox Open Cloud API-Key")
    check("WORTLICH" in missing, "der Agent wird angewiesen, den Satz WÖRTLICH zu sagen")
    check("OPENCLOUD_KEY_HAS_EXPIRATION" in missing and "No Expiration" in missing,
          "ein Key mit Ablaufdatum wird komplett abgelehnt")
    check("OPENCLOUD_SCOPE_INCOMPLETE" in missing and "Test-OpenCloudPermission" in missing,
          "fehlende Read/Write-Rechte am Scope werden vor dem Aufruf blockiert")
    check("OPENCLOUD_CREATOR_MISSING" in source, "fehlt der Ersteller, meldet das Werkzeug das getrennt")
    for code in ("OPENCLOUD_UNREACHABLE", "OPENCLOUD_BAD_RESPONSE", "OPENCLOUD_OPERATION_FAILED",
                 "NO_UPLOAD_FILE", "UNKNOWN_SLOT", "PATH_OUTSIDE_BRIDGE"):
        check(code in source, f"Fehlercode vorhanden: {code}")
    transport_error = region(source, "function Get-OpenCloudTransportError {", "function Get-OpenCloudErrorBody {")
    check("Der Schlüssel wurde NICHT verbraucht" in transport_error,
          "bei einem Netzfehler sagt das Werkzeug ehrlich, dass der Schlüssel nicht verbraucht wurde")

    # ------------------------------------------------------------------
    # 6) Das Werkzeug upload_asset
    # ------------------------------------------------------------------
    print("\n6) Werkzeug upload_asset")
    docs = region(source, "# ---------------- MESH / BLENDER", "# ---------------- JOBS ----------------")
    check("name = 'upload_asset'" in docs, "upload_asset hat einen Doku-Eintrag (Kategorie cloud)")
    for arg in ("slotKey", "filePath", "contentBase64", "fileName", "operationId", "assetType"):
        check(arg in docs, f"die Doku nennt das Argument {arg}")
    handler = region(source, "function Invoke-OpenCloudServerTool($sessionId", "function Invoke-ServerTool($sessionId")
    check("'upload_asset'       { return (Invoke-OpenCloudServerTool" in source,
          "upload_asset ist im Server-Handler verdrahtet")
    check("OpenCloudToolsText" in handler,
          "der Handler lädt die EINE Werkzeug-Quelle (keine Phantom-Funktionen im Runspace)")
    check("PATH_OUTSIDE_BRIDGE" in handler and "StartsWith" in handler,
          "ein filePath außerhalb des Bridge-Ordners wird abgelehnt")
    check("FromBase64String" in handler,
          "contentBase64 wird dekodiert - der Agent kann ein selbst erzeugtes Bild direkt senden")
    check("contentBase64 fehlt fileName" in handler,
          "zu contentBase64 wird fileName verlangt (die Endung bestimmt den Asset-Typ)")
    check("already_uploaded" in handler and "forceNew" in handler,
          "ein schon hochgeladener Slot wird nicht doppelt hochgeladen (forceNew erzwingt es)")
    check("rbxassetid://" in handler, "die Antwort enthält die einsetzbare rbxassetid://-Form")
    check("state = 'pending'" in handler,
          "ein längerer Upload antwortet state=pending mit operationId (kein enges Polling)")
    check("waitSeconds -gt 45" in handler, "die Wartezeit ist gedeckelt (kein endloser Aufruf)")

    # ------------------------------------------------------------------
    # 7) Einstellungsfenster: Karte, Tutorial, Animation
    # ------------------------------------------------------------------
    print("\n7) Einstellungsfenster: ROBLOX OPEN CLOUD (Studio-ID + Key-Speicherung)")
    settings_xaml = region(source, "$settingsXaml = @'", "\n'@")
    # Die erste Zeile ist noch PowerShell ($settingsXaml = @') - weg damit.
    settings_xaml = settings_xaml[settings_xaml.index("\n") + 1:]
    try:
        from xml.etree import ElementTree as ET
        ET.fromstring(settings_xaml.replace("x:Name", "Name").replace("x:Key", "Key"))
        xml_ok = True
    except Exception as exc:  # noqa: BLE001 - der Parse-Fehler ist die Aussage
        xml_ok = False
        print("       XML-Fehler:", exc)
    check(xml_ok, "das Einstellungs-XAML ist wohlgeformt (XML-Parse)")
    for name in ("CloudMissingPanel", "CloudMissingText", "CloudKeyBox", "CloudSaveButton",
                 "CloudSaveHint", "CloudReadyPanel", "CloudReadyText", "CloudReadyNote",
                 "CloudRemoveButton", "CloudOpenDashboardButton",
                 "CloudTutorialHeader", "CloudTutorialChevron", "CloudTutorialToggle",
                 "CloudTutorialWrap", "CloudTutorialBody"):
        check(f'x:Name="{name}"' in settings_xaml, f"Einstellungen enthalten {name}")
    for gone in ("CloudTestButton", "CloudStatusText", "CloudCreatorBox", "CloudCreatorKind",
                 "CloudCreatorHint", "CloudDeveloperBox", "CloudDeveloperButton",
                 "CloudDeveloperPanel", "CloudDeveloperStatus"):
        check(f'x:Name="{gone}"' not in settings_xaml,
              f"das alte Element {gone} ist aus den Einstellungen verschwunden")
    for step in range(1, 8):
        check(f'x:Name="CloudStep{step}"' in settings_xaml,
              f"Tutorial-Schritt CloudStep{step} vorhanden")
    for step in range(8, 11):
        check(f'x:Name="CloudStep{step}"' not in settings_xaml,
              f"das alte Tutorial hat nur noch 7 Schritte (CloudStep{step} ist weg)")
    check('Text="Roblox Open Cloud API-Key"' in settings_xaml,
          "der Abschnitt heißt Roblox Open Cloud API-Key")
    check("Der Key ist Arenas Zugang zu Roblox" in settings_xaml
          and "kein Ablaufdatum" in settings_xaml,
          "der Key-Abschnitt erklärt den Key und dass ein Ablaufdatum abgelehnt wird")
    check('x:Name="CreatorDashboardSwitch"' not in settings_xaml,
          "der Creator-Dashboard-Opt-in-Schalter ist aus den Einstellungen entfernt (7.6.0)")
    check('x:Name="CloudPermissionList"' in settings_xaml
          and 'x:Name="CloudPermissionsButton"' in settings_xaml,
          "Tutorial-Berechtigungsliste und der Knopf Berechtigungen ansehen sind im XAML")
    check('Text="Noch kein API-Key hinzugefügt!"' in settings_xaml,
          "ohne Schlüssel steht der rote Hinweis Noch kein API-Key hinzugefügt!")
    check('Text="API-Key ist eingerichtet!"' in settings_xaml,
          "mit Schlüssel steht der grüne Hinweis API-Key ist eingerichtet!")
    check("PasswordBox" in settings_xaml,
          "der Schlüssel wird in einem PasswordBox-Feld eingegeben")

    tutorial = region(settings_xaml, 'x:Name="CloudTutorialWrap"', '<TextBlock Text="UPDATES"')
    for piece in ("1. Öffne diese Seite:", "API-Schlüssel erstellen",
                  "irgendeinen Namen und eine Beschreibung",
                  "Füge die Berechtigungen hinzu, die du willst! Hier siehst du eine ausführliche Liste, was jede Berechtigung kann:",
                  "No Expiration",
                  "Erstelle den Schlüssel und kopiere ihn sofort",
                  "Füge den Schlüssel hier ein und drücke Speichern.",
                  "Speichern öffnet sofort ein Fenster"):
        check(piece in tutorial, f"das Tutorial nennt: {piece}")
    catalog = region(source, "function Get-CloudPermissionCatalog {", "function New-CloudPermissionRow {")
    permissions = json.loads((APP_ROOT / "opencloud/permissions.json").read_text(encoding="utf-8"))
    check("(Get-OpenCloudCatalog).permissions.PSObject.Properties" in catalog,
          "permission UI uses the shared exact-permission catalog")
    check(len(permissions) == 41 and "asset:read" in permissions and "asset:write" in permissions,
          "all 41 individual permissions are documented, read/write separately")
    check("memory-store" not in catalog and "user.user-notification" not in catalog,
          "ungenutzte Scopes sind aus dem Tutorial-Katalog entfernt")
    check("create.roblox.com/dashboard/credentials" in tutorial,
          "das Tutorial nennt die echte Adresse create.roblox.com/dashboard/credentials")
    check('Text="&#xE71B;"' in tutorial,
          "der Link-Knopf nutzt dasselbe Glyph wie der Stil 'Arena AI öffnen'")
    check("weigert sich die Bridge komplett" in tutorial, "das Tutorial sagt klar: Ablaufdatum = Bridge weigert sich")
    check('MaxHeight="0"' in tutorial and 'Opacity="0"' in tutorial,
          "das Tutorial startet eingeklappt (MaxHeight/Opacity 0)")
    check('ClipToBounds="True"' in tutorial, "der Aufklapp-Bereich clippt (kein Herauslaufen)")

    code_start = source.index("$settingsWindow.FindName('CloudKeyBox')")
    code = source[code_start:source.index("# 7.2.3: Die Test-Benachrichtigung ist vollständig")]
    check("$cloudSaveButton.Add_Click" in code and "$cloudRemoveButton.Add_Click" in code
          and "$cloudDashboardButton.Add_Click" in code
          and "$cloudPermissionsButton.Add_Click" in code,
          "Speichern, Entfernen, der Dashboard-Link und Berechtigungen ansehen sind verdrahtet")
    check("$creatorDashboardSwitch" not in code,
          "der entfernte Creator-Dashboard-Schalter ist nirgends mehr verdrahtet")
    check("Set-OpenCloudKey" in code and "Get-OpenCloudKey" in code and "Remove-OpenCloudKey" in code,
          "die Knöpfe benutzen die eine Schlüssel-Quelle")
    save_click = region(code, "$cloudSaveButton.Add_Click({", "# --- Berechtigungen des gespeicherten Schlüssels ansehen")
    check("Set-OpenCloudKey" not in save_click and "Save-BridgeSettingsFile" not in save_click,
          "Speichern speichert NICHT sofort - erst Introspect, dann das Berechtigungs-Fenster")
    check("Show-CloudPermissionsWindow -PendingKey $keyText" in save_click
          and "Start-CloudIntrospectRun" not in save_click,
          "Speichern öffnet das Berechtigungs-Fenster sofort; Introspect läuft im Fenster")
    perm_window = region(code, "function Show-CloudPermissionsWindow {", "# --- Tutorial: ANIMIERT auf- und zuklappen")
    check("Oh, das ändere ich nochmal!" in perm_window
          and "Ja, alles richtig! Key speichern!" in perm_window,
          "das Berechtigungs-Fenster hat die beiden Entscheidungs-Knöpfe")
    check("Save-OpenCloudKeyFromText" in perm_window,
          "gespeichert wird erst nach dem Ja-Knopf (Save-OpenCloudKeyFromText)")
    check("nichts wurde gespeichert" in perm_window,
          "bei fehlgeschlagener Prüfung sagt das Fenster ehrlich, dass nichts gespeichert wurde")
    check("Save-BridgeSettingsFile" in code, "Speichern legt die Einstellungen dauerhaft ab")
    check("Sync-CloudSharedSettings" in code,
          "die Werte werden nach $Shared gespiegelt (Handler laufen in eigenen Runspaces)")
    for marker in ("openCloudKeySet", "openCloudCreatorId", "openCloudCreatorKind",
                   "openCloudCreatorName", "openCloudSavedAt", "openCloudKeyHint"):
        check(marker in code, f"Sync-CloudSharedSettings übergibt {marker}")
    check("creatorDashboardEnabled" not in code,
          "die entfernte Einstellung creatorDashboardEnabled taucht im Code nicht mehr auf")
    check("Length -lt 20" in code, "zu kurze Schlüssel werden abgelehnt (kein sinnloser Speicherlauf)")
    check("Update-CloudPanelState" in code and "CloudMissingPanel" in code and "CloudReadyPanel" in code,
          "die zwei Zustände schaltet Update-CloudPanelState")
    check("Start-CloudIntrospectRun" in code and "Invoke-OpenCloudIntrospect" in code,
          "die Prüfung läuft über den offiziellen Introspect-Endpunkt")
    check("Apply-CloudIntrospectVerdict" in code,
          "das Ergebnis der Selbstauskunft wird ehrlich angezeigt")
    check("developer-product:write" in source and "universe.place:write" in source
          and "OPENCLOUD_SCOPE_INCOMPLETE" in source,
          "Introspect und UI-Feedback berücksichtigen die zusätzlichen Creator-Dashboard-Scopes")
    check("DispatcherTimer" in code and "BeginInvoke" in code,
          "die Prüfung läuft im Hintergrund (kein eingefrorenes Fenster)")
    check("StudioService:GetUserId()" in source and "Berechtigungen ansehen" in code,
          "die gespeicherte-Key-Ansicht bleibt und Studio liefert weiter die Upload-Identität")

    anim = region(source, "$cloudSteps = New-Object System.Collections.Generic.List[object]",
                  "$cloudDashboardButton.Add_Click")
    check("DoubleAnimation" in anim and "MaxHeightProperty" in anim,
          "das Aufklappen animiert die Höhe (DoubleAnimation auf MaxHeight)")
    check("MaxHeight = 100000" in anim and "UpdateLayout()" in anim,
          "die Zielhöhe wird GEMESSEN (MaxHeight auf, UpdateLayout, zurück)")
    check("RotateTransform" in anim or "AngleProperty" in anim,
          "der Pfeil dreht sich mit (RotateTransform)")
    check("TranslateTransform" in anim and "BeginTime" in anim,
          "die Schritte kommen gestaffelt herein (TranslateTransform + BeginTime)")
    check("CubicEase" in anim, "die Bewegung ist abgefedert (CubicEase)")
    check("CloudTutorialOpen" in anim, "der Zustand offen/geschlossen wird gemerkt")
    check("Write-UiErrorLog 'Open-Cloud-Tutorial'" in anim,
          "ein Animationsfehler wird protokolliert und reißt das Fenster nicht um")

    # ------------------------------------------------------------------
    # 8) Project-first method selection and the optional mesh/upload path
    # ------------------------------------------------------------------
    print("\n8) Project-first method choice; mesh upload stays optional")
    guides = region(source, "function Get-BridgeGuides {", "function Get-DocsResponse")
    check("cloudUploadRules" in guides, "es gibt eine eigene cloudUploadRules-Führung")
    check("meshBuildRules" in guides, "die meshBuildRules-Führung bleibt")
    cloud_rules = region(guides, "cloudUploadRules = @{", "organicBuildRules = @{")
    check("upload_asset" in cloud_rules, "cloudUploadRules nennt upload_asset")
    check("PROJECT-FIRST 3D (7.6.3)" in guides
          and "explicit user method first" in guides
          and "target Place''s established geometry and style" in guides,
          "the active method policy prioritizes the user request and Place convention")
    check("Blender is recommended for suitable new custom geometry" in guides
          and "but not mandatory" in guides,
          "Blender and the mesh workflow are recommendations rather than global requirements")
    check("Only an actually created mesh slot awaiting geometry keeps report_done open." in guides,
          "the only mesh-specific completion gate is a real generated slot awaiting geometry")
    check("BAUEN GEHT VOR SUCHEN" not in guides,
          "the active guide does not force building over a project-appropriate catalog choice")
    report_start = source.index("            'report_done' {", source.index("function Invoke-ServerTool"))
    report = source[report_start:report_start + 30000]
    check("upload_asset" in report and "userMessage" in report,
          "report_done nennt den Weg aus MESH_UPLOAD_PENDING (upload_asset + Nutzer-Satz)")

    # ------------------------------------------------------------------
    # 9) Ausführbarer Modelltest
    # ------------------------------------------------------------------
    run_model_test(status_map)

    if FAILURES:
        print(f"\nFEHLGESCHLAGEN: {len(FAILURES)} Prüfung(en) rot.")
        for item in FAILURES:
            print("  - " + item)
        return 1
    print("\nOK: 7.5.9 Open Cloud Upload + Creator-Dashboard-Tutorial bestanden (Studio-ID-Priorität, automatischer Rückfall, Tutorial, upload_asset, Dateipfad, Fehlerwege, Modelltest).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
