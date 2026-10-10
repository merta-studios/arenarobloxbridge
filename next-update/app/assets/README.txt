BRAND-ASSETS FUER next-update/app

- arena-bridge-title.jpg: Titel-/Startbild im Bridge-Fenster. Der Builder bettet
  es in eine temporaere Kopie von ArenaBridge.ps1 ein; die fertige EXE braucht
  diese Datei nicht neben sich.
- ArenaBridge.ico: mitgeliefertes Standard-Logo fuer das Windows-EXE-Symbol.
- ArenaBridge.custom.ico: optionales eigenes Windows-Symbol. Lege dein Logo
  als gueltige .ico-Datei unter genau diesem Namen hier ab. Der Build nimmt
  diese Datei automatisch statt ArenaBridge.ico. Sie wird lokal ignoriert und
  nicht in Git aufgenommen. Entferne sie, um wieder das Standard-Logo zu nutzen.

Eine normale PNG-/JPG-Datei kann ps2exe nicht direkt als EXE-Symbol verwenden;
vorher in eine Windows-ICO-Datei umwandeln. Empfehlenswert ist ein ICO mit
transparentem Hintergrund und mehreren Groessen (16, 24, 32, 48, 64, 128 und
256 Pixel). Der Builder prueft den ICO-Header und alle Bildbereiche, bevor er
kompiliert. Alternativ kann Build-EXE.ps1 mit -CustomIconPath "C:\\Pfad\\Logo.ico"
aufgerufen werden; fuer den normalen Ablauf genuegt die Datei ArenaBridge.custom.ico.
