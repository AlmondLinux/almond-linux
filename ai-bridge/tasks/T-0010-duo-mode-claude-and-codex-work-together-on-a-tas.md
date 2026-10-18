---
id: T-0010
title: "Duo mode: Claude and Codex work together on a task"
status: in-progress
priority: medium
area: tooling
assignee: claude
created: 2026-10-18
updated: 2026-10-18
branch: task/T-0010-duo-mode-claude-and-codex-work-t
pr: 
review_round: 0
max_review_rounds: 2
approval: required
proposed_by: owner
---

## Goal

The owner gives one task; Claude and Codex work on it together, each doing what it is better at, talking through structured files, with a transcript the owner can read. Requested by the owner on 2026-10-18. Shared context includes the knowledge base from PR #5 (docs/knowledge/).

## Specs to read first

- ai-bridge/README.md, docs/knowledge/README.md, docs/knowledge/AI-BRIDGE.md
- CLAUDE.md, AGENTS.md

## Acceptance criteria

- [x] `ai-bridge/bridge duo "task"` / `duo T-xxxx`: plan → one plan critique → revision → implement → free checks → review by the other AI → fixes, max `max_review_rounds`, then the owner
- [x] Owner questions in the plan stop the run before code; the run can be resumed
- [x] Transcript per task in ai-bridge/conversations/; one commit per round; never pushes or merges
- [x] Uses the official Codex CLI (ChatGPT sign-in) and Claude Code CLI; API-key variables removed from their environment
- [x] Headless Claude limited by an allowlist; Codex sandboxed (read-only, workspace-write when implementing)
- [x] `ai-bridge/bridge ask codex|claude "question"`, read-only and logged
- [x] Tests with fake CLIs; end-to-end run with fakes
- [x] One real duo run with the real Claude and Codex (T-0011, PR #7)
- [x] Live viewer (`ai-bridge/bridge view`)
- [x] One chat (owner request 2026-10-18): single live log, one persistent session per AI, tasks/questions/answers typed in the page, answers resume a paused task, PR opened automatically, failed runs leave a clean tree

## Tests to run

- `ai-bridge/bridge check` (includes tests/test_duo.py)
- End-to-end with fakes in a scratch clone (ai-bridge/docs/TESTING.md)

## Out of scope / needs the owner

- Changing bridge.toml / scripts (sensitive): owner approves in the PR
- claudex: not used (third-party proxy; its ChatGPT-subscription profile uses an unofficial endpoint)

## Log
- 2026-10-18 15:20 — built by Claude (Mac); real run pending
- 2026-10-18 15:40 — real run T-0011 succeeded; viewer added; Codex's findings applied (CodexCLI.app path, critic concerns carried into implement/review, untracked files refused)
