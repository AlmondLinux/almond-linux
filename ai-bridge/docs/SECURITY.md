# Security of the AI bridge

The project's own security policy (how to report vulnerabilities) is [SECURITY.md](../../SECURITY.md). This page covers how the AI workflow is kept safe.

## Secrets

- **No keys in files.** API keys live only in GitHub Actions secrets (`OPENAI_API_KEY`, optionally `CLAUDE_CODE_OAUTH_TOKEN`) or in your terminal's environment for one session. `.env` files are gitignored.
- `bridge check` scans every tracked and new file for things that look like OpenAI, Anthropic, GitHub, AWS keys and private keys, and fails if it finds one. The "Almond checks" workflow runs the same scan on every PR.
- If a key ever lands in a commit: **revoke it first** at the provider (platform.openai.com → API keys; console.anthropic.com; GitHub → Settings → Developer settings), then remove it from the history. Deleting the file is not enough: the old commit still contains it.

## Workflows

| Workflow | Trigger | Secrets | Token permissions | Runs PR code? |
|---|---|---|---|---|
| `bridge-check.yml` | every PR, manual | none | `contents: read` | Yes, but without secrets and with a read-only token |
| `ai-review.yml` | `ai-review` label, manual | `OPENAI_API_KEY` | `contents: read`, `pull-requests: write`, `issues: write` | **No.** `pull_request_target` runs the workflow and bridge script from `main`; the PR's diff is fetched as text and only sent to the model |

Why this matters: a workflow that holds a secret must never execute code from a pull request, or the PR could print the secret. `ai-review.yml` checks out the default branch only, with `persist-credentials: false`.

Other protections:

- **No loops.** Neither workflow runs on `push` or on comments. Comments posted with `GITHUB_TOKEN` never start workflows. The `ai-review` label is removed after each run, so each review needs a new, deliberate label.
- **No duplicates.** `concurrency` groups: one review at a time per PR; a newer check run cancels the older one.
- **Pinned actions.** `actions/checkout` is pinned to a full commit SHA (v7.0.1).
- **Timeouts.** 10 minutes per job.
- **Prompt injection.** A PR's text could try to instruct the reviewer model. The worst it can do is distort the review comment: the model has no tools, no write access and no secrets. Treat reviews as advice, never as approval.

## Who may do what

| Action | Who |
|---|---|
| Create tasks, write code on task branches, open PRs | Claude (and you) |
| Review | OpenAI models (and you) |
| Mark anything APPROVED, approve a task, merge | **Only you.** `bridge approve` refuses to run without an interactive terminal |
| Change sensitive paths (`.github/`, build config, hooks, package lists, `scripts/build.sh`, logo, LICENSE, NOTICE, SECURITY.md, CLAUDE.md, AGENTS.md, bridge config and scripts) or delete files | Claude must ask you first. The checks flag them ("OWNER APPROVAL REQUIRED") and CODEOWNERS requests your review |
| Change repository settings, secrets, branch protection, releases | Only you, in GitHub's web UI |
| Make paid API calls | Only through your explicit trigger (label or `--live --yes-spend`) with `enabled = true` |

Instructions for the agents themselves are in [CLAUDE.md](../../CLAUDE.md) and [AGENTS.md](../../AGENTS.md).

## Limits of these protections

- Claude Code runs with your own GitHub login on your computer, so technically it *could* merge. What stops it is CLAUDE.md, the TTY check in `bridge approve`, and your Claude Code permission settings. Branch protection on `main` (SETUP, last section) adds a real barrier.
- CODEOWNERS only requests your review; as the sole maintainer you cannot be forced to approve your own PR.
