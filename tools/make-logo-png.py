#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Almond Linux - raster logo and boot artwork generator.
#
# Makes every PNG of the logo set from the logo MASTER raster (not from the
# SVGs):
#
#   branding/logo/png/almond-mark-{512,256,128,64,48,32,16}.png
#   branding/logo/png/almond-logo-1024.png
#   branding/boot/plymouth/almond/watermark.png   (single-colour light mark)
#   branding/boot/plymouth/almond/{lock,entry,bullet}.png
#   branding/boot/isolinux-splash.png
#   branding/boot/grub-background.png
#
#   python3 tools/make-logo-png.py MASTER                 write everything
#   python3 tools/make-logo-png.py MASTER --check         compare the files on
#                                                         disk with a fresh build
#                                                         (decoded pixels); exit
#                                                         1 if anything differs
#   python3 tools/make-logo-png.py MASTER --root DIR      write under another
#                                                         repository root
#   python3 tools/make-logo-png.py MASTER --preview DIR   also write boot-screen
#                                                         previews to DIR
#
# MASTER is almond-logo-original.webp, the approved 1254 x 1254 RGBA logo
# master. It is kept outside this repository and is only read, never written.
# The crop boxes below were measured on that exact file, so a master with a
# different SHA-256 is refused unless --force is given.
#
# Needs Python 3 and Pillow (PIL) with WebP support; nothing else. Output is
# deterministic for a given Pillow version (last run: Pillow 12.2.0).
# See branding/logo/README.md and branding/boot/README.md.
#
# Alpha rule: in every transparent PNG written here, a pixel with alpha 16 or
# less is cleared to fully transparent (0, 0, 0, 0). The rule is applied to
# the master, again after every resample (Lanczos and box filters leave a
# faint fringe) and again after palette reduction (a palette entry with alpha
# 16 or less is zeroed, and every transparent source pixel points at a fully
# transparent entry). The finished files therefore contain no pixel with
# 0 < alpha <= 16. GRUB and isolinux backgrounds are opaque.

import argparse
import hashlib
import os
import sys
import tempfile

try:
    from PIL import Image, ImageDraw, features
except ImportError:
    sys.exit("make-logo-png: needs Pillow (python3 -m pip install Pillow)")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MASTER_SHA256 = "7b8b471651d94c1b801f7e58bb364216a7b6e6c88ec7f8543d79df1544d27794"
MASTER_SIZE = (1254, 1254)

# Measured on the master (x0, y0, x1 exclusive, y1 exclusive).
SYMBOL_BOX = (375, 123, 881, 866)    # the almond mark, alpha > 16 bounding box
LETTER_BOX = (209, 866, 1034, 1119)  # the "Almond Linux" lettering
LOCKUP_ORIGIN = (209, 123)           # top-left of the single-colour lockup
LOCKUP_WINDOW = (110, 24, 1134, 1219)  # 1024 x 1195 window, ~100 px padding

# Logo colours measured on the master (median of colour clusters).
FILL = (156, 93, 37)         # #9C5D25
HIGHLIGHT = (235, 186, 123)  # #EBBA7B

# Palette (Almond Pure).
OFF_WHITE = (245, 242, 235)  # #F5F2EB, single-colour light logo
DARK_BROWN = (43, 33, 24)    # #2B2118
GOLDEN_BEIGE = (210, 166, 121)  # #D2A679

FAINT = 16           # alpha at or below this is cleared
PALETTE_LIMIT = 2.0  # max mean abs channel difference for a palette PNG

MARK_SIZES = (512, 256, 128, 64, 48, 32, 16)


# ------------------------------------------------------------------ helpers --
def clear_faint(im):
    """Copy of an RGBA image with every pixel of alpha <= FAINT set to
    (0, 0, 0, 0)."""
    mask = im.getchannel("A").point(lambda v: 255 if v <= FAINT else 0)
    out = im.copy()
    out.paste((0, 0, 0, 0), mask=mask)
    return out


def faint_count(im):
    """Number of pixels with 0 < alpha <= FAINT."""
    hist = im.convert("RGBA").getchannel("A").histogram()
    return sum(hist[1:FAINT + 1])


def resample(im, size):
    """Lanczos resize on premultiplied alpha (no dark fringe)."""
    return im.convert("RGBa").resize(size, Image.LANCZOS).convert("RGBA")


def resize(im, size):
    """resample(), then clear the faint fringe the filter leaves behind. Used
    for every transparent PNG."""
    return clear_faint(resample(im, size))


def mean_diff(a, b, only_visible=True):
    """Mean absolute channel difference of two RGBA images; with
    only_visible, pixels transparent in both are skipped."""
    pa, pb = a.load(), b.load()
    w, h = a.size
    tot = n = 0
    for y in range(h):
        for x in range(w):
            p, q = pa[x, y], pb[x, y]
            if only_visible and p[3] == 0 and q[3] == 0:
                continue
            tot += abs(p[0] - q[0]) + abs(p[1] - q[1]) + abs(p[2] - q[2]) + abs(p[3] - q[3])
            n += 4
    return tot / n if n else 0.0


def quantize_clean(im, colors=256):
    """Palette version of an RGBA image that keeps the alpha rule: every
    palette entry with alpha <= FAINT is zeroed to (0, 0, 0, 0), and every
    transparent source pixel points at such a fully transparent entry. If
    the quantiser made no near-transparent entry, one slot is freed for it.
    Entries with alpha >= 248 (the quantiser averages opaque and edge
    pixels) are snapped to 255, as in clean_master()."""
    for n_colors in (colors, colors - 1):
        q = im.quantize(n_colors, method=Image.Quantize.FASTOCTREE)
        pal = q.getpalette("RGBA")
        n = len(pal) // 4
        clear_index = None
        for i in range(n):
            if pal[4 * i + 3] >= 248:
                pal[4 * i + 3] = 255
            if pal[4 * i + 3] <= FAINT:
                pal[4 * i:4 * i + 4] = [0, 0, 0, 0]
                if clear_index is None:
                    clear_index = i
        if clear_index is None:
            if n_colors == colors:
                continue             # retry with one slot kept free
            pal += [0, 0, 0, 0]
            clear_index = n
        q.putpalette(pal, "RGBA")
        clear = im.getchannel("A").point(lambda v: 255 if v == 0 else 0)
        q.paste(clear_index, mask=clear)
        return q


class Builder:
    def __init__(self, root):
        self.root = root
        self.report = []

    def path(self, rel):
        p = os.path.join(self.root, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        return p

    def save(self, im, rel, try_palette=True):
        """Save RGBA; use a 256-colour palette when it is visually lossless
        (mean abs channel difference < PALETTE_LIMIT over visible pixels)."""
        info = {"size": "%dx%d" % im.size}
        out = im
        if try_palette:
            q = quantize_clean(im)
            d = mean_diff(im, q.convert("RGBA"))
            info["palette_diff"] = "%.3f" % d
            if d < PALETTE_LIMIT:
                out = q
        out.save(self.path(rel), optimize=True)
        info["mode"] = "P(256)" if out.mode == "P" else out.mode
        info["faint"] = faint_count(out)
        self.report.append((rel, info))


# ------------------------------------------------------------------- master --
def load_master(path, force):
    with open(path, "rb") as f:
        digest = hashlib.sha256(f.read()).hexdigest()
    if digest != MASTER_SHA256 and not force:
        sys.exit("make-logo-png: %s is not the approved master (SHA-256 %s);"
                 " use --force to build from it anyway" % (path, digest))
    im = Image.open(path).convert("RGBA")
    if im.size != MASTER_SIZE:
        sys.exit("make-logo-png: master must be %dx%d, got %dx%d" % (MASTER_SIZE + im.size))
    return im


def clean_master(im):
    """Clear faint pixels (alpha <= FAINT); snap compression noise in solid
    areas (alpha >= 248) to fully opaque."""
    im = clear_faint(im)
    a = im.getchannel("A").point(lambda v: 255 if v >= 248 else v)
    im.putalpha(a)
    return im


def _proj(p, a, b):
    """Position of colour p on the axis a -> b (0 at a, 1 at b)."""
    d = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
    dd = d[0] * d[0] + d[1] * d[1] + d[2] * d[2]
    return ((p[0] - a[0]) * d[0] + (p[1] - a[1]) * d[1] + (p[2] - a[2]) * d[2]) / dd


def mark_square(im, pad_frac=0.03):
    """The mark, trimmed and centred in a transparent square with 3% padding."""
    crop = im.crop(SYMBOL_BOX)
    w, h = crop.size
    side = int(round(max(w, h) / (1 - 2 * pad_frac)))
    sq = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    sq.paste(crop, ((side - w) // 2, (side - h) // 2))
    return sq


def mono_light_lockup(im):
    """Off-White single-colour lockup: the master's alpha, with the golden
    highlights of the mark knocked out (alpha scaled by 1 - highlight
    membership)."""
    x0, y0 = LOCKUP_ORIGIN
    src = im.crop((x0, y0, LETTER_BOX[2], LETTER_BOX[3]))
    sp = src.load()
    w, h = src.size
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    op = out.load()
    for y in range(h):
        for x in range(w):
            r, g, b, a = sp[x, y]
            if a == 0:
                continue
            k = 0.0
            if y + y0 < LETTER_BOX[1]:
                t = _proj((r, g, b), FILL, HIGHLIGHT)
                k = min(1.0, max(0.0, (t - 0.15) / 0.7))
            op[x, y] = OFF_WHITE + (int(round(a * (1 - k))),)
    return out


def on_background(size, art, art_h, top, bg=DARK_BROWN):
    """Flat background with art scaled to art_h, centred left to right."""
    w_, h_ = size
    canvas = Image.new("RGBA", (w_, h_), bg + (255,))
    w = int(round(art.size[0] * art_h / art.size[1]))
    small = resample(art, (w, art_h))  # composited on an opaque background:
    # the faint fringe is kept, it is antialiasing here
    canvas.alpha_composite(small, ((w_ - w) // 2, top))
    return canvas.convert("RGB"), ((w_ - w) // 2, top, w, art_h)


def supersample(size, draw_fn, k=8):
    """Draw at k times the size, box-filter down, clear the faint fringe."""
    big = Image.new("RGBA", (size[0] * k, size[1] * k), (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(big), k)
    return clear_faint(big.convert("RGBa").resize(size, Image.BOX).convert("RGBA"))


# ------------------------------------------------------------------- build --
PLY = "branding/boot/plymouth/almond/"


def plymouth_dialog_images(b):
    # lock.png: flat padlock in Off-White (shackle + body), 20x26
    def lock(dr, k):
        dr.rounded_rectangle((5 * k, 1 * k, 15 * k, 15 * k), radius=5 * k, outline=OFF_WHITE + (255,), width=3 * k)
        dr.rounded_rectangle((1 * k, 10 * k, 19 * k, 25 * k), radius=3 * k, fill=OFF_WHITE + (255,))
        dr.ellipse((8.5 * k, 14.5 * k, 11.5 * k, 17.5 * k), fill=DARK_BROWN + (255,))
        dr.rectangle((9.25 * k, 16 * k, 10.75 * k, 21 * k), fill=DARK_BROWN + (255,))
    b.save(supersample((20, 26), lock), PLY + "lock.png", try_palette=False)

    # entry.png: flat text field, Off-White with a Golden Beige 2 px border
    def entry(dr, k):
        dr.rounded_rectangle((0, 0, 240 * k - 1, 32 * k - 1), radius=4 * k, fill=GOLDEN_BEIGE + (255,))
        dr.rounded_rectangle((2 * k, 2 * k, 238 * k - 1, 30 * k - 1), radius=3 * k, fill=OFF_WHITE + (255,))
    b.save(supersample((240, 32), entry), PLY + "entry.png", try_palette=False)

    # bullet.png: Dark Brown dot for typed password characters
    def bullet(dr, k):
        dr.ellipse((1 * k, 1 * k, 11 * k, 11 * k), fill=DARK_BROWN + (255,))
    b.save(supersample((12, 12), bullet), PLY + "bullet.png", try_palette=False)


def build(master, root):
    b = Builder(root)
    im = clean_master(master)

    sq = mark_square(im)
    for s in MARK_SIZES:
        b.save(resize(sq, (s, s)), "branding/logo/png/almond-mark-%d.png" % s)
    # full lockup: an exact (unscaled) window of the master
    b.save(im.crop(LOCKUP_WINDOW), "branding/logo/png/almond-logo-1024.png")

    mono = mono_light_lockup(im)
    # Plymouth watermark: the single-colour light mark (same artwork as the
    # GRUB and isolinux lockups), 200 px tall. The colour mark's dark outline
    # would vanish on the Dark Brown splash background.
    x0, y0 = LOCKUP_ORIGIN
    mark = mono.crop((SYMBOL_BOX[0] - x0, SYMBOL_BOX[1] - y0, SYMBOL_BOX[2] - x0, SYMBOL_BOX[3] - y0))
    w = int(round(mark.size[0] * 200 / mark.size[1]))
    b.save(resize(mark, (w, 200)), PLY + "watermark.png")
    plymouth_dialog_images(b)

    # isolinux (640x480, 32-colour palette) and GRUB (1024x768, RGB)
    iso, iso_box = on_background((640, 480), mono, 150, 20)
    q = iso.quantize(32, method=Image.Quantize.MEDIANCUT)
    d = mean_diff(iso.convert("RGBA"), q.convert("RGBA"), only_visible=False)
    q.save(b.path("branding/boot/isolinux-splash.png"), optimize=True)
    b.report.append(("branding/boot/isolinux-splash.png",
                     {"size": "640x480", "mode": "P(%d)" % len(q.getcolors()),
                      "palette_diff": "%.3f" % d, "lockup_xywh": iso_box}))
    grub, grub_box = on_background((1024, 768), mono, 260, 60)
    grub.save(b.path("branding/boot/grub-background.png"), optimize=True)
    b.report.append(("branding/boot/grub-background.png",
                     {"size": "1024x768", "mode": "RGB", "lockup_xywh": grub_box}))
    return b.report


def previews(root, out):
    """Boot screen previews: watermark centred on Dark Brown, password
    prompt at 75% height (the theme's DialogVerticalAlignment)."""
    os.makedirs(out, exist_ok=True)
    pd = os.path.join(root, PLY)
    wm = Image.open(os.path.join(pd, "watermark.png")).convert("RGBA")
    e = Image.open(os.path.join(pd, "entry.png")).convert("RGBA")
    lk = Image.open(os.path.join(pd, "lock.png")).convert("RGBA")
    bu = Image.open(os.path.join(pd, "bullet.png")).convert("RGBA")
    for (w, h) in ((1024, 768), (1366, 768)):
        c = Image.new("RGBA", (w, h), DARK_BROWN + (255,))
        c.alpha_composite(wm, ((w - wm.size[0]) // 2, (h - wm.size[1]) // 2))
        ey = int(h * 0.75 - e.size[1] / 2)
        ex = (w - e.size[0] - lk.size[0] - 10) // 2
        c.alpha_composite(lk, (ex, ey + (e.size[1] - lk.size[1]) // 2))
        c.alpha_composite(e, (ex + lk.size[0] + 10, ey))
        for k in range(6):
            c.alpha_composite(bu, (ex + lk.size[0] + 22 + k * 16, ey + 10))
        p = os.path.join(out, "plymouth-%dx%d.png" % (w, h))
        c.convert("RGB").save(p)
        print("preview", p)


def check(master, root):
    """Build into a temporary directory and compare decoded pixels with the
    files under root. Returns the number of differing files."""
    bad = 0
    with tempfile.TemporaryDirectory() as tmp:
        report = build(master, tmp)
        for rel, _ in report:
            fresh = Image.open(os.path.join(tmp, rel))
            disk_path = os.path.join(root, rel)
            if not os.path.exists(disk_path):
                print("MISSING", rel)
                bad += 1
                continue
            disk = Image.open(disk_path)
            same = (fresh.size == disk.size and fresh.mode == disk.mode
                    and fresh.convert("RGBA").tobytes() == disk.convert("RGBA").tobytes())
            print("ok  " if same else "DIFF", rel)
            bad += 0 if same else 1
    return bad


def main():
    ap = argparse.ArgumentParser(description="Build the Almond Linux logo and boot PNGs from the logo master.")
    ap.add_argument("master", help="path to almond-logo-original.webp (read only)")
    ap.add_argument("--root", default=ROOT, help="repository root to write under (default: this repository)")
    ap.add_argument("--check", action="store_true", help="compare the files on disk with a fresh build; exit 1 on any difference")
    ap.add_argument("--preview", metavar="DIR", help="also write boot screen previews to DIR")
    ap.add_argument("--force", action="store_true", help="accept a master whose SHA-256 differs from the approved one")
    args = ap.parse_args()
    if not features.check("webp") and args.master.lower().endswith(".webp"):
        sys.exit("make-logo-png: this Pillow has no WebP support")
    master = load_master(args.master, args.force)
    if args.check:
        bad = check(master, args.root)
        print("%d file(s) differ" % bad)
        sys.exit(1 if bad else 0)
    for rel, info in build(master, args.root):
        print(rel, " ".join("%s=%s" % kv for kv in info.items()))
    if args.preview:
        previews(args.root, args.preview)


if __name__ == "__main__":
    main()
