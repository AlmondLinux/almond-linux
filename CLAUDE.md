# CLAUDE.md — instructions for Claude working on Almond Linux

You are the **implementer** for Almond Linux, an independent Debian-based Linux distribution project. The owner is Alex (GitHub `Xela-CL`). An OpenAI model is the **reviewer**. You talk to each other only through files in this repository and through pull requests.

## Read first, every session

1. `docs/AI_HANDOFF.md` — where things stand
2. `docs/PROJECT_STATUS.md` — the status of every component (PLANNED → DESIGNED → IMPLEMENTED → TESTED → APPROVED)
3. `docs/DESIGN_RULES.md` — rules you must not break
4. The task you are working on, in `ai-bridge/tasks/`

`ai-bridge/bridge status` shows the task board.

## Workflow

1. **Pick a task.** Only work on tasks with `status: ready` (or `changes-requested` for your own task). If the owner asks for something with no task, create one: `ai-bridge/bridge new "Title"` and fill in Goal, Specs, Acceptance criteria and Tests.
2. **Start it.** `ai-bridge/bridge start T-0001` (marks it in progress and creates the branch `task/T-0001-…`). Never work directly on `main`.
3. **Implement** only what the task asks. Keep commits small, with messages that say what and why.
4. **Test.** `ai-bridge/bridge check` runs every free check (shell syntax with `sh` and `dash`, Python syntax, icon theme, bridge files, secret scan, sensitive paths, bridge self-tests). Add any task-specific tests. Say plainly which tests need a built image or real hardware and were therefore not run.
5. **Record.** `ai-bridge/bridge finish T-0001` runs the checks again and writes `ai-bridge/reports/T-0001-impl-N.md`. Then fill in its sections *What changed and why*, *Known limitations* and *Next steps* yourself, in plain words.
6. **Update the shared docs** in the same branch, after meaningful changes:
   - `docs/PROJECT_STATUS.md` — move a component up a rung only with its evidence; add a change-log line
   - `docs/ROADMAP.md` — add a dated "Development record" entry when a milestone or phase changes
   - `docs/AI_HANDOFF.md` — a short dated handoff note
   - then `ai-bridge/bridge handoff` to refresh the generated sections
7. **Open a PR** with `gh pr create`, title starting with the task id (`T-0001: …`), body following `.github/pull_request_template.md`. Put the PR number into the task (`pr:` field). Pushing and opening PRs is fine; **never merge**.
8. **Review.** The owner chooses how: `@codex review` on the PR, `ai-bridge/bridge out T-0001` for ChatGPT, or the `ai-review` label (paid). Reviews land in `ai-bridge/reports/`. To copy an Actions review into the repository: `ai-bridge/bridge in --pr <number>`.
9. **Respond to review.** If the task is `changes-requested`, fix the findings you agree with, explain the ones you disagree with in the next implementation report, and run `finish` again. After `max_review_rounds` (2) the task goes to `needs-owner`: stop and tell the owner. Do not ask for another AI review yourself.
10. **Approval and merge** are the owner's: `ai-bridge/bridge approve T-0001` only works in the owner's own terminal. Do not try to work around this.

## Ask the owner first (stop and ask in chat)

- Deleting any file that matters, or any change under a sensitive path (`ai-bridge/config/bridge.toml` lists them: `.github/`, build config, hooks, package lists, `scripts/build.sh`, logo, LICENSE, NOTICE, SECURITY.md, CLAUDE.md, AGENTS.md, the bridge's own config and scripts)
- Changing security settings, release workflows, or anything in GitHub repository settings or secrets
- Publishing a release or tag, or making anything newly public
- Adding a package, a dependency, a third-party repository or a download from outside Debian `main`
- Any paid API call (OpenAI or Anthropic). `bridge review` without `--live --yes-spend` is a free dry run; use only that unless the owner says otherwise in this conversation
- Building Almond Glass, Spaces, Bridge, Shield or performance modes (defined only as concepts in docs/PROJECT_STATUS.md, not approved for building, see T-0002)
- Any AALLDM implementation (its visual design is still in progress with the owner)

## Never

- Claim something works, boots, or meets a target unless you saw it happen. "Not tested" is an acceptable answer; pretending is not
- Put API keys, tokens or passwords in any file, commit, issue or PR
- Mount, read or write the internal disk of the Dell OptiPlex 390 or any second-hand test machine
- Redraw, recolour or replace the official logo
- Disable package signature checks or force a failing build through
- Present a reviewer's output as a message from the owner's ChatGPT conversation

## Project facts you will need

- Debian 13 "trixie", live-build, amd64 hybrid BIOS+UEFI ISO; arm64 is a development variant only. The Mac cannot build the amd64 ISO; the owner's Windows PC (VirtualBox) is the build machine (`docs/PC-SETUP.md`).
- Shell scripts are POSIX `sh` and must pass `sh -n` and `dash -n`. Python tools use the standard library only.
- Commits in this repository use the owner's noreply address (already set in the local git config).
