---
id: T-0011
title: "Docs only: fix the three documentation mismatches found in the first VM test (te"
status: in-progress
priority: medium
area: docs
assignee: duo
created: 2026-10-18
updated: 2026-10-18
branch: task/T-0011-docs-only-fix-the-three-document
pr: 
review_round: 0
max_review_rounds: 2
approval: required
proposed_by: owner
---

## Goal

Docs only: fix the three documentation mismatches found in the first VM test (tests/results/2026-10-17-vm/RESULTS.md, Problem 9): BUILD.md recommends 4 vCPUs for the build VM but 4 froze VirtualBox on the Windows hypervisor and 1 CPU worked; AALDM-PLAN.md names Firefox ESR 140 but the image has 153.5.0esr; PC-SETUP.md runs measure-memory.sh without -w 120 while BUILD.md uses -w 120. Change only docs/BUILD.md, docs/AALDM-PLAN.md and docs/PC-SETUP.md. Do not touch auto/config or any other sensitive path.

## Specs to read first

- docs/PROJECT_STATUS.md
- docs/DESIGN_RULES.md
<!-- add the specific plan sections, e.g. docs/AALDM-PLAN.md#6-launcher-almond-launcher-rofi -->

## Acceptance criteria

- [ ] <!-- criterion -->

## Tests to run

- `ai-bridge/bridge check`
<!-- add task-specific tests; say which ones need a built image or real hardware -->

## Out of scope / needs the owner

<!-- anything the implementer must not do without asking -->

## Log
- 2026-10-18 15:10 — duo started on task/T-0011-docs-only-fix-the-three-document (base task/T-0010-duo-mode-claude-and-codex-work-t)
