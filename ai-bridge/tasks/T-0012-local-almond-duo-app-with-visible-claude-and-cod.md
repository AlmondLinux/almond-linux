---
id: T-0012
title: Local Almond Duo app with visible Claude and Codex collaboration
status: review
priority: medium
area: general
assignee: claude
created: 2026-10-18
updated: 2026-10-18
branch: app/almond-duo-desktop
pr: 9
review_round: 0
max_review_rounds: 2
approval: required
proposed_by: owner
---

## Goal

Give the owner one local Mac app to prompt Claude and Codex together and read their visible conversation.

## Specs to read first

- docs/PROJECT_STATUS.md
- docs/DESIGN_RULES.md
<!-- add the specific plan sections, e.g. docs/AALDM-PLAN.md#6-launcher-almond-launcher-rofi -->

## Acceptance criteria

- [x] Ask both concurrently and exchange second responses.
- [x] Build together uses the tested plan, review, implement and check workflow.
- [x] Save history, export transcripts, isolate runs and stop work.
- [x] Verify the packaged native app with real agents.

## Tests to run

- `ai-bridge/bridge check`
<!-- add task-specific tests; say which ones need a built image or real hardware -->

## Out of scope / needs the owner

No automatic pushes, merges, releases or paid API review.
