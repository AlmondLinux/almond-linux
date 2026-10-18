# D-0001 — Almond AI Bridge: GitHub files as the shared memory

- **Status:** proposed (only the owner changes this to accepted or rejected)
- **Date:** 2026-10-17
- **Proposed by:** Claude (Claude Code on the owner's Mac), at the owner's request

## Context

The owner was copying prompts, screenshots, code and updates by hand between ChatGPT and Claude. Neither product's chat conversation can be reached by the other: there is no supported API to read or write an existing ChatGPT or claude.ai conversation, and scraping either website is not allowed.

## Decision

1. **The repository is the shared memory.** Both AIs read the same files: `docs/PROJECT_STATUS.md`, `docs/DESIGN_RULES.md`, `docs/AI_HANDOFF.md`, `CLAUDE.md`, `AGENTS.md`, and the tasks, reports and decisions in `ai-bridge/`. Commits and pull requests are the source of truth for code.
2. **Claude implements** through Claude Code (the owner's subscription), working on task branches and opening pull requests. It never merges.
3. **An OpenAI model reviews**, through one of three lanes, cheapest first:
   - **Codex on GitHub** — comment `@codex review` on a pull request. Uses the owner's ChatGPT account (if the plan includes Codex) and reads `AGENTS.md`. No copying, no API key.
   - **ChatGPT, one paste each way** — `bridge out` copies a complete review packet; ChatGPT answers in a fixed JSON format; `bridge in` records it.
   - **OpenAI API in GitHub Actions** (optional, paid, off by default) — the owner adds the `ai-review` label to a PR.
4. **Limits:** at most 2 automated review rounds per task, then the owner decides. Paid calls need a master switch in the config plus an explicit trigger, and are capped per call and per month.
5. **The owner approves** every merge. `bridge approve` refuses to run without a real terminal, so an AI agent cannot approve.
6. **Claude in GitHub Actions** (claude-code-action) is documented as a template only, not enabled.

## Reason

Free, works with the tools the owner already pays for, keeps a written record in Git, and needs no server. Everything paid is optional and switched off.

## Alternatives considered

- Browser automation of chatgpt.com / claude.ai: against both services' terms and fragile. Rejected.
- A server that relays between both APIs: costs money on every step and needs hosting. Not needed for a solo project.
- GitHub Issues as the task store: possible later; files were chosen so both AIs can read tasks as plain text in the repository.

## Consequences

ChatGPT's own memory of past conversations is not shared automatically; whatever matters must be written into the repository (a decision record, a task, or the docs). The ChatGPT lane still needs two clipboard actions per review.
