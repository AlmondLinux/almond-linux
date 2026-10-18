---
id: T-0003
title: Launcher fixes from the first VM test
status: review
priority: medium
area: desktop
assignee: claude
created: 2026-10-18
updated: 2026-10-18
branch: task/T-0003-launcher-fixes-from-the-first-vm
pr: 
review_round: 0
max_review_rounds: 2
approval: required
proposed_by: claude
---

## Goal

Fix the Almond Launcher problems found in the 2026-10-17 VM test, within the approved Almond Pure launcher design.

## Specs to read first

- tests/results/2026-10-17-vm/RESULTS.md, "Problems and bugs found" items 2–4
- docs/AALDM-PLAN.md section 6 (launcher)
- docs/DESIGN_RULES.md

## Acceptance criteria

- [x] Opening the launcher with an empty search never highlights a power action (Hibernate, Shut down, Reboot, Log out); pressing Enter at once does nothing harmful
- [x] After typing, the highlight moves to the best (first) match
- [x] "Lock Screen" and "Hibernate" are hidden while no screen locker / no hibernation support exists
- [x] The four tiles without icons ("Session Settings", "Rofi Theme Selector", "Notifications", "File Associations") get an icon, or the entries are hidden if they should not be in the launcher (owner decides which)
- [ ] Long names stay readable (no cut-off for common apps), or the reason is written down

## Tests to run

- `ai-bridge/bridge check`
- In the next VM test (needs a new ISO build on the PC): open with Super 5 times, record the highlighted tile; type `term` and `qterm`, record the highlight; `pgrep rofi` after Esc

## Out of scope / needs the owner

- Installing a screen locker (new package: owner decides)
- Any change to the launcher's look beyond the bugs above

## Log
- 2026-10-18 12:00 — created from the 2026-10-17 VM test results (Claude, Mac); backlog until the owner moves it to ready
- 2026-10-18 14:41 — moved to ready (owner)
- 2026-10-18 14:41 — started on branch task/T-0003-launcher-fixes-from-the-first-vm
- 2026-10-18 14:42 — implementation report 1 written (all checks passed)
