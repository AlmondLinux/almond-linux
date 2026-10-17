---
id: T-0001
title: First AALDM ISO build and VM boot test
status: ready
priority: high
area: build
assignee: claude-pc
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

Turn AALDM 0.1 "Marcona" from IMPLEMENTED into evidence: build the amd64 ISO once in a Debian 13 VM and boot it in BIOS and UEFI mode, recording exactly what happened. A failure report is a valid result.

## Specs to read first

- docs/PROJECT_STATUS.md
- docs/PC-SETUP.md (the step-by-step guide for the owner's Windows PC)
- docs/BUILD.md
- docs/AALDM-PLAN.md sections 0, 1, 6, 15
- docs/PERFORMANCE.md (memory method)

## Acceptance criteria

- [ ] Build attempted on Debian 13 amd64 with `sudo ./scripts/build.sh`; `build.log`, `build-tool-versions.txt` and the package manifest kept
- [ ] If the build succeeded: ISO SHA256 recorded; boot tried in VirtualBox with legacy BIOS and with UEFI (2 GB RAM, no disk)
- [ ] Screenshots: boot menu, desktop, Almond Launcher open (Super key)
- [ ] `measure-memory.sh` run 120 s after login at 2 GB and at 1 GB RAM, outputs saved
- [ ] `RESULTS.md` with date, VirtualBox + Debian versions, every OK/failed item and exact error lines
- [ ] Results committed under `tests/results/2026-xx-xx-vm/` (no ISO file in Git) and PROJECT_STATUS.md updated: only components that actually ran move to TESTED

## Tests to run

- `ai-bridge/bridge check`
- The build and boot steps above (need the Windows PC; cannot run on the Mac)

## Out of scope / needs the owner

- Every download, install and Windows setting change: ask the owner first (name, source, size)
- The Dell OptiPlex 390 is NOT part of this task. Never touch its internal disk
- No changes to `scripts/build.sh`, hooks or package lists in this task: write bugs into RESULTS.md and open a new task for each fix

## Log
- 2026-10-17 17:40 — created from the 2026-10-14 handoff (almond-handoff/PC-CLAUDE-PROMPT.md), which has not been run yet as far as this repository shows
