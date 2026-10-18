---
id: T-0009
title: Preserve Almond conversation knowledge and source provenance
status: review
priority: medium
area: docs
assignee: codex
created: 2026-10-18
updated: 2026-10-18
branch: task/T-0009-preserve-almond-conversation-kno
pr:
review_round: 0
max_review_rounds: 2
approval: required
proposed_by: owner
---

## Goal

Preserve the accessible Almond Linux conversation as a sourced knowledge base, with explicit coverage gaps and a separate PR. Authorized directly by the owner in Codex on 2026-10-18.

## Specs to read first

- docs/knowledge/SOURCES.md
- docs/PROJECT_STATUS.md
- docs/DESIGN_RULES.md

## Acceptance criteria

- [x] Archive all five returned turns without claiming a complete export
- [x] Cover editions, approvals, components, tests, ISO, bugs, assets and AI Bridge
- [x] Preserve chronological conflicts and later repository corrections
- [x] Add AGENTS.md guidance and handoff link
- [x] Request full user export and original visual attachments for completion
- [ ] Run repository checks and open separate PR without merging

## Tests to run

- `ai-bridge/bridge check`
- Validate knowledge Markdown links and archived message-text fidelity

## Out of scope / needs the owner

No OS implementation, paid API activation, workflow changes or merge. AGENTS.md is a sensitive path; the owner explicitly requested Codex instructions in this task. Full historical archive remains pending a user-provided export; omitted material cannot be recovered from the returned reader page.

## Log
- 2026-10-18 14:57 — implementation report 1 written (all checks passed)
