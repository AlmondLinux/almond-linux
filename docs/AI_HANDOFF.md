# AI handoff

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

- **Nothing has been built, booted or measured.** All AALDM source is IMPLEMENTED (untested). See PROJECT_STATUS.md.
- **Next real step:** [T-0001](../ai-bridge/tasks/T-0001-first-iso-build-and-vm-boot.md) — first ISO build and VM boot on the owner's Windows PC (VirtualBox, Debian 13 amd64). The Mac cannot build the amd64 ISO.
- **Owner decision needed:** [T-0002](../ai-bridge/tasks/T-0002-define-unspecified-components.md) — what Almond Glass, Spaces, Bridge, Shield and performance modes are. Do not design or build them before that.
- **AALLDM** (large edition) is paused until it is designed separately.
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
_Generated 2026-10-17 17:44 CEST by `ai-bridge/bridge handoff`. Do not edit by hand._

**Branch:** `ai-bridge/phase-1`

### Waiting for the owner

- nothing

### Open tasks

| Task | Title | Status | Assignee | Review rounds | PR |
|---|---|---|---|---|---|
| [T-0001](../ai-bridge/tasks/T-0001-first-iso-build-and-vm-boot.md) | First AALDM ISO build and VM boot test | ready | claude-pc | 0/2 |  |
| [T-0002](../ai-bridge/tasks/T-0002-define-unspecified-components.md) | Define Almond Glass, Spaces, Bridge, Shield and performance modes | ready | owner | 0/2 |  |

### Latest reports and reviews

- none yet

### Last commits on this branch

```
6401433 2026-10-14 AALDM: Almond Pure assets, desktop theme and amd64 build configuration
96aed5b 2026-10-14 Keep LICENSE as standard MIT text; move scope note to NOTICE
b3aaaba 2026-10-14 Almond Linux 0.1 'Marcona': first draft of the build configuration
```

### Paid API reviews

OpenAI reviews: **off** · model `gpt-5-mini` · spent this month (local log) $0.0000 of $2.00
<!-- bridge:handoff:end -->

## Handoff notes

Add a dated entry when you stop work that someone else will continue. Newest first. Keep each to a few lines: what changed, what is unfinished, what to do next.

- **2026-10-17 — Claude (Mac):** Set up the Almond AI Bridge (phase 1 files, local CLI, free PR checks workflow, optional OpenAI review workflow switched off, dashboard). Created PROJECT_STATUS.md, DESIGN_RULES.md, this file, CLAUDE.md and AGENTS.md. No OS code changed. Next: owner reviews and merges the bridge PR; then T-0001 on the PC.
