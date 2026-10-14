#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Almond Linux - Almond Pure icon theme: whole-tree checker.
#
#     python3 tools/check-icons.py             # check desktop/icons
#     python3 tools/check-icons.py --root DIR  # check another icons tree
#
# Checks every theme under desktop/icons (Almond-Pure and its colour
# variants):
#   - every SVG file: valid XML, <svg> root without width/height, a square
#     viewBox that matches its size directory (16, 24 or 64 for scalable),
#     no gradients, filters, masks, clip paths, patterns, text, images,
#     scripts, styles, <use>, opacity or url() references, under 8 KB;
#   - every symlink: relative, resolving to a file inside the same theme;
#   - every index.theme: Directories= lists exactly the <size>/<context>
#     directories that exist, each with its own section;
#   - the small status icons (16/status, 24/status): every glyph colour has
#     a contrast of at least 3:1 (WCAG non-text contrast) against BOTH the
#     dark panel (Charcoal) and light menus (Off-White).
# Exit status 1 if anything fails. Standard library only. It checks files;
# it says nothing about how a desktop renders them.

import argparse
import os
import re
import sys
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_ICONS = os.path.join(ROOT, "desktop", "icons")

FORBIDDEN_TAGS = {"linearGradient", "radialGradient", "filter", "mask",
                  "clipPath", "pattern", "image", "text", "tspan", "script",
                  "foreignObject", "use", "style"}
FORBIDDEN_ATTRS = {"opacity", "fill-opacity", "stroke-opacity", "filter",
                   "mask", "clip-path", "href", "style"}

CHARCOAL = "#202125"        # dark panel and launcher
OFF_WHITE = "#F5F2EB"       # light menus and popups
# Colours allowed in 16/status and 24/status. Glyph colours must reach 3:1
# on both backgrounds. Detail colours are only allowed on top of a glyph:
# the white cross on the red badge and the charging bolt (Off-White fill,
# Dark Brown outline).
STATUS_GLYPH = {"#A3703A": "status tan", "#7B7B7B": "dim grey (unlit)",
                "#B8672A": "low orange", "#C55454": "muted red"}
STATUS_DETAIL = {"#F5F2EB", "#2B2118"}
COLOUR = re.compile(r"#[0-9A-Fa-f]{6}\b")


def _lin(c):
    c /= 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def luminance(h):
    r, g, b = (int(h[i:i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)


def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def check_svg(path, size):
    problems = []
    if os.path.getsize(path) > 8192:
        problems.append("larger than 8 KB")
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return ["XML error: %s" % exc]
    if root.tag.split("}")[-1] != "svg":
        problems.append("root is not <svg>")
    for attr in ("width", "height"):
        if root.get(attr) is not None:
            problems.append("root has %s" % attr)
    want = "0 0 %d %d" % (size, size)
    if root.get("viewBox") != want:
        problems.append("viewBox %r, expected %r" % (root.get("viewBox"), want))
    for node in root.iter():
        tag = node.tag.split("}")[-1]
        if tag in FORBIDDEN_TAGS:
            problems.append("forbidden element <%s>" % tag)
        for k, v in node.attrib.items():
            k = k.split("}")[-1]
            if k in FORBIDDEN_ATTRS:
                problems.append("forbidden attribute %s" % k)
            if "url(" in v:
                problems.append("url() reference in %s" % k)
    return problems


def check_status_colours(path):
    text = open(path, encoding="utf-8").read()
    problems = []
    used = {c.upper() for c in COLOUR.findall(text)}
    has_badge = re.search(r'<circle[^>]*fill="#C55454"', text) is not None
    has_bolt = "charging" in os.path.basename(path)
    for c in sorted(used):
        if c in STATUS_GLYPH:
            continue
        if c in STATUS_DETAIL and (has_badge or has_bolt):
            continue
        problems.append("colour %s not allowed in a small status icon" % c)
    return problems


def size_of(rel_dir):
    head = rel_dir.split(os.sep)[0]
    return 64 if head == "scalable" else int(head)


def check_theme(theme):
    problems = []
    name = os.path.basename(theme)
    dirs = set()
    for size_dir in sorted(os.listdir(theme)):
        sp = os.path.join(theme, size_dir)
        if not os.path.isdir(sp):
            continue
        for ctx in sorted(os.listdir(sp)):
            cp = os.path.join(sp, ctx)
            if os.path.isdir(cp):
                dirs.add("%s/%s" % (size_dir, ctx))
    for rel in sorted(dirs):
        d = os.path.join(theme, rel)
        size = size_of(rel)
        for fn in sorted(os.listdir(d)):
            p = os.path.join(d, fn)
            where = "%s/%s/%s" % (name, rel, fn)
            if not fn.endswith(".svg"):
                problems.append("%s: not an SVG" % where)
                continue
            if os.path.islink(p):
                target = os.readlink(p)
                real = os.path.realpath(p)
                if os.path.isabs(target):
                    problems.append("%s: absolute link %s" % (where, target))
                elif not os.path.isfile(real):
                    problems.append("%s: broken link -> %s" % (where, target))
                elif not real.startswith(os.path.realpath(theme) + os.sep):
                    problems.append("%s: link leaves the theme" % where)
                continue
            for msg in check_svg(p, size):
                problems.append("%s: %s" % (where, msg))
            if rel in ("16/status", "24/status"):
                for msg in check_status_colours(p):
                    problems.append("%s: %s" % (where, msg))
    index = os.path.join(theme, "index.theme")
    if not os.path.isfile(index):
        problems.append("%s: no index.theme" % name)
        return problems
    text = open(index, encoding="utf-8").read()
    m = re.search(r"^Directories=(.*)$", text, re.M)
    listed = [x for x in (m.group(1).split(",") if m else []) if x]
    if len(listed) != len(set(listed)):
        problems.append("%s/index.theme: duplicate directory" % name)
    for missing in sorted(dirs - set(listed)):
        problems.append("%s/index.theme: %s exists but is not listed"
                        % (name, missing))
    for extra in sorted(set(listed) - dirs):
        problems.append("%s/index.theme: %s is listed but does not exist"
                        % (name, extra))
    for d in listed:
        if "\n[%s]\n" % d not in text:
            problems.append("%s/index.theme: no [%s] section" % (name, d))
    # Small directories must come before the scalable ones (first match
    # wins in the lookup).
    seen_scalable = False
    for d in listed:
        if d.startswith("scalable/"):
            seen_scalable = True
        elif seen_scalable:
            problems.append("%s/index.theme: %s listed after a scalable "
                            "directory" % (name, d))
    return problems


def main():
    ap = argparse.ArgumentParser(description="Check the Almond Pure themes.")
    ap.add_argument("--root", default=DEFAULT_ICONS,
                    help="desktop/icons directory to check")
    args = ap.parse_args()
    problems = []
    themes = sorted(d for d in os.listdir(args.root)
                    if d.startswith("Almond-Pure")
                    and os.path.isdir(os.path.join(args.root, d)))
    for t in themes:
        problems += check_theme(os.path.join(args.root, t))
    for c, label in sorted(STATUS_GLYPH.items()):
        a, b = contrast(c, CHARCOAL), contrast(c, OFF_WHITE)
        print("check-icons: %s %-17s %.2f:1 on Charcoal, %.2f:1 on Off-White"
              % (c, label, a, b))
        if a < 3.0 or b < 3.0:
            problems.append("status colour %s below 3:1" % c)
    for p in problems:
        print("check-icons: " + p, file=sys.stderr)
    print("check-icons: %d themes, %s" % (
        len(themes), "FAILED (%d problems)" % len(problems) if problems
        else "ok"))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
