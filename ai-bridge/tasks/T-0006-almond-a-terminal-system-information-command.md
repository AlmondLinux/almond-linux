---
id: T-0006
title: "almond: a terminal system-information command"
status: ready
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
proposed_by: owner
---

## Goal

A small command, `almond`, that prints the Almond terminal mark and real system information: edition, kernel, CPU, GPU, RAM in use, uptime. Requested by the owner on 2026-10-18.

## Specs to read first

- docs/DESIGN_RULES.md (logo rules, colours, AALDM: nothing resident)
- tests/measure-memory.sh (same "Used = MemTotal − MemAvailable" figure and fake-/proc testing style)

## Acceptance criteria

- [ ] POSIX `sh`, no new packages (uses /proc, /sys, /etc/os-release, `uname`, and `lspci` from pciutils, which is already in the image)
- [ ] Every value is read from the running system; anything that cannot be read is shown as "unknown", never guessed
- [ ] Shows: edition (from /etc/os-release), kernel, CPU model and thread count, GPU(s), RAM used / total, uptime
- [ ] `--no-color`, `--no-logo`, `--help`; colours off automatically when output is not a terminal
- [ ] Testable on a non-Linux host against a fake /proc, /sys and os-release
- [ ] The terminal mark is marked as a proposal until the owner approves it (it is not the official logo)

## Tests to run

- `ai-bridge/bridge check`
- Run against fake system trees with `dash`
- Next VM test: run `almond` in QTerminal and compare with `uname -a`, `lscpu`, `lspci`, `free -m`, `uptime`

## Out of scope / needs the owner

- Approval of the terminal mark

## Log
- 2026-10-18 15:00 — created at the owner's request (Claude, Mac)
