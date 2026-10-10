#!/usr/bin/env python3
"""Offline-Abnahme fuer Arena Roblox Bridge 7.5.9 - ROBLOX OPEN CLOUD UPLOAD.

Was dieses Update ausmacht (und was hier geprueft wird):

1. DAS MESH-FENSTER IST WEG. Kein Fenster "Mesh-Uploads", kein Menueeintrag,
   kein Abtippen von Mesh-Ids durch den Nutzer. (Die Bestandsabnahme des
   Blender-Wegs liegt weiter in test_v740_mesh.py.)
2. DER NUTZER HINTERLEGT SEINEN EIGENEN OPEN-CLOUD-API-SCHLUESSEL im
   Einstellungsfenster (Abschnitt ROBLOX OPEN CLOUD) - verschluesselt, nur auf
   diesem PC, nie im Klartext in einer Einstellungsdatei oder im Log.
3. DAS TUTORIAL DORT IST AUFKLAPPBAR UND ANIMIERT und nennt die RECHTE, ohne
   die Roblox jeden Upload mit 403 ablehnt: ASSETS + LESEN + SCHREIBEN.
4. upload_asset laedt MESHES (FBX/GLB aus Blender) und BILDER (auch selbst
   erzeugte, direkt als Base64) ueber die offizielle Roblox-Schnittstelle hoch
   und antwortet mit der ECHTEN Asset-Id.
5. FEHLT DER SCHLUESSEL, bleibt das Werkzeug verfuegbar und sagt dem Agenten
   einen deutschen Satz, den er dem Nutzer WOERTLICH weitergibt.
6. ROBLOX-FEHLER (Rate-Limit, abgelehnter Schluessel, 5xx, 400, Netz) gehen
   unverfaelscht an den Agenten weiter - mit Status und Originaltext.

Neben den Strukturpruefungen gibt es einen AUSFUEHRBAREN MODELLTEST: ein
kleiner HTTP-Server spielt die Roblox-Assets-API nach (inklusive
Operations-Polling), und die Status->Fehlercode-Tabelle sowie die
Dateiendungs-Tabelle werden dafuer AUS DER PS1 GELESEN - weicht die Bridge
von der dokumentierten Abbildung ab, schlaegt der Test rot an.
"""
from __future__ import annotations

import base64
import json
import re
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PS1 = ROOT / "ArenaBridge.ps1"
VERSION = "7.6.3"
FAILURES: list[str] = []


def check(condition: bool, message: str) -> None:
    print(("[GRUEN] " if condition else "[ROT]   ") + message)
    if not condition:
        FAILURES.append(message)


def region(source: str, start: str, end: str) -> str:
    begin = source.index(start)
    stop = source.index(end, begin)
    return source[begin:stop]


# ======================================================================
# Ausfuehrbarer Modelltest: Roblox-Assets-API nachgespielt
# ======================================================================
class FakeRoblox(BaseHTTPRequestHandler):
    """Spielt apis.roblox.com/assets/v1 nach (Upload + Operations-Polling)."""

    mode = "ok"          # ok | ratelimit | rejected
    log: list[dict] = []

    def log_message(self, *args: object) -> None:  # kein Konsolenlaerm
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
    """Faehrt genau den Weg, den die Bridge faehren muss (Modell, nicht PS-Code)."""
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
    print("\n9) Ausfuehrbarer Modelltest gegen eine nachgespielte Roblox-API")
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
              "der Schluessel reist im Header x-api-key (nicht in der URL, nicht im Body)")
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
              "die asynchrone Operation wird ueber GET /assets/v1/operations/<id> abgefragt")

        # --- Rate-Limit ---------------------------------------------------
        FakeRoblox.mode = "ratelimit"
        result = model_upload(base, "RBX-KEY-4711", "bild.png", b"FAKE-PNG",
                              "Decal", "1234567", status_map)
        check(result["code"] == "OPENCLOUD_RATE_LIMITED" and result["status"] == 429,
              "HTTP 429 wird zu OPENCLOUD_RATE_LIMITED (kein Erfinden, kein Verschweigen)")

        # --- Abgelehnter Schluessel ---------------------------------------
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
    check(raw.startswith(b"\xef\xbb\xbf"), "ArenaBridge.ps1 behaelt die UTF-8-BOM")
    source = raw.decode("utf-8-sig")

    metadata = json.loads((ROOT / "version.json").read_text(encoding="utf-8"))
    notes = "\n".join(str(note) for note in metadata.get("notes", []))
    latest_note = str(metadata.get("notes", [""])[0])
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
    print("\n1) Mesh-Fenster ist entfernt (ausdruecklicher Nutzerwunsch)")
    for gone in ("function Get-MeshWindowXaml", "function Open-MeshWindow",
                 "function Update-MeshWindow", "function Update-MeshAutoWindow",
                 "$script:MeshWindow", "$script:MeshAutoOpenPending"):
        check(gone not in source, f"entfernt: {gone}")
    check("upload_asset" in source, "upload_asset ist der neue Weg (kein Fenster)")

    # ------------------------------------------------------------------
    # 2) Der Schluessel: verschluesselt, nur lokal, nie im Log
    # ------------------------------------------------------------------
    print("\n2) Open-Cloud-Schluessel: verschluesselt abgelegt, nie im Klartext")
    key_fn = region(source, "function Get-OpenCloudKeyPath {", "function Get-OpenCloudConfig {")
    check("'opencloud.key'" in key_fn, "der Schluessel liegt in einer eigenen Datei opencloud.key")
    check("ProtectedData]::Protect(" in key_fn and "DataProtectionScope]::CurrentUser" in key_fn,
          "der Schluessel wird per DPAPI im Kontext des angemeldeten Nutzers verschluesselt")
    check("'dpapi:'" in key_fn and "'plain:'" in key_fn,
          "ohne DPAPI wird der Klartext sichtbar als solcher markiert (keine vorgetaeuschte Sicherheit)")
    get_key = region(source, "function Get-OpenCloudKey {", "function Set-OpenCloudKey {")
    check("OpenCloudKeyCache" in get_key,
          "der entschluesselte Schluessel liegt nur im Speicher der Bridge (Cache)")
    check("Nie in settings.json, nie im Log" in get_key,
          "der Quelltext sagt ausdruecklich: nie in settings.json, nie im Log")

    settings_block = region(source, "function Get-BridgeSettingsFile {", "function Save-BridgeSettingsFile {")
    save_block = region(source, "function Save-BridgeSettingsFile {", "function Get-MeshSlotData {")
    check("openCloudKey = " not in settings_block and "openCloudKey =" not in save_block,
          "der Schluessel selbst wird NICHT in settings.json geschrieben")
    for marker in ("openCloudKeySet", "openCloudKeyHint", "openCloudCreatorId",
                   "openCloudCreatorKind", "openCloudCreatorName", "openCloudSavedAt"):
        check(marker in settings_block, f"die Einstellungen tragen {marker} (Zustand ja/nein, kein Schluessel)")
    leaked = [line.strip() for line in source.splitlines()
              if ("Write-BridgeLog" in line or "Write-RuntimeLog" in line)
              and ("$Key" in line or "config.key" in line or "$keyText" in line)]
    check(not leaked, "kein Log-Aufruf schreibt den Schluessel mit (weder roh noch entschluesselt)")

    # ------------------------------------------------------------------
    # 3) Ersteller: Roblox ordnet jedes Asset jemandem zu
    # ------------------------------------------------------------------
    print("\n3) Ersteller: Studio-Anmeldung zuerst, Key-Resource als automatischer Rueckfall (kein manuelles Feld)")
    introspect = region(source, "function Invoke-OpenCloudIntrospect {", "function Resolve-OpenCloudCreatorFromKey {")
    check("https://apis.roblox.com/api-keys/v1/introspect" in introspect,
          "die Selbstauskunft nutzt den offiziellen Introspect-Endpunkt")
    check("apiKey = $clean" in introspect,
          "die Selbstauskunft schickt den Schluessel im JSON-Body (apiKey)")
    check("assetRead" in introspect and "assetWrite" in introspect,
          "die Scopes werden in ASSETS read/write uebersetzt")
    check("writeUserIds" in introspect and "writeGroupIds" in introspect,
          "die erlaubten Nutzer-/Gruppen-Ressourcen werden gelesen")
    resolve = region(source, "function Resolve-OpenCloudCreatorFromKey {", "function Test-OpenCloudKeyAuth {")
    check("authorizedUserId" in resolve,
          "als Rueckfall dient der autorisierte Nutzer des Schluessels")
    check("openCloudCreatorId" in resolve and "openCloudCreatorKind" in resolve,
          "der Ersteller wird aus dem Schluessel in die Einstellungen geschrieben")
    check("Resolve-OpenCloudCreatorId" not in source,
          "der alte Namens-/ID-Pfad ist entfernt (der Nutzer traegt nichts ein)")
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
          and "Nur wenn keine gueltige Studio-ID vorliegt" in upload_catalog,
          "upload_asset dokumentiert die Studio-ID-Prioritaet und den automatischen Key-Rueckfall")
    check("ASSETS write fuer das angemeldete Studio-Konto" in upload_catalog,
          "upload_asset erklaert das erforderliche Recht fuer den Studio-Nutzer")

    # ------------------------------------------------------------------
    # 4) Das Protokoll: Endpunkt, Multipart, Polling, Grenzen
    # ------------------------------------------------------------------
    print("\n4) Upload-Protokoll (offizielle Assets-API)")
    upload = region(source, "function Invoke-OpenCloudUpload {", "function Get-OpenCloudOperation {")
    check("https://apis.roblox.com/assets/v1/assets" in upload,
          "hochgeladen wird ueber POST https://apis.roblox.com/assets/v1/assets")
    transport = region(source, "function Send-OpenCloudHttp {", "function Get-OpenCloudTransportError {")
    client_fn = region(source, "function New-OpenCloudHttpClient {", "function New-OpenCloudMultipartBytes {")
    multipart = region(source, "function New-OpenCloudMultipartBytes {", "function Send-OpenCloudRequestFallback {")
    check("x-api-key" in client_fn and "TryAddWithoutValidation" in client_fn,
          "der Schluessel reist als Header x-api-key")
    check("Send-OpenCloudHttp" in upload and "config.key" in upload,
          "der Upload uebergibt den Schluessel an den Transport")
    check("'multipart/form-data; boundary='" in transport
          and "New-OpenCloudMultipartBytes" in transport,
          "die Anfrage ist multipart/form-data (fuer den zweiten Transportweg von Hand gebaut)")
    field_marker = r'''name="' + [string]$FieldName + '"; filename="'''
    check('name="request"' in multipart and field_marker in multipart,
          "die Anfrage hat die zwei Felder request und fileContent")
    check("assets/v1/operations/" in source,
          "die asynchrone Operation wird ueber /assets/v1/operations/<id> abgefragt")
    check("20971520" in upload, "die 20-MB-Grenze von Roblox wird geprueft (20971520 Bytes)")
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
          f"die Endungs-Tabelle stimmt ({len(found_types)} Eintraege, Meshes=Model, Bilder=Decal)")
    check("'.obj'" in spec and "nimmt KEIN OBJ an" in spec,
          "OBJ wird abgelehnt - mit dem Hinweis auf die FBX-Datei aus mesh_status")
    check("UNSUPPORTED_FORMAT" in spec and "BAD_ARGS" in spec,
          "unpassende Endung und unpassender assetType werden unterschieden")

    # ------------------------------------------------------------------
    # 5) Fehler: unverfaelscht an den Agenten, mit einem Satz fuer den Nutzer
    # ------------------------------------------------------------------
    print("\n5) Fehler und fehlender Schluessel")
    errors_fn = region(source, "function ConvertTo-OpenCloudHttpError {", "function Invoke-OpenCloudUpload {")
    status_map = parse_status_map(errors_fn)
    check(status_map.get("eq:429") == "OPENCLOUD_RATE_LIMITED", "429 -> OPENCLOUD_RATE_LIMITED")
    check(status_map.get("eq:401") == "OPENCLOUD_KEY_REJECTED", "401 -> OPENCLOUD_KEY_REJECTED")
    check(status_map.get("eq:403") == "OPENCLOUD_KEY_REJECTED", "403 -> OPENCLOUD_KEY_REJECTED")
    check(status_map.get("ge:500") == "OPENCLOUD_SERVER_ERROR", "5xx -> OPENCLOUD_SERVER_ERROR")
    check(status_map.get("fallback") == "OPENCLOUD_UPLOAD_REJECTED", "alles andere -> OPENCLOUD_UPLOAD_REJECTED")
    check("robloxResponse = $Body" in errors_fn,
          "jeder Fehler traegt die unveraenderte Roblox-Antwort (robloxResponse)")
    check("Nichts wird schoengeredet, nichts erfunden" in errors_fn,
          "die Regel steht im Quelltext: nichts wird schoengeredet")

    missing = region(source, "function Assert-OpenCloudToolAccess {", "function Get-OpenCloudAssetSpec {")
    check("OPENCLOUD_KEY_MISSING" in missing and "userMessage" in missing,
          "ohne Schluessel antwortet das Werkzeug OPENCLOUD_KEY_MISSING MIT einem Nutzer-Satz")
    check("Bridge-Einstellungen" in missing and "Roblox Open Cloud API-Key" in missing,
          "der Satz nennt den Weg: Einstellungen -> Roblox Open Cloud API-Key")
    check("WORTLICH" in missing, "der Agent wird angewiesen, den Satz WOERTLICH zu sagen")
    check("OPENCLOUD_KEY_HAS_EXPIRATION" in missing and "No Expiration" in missing,
          "ein Key mit Ablaufdatum wird komplett abgelehnt")
    check("OPENCLOUD_SCOPE_INCOMPLETE" in missing and "Test-OpenCloudPermission" in missing,
          "fehlende Read/Write-Rechte am Scope werden vor dem Aufruf blockiert")
    check("OPENCLOUD_CREATOR_MISSING" in source, "fehlt der Ersteller, meldet das Werkzeug das getrennt")
    for code in ("OPENCLOUD_UNREACHABLE", "OPENCLOUD_BAD_RESPONSE", "OPENCLOUD_OPERATION_FAILED",
                 "NO_UPLOAD_FILE", "UNKNOWN_SLOT", "PATH_OUTSIDE_BRIDGE"):
        check(code in source, f"Fehlercode vorhanden: {code}")
    transport_error = region(source, "function Get-OpenCloudTransportError {", "function Get-OpenCloudErrorBody {")
    check("Der Schluessel wurde NICHT verbraucht" in transport_error,
          "bei einem Netzfehler sagt das Werkzeug ehrlich, dass der Schluessel nicht verbraucht wurde")

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
          "der Handler laedt die EINE Werkzeug-Quelle (keine Phantom-Funktionen im Runspace)")
    check("PATH_OUTSIDE_BRIDGE" in handler and "StartsWith" in handler,
          "ein filePath ausserhalb des Bridge-Ordners wird abgelehnt")
    check("FromBase64String" in handler,
          "contentBase64 wird dekodiert - der Agent kann ein selbst erzeugtes Bild direkt senden")
    check("contentBase64 fehlt fileName" in handler,
          "zu contentBase64 wird fileName verlangt (die Endung bestimmt den Asset-Typ)")
    check("already_uploaded" in handler and "forceNew" in handler,
          "ein schon hochgeladener Slot wird nicht doppelt hochgeladen (forceNew erzwingt es)")
    check("rbxassetid://" in handler, "die Antwort enthaelt die einsetzbare rbxassetid://-Form")
    check("state = 'pending'" in handler,
          "ein laengerer Upload antwortet state=pending mit operationId (kein enges Polling)")
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
          "der Abschnitt heisst Roblox Open Cloud API-Key")
    check("Der Key ist Arenas Zugang zu Roblox" in settings_xaml
          and "kein Ablaufdatum" in settings_xaml,
          "der Key-Abschnitt erklaert den Key und dass ein Ablaufdatum abgelehnt wird")
    check('x:Name="CreatorDashboardSwitch"' not in settings_xaml,
          "der Creator-Dashboard-Opt-in-Schalter ist aus den Einstellungen entfernt (7.6.0)")
    check('x:Name="CloudPermissionList"' in settings_xaml
          and 'x:Name="CloudPermissionsButton"' in settings_xaml,
          "Tutorial-Berechtigungsliste und der Knopf Berechtigungen ansehen sind im XAML")
    check('Text="Noch kein API-Key hinzugefügt!"' in settings_xaml,
          "ohne Schluessel steht der rote Hinweis Noch kein API-Key hinzugefügt!")
    check('Text="API-Key ist eingerichtet!"' in settings_xaml,
          "mit Schluessel steht der gruene Hinweis API-Key ist eingerichtet!")
    check("PasswordBox" in settings_xaml,
          "der Schluessel wird in einem PasswordBox-Feld eingegeben")

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
    permissions = json.loads((ROOT / "opencloud/permissions.json").read_text(encoding="utf-8"))
    check("(Get-OpenCloudCatalog).permissions.PSObject.Properties" in catalog,
          "permission UI uses the shared exact-permission catalog")
    check(len(permissions) == 41 and "asset:read" in permissions and "asset:write" in permissions,
          "all 41 individual permissions are documented, read/write separately")
    check("memory-store" not in catalog and "user.user-notification" not in catalog,
          "ungenutzte Scopes sind aus dem Tutorial-Katalog entfernt")
    check("create.roblox.com/dashboard/credentials" in tutorial,
          "das Tutorial nennt die echte Adresse create.roblox.com/dashboard/credentials")
    check('Text="&#xE71B;"' in tutorial,
          "der Link-Knopf nutzt dasselbe Glyph wie der Stil 'Arena AI oeffnen'")
    check("weigert sich die Bridge komplett" in tutorial, "das Tutorial sagt klar: Ablaufdatum = Bridge weigert sich")
    check('MaxHeight="0"' in tutorial and 'Opacity="0"' in tutorial,
          "das Tutorial startet eingeklappt (MaxHeight/Opacity 0)")
    check('ClipToBounds="True"' in tutorial, "der Aufklapp-Bereich clippt (kein Herauslaufen)")

    code_start = source.index("$settingsWindow.FindName('CloudKeyBox')")
    code = source[code_start:source.index("# 7.2.3: Die Test-Benachrichtigung ist vollstaendig")]
    check("$cloudSaveButton.Add_Click" in code and "$cloudRemoveButton.Add_Click" in code
          and "$cloudDashboardButton.Add_Click" in code
          and "$cloudPermissionsButton.Add_Click" in code,
          "Speichern, Entfernen, der Dashboard-Link und Berechtigungen ansehen sind verdrahtet")
    check("$creatorDashboardSwitch" not in code,
          "der entfernte Creator-Dashboard-Schalter ist nirgends mehr verdrahtet")
    check("Set-OpenCloudKey" in code and "Get-OpenCloudKey" in code and "Remove-OpenCloudKey" in code,
          "die Knoepfe benutzen die eine Schluessel-Quelle")
    save_click = region(code, "$cloudSaveButton.Add_Click({", "# --- Berechtigungen des gespeicherten Schluessels ansehen")
    check("Set-OpenCloudKey" not in save_click and "Save-BridgeSettingsFile" not in save_click,
          "Speichern speichert NICHT sofort - erst Introspect, dann das Berechtigungs-Fenster")
    check("Show-CloudPermissionsWindow -PendingKey $keyText" in save_click
          and "Start-CloudIntrospectRun" not in save_click,
          "Speichern oeffnet das Berechtigungs-Fenster sofort; Introspect laeuft im Fenster")
    perm_window = region(code, "function Show-CloudPermissionsWindow {", "# --- Tutorial: ANIMIERT auf- und zuklappen")
    check("Oh, das ändere ich nochmal!" in perm_window
          and "Ja, alles richtig! Key speichern!" in perm_window,
          "das Berechtigungs-Fenster hat die beiden Entscheidungs-Knoepfe")
    check("Save-OpenCloudKeyFromText" in perm_window,
          "gespeichert wird erst nach dem Ja-Knopf (Save-OpenCloudKeyFromText)")
    check("nichts wurde gespeichert" in perm_window,
          "bei fehlgeschlagener Pruefung sagt das Fenster ehrlich, dass nichts gespeichert wurde")
    check("Save-BridgeSettingsFile" in code, "Speichern legt die Einstellungen dauerhaft ab")
    check("Sync-CloudSharedSettings" in code,
          "die Werte werden nach $Shared gespiegelt (Handler laufen in eigenen Runspaces)")
    for marker in ("openCloudKeySet", "openCloudCreatorId", "openCloudCreatorKind",
                   "openCloudCreatorName", "openCloudSavedAt", "openCloudKeyHint"):
        check(marker in code, f"Sync-CloudSharedSettings uebergibt {marker}")
    check("creatorDashboardEnabled" not in code,
          "die entfernte Einstellung creatorDashboardEnabled taucht im Code nicht mehr auf")
    check("Length -lt 20" in code, "zu kurze Schluessel werden abgelehnt (kein sinnloser Speicherlauf)")
    check("Update-CloudPanelState" in code and "CloudMissingPanel" in code and "CloudReadyPanel" in code,
          "die zwei Zustaende schaltet Update-CloudPanelState")
    check("Start-CloudIntrospectRun" in code and "Invoke-OpenCloudIntrospect" in code,
          "die Pruefung laeuft ueber den offiziellen Introspect-Endpunkt")
    check("Apply-CloudIntrospectVerdict" in code,
          "das Ergebnis der Selbstauskunft wird ehrlich angezeigt")
    check("developer-product:write" in source and "universe.place:write" in source
          and "OPENCLOUD_SCOPE_INCOMPLETE" in source,
          "Introspect und UI-Feedback berücksichtigen die zusätzlichen Creator-Dashboard-Scopes")
    check("DispatcherTimer" in code and "BeginInvoke" in code,
          "die Pruefung laeuft im Hintergrund (kein eingefrorenes Fenster)")
    check("StudioService:GetUserId()" in source and "Berechtigungen ansehen" in code,
          "die gespeicherte-Key-Ansicht bleibt und Studio liefert weiter die Upload-Identitaet")

    anim = region(source, "$cloudSteps = New-Object System.Collections.Generic.List[object]",
                  "$cloudDashboardButton.Add_Click")
    check("DoubleAnimation" in anim and "MaxHeightProperty" in anim,
          "das Aufklappen animiert die Hoehe (DoubleAnimation auf MaxHeight)")
    check("MaxHeight = 100000" in anim and "UpdateLayout()" in anim,
          "die Zielhoehe wird GEMESSEN (MaxHeight auf, UpdateLayout, zurueck)")
    check("RotateTransform" in anim or "AngleProperty" in anim,
          "der Pfeil dreht sich mit (RotateTransform)")
    check("TranslateTransform" in anim and "BeginTime" in anim,
          "die Schritte kommen gestaffelt herein (TranslateTransform + BeginTime)")
    check("CubicEase" in anim, "die Bewegung ist abgefedert (CubicEase)")
    check("CloudTutorialOpen" in anim, "der Zustand offen/geschlossen wird gemerkt")
    check("Write-UiErrorLog 'Open-Cloud-Tutorial'" in anim,
          "ein Animationsfehler wird protokolliert und reisst das Fenster nicht um")

    # ------------------------------------------------------------------
    # 8) Project-first method selection and the optional mesh/upload path
    # ------------------------------------------------------------------
    print("\n8) Project-first method choice; mesh upload stays optional")
    guides = region(source, "function Get-BridgeGuides {", "function Get-DocsResponse")
    check("cloudUploadRules" in guides, "es gibt eine eigene cloudUploadRules-Fuehrung")
    check("meshBuildRules" in guides, "die meshBuildRules-Fuehrung bleibt")
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
    # 9) Ausfuehrbarer Modelltest
    # ------------------------------------------------------------------
    run_model_test(status_map)

    if FAILURES:
        print(f"\nFEHLGESCHLAGEN: {len(FAILURES)} Pruefung(en) rot.")
        for item in FAILURES:
            print("  - " + item)
        return 1
    print("\nOK: 7.5.9 Open Cloud Upload + Creator-Dashboard-Tutorial bestanden (Studio-ID-Prioritaet, automatischer Rueckfall, Tutorial, upload_asset, Dateipfad, Fehlerwege, Modelltest).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
