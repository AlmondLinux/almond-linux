# Architecture decision 0001 — Almond 0.1 base and the AALDM image

Status: proposed target with build configuration; not build-validated. Updated 2026-10-14: the first image is now **AALDM on amd64** (LXQt + Openbox on X11), replacing the earlier draft of an Xfce image for an ARM64 VM. ARM64 remains only as a development variant. Component plan: [AALDM-PLAN.md](AALDM-PLAN.md).

## Concept and scope

Almond can have its own identity while using Debian's kernel, packages and security infrastructure. A sustainable distribution requires ongoing maintenance, update tests, source/license compliance and support—not just a branded ISO. Keep modifications small enough for one maintainer to audit.

## Base comparison

| Base | Strengths | Costs and fit |
|---|---|---|
| Debian stable | Stable package versions, large archive, APT, ARM64, mature live-build customization | Older applications than rolling bases; new hardware needs verification. Best initial fit. |
| Ubuntu LTS | Broad ecosystem, ARM64 and established updates; desktop integration | Check derivative branding/redistribution policy and coverage for each package; additional upstream choices to maintain. Viable second choice. |
| Arch | Extensive customization and current packages | Rolling changes increase regression work. Official Arch targets x86-64; ARM is a separate project. Poor fit for a stability-focused first release (the first draft targeted ARM64, where Arch is a separate project; the AALDM target is now amd64). |
| Fedora | Current desktop technologies, ARM offerings, SELinux and established packaging | Faster release turnover means more frequent migrations. Native Apple support is a distinct Asahi effort, not generic Fedora compatibility. |
| Linux From Scratch | Excellent education and maximum assembly control | A build guide, not a ready-maintained package/security infrastructure. Too much ongoing integration for this first release. |

All require review of constituent software licenses. None transfers blanket rights to upstream names or artwork. None guarantees drivers for every ARM device or support for Almond's modifications.

Sources: [Debian releases](https://www.debian.org/releases/), [Live manual](https://live-team.pages.debian.net/live-manual/html/live-manual.en.html), [Ubuntu releases](https://documentation.ubuntu.com/project/release-team/ubuntu-releases/), [Arch](https://archlinux.org/about/), [Fedora lifecycle](https://docs.fedoraproject.org/en-US/releases/lifecycle/), [LFS](https://www.linuxfromscratch.org/).

## Version 0.1 components

- Debian 13 trixie, **amd64** (the AALDM target: older and weaker 64-bit PCs); **arm64** only as a development variant for VMs on Apple Silicon. Stock Debian kernel, systemd, APT/dpkg.
- live-build creates a **hybrid ISO**: isolinux for legacy-BIOS PCs and GRUB EFI for UEFI PCs, bootable from DVD or USB (arm64: GRUB EFI only). Compressed live filesystem.
- AALDM desktop (provisional, owner-approved for evaluation): **LXQt 2.1 + Openbox on X11** with LightDM and lightdm-gtk-greeter, no compositor, no animations, flat graphics. Chosen for low resident memory with a complete desktop (panel, settings, polkit agent, power management); Xfce, plain Openbox + tint2 and others were evaluated in [AALDM-PLAN.md](AALDM-PLAN.md). The desktop for AALLDM is still undecided. Accessibility still needs hands-on testing.
- NetworkManager (nm-tray), PulseAudio, Firefox ESR, PCManFM-Qt, QTerminal, FeatherPad, rofi-based Almond Launcher. Git and curl are no longer in the image.
- Archive areas `main non-free-firmware`, as Debian's own images do since Debian 12; only the named firmware packages are installed by default. Built **without Recommends** so that every package is chosen on purpose.
- Debian security and updates enabled; require authenticated APT metadata. Debian normally authenticates repository metadata and package hashes, not separate signatures on every .deb.
- Almond identity supplied by an image hook (`0100`), desktop defaults by a second hook (`0200`). Before installed releases, move identity into a maintained Debian package and test base-files upgrades.
- No custom kernel, package manager, AI dependency, external Almond repository or disk installer in 0.1.

## Security and lifecycle boundaries

Live sessions are disposable and can have autologin/passwordless administrative access through live-config. Never ship those settings as installed-user defaults. Do not add remote login services. Verify all listening services, permissions, APT sources, AppArmor and the effective firewall in the booted image. Installing nftables does not configure or activate a firewall: rules and network regression testing remain planned. Secure Boot remains unverified.

Updates in a nonpersistent live session disappear on reboot. Refresh the ISO for durable live-media fixes. Installed-system update persistence, encrypted installation, user creation and recovery belong to the installer milestone. Own packages eventually need an authenticated repository and signing-key recovery/rotation procedures.

Preserve package manifests, exact build-tool versions, logs, checksums, source availability and commit IDs. Repeatable instructions do not establish bit-for-bit reproducibility; archives change. Snapshot inputs and compare independent builds before making that claim.

## Principal risks

1. Naming: complete trademark-register checks before investing money in branding.
2. Native Apple Silicon hardware: upstream Asahi Linux support for recent Mac chips has substantial gaps; a VM does not test physical Mac support. (Not a goal; arm64 is only a development variant.)
3. Solo-maintainer capacity: avoid forking security-sensitive upstream packages; document support limits.
4. Installer data loss: test exclusively on disposable virtual disks until recovery tests pass.
5. Licensing/source delivery: inventory packages and corresponding sources before distributing binaries.
6. Image identity and upgrade regressions: package the branding before stable installed releases.
7. Second-hand test hardware: the first real test PC (OptiPlex 390) is a second-hand PC whose internal disk may still hold someone else's data. Boot it from USB only, never mount or read the internal disk, and wipe that disk only with the owner's explicit permission (AALDM-PLAN section 15).
8. Performance targets (idle RAM under 300 MB, 1 GB RAM usable) are targets, not guarantees, until measured with the method in [PERFORMANCE.md](PERFORMANCE.md).

Reference: [Asahi Linux feature support for recent Mac chips](https://github.com/AsahiLinux/docs/blob/main/docs/platform/feature-support/m4.md), checked 2026-10-14.
