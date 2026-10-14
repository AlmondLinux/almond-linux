# Almond Linux boot artwork

**Status:** these files have **not been tested at runtime**. No Almond Linux
image has been built or booted yet. The notes below come from reading the
Debian 13 "trixie" source of plymouth 24.004.60, grub2 2.12 and syslinux 6.04.

**License:** this is logo artwork. It is not covered by the MIT license; see
[`NOTICE`](../../NOTICE).

**Source:** every PNG here is generated from the logo master by
[`tools/make-logo-png.py`](../../tools/make-logo-png.py); see
[`branding/logo/README.md`](../logo/README.md). The transparent PNGs follow
the same alpha rule as the logo PNGs: no pixel with alpha 1-16.

## Plymouth theme `almond` (`plymouth/almond/`)

A static splash: the single-colour light almond mark (Off-White `#F5F2EB`,
the golden highlights cut out, 200 px tall), centred on flat Dark Brown
`#2B2118`. Nothing moves.

The mark is the same single-colour artwork as the GRUB and isolinux
backgrounds, so the boot looks the same from the boot menu to the splash.
The full-colour mark is not used here: its dark outline (`#3E210F`) almost
disappears on Dark Brown.

### Why `two-step`

- **`two-step`** is used with every animation off: `UseAnimation=false`,
  `UseEndAnimation=false`, `UseProgressBar=false`, no throbber or animation
  frames, and `Transition=none`. In this setup it redraws the screen only when
  something changes, such as a boot message or the password prompt.
- **`script`** was rejected. Its plugin re-arms a refresh timer for the whole
  boot (50 per second by default), even when the script draws nothing new.
- **Flat background:** the start and end colours are the same, so `two-step`
  fills the screen with one colour instead of drawing a gradient.

### Files

| File | Role |
|---|---|
| `almond.plymouth` | Theme definition. It has comments that explain each choice |
| `watermark.png` | The logo, drawn once in the centre of the screen. 136 x 200, `#F5F2EB` on transparent, 256-colour palette + alpha |
| `lock.png`, `entry.png`, `bullet.png` | The password prompt for encrypted disks. `two-step` refuses to start if any of them is missing, so they are required. The prompt sits at 75% of the screen height, below the logo |

Boot messages appear centred on the top line. With no animation, there is
nothing for `MessageBelowAnimation` to sit under.

**Check (still image only):** the script's `--preview` option composites the
watermark and the password prompt on Dark Brown at 1024 x 768 and
1366 x 768. Those previews were looked at: the Off-White mark is clearly
visible and the prompt sits below it. This is a picture of the intended
screen, not a boot test.

### Install (untested)

1. Install the package `plymouth-themes`. In trixie, `two-step.so` ships in
   that package, not in `plymouth`.
2. Copy the directory to `/usr/share/plymouth/themes/almond/`.
3. Run `plymouth-set-default-theme -R almond`. The `-R` option rebuilds the
   initramfs.
4. Boot with `quiet splash` on the kernel command line.

A graphical splash needs a KMS driver in the initramfs. On Intel graphics
that is `i915`. Without it, plymouth falls back to text mode.

## `isolinux-splash.png` (legacy-BIOS boot menu)

- **Image:** 640 x 480, 8-bit palette with 32 colours. Off-White
  (`#F5F2EB`) single-colour lockup on Dark Brown.
- **Format support:** the vesamenu PNG loader in syslinux 6.04 converts palette
  images (`png_set_palette_to_rgb` in `com32/lib/sys/vesa/background.c`).
- **Placement:** the lockup is centred left to right and sits at the top of
  the screen, not in the middle: box x 258, y 20, 124 x 150. The live-build
  default `stdmenu.cfg` (`menu vshift 12`) starts the menu entries on row 12,
  at about y 192 with the default 16 px font. The menu therefore stays clear
  of the logo.
- **Menu colours:** the menu colours belong to the boot-menu configuration, not
  to this image. One suggestion that fits the palette:
  `menu color sel * #ff2b2118 #ffd2a679 *` and
  `menu color title * #fff5f2eb *`.

## `grub-background.png`

- **Image:** 1024 x 768, 8-bit RGB, not interlaced. Same look as the isolinux
  splash: lockup box x 404, y 60, 215 x 260.
- **Format:** the GRUB 2.12 PNG reader rejects interlaced files. It also
  accepts palette images, but RGB is used because it works in every GRUB
  version.
- **Placement:** the live-build GRUB theme puts `boot_menu` at `top = 52%`
  (y of about 399). The lockup ends at y 320, so the two do not overlap.
- **Scaling:** when the image is used as a theme's `desktop-image`, GRUB
  stretches it to the screen size by default.
