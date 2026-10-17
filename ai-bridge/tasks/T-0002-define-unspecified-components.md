---
id: T-0002
title: Define Almond Glass, Spaces, Bridge, Shield and performance modes
status: ready
priority: medium
area: design
assignee: owner
created: 2026-10-17
updated: 2026-10-17
branch: 
pr: 
review_round: 0
max_review_rounds: 2
approval: required
proposed_by: owner
---

## Goal

These five names appear in the owner's plans but nowhere in the repository, so no AI may design or build them yet. For each one, the owner decides (alone or in a ChatGPT design discussion) what it is, which edition it belongs to (AALDM, AALLDM or both) and which version it targets. Each answer becomes a decision record, then a DESIGNED spec.

## Specs to read first

- docs/PROJECT_STATUS.md (Components table)
- docs/DESIGN_RULES.md (AALDM forbids transparency/blur: relevant for "Glass")
- docs/PERFORMANCE.md (relevant for "performance modes")
- docs/ARCHITECTURE.md, section "Security and lifecycle boundaries" (relevant for "Shield")

## Acceptance criteria

- [ ] One decision record per component in `ai-bridge/decisions/` (status accepted by the owner), or an explicit "dropped"
- [ ] For each kept component: one paragraph of purpose, edition, target version, resource cost expectation
- [ ] PROJECT_STATUS.md rows updated from "PLANNED — not specified" to PLANNED (with a one-line definition) or DESIGNED (with a spec link)
- [ ] Name check: "Almond Bridge" (product) is not confused with the "Almond AI Bridge" (developer tooling)

## Tests to run

- `ai-bridge/bridge check`

## Out of scope / needs the owner

- No implementation work. AI agents may draft decision proposals; only the owner accepts them

## Log
- 2026-10-17 17:40 — created while setting up the Almond AI Bridge
