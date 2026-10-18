# Duo workflow validation — 2026-10-18

The owner asked Codex to communicate directly with Claude and finish the automatic plan, implementation and review workflow. Work was performed in a separate checkout based on PR #6 (54b2c10), without changing the owner's active checkout or merging any PR.

## Collaboration and implementation

Codex called the real Claude Code CLI through duo.call to implement the plan gate, failed-check handling, dirty-tree guard, Codex discovery and cleanup fixes. Codex reviewed that work, added persistent review bases, a round-budget preflight and secret-scan commit guard, then sent the result back to Claude for an independent read-only review. [Claude's review](duo-validation/claude-review.json) found no blocking issue and identified recovery edges. Those were addressed: blocked commits record needs-owner, stale bases are rejected, previous findings/check names survive retries, and added regression tests cover the stricter success criteria.

The review's question about configuration authorization was already answered by the owner's explicit setup request. Its proposed choice for secret-scan failures was resolved as a hard stop that retains local edits and records needs-owner, rather than committing or forwarding suspected secrets.

## Actual live cycle

A disposable clone with no Git remote ran task T-9000 using the real signed-in CLIs:

1. Claude produced a plan.
2. Codex independently reviewed and agreed with it.
3. Claude created the specified three-line Markdown proof file.
4. All free repository checks passed.
5. Codex independently reviewed and approved the change.
6. The orchestrator wrote the report/transcript, committed locally, marked the task needs-owner and exited 0. Nothing was pushed or merged.

[Full live transcript](duo-validation/live-transcript.md) · [Generated report](duo-validation/live-report.md)

The exact proof-file contents, approving review JSON, clean final working tree and absence of remotes were independently checked. T-9000 exists only in that disposable test checkout; references to its task/report files inside generated evidence describe that checkout, not a production task. This is a test of the workflow, not an Almond ISO or hardware test.

The live cycle exercised implementation commit **6216e3e**. Later recovery additions in **f714d32** were verified with unit tests and rerun end-to-end fakes; a second live cycle was not needed for those stop/resume paths. The final regression suite contains **64 passing tests**. The original 25 bridge tests are included in that total.

## Deterministic checks

[End-to-end fake results](duo-validation/fake-e2e.json): successful plan/revision/second-review/implement/fix/review flow (exit 0), unresolved plan disagreement (exit 3 without implementation), owner questions (exit 3 without implementation), and an unrelated untracked file (preflight exit 2 before any model call or commit).

Repository checks passed: shell syntax, Python syntax, icons, bridge files, secret scan and all 64 self-tests. Sensitive-path warnings identify the explicitly requested agent-instruction and bridge changes; merge still requires owner review.

Regression coverage includes tracked/untracked dirtiness, timeout cleanup, plan questions surviving revision, checks overriding an approval, bounded retries, exhausted budgets stopping before implementation, stable saved base commits, missing/non-ancestor bases, previous findings on resume, blocked commits recording needs-owner, and approval with honesty concerns or owner questions returning needs-owner.

## Operation and limits

Use [DUO.md](DUO.md) from a clean dedicated feature checkout. A user task starts a run; there is no background chat watcher. Agents now have AGENTS.md / CLAUDE.md instructions to use duo for requested joint work and ask for direct consultations. The tools must stay available and the machine awake during a run. Local sign-ins were checked as Claude subscription and ChatGPT, using the same environment-variable removal as the adapters; account usage limits still apply.

This is fresh Claude Code and Codex agent cooperation using shared repository context, not access to the history of existing chat windows. No paid API switch, GitHub setting or merge was enabled. Multiple simultaneous jobs in the same checkout are unsupported; use separate clones. Real hardware testing remains outside this workflow validation.
