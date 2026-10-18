# AALDM implementation plan

**AALDM — A All Little Distribution Model**: the lightweight Almond Linux edition for older and weaker 64-bit PCs.

Written 2026-10-14. **Nothing in this plan has been built, booted or measured.** It is the plan that must exist before each component is built. When this document and the code disagree, the code is what will be tested, and this document must be fixed.

Status words used in Almond documents: **Planned** · **Implemented (source exists, untested)** · **Tested** · **Released**.

All memory and size figures marked *estimate, not measured* are guesses written down so that measurements can prove them wrong. Where an estimate comes from is stated each time. Real numbers will come only from `tests/measure-memory.sh` with the method in [PERFORMANCE.md](PERFORMANCE.md).

## Contents

0. [Targets and rules](#0-targets-and-rules)
1. [Base system](#1-base-system)
2. [Display server](#2-display-server-x11-now-wayland-later)
3. [Window manager](#3-window-manager-openbox)
4. [Desktop](#4-desktop-lxqt-evaluated-against-the-alternatives)
5. [Display manager](#5-display-manager-lightdm)
6. [Launcher](#6-launcher-almond-launcher-rofi)
7. [File manager](#7-file-manager-pcmanfm-qt-feature-map)
8. [Almond Frame](#8-almond-frame-window-and-widget-theming)
9. [Icons and folder colours](#9-icons-and-folder-colours)
10. [Customisation](#10-customisation)
11. [Accessibility](#11-accessibility)
12. [Web browser on 1 GB RAM](#12-web-browser-on-1-gb-ram)
13. [Audio and network](#13-audio-and-network)
14. [Phases and roadmap](#14-phases-mapped-to-the-roadmap)
15. [Dell OptiPlex 390 notes](#15-dell-optiplex-390-notes)
16. [Open decisions and risks](#16-open-decisions-and-risks)
- [Appendix A — package verification](#appendix-a--package-verification-debian-13-trixie)
- [Appendix B — other packages checked](#appendix-b--other-packages-checked)
- [Appendix C — sources](#appendix-c--sources)

## Summary

| Component | Provisional choice (owner-approved for evaluation) | Status |
|---|---|---|
| Base | Debian 13 "trixie", live-build, `main non-free-firmware`, no Recommends | Implemented (source exists, untested) |
| Display server | X11 (Xorg, modesetting driver, no compositor) | Implemented (source exists, untested) |
| Window manager | Openbox, started through `almond-openbox` | Implemented (source exists, untested) |
| Desktop | LXQt 2.1 (explicit minimal package set) | Implemented (source exists, untested) |
| Display manager | LightDM + lightdm-gtk-greeter | Implemented (source exists, untested) |
| Desktop defaults | LXQt, Openbox, PCManFM-Qt and GTK settings, global shortcuts (`desktop/defaults/`, `desktop/lxqt/`, `desktop/gtk/`, 0200 hook) | Implemented (source exists, untested) |
| Launcher | Almond Launcher (rofi) | Implemented (source exists, untested): assets in `desktop/launcher/`, staged by the build |
| File manager | PCManFM-Qt, configured | Implemented (source exists, untested): defaults file (volumes, thumbnails, desktop); the rest of section 7's configuration Planned |
| Almond Frame | Openbox themes + Qt palette + LXQt QSS | Implemented (source exists, untested): staged by the build |
| Icons | Almond Pure + folder-colour variants | Implemented (source exists, untested): staged by the build |
| Customisation | Existing LXQt/Openbox tools; "Almond Personalize" later | Planned |
| Accessibility | Keyboard, high contrast, text scaling, no motion; Orca optional | Planned |
| Browser | Firefox ESR, with honest 1 GB limits | Implemented (source exists, untested) |

The image's package list is [`config/package-lists/aaldm.list.chroot`](../config/package-lists/aaldm.list.chroot). Its desktop defaults come from the [`0200-almond-desktop`](../config/hooks/live/0200-almond-desktop.hook.chroot) hook and the assets that [`scripts/build.sh`](../scripts/build.sh) stages.

---

## 0. Targets and rules

Targets, **not guarantees**:

- idle RAM under **300 MB** "used" (MemTotal − MemAvailable), 120 s after login;
- usable on **1 GB RAM** where feasible;
- minimal idle CPU, low GPU needs.

Rules that follow from "performance is the top priority":

- No compositing requirement, no blur, no transparency, no animations, no gradients. Flat graphics only.
- No resident daemon unless it is essential. Every resident process has a line in the budget ([PERFORMANCE.md](PERFORMANCE.md)).
- Tools that are only needed sometimes (settings, launcher, file manager windows) cost **0 MB** when closed.
- No package enters the image as an unnoticed Recommends: the build uses `--apt-recommends false` and every package is named.

---

## 1. Base system

**Approach**

- Debian 13 "trixie" (current Debian stable), stock Debian kernel (`linux-image-amd64` through `--linux-flavours`), systemd, APT. No Almond package repository yet.
- Built with Debian's live-build (trixie version `1:20250505+deb13u1`) as a live ISO. `auto/config` takes `ALMOND_EDITION=aaldm` (the only edition defined) and `ALMOND_ARCH=amd64` (default) or `arm64` (development VMs on Apple Silicon Macs).
- amd64: `--bootloaders 'syslinux,grub-efi'` and `--binary-images iso-hybrid`. Syslinux (isolinux) boots legacy-BIOS PCs, GRUB boots UEFI PCs, and the hybrid image boots from a USB stick as well as from optical media. arm64: GRUB EFI only.
- `--apt-recommends false`. Debian packages recommend many extras that are wrong for AALDM: ModemManager (a resident daemon), Debian's artwork (`desktop-base`), the 187 MB Papirus icon theme, screen savers. The cost is that everything a feature needs must be listed by name. Recommends that AALDM needs are listed on purpose and commented in the list: `user-setup` (without it live-config creates no live user), `qt6-svg-plugins` (Qt cannot draw the SVG icons of Almond Pure without it), `libgl1-mesa-dri` (X acceleration), `wpasupplicant` (Wi-Fi), `libavcodec61` (Firefox video).
- Security: `--security true --updates true --apt-secure true` (unchanged). AppArmor is installed. nftables is installed, but no ruleset is configured yet.
- `systemd-timesyncd`: old PCs often have a flat CMOS battery, and a wrong clock breaks HTTPS and APT signature checks. Cost: one small daemon.
- `systemd-zram-generator`: compressed swap in RAM, the only swap a live session can have. It is a boot-time generator, not a daemon. Debian's default config (`/usr/lib/systemd/zram-generator.conf`) creates `zram0` at half of RAM, at most 4 GB, with the kernel's default compressor.
- CPU microcode (`intel-microcode`, `amd64-microcode`, amd64 only through a live-build `#if ARCHITECTURE amd64` block): security fixes for old CPUs such as the OptiPlex 390's Sandy Bridge. Loaded early from the initramfs; no resident cost.

**Archive areas: `main non-free-firmware`**

- Why: real PCs need firmware for many network, Wi-Fi and graphics chips. Debian decided in 2022 (General Resolution 2022/vote_003) to include non-free firmware in its official installation and live images, and since Debian 12 it lives in its own archive area, `non-free-firmware`. Almond follows the same policy. The rest of `non-free` stays off.
- Which firmware: by default only the packages named in the list (`--firmware-chroot false`): `firmware-linux-free`, `firmware-misc-nonfree` (includes the `tigon/` files for Broadcom `tg3` network chips) and `firmware-realtek` (`rtl_nic/` for the Realtek NICs common in older PCs). Live-build's default (`--firmware-chroot true`) would add *every* firmware package of the archive (Intel Wi-Fi alone is about 114 MB installed). `ALMOND_FIRMWARE=all` turns that default back on for diagnosing unknown hardware.
- Licence obligations: firmware is binary-only and keeps its own licence. Each package's terms are in `/usr/share/doc/<package>/copyright` inside the image, and they must stay there. Almond's MIT licence does not cover firmware (see [NOTICE](../NOTICE)). Source code for firmware does not exist publicly, so release notes must say that the ISO contains non-free firmware and list those packages (from `package-manifest.txt`). Before a public release, the firmware licences must be read for redistribution limits.

**Debian packages**: see the list sections "Live system", "Base services" and "Firmware" ([appendix A](#appendix-a--package-verification-debian-13-trixie)).

**Dependencies**: a native Debian 13 build host of the same architecture (`scripts/build.sh` refuses anything else). Live-build installs the bootloader tools (syslinux, isolinux, GRUB EFI, xorriso) inside its own chroot during the build.

**Resource estimate** (*estimate, not measured*): kernel, systemd, journald, udevd, D-Bus, logind, NetworkManager, wpa_supplicant, polkitd, timesyncd and cron together about **90–130 MB** "used" before the desktop starts. Source: the author's general experience with minimal Debian systems; no Almond measurement and no benchmark. ISO size: no useful estimate yet. Debian's own desktop live ISOs are larger because they add the installer, LibreOffice and every firmware package, so AALDM should come out smaller; the first build gives the real number.

**Testing requirements**

- `lb config` and `lb build` finish on a Debian 13 amd64 host; keep `configure.log`, `build.log`, `package-manifest.txt`, `SHA256SUMS`.
- The manifest contains no `modemmanager`, `desktop-base`, `papirus-icon-theme`, `xscreensaver`, `plymouth`, `orca`.
- Boots in BIOS mode and UEFI mode (VM first, then the OptiPlex 390).
- `cat /etc/os-release` shows Almond 0.1 "Marcona" AALDM; `swapon --show` shows `zram0`; `timedatectl` shows NTP synchronised once online.

---

## 2. Display server: X11 now, Wayland later

**Decision**: X11 (Xorg 21.1 from trixie) with the **modesetting** driver that is built into `xserver-xorg-core`, and **no compositor**.

| | X11 + Openbox (chosen) | Wayland (labwc, wayfire, KWin) |
|---|---|---|
| Compositing | None needed: windows draw directly | Always composited by design (the compositor draws every frame) |
| Old GPUs | Works with modesetting + glamor, or unaccelerated (shadow framebuffer) if GL is missing | Needs GLES2 for good speed; wlroots has a software (pixman) renderer, but it is slower |
| LXQt 2.1 in Debian 13 | Full session | LXQt's Wayland session package (`lxqt-wayland-session`) is **not in trixie** (madison, 2026-10-14) |
| Launcher | rofi 1.7.5 (X11 only in trixie; `rofi-wayland` not packaged) | needs rofi ≥ 2.0, fuzzel or wofi |
| Security | Any X client can read keystrokes and the screen of others | Clients are isolated |
| Future | Xorg is in maintenance mode upstream | Where desktop Linux is going |

**Old GPU compatibility**: the OptiPlex 390 has Intel HD Graphics (Sandy Bridge, Gen6). The kernel's `i915` driver supports it with KMS, and Mesa's `crocus` driver provides OpenGL for Gen4–Gen7 Intel GPUs, so glamor acceleration should work. The legacy `xserver-xorg-video-intel` driver is not installed: upstream has had no release since 2014 (Debian ships a 2021 git snapshot), and modesetting is Debian's default. It stays a fallback to test if modesetting shows tearing or slow 2D on this GPU. No i915 firmware is needed: Debian's `firmware-intel-graphics` starts at Skylake (checked in its file list).

**Future Wayland path (Planned, not before Debian ships it)**: LXQt 2.x supports Wayland compositors; labwc is the closest to Openbox and reads Openbox `themerc` themes, so the Almond Openbox themes can carry over. Needed first: `lxqt-wayland-session` in Debian, a Wayland launcher (rofi ≥ 2.0 or fuzzel), and measurements on old GPUs, because Wayland always composites.

**Debian packages**: `xserver-xorg-core`, `xserver-xorg-input-libinput`, `libgl1-mesa-dri`, `xauth`, `x11-xserver-utils`. Not `xinit` (LightDM starts X).

**Resource estimate** (*estimate, not measured*): Xorg with glamor **30–70 MB PSS**. Source: author's estimate; Xorg's own size is small, but loading Mesa (and the LLVM library it links) maps a lot. Without GL it would be smaller and slower.

**Testing requirements**: `grep -E 'modeset|glamor' /var/log/Xorg.0.log` (or the journal) shows modesetting with glamor on the OptiPlex 390; scrolling in Firefox and moving windows without visible tearing; `xrandr` lists the monitor's native mode; X still starts in a VM with a virtual GPU (VirtualBox VMSVGA, QEMU std/virtio).

---

## 3. Window manager: Openbox

**Approach**: Openbox 3.6.1, no compositing, no animations. LXQt 2.1 starts the program named in `/etc/xdg/lxqt/session.conf` (`window_manager=`) *without arguments*, so the desktop assets include `almond-openbox` (`desktop/defaults/usr/bin/`), a wrapper that copies `/etc/xdg/openbox/lxqt-rc.xml` to `~/.config/openbox/lxqt-rc.xml` on first login and starts `openbox --config-file` with it. `desktop/defaults` provides `/etc/xdg/lxqt/session.conf` with `window_manager=almond-openbox`; the 0200 hook only writes that key itself when the file is missing (then `almond-openbox` if the wrapper exists, else `openbox`), and it sets the `x-window-manager` alternative to Openbox. Openbox draws only the window frame; it cannot theme what is inside a window (see section 8).

**Debian packages**: `openbox`, `obconf-qt` (settings, 0 resident). Openbox depends on `python3` (for its XDG autostart helper), which is therefore in the image anyway.

**Resource estimate** (*estimate, not measured*): **5–10 MB PSS**. Source: author's estimate; a 2016 LXDE-project blog benchmark (Debian stable in a 512 MB VirtualBox VM, Qt 5-era LXQt) reportedly measured about 58 MB for a whole plain-Openbox system and 95 MB with LXQt. That figure was found through a search summary and the page could not be re-opened on 2026-10-14 (TLS certificate error), so treat it as a weak hint only.

**Testing requirements**: `pgrep -a openbox` shows `--config-file …/lxqt-rc.xml`; minimise/maximise without animation; Alt+Tab; window frame uses an Almond Pure theme.

---

## 4. Desktop: LXQt evaluated against the alternatives

| Option | Strengths | Weaknesses for AALDM | Verdict |
|---|---|---|---|
| **LXQt 2.1 + Openbox** | Complete desktop (panel, settings, power, polkit agent, notifications); Qt 6 shared by all its parts; works with Openbox; QSS themes and palettes make Almond Frame possible; a Wayland path exists upstream | Qt 6 itself is not small; each LXQt part is its own process; some parts (lock screen, Wayland session) missing in Debian 13 | **Keep** (provisional choice, no strong reason found to change) |
| Xfce 4.20 | Mature, polished, good settings, Debian's former default light desktop; the earlier Almond draft used it | GTK 3 throughout; `xfwm4` has a built-in compositor (it can be switched off); often reported as somewhat heavier than LXQt (unverified reports: measure both before claiming anything); it is the Mint Xfce baseline AALDM wants to beat, so "the same desktop" gives no edge | Not chosen; remains the fallback if LXQt fails tests |
| Openbox + tint2 (+ pcmanfm-qt) | Lowest memory; few processes | No settings centre, no power/polkit agent/notifications without assembling them; every missing piece becomes Almond's own maintenance | Not chosen: too much custom glue for a small team |
| LXDE (GTK) | Very light | Development moved to LXQt; GTK 2 heritage | Not chosen |
| MATE, Cinnamon | Complete | Heavier | Not chosen |
| IceWM, JWM, Fluxbox | Very light, one process | Little integration; theming far from the mockups | Not chosen |

**Approach**: an explicit LXQt package set instead of `lxqt-core`, which would pull `lxqt-runner` (replaced by the launcher). Also not installed: `lxqt-admin`, `lxqt-about`, Debian's LXQt branding, `xdg-desktop-portal-lxqt`, a screen saver. Debian's `/usr/share/lxqt/lxqt.conf` names the `breeze` icon theme, which AALDM does not install, so the 0200 hook writes `/etc/xdg/lxqt/lxqt.conf` with `icon_theme=Almond-Pure` unless `desktop/defaults` provides that file.

**Debian packages**: `lxqt-session`, `lxqt-panel`, `lxqt-config`, `lxqt-globalkeys`, `lxqt-notificationd`, `lxqt-policykit`, `lxqt-powermanagement`, `lxqt-qtplugin`, `lxqt-sudo`, `lxqt-system-theme`, `lxqt-menu-data`, `liblxqt-backlight-helper`, `qt6-svg-plugins`, `qt6-image-formats-plugins`; desktop via `pcmanfm-qt --desktop`; `nm-tray`. Dependencies include `lxqt-themes` (26 MB installed: themes and wallpapers) and `upower` (D-Bus activated, needed by `lxqt-powermanagement`).

**Resource estimate** (*estimate, not measured*, PSS; source: author's estimate, Qt 6 libraries shared between the LXQt processes):

| Part | Estimate |
|---|---|
| lxqt-session, lxqt-globalkeysd, lxqt-notificationd, lxqt-policykit-agent, lxqt-powermanagement | 30–60 MB together |
| lxqt-panel | 20–35 MB |
| pcmanfm-qt --desktop | 20–35 MB (a full-HD wallpaper alone is about 8 MB decoded; a flat colour costs almost nothing) |
| nm-tray | 8–15 MB |

`lxqt-powermanagement` on a desktop PC without battery is a candidate to switch off in LXQt Session Settings (0 MB then); it stays on by default because AALDM also targets old laptops.

**Known gap**: no screen locker is installed (`xscreensaver` and `light-locker` are resident). The live session has no password, so this is acceptable for 0.1; installed releases need a decision (candidate: `i3lock`, no daemon).

**Testing requirements**: `echo $XDG_CURRENT_DESKTOP` gives `LXQt`; panel, menu, notifications (`notify-send` comes from `libnotify-bin`, which is not in the image: install it for this test), polkit prompt (mounting a USB stick), log out / reboot / shut down from the Leave dialog; no window-manager chooser dialog appears at first login.

---

## 5. Display manager: LightDM

| Option | Notes | Verdict |
|---|---|---|
| **LightDM + lightdm-gtk-greeter** | Small daemon; the GTK 3 greeter exits after login; config by drop-in files; supports themes, background colour, a11y menu | **Keep** |
| SDDM | Debian's LXQt task default; Qt Quick greeter needs OpenGL or software rendering, heavier on old GPUs | Not chosen |
| slick-greeter (LightDM) | Nicer look, Python settings tool, background effects | Not chosen |
| LXDM, SLiM | Light, but little maintained | Not chosen |
| nodm | Autologin only | Not chosen |
| greetd + a text greeter | Very light; different look; separate greeter packaging | Not chosen |

**Approach** (0200 hook): `/etc/lightdm/lightdm.conf.d/50-almond.conf` sets `user-session=lxqt` and `greeter-session=lightdm-gtk-greeter`. live-config adds autologin for the live user to `/etc/lightdm/lightdm.conf`. `/etc/lightdm/lightdm-gtk-greeter.conf.d/50-almond.conf` gives the greeter the Almond look: background = the first Almond wallpaper found (dark preferred), else flat Dark Brown `#2B2118`; GTK theme `Adwaita-dark` (from `gnome-themes-extra-data`); icon theme Almond Pure; font Atkinson Hyperlegible; `transition-type=none`; `at-spi-enabled=false`. Greeter files load in this order (lightdm-gtk-greeter 2.0.9 source): `/usr/share/lightdm/lightdm-gtk-greeter.conf.d/`, `/etc/xdg/lightdm/lightdm-gtk-greeter.conf.d/`, `/etc/lightdm/lightdm-gtk-greeter.conf.d/`, each followed by its `lightdm-gtk-greeter.conf`; later files win.

**Debian packages**: `lightdm`, `lightdm-gtk-greeter`, `gnome-themes-extra-data`.

**Resource estimate** (*estimate, not measured*): LightDM daemon and session helper **3–6 MB PSS** after login; the greeter (about 20–40 MB) is gone after login. Source: author's estimate.

**Testing requirements**: live boot reaches the LXQt desktop with autologin; boot with `live-config.noautologin` shows the Almond greeter (dark, no transition); the session menu lists LXQt; `ps` after login shows no `lightdm-gtk-greeter`.

---

## 6. Launcher: Almond Launcher (rofi)

**Approach**: the launcher assets (`desktop/launcher/`: the `almond-launch` script, its helpers `almond-launch-power` and `almond-launch-recent`, `*.rasi` themes, `almond-launch.desktop`) come from a separate workstream. `scripts/build.sh` stages them to `/usr/bin/almond-launch` (0755), `/usr/libexec/almond/` (helpers, 0755), `/usr/share/almond/launcher/` and `/usr/share/applications/`. rofi starts on demand and exits when closed, so its idle cost is **0 MB**. The Super key is bound through LXQt global shortcuts (lone `Super_L`). Debian 13's `lxqt-globalkeys` 2.1.0-2 installs `/etc/xdg/lxqt/globalkeyshortcuts.conf` as a *directory* holding Debian's default shortcuts (its file list and `debian/lxqt-globalkeys.install`), which `lxqt-globalkeysd` cannot read and which a staged file would collide with. So `desktop/lxqt/globalkeyshortcuts.conf` is staged to `/usr/share/almond/lxqt/`, and the 0200 hook writes a plain file at `/etc/xdg/lxqt/globalkeyshortcuts.conf`: Debian's defaults (Ctrl+Alt+T, Print, brightness and other XF86 keys; Debian's Ctrl+Alt+L runs `xdg-screensaver lock`, which does nothing until a screen locker is installed) followed by the Super entry, keeping Debian's originals in `/usr/share/almond/lxqt/debian-defaults/`. Known risk (untested): on an installed system an `lxqt-globalkeys` update that still ships the directory may fail to unpack over that file. This must be checked in the first boot test. Alt+F2 is free: `lxqt-runner`, which registers it, is not installed, and Debian's default shortcut file does not bind it. rofi's mode labels are passed on its command line, its window has square corners (no compositor), and its pid file lives in `$XDG_RUNTIME_DIR` (fallback `~/.cache`). The launcher's "Lock" entry needs a screen locker, which 0.1 does not install (see section 4).

**Debian packages**: `rofi` (1.7.5, X11 only).

**Resource estimate** (*estimate, not measured*): 0 MB closed; **10–20 MB** while open. Source: author's estimate (rofi is a single small C program using cairo/pango).

**Testing requirements**: Super opens the launcher within about half a second on the OptiPlex 390; typing filters applications; Esc closes it; `pgrep rofi` finds nothing afterwards.

---

## 7. File manager: PCManFM-Qt feature map

**Evaluation**: a custom Almond file manager is not justified for 0.1. PCManFM-Qt 2.1 (with libfm-qt) already is the LXQt file manager and desktop, follows the Qt palette, LXQt theme and icon theme (so Almond Pure applies), and has no indexer. Missing features should be contributed upstream to PCManFM-Qt rather than written as a new program.

| Required feature | PCManFM-Qt 2.1 | Needs |
|---|---|---|
| Grid / list / details views | Icon, Thumbnail, Compact and Detailed List views (View menu) | Out of the box; default view = configuration |
| Search | "Find Files" dialog (recursive, by name/content/type/size/date) and a filter bar for the current folder; no index | Out of the box |
| File operations | Copy, move, rename, trash, delete, bulk rename, progress dialog, drag and drop, paste | Out of the box |
| External devices | Mount, unmount and eject in the side pane through GIO: needs `gvfs` (`gvfs-udisks2-volume-monitor`) and `udisks2`; authorisation via polkit (`polkitd` + `lxqt-policykit`). NTFS needs `ntfs-3g`. Phones and media players over MTP: `gvfs-mtp-volume-monitor` | Packages listed. Configured in `desktop/defaults/etc/xdg/pcmanfm-qt/lxqt/settings.conf`: nothing is mounted at login (`MountOnStartup=false`), no autorun dialog (`AutoRun=false`), sticks plugged in during the session are mounted (`MountRemovable=true`); internal disks of test PCs must stay unmounted (section 15) |
| Network locations | Typing `smb://`, `sftp://`, `ftp://`, `dav://` in the location bar works through `gvfs-backends`; `gvfs-fuse` lets Qt programs open those files | Packages listed. Browsing the "Network" place (discovering Windows/Samba machines) needs `wsdd` or Avahi, both resident daemons, not installed: configuration/opt-in. A "connect to server" dialog: check in testing; may need new development |
| Properties | Properties dialog (size, permissions, owner, open-with) | Out of the box |
| Hidden files | Ctrl+H toggles them | Out of the box |
| Places | Side pane: Home, Desktop, Trash, Computer, Applications, Network, Devices, Bookmarks | Out of the box; which entries appear = configuration |
| Recent | GIO `recent:///` works through `gvfs-backends` (gvfsd-recent); not a default side-pane entry | Configuration: pre-seed a bookmark for `recent:///` (bookmarks file in `/etc/skel`); a first-class "Recent" entry = new development upstream |
| Browse (Computer, filesystem root) | "Computer" and "/" in the side pane and location bar | Out of the box |
| Preview panel (off by default) | Not available (only thumbnails and tooltips) | New development (upstream contribution); stays off by default anyway |
| No indexing | No indexer exists | Out of the box |
| Thumbnails | Built in for images; video thumbnails need `ffmpegthumbnailer` (not installed) | Configuration: size limit, local files only, to keep CPU low |

**Debian packages**: `pcmanfm-qt`, `gvfs`, `gvfs-backends`, `gvfs-fuse`, `udisks2`, `ntfs-3g`, `exfatprogs`, `dosfstools`, `eject`, `lxqt-archiver`, `zip`, `unzip`.

**Volume monitors**: GIO starts every volume monitor listed in `/usr/share/gvfs/remote-volume-monitors/` as its own resident process as soon as a program (here `pcmanfm-qt --desktop`) asks for the list of drives. `gvfs-backends` is kept for SMB, SFTP, FTP, WebDAV, MTP, trash and recent, but the 0200 hook disables three of its monitors with a local `dpkg-divert` (renamed to `*.monitor.almond-disabled`, only if present; package upgrades keep them disabled): `goa.monitor` (GNOME Online Accounts, not installed), `afc.monitor` (Apple iPhone/iPad) and `gphoto2.monitor` (cameras in PTP mode, which are then no longer listed). Kept: `udisks2.monitor` (from `gvfs-daemons`: disks and USB sticks) and `mtp.monitor` (phones and media players). File names checked in the trixie file lists of `gvfs-backends` and `gvfs-daemons` 1.57.2-2+deb13u1; gvfs only reads files ending in `.monitor` (`common/gvfsmonitorimpl.c`). Undo one: `sudo dpkg-divert --local --rename --remove /usr/share/gvfs/remote-volume-monitors/afc.monitor`.

**Resource estimate** (*estimate, not measured*): a file manager window lives in the same process as the desktop (`pcmanfm-qt --desktop`), so it adds about **10–25 MB** while open and 0 MB when closed. gvfsd and its helpers, the udisks2 and MTP volume monitors and `udisksd`: **10–20 MB**. Source: author's estimate.

**Testing requirements**: each row of the table above checked in the live session and marked Tested / not working; a USB stick (FAT, exFAT, NTFS) mounts with a polkit prompt or none for the active local user; an SFTP location opens; Ctrl+H; Find Files; the internal disk of a test PC is **not** mounted (check `findmnt` and `lsblk -f` without opening the disk); `pgrep -a -f volume-monitor` lists only the udisks2 and MTP monitors.

---

## 8. Almond Frame: window and widget theming

**Approach**: four layers, all flat (no gradients, no transparency):

1. **Window frames**: Openbox themes (`desktop/openbox/Almond-Pure-Dark`, `-Light`, `-Ocean`), staged to `/usr/share/themes/`. The Openbox config chooses one.
2. **Qt widgets** (all LXQt programs, PCManFM-Qt, qterminal, FeatherPad, qpdfview): Qt's Fusion style with an Almond **Qt palette** (`/usr/share/lxqt/palettes/`, from `desktop/lxqt/palettes/`).
3. **LXQt components** (panel, menu, notifications, desktop): an Almond **LXQt theme** of QSS files (`/usr/share/lxqt/themes/`, from `desktop/lxqt/themes/`).
4. GTK programs (Firefox, the greeter) only get settings (`/etc/gtk-3.0/settings.ini` from `desktop/gtk/`) and Adwaita / Adwaita-dark. A full Almond GTK theme is not planned for 0.1.

**Integrated headers** (title bar merged with the toolbar, as in the mockups) are only possible where a program draws its own header (GTK client-side decorations). Openbox can theme the frame it draws, but it **cannot theme toolbars inside an application window**; Qt programs keep a separate title bar and toolbar. So the mockups' integrated headers are a deliberate deviation for most programs.

**Resource estimate** (*estimate, not measured*): 0 MB extra; themes are files read at start-up. A heavy QSS can slow start-up slightly; measure panel start time.

**Testing requirements**: screenshots of panel, menu, file manager, terminal, a dialog and Firefox against mockup image 1; contrast check of text colours (WCAG AA) for every palette; no transparency (`xprop` / visual check).

---

## 9. Icons and folder colours

**Approach**: the **Almond Pure** icon theme (`desktop/icons/Almond-Pure/`, freedesktop Icon Theme and Naming specifications, `Inherits=Adwaita,hicolor`) and its folder-colour **variants** (`Almond-Pure-Blue`, `-Gray`, `-Green`, `-Orange`, `-Plum`, `-Red` at the time of writing) are staged to `/usr/share/icons/`. A colour variant is chosen like any icon theme (LXQt Appearance → Icon Theme). Brand icons of third-party programs (Firefox and others) are not redrawn; those programs keep their own icons. `adwaita-icon-theme` and `adwaita-icon-theme-legacy` provide fallbacks. The 0200 hook rebuilds icon caches for Almond Pure, hicolor and Adwaita, because live-build's own `9000-remove-gnome-icon-cache` hook deletes them (for reproducibility); without a cache every program scans the icon folders itself. Trade-off: caches make the image slightly less reproducible.

**Debian packages**: `adwaita-icon-theme`, `adwaita-icon-theme-legacy`, `hicolor-icon-theme`, `gtk-update-icon-cache`, `librsvg2-common` (SVG for GTK), `qt6-svg-plugins` (SVG for Qt).

**Resource estimate** (*estimate, not measured*): SVG icons are rendered on demand and cached per process; about 1–3 MB per program. Source: author's estimate.

**Testing requirements**: icons appear in panel, menu and file manager at 16, 24, 48 px; no missing-icon placeholders in the first-boot screenshots; switching to a folder-colour variant changes folder icons only.

---

## 10. Customisation

**Approach**: use what exists, write nothing new for 0.1.

- LXQt Appearance (`lxqt-config-appearance`): widget style, palette, icon theme, LXQt theme, fonts, GTK style.
- Openbox Settings (`obconf-qt`): window frame theme, title layout, fonts.
- Panel settings and desktop preferences (wallpaper, desktop icons).
- LXQt Session Settings: autostart, which LXQt modules run (for example switching off power management on a desktop PC).
- **Almond Personalize** (one Almond app for theme, accent and folder colour): **Planned for later**, only after the default look is tested.

**Resource estimate**: **0 MB resident**; 15–30 MB while a settings window is open (*estimate, not measured*).

**Testing requirements**: change palette, icon variant and Openbox theme, log out and in, confirm they persist in a persistent session (or note that the live session forgets them).

---

## 11. Accessibility

| Area | Plan | Status |
|---|---|---|
| Keyboard navigation | Qt and GTK widgets are keyboard-navigable; Openbox keys (Alt+Tab, Alt+F4); LXQt global shortcuts; the launcher is keyboard-first; the greeter works without a mouse | Planned |
| Screen reader | **Orca is available in Debian 13 (`orca` 48.1) but not installed by default.** Cost: it pulls `at-spi2-core`, `speech-dispatcher`, `espeak-ng`, Python GTK bindings and GStreamer (orca 15.8 MB + speech-dispatcher 28.5 MB installed, plus dependencies), and once `at-spi2-core` is installed every GTK and Qt program starts the accessibility bus (a few MB resident in every session). Running Orca itself: about 60–120 MB (*estimate, not measured*). Opt-in now: `sudo apt install orca` (needs network in the live session). Later: a separate accessibility image or a boot option, decided after measurement | Planned |
| High contrast | An Almond high-contrast Qt palette and Openbox theme (to be designed); GTK's built-in HighContrast theme for GTK programs; the greeter's a11y menu offers high contrast and large font | Planned |
| Text scaling | LXQt Appearance: font size and DPI; Qt scaling via session environment; Firefox zoom | Planned |
| Reduced motion | AALDM has no animations by design: Openbox `animateIconify` off, greeter transitions off, `gtk-enable-animations=false` (GTK settings), Firefox `ui.prefersReducedMotion` (Planned) | Implemented (source exists, untested), except Firefox: Planned |
| Boot sound | Live-build's GRUB menu plays a short beep when it appears (a Debian accessibility aid for blind users); kept | Implemented (source exists, untested) — live-build's default |

**Testing requirements**: one complete session (log in, open the launcher, start the file manager, copy a file, shut down) using only the keyboard; with Orca installed, the greeter and the panel are spoken; contrast measurements for each palette.

---

## 12. Web browser on 1 GB RAM

**Honest statement**: a modern browser is the heaviest program on AALDM. Firefox ESR with one or two simple tabs is likely to use **250–450 MB** (*estimate, not measured*; source: author's experience with current Firefox releases), and heavy sites far more. On a 1 GB PC that leaves little room; zram swap helps, but browsing several heavy sites at once on 1 GB will be slow. "Runs on 1 GB" for AALDM means the desktop and light browsing, not many tabs.

| Option | Engine | Security support in Debian 13 | Memory | Verdict |
|---|---|---|---|---|
| **Firefox ESR** | Gecko | Yes (Debian rebuilds new ESR releases for stable, so the major version changes) | High | **Default** |
| Chromium | Blink | Yes | High, usually at least Firefox's | Not default |
| Falkon, qutebrowser, Konqueror | QtWebEngine | **No**: Debian 13 release notes say QtWebEngine is not covered by security support | Medium | Rejected |
| Epiphany (GNOME Web), luakit, surf, vimb | WebKitGTK | Yes (WebKitGTK is covered) | Medium; Epiphany pulls GTK 4 and libadwaita | Candidate "light browser" for later testing |
| NetSurf, Dillo, Links2 | Own small engines | Not listed among supported browser engines; little or no JavaScript | Very low | Not suitable as the main browser; most modern sites break |

The image built on 2026-10-17 contained `firefox-esr` 153.5.0esr-1~deb13u1 (build manifest, [test results](../tests/results/2026-10-17-vm/RESULTS.md)); the version moves with Debian security updates.

**Approach for 0.1**: Firefox ESR plus things that make it cheaper without a second browser: zram swap; `libavcodec61` so H.264 video can be used (H.264 decodes far more cheaply on old CPUs than VP9 or AV1); local PDFs and videos open in `qpdfview` and `mpv`, not in Firefox. Planned: a Firefox preferences file (`/etc/firefox-esr/`) with fewer content processes, reduced motion and no smooth scrolling, after measuring the effect.

**Testing requirements**: on the OptiPlex 390 and in a 1 GB VM: open a news site and a video site; record `measure-memory.sh` output with Firefox open; note whether the system starts swapping heavily (`vmstat 5`).

---

## 13. Audio and network

**Audio: PulseAudio, not PipeWire, for 0.1.** PipeWire is Debian's direction, but on X11 its video and screen-capture roles are not needed, and it runs three processes (`pipewire`, `pipewire-pulse`, `wireplumber` with a Lua session manager) where PulseAudio runs one. `pavucontrol-qt`, the LXQt panel and Firefox all work with either through the PulseAudio API. Swap rule: measure both on the same machine; if PipeWire costs no more than PulseAudio (PSS), or PulseAudio misbehaves, switch. `rtkit` is not installed (PulseAudio works without realtime scheduling). No Bluetooth stack by default (`bluez` is a daemon); add it when a target PC needs it. Estimate: PulseAudio **6–12 MB PSS** (*estimate, not measured*).

**Network**: NetworkManager with `wpasupplicant` and `wireless-regdb`, tray icon `nm-tray` (Qt). Not installed: ModemManager, `dnsmasq-base` (only for hotspot/shared connections), `ppp`. Estimate: NetworkManager + wpa_supplicant **15–25 MB PSS** (*estimate, not measured*).

---

## 14. Phases mapped to the roadmap

These are the owner's ten AALDM phases, in the owner's order and wording. **No phase is complete**: nothing has been built, booted or measured, so no phase has its evidence yet. Phase 1 is version 0.1 "Marcona"; the versions given for phases 2–10 are a **provisional** mapping onto [ROADMAP.md](ROADMAP.md), to be confirmed by the owner.

| Phase | Owner's phase | Roadmap version (2–10 provisional) | Work in this repository (2026-10-14) | Status | Evidence required |
|---|---|---|---|---|---|
| 1 | Bootable Debian-based Almond AALDM ISO | **0.1 "Marcona"** | `auto/config`, `config/package-lists/aaldm.list.chroot`, hooks `0100`/`0200`, `scripts/build.sh` (sections 1–7, 12, 13) | Implemented (source exists, untested); not complete | build log, `package-manifest.txt`, ISO hash, BIOS and UEFI boot in a VM, memory reports ([PERFORMANCE.md](PERFORMANCE.md)) |
| 2 | Apply official Almond branding | 0.2 "Largueta" | identity hook `0100`, logo (`branding/logo/`), boot menus and Plymouth theme (`branding/boot/`), wallpapers; identity as a Debian package: Planned | Implemented (source exists, untested); not complete | photos/screenshots of the BIOS and UEFI boot menus, greeter and desktop |
| 3 | Integrate Almond Icons and Almond Fold | 0.2 "Largueta" | Almond Pure icon theme and its folder icons ("Almond Fold", `tools/make-folders.py`) with colour variants (`desktop/icons/`, section 9), staged by the build | Implemented (source exists, untested); not complete | icon coverage screenshots at 16, 24 and 48 px |
| 4 | Apply Almond Pure window themes | 0.2 "Largueta" | Almond Frame: Openbox themes, Qt palettes, LXQt themes, GTK settings (section 8) | Implemented (source exists, untested); not complete | screenshots against mockup image 1, contrast review |
| 5 | Implement the approved launcher prototype | 0.3 "Valencia" | Almond Launcher on rofi (`desktop/launcher/`, section 6) and its Super key | Implemented (source exists, untested); not complete | timing and keyboard test on the test PCs |
| 6 | Integrate Almond Files | 0.3 "Valencia" | PCManFM-Qt defaults (`desktop/defaults/etc/xdg/pcmanfm-qt/`) and the feature map in section 7 | Implemented (source exists, untested) for the defaults; the rest Planned; not complete | the table of section 7 marked Tested row by row |
| 7 | Implement customization options | 0.3 "Valencia" | existing LXQt/Openbox settings tools; Almond Personalize later (section 10) | Planned | settings persist; Personalize specification |
| 8 | Test on low-end hardware | 0.3 "Valencia" → 0.5 | `tests/measure-memory.sh`; acceptance tests in [BUILD.md](BUILD.md) (1 GB and 2 GB VMs, then the OptiPlex 390). The first measurements are already part of 0.1's evidence | Implemented (source exists, untested) for the tools; testing not started | 5-boot memory reports per machine, boot logs, hardware reports |
| 9 | Optimize performance | 0.5 | budgets and method in [PERFORMANCE.md](PERFORMANCE.md); changes follow the measurements | Planned | measured results against every budget line, before and after each change |
| 10 | Prepare a stable preview release | 0.5 (1.0 is the first stable public release after it) | release notes, licences, signing and support process are not started | Planned | see the 0.5 and 1.0 evidence in [ROADMAP.md](ROADMAP.md) |

Accessibility (section 11) has no phase of its own in the owner's list; where it is planned and checked is an open decision (section 16).

---

## 15. Dell OptiPlex 390 notes

**Hardware (to confirm on the machine)**: 2011 Dell business desktop, Intel H61 chipset, 2nd-generation Intel Core / Pentium / Celeron (Sandy Bridge) — all **64-bit**, so Debian 13 amd64 runs on it. Integrated **Intel HD Graphics** (Gen6), kernel driver `i915`, Mesa `crocus`; no GPU firmware needed. Record the exact CPU and RAM with `lscpu` and `free -m`.

**Firmware: BIOS or UEFI?** Not settled. Dell community posts disagree: one describes the 390 as an early UEFI system without Secure Boot, another says it is legacy-BIOS only. The AALDM ISO is therefore **hybrid**: isolinux for legacy BIOS, GRUB for UEFI, both on one USB stick. At power-on press F12 for the one-time boot menu; try the USB entry in each mode that appears and record which ones boot. Secure Boot does not apply if the firmware has no Secure Boot.

**Network card**: the onboard NIC model was **not verified** for this plan. Record `lspci -nnk | grep -A3 -i ethernet` (`pciutils` is in the image). The image carries `firmware-misc-nonfree` (`tigon/` for Broadcom `tg3`) and `firmware-realtek` (`rtl_nic/` for `r8169`). If the NIC does not come up, check `journalctl -k | grep -i firmware`; if a file is missing, rebuild with `ALMOND_FIRMWARE=all` to confirm, then add the specific package to the list.

**Data and authorisation**: treat it as a second-hand PC whose internal disk may still hold someone else's data.

1. **Boot only from USB.** Never open, mount, browse or read the internal disk, even if the file manager lists it under Devices. AALDM's PCManFM-Qt defaults mount nothing at login; confirm with `findmnt` and `lsblk -f` that the internal disk has no mount point. If the PC's owner agrees, disconnect the internal disk's SATA data cable for the first tests; then nothing can touch it.
2. **Wipe (sanitise) the internal disk only with the owner's explicit permission**, with a method suited to the drive type (full overwrite for a hard disk; the drive's secure-erase or discard for an SSD), and write down what was done. Almond's live image contains no tool that does this automatically, and it must stay that way.
3. Never run an installer against that disk until the above is done and someone explicitly decides it.

---

## 16. Open decisions and risks

1. **Phase mapping**: section 14 uses the owner's ten phases; the versions given for phases 2–10 are provisional and need the owner's confirmation, as does where accessibility work belongs.
2. **Screen locker** for installed releases (none in 0.1).
3. **Audio**: PulseAudio vs PipeWire, decided by measurement.
4. **Accessibility image** with Orca and at-spi preinstalled: separate ISO or boot option.
5. **Desktop defaults coordination**: Super-key binding (the merged `/etc/xdg/lxqt/globalkeyshortcuts.conf`, section 6), LXQt theme/palette selection in `/etc/xdg/lxqt/lxqt.conf`, panel layout, volume defaults — these belong to `desktop/defaults` and must be checked together in the first boot.
6. **Global shortcuts and package upgrades**: the 0200 hook replaces a directory that `lxqt-globalkeys` 2.1.0-2 owns with a file. Before installed releases, decide how this survives package upgrades (for example an Almond package that owns the merged file, or a fixed Debian package: forky's 2.4.0-1 installs a plain file).
7. **Firmware coverage** on other old PCs (Intel/Atheros/Broadcom Wi-Fi): stays opt-in (`ALMOND_FIRMWARE=all`) until testing shows which packages are worth their size.
8. **Cross-building** (amd64 ISO on an Apple Silicon Mac): future work; for now an amd64 Debian host is required.
9. **Risk**: the 300 MB target is not proven. The estimates above add up to roughly 225–400 MB for an idle session, so the target is plausible but may fail; measurement decides which parts to cut.
10. **Risk**: building without Recommends may leave out something a feature silently needs. Mitigation: review `package-manifest.txt` and test every feature row in this plan.

---

## Appendix A — package verification (Debian 13 "trixie")

Every package in [`config/package-lists/aaldm.list.chroot`](../config/package-lists/aaldm.list.chroot) was looked up on **2026-10-14** with Debian's read-only archive API, once per architecture:

```sh
curl -s 'https://api.ftp-master.debian.org/madison?package=NAME&s=trixie&a=amd64,all&f=json'
curl -s 'https://api.ftp-master.debian.org/madison?package=NAME&s=trixie&a=arm64,all&f=json'
```

An empty result means "not in trixie" for that architecture. "yes" under amd64/arm64 means a binary exists for that architecture or the package is architecture-independent (`all`). **Versions in both appendix tables are the amd64 (or `all`) versions**, re-queried with `a=amd64,all` on 2026-10-14. Binary rebuilds (`+bN` suffixes) can differ per architecture: for example `lightdm-gtk-greeter` is 2.0.9-1 on amd64 but 2.0.9-1+b2 on arm64, and `qpdfview` is 0.5.0+ds-5+b1 on amd64 but +b2 on arm64; the arm64 development variant's real versions are in its own `package-manifest.txt`. Versions are the trixie (stable) versions at that date; security and point updates change them. Dependencies and Recommends were read from packages.debian.org (trixie) on the same day. **Result: all 87 names exist for amd64; all except the two microcode packages exist for arm64, and those two sit in an `#if ARCHITECTURE amd64` block.**

| Package | trixie version (2026-10-14) | Area | amd64 | arm64 | Why it is in the list |
|---|---|---|---|---|---|
| `live-boot` | 1:20250815~deb13u1 | main | yes | yes | live system boot (initramfs) |
| `live-config` | 11.0.5 | main | yes | yes | live system configuration at boot |
| `live-config-systemd` | 11.0.5 | main | yes | yes | live-config backend for systemd |
| `live-tools` | 1:20240525 | main | yes | yes | live helpers (Recommends of live-boot/live-config) |
| `systemd-sysv` | 257.13-1~deb13u1 | main | yes | yes | init |
| `user-setup` | 1.107 | main | yes | yes | creates the live user (only a Recommends of live-config) |
| `sudo` | 1.9.16p2-3+deb13u2 | main | yes | yes | administrative access for the live user |
| `locales` | 2.41-12+deb13u4 | main | yes | yes | live-config locale setup |
| `keyboard-configuration` | 1.242~deb13u1 | main | yes | yes | keyboard layout |
| `dbus-user-session` | 1.16.2-2 | main | yes | yes | per-user D-Bus session bus |
| `libpam-systemd` | 257.13-1~deb13u1 | main | yes | yes | logind sessions for LightDM/polkit |
| `polkitd` | 126-2 | main | yes | yes | authorisation for mounts, network, power (trixie name; policykit-1 is source-only) |
| `systemd-timesyncd` | 257.13-1~deb13u1 | main | yes | yes | clock sync (flat CMOS batteries on old PCs) |
| `systemd-zram-generator` | 1.2.1-2 | main | yes | yes | compressed swap in RAM for 1 GB PCs; generator, no daemon |
| `apparmor` | 4.1.0-1 | main | yes | yes | mandatory access control profiles |
| `nftables` | 1.1.3-1 | main | yes | yes | firewall tooling (no rules configured yet) |
| `ca-certificates` | 20250419 | main | yes | yes | TLS trust store |
| `firmware-linux-free` | 20241210-2 | main | yes | yes | free firmware |
| `firmware-misc-nonfree` | 20250410-2 | non-free-firmware | yes | yes | tigon/ (Broadcom tg3) and other common firmware |
| `firmware-realtek` | 20250410-2 | non-free-firmware | yes | yes | rtl_nic/ for Realtek NICs |
| `intel-microcode` | 3.20251111.1~deb13u1 | non-free-firmware | yes | NO | CPU security fixes (amd64 only, #if guarded) |
| `amd64-microcode` | 3.20250311.1 | non-free-firmware | yes | NO | CPU security fixes (amd64 only, #if guarded) |
| `xserver-xorg-core` | 2:21.1.16-1.3+deb13u3 | main | yes | yes | X server incl. modesetting driver |
| `xserver-xorg-input-libinput` | 1.5.0-1 | main | yes | yes | keyboard, mouse, touchpad |
| `libgl1-mesa-dri` | 25.0.7-2+deb13u1 | main | yes | yes | Mesa drivers for glamor acceleration (Recommends of xserver-xorg-core) |
| `xauth` | 1:1.1.2-1.1 | main | yes | yes | X authority tool |
| `x11-xserver-utils` | 7.7+11 | main | yes | yes | xrandr, xset (tests, monitor setup) |
| `lightdm` | 1.32.0-6+b2 | main | yes | yes | display manager |
| `lightdm-gtk-greeter` | 2.0.9-1 | main | yes | yes | login screen |
| `gnome-themes-extra-data` | 3.28-4 | main | yes | yes | Adwaita-dark GTK 3 theme for the greeter |
| `openbox` | 3.6.1-12+b2 | main | yes | yes | window manager |
| `obconf-qt` | 0.16.5-1 | main | yes | yes | Openbox settings (0 resident) |
| `lxqt-session` | 2.1.1-1 | main | yes | yes | LXQt session manager |
| `lxqt-panel` | 2.1.4-1 | main | yes | yes | panel |
| `lxqt-config` | 2.1.1-1 | main | yes | yes | settings centre (0 resident) |
| `lxqt-globalkeys` | 2.1.0-2 | main | yes | yes | global shortcuts (Super for the launcher) |
| `lxqt-notificationd` | 2.1.1-1 | main | yes | yes | notifications |
| `lxqt-policykit` | 2.1.0-1 | main | yes | yes | polkit agent |
| `lxqt-powermanagement` | 2.1.0-2 | main | yes | yes | battery, idle, power keys |
| `lxqt-qtplugin` | 2.1.0-1+b1 | main | yes | yes | Qt platform theme for LXQt |
| `lxqt-sudo` | 2.1.0-1 | main | yes | yes | graphical sudo (pcmanfm-qt depends on it) |
| `lxqt-system-theme` | 2.1.0-1 | main | yes | yes | LXQt system theme |
| `lxqt-menu-data` | 2.1.0-1 | main | yes | yes | application menu data |
| `liblxqt-backlight-helper` | 2.1.0-3 | main | yes | yes | laptop backlight helper |
| `qt6-svg-plugins` | 6.8.2-3 | main | yes | yes | Qt SVG icon/image plugin (Almond Pure is SVG) |
| `qt6-image-formats-plugins` | 6.8.2-4 | main | yes | yes | extra image formats for lximage-qt |
| `xdg-user-dirs` | 0.18-2 | main | yes | yes | Desktop/Documents/... folders |
| `xdg-utils` | 1.2.1-2 | main | yes | yes | xdg-open and friends |
| `desktop-file-utils` | 0.28-1 | main | yes | yes | desktop entry database |
| `pcmanfm-qt` | 2.1.0-2 | main | yes | yes | file manager and desktop |
| `qterminal` | 2.1.0-1 | main | yes | yes | terminal |
| `featherpad` | 1.6.1-1 | main | yes | yes | text editor |
| `lximage-qt` | 2.1.1-1 | main | yes | yes | image viewer |
| `lxqt-archiver` | 1.1.0-1 | main | yes | yes | archive manager |
| `unzip` | 6.0-29+deb13u1 | main | yes | yes | zip support for lxqt-archiver |
| `zip` | 3.0-15+deb13u1 | main | yes | yes | zip support for lxqt-archiver |
| `screengrab` | 2.9.0-1 | main | yes | yes | screenshots |
| `qps` | 2.10.0-1 | main | yes | yes | process viewer |
| `qpdfview` | 0.5.0+ds-5+b1 | main | yes | yes | PDF viewer (lighter than Firefox for local PDFs) |
| `mpv` | 0.40.0-3+deb13u1 | main | yes | yes | media player |
| `rofi` | 1.7.5-0.1+b2 | main | yes | yes | Almond Launcher engine |
| `firefox-esr` | 140.15.0esr-1~deb13u1 | main | yes | yes | web browser (the 2026-10-17 build pulled 153.5.0esr-1~deb13u1: [test results](../tests/results/2026-10-17-vm/RESULTS.md)) |
| `libavcodec61` | 7:7.1.5-0+deb13u1 | main | yes | yes | H.264/AAC/MP3 for Firefox and mpv |
| `gvfs` | 1.57.2-2+deb13u1 | main | yes | yes | GIO virtual file systems |
| `gvfs-backends` | 1.57.2-2+deb13u1 | main | yes | yes | SMB, SFTP, FTP, WebDAV, MTP, trash, recent |
| `gvfs-fuse` | 1.57.2-2+deb13u1 | main | yes | yes | network files usable by non-GIO apps |
| `udisks2` | 2.10.1-12.1+deb13u2 | main | yes | yes | external drives |
| `ntfs-3g` | 1:2022.10.3-5+deb13u2 | main | yes | yes | NTFS drives |
| `exfatprogs` | 1.2.9-1+deb13u1 | main | yes | yes | exFAT tools |
| `dosfstools` | 4.2-1.2 | main | yes | yes | FAT tools |
| `eject` | 2.41.5-0+deb13u1 | main | yes | yes | eject media |
| `network-manager` | 1.52.1-1 | main | yes | yes | networking |
| `wpasupplicant` | 2:2.10-24 | main | yes | yes | Wi-Fi (Recommends of network-manager) |
| `wireless-regdb` | 2026.05.30-1~deb13u1 | main | yes | yes | Wi-Fi regulatory data |
| `nm-tray` | 0.5.1-1 | main | yes | yes | network tray (Qt) |
| `pulseaudio` | 17.0+dfsg1-2+b1 | main | yes | yes | sound server |
| `pavucontrol-qt` | 2.1.0-1 | main | yes | yes | volume control (0 resident) |
| `alsa-utils` | 1.2.14-1 | main | yes | yes | mixer defaults, alsamixer |
| `fonts-dejavu-core` | 2.37-8 | main | yes | yes | base fonts (also needed by live-build's splash) |
| `fonts-atkinson-hyperlegible` | 0.0~git20210430.1cb3116-3 | main | yes | yes | legible UI font (OTF) |
| `adwaita-icon-theme` | 48.1-1 | main | yes | yes | fallback icons (Almond Pure inherits Adwaita) |
| `adwaita-icon-theme-legacy` | 46.2-2 | main | yes | yes | full-colour fallbacks for Adwaita |
| `hicolor-icon-theme` | 0.18-2 | main | yes | yes | base icon theme |
| `gtk-update-icon-cache` | 4.18.6+ds-2 | main | yes | yes | icon caches (0200 hook) |
| `librsvg2-common` | 2.60.0+dfsg-1 | main | yes | yes | SVG loader for GTK |
| `pciutils` | 1:3.13.0-2 | main | yes | yes | lspci for hardware reports |
| `usbutils` | 1:018-2 | main | yes | yes | lsusb for hardware reports |

## Appendix B — other packages checked

Alternatives evaluated in this plan, and names from the brief that turned out to be different in trixie (checked the same way, 2026-10-14; amd64 versions).

| Package | trixie version | Area | amd64 | arm64 | Decision |
|---|---|---|---|---|---|
| `xserver-xorg-video-intel` | 2:2.99.917+git20210115-1 | main | yes | NO | Not used: unmaintained upstream DDX; the modesetting driver in xserver-xorg-core is Debian's default. Kept as a test fallback for Sandy Bridge if modesetting misbehaves. |
| `xserver-xorg-video-fbdev` | 1:0.5.0-2 | main | yes | yes | Not used: modesetting also drives simpledrm/efifb; add only if a test PC has no KMS driver. |
| `xserver-xorg-video-vesa` | 1:2.6.0-2 | main | yes | NO | Not used: legacy-BIOS-only fallback (amd64 only). |
| `xinit` | 1.4.2-1 | main | yes | yes | Not used: LightDM starts X. Install for startx debugging. |
| `mesa-utils` | 9.0.0-2+b2 | main | yes | yes | Not used: glxinfo for GPU tests; install when testing. |
| `tint2` | 17.0.1-1.2 | main | yes | yes | Evaluated (Openbox + tint2 desktop option); not chosen. |
| `obconf` | 1:2.0.4+git20150213-3 | main | yes | yes | Not used: GTK Openbox settings; obconf-qt fits LXQt. |
| `lxqt-core` | 33.2 | main | yes | yes | Not used: depends on lxqt-runner and qterminal etc.; the explicit list replaces it. |
| `lxqt` | 33.2 | main | yes | yes | Not used: pulls lxqt-admin, qlipper, Debian branding, an X display manager choice. |
| `task-lxqt-desktop` | 3.81 | main | yes | yes | Not used: depends on SDDM and recommends LibreOffice and more. |
| `lxqt-runner` | 2.1.2-1 | main | yes | yes | Not used: rofi-based Almond Launcher replaces it. |
| `lxqt-admin` | 2.1.0-1 | main | yes | yes | Not in 0.1: user/time admin tools; useful once Almond is installable. |
| `lxqt-about` | 2.1.0-1 | main | yes | yes | Not in 0.1. |
| `lxqt-branding-debian` | 0.14.0.6 | main | yes | yes | Not used: Debian branding. |
| `slick-greeter` | 2.0.9-1 | main | yes | yes | Evaluated: heavier greeter (Python settings tool, background effects). |
| `lightdm-settings` | 2.0.7-1 | main | yes | yes | Not used: needs slick-greeter. |
| `sddm` | 0.21.0+git20250502.4fe234b-2 | main | yes | yes | Evaluated: Qt Quick greeter needs OpenGL or software rendering; heavier on old GPUs. |
| `lxdm` | 0.5.3-6 | main | yes | yes | Evaluated: light but little maintained. |
| `slim` | 1.4.1-2 | main | yes | yes | Evaluated: little maintained. |
| `greetd` | 0.10.3-4 | main | yes | yes | Evaluated: needs a separate greeter; text greeters change the look. |
| `nodm` | 0.13-6.2 | main | yes | yes | Evaluated: autologin only, no login screen. |
| `network-manager-gnome` | 1.36.0-3+b1 | main | yes | yes | Not used: GTK applet; nm-tray is the Qt one. |
| `modemmanager` | 1.24.0-1+deb13u1 | main | yes | yes | Not used: resident daemon for mobile broadband modems (a Recommends of network-manager). |
| `pipewire` | 1.4.2-1 | main | yes | yes | Evaluated (audio): not chosen for 0.1; see section 13. |
| `pipewire-pulse` | 1.4.2-1 | main | yes | yes | Evaluated (audio). |
| `wireplumber` | 0.5.8-2 | main | yes | yes | Evaluated (audio). |
| `pipewire-audio` | 1.4.2-1 | main | yes | yes | Evaluated (audio). |
| `rtkit` | 0.13-5.1 | main | yes | yes | Not used: realtime scheduling helper for audio; PulseAudio works without it. |
| `upower` | 1.90.9-1 | main | yes | yes | Pulled in as a dependency of lxqt-powermanagement (D-Bus activated). |
| `xsettingsd` | 1.0.2-1 | main | yes | yes | Not used: resident GTK settings daemon; GTK reads /etc/gtk-3.0/settings.ini. |
| `xdg-desktop-portal-lxqt` | 1.1.0-2+b1 | main | yes | yes | Not used on X11 in 0.1. |
| `xscreensaver` | 6.09+dfsg1-1 | main | yes | yes | Not used: resident; no screen locker in 0.1 (known gap). |
| `light-locker` | 1.8.0-3+b1 | main | yes | yes | Not used: resident. |
| `i3lock` | 2.15-2 | main | yes | yes | Candidate screen locker for installed releases (no daemon). |
| `xss-lock` | 0.3.0+git20230128.0c562b-1+b2 | main | yes | yes | Candidate helper to lock on suspend (small daemon). |
| `plymouth` | 24.004.60-5 | main | yes | yes | Not installed on AALDM: boot time and memory; theme files are staged for later. |
| `plymouth-themes` | 24.004.60-5 | main | yes | yes | Not installed (contains the two-step plugin the Almond theme needs). |
| `orca` | 48.1-1+deb13u2 | main | yes | yes | Optional, not in the default image: see section 11. |
| `speech-dispatcher` | 0.12.0-5 | main | yes | yes | Comes with orca. |
| `espeak-ng` | 1.52.0+dfsg-5 | main | yes | yes | Comes with orca (via speech-dispatcher). |
| `at-spi2-core` | 2.56.2-1+deb13u2 | main | yes | yes | Comes with orca; not installed by default. |
| `onboard` | 1.4.1-10 | main | yes | yes | Optional on-screen keyboard. |
| `brltty` | 6.7-3.1+deb13u3 | main | yes | yes | Optional braille support. |
| `xbrlapi` | 6.7-3.1+deb13u3 | main | yes | yes | Optional braille support. |
| `magnus` | 1:1.0.3-4 | main | yes | yes | Optional screen magnifier. |
| `kmag` | 4:25.04.0-1 | main | yes | yes | Optional screen magnifier (KDE). |
| `breeze-icon-theme` | 4:5.116.0-1 | main | yes | yes | Not used: Debian lxqt.conf default; replaced by Almond Pure + Adwaita. |
| `papirus-icon-theme` | 20250501-1 | main | yes | yes | Not used: about 187 MB installed. |
| `gnome-themes-extra` | 3.28-4 | main | yes | yes | Not used: pulls a GTK 2 engine; only the -data package is needed. |
| `firmware-intel-graphics` | 20250410-2 | non-free-firmware | yes | yes | Not used: i915 firmware starts at Skylake; not needed for the OptiPlex 390 (Sandy Bridge). |
| `firmware-iwlwifi` | 20250410-2 | non-free-firmware | yes | yes | Optional (about 114 MB installed): Intel Wi-Fi; ALMOND_FIRMWARE=all includes it. |
| `firmware-atheros` | 20250410-2 | non-free-firmware | yes | yes | Optional (about 97 MB installed). |
| `firmware-brcm80211` | 20250410-2 | non-free-firmware | yes | yes | Optional (about 18 MB installed). |
| `firmware-amd-graphics` | 20250410-2 | non-free-firmware | yes | yes | Optional (about 92 MB installed): AMD/ATI GPUs. |
| `firmware-nvidia-graphics` | 20250410-2 | non-free-firmware | yes | yes | Optional (about 65 MB installed). |
| `firmware-linux-nonfree` | 20250410-2 | non-free-firmware | yes | yes | Not used: metapackage for the big firmware set. |
| `firmware-bnx2` | 20250410-2 | non-free-firmware | yes | yes | Optional: Broadcom NetXtreme II server NICs. |
| `chromium` | 150.0.7871.181-1~deb13u1 | main | yes | yes | Evaluated (browser): security-supported, at least as heavy as Firefox. |
| `falkon` | 25.04.1-1 | main | yes | yes | Evaluated (browser): QtWebEngine, not covered by Debian 13 security support. |
| `qutebrowser` | 3.4.0-1 | main | yes | yes | Evaluated (browser): QtWebEngine, not covered by security support. |
| `epiphany-browser` | 48.5-0+deb13u1 | main | yes | yes | Evaluated (browser): WebKitGTK, covered by security support; pulls GTK 4/libadwaita. |
| `luakit` | 1:2.4.0-1 | main | yes | yes | Evaluated (browser): WebKitGTK. |
| `surf` | 2.1+git20250419-1 | main | yes | yes | Evaluated (browser): WebKitGTK, minimal UI. |
| `vimb` | 3.7.0+git20240706-1+b1 | main | yes | yes | Evaluated (browser): WebKitGTK, keyboard-driven. |
| `konqueror` | 4:25.04.0-1 | main | yes | yes | Evaluated (browser): KDE, QtWebEngine. |
| `netsurf-gtk` | 3.11-2 | main | yes | yes | Evaluated (browser): very light, little JavaScript; many sites fail. |
| `dillo` | 3.0.5-7.1 | main | yes | yes | Evaluated (browser): very light, no JavaScript. |
| `links2` | 2.29-2+b3 | main | yes | yes | Evaluated (browser): text/graphics, no JavaScript. |
| `lynx` | 2.9.2-1 | main | yes | yes | Evaluated (browser): text only. |
| `w3m` | 0.5.3+git20230121-2.1 | main | yes | yes | Evaluated (browser): text only. |
| `xfce4` | 4.20.1 | main | yes | yes | Evaluated (desktop). |
| `xfce4-session` | 4.20.2-2 | main | yes | yes | Evaluated (desktop). |
| `xfwm4` | 4.20.0-1 | main | yes | yes | Evaluated (desktop). |
| `xfdesktop4` | 4.20.1-1 | main | yes | yes | Evaluated (desktop). |
| `xfce4-panel` | 4.20.4-1 | main | yes | yes | Evaluated (desktop). |
| `task-xfce-desktop` | 3.81 | main | yes | yes | The earlier Xfce draft (removed). |
| `icewm` | 3.7.4-1 | main | yes | yes | Evaluated (desktop). |
| `jwm` | 2.4.6-2 | main | yes | yes | Evaluated (desktop). |
| `fluxbox` | 1.3.7-1+b1 | main | yes | yes | Evaluated (desktop). |
| `lxde-core` | 13.0 | main | yes | yes | Evaluated (desktop): GTK 2/3 LXDE, development moved to LXQt. |
| `lxpanel` | 0.11.1-1 | main | yes | yes | Evaluated (desktop). |
| `pcmanfm` | 1.4.0-1 | main | yes | yes | Evaluated (file manager, GTK). |
| `mate-desktop-environment-core` | 1.26.0+2 | main | yes | yes | Evaluated (desktop). |
| `labwc` | 0.8.3-1 | main | yes | yes | Future Wayland path (Openbox-like compositor, reads Openbox themes). |
| `wayfire` | 0.9.0-5 | main | yes | yes | Evaluated (Wayland compositor). |
| `sway` | 1.10.1-2 | main | yes | yes | Evaluated (Wayland compositor, tiling). |
| `kwin-wayland` | 4:6.3.6-1 | main | yes | yes | Evaluated (Wayland compositor, heavy). |
| `swaybg` | 1.2.1-1 | main | yes | yes | Wayland wallpaper helper (future). |
| `wofi` | 1.4.1-1+b2 | main | yes | yes | Wayland launcher option (future). |
| `fuzzel` | 1.12.0+ds-1 | main | yes | yes | Wayland launcher option (future). |
| `thunar` | 4.20.2-1+deb13u1 | main | yes | yes | Evaluated (file manager). |
| `spacefm` | 1.0.6-9 | main | yes | yes | Evaluated (file manager). |
| `nemo` | 6.4.5-1 | main | yes | yes | Evaluated (file manager). |
| `caja` | 1.26.4-1 | main | yes | yes | Evaluated (file manager). |
| `dolphin` | 4:25.04.3-1+deb13u1 | main | yes | yes | Evaluated (file manager, heavy KDE deps). |
| `xfe` | 2.0.1-2 | main | yes | yes | Evaluated (file manager). |
| `doublecmd-qt` | 1.1.22-1 | main | yes | yes | Evaluated (file manager, two-pane). |
| `earlyoom` | 1.8.2-1 | main | yes | yes | Optional: userspace OOM killer (resident daemon). |
| `zram-tools` | 0.3.7-1 | main | yes | yes | Not used: systemd-zram-generator does the same without a script. |
| `curl` | 8.14.1-2+deb13u5 | main | yes | yes | Not in the image (was in the draft); install when needed. |
| `git` | 1:2.47.3-0+deb13u1 | main | yes | yes | Build host only (removed from the image). |
| `qt6-wayland` | 6.8.2-4 | main | yes | yes | Not used on X11. |
| `galculator` | 2.1.4-2 | main | yes | yes | Candidate calculator (not in 0.1). |
| `qmmp` | 2.2.4-1+b1 | main | yes | yes | Candidate audio player (not in 0.1). |
| `fonts-noto-core` | 20201225-2 | main | yes | yes | Not in 0.1: wide script coverage, large. |
| `fonts-hack` | 3.003-3 | main | yes | yes | Not used: qterminal falls back to DejaVu Sans Mono. |
| `xfonts-base` | 1:1.0.5+nmu1 | main | yes | yes | Not used: core X fonts for legacy X programs. |
| `dbus-x11` | 1.16.2-2 | main | yes | yes | Not used: dbus-user-session provides the session bus. |
| `libgtk-3-bin` | 3.24.49-3 | main | yes | yes | Not used. |
| `qt6-qpa-plugins` | 6.8.2+dfsg-9+deb13u2 | main | yes | yes | Not used: only the VNC and TUIO plugins; the xcb platform plugin is part of `libqt6gui6` (checked in its file list). |

Names that are **not** binary packages in trixie (madison returned nothing, or only a source package):

| Name | Finding | Used instead |
|---|---|---|
| `policykit-1` | source package only in trixie | `polkitd` (and `pkexec`) |
| `lxqt-wayland-session` | not in trixie | — (Wayland session: future) |
| `rofi-wayland` | not in trixie | `rofi` (X11) |
| `fonts-atkinson-hyperlegible-otf` | not in trixie | `fonts-atkinson-hyperlegible` (contains the OTF files) |
| `openbox-menu` | not in trixie | LXQt menu |
| `firefox` | not in trixie | `firefox-esr` |
| `midori`, `badwolf` | not in trixie | — |
| `speedcrunch` | not in trixie | — (calculator not in 0.1) |
| `lxqt-l10n` | not in trixie | per-program `-l10n` packages (not installed in 0.1; English only) |

Build-host tools (installed on the build machine or, by live-build itself, inside its chroot): `live-build` 1:20250505+deb13u1, `debootstrap` 1.0.141, `xorriso`, `squashfs-tools`, `syslinux`, `isolinux`, `syslinux-common`, `grub-efi-amd64-bin`, `grub-efi-amd64-signed`, `grub-pc-bin`, `grub-efi-ia32-bin`, `shim-signed`, `mtools`, `dosfstools`, `librsvg2-bin`, `git` — all present in trixie for amd64 (`grub-efi-arm64-bin` / `-signed` for arm64).

## Appendix C — sources

Read on 2026-10-14 unless stated otherwise.

- Debian archive API (madison): <https://api.ftp-master.debian.org/madison>; package pages: <https://packages.debian.org/trixie/>.
- live-build 1:20250505+deb13u1 source (option defaults, `#if` package-list syntax, `config/bootloaders/` merging, splash handling, firmware, manifest): <https://sources.debian.org/src/live-build/1:20250505+deb13u1/>.
- live-config 11.0.5 source (LightDM autologin component): <https://sources.debian.org/src/live-config/11.0.5/>.
- lxqt-session 2.1.1-1 source (`session.conf`, `lxqt.conf`, window-manager start): <https://sources.debian.org/src/lxqt-session/2.1.1-1/>.
- lightdm-gtk-greeter 2.0.9-1 source (configuration file order and keys): <https://sources.debian.org/src/lightdm-gtk-greeter/2.0.9-1/>.
- rust-zram-generator 1.2.1-2 Debian packaging (default zram config): <https://sources.debian.org/src/rust-zram-generator/1.2.1-2/>.
- Debian 13 release notes, "Issues to be aware of", section on browser security support (QtWebEngine not covered; WebKitGTK covered; Firefox and Chromium recommended): <https://www.debian.org/releases/trixie/release-notes/issues.en.html>.
- Debian General Resolution on non-free firmware (2022): <https://www.debian.org/vote/2022/vote_003>; Debian firmware overview: <https://wiki.debian.org/Firmware>.
- OptiPlex 390 firmware mode: Dell community forum threads with conflicting reports (UEFI without Secure Boot vs. legacy only), for example <https://www.dell.com/community/Optiplex-Desktops/Optiplex-390-How-to-disable-secure-boot/td-p/7752061>; not authoritative — check the machine.
- LXQt vs Openbox memory hint: a 2016 benchmark post on the LXDE project blog (blog.lxde.org) — seen only through a web-search summary; the blog could not be opened on 2026-10-14 (TLS certificate error), so the exact post and figures are not re-checked.
