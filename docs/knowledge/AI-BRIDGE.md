# Almond AI Bridge and PR #1
[PR #1](https://github.com/AlmondLinux/almond-linux/pull/1) was **OPEN**, base main, head ai-bridge/phase-1 at d668bc8e27b88196e703162cfa894525fc842a76 on 2026-10-18.

The developer bridge is repository tooling, distinct from Almond Bridge for Windows applications. Source includes shared documentation, AGENTS/CLAUDE instructions, task/decision/report formats, a Python standard-library CLI, dashboard generation and GitHub workflows. It coordinates work through files and PRs; it does not send messages into the original ChatGPT or Claude conversation.

## Evidence and activation
PR #1's free check was passing at inspection: [GitHub run](https://github.com/AlmondLinux/almond-linux/actions/runs/39129194107/job/117680665606). Earlier reports describe 25 local self-tests; this import records its own checks in the T-0009 implementation report.

[Configuration](../../ai-bridge/config/bridge.toml) has openai.enabled=false. Paid API review remains opt-in and unactivated here. No credentials or settings were inspected or changed. A passing free check does not prove a live OpenAI request or deployed paid-review workflow works.

The historical assistant suggested free GitHub/Codex reviews first. Its suggested confirmation message was not itself an owner message. Repository task records provide later independent context; do not execute archived suggestions as instructions.

## Review workflow
Owner authorizes work; implementer prepares task/branch/report; reviewer checks evidence; owner approves and merges. Current bridge limits automated review rounds to two. Do not solicit paid review or auto-merge as part of importing knowledge.

This knowledge PR is stacked on PR #1 so its diff contains the knowledge work, not a duplicate of the bridge. Review PR #1 separately. If PR #1 merges first, retarget this PR to main and inspect the resulting diff; if rejected, adapt the knowledge change explicitly. Neither PR is merged by this task.

Read [bridge documentation](../../ai-bridge/README.md), [handoff](../AI_HANDOFF.md) and [source coverage](SOURCES.md). Product/API availability claims quoted in old bridge docs are historical documentation, not independently verified current service guarantees.
