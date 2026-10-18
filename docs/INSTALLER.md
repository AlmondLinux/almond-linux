# Installer: "Install Almond Linux" with Calamares

Task [T-0007](../ai-bridge/tasks/T-0007-install-almond-linux-option-with-calamares.md). Written 2026-10-18. **Nothing here has been built, booted or used to install anything.** Status: IMPLEMENTED (untested).

## What the user sees (once built)

- In the live session: an **Install Almond Linux** icon on the desktop and an "Install Almond Linux" entry in the Almond Launcher.
- It opens Calamares with Almond branding (light sidebar, the owner's logo unaltered). Steps: Welcome → Location → Keyboard → Partitions → User → Summary, then a confirmation before anything is written (`prompt-install: true`).
- The installed system boots to the LightDM login screen with the user created in the installer. No live user, no autologin, no passwordless sudo, no installer.

## Research: Calamares in Debian 13

| Package | Version | Size | Role |
|---|---|---|---|
| `calamares` | 3.3.14-1 | 11 MB installed, plus its dependencies (KDE Frameworks 6 parts, kpmcore, Qt 6 QML, libpython3.13, os-prober) | The installer program. Recommends (btrfs-progs, squashfs-tools) are not installed because AALDM builds without Recommends |
| `calamares-settings-debian` | 13.0.13-1 | 225 kB | Debian's configuration and helper modules: `sources-media` (uses the live medium as an apt source), `bootloader-config` (installs grub-pc or grub-efi into the new system), `dpkg-unsafe-io`, `sources-final`. Also Debian's branding and an "Install Debian" icon |

Sources: packages.debian.org (trixie), sources.debian.org (calamares-settings-debian 13.0.13-1), checked 2026-10-18.

Almond uses Debian's helper modules but replaces everything that names or shows Debian:

| Debian file | Almond replacement |
|---|---|
| `/etc/calamares/settings.conf` (branding `debian`) | `branding: almond`; no `plymouthcfg` step (AALDM has no plymouth); an Almond clean-up step after `packages` |
| `/etc/calamares/modules/packages.conf` | Removes the live packages **and** the installer from the new system |
| `/etc/calamares/modules/welcome.conf` | No release-notes link; same requirements (15 GB disk, 1 GB RAM) until AALDM's installed size is measured |
| `/etc/calamares/branding/debian/` | `/etc/calamares/branding/almond/`: Almond strings and colours; images are links to `/usr/share/pixmaps/almond-mark-128.png` and `almond-logo-1024.png` |
| `calamares-install-debian.desktop`, its autostart desktop icon | `almond-install.desktop`, `almond-install` wrapper, `almond-install-icon` autostart |

Debian's files stay in the image under `*.almond-disabled` (local `dpkg-divert`, as the 0200 hook already does for gvfs monitors).

## Files

| File | Installed as | What it does |
|---|---|---|
| `config/package-lists/aaldm.list.chroot` (2 lines added) | | Installs `calamares`, `calamares-settings-debian` |
| `config/package-lists/aaldm-installer.list.binary` | ISO package pool | GRUB (BIOS + UEFI, signed), shim, cryptsetup for the **new** system, so an install works without a network |
| `config/hooks/live/0300-almond-installer.hook.chroot` | | Diverts Debian's files, installs Almond's, links the branding images. Skips itself if Calamares is missing |
| `desktop/defaults/usr/share/almond/calamares/` | same path | Almond settings, modules and branding (copied into `/etc/calamares` by the hook) |
| `desktop/defaults/usr/bin/almond-install` | `/usr/bin/almond-install` | Starts Calamares with `pkexec`; refuses outside the live system |
| `desktop/defaults/usr/share/applications/almond-install.desktop` | same path | Launcher entry (hidden when Calamares is missing) |
| `desktop/defaults/etc/xdg/autostart/almond-install-icon.desktop` + `desktop/defaults/usr/libexec/almond/almond-install-icon` | same paths | Copies the entry to the live user's desktop at login |

## Open risks (check in the first install test)

1. **Bootloader from the ISO pool.** Debian's `sources-media` step adds `deb [trusted=yes] file:/run/live/medium trixie main` and `bootloader-config` runs `apt-get install grub-pc` or `grub-efi` from it. Almond's ISO had no pool (`--debian-installer none`); `aaldm-installer.list.binary` asks live-build to add one. Whether live-build lays it out as an apt repository at that path is **not verified**. If not, the bootloader step fails offline.
2. **Disk size.** Calamares' dependencies (KF6, kpmcore, Qt QML) make the ISO larger. Not measured.
3. **Polkit in the live session.** `pkexec calamares` relies on live-config allowing the live user; not checked.
4. **GRUB menu name** on the installed system comes from `GRUB_DISTRIBUTOR`. It may say "Debian" until Almond sets it.
5. **Password rules** are Debian's (any non-empty password). The owner may want stricter ones (`modules/users.conf`).
6. The installed system keeps `/etc/apt/sources.list.d` from `sources-final` (Debian's mirrors). That is expected: Almond 0.x uses Debian's archive.

## Test plan (disposable VirtualBox disks only)

**Never on real hardware. Never on the Dell OptiPlex 390's internal disk.**

For each of BIOS and UEFI:

1. New VM "almond-install-bios" / "-uefi": 2 CPUs, 2048 MB, **new empty 20 GB VDI**, the new ISO attached, network **off** (proves the offline install).
2. Boot the live system. Screenshot the desktop: is the "Install Almond Linux" icon there? Open it from the launcher too.
3. Install: "Erase disk", user `tester`, a test password. Screenshot every page. Note the time taken.
4. When it finishes, power off, detach the ISO, boot from the disk.
5. Check and record:
   - the GRUB menu appears and boots; its title
   - LightDM login screen (no autologin); log in as `tester`
   - `cat /etc/os-release` shows Almond
   - `id` (groups include sudo), `sudo -l` asks for the password
   - `getent passwd almond` returns nothing (no live user)
   - `dpkg -l calamares live-boot live-config` shows them not installed
   - no "Install Almond Linux" entry in the launcher or on the desktop
   - `ls /etc/calamares` fails (removed)
   - turn the network on: `sudo apt update` works
   - `sudo sh /usr/share/almond/tests/measure-memory.sh -w 120` (installed-system memory)
6. Reboot twice; it should come back the same.

Record results in `tests/results/<date>-install/RESULTS.md` like the first VM test.
