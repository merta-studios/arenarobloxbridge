# Arena Roblox Bridge — Download-Website (für Netlify)

**Live-Adresse: <https://arena-rblx-bridge.netlify.app/>** — ab Version 7.9.4 öffnet
die Bridge genau diese Seite, wenn der Nutzer das Update wirklich installieren will.
Die Bridge prüft Updates weiterhin selbst im Repository (`latest.json`); die Seite
liefert die Datei.

Dieser Ordner enthält die komplette, eigenständige Download-Website für
`ArenaRobloxBridge.exe`. Der gesamte Inhalt dieses Ordners (`index.html`,
`netlify.toml`, `README.md`) kann unverändert in ein zweites GitHub-Repository
kopiert und direkt über **Netlify** gehostet werden.

## Darstellung und Funktionsweise

- **Bewusst komplett schlicht:** Eine leere weiße Seite mit schwarzem Text genau
  in der Mitte, der live den Status des Downloads anzeigt.
- **Hintergrund-Abruf:** Beim Öffnen liest die Seite im Hintergrund
  `next-update/release/latest.json` aus dem Haupt-Repository
  (`merta-studios/arenarobloxbridge`), ermittelt die aktuelle Version und lädt
  die zugehörige EXE im Hintergrund mit Prozent- und Größenanzeige herunter.
- **Prüfung & sauberer Dateiname:** Sobald alle Bytes geladen sind, prüft die
  Seite Größe und SHA-256-Prüfsumme und speichert die Datei direkt auf dieser
  sauberen Seite als **`ArenaRobloxBridge.exe`** — sowohl für Erst-Downloads als
  auch für spätere Updates.
- **Hinweis zu Fehlalarmen (Version 8.0.0):** Nach dem Start des Downloads wird
  eine Zeile eingeblendet, die SmartScreen- und Virenscanner-Warnungen als
  bekannten Fehlalarm einordnet (die EXE ist nicht signiert). Hintergrund,
  Meldewege der Scanner-Hersteller und der Signatur-Weg über den Builder:
  `../developer/docs/FALSE-POSITIVE-MELDUNG.md`. Dieser Text ist bewusst nur
  eine Zeile im bestehenden Detail-Text — das schlichte Seitenlayout bleibt.

## Auf Netlify veröffentlichen (später im Zweit-Repo)

1. Neues (zweites) GitHub-Repository anlegen.
2. Den **Inhalt** dieses Ordners (`index.html`, `netlify.toml`, `README.md`) in
   den Hauptordner des zweiten Repositories kopieren und auf `main` speichern.
3. Bei Netlify **Add new site → Import an existing project** wählen und das
   zweite GitHub-Repository verbinden (keine Build-Befehle nötig; `netlify.toml`
   stellt alles automatisch ein).
4. Die Netlify-Adresse ist hinterlegt: Version 7.9.4 öffnet beim Update
   `https://arena-rblx-bridge.netlify.app/` (siehe
   `app/ArenaBridge.ps1`, `$script:UpdateDownloadPageUrl`). Ändert sich die
   Adresse, muss sie dort, in `README.md`/`START-HIER.txt` und hier angepasst
   werden.
