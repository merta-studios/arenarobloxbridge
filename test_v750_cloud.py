#!/usr/bin/env python3
"""Offline-Abnahme fuer Arena Roblox Bridge 7.5.0 - ROBLOX OPEN CLOUD UPLOAD.

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
VERSION = "7.5.0"
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
    check(metadata.get("version") == VERSION, "version.json ist 7.5.0")
    for phrase in ("Open Cloud", "upload_asset", "MESH-FENSTER", "ASSETS", "Asset-Id"):
        check(phrase in notes, f"Release-Notiz nennt {phrase}")

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
    print("\n3) Ersteller (Nutzer oder Gruppe)")
    resolve = region(source, "function Resolve-OpenCloudCreatorId {", "function Get-OpenCloudAssetSpec {")
    check("users.roblox.com/v1/usernames/users" in resolve,
          "ein Roblox-NAME wird ueber users.roblox.com in eine ID uebersetzt")
    check('"usernames"' in resolve.replace("'", '"') or "usernames" in resolve,
          "die Anfrage nutzt den offiziellen usernames-Endpunkt")
    check("'group'" in source and "openCloudCreatorKind" in source,
          "auch eine GRUPPE kann Ersteller sein (Umschalter Nutzer/Gruppe)")
    check("Roblox-Name oder Zahlen-ID" in source and "(oder dieser Gruppe)" in source,
          "der Hinweis sagt, dass bei einer Gruppe die Zahlen-ID einzutragen ist")
    check("$creator['groupId']" in source and "$creator['userId']" in source,
          "der Upload unterscheidet Nutzer- und Gruppen-Ersteller")
    check("creationContext" in source and "creator = $creator" in source,
          "die Metadaten tragen creationContext.creator (so verlangt es die API)")

    # ------------------------------------------------------------------
    # 4) Das Protokoll: Endpunkt, Multipart, Polling, Grenzen
    # ------------------------------------------------------------------
    print("\n4) Upload-Protokoll (offizielle Assets-API)")
    upload = region(source, "function Invoke-OpenCloudUpload {", "function Get-OpenCloudOperation {")
    check("https://apis.roblox.com/assets/v1/assets" in upload,
          "hochgeladen wird ueber POST https://apis.roblox.com/assets/v1/assets")
    client_fn = region(source, "function New-OpenCloudHttpClient {", "function Get-OpenCloudErrorBody {")
    check("x-api-key" in client_fn and "TryAddWithoutValidation" in client_fn,
          "der Schluessel reist als Header x-api-key")
    check("'x-api-key'" in upload or "config.key" in upload,
          "der Upload uebergibt den Schluessel an den Client")
    check("MultipartFormDataContent" in upload, "die Anfrage ist multipart/form-data")
    check("$form.Add($requestPart, 'request')" in upload and "$form.Add($filePart, 'fileContent', $name)" in upload,
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
                      ".tga": ("Decal", "image/x-targa")}
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

    missing = region(source, "if (-not $config.hasKey) {", "if ([string]::IsNullOrWhiteSpace([string]$config.creatorId)) {")
    check("OPENCLOUD_KEY_MISSING" in missing and "userMessage" in missing,
          "ohne Schluessel antwortet das Werkzeug OPENCLOUD_KEY_MISSING MIT einem Nutzer-Satz")
    check("Zahnrad (Einstellungen)" in missing and "ROBLOX OPEN CLOUD" in missing,
          "der Satz nennt den Weg: Einstellungen -> ROBLOX OPEN CLOUD")
    check("WORTLICH" in missing, "der Agent wird angewiesen, den Satz WOERTLICH zu sagen")
    check("OPENCLOUD_CREATOR_MISSING" in source, "fehlt der Ersteller, meldet das Werkzeug das getrennt")
    for code in ("OPENCLOUD_UNREACHABLE", "OPENCLOUD_BAD_RESPONSE", "OPENCLOUD_OPERATION_FAILED",
                 "NO_UPLOAD_FILE", "UNKNOWN_SLOT", "PATH_OUTSIDE_BRIDGE"):
        check(code in source, f"Fehlercode vorhanden: {code}")
    check("Der Schluessel wurde NICHT verbraucht" in upload,
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
    print("\n7) Einstellungsfenster: ROBLOX OPEN CLOUD")
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
    for name in ("CloudKeyBox", "CloudSaveButton", "CloudTestButton", "CloudRemoveButton",
                 "CloudStatusText", "CloudCreatorBox", "CloudCreatorKind", "CloudCreatorHint",
                 "CloudTutorialHeader", "CloudTutorialChevron", "CloudTutorialToggle",
                 "CloudTutorialWrap", "CloudTutorialBody"):
        check(f'x:Name="{name}"' in settings_xaml, f"Einstellungen enthalten {name}")
    for step in range(1, 7):
        check(f'x:Name="CloudStep{step}"' in settings_xaml, f"Tutorial-Schritt CloudStep{step} vorhanden")
    check('Content="Nutzer"' in settings_xaml and 'Content="Gruppe"' in settings_xaml,
          "beim Ersteller ist zwischen Nutzer und Gruppe waehlbar")
    check("PasswordBox" in settings_xaml, "der Schluessel wird in einem PasswordBox-Feld eingegeben")

    tutorial = region(settings_xaml, 'x:Name="CloudTutorialWrap"', '<TextBlock Text="UPDATES"')
    for right in ("ASSETS", "READ", "WRITE", "asset:read", "asset:write", "Access Permissions"):
        check(right in tutorial, f"das Tutorial nennt das Recht {right}")
    check("create.roblox.com/credentials" in tutorial, "das Tutorial nennt die echte Adresse create.roblox.com/credentials")
    check("Save &amp; Generate Key" in tutorial or "Save & Generate Key" in tutorial,
          "das Tutorial endet beim Erzeugen des Schluessels")
    check("Ablaufdatum" in tutorial, "das Tutorial warnt vor einem Ablaufdatum (stiller Stop)")
    check("MaxHeight=\"0\"" in tutorial and "Opacity=\"0\"" in tutorial,
          "das Tutorial startet eingeklappt (MaxHeight/Opacity 0)")
    check("ClipToBounds=\"True\"" in tutorial, "der Aufklapp-Bereich clippt (kein Herauslaufen)")

    code_start = source.index("$settingsWindow.FindName('CloudKeyBox')")
    code = source[code_start:source.index("# 7.2.3: Die Test-Benachrichtigung ist vollstaendig")]
    check("$cloudSaveButton.Add_Click" in code and "$cloudTestButton.Add_Click" in code
          and "$cloudRemoveButton.Add_Click" in code,
          "Speichern, Prüfen und Entfernen sind verdrahtet")
    check("Set-OpenCloudKey" in code and "Get-OpenCloudKey" in code and "Remove-OpenCloudKey" in code,
          "die Knoepfe benutzen die eine Schluessel-Quelle")
    check("Save-BridgeSettingsFile" in code, "Speichern legt die Einstellungen dauerhaft ab")
    check("Sync-CloudSharedSettings" in code,
          "die Werte werden nach $Shared gespiegelt (Handler laufen in eigenen Runspaces)")
    for marker in ("openCloudKeySet", "openCloudCreatorId", "openCloudCreatorKind",
                   "openCloudCreatorName", "openCloudSavedAt", "openCloudKeyHint"):
        check(marker in code, f"Sync-CloudSharedSettings uebergibt {marker}")
    check("Length -lt 20" in code, "zu kurze Schluessel werden abgelehnt (kein sinnloser Speicherlauf)")
    check("Resolve-OpenCloudCreatorId" in code, "Speichern loest den Ersteller-Namen in eine ID auf")
    check("Test-OpenCloudKeyAuth" in code, "Prüfen fragt Roblox, ob der Schluessel angenommen wird")
    check("DispatcherTimer" in code and "BeginInvoke" in code,
          "die Prüfung laeuft im Hintergrund (kein eingefrorenes Fenster)")

    anim = region(source, "$cloudSteps = New-Object System.Collections.Generic.List[object]",
                  "$cloudKeyBox.Add_Click" if "$cloudKeyBox.Add_Click" in source else "$cloudSaveButton.Add_Click")
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
    # 8) Die Empfehlung: Blender bauen und selbst hochladen
    # ------------------------------------------------------------------
    print("\n8) Empfehlung an den Agenten: bauen statt suchen")
    guides = region(source, "function Get-BridgeGuides {", "function Get-DocsResponse")
    check("cloudUploadRules" in guides, "es gibt eine eigene cloudUploadRules-Fuehrung")
    check("meshBuildRules" in guides, "die meshBuildRules-Fuehrung bleibt")
    cloud_rules = region(guides, "cloudUploadRules = @{", "organicBuildRules = @{")
    check("upload_asset" in cloud_rules, "cloudUploadRules nennt upload_asset")
    check("ausdruecklich" in guides.lower() or "EMPFOHLEN" in guides,
          "die Fuehrung spricht eine EMPFEHLUNG aus (kein bloesser Hinweis)")
    check("BLENDER-MESH-BAU (7.5.0" in source or "BLENDER-MESH-BAU" in source,
          "die wichtigen Regeln nennen den Blender-Weg")
    check("BAUEN GEHT VOR SUCHEN" in source,
          "die Regeln sagen: bauen geht vor Katalogsuche und vor Primitiven")
    report_start = source.index("            'report_done' {")
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
    print("\nOK: 7.5.0 Open Cloud Upload bestanden (Fenster weg, Schluessel, Tutorial, upload_asset, Fehlerwege, Modelltest).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
