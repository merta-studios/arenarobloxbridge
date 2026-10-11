#!/usr/bin/env python3
"""Offline-Regressionstest fuer Arena Roblox Bridge 7.7.1 (Branding/Hintergrund).

Dieser Test braucht KEIN Windows, kein PowerShell und kein Roblox Studio. Er
prueft ausschliesslich den vom Nutzer beauftragten Oberflaechen-Umbau:

1. LOGO OBEN LINKS: groesser als vorher (mindestens 46 px) und ECKIG
   (CornerRadius="0"), damit das Logo nicht mehr als abgerundeter Kreis/Blob
   erscheint.
2. PLACE-LISTE OHNE PLACE: Das Platzhalter-Icon ist nicht mehr der gezeichnete
   Strich mit den zwei Kreisen, sondern dieselbe eingebettete Logo-Bitmap
   (EmptyStateLogoImage + Set-ProgramBrandImage).
3. HINTERGRUND: Die farbigen Aurora-Verlaufskreise (RadialGradientBrush im
   Hauptfenster) sind vollstaendig entfernt. Stattdessen faellt das vom Nutzer
   bereitgestellte Bild app/assets/liquidglasbackground.png den Fensterbereich
   aus - proportional beschnitten (UniformToFill), also unverzerrt.
4. LADEBILDSCHIRM: Das "BETA BUILD"-Abzeichen oben rechts ist weg; die Bridge
   ist keine Beta mehr.
5. SELBSTGENUEGSAMKEIT: Hintergrund und Logo werden wie das Titelbild ueber
   einen eigenen Builder-Platzhalter in die EXE eingebettet und vom
   Build-Smoke-Test decodiert. Neben der fertigen EXE darf keine Bilddatei
   liegen muessen.

Aufruf:
    python developer/tests/test_v771_branding.py
"""

from __future__ import annotations

import re
import struct
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP_ROOT = ROOT / "app"
PS1 = APP_ROOT / "ArenaBridge.ps1"
BUILDER = ROOT / "builder" / "Build-EXE.ps1"
BACKGROUND = APP_ROOT / "assets" / "liquidglasbackground.png"
LOGO = APP_ROOT / "assets" / "neueslogo.png"

WINDOW_WIDTH = 920
WINDOW_HEIGHT = 620

FAILURES: list[str] = []


def check(condition: bool, message: str) -> None:
    print(("[GRUEN] " if condition else "[ROT]   ") + message)
    if not condition:
        FAILURES.append(message)


def load_source() -> str:
    raw = PS1.read_bytes()
    if not raw.startswith(b"\xef\xbb\xbf"):
        raise SystemExit("[ROT]   ArenaBridge.ps1 muss mit UTF-8-BOM beginnen")
    return raw.decode("utf-8-sig")


def main_window_xaml(source: str) -> tuple[ET.Element, str]:
    start = source.index("$xaml = @'") + len("$xaml = @'")
    end = source.index("\n'@", start)
    xaml = source[start:end]
    try:
        root = ET.fromstring(xaml)
    except ET.ParseError as error:
        raise SystemExit(f"[ROT]   Hauptfenster-XAML ist kein gueltiges XML: {error}")
    return root, xaml


def find_named(root: ET.Element, name: str) -> ET.Element | None:
    key = "{http://schemas.microsoft.com/winfx/2006/xaml}Name"
    return next((node for node in root.iter() if node.attrib.get(key) == name), None)


def parent_of(root: ET.Element, child: ET.Element) -> ET.Element | None:
    for node in root.iter():
        if child in list(node):
            return node
    return None


def png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        return (0, 0)
    return struct.unpack(">II", data[16:24])


def splash_region(source: str) -> str:
    start = source.index('<Border x:Name="SplashScreen"')
    end = source.index("</Window>", start)
    return source[start:end]


def main() -> int:
    source = load_source()
    root, xaml = main_window_xaml(source)
    splash = splash_region(source)

    # ---------------------------------------------------------------- 1. LOGO
    logo_image = find_named(root, "ProgramLogoImage")
    check(logo_image is not None, "das Titelzeilen-Logo existiert im Hauptfenster")
    logo_box = parent_of(root, logo_image) if logo_image is not None else None
    logo_width = int(float(logo_image.attrib.get("Width", "0"))) if logo_image is not None else 0
    logo_height = int(float(logo_image.attrib.get("Height", "0"))) if logo_image is not None else 0
    check(logo_width >= 46 and logo_height >= 46,
          f"das Titelzeilen-Logo ist deutlich groesser als 38 px ({logo_width}x{logo_height})")
    check(logo_box is not None and str(logo_box.attrib.get("CornerRadius", "")).strip().strip("0.") == ""
          and logo_box.attrib.get("CornerRadius") == "0",
          "das Titelzeilen-Logo ist eckig (CornerRadius=0, nicht abgerundet)")
    check(logo_image is not None and logo_image.attrib.get("Stretch") == "Uniform",
          "das Titelzeilen-Logo wird proportional skaliert (keine Verzerrung)")
    check("Set-ProgramBrandLogo -ImageControl $ProgramLogoImage" in source,
          "das Titelzeilen-Logo wird weiterhin beim Start geladen")

    # ------------------------------------------------- 2. PLACE-LISTEN-PLATZHALTER
    empty_logo = find_named(root, "EmptyStateLogoImage")
    check(empty_logo is not None, "die Place-Liste hat ein eigenes Logo-Bild (EmptyStateLogoImage)")
    check("Set-ProgramBrandImage -ImageControl $EmptyStateLogoImage" in source,
          "derselbe Logoeinspeiser fuellt das Platzhalter-Icon der Place-Liste")
    empty_region_start = xaml.index('x:Name="EmptyState"')
    empty_region = xaml[empty_region_start:empty_region_start + 1400]
    check("Margin=\"15,0,0,0\"" not in empty_region and "RadiusX=\"1.5\"" not in empty_region,
          "der gezeichnete Platzhalter (Strich mit zwei Kreisen) ist entfernt")
    check("<Ellipse" not in empty_region, "im Platzhalter gibt es keine gezeichneten Kreise mehr")

    # --------------------------------------------------------- 3. HINTERGRUNDBILD
    background_image = find_named(root, "BackgroundImage")
    check(background_image is not None, "das Hauptfenster hat ein Hintergrundbild-Element")
    check(background_image is not None and background_image.attrib.get("Stretch") == "UniformToFill",
          "das Hintergrundbild faellt den Bereich aus, ohne verzerrt zu werden (UniformToFill)")
    check(background_image is not None
          and background_image.attrib.get("RenderOptions.BitmapScalingMode") == "HighQuality",
          "das Hintergrundbild wird in hoher Qualitaet skaliert")
    background_grid = parent_of(root, background_image) if background_image is not None else None
    check(background_grid is not None and background_grid.attrib.get("IsHitTestVisible") == "False",
          "das Hintergrundbild liegt hinter dem Inhalt und fängt keine Klicks ab")

    aurora_region_start = xaml.index('Grid.RowSpan="2" IsHitTestVisible="False"')
    aurora_region_end = xaml.index("<!-- ======================== TITELLEISTE", aurora_region_start)
    aurora_region = xaml[aurora_region_start:aurora_region_end]
    check("<RadialGradientBrush" not in aurora_region and "<Ellipse" not in aurora_region,
          "die farbigen Aurora-Verlaufskreise sind vollstaendig entfernt")
    for old_color in ("#547B5CFF", "#4D2E4FFF", "#4000CFC0", "#47C13FF0", "#3D21C55D", "#29FF4D6D"):
        check(old_color not in xaml, f"die alte Aurora-Farbe {old_color} ist nicht mehr im Fenster")
    check("RadialGradientBrush" not in xaml, "im Hauptfenster-XAML gibt es keine Verlaufskreise mehr")

    check("Set-BackgroundArtwork -ImageControl $BackgroundImage" in source,
          "das Hintergrundbild wird beim Fensteraufbau gesetzt")
    check("$script:BackgroundImageBase64 = '__ARENA_BACKGROUND_IMAGE_BASE64__'" in source,
          "die App-Quelle hat einen eindeutigen Builder-Platzhalter fuer das Hintergrundbild")
    check(source.count("__ARENA_BACKGROUND_IMAGE_BASE64__") >= 1,
          "der Hintergrund-Platzhalter ist im Smoke-Test geprueft")

    background_width, background_height = png_size(BACKGROUND)
    logo_width_px, logo_height_px = png_size(LOGO)
    check(BACKGROUND.is_file() and background_width >= WINDOW_WIDTH and background_height >= WINDOW_HEIGHT,
          f"liquidglasbackground.png ist gross genug fuer das {WINDOW_WIDTH}x{WINDOW_HEIGHT}-Fenster "
          f"({background_width}x{background_height})")
    check(LOGO.is_file() and logo_width_px == 1024 and logo_height_px == 1024,
          "neueslogo.png bleibt die unangetastete 1024px-Logoquelle")

    builder = BUILDER.read_text(encoding="utf-8")
    check("Join-Path $assetsDirectory 'liquidglasbackground.png'" in builder,
          "der Builder kennt das neue Hintergrund-Asset")
    check("__ARENA_BACKGROUND_IMAGE_BASE64__" in builder,
          "der Builder ersetzt den Hintergrund-Platzhalter durch das echte Bild")
    check("backgroundImageWidth" in builder and "liquidglasbackground.png" in builder,
          "der EXE-Smoke-Test prueft, dass der Hintergrund decodiert wurde")

    # ------------------------------------------------------------ 4. KEIN BETA
    check("BETA BUILD" not in source, 'der Ladebildschirm zeigt kein "BETA BUILD" mehr')
    check("Beta Build" not in source and "Beta-Build" not in source,
          "es gibt keine weitere Beta-Beschriftung auf dem Ladebildschirm")
    check("<Ellipse Width=\"6\" Height=\"6\" Fill=\"#54E6D0\"" not in splash,
          "der Beta-Punkt oben rechts im Startbild ist entfernt")
    check('Text="ARENA"' in splash and 'Text="ROBLOX BRIDGE"' in splash,
          "der Startbildschirm behält seinen Titel-Text")

    smoke_region = source[source.index("if ($env:ARENABRIDGE_BUILD_SMOKE -eq '1') {"):
                          source.index("# 7.2.9 PROOF_OF_LIFE")]
    check("backgroundImageWidth" in smoke_region and "backgroundImageHeight" in smoke_region,
          "der Build-Smoke-Test meldet die decodierte Hintergrundgroesse")
    check("$smokeBackgroundStream" in smoke_region,
          "der Build-Smoke-Test gibt den Hintergrund-Speicherstrom wieder frei")

    print()
    if FAILURES:
        print(f"FAILED: {len(FAILURES)} Branding-Pruefung(en).")
        for failure in FAILURES:
            print(f"  - {failure}")
        return 1
    print("OK: Logo, Place-Platzhalter, Hintergrundbild und Startbildschirm sind wie beauftragt.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
