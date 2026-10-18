# Project status

The single place that says how far each part of Almond Linux has got. Humans and AI agents (Claude, OpenAI models) read this first and keep it true.

Last reviewed: 2026-10-18. Source of truth for code: the Git history and pull requests of this repository. Where this file and the code disagree, the code is what will be tested and this file must be fixed.

## Status ladder

Every component sits on exactly one rung. A rung is only claimed when its evidence exists.

| Rung | Meaning | Evidence needed |
|---|---|---|
| **PLANNED** | Named and wanted. No agreed design yet. | A line in this file or the roadmap |
| **DESIGNED** | A written spec or approved mockup exists. No code. | Link to the spec / mockup and the date the owner agreed it |
| **IMPLEMENTED** | Source exists in this repository. **Has not run** on a real or virtual Almond system. | Commit or PR |
| **TESTED** | Ran on a built Almond image (VM or hardware) and the test results are recorded. | Test report with date, machine, build commit, ISO hash |
| **APPROVED** | The owner has signed off on the tested result. Only the owner can set this. | Owner's decision record or PR approval |

Older documents use the words *Planned · Implemented (source exists, untested) · Tested · Released*. "Implemented (source exists, untested)" is the same as **IMPLEMENTED** here. *Released* comes after APPROVED and means a published release.

**TESTED (VM)** below means: ran in a VirtualBox VM and the result is recorded. It says nothing about real hardware. Where only part of a component was checked, the notes say which part.

Rules:

- Never move a component up a rung without its evidence. Never mark unfinished work as complete.
- An AI agent may move a component to DESIGNED, IMPLEMENTED or TESTED (with evidence). **Only the owner moves anything to APPROVED.**
- When a rung is lowered (a test failed, a design was rejected), say so and why in the change log at the bottom.

## Overall

**The first AALDM ISO was built and booted in VirtualBox on 2026-10-17, in legacy BIOS and UEFI mode.** Build commit `6401433`, ISO SHA256 `7129bf3e3f7bededa373fe74dcc1e742891fd4d4c5dd7488581b5360d653fe9d` (845,152,256 bytes). Full report: [tests/results/2026-10-17-vm/RESULTS.md](../tests/results/2026-10-17-vm/RESULTS.md).

- Nothing has run on real hardware. Nothing is APPROVED. Nothing is released.
- The 300 MB idle-RAM target was **not met** in the first single-boot measurements (413 MiB at 2 GB RAM, 393 MiB at 1 GB).
- Bugs found in that test are listed under [Known bugs](#known-bugs-and-risks) and turned into backlog tasks.

## Vision

Almond Linux is an independent Linux distribution project: simple, stable, fast, and yours. Debian Stable first (0.1 → 1.0), then independence one layer at a time (own package repository → own build system → no longer Debian-based). Details: [ROADMAP.md](ROADMAP.md).

## Editions

Edition names confirmed by the owner on 2026-10-18 ([D-0002](../ai-bridge/decisions/D-0002-edition-names.md)).

| Edition | Meaning | Rung | Notes |
|---|---|---|---|
| **AALDM** — A All Little Distribution Model | Light edition for older and low-power 64-bit PCs | **TESTED (VM)** — first boot only | Debian 13 + LXQt + Openbox + X11 + LightDM, amd64 hybrid BIOS/UEFI ISO. Built and booted 2026-10-17 (see Overall). Plan: [AALDM-PLAN.md](AALDM-PLAN.md) |
| **AALLDM** — A All Large Linux Distribution Model | Large, modern edition for newer PCs | **DESIGNED** (visual baseline approved) | Owner approved the final **Almond Fusion** design (based on Design 03 — Almond Custom) on 2026-10-18 ([D-0003](../ai-bridge/decisions/D-0003-aalldm-visual-design-approved.md)): graphite/charcoal with gold and silver accents, right-side translucent Almond Glass bar, widgets, Almond Spaces, Chrome as preferred browser (redistribution unresolved). Mockup images not in this repository yet. **No AALLDM software exists.** Base system, minimum hardware and CPU architectures undecided |

## Components

| Component | What it is | Rung | Evidence / notes |
|---|---|---|---|
| Build configuration (live-build) | `auto/config`, package list, hooks, `scripts/build.sh` | **TESTED (VM)** | Built OK on 2026-10-17 in a Debian 13.7 VM (live-build 1:20250505+deb13u1), 0 errors, 765 packages, both hooks ran. Warnings: no zstd (initramfs gzip-compressed) |
| ISO image | Bootable AALDM live ISO | **TESTED (VM)** | Boots to the LXQt desktop with autologin in BIOS (isolinux) and UEFI (GRUB) mode, 2 GB and 1 GB RAM. Not tested: Secure Boot, real hardware, fail-safe and Utilities menu entries |
| Official Almond logo | Owner's brown almond logo | **APPROVED** (as artwork) | Adopted by the owner 2026-10-14. Master: `branding/logo/`. Rules: [DESIGN_RULES.md](DESIGN_RULES.md#logo) |
| Approved visual design — **Almond Pure** | The look of AALDM: flat, warm, no transparency | **DESIGNED** | Owner approved four AI mockups 2026-10-14 (image 1 = priority, image 2 = Super-key launcher). Mockup images are not in this repository. The built desktop has not been compared with the mockups. Owner feedback after the first boot: dislikes the desktop icons; wants a start menu (backlog task) |
| Almond Icons + Almond Fold | Icon theme and folder-colour variants (Blue, Gray, Green, Orange, Plum, Red) | **IMPLEMENTED** (seen running) | Icon caches built in the image and icons visible in the VM, but no icon checks were run. Four launcher tiles show no icon. `tools/check-icons.py` checks the files only |
| **Almond Launcher** ("Almond Launch") | Super-key app launcher (rofi) | **TESTED (VM)** — partly, bugs found | Super opens it, typing filters, Enter starts, Esc closes (BIOS); opens in UEFI too. Bugs: Hibernate highlighted by default, the highlight does not follow the first match, Lock/Hibernate offered without a screen locker, four tiles without icons |
| **Almond Files** | File manager = configured PCManFM-Qt (no custom app) | **IMPLEMENTED** (seen running) | Opened in the VM; none of the [AALDM-PLAN §7](AALDM-PLAN.md#7-file-manager-pcmanfm-qt-feature-map) checks were run. Volume monitors goa/afc/gphoto2 were diverted at build time. A larger "Almond Files Pro — Adaptive Minimalist" design for AALLDM is in the owner's notes (direction chosen, not a spec) |
| **Almond Frame** | Window/widget theming: Openbox themes Light/Dark/Ocean, Qt palettes, LXQt QSS | **IMPLEMENTED** (seen running) | LXQt with Openbox confirmed running; no theme or contrast checks done. "Unified Frame" (integrated headers) is an AALLDM design direction in the owner's notes |
| Wallpapers, boot artwork, image identity | Branding inside the image | **TESTED (VM)** — partly | Almond boot menus in BIOS and UEFI, `/etc/os-release` = "Almond Linux 0.1 Marcona (AALDM development preview)". Bug: the GRUB title overlaps the logo |
| **Almond Glass** | AALLDM: right-side application bar, solid/translucent/frosted/clear styles, adjustable position, opacity, size | **DESIGNED** (part of the approved AALLDM visual design) |  Translucent styles are AALLDM-only: AALDM's rules forbid transparency. Not approved for building ([T-0002](../ai-bridge/tasks/T-0002-confirm-component-definitions.md)) |
| **Almond Spaces** | AALLDM: workspaces with saved layouts, grouping, previews, multi-monitor, restore | **DESIGNED** (visual only, part of the approved AALLDM design) | Restore and multi-monitor behaviour still open. Not approved for building (T-0002) |
| **Almond Bridge** | Windows application compatibility manager for **supported** apps (Wine or Proton as possible engines) | **PLANNED** | No engine chosen, no support list. Never promise universal Windows compatibility. Not the same thing as the *Almond AI Bridge* (the developer tooling in `ai-bridge/`). (T-0002) |
| **Almond Shield** | **Optional** antivirus and security center (scanning, quarantine, warnings) | **PLANNED** — proposal | The base OS must stay secure without it. Today's security defaults: [ARCHITECTURE.md](ARCHITECTURE.md#security-and-lifecycle-boundaries); nftables is installed but has no rules. (T-0002) |
| **Performance modes** | Presets **Potato / Medium / High**, user-overridable | **PLANNED** — design requirement | No figures exist. Open: do they apply to AALDM? Medium/High include transparency and animation, which AALDM's rules forbid. (T-0002) |
| Customisation | LXQt/Openbox settings tools now; "Almond Personalize" app later | **PLANNED** | [AALDM-PLAN §10](AALDM-PLAN.md#10-customisation). Requirements in [DESIGN_RULES.md](DESIGN_RULES.md#customisation-requirements) |
| Memory measurement | `tests/measure-memory.sh` | **TESTED (VM)** | Ran in the live image on 2026-10-17. Possible bug: counts 72 processes as unreadable while reporting 0 kernel threads |
| Installer | "Install Almond Linux" with Calamares (Debian's), Almond settings and branding | **IMPLEMENTED** | Task T-0007, [INSTALLER.md](INSTALLER.md). Never built or run. Main risk: the bootloader is installed from a package pool on the ISO, whose layout is unverified. Test plan: disposable VirtualBox disks only. Milestone 0.5 |
| Website | almondlinux.github.io | Live | Separate repository `AlmondLinux/almondlinux.github.io`. Still says no ISO has been built: needs updating |
| Almond AI Bridge | Developer workflow for Claude + OpenAI models (`ai-bridge/`) | **IMPLEMENTED** | Free PR checks ran on GitHub (PR #1, passed). OpenAI API review is off until the owner configures it. See [ai-bridge/README.md](../ai-bridge/README.md) |

## Performance targets (AALDM)

Targets: idle RAM under 300 MB used 120 s after login, usable on 1 GB RAM where feasible, minimal idle CPU, low GPU needs. Method: [PERFORMANCE.md](PERFORMANCE.md).

First measurements (2026-10-17, one boot each, VirtualBox, a QTerminal window open, **not** the 5-boot median the method asks for):

| VM RAM | Used (MemTotal − MemAvailable) | Desktop session PSS | Largest processes (PSS) |
|---|---|---|---|
| 2048 MB | **413.2 MiB** | 243.7 MiB | Xorg 93.9, LXQt session + panel 53.6, pcmanfm-qt 18.7, PulseAudio 17.5, gvfs + udisks2 15.7 |
| 1024 MB | **393.2 MiB** | 244.5 MiB | same pattern |

So the 300 MB target is **not met** yet. The 1 GB run had four 60-second VM clock stalls. Raw reports: [tests/results/2026-10-17-vm/](../tests/results/2026-10-17-vm/). No comparison with other distributions is published until measured with the full method ([ROADMAP.md](ROADMAP.md#aaldm-goal-a-better-light-desktop-than-linux-mint-xfce)).

## Hardware testing

| Machine | Role | Status | Rules |
|---|---|---|---|
| VirtualBox 7.2.20 on the owner's Windows 11 PC (i9-13900K) | Build VM (Debian 13.7, 1 CPU) + test VM (2 CPUs, 2 GB / 1 GB, no disk) | **First run done 2026-10-17** | [PC-SETUP.md](PC-SETUP.md). The build VM froze with 4 CPUs (VirtualBox on the Windows hypervisor); 1 CPU worked |
| Dell OptiPlex 390 (2011, Intel, integrated graphics) | First real test PC | Not started | **USB live boot only.** The internal disk still holds old data: never mount, read or write it; wipe only with the owner's explicit OK |
| Apple Silicon Mac (UTM/Parallels, arm64) | Development variant only | Not started | Not a target. Cannot build the amd64 ISO |

## Known bugs and risks

Found in the 2026-10-17 VM test ([RESULTS.md](../tests/results/2026-10-17-vm/RESULTS.md), "Problems and bugs found"):

1. **Launcher:** "Hibernate" is highlighted when it opens (2 of 3 times), so pressing Enter at once could hibernate. After typing, the highlight does not move to the first match. Four tiles have no icon. Long names are cut off.
2. **Launcher:** offers "Lock Screen" and "Hibernate", but no screen locker is installed.
3. **First login:** two LXQt power-management pop-ups ("No battery!", first-run notice).
4. **UEFI GRUB menu:** the title is drawn over the almond logo.
5. **No zstd** in the image, so the initramfs is gzip-compressed (effect not measured).
6. **measure-memory.sh:** possibly counts kernel threads as "unreadable".
7. **Docs vs reality:** BUILD.md recommends 4 vCPUs (froze on this PC); AALDM-PLAN names Firefox ESR 140 (image has 153.5); PC-SETUP.md runs measure-memory.sh without `-w 120`.
8. **Idle memory** above the 300 MB target (see Performance targets).

Owner feedback after the first look: does not like the desktop icons (Home, Computer, Trash); wants a start menu with categories and settings.

Known risks, from [AALDM-PLAN §16](AALDM-PLAN.md#16-open-decisions-and-risks):

1. Building without Recommends may leave out something a feature silently needs.
2. The 0200 hook replaces a directory owned by `lxqt-globalkeys` with a file; package upgrades on an installed system may fail (the build itself worked).
3. Naming: OEPM/EUIPO trademark searches not done; similarity to "AlmaLinux" is the main risk.

## Task board

Generated from `ai-bridge/tasks/` by `ai-bridge/bridge handoff`. Do not edit between the markers.

<!-- bridge:tasks:start -->
| Task | Title | Status | Assignee | Review rounds | PR |
|---|---|---|---|---|---|
| [T-0003](../ai-bridge/tasks/T-0003-launcher-fixes-from-the-first-vm-test.md) | Launcher fixes from the first VM test | backlog | claude | 0/2 |  |
| [T-0004](../ai-bridge/tasks/T-0004-first-boot-polish-and-docs-fixes-from-the-first.md) | First-boot polish and docs fixes from the first VM test | backlog | claude | 0/2 |  |
| [T-0005](../ai-bridge/tasks/T-0005-owner-feedback-desktop-icons-and-a-start-menu.md) | Owner feedback: desktop icons and a start menu | backlog | claude | 0/2 |  |
| [T-0002](../ai-bridge/tasks/T-0002-confirm-component-definitions.md) | Confirm component definitions, edition names and AALLDM design status | ready | owner | 0/2 |  |
| [T-0006](../ai-bridge/tasks/T-0006-almond-a-terminal-system-information-command.md) | almond: a terminal system-information command | ready | claude | 0/2 |  |
| [T-0008](../ai-bridge/tasks/T-0008-website-status-update-for-the-first-vm-boot.md) | Website status update for the first VM boot | ready | claude | 0/2 |  |
| [T-0007](../ai-bridge/tasks/T-0007-install-almond-linux-option-with-calamares.md) | Install Almond Linux option with Calamares | review | claude | 0/2 |  |
| [T-0001](../ai-bridge/tasks/T-0001-first-iso-build-and-vm-boot.md) | First AALDM ISO build and VM boot test | needs-owner | claude-pc | 0/2 |  |
<!-- bridge:tasks:end -->

## Change log

- 2026-10-18 — Owner decisions: edition names confirmed (D-0002); AALLDM visual design approved, PLANNED → DESIGNED, and with it the look of Almond Glass and Spaces (D-0003). Their behaviour (restore, multi-monitor, styles) still needs a spec.
- 2026-10-18 — Recorded the 2026-10-17 VM build and boot test: build configuration, ISO, launcher (partly), boot artwork (partly) and memory script moved to TESTED (VM); AALDM edition to TESTED (VM), first boot only. Added the owner's definitions of Glass, Spaces, Bridge, Shield and performance modes from the owner's design notes (the 2026-10-17 entry wrongly said they appeared nowhere: they were in the owner's notes, not in this repository). AALLDM: design in progress, approval to be confirmed by the owner.
- 2026-10-17 — File created from README, ROADMAP and AALDM-PLAN as of commit 6401433. Glass, Spaces, Bridge, Shield and performance modes added as PLANNED / not specified (they appear in the owner's brief but nowhere in the repository).
