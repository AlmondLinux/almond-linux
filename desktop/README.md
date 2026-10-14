# Almond Pure desktop for AALDM

This folder holds the look and the default settings of the **AALDM** edition
(A All Little Distribution Model) of Almond Linux: LXQt with Openbox on X11,
using the **Almond Pure** design.

> **Status: Implemented (source exists, untested). Nothing here has run yet.**
> The files were written and checked on a Mac. No Linux or X11 session was
> available, so every runtime behaviour
> described below is **untested**. What *was* checked is listed in
> [What was checked](#what-was-checked).

Performance comes first. All of it is flat: solid colours, no gradients, no
blur, no transparency, no animations, and nothing that needs a compositor.
The launcher runs only while it is open.

## What is in this folder

| Folder | What it is |
|---|---|
| `openbox/` | **Almond Frame**: Openbox window-frame themes `Almond-Pure-Light`, `Almond-Pure-Dark`, `Almond-Pure-Ocean` (themerc plus button bitmaps) |
| `launcher/` | **Almond Launcher**: `almond-launch` (a rofi front end), its two helper modes, three rofi themes, a desktop entry and an example settings file |
| `lxqt/themes/` | LXQt themes `almond-pure-dark` and `almond-pure-light` (panel, notifications, runner, tooltips) |
| `lxqt/palettes/` | Qt colour palettes `Almond-pure-light`, `Almond-pure-dark`, `Almond-pure-ocean` |
| `lxqt/globalkeyshortcuts.conf` | Almond's global shortcut: the Super key opens the launcher (merged with Debian's default shortcuts at build time) |
| `defaults/` | System-wide defaults, laid out as they are installed (`defaults/etc/...` becomes `/etc/...`) |
| `gtk/settings.ini` | GTK 3 fallback settings (Firefox ESR and other GTK apps) |
| `wallpapers/` | Wallpapers `almond-pure-light.svg` (default), `almond-pure-dark.svg`, `almond-pure-ocean.svg` |
| `icons/` | The Almond Pure icon theme, made separately. See the files there. |

**Openbox themes only style the window frame**: the title bar, its buttons,
the border, Openbox's own menus and the Alt+Tab list. They never change
toolbars, buttons or colours *inside* applications. Those come from the Qt
palette and widget style (LXQt Appearance) and from GTK settings.

## Where each file is installed

| In this repository | On the installed system |
|---|---|
| `openbox/Almond-Pure-Light/` (and `-Dark`, `-Ocean`) | `/usr/share/themes/Almond-Pure-Light/` (keeps the `openbox-3/` subfolder) |
| `launcher/almond-launch` | `/usr/bin/almond-launch` |
| `launcher/almond-launch-recent`, `launcher/almond-launch-power` | `/usr/libexec/almond/` |
| `launcher/almond-launch.rasi`, `-light.rasi`, `-ocean.rasi` | `/usr/share/almond/launcher/` |
| `launcher/almond-launch.desktop` | `/usr/share/applications/almond-launch.desktop` |
| `launcher/launcher.conf.example` | `/usr/share/almond/launcher/launcher.conf.example` |
| `lxqt/themes/almond-pure-dark/`, `almond-pure-light/` | `/usr/share/lxqt/themes/` |
| `lxqt/palettes/*` | `/usr/share/lxqt/palettes/` |
| `lxqt/globalkeyshortcuts.conf` | `/usr/share/almond/lxqt/globalkeyshortcuts.conf`; the 0200 hook merges it with Debian's defaults into the file `/etc/xdg/lxqt/globalkeyshortcuts.conf` |
| `defaults/etc/xdg/lxqt/lxqt.conf`, `session.conf`, `panel.conf` | `/etc/xdg/lxqt/` |
| `defaults/etc/xdg/openbox/lxqt-rc.xml` | `/etc/xdg/openbox/lxqt-rc.xml` |
| `defaults/etc/xdg/pcmanfm-qt/lxqt/settings.conf` | `/etc/xdg/pcmanfm-qt/lxqt/settings.conf` |
| `defaults/usr/bin/almond-openbox` | `/usr/bin/almond-openbox` |
| `gtk/settings.ini` | `/etc/gtk-3.0/settings.ini` |
| `wallpapers/*.svg` | `/usr/share/backgrounds/almond/` |
| `icons/Almond-Pure/` | `/usr/share/icons/Almond-Pure/` |

These paths should not collide with Debian 13 packages. Checked: the
packages.debian.org file lists of `openbox` (it owns
`/etc/xdg/openbox/rc.xml`, which is why Almond uses `lxqt-rc.xml` and a
wrapper instead), `libgtk-3-common` (no `/etc/gtk-3.0/settings.ini`) and
`lxqt-globalkeys` (see below), and the LXQt and PCManFM-Qt sources (they
install their defaults under `/usr/share/lxqt/` and `/usr/share/pcmanfm-qt/`).
The Almond-named files are new names.

**One Debian path is special:** Debian 13's `lxqt-globalkeys` 2.1.0-2
installs `/etc/xdg/lxqt/globalkeyshortcuts.conf` as a **directory** that
holds Debian's default shortcuts
(`/etc/xdg/lxqt/globalkeyshortcuts.conf/globalkeyshortcuts.conf`; its
`debian/lxqt-globalkeys.install` names that path as the destination
directory, and forky's 2.4.0-1 installs a plain file instead). A file staged
at that path would collide with the package, and `lxqt-globalkeysd`, which
only reads a file there, never loads Debian's defaults. So Almond's file is
staged to `/usr/share/almond/lxqt/`, and the `0200-almond-desktop` hook
writes a plain file at that path: Debian's entries (Ctrl+Alt+T terminal,
Print screenshot, brightness and other XF86 keys, ...) followed by Almond's
Super entry. Debian's Ctrl+Alt+L entry (`xdg-screensaver lock`) is kept but
does nothing until a screen locker is installed (none in 0.1). Debian's originals stay in
`/usr/share/almond/lxqt/debian-defaults/`. Known risk (untested): on an
installed system, an `lxqt-globalkeys` update that still ships the directory
may fail to unpack over that file; the live image is not upgraded in place.

The scripts are POSIX `sh` and work from a source checkout too:
`desktop/launcher/almond-launch` uses the themes and helpers next to it.

### Debian packages these files expect

Not decided here (the package list lives in `config/package-lists/`), listed
so nothing is missed: `lxqt-session`, `lxqt-panel`, `lxqt-globalkeys`,
`lxqt-config`, `lxqt-qtplugin`, `lxqt-notificationd`, `lxqt-powermanagement`
(battery icon), `openbox`, `obconf-qt`, `pcmanfm-qt`, `rofi` (1.7.5 in
Debian 13), `nm-tray` (network icon; ships its own autostart entry),
`xdg-utils` (`xdg-open`), `dbus-bin` (`dbus-send`), `procps` (`ps`),
`qt6-svg-plugins` (SVG wallpaper and icons in Qt), `fonts-dejavu-core`, and a
screen locker for "Lock" (not chosen yet). `pavucontrol-qt` is what the
volume control's "Mixer" button opens by default.

## Almond Frame (Openbox themes)

* Compact title bar: `padding.height: 3`, `padding.width: 4`, no bottom
  handle, no client padding. With the 10 pt title font set in
  `lxqt-rc.xml` the title bar should be about 22 px high (estimate from
  Openbox's size rules, not measured).
* Thin border: `border.width: 1`. The active window's border uses the accent;
  inactive windows are muted.
* Buttons, left to right: app icon, title, minimise, maximise, close
  (`NLIMC`). All glyphs are 9x9 bitmaps with the same 1 px stroke:
  minimise = one bar at the bottom, maximise = one square, restore (shown
  when maximised) = two offset squares, close = X. `desk` (all desktops) and
  `shade` glyphs are included for people who add those buttons.
* Close turns Muted Red `#C55454` on hover (darker `#A84545` when pressed),
  with an Off-White X. Other buttons get a flat tinted square on hover.
* Flat textures only (`flat solid` or `parentrelative`), no text shadows.

| Theme | Active title | Inactive title | Active border |
|---|---|---|---|
| Almond-Pure-Light | Warm Cream `#F5DEB3`, Dark Brown text | Off-White `#F5F2EB`, `#6B6258` text | Almond Brown `#8B5A2B` |
| Almond-Pure-Dark | Dark Brown `#2B2118`, Warm Cream text | Charcoal `#202125`, `#A39A8E` text | Golden Beige `#D2A679` |
| Almond-Pure-Ocean | Deep blue `#2F5A8A`, Off-White text | Slate `#3C4A58`, `#C8D0D8` text | Muted Blue `#4B7CB8` |

Contrast (WCAG 2.1 formula, computed from the themerc files):

| Theme | Pair | Ratio |
|---|---|---|
| Light | active title text `#2B2118` on `#F5DEB3` | 11.99 |
| Light | inactive title text `#6B6258` on `#F5F2EB` | 5.35 |
| Dark | active title text `#F5DEB3` on `#2B2118` | 11.99 |
| Dark | inactive title text `#A39A8E` on `#202125` | 5.80 |
| Ocean | active title text `#F5F2EB` on `#2F5A8A` | 6.37 |
| Ocean | inactive title text `#C8D0D8` on `#3C4A58` | 5.82 |
| all | menu text / selected menu text | 7.10 to 14.09 |
| all | close glyph `#F5F2EB` on `#C55454` (a graphic, needs 3:1) | 3.94 |

The Ocean title blue is Muted Blue darkened: Off-White on Muted Blue itself
is only 3.85:1.

**Keys.** Every key used in the three themerc files was checked
automatically against the keys that Openbox 3.6.0's own theme loader
(`obrender/theme.c`) reads (Debian 13 ships Openbox 3.6.1), and compared with
the openbox.org theme guide (now at <https://openbox.org/help/Themes>; the
old `wiki/Help:Themes` address returns 404). Keys used here that the guide
does **not** list, but the 3.6 source does read: the per-button close keys
(`window.*.button.close.hover.*`, `...close.pressed.*`),
`menu.bullet.image.color`, `menu.bullet.selected.image.color`,
`osd.active.label.*`, `osd.inactive.label.*` and `osd.button.*`. They are
treated as correct because the loader reads them, but they have not been
seen working. The guide and the source also disagree on the names of the
optional hover bitmaps for toggled buttons (`max_toggled_hover.xbm` in the
guide, `max_hover_toggled.xbm` in the source); Almond ships neither, so
Openbox reuses `max_toggled.xbm`. Not checked: how the 9x9 glyphs look with
much smaller title fonts (they are centred in the button).

## Almond Launcher

`almond-launch` opens **rofi** in Almond's style. rofi is in Debian, works on
X11 and is not running when the launcher is closed.

**How it behaves (as designed, untested):**

* Press and release **Super** (the Windows key): the launcher opens.
  Press Super again, or Escape, or click outside it: it closes.
  Running `almond-launch` while it is open also closes it (toggle, using a
  pid file that rofi writes in `$XDG_RUNTIME_DIR`, or in `~/.cache` when
  that is not set; never in `/tmp`).
* Typing searches at once. Arrow keys move through the grid, Enter opens,
  one mouse click opens.
* Four modes, switched with Ctrl+Tab, Shift+Left/Right or the buttons on the
  left. Their labels are passed on the rofi command line, so they do not
  depend on the theme file:
  * **Apps**: installed applications (rofi `drun`), as an icon grid.
  * **Windows**: open windows; choosing one switches to it (rofi `window`).
  * **Recent**: the 15 most recent local files that still exist, newest
    first, from `~/.local/share/recently-used.xbel`, opened with `xdg-open`.
    If that file is missing, the list is empty and says so. GTK programs
    write this file; many Qt/LXQt programs do not, so the list may be short.
  * **System**: Settings (opens `lxqt-config`), Lock, Log Out, Sleep,
    Restart, Shut Down. Log Out, Restart and Shut Down ask "...now?" first.
    They then ask the LXQt session over D-Bus to end cleanly; without an
    LXQt session they use `loginctl` / `systemctl`. Sleep uses
    `systemctl suspend`; Lock uses `lxqt-leave --lockscreen`, which needs a
    screen locker to be installed.
* rofi takes the keyboard while it is open, so LXQt cannot see the second
  Super press. That is why rofi itself is told to close on `Super_L`
  (`-kb-cancel`). Alt+Tab and the other window shortcuts are not changed.
* Hold-to-reveal is **not** implemented (not approved).

**The Super key binding** is the entry `[Super_L.50]` (command
`almond-launch`) that the 0200 hook adds to
`/etc/xdg/lxqt/globalkeyshortcuts.conf`, after Debian's default shortcuts
(see [Where each file is installed](#where-each-file-is-installed)).
lxqt-globalkeys runs it when Super is pressed and released on its own, not
for Super+key combinations. To change the key: *LXQt Settings, Shortcut
Keys*, select "Almond Launch" and record another key (for example Alt+F1).
Known risk (untested): while LXQt holds the bare Super key, Openbox's own
Super+key shortcuts in `lxqt-rc.xml` (Super+D, Super+F1...) may not reach
Openbox. If that happens, move those shortcuts into LXQt's Shortcut Keys or
bind the launcher to another key. Alt+F2 is free: `lxqt-runner`, which
registers that key, is not installed, and Debian's default shortcuts do not
bind it.

**Panel button:** the almond button at the left of the panel runs the same
command (quick-launch entry pointing at `almond-launch.desktop`).

**Launcher theme:** dark by default. To change it, create
`~/.config/almond/launcher.conf` containing one of

```
ALMOND_LAUNCH_THEME=dark
ALMOND_LAUNCH_THEME=light
ALMOND_LAUNCH_THEME=ocean
```

The file is read as text, never run. An environment variable with the same
name overrides it. A complete personal rofi theme can be placed at
`~/.config/almond/launcher.rasi`; it replaces the built-in ones.
`almond-launch` starts rofi with `-no-config`, so other rofi settings a
user may have do not change the launcher.

**Differences from mockup image 2 (and why):**

* The mockup shows apps, a "Recent" column and a "Power" box at the same
  time. rofi shows one mode at a time, so Recent and Power (named
  "System") are modes behind the buttons on the left.
* No "Places" category: rofi has no places mode; Home, Trash and the drives
  are on the desktop and in the file manager.
* The footer shows the keys that really work instead of "Press / to search"
  and "Keep going" (rofi searches as soon as you type).
* Square window corners, solid colours, no blurred background. AALDM runs
  no compositor, and the transparent pixels outside rounded corners of
  rofi's ARGB window would show as black; buttons and cells inside the
  window keep 6 px corners.

## LXQt defaults (`defaults/`)

* `lxqt.conf`: icon theme `Almond-Pure`, LXQt theme `almond-pure-dark` (dark
  panel), Qt style Fusion, font Sans 10, and the colours of the
  `Almond-pure-light` palette for applications.
* `session.conf`: `window_manager=almond-openbox` (see below) and LXQt's
  leave confirmation kept on.
* `panel.conf`: one panel at the **top**, 28 px, 16 px icons, locked. Left:
  the almond launcher button. Middle: task list. Right: tray icons, volume,
  and the clock as `ddd, MMM d  HH:mm` (for example "Wed, Oct 14  21:57";
  it redraws once a minute). The tray holds the network icon (nm-tray), the
  battery icon and other apps' icons. LXQt power management only shows a
  battery icon when it finds a battery: on its first run it checks for one
  and switches battery monitoring off on desktop PCs (lxqt-powermanagement
  2.1 source).
* `pcmanfm-qt/lxqt/settings.conf`: desktop icons Home, Trash and Computer,
  wallpaper `almond-pure-light.svg` in "zoom" mode, double-click to open,
  thumbnails only for local files up to 2 MiB. Volumes: nothing is mounted
  at login (`MountOnStartup=false`) and no autorun dialog appears
  (`AutoRun=false`); a USB stick plugged in during the session is still
  mounted (`MountRemovable=true`). Reasons: security, RAM, and second-hand
  test PCs whose internal disk must never be mounted.
* `openbox/lxqt-rc.xml`: theme Almond-Pure-Light, title font Sans 10,
  `animateIconify` off, one desktop, normal click-to-focus, Openbox's usual
  key and mouse bindings, minus Openbox's Super+E (it starts a KDE program
  that AALDM does not have) and Print (LXQt's shortcuts handle it: Debian's
  default runs `screengrab -f`, merged in by the 0200 hook).
* `usr/bin/almond-openbox`: starts Openbox with `lxqt-rc.xml`.

**Deviations from the task notes, with reasons:**

* `session.conf` says `window_manager=almond-openbox`, not `openbox`. LXQt 2.1
  starts that program without arguments (`lxqtmodman.cpp`), and plain
  Openbox then reads Debian's generic `/etc/xdg/openbox/rc.xml`, so a file
  called `lxqt-rc.xml` would be ignored. The wrapper copies
  `/etc/xdg/openbox/lxqt-rc.xml` to `~/.config/openbox/lxqt-rc.xml` on first
  login and starts `openbox` with that file. Openbox Settings (obconf-qt)
  then edit the user's copy.
* Application colours default to the **light** palette, not the dark one.
  The default window frame is Almond-Pure-Light and mockup image 1 shows
  light windows on the light desktop; dark application contents inside
  light frames would clash. The panel and launcher stay dark, as in the
  mockup.
* Palette files are named `Almond-pure-light`, `Almond-pure-dark`,
  `Almond-pure-ocean`, without `.conf`. LXQt palettes have no extension
  (see `lxqt-themes/palettes/`), and LXQt Appearance loads a palette
  automatically when it is named like the chosen LXQt theme with a capital
  first letter (`almond-pure-dark` -> `Almond-pure-dark`). The Ocean
  palette has no matching LXQt theme; load it by hand.
* A **task list** was added to the middle of the panel. The mockup shows no
  task list, but without one a minimised window can only be found again with
  Alt+Tab or the launcher's Windows mode. Remove `taskbar` from `plugins=`
  in `panel.conf` to match the mockup exactly.
* Desktop "drives": PCManFM-Qt 2.1 cannot put one icon per drive on the
  desktop, so the desktop shows **Computer**, which lists the drives.
* "Preview panel off": PCManFM-Qt 2.1 has no preview panel, so there is
  nothing to switch off.
* The mockup's panel is a small tray on the right only; the task asked for a
  launcher button on the left, so the panel spans the full width.

## GTK fallback

`/etc/gtk-3.0/settings.ini`: GTK theme Adwaita (built into GTK 3), icon
theme Almond-Pure, font Sans 10, light theme, animations off. A user's
`~/.config/gtk-3.0/settings.ini` wins over it. The same file can be copied to
`/etc/gtk-4.0/settings.ini` if GTK 4 apps are added later.

## Wallpapers

Three flat vector wallpapers, 16:9 (`viewBox="0 0 1920 1080"`), drawn for
Almond: large stylised leaves with veins cut out in the background colour.
No gradients, filters, images or text; each file is 2-5 KB.

| File | Colours |
|---|---|
| `almond-pure-light.svg` (default) | Warm Cream background, light beige, Golden Beige and Almond Brown leaves, and the official almond mark in the lower left, placed inside the 4:3 and 5:4 safe area so 'zoom' mode on older monitors does not crop it |
| `almond-pure-dark.svg` | Dark Brown background, muted brown and olive leaves |
| `almond-pure-ocean.svg` | Deep blue background, muted blue and teal leaves |

The almond mark is only on the light wallpaper, where it sits on cream.
PCManFM-Qt needs the Qt SVG image plugin (`qt6-svg-plugins`) to show SVG
wallpapers; it renders the file once and keeps a scaled copy in its cache.

Desktop icon labels are dark brown for the light wallpaper. With the dark
or ocean wallpaper, change the label colour in *Desktop Preferences* to a
light one (for example `#F5DEB3`), or the labels will be hard to read.

## Changing the look

| What | Where |
|---|---|
| Panel style (dark or light panel) | *LXQt Settings, Appearance, LXQt Theme*: `almond-pure-dark` or `almond-pure-light`. With "Use palette provided by theme" ticked, the matching palette is loaded as well. |
| Application colours | *Appearance, Widget Style, Load Palette*: `Almond-pure-light`, `Almond-pure-dark` or `Almond-pure-ocean` |
| Icons | *Appearance, Icons Theme*: "Almond Pure" (folder-colour variants, if installed, are listed there too) |
| Window frames | *Openbox Settings* (obconf-qt), *Theme*: Almond-Pure-Light, -Dark or -Ocean |
| Wallpaper | Right-click the desktop, *Desktop Preferences*, *Background* (files in `/usr/share/backgrounds/almond/`) |
| Launcher colours | `~/.config/almond/launcher.conf`, see above |
| Launcher key | *LXQt Settings, Shortcut Keys*, "Almond Launch" |

A matching set: Light (the shipped default) = Almond-Pure-Light frames +
`Almond-pure-light` palette + light wallpaper, with the dark panel and
launcher; Dark = Almond-Pure-Dark frames +
`almond-pure-dark` LXQt theme + `Almond-pure-dark` palette + dark wallpaper +
`ALMOND_LAUNCH_THEME=dark`; Ocean = Almond-Pure-Ocean frames +
`Almond-pure-ocean` palette + ocean wallpaper + `ALMOND_LAUNCH_THEME=ocean`.

## Restoring the defaults

Log out, delete the per-user file (or folder), and log in again:

| To reset | Delete |
|---|---|
| Appearance (themes, palette, icons, fonts) | `~/.config/lxqt/lxqt.conf` |
| Panel | `~/.config/lxqt/panel.conf` |
| Session settings | `~/.config/lxqt/session.conf` |
| Shortcut keys (brings back Super for the launcher and Debian's default shortcuts) | `~/.config/lxqt/globalkeyshortcuts.conf` |
| Window manager settings and frame theme | `~/.config/openbox/lxqt-rc.xml` (copied again from `/etc/xdg/openbox/` at the next login) |
| File manager and desktop (wallpaper, desktop icons) | the folder `~/.config/pcmanfm-qt/lxqt/` |
| Launcher theme | `~/.config/almond/launcher.conf` and `~/.config/almond/launcher.rasi` |
| GTK settings | `~/.config/gtk-3.0/settings.ini` |
| Palettes saved by the user | files in `~/.local/share/lxqt/palettes/` |

## Resource notes

**All numbers below are estimates. None were measured** (nothing has run).

* The launcher is not resident: rofi starts on Super and exits when closed.
  Estimated 10 to 20 MB of RAM while open; nothing when closed.
* The helper modes are short shell scripts that run only when their mode is
  loaded or an entry is chosen. "Recent" reads one XML file with `sed`/`awk`
  (about 0.04 s for 400 entries on the development Mac; not timed on Linux).
* No animations anywhere: Openbox iconify animation off, panel
  auto-hide animation 0, GTK animations off.
* The clock redraws once a minute (its format has no seconds).
* Thumbnails are limited to local files of 2 MiB or less, which avoids
  decoding large photos and videos on slow CPUs.
* The wallpaper is a small SVG, rendered once by PCManFM-Qt and then cached.
* No compositor is needed: no transparency or shadows are used.
* The "Lock" entry needs a screen locker, which may add a resident process;
  which one is still open.

## What was checked

On macOS (2026-10-14), without Linux:

* All shell scripts: `sh -n` and `dash -n`. `almond-launch-recent` and
  `almond-launch-power` were run under `dash` with test data and stub
  commands (recent list order, missing file, percent-decoding, confirmation
  flow); `almond-launch` was run with a stub `rofi` (theme selection, toggle
  closing an open instance).
* Every themerc key against Openbox 3.6.0's `obrender/theme.c` and the
  openbox.org theme guide; textures limited to `flat solid` /
  `parentrelative`. The 9x9 bitmaps were parsed back and drawn.
* `lxqt-rc.xml`: valid XML (`xmllint`); every action and mouse context name
  against Openbox 3.6.0 sources.
* rasi files: brace and declaration structure, property names against rofi
  1.7.5 sources, no transparency values, window corner radius 0 and inner
  radii 6 px or less. How rofi 1.7.5 reads mode labels from the command
  line (`-display-drun`, `-display-window`, `-recent-display-name`,
  `-power-display-name`) was read from its source (`mode.c`,
  `xrmoptions.c`), not seen working.
* QSS files: structure; no gradients, rgba colours or images.
* LXQt, PCManFM-Qt and lxqt-globalkeys keys against their source code at the
  versions in Debian 13 (lxqt-panel 2.1.4, lxqt-session 2.1.1,
  lxqt-globalkeys 2.1.0, pcmanfm-qt 2.1.0, lxqt-config 2.1.1, lxqt-qtplugin
  2.1.0, rofi 1.7.5).
* The `lxqt-globalkeys` 2.1.0-2 file list (packages.debian.org) and its
  `debian/lxqt-globalkeys.install` (sources.debian.org): Debian's default
  shortcuts sit in a directory. The merge in the 0200 hook was run twice in
  a sandbox on macOS with `dash`, Debian's real default file and a stub
  `dpkg-divert`: all Debian entries and the Super entry end up in one file,
  and the second run gives the same file.
* Wallpapers: valid XML, colour count, no forbidden elements, rendered at
  960x540 and looked at. Title bars, panel and launcher were drawn as rough
  mock-ups from the real colour values and bitmaps (not real screenshots).

**Still uncertain (needs a real session):** rofi accepting the bare `Super_L`
in `kb-cancel` (reported to work by other users, not seen here); whether
`lxqt-globalkeysd` loads every entry of the merged
`/etc/xdg/lxqt/globalkeyshortcuts.conf`; whether
lxqt-globalkeys' hold on Super blocks Openbox's Super+key shortcuts; whether
`/etc/xdg/lxqt/*.conf` takes priority over `/usr/share/lxqt/*.conf` with the
`XDG_CONFIG_DIRS` order that LightDM and `startlxqt` produce; the clock's
double space surviving in the label; and the real title-bar height.

## Licence

Almond's own files here are under the MIT License (see `LICENSE` in the
repository root). The Almond name and logo, including the small almond mark
on the light wallpaper, are excluded; see `NOTICE`.
