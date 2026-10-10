Brand assets used by next-update/Build-EXE.ps1:

- arena-bridge-title.jpg: in-app startup title/banner image. Build-EXE.ps1 embeds
  the JPG bytes into a temporary compile-only PowerShell copy; the final EXE
  does not need this file beside it.
- ArenaBridge.ico: multi-size Windows icon embedded in the compiled EXE.

If an asset is replaced, rebuild and re-run the offline preparation checks. The
builder records SHA-256 values for both assets in local release-metadata.json.
