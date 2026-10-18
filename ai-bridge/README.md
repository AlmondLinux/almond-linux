# Almond AI Bridge

How Claude and OpenAI models work together on Almond Linux **without copying things between chat windows by hand.**

The trick is simple: **both AIs read and write the same files in this repository.** Tasks, implementation reports, reviews and decisions are plain files in `ai-bridge/`; project knowledge lives in `docs/`. GitHub pull requests carry the code. You stay in charge of every merge.

> **What this is not.** It does not connect to your existing ChatGPT conversation or your claude.ai chats. No supported API can read or write those, and scraping the websites is not allowed. ChatGPT and Claude only "know" what is written in this repository, which is exactly why the important things get written here.

## The workflow

```
  you                     Claude (Claude Code)              OpenAI model (reviewer)
  ───                     ────────────────────              ───────────────────────
1 bridge new "Task"  ──►  ai-bridge/tasks/T-0003-….md
2                         bridge start T-0003  (branch)
3                         implements on the branch
4                         bridge check  (free tests)
5                         bridge finish T-0003  ──►  ai-bridge/reports/T-0003-impl-1.md
                          gh pr create                     │
6 pick ONE review lane: ───────────────────────────────────┤
    a) comment "@codex review" on the PR           ─────► Codex reviews on GitHub (reads AGENTS.md)
    b) bridge out T-0003 → paste into ChatGPT      ─────► ChatGPT answers in JSON
       copy answer → bridge in --task T-0003
    c) add label "ai-review" (paid, opt-in)        ─────► GitHub Action calls the OpenAI API
7                                                    ◄──── review saved: reports/T-0003-review-1.md
8                         fixes findings, bridge finish again (round 2)
9 bridge approve T-0003   (only works in YOUR terminal; asks before merging)
10 merged
```

**Loop limit:** at most **2** automated review rounds per task. After that the task goes to `needs-owner` and no AI review runs until you decide. Change it in `config/bridge.toml` (`max_review_rounds`).

## Easiest: duo mode

`ai-bridge/bridge duo "what you want"`: Claude and Codex split the work by their strengths and check each other, on your existing Claude and ChatGPT subscriptions. You read the transcript and approve. Details: [docs/DUO.md](docs/DUO.md). The lanes below are for reviewing work that was done another way.

## Which review lane should I use?

| Lane | Copying | Cost | What you need |
|---|---|---|---|
| **a) Codex on GitHub** — comment `@codex review` on the PR | none | Included in ChatGPT plans that include Codex (check your plan's usage limits) | Connect the repo once at chatgpt.com/codex (SETUP step A). Codex reads `AGENTS.md` → "Code Review Rules". It posts a normal GitHub review, not the JSON format; ask Claude to read the PR comments |
| **b) ChatGPT paste** — `bridge out` / `bridge in` | 2 clipboard actions | Your ChatGPT subscription; no API | Nothing beyond the one-time ChatGPT Project text in `chatgpt/PROJECT_INSTRUCTIONS.md` |
| **c) OpenAI API** — `ai-review` label | none | Paid per token (about $0.01–0.03 per review with `gpt-5-mini`, see [docs/COSTS.md](docs/COSTS.md)) | An OpenAI API key with credit, a repository secret, and `openai.enabled = true` (SETUP step B) |

Start with **a** if your plan has Codex, otherwise **b**. Turn on **c** only if you want it fully hands-off.

## Commands

Run from the repository root. Python 3.11+ and git; `gh` for PR features.

| Command | What it does |
|---|---|
| `ai-bridge/bridge` | Task board, who is waiting for you, API spending this month |
| `ai-bridge/bridge new "Title"` | New task file from the template (status `ready`) |
| `ai-bridge/bridge start T-0001` | Marks the task in progress and switches to branch `task/T-0001-…` |
| `ai-bridge/bridge check` | All free checks: shell syntax (`sh` + `dash`), Python syntax, icon theme, task/review files, secret scan, sensitive paths, bridge self-tests |
| `ai-bridge/bridge finish T-0001` | Runs the checks and writes `reports/T-0001-impl-N.md` (files changed, commits, results, owner-approval flags) |
| `ai-bridge/bridge out T-0001` | Review packet (task + report + diff + rules + answer format) → `.bridge-out/` and the clipboard |
| `ai-bridge/bridge in` | Reads ChatGPT's answer from the clipboard (or `--file`). A JSON review is recorded against its task; an `almond-decision` block becomes a proposed decision; an `almond-task` block becomes a backlog task |
| `ai-bridge/bridge in --pr 12` | Copies the GitHub Action's review comment on PR #12 into `reports/` |
| `ai-bridge/bridge review T-0001` | **Dry run**: shows the worst-case API cost. Pays only with `--live --yes-spend` **and** `openai.enabled = true` |
| `ai-bridge/bridge handoff` | Refreshes the generated sections of `docs/AI_HANDOFF.md` and `docs/PROJECT_STATUS.md` |
| `ai-bridge/bridge dashboard --open` | Writes and opens `.bridge-out/dashboard.html` (tasks, component status, reviews, spending) |
| `ai-bridge/bridge ready T-0004` | Moves a backlog task (e.g. one ChatGPT proposed) to ready |
| `ai-bridge/bridge duo "task"` | **Claude and Codex work on it together**: plan, critique, implement, review (max 2 rounds), transcript in `conversations/`. Never pushes. See [docs/DUO.md](docs/DUO.md) |
| `ai-bridge/bridge ask codex "question"` | Read-only question to Codex (or `ask claude`); answers kept in `conversations/ask-<date>.md` |
| `ai-bridge/bridge approve T-0001` | **Owner only.** Refuses to run without a real terminal, asks you to type the id, then offers to merge the PR |

## Files

```
CLAUDE.md                     rules + workflow for Claude (the implementer)
AGENTS.md                     rules for Codex/ChatGPT/other agents, incl. "Code Review Rules"
docs/PROJECT_STATUS.md        status of every component: PLANNED → DESIGNED → IMPLEMENTED → TESTED → APPROVED
docs/DESIGN_RULES.md          logo, colours, Almond Pure, packages, honesty
docs/AI_HANDOFF.md            where things stand; read first
docs/ROADMAP.md, ARCHITECTURE.md   (existing) milestones, OS architecture
ai-bridge/
  bridge                      the command (runs scripts/bridge.py)
  config/bridge.toml          limits, model, prices, sensitive paths      (owner approval to change)
  config/review-schema.json   the review answer format (JSON Schema)
  config/review-rules.md      what reviewers check (goes into every packet)
  tasks/                      one file per task: T-0001-….md
  reports/                    implementation reports and reviews
  decisions/                  decision records: D-0001-….md
  templates/                  task and decision templates; Claude-in-Actions template (inactive)
  chatgpt/PROJECT_INSTRUCTIONS.md   one-time text for a ChatGPT Project
  usage/usage.jsonl           log of paid API calls made from your terminal
  docs/                       SETUP, COSTS, SECURITY, TESTING
  tests/test_bridge.py        self-tests (no network)
.github/workflows/bridge-check.yml   free checks on every PR (no secrets)
.github/workflows/ai-review.yml      optional paid review (label-triggered, off by default)
.github/CODEOWNERS, pull_request_template.md
```

## Phases

| Phase | What | State |
|---|---|---|
| 1 | Shared docs, CLAUDE.md, AGENTS.md, task/report/review formats, CLI, free PR checks | Built and tested locally (see [docs/TESTING.md](docs/TESTING.md)). The workflows run once merged to `main` |
| 2 | OpenAI API review (local command + GitHub Action) | Built; tested with a fake API only. **Off** until you do SETUP step B |
| 3 | Claude in GitHub Actions | Template only (`templates/claude-code-action.yml.example`). Not active |
| 4 | Dashboard | Built: `bridge dashboard`, plus a check summary on each PR's Actions page |

## Known limitations

- ChatGPT's and Claude's chat histories are not shared. Anything that matters must be written into the repo (ask ChatGPT for an `almond-decision` block).
- Lane **b** still needs two clipboard actions per review.
- Codex's GitHub review uses its own format (only P0/P1 issues are flagged on GitHub) and is not converted into `reports/` automatically.
- The local spending log only sees calls made from your terminal. GitHub Actions calls are counted from the review comments on PRs; deleting those comments hides them from the monthly limit. The OpenAI project budget is the only hard limit.
- Token counts before a call are estimates (4 characters ≈ 1 token). The real cost is logged after the call from the API's usage numbers.
- `bridge check` checks files only. It does not build, boot or measure an Almond image.
- Prices in `config/bridge.toml` were copied from OpenAI's pricing page on 2026-10-17 and will drift.
