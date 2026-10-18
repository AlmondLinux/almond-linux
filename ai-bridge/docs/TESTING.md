# Testing the bridge

## Run the tests yourself

```sh
python3 -m unittest discover -s ai-bridge/tests -v   # 25 self-tests, no network
ai-bridge/bridge check                               # every free check, self-tests included
```

The self-tests replace the OpenAI API with a fake and write only to a temporary folder.

## What was tested on 2026-10-17 (macOS, Python 3.15, before the first PR)

| What | How | Result |
|---|---|---|
| Self-tests | `unittest`: front matter, ids, schema validation, JSON extraction, task creation, round limit, verdict → status, invalid reviews rejected, decision/task blocks, approve refuses without a terminal, cost guards (switch off, per-call, monthly, size), usage log, fake API success / HTTP error / incomplete answer, dry run never calls the API, secret patterns, sensitive paths, diff filter, doc markers | 25 passed |
| `bridge check` on the real repository | shell (`sh -n` + `dash -n`, 11 scripts), Python, icon theme, bridge files, secret scan (793 files), sensitive paths, self-tests | all pass; sensitive paths correctly WARN for this PR's own `.github/`, `CLAUDE.md`, `AGENTS.md` and bridge config/scripts |
| Full local workflow | In a throwaway clone: `new` → `start` (branch made) → commit → `finish` (report written) → `out` (packet) → `in` (pasted review) → `finish` → `in` → third `in` refused at the round limit; `status` shows "waiting for the owner" | works as designed |
| Paid path, without paying | In the clone: `openai.enabled = true` pointed at a fake local API server; `review` (dry run) then `review --live --yes-spend` | request had the key header, strict JSON schema, low reasoning, `store: false`; review saved; cost logged to `usage.jsonl` |
| GitHub Action logic, without GitHub | `ci-review` with a fake `gh` and the fake API | posts one comment with cost marker and JSON; second run stops at "2 AI reviews (limit 2)"; with $1.995 already recorded this month it refuses ("monthly limit reached"); no key → clean "no review was made" message; `in --pr` copies the comment into `reports/` |
| Dashboard | `bridge dashboard`, opened in a browser at phone width | renders tasks, cost guard and the component table from PROJECT_STATUS.md |

## Not tested yet

- The two GitHub Actions workflows on GitHub itself. `pull_request_target` workflows only run from the default branch, so they can only be tested after this PR is merged.
- A real OpenAI API call (not made: it costs money and needs your key).
- Codex `@codex review` on this repository (needs your ChatGPT/Codex account).
- `bridge approve` with a real terminal and a real PR merge.
- The clipboard on Windows and Linux (macOS `pbcopy`/`pbpaste` is used on the Mac).

## After merging: a 5-minute check

1. Open any small PR. The **Almond checks** job should appear and pass; its summary is on the run's page.
2. Optional, if you did SETUP step B: add the `ai-review` label. Expect one comment within two minutes, the label removed, and the cost in the comment.
