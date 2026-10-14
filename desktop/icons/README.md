# Almond Pure icons

Almond Pure is the icon theme of Almond Linux (AALDM, the lightweight
edition): flat, warm colours, clear silhouettes, no gradients, no shadows,
no transparency. This directory holds the main theme and six folder-colour
variants.

> **Status: Implemented (source exists, untested).** The icons have only been
> drawn and checked as images (rendered to PNG on macOS) and by
> `tools/check-icons.py` (XML, forbidden SVG features, links, `index.theme`,
> status colours). None of this has run on Linux yet. Nothing here has been
> tried in LXQt, pcmanfm-qt, a GTK application or an icon cache. Every
> statement below about how the desktop *uses* these files describes the
> intended behaviour, not something that was observed.

## Layout

```
desktop/icons/
  Almond-Pure/              the theme (Name=Almond Pure)
    index.theme             directories + Inherits=Adwaita,hicolor
    16/<context>/           16 px pixel-aligned SVGs, used for 14-18 px
    24/<context>/           24 px pixel-aligned SVGs, used for 20-28 px
    scalable/<context>/     64x64 SVGs, used for every other size (8-512)
  Almond-Pure-Green/        folder colour variants: folder icons only,
  Almond-Pure-Blue/         Inherits=Almond-Pure for everything else
  Almond-Pure-Orange/
  Almond-Pure-Red/
  Almond-Pure-Gray/
  Almond-Pure-Plum/
```

Contexts: `apps`, `places`, `devices`, `mimetypes`, `actions`, `status` (64 px
scalable); `actions`, `status`, `places`, `devices` and `mimetypes` (only
`inode-directory`) at 16 and 24 px; `apps` (only the Almond logo) at 16 px.
Icon names follow the freedesktop.org Icon Naming Specification. Common
alternative names are relative symlinks in the same directory, for example
`start-here` and `distributor-logo` (the Almond logo),
`system-suspend-hibernate` and `system-hibernate` (the suspend icon),
`battery-caution-charging` and `battery-empty-charging` (the low-charging
battery). There are no `-symbolic` aliases.

`index.theme` lists the 16 and 24 px directories **before** the scalable ones.
Qt and the freedesktop lookup algorithm take the first listed directory whose
size matches, and a scalable directory matches every size from 8 to 512, so
the other order would hide the pixel-aligned small icons. The small
directories are `Type=Threshold` (`Threshold=2` at 16, `Threshold=4` at 24),
so a request for 14-18 px uses the 16 px drawing and a request for 20-28 px
(a 22 px panel, for example) uses the 24 px drawing. With `Type=Fixed` only
exactly 16 and 24 px would.

Almond Pure does not draw icons for third-party applications (Firefox and so
on). Those applications keep their own icons.

## Style rules (short version)

- SVG 1.1, `viewBox="0 0 64 64"` (or 16 / 24 for the small sizes), no
  `width`/`height`, artwork inside 4..60.
- Flat fills. Up to two tones per object (front and a ~15 % darker back) and
  one darker lip line. No gradients, filters, blur, shadows, opacity, text,
  raster images or external references.
- Corner radius 3-4 on large shapes; strokes 3-4 wide with round caps/joins.
- Glyphs: Off-White `#F5F2EB` on coloured bodies, Dark Brown `#2B2118` or
  Charcoal `#202125` on light bodies.
- Bare glyphs with no body of their own (the 16 and 24 px status icons and
  the `window-*` actions) sit straight on the panel or a menu, which may be
  dark or light. They use one warm tan that reaches at least 3:1 (WCAG
  non-text contrast) on both, plus colours chosen the same way:

  | Colour | Use | On Charcoal `#202125` | On Off-White `#F5F2EB` |
  |---|---|---|---|
  | Status Tan `#A3703A` | the glyph | 3.78:1 | 3.81:1 |
  | Dim grey `#7B7B7B` | unlit bars and waves, disabled glyphs | 3.80:1 | 3.79:1 |
  | Low orange `#B8672A` | the level in `battery-low` | 3.84:1 | 3.75:1 |
  | Muted Red `#C55454` | muted, empty, caution, the "off" badge | 3.65:1 | 3.94:1 |

  Off-White and Dark Brown appear only *on top of* a glyph: the cross on the
  red badge and the charging bolt (Off-White fill, Dark Brown outline). Lit
  and unlit parts have the same lightness, so neither background reverses
  them; they differ in colour (tan against grey), not in brightness, so a
  viewer who cannot tell those colours apart sees no difference between lit
  and unlit signal bars. On the Golden Beige highlight of a selected menu row
  the tan is only about 1.9:1.
- Dark tiles (terminal, system monitor, launcher) have a 1-unit Warm Gray
  `#8B8B8B` rim so their outline holds on the Charcoal and Dark Brown
  launcher background.
- Small files (target under 3 KB, never over 8 KB).

## Folders ("Almond Fold")

All folder icons come from `tools/make-folders.py`: one folder shape (back
panel with a tab, front panel with 4-unit corners), one emblem and one colour
from a table. Do not edit the generated SVGs by hand; change the generator
and run it again.

| Icon | Emblem | Colour in Almond Pure |
|---|---|---|
| `folder` | none | Golden Beige |
| `folder-open` | open front, sheet of paper | Golden Beige |
| `user-home` | house | Golden Beige |
| `folder-documents` | page with lines | Golden Beige |
| `folder-download` | arrow into a tray (16 px: 3 px stem, stepped 5 px head) | Forest Green |
| `folder-pictures` | picture with mountains and sun | Golden Beige |
| `folder-music` | two beamed notes | Muted Red |
| `folder-videos` | film strip with play button | Plum |
| `user-desktop` | monitor | Slate `#4A4F5C` |
| `folder-publicshare` | two people (24 px: one person) | Golden Beige |
| `folder-templates` | stacked pages | Golden Beige |
| `folder-projects` (not a freedesktop name) | small folder, tone on tone | Golden Beige |
| `folder-remote` | globe (24 px: outline circle, one meridian, one parallel) | Golden Beige |

Aliases (symlinks): `folder-downloads`, `folder-desktop`, `folder-home`,
`folder-network`, `folder-public`.

Other icons drawn by the same script (main theme only):
`user-trash` (grey bin), `user-trash-full` (the same bin with two sheets of
paper; the flat lid is lifted straight up, at every size),
`network-workgroup` (three connected computers), and
`apps/system-file-manager` (the Files application: exactly the `folder`
drawing, so the file manager and its folders match).

At 16 px only the home, download, documents, pictures, music, videos and
desktop folders keep an emblem; the rest are plain folders at that size.

## Folder colours

Each `Almond-Pure-<Colour>` directory is a complete, tiny icon theme. It
contains only the folder icons, drawn in that colour, plus an `index.theme`
with `Inherits=Almond-Pure`. Every other icon falls back to Almond Pure.

**Choosing a different icon theme is choosing a folder colour.** In LXQt:
*Preferences → LXQt Settings → Appearance → Icons Theme*, then pick
"Almond Pure Green", "Almond Pure Blue" and so on. (Expected to work this way.
Untested.) No daemon, no script and no extra package is needed.

In a variant every folder takes the variant colour, including Downloads,
Music, Videos and Desktop. The emblem shapes stay the same; the emblem colour
follows the glyph rule (Off-White or Dark Brown, whichever contrasts more
with the folder; Charcoal on Gray).

Every theme has `mimetypes/inode-directory.svg` at each size where it has a
`places/folder.svg`: a relative symlink to `../places/folder.svg`. File
managers built on GIO, such as pcmanfm-qt, usually ask for `inode-directory`
before `folder`. Without the link a variant would show Almond Pure's beige
generic folder, and a 16 or 24 px request would get the scalable drawing.

GTK applications read their own icon setting (`gtk-icon-theme-name`), so they
only follow the change if that setting changes too. Untested.

## Regenerating

```
python3 tools/make-folders.py            # writes the places icons, the
                                         # inode-directory links, the Files
                                         # icon and the variants
python3 tools/make-folders.py --check    # verifies the files on disk match;
                                         # exits 1 if anything is stale
python3 tools/make-mimetypes.py          # writes scalable/mimetypes
python3 tools/check-icons.py             # checks the whole tree (see below)
```

Standard library only, deterministic output. To change a colour, edit
`FOLDER_COLOURS` at the top of the script. To add a variant, add a line to
`VARIANTS`. The script also checks every file: valid XML, no forbidden SVG
features, under 8 KB, and emblem contrast of at least 3:1.

`tools/check-icons.py` checks every theme: each SVG is valid XML with a
viewBox matching its size directory and no gradients, filters, masks, clip
paths, text, images or opacity; each symlink is relative and resolves inside
its theme; each `index.theme` lists exactly the directories that exist, small
ones first; and the small status icons use only the colours in the table
above. The other icons (apps, actions, devices, the 16/24 px status icons)
are drawn by hand; the browser globe and the photo frame are pre-clipped
outlines, not `clipPath`.

## Trying it on a Linux machine

Untested steps:

```
mkdir -p ~/.local/share/icons
cp -RP desktop/icons/Almond-Pure* ~/.local/share/icons/   # keeps the links
```

If an `icon-theme.cache` exists for these themes, rebuild it after any change
(`gtk-update-icon-cache -f ~/.local/share/icons/Almond-Pure`), otherwise GTK
applications may keep showing the old icons.

## Differences from the mockup

The approved mockups are AI-generated pictures. The icons follow them with
these deliberate changes:

- Documents and Templates use a dark page silhouette with light lines instead
  of the mockup's cream paper: cream on Golden Beige is about 2:1 contrast
  and disappears at small sizes.
- Pictures stays Golden Beige with a dark picture glyph (the mockup shows a
  blue picture across the folder).
- Trash is a grey bin, not a grey folder with a bin glyph.
- Projects keeps the mockup's faint tone-on-tone folder mark, so at 16 and
  24 px it looks almost like a plain folder.
- No highlights or soft shading: the mockup's slight sheen is replaced by flat
  two-tone panels.
- Small status icons are tan, not white: white glyphs disappear in light
  menus and popups (network list, volume popup).

## Licence

The icon files are Almond's own work and are covered by the MIT License in
the repository root. The Almond name and the almond logo are excluded; see
`NOTICE`. The logo files here are `apps/almond.svg` (scalable and 16 px; the
16 px file is a copy of `branding/logo/almond-mark-16.svg`) and the links to
them (`almond-logo`, `start-here`, `distributor-logo`).
