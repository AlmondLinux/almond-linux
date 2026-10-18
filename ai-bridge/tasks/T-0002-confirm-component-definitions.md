---
id: T-0002
title: Confirm component definitions, edition names and AALLDM design status
status: ready
priority: medium
area: design
assignee: owner
created: 2026-10-17
updated: 2026-10-18
branch: 
pr: 
review_round: 0
max_review_rounds: 2
approval: required
proposed_by: owner
---

## Goal

The owner's design notes (Obsidian vault "Almond Linux", 2026-10-15, from ChatGPT design discussions) define Almond Glass, Spaces, Bridge, Shield and performance modes. PROJECT_STATUS.md now carries those definitions as PLANNED. The owner confirms or corrects them, so that agents work from one agreed version.

## Specs to read first

- docs/PROJECT_STATUS.md (Editions and Components tables)
- docs/DESIGN_RULES.md (AALDM forbids transparency/blur: relevant for Glass and the Medium/High performance modes)
- docs/ARCHITECTURE.md, section "Security and lifecycle boundaries" (relevant for Shield)

## Acceptance criteria

- [x] **Edition names:** the owner confirms the exact expansions (repository: "A All Little Distribution Model" / "A All Large Linux Distribution Model"; an AALLDM prompt in the notes says "…Linux Distro Model")
- [x] **AALLDM design:** the owner says whether Fusion V2 / Design 03 is approved. If yes: add the mockup (or a link) and the date, and move it to DESIGNED
- [ ] **Performance modes:** decide whether Potato / Medium / High apply to AALDM (Medium/High add transparency and animation, which AALDM's rules forbid) or only to AALLDM
- [ ] **Glass, Spaces, Bridge, Shield:** each definition in PROJECT_STATUS.md confirmed or corrected; edition and target version stated
- [ ] One decision record per decision in `ai-bridge/decisions/` (ChatGPT can write `almond-decision` blocks; `ai-bridge/bridge in` saves them)

## Tests to run

- `ai-bridge/bridge check`

## Out of scope / needs the owner

- No implementation work. AI agents may draft decision proposals; only the owner accepts them

## Log
- 2026-10-17 17:40 — created while setting up the Almond AI Bridge
- 2026-10-18 12:00 — rewritten: the definitions were found in the owner's notes; the task is now to confirm them (Claude, Mac)
- 2026-10-18 13:00 — owner decided: names = option B (D-0002); AALLDM visual design approved (D-0003). Still open: performance modes scope, Glass/Spaces behaviour, Bridge, Shield; AALLDM mockup images to be added
