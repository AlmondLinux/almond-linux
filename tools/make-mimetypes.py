#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Almond Linux - Almond Pure icon theme: file-type (mimetypes) icon generator.
#
# Every file-type icon is built from ONE page template (folded top-right
# corner, flat two-tone depth) plus one emblem and one row of the colour
# table below. Run it from anywhere:
#
#     python3 tools/make-mimetypes.py            # write SVGs + aliases
#     python3 tools/make-mimetypes.py --check    # only validate what exists
#     python3 tools/make-mimetypes.py --out DIR  # write somewhere else
#
# Standard library only. Output is deterministic (same input, same bytes).
# Style rules (from the Almond Pure icon style guide): SVG 1.1, 64x64
# viewBox, no width/height, flat fills only, no gradients/filters/opacity,
# no text, no external references, small files.

import argparse
import math
import os
import sys
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT = os.path.join(ROOT, "desktop", "icons", "Almond-Pure",
                           "scalable", "mimetypes")

# ---------------------------------------------------------------- palette --
# Brand palette (exact hex) plus derived shades. "Shade" = the base colour
# multiplied by 0.85 (about 15 % darker), used for the folded flap and the
# bottom lip so every page has the same two-tone depth.
OFF_WHITE = "#F5F2EB"
DARK_BROWN = "#2B2118"
GOLDEN = "#D2A679"
GREEN = "#4A7C59"
BLUE = "#4B7CB8"

C = {
    "blue":        ("#4B7CB8", "#40699C"),   # Muted Blue
    "green":       ("#4A7C59", "#3F694C"),   # Forest Green
    "orange":      ("#D67E3A", "#B66B31"),   # Muted Orange
    "red":         ("#C55454", "#A74747"),   # Muted Red
    "brown":       ("#8B5A2B", "#764D25"),   # Almond Brown
    "golden":      ("#D2A679", "#B38D67"),   # Golden Beige
    "gray":        ("#8B8B8B", "#767676"),   # Warm Gray
    "plum":        ("#6B4C8A", "#5B4175"),   # Plum (video/media only)
    "plum_light":  ("#876D9D", "#735D86"),   # Plum + 20 % Off-White (audio)
    "slate":       ("#526378", "#465466"),   # Muted Blue+Warm Gray+Charcoal
    # Framed pages: (frame/flap/lip tone, page front)
    "paper":       ("#C2B6A3", OFF_WHITE),   # Off-White page, warm frame
    "night":       ("#5A4A3C", DARK_BROWN),  # Dark Brown page, light frame
}

# --------------------------------------------------------------- geometry --
# Page silhouette on the 64 grid: x 10..54, y 4..60, fold 14, radius 4.
L, R, T, B = 10, 54, 4, 60
FOLD = 14
RAD = 4
FRAME = 2          # framed pages: border width on top / left / right
LIP = 3            # bottom lip height (solid pages) / bottom border (framed)
CX, CY = 32, 36    # emblem centre: middle of the page below the fold


def n(v):
    """Compact number formatting: 2 decimals max, no trailing zeros."""
    s = ("%.2f" % v).rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def page_d(inset=0.0, bottom=0.0):
    """Path data for the page silhouette, optionally inset (framed pages)."""
    left, right, top, bot = L + inset, R - inset, T + inset, B - bottom
    r = max(RAD - inset, 1.0)
    diag = (R - FOLD) - T - inset * math.sqrt(2)   # fold edge: x - y = diag
    x_top = diag + top
    y_right = right - diag
    return ("M%s %sH%sL%s %sV%sA%s %s 0 0 1 %s %sH%sA%s %s 0 0 1 %s %sV%s"
            "A%s %s 0 0 1 %s %sZ" % (
                n(left + r), n(top), n(x_top), n(right), n(y_right),
                n(bot - r), n(r), n(r), n(right - r), n(bot),
                n(left + r), n(r), n(r), n(left), n(bot - r),
                n(top + r), n(r), n(r), n(left + r), n(top)))


# Folded flap: triangle under the cut corner, inner corner rounded (r=3).
FLAP_D = "M%d %dV%dA3 3 0 0 0 %d %dH%dZ" % (
    R - FOLD, T, T + FOLD - 3, R - FOLD + 3, T + FOLD, R)

# Bottom lip of a solid page: the strip between the page bottom (y=60) and
# the same rounded bottom raised by LIP units.
LIP_D = ("M{l} {a}A4 4 0 0 0 {l4} {b}H{r4}A4 4 0 0 0 {r} {a}V{c}"
         "A4 4 0 0 1 {r4} {B}H{l4}A4 4 0 0 1 {l} {c}Z").format(
    l=L, r=R, l4=L + RAD, r4=R - RAD, a=B - LIP - RAD, b=B - LIP,
    c=B - RAD, B=B)


def el(tag, **attrs):
    parts = []
    for k, v in attrs.items():
        k = k.rstrip("_").replace("_", "-")
        parts.append('%s="%s"' % (k, v))
    return "<%s %s/>" % (tag, " ".join(parts))


def path(fill, d, **kw):
    return el("path", fill=fill, d=d, **kw)


def stroke(colour, d, width=4):
    return el("path", fill="none", stroke=colour, stroke_width=n(width),
              stroke_linecap="round", stroke_linejoin="round", d=d)


def rect(fill, x, y, w, h, r=0):
    attrs = dict(fill=fill, x=n(x), y=n(y), width=n(w), height=n(h))
    if r:
        attrs["rx"] = n(r)
    return el("rect", **attrs)


def circle(fill, cx, cy, r):
    return el("circle", fill=fill, cx=n(cx), cy=n(cy), r=n(r))


def page(style, colour, flap=None):
    """The shared page template. Returns SVG elements (list of strings)."""
    a, b = C[colour]
    if style == "solid":            # a = front, b = shade
        return [path(a, page_d()), path(flap or b, FLAP_D), path(b, LIP_D)]
    # framed: a = frame tone (also flap + bottom border), b = page front
    return [path(a, page_d()), path(b, page_d(FRAME, LIP)),
            path(flap or a, FLAP_D)]


# ---------------------------------------------------------------- emblems --
# Each emblem receives (glyph colour, page colour) and returns elements.
# Emblems live in the page area below the fold, centred on (CX, CY).

def lines(ink, _bg, rows=None):
    """Ragged left-aligned text lines (documents)."""
    rows = rows or [(11, 34), (18, 37), (25, 47), (32, 47), (39, 47), (46, 39)]
    return [rect(ink, 17, y, x2 - 17, 4, 2) for y, x2 in rows]


def pdf_lines(ink, _bg):
    return lines(ink, _bg, [(12, 34), (19, 37), (26, 47), (33, 41)])


def pdf_band(ink, _bg):
    # Coloured band across the bottom of the white page, above the border.
    x0, x1, y0, y1, r = L + FRAME, R - FRAME, 42, B - LIP, RAD - FRAME
    band = ("M%d %dH%dV%dA%d %d 0 0 1 %d %dH%dA%d %d 0 0 1 %d %dZ" % (
        x0, y0, x1, y1 - r, r, r, x1 - r, y1, x0 + r, r, r, x0, y1 - r))
    return [path(ink, band)]


def picture(_ink, _bg):
    """Framed landscape: blue sky, golden sun, green mountains."""
    x0, y0, w, h, r = 16, 24, 32, 24, 3
    x1, y1 = x0 + w, y0 + h
    hills = ("M%d 42L25 33L31 39L38 31L%d 41V%dA%d %d 0 0 1 %d %dH%d"
             "A%d %d 0 0 1 %d %dZ" % (x0, x1, y1 - r, r, r, x1 - r, y1,
                                       x0 + r, r, r, x0, y1 - r))
    return [rect(BLUE, x0, y0, w, h, r), circle(GOLDEN, 23, 30.5, 3.5),
            path(GREEN, hills)]


def note(ink, _bg):
    """Two beamed eighth notes."""
    out = []
    for hx, hy in ((24, 45), (40, 42)):
        out.append('<ellipse fill="%s" cx="%s" cy="%s" rx="5" ry="4" '
                   'transform="rotate(-20 %s %s)"/>' % (ink, hx, hy, hx, hy))
    out.append(rect(ink, 26, 24, 3, 21))
    out.append(rect(ink, 42, 21, 3, 21))
    out.append(path(ink, "M26 24L45 21V27L26 30Z"))
    return out


def film(ink, bg):
    """Film frame with perforations and a play triangle."""
    out = [rect(ink, 16, 24, 32, 24, 3)]
    for x in (18.5, 24.5, 30.5, 36.5, 42.5):
        out.append(rect(bg, x, 26, 3, 3, 0.75))
        out.append(rect(bg, x, 43, 3, 3, 0.75))
    tri = "M29 31.5V40.5L37 36Z"
    out.append(el("path", fill=bg, stroke=bg, stroke_width="2",
                  stroke_linejoin="round", d=tri))
    return out


def zipper(ink, bg):
    """Archive: zipper teeth down the middle and a pull tab."""
    out = []
    for i, y in enumerate(range(7, 31, 4)):
        out.append(rect(ink, 26 if i % 2 == 0 else 32, y, 6, 4))
    out.append(rect(ink, 25, 31, 14, 17, 3))
    out.append(rect(bg, 29.5, 37, 5, 7, 2))
    return out


def prompt(ink, _bg):
    """Shell prompt '>_' drawn with strokes."""
    return [stroke(ink, "M20 29L28 36L20 43"),
            rect(ink, 32, 40, 13, 4, 2)]


def code(ink, _bg):
    """'</>' drawn with strokes."""
    return [stroke(ink, "M24 29L17 36L24 43"),
            stroke(ink, "M35 26L29 46"),
            stroke(ink, "M40 29L47 36L40 43")]


def gear(ink, bg, teeth=8, r_out=13.5, r_in=10, hole=4.5):
    """Gear: flat polygon with a hole in the page colour."""
    pitch = 2 * math.pi / teeth
    pts = []
    for k in range(teeth):
        c = k * pitch - math.pi / 2
        for r, f in ((r_in, -0.30), (r_out, -0.17), (r_out, 0.17),
                     (r_in, 0.30)):
            a = c + f * pitch
            pts.append("%s %s" % (n(CX + r * math.cos(a)),
                                  n(CY + r * math.sin(a))))
    return [path(ink, "M" + "L".join(pts) + "Z"), circle(bg, CX, CY, hole)]


def letter_a(ink, _bg):
    """Capital 'A' drawn with strokes (no fonts)."""
    return [stroke(ink, "M21 47L32 24L43 47", 5),
            stroke(ink, "M26 39.5H38", 4)]


def grid(ink, _bg):
    """Spreadsheet: 3 x 4 cells separated by page-coloured gaps."""
    out = []
    for row in range(4):
        for col in range(3):
            out.append(rect(ink, 18 + col * 10, 23 + row * 7, 8, 5, 1))
    return out


def pie(ink, _bg, r=12, gap=2.5):
    """Presentation: pie chart with one exploded slice."""
    cx, cy = CX - gap / 2, CY + gap / 2
    body = "M%s %sV%sA%d %d 0 1 0 %s %sZ" % (
        n(cx), n(cy), n(cy - r), r, r, n(cx + r), n(cy))
    sx, sy = cx + gap, cy - gap
    slice_ = "M%s %sV%sA%d %d 0 0 1 %s %sZ" % (
        n(sx), n(sy), n(sy - r), r, r, n(sx + r), n(sy))
    return [path(ink, body), path(ink, slice_)]


def disc(_ink, bg):
    """Optical disc: light disc, dark hub, centre hole."""
    return [circle(OFF_WHITE, CX, CY, 13.5), circle(DARK_BROWN, CX, CY, 6),
            circle(bg, CX, CY, 3.5)]


# ------------------------------------------------------------ colour table --
# name: (page style, colour key, emblem(s), glyph colour, flap override,
#        aliases). Aliases become relative symlinks next to the icon.
ICONS = [
    ("text-x-generic", "framed", "paper", [lines], "#8B8B8B", None, []),
    ("x-office-document", "solid", "blue", [lines], OFF_WHITE, None,
     ["application-vnd.oasis.opendocument.text", "application-msword"]),
    ("application-pdf", "framed", "paper", [pdf_lines, pdf_band],
     "#C55454", "#C55454", []),
    ("image-x-generic", "framed", "paper", [picture], None, None, []),
    ("audio-x-generic", "solid", "plum_light", [note], OFF_WHITE, None, []),
    ("video-x-generic", "solid", "plum", [film], OFF_WHITE, None, []),
    ("package-x-generic", "solid", "brown", [zipper], OFF_WHITE, None,
     ["application-x-compressed-tar", "application-zip", "application-x-tar",
      "application-gzip", "application-x-7z-compressed"]),
    ("text-x-script", "framed", "night", [prompt], OFF_WHITE, None,
     ["application-x-shellscript"]),
    ("text-x-source", "solid", "slate", [code], OFF_WHITE, None,
     ["text-x-csrc", "text-x-python", "text-html", "text-css",
      "application-json"]),
    ("application-x-executable", "solid", "gray", [gear], OFF_WHITE, None,
     []),
    ("font-x-generic", "solid", "blue", [letter_a], OFF_WHITE, None, []),
    ("x-office-spreadsheet", "solid", "green", [grid], OFF_WHITE, None,
     ["application-vnd.oasis.opendocument.spreadsheet"]),
    ("x-office-presentation", "solid", "orange", [pie], OFF_WHITE, None,
     ["application-vnd.oasis.opendocument.presentation"]),
    ("application-x-iso9660-image", "solid", "golden", [disc], DARK_BROWN,
     None, ["application-x-cd-image"]),
]

# Links that point outside this directory (still inside the theme).
EXTERNAL_LINKS = {"inode-directory": "../places/folder.svg"}

HEADER = ('<svg xmlns="http://www.w3.org/2000/svg" version="1.1" '
          'viewBox="0 0 64 64">')
COMMENT = ("<!-- Almond Pure | %s | generated by tools/make-mimetypes.py "
           "| MIT -->")


def build(name, style, colour, emblems, ink, flap):
    a, b = C[colour]
    page_colour = b if style == "framed" else a
    body = page(style, colour, flap)
    for emblem in emblems:
        body += emblem(ink, page_colour)
    return "\n".join([HEADER, COMMENT % name] + body + ["</svg>"]) + "\n"


# ------------------------------------------------------------- validation --
FORBIDDEN_TAGS = {"linearGradient", "radialGradient", "filter", "mask",
                  "clipPath", "image", "text", "script", "foreignObject",
                  "use", "pattern", "style", "metadata", "tspan"}


def validate(fn):
    """Return a list of problems for one SVG file (empty = OK)."""
    problems = []
    size = os.path.getsize(fn)
    if size > 8192:
        problems.append("larger than 8 KB (%d bytes)" % size)
    try:
        root = ET.parse(fn).getroot()
    except ET.ParseError as exc:
        return ["XML parse error: %s" % exc]
    if root.get("viewBox") != "0 0 64 64":
        problems.append("viewBox is %r" % root.get("viewBox"))
    for attr in ("width", "height"):
        if root.get(attr) is not None:
            problems.append("root has %s attribute" % attr)
    ids = set()
    for node in root.iter():
        tag = node.tag.split("}")[-1]
        if tag in FORBIDDEN_TAGS:
            problems.append("forbidden element <%s>" % tag)
        for k, v in node.attrib.items():
            k = k.split("}")[-1]
            if k in ("opacity", "fill-opacity", "stroke-opacity", "filter",
                     "mask", "clip-path", "href"):
                problems.append("forbidden attribute %s" % k)
            if "url(" in v:
                problems.append("external/paint reference in %s" % k)
            if k == "id":
                if v in ids:
                    problems.append("duplicate id %s" % v)
                ids.add(v)
    return problems


def check_dir(out):
    bad = 0
    for fn in sorted(os.listdir(out)):
        full = os.path.join(out, fn)
        if not fn.endswith(".svg"):
            continue
        if os.path.islink(full):
            target = os.readlink(full)
            if os.path.isabs(target):
                print("FAIL %s: absolute symlink %s" % (fn, target))
                bad += 1
            elif not os.path.exists(full):
                print("WARN %s -> %s (target not present yet)" % (fn, target))
            continue
        problems = validate(full)
        if problems:
            bad += 1
            print("FAIL %s: %s" % (fn, "; ".join(problems)))
    return bad


# ------------------------------------------------------------------- main --
def link(out, alias, target):
    dst = os.path.join(out, alias + ".svg")
    if os.path.lexists(dst):
        os.remove(dst)
    os.symlink(target, dst)


def main():
    ap = argparse.ArgumentParser(
        description="Generate the Almond Pure file-type (mimetypes) icons.")
    ap.add_argument("--out", default=DEFAULT_OUT, help="output directory")
    ap.add_argument("--check", action="store_true",
                    help="only validate the existing output directory")
    args = ap.parse_args()
    out = os.path.abspath(args.out)

    if not args.check:
        os.makedirs(out, exist_ok=True)
        for name, style, colour, emblems, ink, flap, aliases in ICONS:
            fn = os.path.join(out, name + ".svg")
            if os.path.islink(fn):
                os.remove(fn)
            with open(fn, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(build(name, style, colour, emblems, ink, flap))
            for alias in aliases:
                link(out, alias, name + ".svg")
        for alias, target in EXTERNAL_LINKS.items():
            link(out, alias, target)
        print("wrote %d icons + %d aliases to %s" % (
            len(ICONS), sum(len(i[-1]) for i in ICONS) + len(EXTERNAL_LINKS),
            out))

    bad = check_dir(out)
    print("validation: %s" % ("OK" if not bad else "%d problem(s)" % bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
