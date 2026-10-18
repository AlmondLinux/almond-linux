---
id: T-0008
title: Website status update for the first VM boot
status: ready
priority: medium
area: website
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

The website (AlmondLinux/almondlinux.github.io) says accurately that an experimental AALDM ISO was built and booted in VirtualBox, without offering a download or calling anything stable. Requested by the owner on 2026-10-18.

## Specs to read first

- docs/PROJECT_STATUS.md, tests/results/2026-10-17-vm/RESULTS.md

## Acceptance criteria

- [ ] Every "no ISO has been built" statement on the site is updated
- [ ] Facts only: date, VirtualBox, BIOS and UEFI, memory numbers with the "one boot, target not met" caveat
- [ ] No download link, no "stable", no comparison with other distributions
- [ ] Prepared on a branch with a PR in the site repository; nothing goes live until the owner merges

## Tests to run

- Local preview of the site (launch.json "almond-site")

## Out of scope / needs the owner

- Publishing (merging the site PR)

## Log
- 2026-10-18 15:00 — created at the owner's request (Claude, Mac)
