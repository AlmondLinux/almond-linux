# Almond Linux logo

These files are the Almond Linux logo: the brown almond with three golden
curved lines (the **mark**) and the full **lockup** (mark + "Almond" + "Linux").

**License:** the Almond Linux name and logo are **not** covered by the MIT
license of this repository. They identify the project and are not licensed for
reuse. See [`NOTICE`](../../NOTICE). This covers every file in `branding/logo/`
and `branding/boot/`, plus the `almond` icon in the Almond Pure icon theme.

## Source

All files come from the logo master approved by the owner,
`almond-logo-original.webp`. It is a 1254 x 1254 transparent raster, kept
outside this repository. The logo was not redesigned. The vector files are
traced from the master, and the PNG files are resampled from the master
raster, not from the SVGs, by
[`tools/make-logo-png.py`](../../tools/make-logo-png.py) (Python 3 and
Pillow). With the master at hand, run
`python3 tools/make-logo-png.py path/to/almond-logo-original.webp` to rebuild
every PNG listed below and in `branding/boot/`, or add `--check` to compare
the files on disk with a fresh build. The script only reads the master and
refuses a file whose SHA-256 differs from the approved one.

Logo colours (measured from the master):

| Part | Colour | Note |
|---|---|---|
| Outline and lettering | `#3E210F` | Matches the palette's logo outline brown |
| Almond fill | `#9C5D25` | The logo's own brown. Almond Brown `#8B5A2B` is the UI colour |
| Highlights | `#EBBA7B` | The logo's own gold. Golden Beige `#D2A679` is the UI colour |
| Single colour, dark | `#2B2118` | Dark Brown, for light backgrounds |
| Single colour, light | `#F5F2EB` | Off-White, for dark backgrounds |

## Files

### Vector (`branding/logo/`)

| File | Purpose |
|---|---|
| `almond-mark.svg` | The mark in full colour. Three flat layers: outline shape, fill, three highlights. viewBox 506 x 742, tight around the mark |
| `almond-logo.svg` | The full lockup in full colour. The "Almond" and "Linux" lettering is traced outlines, not a font. viewBox 826 x 996 |
| `almond-mark-mono-dark.svg` | The mark in one colour, `#2B2118`, for light backgrounds. The highlights are cut out (transparent) |
| `almond-mark-mono-light.svg` | The same mark in `#F5F2EB`, for dark backgrounds |
| `almond-logo-mono-dark.svg` | The lockup in one colour, `#2B2118`, highlights cut out |
| `almond-logo-mono-light.svg` | The lockup in one colour, `#F5F2EB`. The boot menus use it |
| `almond-mark-16.svg` | A simplified mark on a 16 x 16 grid, for 16-24 px use (see "Small sizes") |

The full-colour lockup uses dark lettering, which almost disappears on Dark
Brown or Charcoal. On a dark background, use a `-mono-light` file.

### Raster (`branding/logo/png/`)

| File | Size | Format |
|---|---|---|
| `almond-mark-512.png` | 512 x 512 | 256-colour palette + alpha (difference 0.94) |
| `almond-mark-256.png` | 256 x 256 | 256-colour palette + alpha (difference 1.03) |
| `almond-mark-128.png` | 128 x 128 | 256-colour palette + alpha (difference 1.33) |
| `almond-mark-64.png` | 64 x 64 | 256-colour palette + alpha (difference 1.79) |
| `almond-mark-48.png` | 48 x 48 | RGBA (the palette version differed by 2.00, not below the limit of 2) |
| `almond-mark-32.png` | 32 x 32 | RGBA (the palette version differed by 2.20) |
| `almond-mark-16.png` | 16 x 16 | RGBA (the palette version differed by 2.31) |
| `almond-logo-1024.png` | 1024 x 1195 | Full lockup, 256-colour palette + alpha (difference 0.93) |

How the PNG files were made (all by `tools/make-logo-png.py`):

- **Alpha rule:** no transparent PNG in `branding/logo/png/` or
  `branding/boot/plymouth/almond/` has a pixel with alpha between 1 and 16.
  Such pixels are cleared to fully transparent (alpha 0) in the master, again
  after every resize (the filter leaves a faint fringe), and again after
  palette reduction: a palette entry with alpha 16 or less is set to fully
  transparent, and every transparent pixel uses such an entry. This removes
  the nearly invisible stray pixels and the faintest edge fringe.
  Compression noise in solid areas (alpha 248-254) is set to fully opaque, in
  the master and in the palette.
- **Mark PNGs:** the mark was trimmed, then centred in a 790 x 790 square with
  3% transparent padding. It was downscaled with Lanczos on premultiplied alpha,
  so the edges have no dark fringe.
- **Palette:** a file uses a 256-colour palette only when the mean absolute
  channel difference from the full-colour image is below 2, over visible pixels.
  The difference is shown in the table above. The RGBA files are exact.
- **Lockup PNG:** `almond-logo-1024.png` is an exact 1024 x 1195 window of the
  master, with no resampling. It has about 100 px of transparent padding.

**Check (2026-10-14):** every PNG above has 0 pixels with alpha 1-16. Against
the previous files, the mean difference after compositing on white is below
0.6 for 512-64 px and the lockup, 1.5 for 48 px and 0.25 for 32 px. For 16 px
it is 2.25 on white (1.06 on Dark Brown): 0.54 of that is the removed faint
haze, the rest is the old file's palette error, because the new 16 px file is
exact RGBA. Side-by-side renders at 6x zoom on white and on Dark Brown showed
no visible change.

### Icon theme

| File | Purpose |
|---|---|
| `desktop/icons/Almond-Pure/scalable/apps/almond.svg` | The application or distributor icon on the 64 x 64 grid. The mark is 56 units tall (y 4-60) and centred |
| `desktop/icons/Almond-Pure/scalable/apps/almond-logo.svg` | A relative symlink to `almond.svg` |
| `desktop/icons/Almond-Pure/scalable/apps/start-here.svg`, `distributor-logo.svg` | Relative symlinks to `almond.svg` (names menus and panels commonly request) |
| `desktop/icons/Almond-Pure/16/apps/almond.svg` | A copy of `almond-mark-16.svg` for 16 px (and 14-18 px via Threshold=2), with the same `almond-logo`, `start-here` and `distributor-logo` aliases |

### Boot artwork (`branding/boot/`)

See [`branding/boot/README.md`](../boot/README.md).

| File | Purpose |
|---|---|
| `plymouth/almond/almond.plymouth` | Plymouth theme "Almond". Uses the `two-step` module, fully static |
| `plymouth/almond/watermark.png` | The single-colour light mark (`#F5F2EB`, highlights cut out), 136 x 200, transparent. The splash logo, same artwork as the GRUB and isolinux backgrounds |
| `plymouth/almond/lock.png`, `entry.png`, `bullet.png` | The password prompt for encrypted disks. `two-step` does not load without these three files |
| `isolinux-splash.png` | 640 x 480, 8-bit palette (32 colours). Legacy-BIOS boot menu background |
| `grub-background.png` | 1024 x 768, 8-bit RGB, not interlaced. GRUB background |

## How the vectors were made

1. **Separate the layers.** Each master pixel was projected onto the colour
   axis outline→fill and onto the axis fill→highlight. This gives three smooth
   fields: alpha, interior and highlight.
2. **Trace.** Marching squares followed each field's boundary at the 50% level,
   with sub-pixel interpolation.
3. **Fit curves.** Each boundary was resampled. Sharp corners (the highlight
   tips, the letter corners) were detected and kept. The segments between
   corners were lightly smoothed and simplified with Douglas-Peucker
   (0.1 px tolerance). Each segment was then fitted with cubic Beziers
   (Schneider's algorithm), with a maximum error of 0.3 master px.
4. **Stack.** The layers sit on top of each other: outline shape, then fill,
   then the three highlights. The lettering uses `fill-rule="evenodd"` for the
   counters of "A", "o" and "d".

**Check:** each SVG was rendered with macOS QuickLook at the master's pixel
size, so 1 px equals 1 master px. Every pixel of the render and of the master
was sorted into a colour class. The table shows the IoU (intersection over
union) of each layer between render and master:

| Layer | `almond-mark.svg` | `almond-logo.svg` |
|---|---|---|
| Outline layer (whole silhouette) | 0.9992 | 0.9992 |
| Fill layer (interior) | 0.9966 | 0.9966 |
| Highlight layer (3 strokes) | 0.9797 | 0.9797 |
| Visible outline ring alone | 0.9887 | 0.9887 |
| Lettering "Almond" + "Linux" | n/a | 0.9959 |

The single-colour files were checked the same way. The ink (silhouette minus
the highlights) scored 0.9973 for the mark and 0.9967 for the lockup.

## Small sizes

The mark has fine details: a 25 px outline and highlights at most 35 px wide,
in a mark 742 px tall. These details get blurry at icon sizes, so both
small-grid files have optical adjustments. Both were made on the master raster
with an exact distance field and then traced again, so the silhouette is
unchanged:

- **`almond.svg` (64 grid):** the outline ring is about 2.6 units instead of
  1.9. Each highlight is about 0.3 units wider on each side. All three
  highlights are kept.
- **`almond-mark-16.svg` (16 grid):** the outline ring is about 1.1 px and the
  highlights are about 1 px wide. The short left highlight is left out, because
  at 16 px it merges with the fill. The S-curve and the right highlight stay.
  The long left flank sits on a pixel edge.

Both were rendered at 16, 24, 32, 48 and 64 px and checked on white and on Dark
Brown.
