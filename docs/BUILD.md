# Building and testing AALDM

## Objective

Produce the experimental **Almond Linux 0.1 "Marcona" AALDM** live ISO for 64-bit PCs (amd64), then prove it boots in a VM in both legacy-BIOS and UEFI mode, and later on the first real test PC, a Dell OptiPlex 390.

**These instructions and scripts have NOT produced an ISO yet.** Everything below is the intended procedure; "expected" means not observed.

## What gets built

| Setting | Default | Other values |
|---|---|---|
| `ALMOND_EDITION` | `aaldm` (A All Little Distribution Model) | none yet; AALLDM is not defined |
| `ALMOND_ARCH` | `amd64`: hybrid ISO, boots legacy BIOS (isolinux) and UEFI (GRUB), from DVD or USB | `arm64`: development variant for VMs on Apple Silicon Macs, UEFI only |
| `ALMOND_FIRMWARE` | `listed`: only the firmware packages in the package list | `all`: every firmware package of the archive (bigger; for diagnosing hardware) |

Desktop: LXQt 2.1 + Openbox on X11, LightDM, Firefox ESR, from Debian 13 "trixie" `main` and `non-free-firmware`. Reasons and package details: [AALDM-PLAN.md](AALDM-PLAN.md).

## Build host

- **amd64 ISO: a native amd64 Debian 13 machine.** In practice a Debian 13 amd64 VM on an ordinary x86-64 PC (Windows, Linux or an Intel Mac). Step-by-step for a Windows PC with VirtualBox: [PC-SETUP.md](PC-SETUP.md).
- **Apple Silicon Macs can only build the arm64 development variant natively**, inside a Debian 13 arm64 VM (UTM/QEMU or Parallels). That variant tests the build and the desktop, not the target hardware.
- **Cross-building** (amd64 ISO on an arm64 host, through qemu-user emulation) is future work. `scripts/build.sh` refuses when the host architecture differs from `ALMOND_ARCH`.
- Starting allocation for the build VM: 8 GB RAM, 80 GB virtual disk (recommendations, not measured minimums), and **1 virtual CPU when VirtualBox runs on Windows through the Windows hypervisor** (the NEM fallback; `VBox.log` then says `VT-x is not available`). On 2026-10-17, 4 vCPUs froze the Debian install for about 45 minutes, while 1 vCPU installed it in about 5 minutes and the build completed ([test results](../tests/results/2026-10-17-vm/RESULTS.md), Problem 1). More vCPUs may work where VirtualBox has VT-x to itself (for example with Memory Integrity off); that was not tested. Keep the build on the VM's own Linux filesystem, not a shared folder. Do not attach physical disks.
- Verify the Debian installer image's checksum before installing the build VM (Debian publishes `SHA256SUMS` and signatures next to each image).

The build runs as root inside that dedicated machine, because live-build creates mounts and chroots. `scripts/build.sh` refuses to run on macOS or any non-Linux system, on anything that is not Debian 13, without root, without live-build, or with the wrong architecture.

## Commands inside the Debian build machine

```sh
sudo apt update
sudo apt install live-build debootstrap ca-certificates git
```

live-build installs the bootloader and image tools it needs (syslinux, isolinux, GRUB EFI, xorriso, squashfs-tools, rsvg-convert) *inside its own build chroot*, so they are not strictly needed on the host. Installing them on the host as well, as [PC-SETUP.md](PC-SETUP.md) does, is harmless.

From the project directory:

```sh
sudo ./scripts/build.sh                        # AALDM, amd64 (default)
sudo ALMOND_ARCH=arm64 ./scripts/build.sh      # arm64 dev variant (arm64 host)
sudo ALMOND_FIRMWARE=all ./scripts/build.sh    # all firmware packages
```

`sudo` drops environment variables set earlier, so put them **on the sudo line** as shown.

Each run creates a new `build/attempt.XXXXXX/` and never deletes earlier attempts. Before building, the script copies `auto/` and `config/` there and stages the Almond assets into the attempt's `config/includes.chroot/` (missing assets are reported as warnings; the build continues):

| Source in the repository | Path in the image |
|---|---|
| `desktop/icons/*/` | `/usr/share/icons/` |
| `desktop/openbox/*/` | `/usr/share/themes/` |
| `desktop/launcher/almond-launch` | `/usr/bin/almond-launch` (0755) |
| `desktop/launcher/*.rasi`, `*.example` | `/usr/share/almond/launcher/` |
| `desktop/launcher/almond-launch-*` (helpers, not `.rasi`) | `/usr/libexec/almond/` (0755) |
| `desktop/launcher/almond-launch.desktop` | `/usr/share/applications/` |
| `desktop/lxqt/globalkeyshortcuts.conf` (Super key) | `/usr/share/almond/lxqt/globalkeyshortcuts.conf` (a copy in `desktop/defaults/etc/xdg/lxqt/` wins and is moved there too). Not staged to `/etc/xdg/lxqt/`: Debian 13's `lxqt-globalkeys` installs that path as a directory. The 0200 hook merges it with Debian's default shortcuts into a plain file at `/etc/xdg/lxqt/globalkeyshortcuts.conf` |
| `desktop/wallpapers/*` | `/usr/share/backgrounds/almond/` |
| `desktop/defaults/etc/`, `desktop/defaults/usr/` | `/etc/`, `/usr/` |
| `desktop/lxqt/themes/*/`, `desktop/lxqt/palettes/*` | `/usr/share/lxqt/themes/`, `/usr/share/lxqt/palettes/` |
| `desktop/gtk/settings.ini` | `/etc/gtk-3.0/settings.ini` |
| `branding/boot/plymouth/almond/` | `/usr/share/plymouth/themes/almond/` (staged for later; plymouth is not installed) |
| `branding/logo/png/*.png` | `/usr/share/pixmaps/almond-*.png` |
| `tests/measure-memory.sh` | `/usr/share/almond/tests/measure-memory.sh` |
| `branding/boot/isolinux-splash.png` (amd64) | BIOS boot menu background (`config/bootloaders/isolinux/splash.png`) |
| `branding/boot/grub-background.png` | GRUB (UEFI) menu background (`config/bootloaders/grub-pc/splash.png`) |

Staged files are made root-owned, 0644 (0755 if they were executable); `.DS_Store` and `*.md` files are dropped. The hooks in `config/hooks/live/` then set the Almond identity (`0100`) and the desktop defaults (`0200`: LXQt session with Openbox, LightDM and greeter settings, icon caches, the merged global-shortcuts file, and `dpkg-divert`s that disable the GOA, AFC and gphoto2 gvfs volume monitors).

Expected output, not observed, in `build/attempt.XXXXXX/`:

| File | Content |
|---|---|
| `live-image-amd64.hybrid.iso` (`live-image-arm64.iso` for arm64) | the image |
| `SHA256SUMS` | SHA-256 of the ISO and of `package-manifest.txt` |
| `package-manifest.txt` | copy of live-build's `live-image-<arch>.packages` (every installed package and version) |
| `build-settings.txt` | edition, architecture, firmware mode, host, git commit and whether the tree had uncommitted changes |
| `build-tool-versions.txt` | live-build and debootstrap versions |
| `configure.log`, `build.log` | full logs |

Check the hash from that directory:

```sh
sha256sum -c SHA256SUMS
```

A checksum detects changes; it does not prove who made the file. Release signing is still planned.

## Acceptance test (amd64 VM)

Create a test VM (VirtualBox, QEMU/KVM or similar) with **2 GB RAM** first, then repeat with **1 GB RAM**; 2 CPUs; NAT networking; **no virtual hard disk**. Attach the ISO. Run the whole test twice: once with **legacy BIOS** firmware, once with **UEFI**.

1. The boot menu appears (Almond background expected; BIOS: isolinux, UEFI: GRUB) and the default entry reaches the desktop without a login prompt.
2. Open a terminal (QTerminal): `uname -m` reports **`x86_64`**.
3. `cat /etc/os-release` identifies Almond Linux 0.1 "Marcona" AALDM with `ID_LIKE=debian` and `VARIANT_ID=aaldm`.
4. The session is **LXQt with Openbox**: `echo $XDG_CURRENT_DESKTOP` prints `LXQt`; `pgrep -a openbox` shows Openbox running with `--config-file` (through `almond-openbox`); no window-manager chooser appeared at first login.
5. **Super opens the Almond Launcher** (rofi); typing filters, Enter starts the program, Esc closes it; afterwards `pgrep rofi` prints nothing. Debian's default shortcuts still work: Ctrl+Alt+T opens QTerminal, Print starts `screengrab`. `/etc/xdg/lxqt/globalkeyshortcuts.conf` is a file, not a directory.
6. Network: `nmcli device status` shows the connection; Firefox ESR loads an HTTPS page.
7. `sudo apt update` succeeds without unauthenticated-repository warnings; sources include trixie, trixie-updates and trixie-security with `main non-free-firmware`.
8. Exercise the file manager (USB stick if the VM can pass one through), text editor, image viewer, keyboard layout, screen resolution, sound (`pavucontrol-qt`), and keyboard-only use. `pgrep -a -f volume-monitor` lists only the udisks2 and MTP monitors.
9. **Memory**: leave the machine untouched, then run
   ```sh
   sudo sh /usr/share/almond/tests/measure-memory.sh -w 120 > memory.txt
   ```
   Repeat over 5 fresh boots and report the median, as described in [PERFORMANCE.md](PERFORMANCE.md).
10. Inspect `ss -lntup`, `sudo nft list ruleset` and `sudo aa-status`; record the actual results. Installing nftables does not configure a firewall.
11. Shut down, boot again, and record: VM software and version, firmware mode, RAM, ISO hash, and the result of every step (including failures). Changes are expected to disappear without persistence.

For the **arm64 dev variant**, use an arm64 UEFI VM and expect `uname -m` = `aarch64`; everything else is the same except the BIOS run.

## OptiPlex 390 test plan (second-hand PC)

The first real test PC is a Dell OptiPlex 390 (2011, 64-bit Intel, Intel HD Graphics): a second-hand PC whose internal disk may still hold someone else's data. Read [AALDM-PLAN.md section 15](AALDM-PLAN.md#15-dell-optiplex-390-notes) first. The same rules apply to any second-hand test PC.

**Before starting**

- Boot **only from USB**. Never open, mount, browse or read the internal disk. If the PC's owner agrees, unplug the internal disk's SATA data cable for these tests.
- **Do not install anything to its internal disk.** Wiping (sanitising) that disk needs the owner's explicit permission and is a separate, explicit decision.

**Boot from USB**

1. Write the amd64 ISO to a USB stick on another computer (Rufus in DD mode, balenaEtcher, or `dd` on Linux). This erases the stick only.
2. Power on the OptiPlex and press **F12** for the one-time boot menu.
3. **BIOS vs UEFI**: if the menu offers the USB stick under both "Legacy" and "UEFI", test each, one boot at a time. Record which modes exist and which boot. (Reports disagree about whether this model supports UEFI at all, which is why the ISO is hybrid.)
4. Run the acceptance steps 2–11 above. On this machine also record:
   - `lscpu`, `free -m`, `lspci -nnk` (exact CPU, RAM, GPU and **network card** with its driver);
   - whether X uses the modesetting driver with glamor (`journalctl -b | grep -i -E 'modeset|glamor'`);
   - missing firmware messages (`journalctl -k | grep -i firmware`); if the network card does not work, try a build with `ALMOND_FIRMWARE=all` and compare;
   - five memory reports (step 9), plus one with Firefox open on one page.
5. **Check that no internal disk is mounted**, right after the desktop appears and again at the end: run `findmnt` and `lsblk -f` and confirm that no partition of the internal disk has a mount point (only the USB stick, the live system's own mounts, tmpfs/overlay and zram may appear). These commands only list devices, mount points and filesystem labels; they open no file on the disk. Do not run anything else against the internal disk. If an internal partition is mounted, stop, unmount it without opening any file (`sudo umount <mount point>`), and report it as a bug.
6. In the live session, never open, mount or browse the internal drive, even if it is listed under Devices in the file manager. Do not run any installer.

## Troubleshooting

- **Refusal on macOS or another OS**: expected guard. Build inside a Debian 13 machine.
- **"this host is arm64 but ALMOND_ARCH is amd64"** (or the reverse): build on a host of the target architecture; cross-building is not supported yet.
- **Missing package or repository errors**: inspect `build.log`; never disable signature verification to force a build. The package names were checked against trixie on 2026-10-14 (AALDM-PLAN appendix A); a later Debian point release can rename or remove packages.
- **Unsupported live-build options**: keep `configure.log` and the installed live-build version (`build-tool-versions.txt`); compare with the live-build manual for that version before changing options.
- **A feature is missing after boot** (no icons, a program does not start): the image is built without Recommends, so a needed package may not be in the list. Look up the program's Recommends on packages.debian.org, check `package-manifest.txt`, and report it.
- **No bootable device**: check the firmware mode (BIOS/UEFI) of the VM or PC and that the ISO (or USB stick) is attached first in the boot order.
- **Black screen or no desktop**: check the VM's graphics controller; on real hardware try the boot menu's failsafe entry; collect `journalctl -b` from a text console (Ctrl+Alt+F2).
- **Disk space**: give the build VM more storage; failed attempts are kept on purpose. Inspect before removing any attempt.

Next milestone: one successful build and one recorded boot test in each firmware mode, before any visual work is called done.
