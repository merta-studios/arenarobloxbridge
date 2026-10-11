APP-QUELLE
==========

ArenaBridge.ps1 und version.json sind die isolierte Quellfassung der neuen
Bridge. Assets liegen unter assets\; Open-Cloud-Daten unter opencloud\.

Zum normalen Bauen diese Quelldatei nicht direkt starten: zurueck zum
next-update-Ordner gehen und Build-EXE.bat doppelklicken. Der private
Test-Build erscheint im EINZIGEN Ausgabeordner:

    release\ArenaBridge.exe

Die exe aus diesem Ordner wird erst nach einem erfolgreichen persoenlichen
Test und ausdruecklicher Release-Freigabe in das Repository hochgeladen.
Ein Code-PR oder ein lokaler Build allein loest kein Nutzer-Update aus.

Das feste Programm-Logo ist assets\neueslogo.png. Die PNG wird fuer das
Bridge-Fenster direkt eingebettet; assets\ArenaBridge.ico ist daraus fuer das
Windows-EXE-Symbol erzeugt. Es wird groesser und eckig (ohne Rundung) oben
links neben dem Fenstertitel gezeigt und ist auch das Platzhalter-Icon der
Place-Liste, solange noch kein Place verbunden ist.

Der Fensterhintergrund ist assets\liquidglasbackground.png. Das Bild wird
ebenfalls eingebettet, faellt den ganzen Fensterbereich aus und wird
proportional beschnitten; die frueheren farbigen Verlaufskreise sind entfernt.
