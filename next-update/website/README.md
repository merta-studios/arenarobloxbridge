# Arena Roblox Bridge — Download-Website (für Netlify)

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

## Auf Netlify veröffentlichen (später im Zweit-Repo)

1. Neues (zweites) GitHub-Repository anlegen.
2. Den **Inhalt** dieses Ordners (`index.html`, `netlify.toml`, `README.md`) in
   den Hauptordner des zweiten Repositories kopieren und auf `main` speichern.
3. Bei Netlify **Add new site → Import an existing project** wählen und das
   zweite GitHub-Repository verbinden (keine Build-Befehle nötig; `netlify.toml`
   stellt alles automatisch ein).
4. Sobald die Netlify-Adresse feststeht, kann sie in einer späteren Bridge-Version
   als Update-Link hinterlegt werden. Version 7.9.3 nutzt beim Update vorerst
   weiterhin den direkten Repository-Link.
