---
id: T-0005
title: "Owner feedback: desktop icons and a start menu"
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

The owner's feedback after first seeing the desktop (2026-10-17): they do not like the desktop icons, and they want a start menu to configure everything. Decide what to change, then implement it.

## Specs to read first

- tests/results/2026-10-17-vm/RESULTS.md, "Owner feedback"
- docs/DESIGN_RULES.md (Almond Pure is owner-approved; the panel deliberately has only the launcher button today)
- `desktop/defaults/etc/xdg/pcmanfm-qt/lxqt/settings.conf` (`DesktopShortcuts=Home, Trash, Computer`, `DesktopIconSize=48`), `panel.conf`

## Acceptance criteria

- [ ] Owner decision recorded (decision record): which desktop icons stay, if any, and how they look
- [ ] Owner decision recorded: a classic start menu (for example LXQt's main menu with categories and a Settings section) next to, or instead of, the Super-key launcher
- [ ] Implemented as decided, with the memory cost of any new panel plugin noted in docs/PERFORMANCE.md

## Tests to run

- `ai-bridge/bridge check`
- Next VM test: screenshots of the desktop and the menu; memory report

## Out of scope / needs the owner

- This changes an approved design: nothing is built before the owner's decisions

## Log
- 2026-10-18 12:00 — created from the 2026-10-17 VM test results (Claude, Mac); backlog until the owner moves it to ready
