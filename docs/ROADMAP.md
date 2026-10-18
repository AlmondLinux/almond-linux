# Milestones

No deadline is promised before a first timed build.

Status words: **Planned** · **Implemented (source exists, untested)** · **Tested** · **Released**. The per-component status, on the ladder PLANNED → DESIGNED → IMPLEMENTED → TESTED → APPROVED, is kept in [PROJECT_STATUS.md](PROJECT_STATUS.md).

| Version | Objective | Status | Required evidence |
|---|---|---|---|
| 0.1 "Marcona" | First bootable **AALDM** ISO for 64-bit PCs (amd64, hybrid BIOS+UEFI live image; LXQt + Openbox on X11). An arm64 build exists only as a development variant for VMs | Implemented (source exists, untested) | ISO hash, build log, package manifest, boot in BIOS and UEFI mode, repeat boot, networking and terminal checks, memory reports (tests/measure-memory.sh, 5 boots) |
| 0.2 "Largueta" | Custom Almond branding, wallpaper, themes, and system identity | Planned (the Almond Pure assets themselves: Implemented (source exists, untested)) | Original licensed logo/wallpaper, light/dark palette and contrast review, screenshots |
| 0.3 "Valencia" | Customized desktop experience | Planned | Layout, launcher, settings, software-management usability and regression checks |
| 0.5 | Graphical installer and testing (installable preview) | Planned | Disposable-disk installs, account/permission tests, persistent updates, bootloader and recovery validation, security review |
| 1.0 | First stable public release | Planned | Published support matrix, maintained updates, release/source/license materials, reproducible build instructions and support process |

## AALDM phases (mapped to the versions above)

The owner's ten AALDM phases, in order. **No phase is complete.** Phase 1 is 0.1 "Marcona"; the versions for phases 2–10 are a **provisional** mapping, to be confirmed by the owner. Status and required evidence per phase: [AALDM-PLAN.md section 14](AALDM-PLAN.md#14-phases-mapped-to-the-roadmap).

| Phase | Owner's phase | Version (2–10 provisional) | Status |
|---|---|---|---|
| 1 | Bootable Debian-based Almond AALDM ISO | 0.1 "Marcona" | Implemented (source exists, untested) |
| 2 | Apply official Almond branding | 0.2 "Largueta" | Implemented (source exists, untested); identity package Planned |
| 3 | Integrate Almond Icons and Almond Fold | 0.2 "Largueta" | Implemented (source exists, untested) |
| 4 | Apply Almond Pure window themes | 0.2 "Largueta" | Implemented (source exists, untested) |
| 5 | Implement the approved launcher prototype | 0.3 "Valencia" | Implemented (source exists, untested) |
| 6 | Integrate Almond Files | 0.3 "Valencia" | Implemented (source exists, untested) for the PCManFM-Qt defaults; the rest Planned |
| 7 | Implement customization options | 0.3 "Valencia" | Planned |
| 8 | Test on low-end hardware | 0.3 "Valencia" → 0.5 (first measurements are part of 0.1's evidence) | Planned (tools: Implemented (source exists, untested)) |
| 9 | Optimize performance | 0.5 | Planned |
| 10 | Prepare a stable preview release | 0.5 (1.0, the first stable public release, follows) | Planned |

First evidence (2026-10-17): the AALDM ISO was built and booted in VirtualBox in BIOS and UEFI mode ([results](../tests/results/2026-10-17-vm/RESULTS.md)). Phase 1 is not complete: real hardware, the 5-boot memory median and the remaining acceptance checks are still open.

Native Apple Silicon installation is a separate hardware-dependent workstream, not promised by any version number. Do not start with Mac-chip-specific kernel development.

Brand direction: the owner's almond logo (adopted 2026-10-14) and palette — brown #8B5A2B, almond beige #D2A679, cream #F5DEB3, dark brown #2B2118. Test contrast before adopting new colour pairs.

Editions (decided 2026-10-14): **AALLDM — A All Large Linux Distribution Model** (large edition: fuller, modern desktop for newer PCs) and **AALDM — A All Little Distribution Model** (little edition: lighter system for older and low-power 64-bit PCs). Debian 13 no longer supports installing on 32-bit PCs (i386), so AALDM needs a 64-bit PC (amd64).

AALDM decisions (2026-10-14): AALDM reaches 0.1 first, on amd64. Provisional stack, approved by the owner for evaluation: LXQt + Openbox + X11 with LightDM; first real test PC: a Dell OptiPlex 390. Targets, not guarantees: idle RAM under 300 MB, usable on 1 GB RAM where feasible, minimal idle CPU, low GPU needs. The earlier 0.1 draft (Xfce on an ARM64 VM) was replaced; arm64 remains only as a development variant. Still open: AALLDM's desktop, minimum hardware per edition, CPU architectures for AALLDM.

Release codenames (approved 2026-10-14): Spanish almond varieties. 0.1 "Marcona", 0.2 "Largueta", 0.3 "Valencia". 0.5 and 1.0 not named yet.

## Long-term direction: independence (decided 2026-10-14)

Debian first, then independent. Versions 0.1 to 1.0 are built on Debian Stable. After that, Almond plans to replace what it borrows, one layer at a time (no dates promised):

1. **Own package repository** for Almond-made software only (branding, settings, tools, installer), signed with an Almond key, sitting on top of Debian.
2. **Own build system**: rebuild packages from source on Almond infrastructure, starting with the ones Almond changes; track Debian security updates in the meantime.
3. **Fully independent**: Almond's own package set and repositories, no longer based on Debian.

What independence costs (so the plan stays honest): every package then needs its own maintenance, security fixes, build servers and mirrors. This is the main reason most distributions stay derivatives. Each step should only start when the previous one is working and someone can maintain it.

## AALDM goal: a better light desktop than Linux Mint Xfce

Ambition (owner, 2026-10-14): the little edition should be good enough that people choose it over Linux Mint's lightweight Xfce edition. This is a target, not a claim. Nothing comparing Almond with Mint is published until it has been measured.

How it will be earned:

1. **Baseline first.** Install the current Linux Mint Xfce edition in a VM and record its numbers. Same VM settings for every test (CPU count, RAM, disk, display). Record versions and dates.
2. **Measure the same things on AALDM, same VM:**
   - idle RAM after login (`tests/measure-memory.sh`, 120 s after login, median of 5 boots; method in [PERFORMANCE.md](PERFORMANCE.md))
   - boot time to usable desktop (`systemd-analyze` plus a stopwatch to first usable desktop)
   - installed disk size and ISO size
   - number of background services (`systemctl list-units --type=service --state=running`)
   - a usability pass: first-boot steps, installing an app, updating, connecting to Wi-Fi
3. **Set targets after the baseline** (for example, clearly lower idle RAM and fewer background services), not before.
4. **Lightness alone will not win.** Mint is strong on polish and tools: update manager, software manager, driver manager, Timeshift snapshots, and a large community. AALDM needs answers for updates, installing software and recovery too, or people will not switch.
5. **Publishing.** Only publish numbers with the method, versions and raw results, so anyone can repeat them. Comparisons must be objective and verifiable (EU comparative-advertising rules). "Linux Mint" is a trademark of its owners and must only be named factually.

Future directories are created only when needed: packages/ for maintained .deb packages, installer/ for installer integration. (branding/, desktop/ and tests/ now exist.) Generated builds stay ignored; release binaries belong in a release store, not Git history.

## Development record — 2026-10-14 (first draft, ARM64; superseded by the AALDM entry below)

Implemented: live-build ARM64 configuration, desktop package list, image identity hook, guarded build wrapper, architecture and build documentation.

Verified locally (2026-10-14): shell syntax (`sh -n`), and that `scripts/build.sh` refuses to run on a non-Linux host without creating any files. Not verified: package resolution, image generation, bootability, network operation, security defaults, installation, Secure Boot or reproducibility.

Repository practice: use a dedicated GitHub repository containing only Almond files; meaningful commits, reviewed changes, dated decision records, signed release tags and externally stored release hashes. Git dates alone are editable and do not prove exclusive ownership. Published 2026-10-14: https://github.com/AlmondLinux/almond-linux (this repository, MIT License) and https://github.com/AlmondLinux/almondlinux.github.io (the website).

## Development record — 2026-10-14 (AALDM)

Implemented (source exists, untested): AALDM build configuration (`auto/config` with `ALMOND_EDITION`, `ALMOND_ARCH`, `ALMOND_FIRMWARE`; amd64 hybrid BIOS+UEFI ISO, arm64 dev variant; `main non-free-firmware`; no Recommends), package list `config/package-lists/aaldm.list.chroot` (replaces the Xfce draft `desktop.list.chroot`, which was removed), desktop hook `0200-almond-desktop`, asset staging and manifest/hash recording in `scripts/build.sh`, `tests/measure-memory.sh`, and the plan and budgets in [AALDM-PLAN.md](AALDM-PLAN.md) and [PERFORMANCE.md](PERFORMANCE.md).

Verified locally (2026-10-14, on macOS): `sh -n` and `dash -n` for every shell script; `scripts/build.sh` refuses to run on macOS and creates no files; every package name exists in Debian 13 trixie (Debian's madison API; table in AALDM-PLAN appendix A); the staging step and the 0200 hook were run in sandboxes with stand-in tools (no live-build, no chroot); `measure-memory.sh` was run against a synthetic `/proc` tree. Not verified: package resolution, image generation, bootability, the desktop session, memory use, networking, security defaults, installation, Secure Boot or reproducibility.

Corrections (2026-10-14, source only; nothing booted): Debian 13's `lxqt-globalkeys` installs `/etc/xdg/lxqt/globalkeyshortcuts.conf` as a directory, so the Super-key file is now staged to `/usr/share/almond/lxqt/` and the 0200 hook merges it with Debian's default shortcuts into a plain file (verified against the Debian file list and packaging; the merge was run in a macOS sandbox with stub tools). The hook also disables the GOA, AFC and gphoto2 gvfs volume monitors with `dpkg-divert`. PCManFM-Qt no longer mounts volumes at login or shows an autorun dialog. The launcher window has square corners (no compositor), passes its mode labels on the rofi command line and keeps its pid file out of `/tmp`. The AALDM phases are now the owner's ten phases. Status of all of it: Implemented (source exists, untested).


### 2026-10-18 — Almond Duo app

T-0012: local Almond Duo app implemented and tested on macOS; see ai-bridge/reports/T-0012-impl-1.md for exact test scope. Pending owner review; no OS component approval implied.
