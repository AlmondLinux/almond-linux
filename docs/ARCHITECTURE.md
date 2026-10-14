# Architecture decision 0001 — initial ARM64 VM preview

Status: proposed target with initial build configuration; not build-validated.

## Concept and scope

Almond can have its own identity while using Debian's kernel, packages and security infrastructure. A sustainable distribution requires ongoing maintenance, update tests, source/license compliance and support—not just a branded ISO. Keep modifications small enough for one maintainer to audit.

## Base comparison

| Base | Strengths | Costs and fit |
|---|---|---|
| Debian stable | Stable package versions, large archive, APT, ARM64, mature live-build customization | Older applications than rolling bases; new hardware needs verification. Best initial fit. |
| Ubuntu LTS | Broad ecosystem, ARM64 and established updates; desktop integration | Check derivative branding/redistribution policy and coverage for each package; additional upstream choices to maintain. Viable second choice. |
| Arch | Extensive customization and current packages | Rolling changes increase regression work. Official Arch targets x86-64; ARM is a separate project. Poor fit for this first ARM64 release. |
| Fedora | Current desktop technologies, ARM offerings, SELinux and established packaging | Faster release turnover means more frequent migrations. Native Apple support is a distinct Asahi effort, not generic Fedora compatibility. |
| Linux From Scratch | Excellent education and maximum assembly control | A build guide, not a ready-maintained package/security infrastructure. Too much ongoing integration for this first release. |

All require review of constituent software licenses. None transfers blanket rights to upstream names or artwork. None guarantees drivers for every ARM device or support for Almond's modifications.

Sources: [Debian releases](https://www.debian.org/releases/), [Live manual](https://live-team.pages.debian.net/live-manual/html/live-manual.en.html), [Ubuntu releases](https://documentation.ubuntu.com/project/release-team/ubuntu-releases/), [Arch](https://archlinux.org/about/), [Fedora lifecycle](https://docs.fedoraproject.org/en-US/releases/lifecycle/), [LFS](https://www.linuxfromscratch.org/).

## Version 0.1 components

- Debian 13 trixie ARM64; stock Debian kernel, systemd, APT/dpkg.
- live-build creates an ISO with GRUB EFI and a compressed live filesystem.
- XFCE with LightDM for this first VM preview: modest resource use, existing settings, accessibility facilities and customization. Accessibility still needs hands-on testing. This is a choice for the 0.1 preview image only; the desktop for each edition (AALLDM, AALDM) is still undecided.
- NetworkManager, Firefox ESR, terminal, text editor and Git.
- Main archive only for the VM preview; evaluate redistributable firmware per future physical target.
- Debian security and updates enabled; require authenticated APT metadata. Debian normally authenticates repository metadata and package hashes, not separate signatures on every .deb.
- Almond identity supplied by an image hook. Before installed releases, move identity into a maintained Debian package and test base-files upgrades.
- No custom kernel, package manager, AI dependency, external Almond repository or disk installer in 0.1.

## Security and lifecycle boundaries

Live sessions are disposable and can have autologin/passwordless administrative access through live-config. Never ship those settings as installed-user defaults. Do not add remote login services. Verify all listening services, permissions, APT sources, AppArmor and the effective firewall in the booted image. Installing nftables does not configure or activate a firewall: rules and network regression testing remain planned. Secure Boot remains unverified.

Updates in a nonpersistent live session disappear on reboot. Refresh the ISO for durable live-media fixes. Installed-system update persistence, encrypted installation, user creation and recovery belong to the installer milestone. Own packages eventually need an authenticated repository and signing-key recovery/rotation procedures.

Preserve package manifests, exact build-tool versions, logs, checksums, source availability and commit IDs. Repeatable instructions do not establish bit-for-bit reproducibility; archives change. Snapshot inputs and compare independent builds before making that claim.

## Principal risks

1. Naming: complete trademark-register checks before investing money in branding.
2. Native Apple Silicon hardware: upstream Asahi Linux support for recent Mac chips has substantial gaps; a VM does not test physical Mac support.
3. Solo-maintainer capacity: avoid forking security-sensitive upstream packages; document support limits.
4. Installer data loss: test exclusively on disposable virtual disks until recovery tests pass.
5. Licensing/source delivery: inventory packages and corresponding sources before distributing binaries.
6. Image identity and upgrade regressions: package the branding before stable installed releases.

Reference: [Asahi Linux feature support for recent Mac chips](https://github.com/AsahiLinux/docs/blob/main/docs/platform/feature-support/m4.md), checked 2026-10-14.
