# Duo mode: Claude and Codex work together

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

- **Plan critique:** if the critic asks for changes (or objects to the implementer), the planner revises once and the critic reviews the revision a second time. If they still disagree, the run **stops before any code is written** and the task goes to you (`needs-owner`); the disagreement is added to the task file. `--ignore-questions` does not skip this.
- Original plan-critic concerns are saved and forwarded to both implementation and final review, even after the revised plan is accepted.
- **Review rounds:** at most 2 (`max_review_rounds`). After that the task goes to you, even if they still disagree.
- **Free checks decide too:** a failed `bridge check` always sends the implementer back for a fix round, even if the reviewer approved. If checks still fail when the rounds run out, the result is **failed** (exit code 1), not done. Only "reviewer approved and every check passed" counts as success (exit code 0); an unresolved review ends as needs-owner (exit code 3).
- **Questions only you can answer** (in the plan or its revision; a revision cannot drop an earlier question) stop the run **before any code is written.** They are added to the task file; answer them there or tell Claude, then run `ai-bridge/bridge duo T-xxxx` again.
- **Branches:** duo works on its own branch (`task/T-xxxx-…`), stacked on the branch you started from. It refuses to start on `main` or with any change in the working tree, tracked or untracked (it lists them), because each round commits with `git add -A`. Ignored files (`.gitignore`, e.g. Python caches) are not affected.
- **Commits:** the orchestrator makes one commit per round. **It never pushes, opens PRs or merges.**
- **What each AI may do:**
  - Codex runs in its sandbox: read-only for planning and review, workspace-write (no network) for implementing.
  - Headless Claude gets an allowlist: read tools, plus edit tools and syntax checks when implementing. `git commit`, `git push`, `git checkout`, `rm` and web tools are denied.
- **Honesty:** both follow `CLAUDE.md` / `AGENTS.md`: nothing counts as tested unless it was run, and the ISO can only be tested on the PC. Sensitive paths are listed in the report for your approval.

## Cost

Duo is meant to run on subscriptions you already have:

- **Claude:** the Claude Code CLI signed in with your Claude plan.
- **Codex:** the Codex CLI bundled with the ChatGPT desktop app (`/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex`, or the binary in `…/codex-cli/CodexCLI.app/Contents/MacOS/codex`), signed in with your ChatGPT account.
- **API keys in the environment:** `ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN`, `OPENAI_API_KEY` and `CODEX_API_KEY` are removed from the CLIs' environment, so a key set for other work is not picked up by accident.
- **That alone does not guarantee subscription billing.** Billing depends on how each CLI itself is signed in: a CLI logged in with an API key (for example `codex login --with-api-key`, or a Claude Code setup that uses an API key or a key helper from its settings) is billed per token even with the variables removed, and a plan's paid extra usage, if you turned it on, can also cost money. Check before a run: `claude auth status` should report your claude.ai subscription, and `codex login status` should report a ChatGPT login.
- **Plan allowance:** a run uses some of each plan's usage. The transcript shows Codex's tokens and Claude Code's "API-equivalent" figure; when Claude is signed in with a subscription that figure is an estimate, not a charge.
- **Your Codex settings:** `~/.codex/config.toml` sets the model to `gpt-6-astra` with `service_tier = "priority"`, and duo uses those settings. If priority uses your allowance faster, set `codex_model` in `bridge.toml [duo]`, or change your Codex config.

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

## Resume and local setup

Run from a dedicated, clean feature checkout. The original base commit is saved as `duo_base` in the task so later reviews retain earlier work. Exhausted review limits are checked before calling either model. Automatic commits rerun the secret scan and refuse on a match. Do not run simultaneous jobs or make manual edits in the same checkout while duo is running.

Check the same authentication environment used by duo before your first live run:

```sh
env -u ANTHROPIC_API_KEY -u ANTHROPIC_AUTH_TOKEN claude auth status
env -u OPENAI_API_KEY -u CODEX_API_KEY codex login status
```

Use subscription sign-ins for this setup; resolving an authentication failure is not authorization to enable API billing. The local tools and the computer must remain running during a task. This is an on-demand workflow, not an always-on watcher of existing chat windows.

A secret-scan or automatic-commit failure is a hard stop: the task is marked `needs-owner`, its transcript records the stop, and local edits are retained without committing them. Repair those files before resuming. Other failed checks use the bounded fix loop. On a retry, the previous review and failed check names are passed to the implementer and round labels continue counting. If a saved review base is missing or no longer an ancestor after a rebase, duo refuses to guess a replacement; verify and update `duo_base` explicitly.
