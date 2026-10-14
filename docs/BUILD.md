# First ARM64 build and VM test

## Objective

Produce an experimental Almond 0.1 live ISO, then prove it boots in an ARM64 UEFI VM. These instructions and scripts have NOT produced an ISO yet.

## Host and tools

Development happens on an Apple Silicon Mac, but the build itself must run inside a Linux virtual machine. No working Linux build VM has been set up yet.

Create a dedicated Debian 13 ARM64 virtual machine (for example with UTM/QEMU or Parallels Desktop) using an official Debian installer. Verify installer checksums/signatures using Debian's published instructions. Use 4 virtual CPUs, 8 GB RAM and an 80 GB virtual disk as starting allocations. These are recommendations, not measured minimum requirements. Keep builds on the VM's Linux filesystem, not a macOS shared folder.

The build uses root inside this dedicated VM because live-build creates mounts and chroots. It must not run directly on macOS. Do not attach physical disks.

## Commands inside the Debian build VM

First install the existing Debian tools: live-build orchestrates the image; debootstrap creates the Debian root filesystem; xorriso and squashfs-tools package it; GRUB tools provide ARM64 EFI boot files.

```sh
sudo apt update
sudo apt install live-build debootstrap xorriso squashfs-tools grub-efi-arm64-bin mtools dosfstools ca-certificates git
```

Copy this project into the VM's home directory. From that project directory, the following starts a fresh isolated build attempt and retains logs. It does not erase previous attempts.

```sh
sudo ./scripts/build.sh
```

Expected, not observed: an ISO and SHA256SUMS under `build/attempt.XXXXXX/`. The script records build tool versions there. Preserve live-build's package list alongside the ISO. Check its hash from that output directory:

```sh
sha256sum -c SHA256SUMS
```

A checksum detects changes; it does not authenticate a publisher without a separately trusted signature. Release signing is still planned.

## Acceptance test

Create a second ARM64 UEFI VM with 4 GB RAM, NAT networking, no physical disk access and initially no writable disk. Attach the built ISO.

1. Reach the graphical desktop through the EFI boot menu.
2. Open a terminal: `uname -m` should report `aarch64`.
3. `cat /etc/os-release` should identify Almond 0.1 "Marcona" with Debian lineage (`ID_LIKE=debian`).
4. Check browser HTTPS access and DNS; `nmcli device status` should show connectivity.
5. `sudo apt update` must succeed without unauthenticated repository warnings. Inspect configured suites for trixie, trixie-updates and trixie-security.
6. Exercise terminal, editor, keyboard layout, resolution, clipboard where supported, and basic accessibility.
7. Inspect `ss -lntup`, `sudo nft list ruleset`, and AppArmor status; record actual results. Firewall hardening is not implemented by merely installing nftables.
8. Shut down and boot a second time. Record VM version, firmware settings, ISO hash and results. Changes are expected to disappear without persistence.

## Troubleshooting

- macOS refusal: expected guard; use the Debian guest.
- Wrong architecture: use Debian arm64, not amd64, and an ARM64 EFI VM.
- Missing package or repository errors: inspect build.log and sources; never disable signature verification to force a build.
- Unsupported live-build options: preserve configure.log and installed live-build version; reconcile the packaged tool with its manual before changing options.
- No bootable device: verify EFI firmware, ARM64 image and ISO attachment; inspect the ISO's EFI boot image.
- Black screen: inspect guest display configuration and logs; a virtual display issue does not prove native Mac compatibility.
- Disk space: allocate more VM storage; failed attempts remain deliberately. Inspect before manually removing any attempt.

Next milestone: one successful build and one recorded boot test, before visual customization.
