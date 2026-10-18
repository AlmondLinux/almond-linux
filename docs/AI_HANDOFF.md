# AI handoff

Automatic joint workflow: [duo validation](../ai-bridge/docs/DUO-VALIDATION.md) records a real Claude plan → Codex critique → Claude implementation → checks → Codex review cycle. Use the duo instructions for owner-requested joint tasks; no automatic merge or background chat mirroring.

Conversation context: [project knowledge base](knowledge/README.md), imported 2026-10-18 (T-0009). Only five recent ChatGPT turns were accessible; full export and mockups remain missing. Read its chronology for corrected names, visual approval scope, and precise VM coverage. This import changes no OS component status.

Read this first if you are an AI agent (Claude, Codex, ChatGPT or another model) picking up Almond Linux work. It says where things stand and what to do next. Humans are welcome too.

Then read, in order: [PROJECT_STATUS.md](PROJECT_STATUS.md) → [DESIGN_RULES.md](DESIGN_RULES.md) → the task you were given in [`ai-bridge/tasks/`](../ai-bridge/tasks/). Implementers follow [CLAUDE.md](../CLAUDE.md); reviewers follow [AGENTS.md](../AGENTS.md).

## Who does what

| Role | Who | How |
|---|---|---|
| Owner | Alex (GitHub `Xela-CL`) | Creates and prioritises tasks, approves designs, approves and merges every PR. The only one who can mark anything APPROVED |
| Implementer | Claude (Claude Code on the owner's Mac or Windows PC) | Takes a `ready` task, works on a task branch, runs checks, writes the implementation report, opens a PR. Never merges |
| Reviewer | An OpenAI model: Codex (`@codex review` on a PR), ChatGPT (pasted packet) or the OpenAI API (GitHub Action) | Returns a structured review. A review is not a message from the owner's ChatGPT conversation |

## Current state (curated)

Last updated 2026-10-17.

- **First ISO built and booted in VirtualBox (2026-10-17)**, BIOS and UEFI. Report: [tests/results/2026-10-17-vm/RESULTS.md](../tests/results/2026-10-17-vm/RESULTS.md). Idle memory 413 MiB (2 GB VM): above the 300 MB target. Nothing on real hardware yet.
- **Bugs from that test** are backlog tasks T-0003 (launcher), T-0004 (first-boot polish and docs) and T-0005 (owner feedback: desktop icons, start menu). The owner moves them to ready.
- **Owner decisions 2026-10-18:** edition names confirmed ([D-0002](../ai-bridge/decisions/D-0002-edition-names.md)); AALLDM visual design approved ([D-0003](../ai-bridge/decisions/D-0003-aalldm-visual-design-approved.md)) — DESIGNED, no code. Still open in [T-0002](../ai-bridge/tasks/T-0002-confirm-component-definitions.md): performance-modes scope, Glass/Spaces behaviour, Bridge, Shield.
- **Almond AI Bridge** (this workflow) was set up 2026-10-17: [ai-bridge/README.md](../ai-bridge/README.md). Paid OpenAI reviews are off.

## Hard rules for every agent

1. Never claim more than the evidence shows. IMPLEMENTED ≠ TESTED ≠ APPROVED.
2. Never put secrets in files. Never paste API keys into issues, PRs or docs.
3. Never mount, read or write the internal disk of the Dell OptiPlex 390.
4. Never merge, never approve, never change repository settings, secrets or release workflows.
5. Sensitive paths (listed in `ai-bridge/config/bridge.toml`) and any file deletion need the owner's explicit approval.
6. Stop after the review-round limit (2 by default) and hand the decision to the owner.

## Generated status

<!-- bridge:handoff:start -->
_Generated 2026-10-18 15:14 CEST by `ai-bridge/bridge handoff`. Do not edit by hand._

**Branch:** `task/T-0010-duo-mode-claude-and-codex-work-t`

### Waiting for the owner

- T-0001 First AALDM ISO build and VM boot test

### Open tasks

| Task | Title | Status | Assignee | Review rounds | PR |
|---|---|---|---|---|---|
| [T-0002](../ai-bridge/tasks/T-0002-confirm-component-definitions.md) | Confirm component definitions, edition names and AALLDM design status | ready | owner | 0/2 |  |
| [T-0006](../ai-bridge/tasks/T-0006-almond-a-terminal-system-information-command.md) | almond: a terminal system-information command | ready | claude | 0/2 |  |
| [T-0007](../ai-bridge/tasks/T-0007-install-almond-linux-option-with-calamares.md) | Install Almond Linux option with Calamares | ready | claude | 0/2 |  |
| [T-0010](../ai-bridge/tasks/T-0010-duo-mode-claude-and-codex-work-together-on-a-tas.md) | Duo mode: Claude and Codex work together on a task | in-progress | claude | 0/2 |  |
| [T-0008](../ai-bridge/tasks/T-0008-website-status-update-for-the-first-vm-boot.md) | Website status update for the first VM boot | review | claude | 0/2 | #almondlinux.github.io#1 |
| [T-0009](../ai-bridge/tasks/T-0009-preserve-almond-conversation-knowledge-and-sourc.md) | Preserve Almond conversation knowledge and source provenance | review | codex | 0/2 | #5 |
| [T-0001](../ai-bridge/tasks/T-0001-first-iso-build-and-vm-boot.md) | First AALDM ISO build and VM boot test | needs-owner | claude-pc | 0/2 |  |

### Latest reports and reviews

- [T-0009-impl-1.md](../ai-bridge/reports/T-0009-impl-1.md) — implementation 

### Last commits on this branch

```
54b2c10 2026-10-18 T-0010: duo mode - Claude and Codex work on a task together
8de263d 2026-10-18 T-0009: Link knowledge review to PR #5
ad8dced 2026-10-18 T-0009: Preserve sourced Almond conversation knowledge and gaps
d668bc8 2026-10-18 T-0008: website status draft is in AlmondLinux/almondlinux.github.io#1
82ba00c 2026-10-18 Add tasks T-0006 (almond command), T-0007 (installer), T-0008 (website status)
1a8d4a1 2026-10-18 Record owner decisions: edition names (D-0002), AALLDM visual design approved (D-0003)
aa2cd2a 2026-10-18 Record the first VM build and boot test; reconcile project status
26337d0 2026-10-17 Almond AI Bridge phase 1: shared docs, task/review workflow, free PR checks
```

### Paid API reviews

OpenAI reviews: **off** · model `gpt-5-mini` · spent this month (local log) $0.0000 of $2.00
<!-- bridge:handoff:end -->

## Handoff notes

Add a dated entry when you stop work that someone else will continue. Newest first. Keep each to a few lines: what changed, what is unfinished, what to do next.

- **2026-10-18 — Claude (Mac):** Recorded the PC's 2026-10-17 build and VM boot results in `tests/results/2026-10-17-vm/` and updated PROJECT_STATUS.md (several components now TESTED (VM)). Added the owner's component definitions from their design notes. Opened backlog tasks T-0003–T-0005 for the bugs found. Waiting for the owner on T-0002.
- **2026-10-17 — Claude (Mac):** Set up the Almond AI Bridge (phase 1 files, local CLI, free PR checks workflow, optional OpenAI review workflow switched off, dashboard). Created PROJECT_STATUS.md, DESIGN_RULES.md, this file, CLAUDE.md and AGENTS.md. No OS code changed. Next: owner reviews and merges the bridge PR; then T-0001 on the PC.
