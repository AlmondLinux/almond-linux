#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Almond Linux - Almond Pure icon theme: "ALMOND FOLD" folder icon generator.
#
# Every folder icon is composed from ONE folder template (darker back panel
# with a tab, lighter front panel), ONE emblem and ONE row of the colour
# table below, so all folders stay consistent and their colours can be
# changed in one place. It writes:
#
#   desktop/icons/Almond-Pure/{scalable,24,16}/places/      base theme
#   desktop/icons/Almond-Pure/{24,16}/mimetypes/inode-directory.svg
#                                                           (relative links
#                                                           to places/folder)
#   desktop/icons/Almond-Pure/scalable/apps/system-file-manager.svg
#                                                           (the folder
#                                                           drawing itself)
#   desktop/icons/Almond-Pure-<Colour>/                     folder colour
#                                                           variant themes
#
# Almond-Pure/scalable/mimetypes/ (including its inode-directory link)
# belongs to tools/make-mimetypes.py.
#
#     python3 tools/make-folders.py            # write everything
#     python3 tools/make-folders.py --check    # compare the tree on disk
#                                              # with a fresh build; exit 1
#                                              # if anything differs
#     python3 tools/make-folders.py --root DIR # write under another
#                                              # desktop/icons directory
#
# Standard library only. Output is deterministic (same input, same bytes).
# It never touches index.theme of Almond-Pure (hand-written) and never
# deletes files it did not generate.
#
# Style rules (Almond Pure icon style guide): SVG 1.1, square viewBox
# (64, 24 or 16), no width/height, flat fills only, no gradients, filters,
# opacity, text, raster images or external references; small files.

import argparse
import filecmp
import math
import os
import re
import shutil
import sys
import tempfile
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_ICONS = os.path.join(ROOT, "desktop", "icons")
BASE_THEME = "Almond-Pure"

# ---------------------------------------------------------------- palette --
OFF_WHITE = "#F5F2EB"
WARM_CREAM = "#F5DEB3"
GOLDEN_BEIGE = "#D2A679"
DARK_BROWN = "#2B2118"
CHARCOAL = "#202125"
WARM_GRAY = "#8B8B8B"
MUTED_BLUE = "#4B7CB8"
SLATE = "#4A4F5C"


def _rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _hex(rgb):
    return "#%02X%02X%02X" % tuple(max(0, min(255, int(round(c)))) for c in rgb)


def shade(h, factor=0.85):
    """Darker tone of a colour (RGB multiplied by factor; 0.85 = 15 % darker)."""
    return _hex(c * factor for c in _rgb(h))


def mix(a, b, t):
    """Flat mix of two colours: t=0 gives a, t=1 gives b."""
    return _hex(x + (y - x) * t for x, y in zip(_rgb(a), _rgb(b)))


def luminance(h):
    out = []
    for c in _rgb(h):
        c /= 255.0
        out.append(c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * out[0] + 0.7152 * out[1] + 0.0722 * out[2]


def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


# ----------------------------------------------------------- colour table --
# Edit this table to change folder colours. "front" is the front panel,
# "back" the back panel/tab (default: front 15 % darker), "emblem" the glyph
# colour (default: Off-White or Dark Brown, whichever contrasts more with
# the front panel - the style guide's "light glyph on coloured bodies, dark
# glyph on light bodies" rule made measurable).
FOLDER_COLOURS = {
    "beige":  {"front": GOLDEN_BEIGE, "back": "#B98A57", "emblem": DARK_BROWN},
    "green":  {"front": "#4A7C59"},                       # Forest Green
    "blue":   {"front": MUTED_BLUE},                      # Muted Blue
    "orange": {"front": "#D67E3A"},                       # Muted Orange
    "red":    {"front": "#C55454"},                       # Muted Red
    "gray":   {"front": WARM_GRAY, "emblem": CHARCOAL},   # Warm Gray
    "plum":   {"front": "#6B4C8A"},                       # Plum (videos)
    "slate":  {"front": SLATE},                           # Desktop
}


def colours(name):
    entry = FOLDER_COLOURS[name]
    front = entry["front"]
    back = entry.get("back") or shade(front)
    emblem = entry.get("emblem")
    if not emblem:
        emblem = max((OFF_WHITE, DARK_BROWN), key=lambda e: contrast(e, front))
    return {"F": front, "B": back, "E": emblem}


# Folder icons: name -> (emblem, colour in the base theme).
FOLDERS = [
    ("folder",             None,        "beige"),
    ("folder-open",        "open",      "beige"),
    ("user-home",          "home",      "beige"),
    ("folder-documents",   "documents", "beige"),
    ("folder-download",    "download",  "green"),
    ("folder-pictures",    "pictures",  "beige"),
    ("folder-music",       "music",     "red"),
    ("folder-videos",      "videos",    "plum"),
    ("user-desktop",       "desktop",   "slate"),
    ("folder-publicshare", "public",    "beige"),
    ("folder-templates",   "templates", "beige"),
    ("folder-projects",    "projects",  "beige"),   # not a freedesktop name
    ("folder-remote",      "remote",    "beige"),
]

# Common alternative names -> relative symlinks in the same directory.
ALIASES = {
    "folder-downloads": "folder-download",
    "folder-desktop":   "user-desktop",
    "folder-home":      "user-home",
    "folder-network":   "folder-remote",
    "folder-public":    "folder-publicshare",
}

# Folder colour variant themes: Almond-Pure-<Name> -> colour of ALL folders.
VARIANTS = {
    "Green":  "green",
    "Blue":   "blue",
    "Orange": "orange",
    "Red":    "red",
    "Gray":   "gray",
    "Plum":   "plum",
}

SIZES = (64, 24, 16)
SIZE_DIR = {64: "scalable", 24: "24", 16: "16"}


def num(v):
    s = ("%.2f" % v).rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def rounded_poly(points, r):
    """Path data for a polygon whose corners are rounded (quadratic)."""
    out = []
    count = len(points)
    for i, (vx, vy) in enumerate(points):
        px, py = points[i - 1]
        nx, ny = points[(i + 1) % count]
        d1 = math.hypot(px - vx, py - vy)
        d2 = math.hypot(nx - vx, ny - vy)
        rr = min(r, d1 / 2, d2 / 2)
        ax, ay = vx + (px - vx) / d1 * rr, vy + (py - vy) / d1 * rr
        bx, by = vx + (nx - vx) / d2 * rr, vy + (ny - vy) / d2 * rr
        out.append(("L" if out else "M") + "%s %s" % (num(ax), num(ay)))
        out.append("Q%s %s %s %s" % (num(vx), num(vy), num(bx), num(by)))
    return "".join(out) + "Z"


# ------------------------------------------------------- folder templates --
# 64 grid: safe area 4..60. Tab y 7..14, back panel top y 14, front panel
# y 18..57 (56 x 39, radius 4). Whole folder 56 x 50, centred on (32, 32).
# 24 and 16 grids: pixel-aligned redraws of the same silhouette.
TEMPLATE = {
    64: {
        "back": "M4 11A4 4 0 0 1 8 7H27C30.5 7 30.5 14 34 14H56A4 4 0 0 1 60 "
                "18V53A4 4 0 0 1 56 57H8A4 4 0 0 1 4 53Z",
        "front": '<rect x="4" y="18" width="56" height="39" rx="4" fill="{F}"/>',
        "paper": '<rect x="10" y="17" width="44" height="14" rx="2" fill="%s"/>'
                 % OFF_WHITE,
        "open": rounded_poly([(11, 26), (60, 26), (55, 57), (4, 57)], 4),
        "emblem_at": (20, 26),          # emblems are drawn in a 24x24 box
    },
    24: {
        "back": "M2 4.5A1.5 1.5 0 0 1 3.5 3H10L12 5H20.5A1.5 1.5 0 0 1 22 "
                "6.5V19.5A1.5 1.5 0 0 1 20.5 21H3.5A1.5 1.5 0 0 1 2 19.5Z",
        "front": '<rect x="2" y="7" width="20" height="14" rx="1.5" fill="{F}"/>',
        "paper": '<rect x="4" y="6" width="16" height="5" rx="1" fill="%s"/>'
                 % OFF_WHITE,
        "open": rounded_poly([(5, 10), (22, 10), (20.5, 21), (2, 21)], 1.5),
        "emblem_at": None,
    },
    16: {
        "back": "M1 3A1 1 0 0 1 2 2H6L7 3H14A1 1 0 0 1 15 4V13A1 1 0 0 1 14 "
                "14H2A1 1 0 0 1 1 13Z",
        "front": '<rect x="1" y="5" width="14" height="9" rx="1" fill="{F}"/>',
        "paper": '<rect x="3" y="4" width="11" height="4" rx=".5" fill="%s"/>'
                 % OFF_WHITE,
        "open": rounded_poly([(3, 7), (15, 7), (14, 14), (1, 14)], 1),
        "emblem_at": None,
    },
}

# ---------------------------------------------------------------- emblems --
# {E} emblem colour, {F} front panel colour (used for cut-outs), {B} back
# panel colour. 64-grid emblems use a local 24x24 box placed at emblem_at
# (box centre = front panel centre); 24/16-grid emblems use absolute
# pixel-aligned coordinates. An emblem missing from a size is dropped there.
# Every stroked element carries round caps and joins (RS).
RS = 'stroke-linecap="round" stroke-linejoin="round"'
EMBLEMS = {
    64: {
        "home":
            '<path d="M12 2.5L22 11.5H19V21H5V11.5H2Z" fill="{E}" stroke="{E}" '
            'stroke-width="2" ' + RS + '/>'
            '<rect x="15" y="3" width="4" height="7" rx="1" fill="{E}"/>'
            '<path d="M10 22.5V17A2 2 0 0 1 14 17V22.5Z" fill="{F}"/>',
        "documents":
            '<path d="M7 1H14L19 6V21A2 2 0 0 1 17 23H7A2 2 0 0 1 5 21V3A2 2 '
            '0 0 1 7 1Z" fill="{E}"/>'
            '<path d="M14 .5V5A1 1 0 0 0 15 6H19.5" fill="none" stroke="{F}" '
            'stroke-width="1.5" ' + RS + '/>'
            '<path d="M9 11H15M9 15H15M9 19H15" stroke="{F}" stroke-width="2" '
            + RS + '/>',
        "download":
            '<path d="M12 2V13.5M6.5 8L12 13.5L17.5 8M4 15V18A3 3 0 0 0 7 21H17'
            'A3 3 0 0 0 20 18V15" fill="none" stroke="{E}" stroke-width="4" '
            + RS + '/>',
        "pictures":
            '<rect x="2.5" y="3.5" width="19" height="17" rx="2.5" fill="none" '
            'stroke="{E}" stroke-width="3" ' + RS + '/>'
            '<path d="M4 19L9.5 11L14 17L16.5 14L20 19Z" fill="{E}" stroke="{E}" '
            'stroke-width="1" ' + RS + '/>'
            '<circle cx="15.5" cy="9" r="2.5" fill="{E}"/>',
        "music":
            '<circle cx="7" cy="18" r="4" fill="{E}"/>'
            '<circle cx="18" cy="15.5" r="4" fill="{E}"/>'
            '<path d="M8.5 5L22 2V15.5H19.5V6.5L11 8.4V18H8.5Z" fill="{E}" '
            'stroke="{E}" stroke-width="1" ' + RS + '/>',
        "videos":
            '<rect x="1" y="3" width="22" height="18" rx="3" fill="{E}"/>'
            '<path d="M3.5 5.5h2v2h-2zM3.5 11h2v2h-2zM3.5 16.5h2v2h-2zM18.5 '
            '5.5h2v2h-2zM18.5 11h2v2h-2zM18.5 16.5h2v2h-2z" fill="{F}" '
            'stroke="{F}" stroke-width="1" ' + RS + '/>'
            '<path d="M10 8.5L15.5 12L10 15.5Z" fill="{F}" stroke="{F}" '
            'stroke-width="1.5" ' + RS + '/>',
        "desktop":
            '<rect x="2.5" y="2.5" width="19" height="13" rx="2" fill="none" '
            'stroke="{E}" stroke-width="3" ' + RS + '/>'
            '<rect x="10" y="16" width="4" height="4" fill="{E}"/>'
            '<rect x="6" y="19" width="12" height="3" rx="1.5" fill="{E}"/>',
        "public":
            '<circle cx="16" cy="6.5" r="4" fill="{E}"/>'
            '<path d="M9 20.5V18A7 6.5 0 0 1 23 18V20.5A1.5 1.5 0 0 1 21.5 22H'
            '10.5A1.5 1.5 0 0 1 9 20.5Z" fill="{E}"/>'
            '<g fill="{F}" stroke="{F}" stroke-width="3" ' + RS + '>'
            '<circle cx="8" cy="9" r="4.5"/>'
            '<path d="M1 23V21.5A7.5 7 0 0 1 16 21.5V23Z"/></g>'
            '<circle cx="8" cy="9" r="4.5" fill="{E}"/>'
            '<path d="M1 23V21.5A7.5 7 0 0 1 16 21.5V23Z" fill="{E}"/>',
        "templates":
            '<rect x="9" y="1" width="13" height="16" rx="2" fill="{E}"/>'
            '<rect x="3" y="6" width="13" height="17" rx="2" fill="{E}" '
            'stroke="{F}" stroke-width="3" ' + RS + '/>'
            '<rect x="3" y="6" width="13" height="17" rx="2" fill="{E}"/>'
            '<path d="M6.5 11H12.5M6.5 15H12.5M6.5 19H12.5" stroke="{F}" '
            'stroke-width="2" ' + RS + '/>',
        "projects":
            '<path d="M4 4H9.5L12 7H20A2 2 0 0 1 22 9V18A2 2 0 0 1 20 20H4A2 2 '
            '0 0 1 2 18V6A2 2 0 0 1 4 4Z" fill="{B}"/>',
        "remote":
            '<circle cx="12" cy="12" r="10" fill="{E}"/>'
            '<path d="M1 12H23M2 6.5H22M2 17.5H22M12 2C7.5 7 7.5 17 12 22C16.5 '
            '17 16.5 7 12 2Z" fill="none" stroke="{F}" stroke-width="2" '
            + RS + '/>',
    },
    24: {
        "home":
            '<path d="M12 9L17 13.5H16V18H8V13.5H7Z" fill="{E}"/>'
            '<rect x="11" y="15" width="2" height="3" fill="{F}"/>',
        "documents":
            '<path d="M9 9H13L15 11V19H9Z" fill="{E}"/>'
            '<path d="M10 13h4v1h-4zM10 15h4v1h-4zM10 17h4v1h-4z" fill="{F}"/>',
        "download":
            '<path d="M11 9h2v3h-2zM8 12H16L12 16ZM7 15H9V17H15V15H17V19H7Z" '
            'fill="{E}"/>',
        "pictures":
            '<path d="M7 9H17V19H7ZM8 10V18H16V10Z" fill="{E}" '
            'fill-rule="evenodd"/>'
            '<path d="M8 18L11 13.5L13.5 16.5L15 15L16 16V18ZM13 11h2v2h-2z" '
            'fill="{E}"/>',
        "music":
            '<circle cx="9" cy="17" r="2" fill="{E}"/>'
            '<circle cx="15" cy="17" r="2" fill="{E}"/>'
            '<path d="M10 9H17V17H16V11H11V17H10Z" fill="{E}"/>',
        "videos":
            '<path d="M7 10A1 1 0 0 1 8 9H16A1 1 0 0 1 17 10V18A1 1 0 0 1 16 19'
            'H8A1 1 0 0 1 7 18Z" fill="{E}"/>'
            '<path d="M8 10h1v1H8zM8 12h1v1H8zM8 14h1v1H8zM8 16h1v1H8zM15 10h1'
            'v1h-1zM15 12h1v1h-1zM15 14h1v1h-1zM15 16h1v1h-1zM11 11.5L14 14L11 '
            '16.5Z" fill="{F}"/>',
        "desktop":
            '<path d="M6 9H18V17H6ZM7 10V15H17V10Z" fill="{E}" '
            'fill-rule="evenodd"/>'
            '<path d="M11 17h2v1h-2zM9 18h6v1H9z" fill="{E}"/>',
        # One person (the 64 grid shows two; two do not fit at 24 px).
        "public":
            '<circle cx="12" cy="11" r="2.5" fill="{E}"/>'
            '<path d="M7 19V18.5A5 4.5 0 0 1 17 18.5V19A1 1 0 0 1 16 20H8A1 1 '
            '0 0 1 7 19Z" fill="{E}"/>',
        "templates":
            '<rect x="10" y="9" width="6" height="7" fill="{E}"/>'
            '<rect x="7" y="10" width="8" height="10" fill="{F}"/>'
            '<rect x="8" y="11" width="6" height="8" fill="{E}"/>'
            '<path d="M9 13h4v1H9zM9 15h4v1H9z" fill="{F}"/>',
        "projects":
            '<path d="M7 10H10L11 11H17V18H7Z" fill="{B}"/>',
        # Outline globe: circle, one meridian, one parallel (the equator).
        "remote":
            '<g fill="none" stroke="{E}" stroke-width="1.5" ' + RS + '>'
            '<circle cx="12" cy="14" r="4.75"/>'
            '<ellipse cx="12" cy="14" rx="2" ry="4.75"/>'
            '<path d="M7.25 14H16.75"/></g>',
    },
    16: {
        "home":
            '<path d="M8 6L12 10H11V13H5V10H4Z" fill="{E}"/>'
            '<rect x="7" y="11" width="2" height="2" fill="{F}"/>',
        # 3 px stem, stepped 5-3-1 px head (crisp one-pixel tip), tray bar.
        # Centred on x 8.5: odd widths cannot sit on the panel centre (8).
        "download":
            '<path d="M7 6h3v3H7zM6 9h5v1H6zM7 10h3v1H7zM8 11h1v1H8zM4 12h9v1'
            'H4z" fill="{E}"/>',
        "documents":
            '<path d="M6 6H9L10 7V13H6Z" fill="{E}"/>'
            '<path d="M7 9h2v1H7zM7 11h2v1H7z" fill="{F}"/>',
        "music":
            '<path d="M7 6h5v2H7zM7 8h1v3H7zM11 8h1v2h-1zM5 11h3v2H5zM9 10h3v2H9z"'
            ' fill="{E}"/>',
        "videos":
            '<path d="M6 6.5L11 9.5L6 12.5Z" fill="{E}"/>',
        "desktop":
            '<path d="M5 6H11V11H5ZM6 7V10H10V7Z" fill="{E}" '
            'fill-rule="evenodd"/>'
            '<path d="M7 11h2v1H7zM6 12h4v1H6z" fill="{E}"/>',
        "pictures":
            '<path d="M3 13L7 9L10 12L11 11L13 13ZM10 6h2v2h-2z" '
            'fill="{E}"/>',
    },
}


def svg(size, body):
    return ('<svg xmlns="http://www.w3.org/2000/svg" version="1.1" '
            'viewBox="0 0 %d %d">%s</svg>\n' % (size, size, body))


def folder_svg(size, emblem, cols):
    t = TEMPLATE[size]
    parts = ['<path d="%s" fill="{B}"/>' % t["back"]]
    if emblem == "open":
        parts.append(t["paper"])
        parts.append('<path d="%s" fill="{F}"/>' % t["open"])
    else:
        parts.append(t["front"])
        glyph = EMBLEMS[size].get(emblem) if emblem else None
        if glyph:
            if t["emblem_at"]:
                glyph = '<g transform="translate(%d %d)">%s</g>' % (
                    t["emblem_at"] + (glyph,))
            parts.append(glyph)
    body = "".join(parts)
    for key, value in cols.items():
        body = body.replace("{%s}" % key, value)
    return svg(size, body)


# ------------------------------------------------- non-folder place icons --
# Only in the base theme. Grey bin (mockup image 1), full bin, workgroup.
# Full bin, all three sizes: the same flat lid as the empty bin (no handle),
# lifted straight up by two sheets of paper. Lid and bin are centred on the
# grid (x 9..55 at 64), so the icon's bounding box is centred too.
BIN_BODY = mix(WARM_GRAY, OFF_WHITE, 0.45)      # light warm grey
BIN_DARK = WARM_GRAY                             # lid, handle, ribs
PAPER_A = WARM_CREAM
PAPER_B = GOLDEN_BEIGE
NET_LINE = WARM_GRAY

TRASH = {
    64: {
        "body":
            '<path d="%s" fill="%s"/>' % (rounded_poly(
                [(13, 21), (51, 21), (47.5, 58), (16.5, 58)], 4), BIN_BODY) +
            '<path d="M24 27L25 51M32 27V51M40 27L39 51" stroke="%s" '
            'stroke-width="3.5" stroke-linecap="round"/>' % BIN_DARK,
        "lid":
            ('<path d="M26 12.5V10A2 2 0 0 1 28 8H36A2 2 0 0 1 38 10V12.5" '
             'fill="none" stroke="%s" stroke-width="3.5" ' + RS + '/>'
             '<rect x="9" y="12" width="46" height="7" rx="3" fill="%s"/>')
            % (BIN_DARK, BIN_DARK),
        "full":
            '<rect x="16" y="11" width="15" height="17" rx="1.5" fill="%s" '
            'transform="rotate(-8 23.5 19.5)"/>'
            '<rect x="33" y="10" width="15" height="18" rx="1.5" fill="%s" '
            'transform="rotate(8 40.5 19)"/>'
            '<rect x="9" y="4" width="46" height="7" rx="3" fill="%s"/>'
            % (PAPER_A, PAPER_B, BIN_DARK),
    },
    24: {
        "body":
            '<path d="M5 8H19L17.6 20.1A1 1 0 0 1 16.6 21H7.4A1 1 0 0 1 6.4 '
            '20.1Z" fill="%s"/>'
            '<path d="M9 10h1v8H9zM14 10h1v8h-1z" fill="%s"/>'
            % (BIN_BODY, BIN_DARK),
        "lid":
            '<path d="M9 3H15V5H14V4H10V5H9Z" fill="%s"/>'
            '<rect x="4" y="5" width="16" height="2" rx="1" fill="%s"/>'
            % (BIN_DARK, BIN_DARK),
        "full":
            '<rect x="4" y="2" width="16" height="2" rx="1" fill="%s"/>'
            '<path d="M7 4h5v4H7z" fill="%s"/>'
            '<path d="M12 4h5v4h-5z" fill="%s"/>'
            % (BIN_DARK, PAPER_A, PAPER_B),
    },
    16: {
        "body":
            '<path d="M3 6H13V13A1 1 0 0 1 12 14H4A1 1 0 0 1 3 13Z" fill="%s"/>'
            '<path d="M6 8h1v4H6zM9 8h1v4H9z" fill="%s"/>'
            % (BIN_BODY, BIN_DARK),
        "lid":
            '<path d="M6 2h4v1H6zM2 3H14V5H2Z" fill="%s"/>' % BIN_DARK,
        "full":
            '<path d="M2 1H14V3H2Z" fill="%s"/>'
            '<path d="M4 3h4v3H4z" fill="%s"/>'
            '<path d="M8 3h4v3H8z" fill="%s"/>'
            % (BIN_DARK, PAPER_A, PAPER_B),
    },
}


def trash_svg(size, full):
    t = TRASH[size]
    return svg(size, (t["full"] if full else t["lid"]) + t["body"])


def _monitor(x, y, w, h, frame, stand):
    """A monitor: slate frame, Muted Blue screen, slate stand (pixel units)."""
    return ('<rect x="%s" y="%s" width="%s" height="%s" rx="%s" fill="%s"/>'
            '<rect x="%s" y="%s" width="%s" height="%s" fill="%s"/>' % (
                num(x), num(y), num(w), num(h), num(frame), SLATE,
                num(x + frame), num(y + frame), num(w - 2 * frame),
                num(h - 2 * frame), MUTED_BLUE) +
            ('<rect x="%s" y="%s" width="%s" height="%s" fill="%s"/>' % (
                num(x + w / 2 - stand[0] / 2), num(y + h), num(stand[0]),
                num(stand[1]), SLATE) if stand else ""))


WORKGROUP = {
    64: ('<path d="M32 26V32M14 38V32H50V38" fill="none" stroke="%s" '
         'stroke-width="3" ' + RS + '/>') % NET_LINE +
        _monitor(20, 6, 24, 17, 3, (4, 3)) +
        '<rect x="25" y="25" width="14" height="3" rx="1.5" fill="%s"/>' % SLATE +
        _monitor(4, 38, 20, 14, 3, (4, 3)) +
        '<rect x="8" y="54" width="12" height="3" rx="1.5" fill="%s"/>' % SLATE +
        _monitor(40, 38, 20, 14, 3, (4, 3)) +
        '<rect x="44" y="54" width="12" height="3" rx="1.5" fill="%s"/>' % SLATE,
    24: '<path d="M11.5 10h1v3h-1zM5 13H19V15H18V14H6V15H5Z" fill="%s"/>'
        % NET_LINE +
        _monitor(7, 2, 10, 7, 1, (2, 1)) +
        '<rect x="9" y="10" width="6" height="1" fill="%s"/>' % SLATE +
        _monitor(1, 15, 9, 6, 1, (2, 1)) +
        '<rect x="3" y="22" width="5" height="1" fill="%s"/>' % SLATE +
        _monitor(14, 15, 9, 6, 1, (2, 1)) +
        '<rect x="16" y="22" width="5" height="1" fill="%s"/>' % SLATE,
    16: '<path d="M7.5 6h1v2h-1zM3 8H13V10H12V9H4V10H3Z" fill="%s"/>' % NET_LINE +
        _monitor(5, 1, 6, 5, 1, None) +
        _monitor(1, 10, 6, 5, 1, None) +
        _monitor(9, 10, 6, 5, 1, None),
}


def workgroup_svg(size):
    return svg(size, WORKGROUP[size])


# ------------------------------------------------------------------ output --
INDEX_VARIANT = """[Icon Theme]
Name=Almond Pure {label}
Comment=Almond Pure with {lower} folders. Only folder icons live here; every other icon comes from Almond Pure.
Inherits=Almond-Pure
Example=folder
# Small sizes first: lookups return the first directory that matches, and the
# scalable directories match every size from 8 to 512. Type=Threshold lets
# the 16 px drawings serve 14-18 px requests and the 24 px drawings 20-28 px
# requests (a 22 px panel, for example) instead of only exact sizes.
Directories=16/mimetypes,16/places,24/mimetypes,24/places,scalable/mimetypes,scalable/places

[16/mimetypes]
Size=16
Context=MimeTypes
Type=Threshold
Threshold=2

[16/places]
Size=16
Context=Places
Type=Threshold
Threshold=2

[24/mimetypes]
Size=24
Context=MimeTypes
Type=Threshold
Threshold=4

[24/places]
Size=24
Context=Places
Type=Threshold
Threshold=4

[scalable/mimetypes]
Size=64
Context=MimeTypes
Type=Scalable
MinSize=8
MaxSize=512

[scalable/places]
Size=64
Context=Places
Type=Scalable
MinSize=8
MaxSize=512
"""

FORBIDDEN = re.compile(
    r"gradient|<filter|opacity|<text|<image|<style|<script|href|@import|"
    r"clip-?path|<mask|width=\"\d+\" height=\"\d+\" viewBox", re.I)


def write(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.lexists(path) and os.path.islink(path):
        os.unlink(path)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(data)


def link(directory, alias, target):
    """Relative symlink directory/alias -> target (same directory, or
    ../places/... for inode-directory)."""
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, alias)
    if os.path.lexists(path):
        os.unlink(path)
    os.symlink(target, path)


def build_theme(theme_dir, colour_for, include_non_folders):
    """Write one theme's place icons. colour_for(name, default) -> colour."""
    written = []
    for size in SIZES:
        places = os.path.join(theme_dir, SIZE_DIR[size], "places")
        for name, emblem, default in FOLDERS:
            data = folder_svg(size, emblem, colours(colour_for(name, default)))
            write(os.path.join(places, name + ".svg"), data)
            written.append((os.path.join(places, name + ".svg"), data))
        for alias, target in sorted(ALIASES.items()):
            link(places, alias + ".svg", target + ".svg")
        if include_non_folders:
            extra = {
                "user-trash": trash_svg(size, False),
                "user-trash-full": trash_svg(size, True),
                "network-workgroup": workgroup_svg(size),
            }
            for name, data in sorted(extra.items()):
                write(os.path.join(places, name + ".svg"), data)
                written.append((os.path.join(places, name + ".svg"), data))
    return written


def inode_directory(theme, sizes):
    """File managers built on GIO (pcmanfm-qt via libfm-qt) ask for
    "inode-directory" before "folder". A relative link to the same theme's
    places/folder.svg keeps the two identical at every size; without it a
    16 or 24 px request (or any request in a colour variant) would fall back
    to a different drawing."""
    for size in sizes:
        link(os.path.join(theme, SIZE_DIR[size], "mimetypes"),
             "inode-directory.svg", "../places/folder.svg")


def build(icons_root):
    base = os.path.join(icons_root, BASE_THEME)
    written = build_theme(base, lambda name, default: default, True)
    # Almond-Pure/scalable/mimetypes belongs to make-mimetypes.py, which
    # writes the same link there.
    inode_directory(base, (24, 16))
    # The Files application icon is the folder drawing itself, so the file
    # manager and the folders it shows always match.
    path = os.path.join(base, "scalable", "apps", "system-file-manager.svg")
    data = folder_svg(64, None, colours("beige"))
    write(path, data)
    written.append((path, data))
    for label, colour in VARIANTS.items():
        theme = os.path.join(icons_root, "%s-%s" % (BASE_THEME, label))
        written += build_theme(theme, lambda name, default, c=colour: c, False)
        inode_directory(theme, SIZES)
        write(os.path.join(theme, "index.theme"),
              INDEX_VARIANT.format(label=label, lower=label.lower()))
    return written


def validate(written):
    problems = []
    for path, data in written:
        try:
            root = ET.fromstring(data)
        except ET.ParseError as exc:
            problems.append("%s: XML error %s" % (path, exc))
            continue
        if not root.tag.endswith("svg") or "width" in root.attrib \
                or "height" in root.attrib:
            problems.append("%s: root must be <svg> without width/height" % path)
        if FORBIDDEN.search(data):
            problems.append("%s: forbidden construct" % path)
        if len(data.encode("utf-8")) > 8192:
            problems.append("%s: larger than 8 KB" % path)
    for name in sorted(FOLDER_COLOURS):
        c = colours(name)
        ratio = contrast(c["E"], c["F"])
        if ratio < 3.0:
            problems.append("colour %s: emblem contrast %.2f < 3" % (name, ratio))
    return problems


def tree_listing(top):
    out = {}
    for dirpath, dirnames, filenames in os.walk(top):
        for f in filenames + [d for d in dirnames
                              if os.path.islink(os.path.join(dirpath, d))]:
            p = os.path.join(dirpath, f)
            out[os.path.relpath(p, top)] = p
    return out


def check(icons_root):
    """Build into a temp dir and compare with what is on disk."""
    tmp = tempfile.mkdtemp(prefix="make-folders-")
    try:
        written = build(tmp)
        problems = validate(written)
        fresh = tree_listing(tmp)
        for rel, new in sorted(fresh.items()):
            old = os.path.join(icons_root, rel)
            if os.path.islink(new):
                if not os.path.islink(old) or os.readlink(old) != os.readlink(new):
                    problems.append("stale or missing link: " + rel)
            elif not os.path.isfile(old) or os.path.islink(old) or \
                    not filecmp.cmp(old, new, shallow=False):
                problems.append("stale or missing file: " + rel)
        return problems
    finally:
        shutil.rmtree(tmp)


def main():
    ap = argparse.ArgumentParser(description=__doc__ or "Almond Pure folders")
    ap.add_argument("--root", default=DEFAULT_ICONS,
                    help="desktop/icons directory to write into")
    ap.add_argument("--check", action="store_true",
                    help="only verify the files on disk match a fresh build")
    args = ap.parse_args()
    if args.check:
        problems = check(args.root)
        for p in problems:
            print("make-folders: " + p, file=sys.stderr)
        print("make-folders: check %s" % ("FAILED" if problems else "ok"))
        return 1 if problems else 0
    written = build(args.root)
    problems = validate(written)
    for p in problems:
        print("make-folders: " + p, file=sys.stderr)
    print("make-folders: wrote %d icons, %d alias links per places directory"
          % (len(written), len(ALIASES)))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
