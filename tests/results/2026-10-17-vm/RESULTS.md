# Almond Linux 0.1 "Marcona" AALDM — first build and VM boot test

Plain facts from the first end-to-end run on the Windows build-and-test PC. "Not tested" means exactly that.

- **Test date:** 2026-10-17 (written up 2026-10-18)
- **Repository:** https://github.com/AlmondLinux/almond-linux, commit `64014332c5ce6f22af1b43996bd2375184206fc1` (2026-10-14, "AALDM: Almond Pure assets, desktop theme and amd64 build configuration"), worktree clean
- **Nothing was committed or pushed.** No file in the repository was changed.

## Summary

| Item | Result |
|---|---|
| Build | **OK** (`P: Build completed successfully`, 0 `E:` lines in `build.log`, about 14 min) |
| ISO | `live-image-amd64.hybrid.iso`, 845,152,256 bytes |
| ISO SHA256 | `7129bf3e3f7bededa373fe74dcc1e742891fd4d4c5dd7488581b5360d653fe9d` (`sha256sum -c` OK in the VM; `Get-FileHash` matches on Windows) |
| Legacy BIOS boot (VirtualBox, 2048 MB) | **OK**: isolinux menu → LXQt desktop with autologin |
| UEFI boot (VirtualBox, 2048 MB) | **OK**: GRUB menu → LXQt desktop with autologin |
| Memory "Used", 2048 MB VM (1 boot) | **413.2 MiB** |
| Memory "Used", 1024 MB VM (1 boot) | **393.2 MiB** |
| 300 MB idle target (AALDM-PLAN §0) | **Not met** in these single-boot measurements |

## Environment

**Host PC**
- Windows 11 Home, version 10.0.26200 (build 26200), 64-bit
- Intel Core i9-13900K (24 cores / 32 threads), 63.7 GB RAM
- Windows hypervisor running (`HypervisorPresent=True`; VBS running, security services 2 and 7). Memory Integrity left on. Hyper-V feature state not checked (needs admin). WSL not installed.
- VirtualBox **7.2.20 r175154**. Because VT-x is held by the Windows hypervisor, VirtualBox ran through the Windows Hypervisor Platform (`HM: HMR3Init: Attempting fall back to NEM: VT-x is not available`).

**Build VM `almond-build`** (`C:\AlmondVMs\almond-build\`)
- Type Debian_64, 8192 MB RAM, **1 CPU** (see Problem 1), 80 GB dynamic VDI on SATA, BIOS firmware, NAT with 127.0.0.1:2222 → 22
- Debian **13.7.0** "trixie" from `debian-13.7.0-amd64-netinst.iso` (792,723,456 bytes, SHA256 `a7ef94ac2fb9a7fec454552abd629b7cc9d5155c886165a45649f5ce6167e355`, matches the official `SHA256SUMS`)
- Installed with `VBoxManage unattended install`, using a copy of VirtualBox's Debian preseed with `tasksel tasksel/first multiselect standard, ssh-server` added. Result: 304 packages, no desktop, kernel 6.12.113+deb13-amd64.
- Build tools: live-build `1:20250505+deb13u1`, debootstrap `1.0.141`, xorriso 1.5.6-1.2+b1, squashfs-tools 1:4.6.1-1, grub-efi-amd64-bin / grub-pc-bin 2.12-9+deb13u2, syslinux / isolinux 6.04~git20190206, mtools 4.0.48-1, dosfstools 4.2-1.2, git 2.47.3

**Test VM `almond-test`** (`C:\AlmondVMs\almond-test\`)
- Type Debian_64, 2 CPUs, **no hard disk**, ISO on a SATA DVD drive, VMSVGA with 32 MB VRAM, NAT, HDA audio, USB tablet
- 2048 MB for the BIOS, UEFI and 2 GB memory runs; 1024 MB for the 1 GB memory run
- Firmware `bios` first, then `efi`. Secure Boot was not enabled in the VM (not tested).

## Build

- Command: `sudo ./scripts/build.sh` (defaults: `ALMOND_EDITION=aaldm`, `ALMOND_ARCH=amd64`, `ALMOND_FIRMWARE=listed`), started in the background with `nohup … setsid`
- Attempt directory: `/home/almond/almond-linux/build/attempt.3t4fCW/`, kept untouched in the build VM
- Started 2026-10-17T14:51:56Z; `lb build` finished 17:05:26 VM local time (about 14 minutes)
- Staging: `Staging: 42 item(s) staged, 0 warning(s).`
- `debootstrap` ran with `--force-check-gpg`; `auto/config` uses `--apt-secure true`. No signature check was disabled.
- Both hooks ran. `0200-almond-desktop` printed, among others:
  - `x-session-manager -> /usr/bin/startlxqt`, `x-window-manager -> /usr/bin/openbox`
  - `greeter: background=/usr/share/backgrounds/almond/almond-pure-dark.svg theme=Adwaita-dark icons=Almond-Pure`
  - icon caches for Almond-Pure (+ Blue, Gray, Green, Orange, Plum, Red), hicolor, Adwaita, AdwaitaLegacy
  - `global shortcuts: replaced the directory /etc/xdg/lxqt/globalkeyshortcuts.conf with a merged file (1 Debian file(s) + Almond's)`
  - goa, afc and gphoto2 volume monitors diverted to `*.almond-disabled`
- Package manifest: 765 packages; kernel `linux-image-6.12.113+deb13-amd64 6.12.113-1`. None of `modemmanager`, `desktop-base`, `papirus-icon-theme`, `xscreensaver`, `plymouth`, `orca` is present.
- Selected versions from the manifest: firefox-esr `153.5.0esr-1~deb13u1`, lxqt-session 2.1.1-1, openbox 3.6.1-12+b2, rofi 1.7.5-0.1+b2, lightdm 1.32.0-6+b2, xserver-xorg-core 2:21.1.16-1.3+deb13u4, live-boot 1:20250815~deb13u1, live-config 11.0.5
- ISO volume `ALMOND_01`; El Torito: BIOS `/isolinux/isolinux.bin`, UEFI `/boot/grub/efi.img`. Log line: `P: UEFI Secure Boot support enabled.`
- Network: about 714 MB had been received by the build VM's network card after 12 minutes. That count also includes the earlier ~24 MB tool install and the clone.

**Warnings in `build.log`** (exact text; no `E:` lines):
- `W: No zstd in /usr/bin:/sbin:/bin, using gzip`, 3 times, right after `update-initramfs: Generating /boot/initrd.img-6.12.113+deb13-amd64`. The `zstd` package is not in the image, so the initramfs is gzip-compressed. Effect on size and boot time not measured.
- `dpkg-divert: warning: diverting file '/usr/sbin/start-stop-daemon' from an Essential package with rename is dangerous, use --no-rename` and the same for `/usr/bin/hostname`, 5 times each (live-build's own diversions)
- `update-rc.d: warning: start and stop actions are no longer supported; falling back to defaults` and `update-rc.d: warning: start runlevel arguments (none) do not match live-tools Default-Start values (S)`
- `W: Skipping removal of chroot_debianchroot, it is not applied`
- In live-build's GRUB EFI stage: `WARNING: The following essential packages will be removed.` and `dpkg: warning: this is a protected package; it should not be removed`. These are inside the block live-build itself marks `!!! The following error/warning messages can be ignored !!!`: it temporarily installs GRUB/shim packages in the chroot to build the EFI image, then removes them again.

## Boot test: legacy BIOS (2048 MB, 2 CPUs)

| BUILD.md acceptance step | Result |
|---|---|
| 1. Boot menu and default entry reach the desktop without login | **OK.** Almond isolinux splash, menu "Live system (amd64)", "Live system (amd64 fail-safe mode)", "Utilities". No countdown: it waits for Enter. About 30 s from Enter to the desktop. No login prompt. |
| 2. `uname -m` | **OK:** `x86_64` |
| 3. `/etc/os-release` | **OK:** `PRETTY_NAME="Almond Linux 0.1 Marcona (AALDM development preview)"`, `ID_LIKE=debian`, `VARIANT_ID=aaldm` |
| 4. LXQt with Openbox | **OK:** `desktop=LXQt`; `1120 openbox --config-file /home/almond/.config/openbox/lxqt-rc.xml`; no window-manager chooser appeared |
| 5. Super opens the launcher, typing filters, Enter starts, Esc closes | **OK** for Super (sent into the VM with `VBoxManage keyboardputscancode e0 5b e0 db`), typing, Enter (QTerminal started) and Esc. Also opens from the panel's almond button. `pgrep rofi` before the Super test: `rofi-not-running`; after Esc: not confirmed (see Problem 6). `/etc/xdg/lxqt/globalkeyshortcuts.conf` is a file (`-rw-r--r-- 1 root root 3264`). Ctrl+Alt+T and Print: not tested. |
| 6. Network | **Partly:** `nmcli`: `enp0s3 ethernet connected "Wired connection 1"`. Firefox ESR started (by accident, see Problem 6) and showed "Welcome to Firefox". **Loading an HTTPS page: not tested.** |
| 7. `sudo apt update` | **Not tested** |
| 8. File manager, editor, image viewer, keyboard layout, resolution, sound, keyboard-only use, volume monitors | **Not tested** (the file manager and the LXQt Appearance settings were opened, but no checks were run) |
| 9. Memory | Done, 1 boot each at 2048 and 1024 MB (see below); not the 5-boot median |
| 10. `ss -lntup`, `nft list ruleset`, `aa-status` | **Not tested** |
| 11. Shut down and boot again | The VM was reset and booted again 3 times and reached the desktop each time; changes did not persist |

Other observations: zram works (`/dev/zram0 partition 1010172 KB, used 0, priority 100`). `swapon` gave `bash: swapon: command not found` for the normal user, because it is in `/usr/sbin`. Passwordless `sudo` works for the live user. Screen resolution was 1280×800. The panel clock shows UTC.

## Boot test: UEFI (2048 MB, 2 CPUs)

- VirtualBox EFI logo, then **"Live Boot Menu with GRUB"** with the Almond logo and the same three entries, help line "enter: boot, `e`: options, `c`: cmd-line". No countdown.
- Enter (sent with VBoxManage) → LXQt desktop with autologin after about 30 s.
- The Super key opened Almond Launch and Esc closed it.
- **Not run in UEFI mode:** the terminal checks (steps 2–4, 6), the memory tests and everything not run in BIOS mode.
- VirtualBox reported 0 clock-lag events in this run.

## Memory (`tests/measure-memory.sh`)

Method used: fresh boot (VM reset or power-on) in BIOS mode, about 2 minutes untouched on the desktop, then the launcher → QTerminal, then `sudo sh /usr/share/almond/tests/measure-memory.sh -w 120 > memory-N.txt` (the script waits another 120 s itself). QTerminal was open during the measurement. The file was copied out with `python3 -m http.server 8000` in the VM and a VirtualBox NAT rule `127.0.0.1:8080 → 8000`; the server was stopped afterwards.

| Figure (MiB) | 2048 MB VM (`memory-2gb.txt`) | 1024 MB VM (`memory-1gb.txt`) |
|---|---|---|
| Uptime at measurement | 329 s | 335 s |
| MemTotal | 1973.7 | 967.2 |
| MemFree | 1086.3 | 96.0 |
| MemAvailable | 1560.5 | 573.9 |
| Cached | 620.8 | 616.6 |
| Shmem | 31.6 | 27.7 |
| **Used (MemTotal − MemAvailable)** | **413.2** | **393.2** |
| Swap (zram) total / used | 986.5 / 0.0 | 483.5 / 0.0 |
| Desktop session total (PSS) | 243.7 | 244.5 |
| All readable processes (PSS) | 287.4 | 288.1 |

PSS by component (2048 MB / 1024 MB): Xorg 93.9 / 94.3, LXQt session + panel 53.6 / 53.3, pcmanfm-qt 18.7 / 18.9, PulseAudio 17.5 / 17.5, gvfs + udisks2 15.7 / 15.8, nm-tray 13.6 / 13.7, NetworkManager 12.5 / 12.5, Openbox 8.7 / 8.9, LightDM 3.1 / 3.0, rofi 0.0 / 0.0. QTerminal (open) 12.3 / 12.3.

Caveats:
- One boot per RAM size, not the 5-boot median that PERFORMANCE.md asks for.
- During the 1024 MB run VirtualBox logged 4 stalls: `TM: Giving up catch-up attempt at a 60 002 966 245 ns lag` (60 s each, 240 s in total, at 2–6 min of VM uptime). The 2048 MB run logged none.
- Both reports show `Unreadable or exited during scan: 72` together with `Kernel threads (no user memory): 0` (see Problem 5).

## Problems and bugs found

1. **The build VM froze with 4 CPUs.** The first unattended Debian install stopped at "Starting up the partitioner 13%" for about 45 minutes. The screenshots were identical from minute 2 onwards, keys were ignored, and `VBox.log` showed `TM: Giving up catch-up attempt at a 2 791 175 831 854 ns lag`. With 1 CPU the install finished in about 5 minutes, and the build ran on 1 CPU. This is VirtualBox running through the Windows hypervisor (NEM), not an Almond problem. The test VM ran with 2 CPUs; it had short 60 s stalls only in the 1024 MB run. Not tried: turning Memory Integrity off.
2. **Launcher: four tiles without an icon:** "Session Set…", "Rofi Theme …", "Notifications", "File Associa…" (`04-bios-launcher-after-click.png`, `09-bios-launcher-super-sent.png`).
3. **Launcher: risky default highlight.** When opened with an empty search box, the highlighted tile was "Hibernate" 2 of 3 times (once "Brightness"), so pressing Enter at once would hibernate. After typing `qterminal`, the highlight stayed on the second position ("QTerminal d…", the drop-down terminal) instead of moving to the first match, 2 of 2 times. "Type a name, press Enter" can therefore open the wrong program. Long names are cut off with "…".
4. **Launcher offers "Lock Screen" and "Hibernate".** No screen locker is installed (known gap in AALDM-PLAN §4). Neither tile was clicked; effect not tested.
5. **Possible `measure-memory.sh` bug:** `Unreadable or exited during scan: 72` but `Kernel threads (no user memory): 0`, measured as uid 0. Kernel threads may be counted as "unreadable". Not investigated.
6. **First-login pop-ups:** two `lxqt-powermanagement` notifications appeared after login in the boots where the first desktop screenshot was checked (1st and 2nd BIOS boot): "No battery! LXQt could not find data about any battery - monitoring disabled" and "You are running LXQt Power Management for the first time… Configure...". They disappeared on their own within 1–2 minutes.
7. **GRUB (UEFI) menu:** the title "Live Boot Menu with GRUB" is drawn over the top of the almond logo (`20-uefi-grub-menu.png`).
8. **No zstd in the image** (`W: No zstd … using gzip`, see Build).
9. **Docs vs. reality:**
   - BUILD.md recommends 4 vCPUs for the build VM, which froze on this PC.
   - AALDM-PLAN names Firefox ESR 140; the image has `153.5.0esr-1~deb13u1`.
   - PC-SETUP.md runs `measure-memory.sh` without `-w 120`; BUILD.md uses `-w 120`.
   - PC-SETUP.md suggests shared folders and Guest Additions; `scp` from the build VM worked without them. The live image has no Guest Additions, so clipboard sharing with the test VM does not work.
10. **Not an Almond bug, recorded for completeness:** `VBoxManage unattended install` prints the user password in clear text in its output (`password = …`). Changing it afterwards was recommended; whether it was changed is not verified.

Test-procedure incidents (my mistakes, not image bugs):
- Text I typed into the VM with `keyboardputstring`, without first checking keyboard focus, partly landed outside QTerminal. Only "cl" reached the terminal, then Firefox opened and the terminal was moved and resized (`11-`, `11b-bios-rofi-after-esc.png`). Nothing was typed into Firefox. So "rofi exited after Esc" was not confirmed by `pgrep`; the screenshot only shows the launcher closed.
- One Enter press at the boot menu did not reach the VM (the window probably had no keyboard focus); I then sent Enter with VBoxManage.
- In the first BIOS session a file manager window ("Desktop" folder) appeared 50–60 s after the desktop (`03-bios-desktop-filemanager-open.png`); whether the owner opened it is **not confirmed**. The Configuration Center and Appearance windows in a later session were opened by the owner. In the three later clean boots (2 GB, 1 GB, UEFI) no window opened by itself.
- The owner's own Windows-key press was not captured: two screenshots 3 s apart showed no launcher (`08`, `08b`). The key sent with VBoxManage did open it.

## Owner feedback (from the first look at the desktop)

- **Does not like the desktop icons** ("almond" home folder, "Computer", "Trash") and how they look. They come from `desktop/defaults/etc/xdg/pcmanfm-qt/lxqt/settings.conf` (`DesktopShortcuts=Home, Trash, Computer`, `DesktopIconSize=48`) and the Almond Pure icon theme.
- **Wants a start menu to configure everything.** The panel has no classic application menu by design (`panel.conf`: only the almond quick-launch button, which opens the Almond Launcher). Settings are reachable only by finding "LXQt Config…" or "Appearance" in the launcher. Owner prefers a classic start menu with categories and settings.

## Not tested

Firefox loading an HTTPS page; `sudo apt update` in the live system; Ctrl+Alt+T and Print shortcuts; sound; file manager functions (USB stick, SFTP, Find Files, Ctrl+H); text editor; image viewer; keyboard layout and resolution change; keyboard-only session; `pgrep -a -f volume-monitor`; `ss -lntup`, `nft list ruleset`, `aa-status`; Secure Boot; the fail-safe and Utilities menu entries; the terminal checks and memory in UEFI mode; the 5-boot memory median; Firefox memory; the greeter (`live-config.noautologin`); real hardware (the Dell OptiPlex 390 was not used).

## Files in this folder

| File | What it is |
|---|---|
| `live-image-amd64.hybrid.iso` | the ISO (845,152,256 bytes) |
| `SHA256SUMS` | SHA-256 of the ISO and `package-manifest.txt` (both verified on Windows) |
| `live-image-amd64.packages`, `package-manifest.txt` | installed packages and versions (identical files) |
| `build-tool-versions.txt`, `build-settings.txt`, `configure.log`, `build.log` | build records |
| `memory-2gb.txt`, `memory-1gb.txt` | memory reports |
| `screenshots/` | `01`–`13` BIOS, `20`–`23` UEFI; subfolders `bios-progress`, `mem2gb-progress` (invalid idle run), `mem2gb-run3`, `mem1gb`, `uefi` hold the step-by-step shots |

Key screenshots: boot menus `01-bios-boot-menu.png` and `20-uefi-grub-menu.png`; desktops `02-bios-desktop.png` and `21-uefi-desktop.png`; Almond Launcher open `04-bios-launcher-after-click.png`, `09-bios-launcher-super-sent.png` and `22-uefi-launcher.png`.
