# Duo mode: Claude and Codex work together

## The one Almond chat

```sh
ai-bridge/bridge view --open
```

**One conversation** between you, Claude and Codex, at http://127.0.0.1:4820 (in the Claude desktop app: the `almond-duo` browser preview). Type at the bottom:

- **Task:** Claude and Codex plan it, build it, review each other, and **open a PR when done**. You only merge.
- **Question:** Claude answers, then Codex checks the answer (agrees or corrects it).
- **They ask you something:** the chat shows the question and "waiting for your answer". Type the answer and press Send; the task carries on by itself. No commands needed.

Everything stays in that one chat, at `.bridge-out/chat.md` (local, survives branch switches). Each AI also keeps **one session for the whole chat**, so it remembers earlier tasks and answers. `ai-bridge/bridge chat --new` starts fresh sessions and keeps the log. `ai-bridge/bridge chat` shows the status. Each task's transcript is also committed with its PR (`ai-bridge/conversations/T-xxxx.md`).

Messages are handled one at a time, in order. Tasks branch from the branch the repository is on when the task starts, and the repository goes back to that branch afterwards.

The page only answers on 127.0.0.1 or localhost, and every message needs a secret that changes each time the page starts, so other websites can't send it commands.

## Running a task from a terminal

You give one task. Claude and Codex plan it, check each other, build it and review it, each doing the part it is better at. Every message between them is written to a transcript you can read. You approve the result.

```sh
ai-bridge/bridge duo "Fix the docs mismatches from the first VM test"
```

Or for an existing task: `ai-bridge/bridge duo T-0004`.

## How they talk

They don't share a chat. They talk through the repository:

- **Same knowledge:** both read the same files first: `docs/AI_HANDOFF.md`, the knowledge base in `docs/knowledge/` (decisions, corrections, test coverage), `docs/PROJECT_STATUS.md`, `docs/DESIGN_RULES.md`, and the task file.
- **Structured messages:** each turn is a JSON object in a fixed format (plan, plan review, implementation report, code review), so the other side can't misread it.
- **Transcript:** every turn is written to `ai-bridge/conversations/T-xxxx.md`, in order, with who spoke to whom.

```
You ──task──► Claude ──plan──► Codex ──critique──► Claude ──revised plan──┐
                                                                          │
   ┌──────────────────── implementer (Claude or Codex) ◄──────────────────┘
   │ edits files on the task branch
   ▼
 free checks (bridge check) ──► the OTHER one reviews the diff
   ▲                                   │
   └──── "request changes" (max 2) ◄───┤
                                       ▼ "approve" or out of rounds
                        report + transcript → you (needs-owner)
```

## Watching them talk

```sh
ai-bridge/bridge view --open
```

This opens a local page (http://127.0.0.1:4820) showing every conversation as chat bubbles: Claude in brown, Codex in blue, checks in green, and you in grey. It updates every 3 seconds and shows "Claude and Codex are working" while a duo run is going. You can leave it open in a browser tab during a run. Inside the Claude desktop app it opens in the browser pane (launch configuration `almond-duo`). The page is read-only and only reachable from this Mac.

## Who does what

From `ai-bridge/config/duo-roles.md`. These are working assumptions; change them in `bridge.toml [duo]` if the transcripts show otherwise.

| | Claude | Codex |
|---|---|---|
| Plans the task | ✔ (default) | |
| Criticises the plan before any code | | ✔ (default) |
| Implements docs, build config, design-sensitive work | ✔ | |
| Implements self-contained code with a clear test | | ✔ |
| Reviews the other's work | when Codex implemented | when Claude implemented |

The planner proposes the implementer and says why; the critic can object. You can force it with `--implementer claude` or `--implementer codex`.

The main reason to use two models: **each catches mistakes the other is blind to.** The reviewer is never the one who wrote the code.

## Limits and safety

- **Plan critique:** if the planner revises the plan, the critic's original concerns still go to the implementer and the reviewer, so they can't quietly disappear.
- **Plan critique rounds:** one. **Review rounds:** at most 2 (`max_review_rounds`). After that the task goes to you, even if they still disagree.
- **Questions only you can answer** (in the plan) stop the run **before any code is written.** Answer them in the task file or tell Claude, then run `ai-bridge/bridge duo T-xxxx` again.
- **Branches:** duo works on its own branch (`task/T-xxxx-…`), stacked on the branch you started from. It refuses to start with uncommitted changes, or on `main`.
- **Commits:** one commit per round. When a task is done, it pushes the task branch and opens a PR against the branch it started from (`open_pr = true` in `bridge.toml [duo]`; set it to `false` to keep branches local). **It never merges.**
- **If a run fails partway,** the work so far is committed to the task branch and the repository goes back to the base branch, so the next message still works.
- **What each AI may do:**
  - Codex runs in its sandbox: read-only for planning and review, workspace-write (no network) for implementing.
  - Headless Claude gets an allowlist: read tools, plus edit tools and syntax checks when implementing. `git commit`, `git push`, `git checkout`, `rm` and web tools are denied.
- **Honesty:** both follow `CLAUDE.md` / `AGENTS.md`: nothing counts as tested unless it was run, and the ISO can only be tested on the PC. Sensitive paths are listed in the report for your approval.

## Cost

Both run on subscriptions you already have:

- **Claude:** the Claude Code CLI on your Claude plan.
- **Codex:** the Codex CLI bundled with the ChatGPT desktop app (`/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex`), signed in with your ChatGPT account.
- **No surprise billing:** `ANTHROPIC_API_KEY` and `OPENAI_API_KEY` are removed from their environment, so no per-token API billing starts by accident.
- **Plan allowance:** a run uses some of each plan's usage. The transcript shows Codex's tokens and Claude's "API-equivalent" figure; that figure is not a charge on a subscription.
- **Your Codex settings:** `~/.codex/config.toml` sets the model to `gpt-6-astra` with `service_tier = "priority"`, and duo uses those settings. If priority uses your allowance faster, set `codex_model` in `bridge.toml [duo]`, or change your Codex config.

## Questions for both

```sh
ai-bridge/bridge discuss "Is the 300 MiB target measured with a terminal open?"
```

Claude answers, then Codex checks the answer. Both replies go to the chat. The chat page's **Question** mode does exactly this.

## Asking the other AI a question

```sh
ai-bridge/bridge ask codex "Does the 0300 hook work with dash?"
ai-bridge/bridge ask claude "Which docs still say 300 MB instead of MiB?"
```

Read-only. Answers (with sources and confidence) are kept in `ai-bridge/conversations/ask-<date>.md`. Claude uses this during a chat session to get Codex's second opinion; add `--from-ai` so the log shows who asked.

## What this is not

- **Not your ChatGPT conversation.** Codex works from the repository; it doesn't remember your ChatGPT chats. Anything that matters must be written into the repo (decision records, tasks, `docs/knowledge/`).
- **Not unattended merging.** Every result waits for you.
- **Not claudex.** claudex runs Claude Code with other models through a proxy. Duo uses the two official CLIs, so you get two different agents.

## If something goes wrong

| Message | Fix |
|---|---|
| `Codex CLI not found` | Install the ChatGPT desktop app, or `npm i -g @openai/codex`, then `codex login` |
| `Codex failed … not logged in` | Open the ChatGPT app → Codex, or run `codex login` |
| `Claude failed` | Run `claude` once in a terminal and sign in |
| `did not finish within 25 minutes` | Raise `timeout_minutes` in `bridge.toml [duo]`, or split the task |
| `answer did not match …schema` | Re-run; if it repeats, the model ignored the format. The transcript shows the last good step |
