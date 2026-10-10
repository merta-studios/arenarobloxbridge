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
Windows-EXE-Symbol erzeugt.
