# Milestones

No deadline is promised before a first timed build.

| Version | Objective | Status | Required evidence |
|---|---|---|---|
| 0.1 "Marcona" | First bootable Debian-based ISO (ARM64 VM live desktop) | In progress | ISO hash, build log, package manifest, repeat boot, networking and terminal checks |
| 0.2 "Largueta" | Custom Almond branding, wallpaper, themes, and system identity | Planned | Original licensed logo/wallpaper, light/dark palette and contrast review, screenshots |
| 0.3 "Valencia" | Customized desktop experience | Planned | Layout, launcher, settings, software-management usability and regression checks |
| 0.5 | Graphical installer and testing (installable VM preview) | Planned | Disposable-disk installs, account/permission tests, persistent updates, bootloader and recovery validation, security review |
| 1.0 | First stable public release | Planned | Published support matrix, maintained updates, release/source/license materials, reproducible build instructions and support process |

Native Apple Silicon installation is a separate hardware-dependent workstream, not promised by any version number. Do not start with Mac-chip-specific kernel development.

Brand direction: the owner's almond logo (adopted 2026-10-14) and palette — brown #8B5A2B, almond beige #D2A679, cream #F5DEB3, dark brown #2B2118. Test contrast before adopting new colour pairs.

Editions (decided 2026-10-14): **AALLDM — A All Large Linux Distribution Model** (large edition: fuller, modern desktop for newer PCs) and **AALDM — A All Little Distribution Model** (little edition: lighter system for older and low-power PCs). Open decisions: desktop environment per edition, minimum hardware, CPU architectures per edition, and which edition reaches 0.1 first. Note: Debian 13 no longer supports installing on 32-bit PCs (i386), so a Debian 13-based AALDM would need a 64-bit PC (amd64); the drafted 0.1 configuration targets ARM64 virtual machines only.

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
   - idle RAM after login (`free -m`, 2 minutes after login, average of 5 boots)
   - boot time to usable desktop (`systemd-analyze` plus a stopwatch to first usable desktop)
   - installed disk size and ISO size
   - number of background services (`systemctl list-units --type=service --state=running`)
   - a usability pass: first-boot steps, installing an app, updating, connecting to Wi-Fi
3. **Set targets after the baseline** (for example, clearly lower idle RAM and fewer background services), not before.
4. **Lightness alone will not win.** Mint is strong on polish and tools: update manager, software manager, driver manager, Timeshift snapshots, and a large community. AALDM needs answers for updates, installing software and recovery too, or people will not switch.
5. **Publishing.** Only publish numbers with the method, versions and raw results, so anyone can repeat them. Comparisons must be objective and verifiable (EU comparative-advertising rules). "Linux Mint" is a trademark of its owners and must only be named factually.

Future directories are created only when needed: packages/ for maintained .deb packages, branding/ for actual artwork, installer/ for installer integration, tests/ for automated acceptance checks. Generated builds stay ignored; release binaries belong in a release store, not Git history.

## Development record — 2026-10-14

Implemented: live-build ARM64 configuration, desktop package list, image identity hook, guarded build wrapper, architecture and build documentation.

Verified locally (2026-10-14): shell syntax (`sh -n`), and that `scripts/build.sh` refuses to run on a non-Linux host without creating any files. Not verified: package resolution, image generation, bootability, network operation, security defaults, installation, Secure Boot or reproducibility.

Repository practice: use a dedicated GitHub repository containing only Almond files; meaningful commits, reviewed changes, dated decision records, signed release tags and externally stored release hashes. Git dates alone are editable and do not prove exclusive ownership. Published 2026-10-14: https://github.com/AlmondLinux/almond-linux (this repository, MIT License) and https://github.com/AlmondLinux/almondlinux.github.io (the website).
