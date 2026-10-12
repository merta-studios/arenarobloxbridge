APP-QUELLE
==========

ArenaBridge.ps1 und version.json sind die isolierte Quellfassung der neuen
Bridge. Assets liegen unter assets\; Open-Cloud-Daten unter opencloud\.

Die Notizen in version.json sind ab 7.9.2 KURZE STICHPUNKTE im Nutzer-Ton
(Stichpunkt-Regel, siehe developer\docs\GANZ WICHTIG LESEN VOR JEDER BEARBEITUNG):
notes[0] beginnt mit "• <Version> — TITEL:", danach mindestens vier Stichpunkte,
zusammen unter 600 Zeichen. Deutsche Texte benutzen echte Umlaute (ä/ö/ü/ß);
die Datei bleibt UTF-8 (der Builder liest sie mit -Encoding UTF8).

Zum normalen Bauen diese Quelldatei nicht direkt starten: zurück zum
next-update-Ordner gehen und Build-EXE.bat doppelklicken. Der private
Test-Build erscheint im EINZIGEN Ausgabeordner:

    release\ArenaRobloxBridge.exe

Ab 7.9.4 ist das GENAU EINE Programmdatei. Es gibt keine zweite EXE und kein
Start-Diagnostic.bat mehr.

Die exe aus diesem Ordner wird erst nach einem erfolgreichen persönlichen
Test und ausdrücklicher Release-Freigabe in das Repository hochgeladen.
Ein Code-PR oder ein lokaler Build allein löst kein Nutzer-Update aus.

ABLAUF DES UPDATES (ab 7.9.4): Geprüft wird weiter im Hintergrund über
latest.json aus dem Repository. Der grüne Knopf "Jetzt installieren" öffnet
jedoch die Download-Seite https://arena-rblx-bridge.netlify.app/ im Browser;
dort liegt immer die neueste ArenaRobloxBridge.exe. Die Bridge ersetzt sich
weiterhin nie selbst.

Das feste Programm-Logo ist assets\neueslogo.png. Die PNG wird für das
Bridge-Fenster direkt eingebettet; assets\ArenaBridge.ico ist daraus für das
Windows-EXE-Symbol erzeugt. Es wird größer und eckig (ohne Rundung) oben
links neben dem Fenstertitel gezeigt und ist auch das Platzhalter-Icon der
Place-Liste, solange noch kein Place verbunden ist.

Der Fensterhintergrund ist assets\liquidglasbackground.png. Das Bild wird
ebenfalls eingebettet, fällt den ganzen Fensterbereich aus und wird
proportional beschnitten; die früheren farbigen Verlaufskreise sind entfernt.
