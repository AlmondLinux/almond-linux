---
id: T-0004
title: First-boot polish and docs fixes from the first VM test
status: backlog
priority: medium
area: desktop
assignee: claude
created: 2026-10-18
updated: 2026-10-18
branch: 
pr: 
review_round: 0
max_review_rounds: 2
approval: required
proposed_by: claude
---

## Goal

Small fixes from the 2026-10-17 VM test that make the first boot cleaner and the docs match reality.

## Specs to read first

- tests/results/2026-10-17-vm/RESULTS.md, "Problems and bugs found" items 5–9
- docs/BUILD.md, docs/PC-SETUP.md, docs/AALDM-PLAN.md

## Acceptance criteria

- [ ] No LXQt power-management pop-ups at first login on a PC without a battery (configure lxqt-powermanagement defaults; do not remove power management)
- [ ] UEFI GRUB menu: the title no longer overlaps the almond logo
- [ ] Decide zstd: add `zstd` to the package list (initramfs zstd) or record why gzip stays; measure ISO size and boot time either way
- [ ] `tests/measure-memory.sh`: find out why 72 processes count as "unreadable" with 0 kernel threads, and fix it if it is a bug
- [ ] Docs: BUILD.md vCPU advice (4 vCPUs froze VirtualBox on the Windows hypervisor; 1 worked), AALDM-PLAN Firefox ESR version (image has 153.5), PC-SETUP.md `measure-memory.sh -w 120`, the stale "No ISO has been built" comment in `auto/config`

## Tests to run

- `ai-bridge/bridge check`
- Next VM test: first-login screenshots in BIOS and UEFI mode; measure-memory report

## Out of scope / needs the owner

- Package-list and `auto/config` changes are sensitive paths: the owner approves them in the PR

## Log
- 2026-10-18 12:00 — created from the 2026-10-17 VM test results (Claude, Mac); backlog until the owner moves it to ready
