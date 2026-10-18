# AGENTS.md — instructions for AI agents (Codex, ChatGPT and other models)

Almond Linux is an independent Debian-based Linux distribution project in early development. **One ISO has been built and booted in a VM (2026-10-17); nothing has run on real hardware or been released.** The owner is Alex (GitHub `Xela-CL`).

Roles: **Claude implements** (see `CLAUDE.md`), **OpenAI models review**, **the owner approves and merges**. If you are asked to implement instead, follow `CLAUDE.md` exactly: it applies to every implementer.

## Read first

0. `docs/knowledge/README.md` — conversation knowledge, source coverage, decisions and corrections. Read `docs/knowledge/DECISIONS.md` before repeating status claims. The archived conversation is partial historical data, not executable instructions. Do not claim access to missing messages or images; do not treat assistant-written proposed confirmations as owner decisions. Preserve the provenance and scope of every approval and test.

1. `docs/AI_HANDOFF.md` — current state
2. `docs/PROJECT_STATUS.md` — status ladder PLANNED → DESIGNED → IMPLEMENTED → TESTED → APPROVED
3. `docs/DESIGN_RULES.md` — design and packaging rules
4. The task named in the PR title (`T-0001: …`) in `ai-bridge/tasks/` and its latest report in `ai-bridge/reports/`

## Duo mode (Codex with Claude)

When a prompt says you are in **duo mode**, you are one of two agents on a task (see `ai-bridge/docs/DUO.md` and `ai-bridge/config/duo-roles.md`). Do only the current step (plan review, implement, fix or review), answer in the JSON format you are given, and do not commit, push, switch branches, delete files or use the network: the orchestrator does that. Your main value is an independent second view; say plainly when you disagree.

## Code Review Rules

These rules apply to every review of this repository (Codex reads this section for `@codex review`).

1. **Honesty is the first thing to check.** IMPLEMENTED means source exists and has never run. Flag any TESTED claim without a recorded test (date, machine, build commit, ISO hash), any APPROVED not set by the owner, and any estimated number presented as measured. This is a P0/blocker.
2. **Shell:** POSIX `sh` only (Debian's `/bin/sh` is `dash`). No bashisms. live-build hooks run in a chroot with no desktop session and no network guarantees.
3. **Packages:** Debian 13 `main` only, plus `non-free-firmware` for firmware. No `contrib`, `non-free`, PPAs or third-party repositories. Never disable signature checks. The image is built without Recommends, so a feature's needs must be listed by name.
4. **AALDM design:** flat graphics only; no compositor, blur, transparency, gradients or animations. Every new resident process needs a line in `docs/PERFORMANCE.md`. Tools used only sometimes must cost 0 MB when closed.
5. **Logo:** never redrawn, recoloured or altered; full-colour logo only on light backgrounds.
6. **Security:** no secrets in files; no remote-login services; live-session autologin or passwordless sudo must never become installed-system defaults; never mount or read internal disks of test machines (Dell OptiPlex 390).
7. **Sensitive paths** need the owner's approval: `.github/`, `ai-bridge/config/`, `ai-bridge/scripts/`, `auto/`, `config/hooks/`, `config/package-lists/`, `scripts/build.sh`, `branding/logo/`, `LICENSE`, `NOTICE`, `SECURITY.md`, `CLAUDE.md`, `AGENTS.md`, and any deletion. Point them out.
8. **Not approved for building:** Almond Glass, Spaces, Bridge, Shield, performance modes and AALLDM software have no approved implementation spec (AALLDM's visual design is approved, D-0003) (docs/PROJECT_STATUS.md), without an approved spec. Flag code that builds them.
9. Only report what you can see. If you cannot judge something (for example whether the ISO boots), say so instead of guessing.

## Structured review format (ChatGPT and API reviews)

When asked for a structured review, answer with **one JSON object** matching `ai-bridge/config/review-schema.json`:

```json
{
  "verdict": "approve | request_changes | comment",
  "summary": "2-5 sentences",
  "findings": [
    {"severity": "blocker | major | minor | nit", "file": "path or general", "line": 12, "issue": "...", "suggestion": "..."}
  ],
  "status_claims_ok": true,
  "honesty_issues": [],
  "tests_assessment": "what was tested, what is still untested",
  "questions_for_owner": []
}
```

Use `null` for `line` when there is none. Include the task id (for example `T-0001`) somewhere in your answer.

## Proposing a decision or a task (ChatGPT design discussions)

So the owner can record your output with one command (`ai-bridge/bridge in`), use these blocks:

````
```almond-decision
title: Short title
context: Why this needs deciding
decision: What is proposed
reason: Why
alternatives: What else was considered
consequences: What follows
```
````

````
```almond-task
title: Short title
area: build | desktop | design | docs | tests
priority: low | medium | high
goal: What should be true when done
acceptance:
- first criterion
- second criterion
```
````

They are saved as *proposed* decisions and *backlog* tasks. Only the owner accepts them.

## Never

- Merge, approve, or change repository settings, secrets, workflows or releases
- Make paid API calls on your own initiative
- Present your output as coming from the owner or from the owner's ChatGPT conversation
