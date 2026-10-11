ARENA ROBLOX BRIDGE — MARKEN-ASSETS
===================================

- neueslogo.png ist das vom Nutzer bereitgestellte, verbindliche Logo. Der
  EXE-Builder bettet genau diese PNG-Datei in den Programmcode ein; sie wird
  im Bridge-Fenster neben dem Titel und im Update-Hinweis angezeigt.
- ArenaBridge.ico ist das passende mehrgroessige Windows-Icon, das aus
  neueslogo.png erzeugt wurde. Build-EXE.ps1 validiert das ICO und gibt es
  an ps2exe weiter, damit auch die ArenaBridge.exe dieses Logo als
  Dateisymbol traegt.
- arena-bridge-title.jpg bleibt das separate grosse Start-/Titelbild; es ist
  nicht das Programm-Logo.
- liquidglasbackground.png ist das vom Nutzer bereitgestellte
  Fensterhintergrund-Bild. Build-EXE.ps1 bettet es ebenso ein; es faellt den
  gesamten Fensterbereich aus und wird proportional beschnitten, also nie
  verzerrt. Die frueheren farbigen Verlaufskreise im Fenster sind entfernt.

Die PNG wird beim Build in eine temporaere Kopie von ArenaBridge.ps1
eingebettet. Weder Logo noch Startbild muessen neben der fertigen EXE liegen.
Das Branding wird nicht ueber ein optionales ArenaBridge.custom.ico
ueberschrieben: neueslogo.png ist die einzige Logo-Quelle.
