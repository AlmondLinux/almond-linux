---
id: T-0007
title: Install Almond Linux option with Calamares
status: ready
priority: medium
area: installer
assignee: claude
created: 2026-10-18
updated: 2026-10-18
branch: 
pr: 
review_round: 0
max_review_rounds: 2
approval: required
proposed_by: owner
---

## Goal

The live desktop offers a clear "Install Almond Linux" option, using the Calamares installer from Debian, so AALDM can be installed. Requested by the owner on 2026-10-18. This is the start of the 0.5 installer milestone.

## Specs to read first

- docs/ROADMAP.md (0.5: graphical installer and testing; installs on disposable disks only)
- docs/ARCHITECTURE.md, "Security and lifecycle boundaries" (live-session conveniences must not become installed defaults)
- docs/AALDM-PLAN.md §0 (performance rules)

## Acceptance criteria

- [ ] Research written down: which Debian 13 packages (`calamares`, `calamares-settings-debian`), their size, what they configure, and what must be Almond-specific (branding, no Debian logos presented as Almond)
- [ ] Almond Calamares settings and branding (owner's logo used unaltered, Almond colours), with the live user, autologin and passwordless sudo removed from the installed system
- [ ] An "Install Almond Linux" entry on the live desktop and in the launcher, only in the live session
- [ ] Packages added to `config/package-lists/aaldm.list.chroot` (sensitive path: owner approves)
- [ ] Test plan for disposable VirtualBox disks: BIOS and UEFI installs, first boot of the installed system, user and password, no live user left, updates work

## Tests to run

- `ai-bridge/bridge check`
- Install tests on throwaway VirtualBox disks on the PC (never on real hardware, never on the OptiPlex 390's disk)

## Out of scope / needs the owner

- Adding packages and changing build hooks: owner approves in the PR
- Any install on real hardware

## Log
- 2026-10-18 15:00 — created at the owner's request (Claude, Mac)
