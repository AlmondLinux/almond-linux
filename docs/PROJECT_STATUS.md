# Project status

The single place that says how far each part of Almond Linux has got. Humans and AI agents (Claude, OpenAI models) read this first and keep it true.

Last reviewed: 2026-10-17. Source of truth for code: the Git history and pull requests of this repository. Where this file and the code disagree, the code is what will be tested and this file must be fixed.

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

Rules:

- Never move a component up a rung without its evidence. Never mark unfinished work as complete.
- An AI agent may move a component to DESIGNED, IMPLEMENTED or TESTED (with evidence). **Only the owner moves anything to APPROVED.**
- When a rung is lowered (a test failed, a design was rejected), say so and why in the change log at the bottom.

## Overall

**No ISO has been built, booted or released. Nothing is TESTED. Nothing is APPROVED.**

The next real step is the first ISO build and VM boot on the owner's Windows PC ([docs/PC-SETUP.md](PC-SETUP.md)), tracked as task [T-0001](../ai-bridge/tasks/T-0001-first-iso-build-and-vm-boot.md).

## Vision

Almond Linux is an independent Linux distribution project: simple, stable, fast, and yours. Debian Stable first (0.1 → 1.0), then independence one layer at a time (own package repository → own build system → no longer Debian-based). Details: [ROADMAP.md](ROADMAP.md).

## Editions

| Edition | Meaning | Rung | Notes |
|---|---|---|---|
| **AALDM** — A All Little Distribution Model | Light edition for older and low-power 64-bit PCs | **IMPLEMENTED** (build config, untested) | First edition. Debian 13 + LXQt + Openbox + X11 + LightDM, amd64 hybrid BIOS/UEFI ISO. Plan: [AALDM-PLAN.md](AALDM-PLAN.md) |
| **AALLDM** — A All Large Linux Distribution Model | Large, modern edition for newer PCs | **PLANNED** | Desktop, minimum hardware and CPU architectures undecided. All AALLDM work is paused until it is designed separately |

## Components

| Component | What it is | Rung | Evidence / notes |
|---|---|---|---|
| Build configuration (live-build) | `auto/config`, package list, hooks, `scripts/build.sh` | **IMPLEMENTED** | Commit 6401433. Checked on macOS only: shell syntax, refusal to run outside Debian 13, every package name exists in trixie |
| ISO image | Bootable AALDM live ISO | **PLANNED** | Never built |
| Official Almond logo | Owner's brown almond logo | **APPROVED** (as artwork) | Adopted by the owner 2026-10-14. Master: `branding/logo/`. Rules: [DESIGN_RULES.md](DESIGN_RULES.md#logo). Its use on boot screens etc. is still IMPLEMENTED only |
| Approved visual design — **Almond Pure** | The look of AALDM: flat, warm, no transparency | **DESIGNED** | Owner approved four AI mockups 2026-10-14 (image 1 = priority, image 2 = Super-key launcher). Mockup images are not in this repository. Rules: [DESIGN_RULES.md](DESIGN_RULES.md) |
| Almond Icons + Almond Fold | Icon theme and folder-colour variants (Blue, Gray, Green, Orange, Plum, Red) | **IMPLEMENTED** | `desktop/icons/`; `tools/check-icons.py` checks the files (not how a desktop renders them) |
| **Almond Launcher** ("Almond Launch") | Super-key app launcher (rofi) | **IMPLEMENTED** | `desktop/launcher/`. Has never run. Lock entry needs a screen locker that 0.1 does not ship |
| **Almond Files** | File manager = configured PCManFM-Qt (no custom app) | **IMPLEMENTED** (defaults only) | Defaults file exists; the rest of [AALDM-PLAN §7](AALDM-PLAN.md#7-file-manager-pcmanfm-qt-feature-map) is PLANNED |
| **Almond Frame** | Window/widget theming: Openbox themes Light/Dark/Ocean, Qt palettes, LXQt QSS | **IMPLEMENTED** | `desktop/openbox/`, `desktop/lxqt/` |
| Wallpapers, boot artwork, image identity | Branding inside the image | **IMPLEMENTED** | `desktop/wallpapers/`, `branding/boot/`, hook 0100 |
| **Almond Glass** | Named by the owner | **PLANNED** — *not specified* | No spec exists in this repository. Note: AALDM's rules forbid transparency and blur, so if "Glass" means a translucent style it can only belong to AALLDM. Owner to define ([T-0002](../ai-bridge/tasks/T-0002-define-unspecified-components.md)) |
| **Almond Spaces** | Named by the owner | **PLANNED** — *not specified* | No spec. Owner to define (T-0002) |
| **Almond Bridge** | Named by the owner | **PLANNED** — *not specified* | No spec. Not the same thing as the *Almond AI Bridge* (the developer tooling in `ai-bridge/`). Owner to define (T-0002) |
| **Almond Shield** | Named by the owner | **PLANNED** — *not specified* | No spec. Today's security defaults are described in [ARCHITECTURE.md](ARCHITECTURE.md#security-and-lifecycle-boundaries); nftables is installed but no firewall rules exist. Owner to define (T-0002) |
| **Performance modes** | Named by the owner | **PLANNED** — *not specified* | No spec. Today there is one performance budget for AALDM ([PERFORMANCE.md](PERFORMANCE.md)). Owner to define (T-0002) |
| Customisation | LXQt/Openbox settings tools now; "Almond Personalize" app later | **PLANNED** | [AALDM-PLAN §10](AALDM-PLAN.md#10-customisation). Requirements in [DESIGN_RULES.md](DESIGN_RULES.md#customisation-requirements) |
| Memory measurement | `tests/measure-memory.sh` | **IMPLEMENTED** | Run against a synthetic `/proc` on macOS only; never on Linux |
| Installer | Graphical installer | **PLANNED** | Version 0.5 |
| Website | almondlinux.github.io | Live | Separate repository `AlmondLinux/almondlinux.github.io` |
| Almond AI Bridge | Developer workflow for Claude + OpenAI models (`ai-bridge/`) | **IMPLEMENTED** | Phase 1 (GitHub handoff) works locally; OpenAI API review is off until the owner configures it. See [ai-bridge/README.md](../ai-bridge/README.md) |

## Performance targets (AALDM)

Targets, **not measurements**: idle RAM under 300 MB used 120 s after login, usable on 1 GB RAM where feasible, minimal idle CPU, low GPU needs. Nothing has been measured. Method: [PERFORMANCE.md](PERFORMANCE.md). No comparison with other distributions is published until measured ([ROADMAP.md](ROADMAP.md#aaldm-goal-a-better-light-desktop-than-linux-mint-xfce)).

## Hardware testing

| Machine | Role | Rung | Rules |
|---|---|---|---|
| VirtualBox VM (Debian 13 amd64) on the owner's Windows PC | Build machine + first boot tests | Not started | [PC-SETUP.md](PC-SETUP.md) |
| Dell OptiPlex 390 (2011, Intel, integrated graphics) | First real test PC | Not started | **USB live boot only.** The internal disk still holds old data: never mount, read or write it; wipe only with the owner's explicit OK |
| Apple Silicon Mac (UTM/Parallels, arm64) | Development variant only | Not started | Not a target. Cannot build the amd64 ISO |

## Known bugs and risks

Nothing has run, so there are no observed bugs yet. Known risks, from [AALDM-PLAN §16](AALDM-PLAN.md#16-open-decisions-and-risks):

1. The 300 MB idle-RAM target is not proven (estimates add up to roughly 225–400 MB).
2. Building without Recommends may leave out something a feature silently needs.
3. The 0200 hook replaces a directory owned by `lxqt-globalkeys` with a file; package upgrades on an installed system may fail.
4. No screen locker in 0.1 (the launcher's Lock entry does nothing).
5. Naming: OEPM/EUIPO trademark searches not done; similarity to "AlmaLinux" is the main risk.

## Task board

Generated from `ai-bridge/tasks/` by `ai-bridge/bridge handoff`. Do not edit between the markers.

<!-- bridge:tasks:start -->
| Task | Title | Status | Assignee | Review rounds | PR |
|---|---|---|---|---|---|
| [T-0001](../ai-bridge/tasks/T-0001-first-iso-build-and-vm-boot.md) | First AALDM ISO build and VM boot test | ready | claude-pc | 0/2 |  |
| [T-0002](../ai-bridge/tasks/T-0002-define-unspecified-components.md) | Define Almond Glass, Spaces, Bridge, Shield and performance modes | ready | owner | 0/2 |  |
<!-- bridge:tasks:end -->

## Change log

- 2026-10-17 — File created from README, ROADMAP and AALDM-PLAN as of commit 6401433. Glass, Spaces, Bridge, Shield and performance modes added as PLANNED / not specified (they appear in the owner's brief but nowhere in the repository).
