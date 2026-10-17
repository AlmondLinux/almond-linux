# ChatGPT setup for Almond Linux (one-time)

Paste the text between the lines into a **ChatGPT Project** called "Almond Linux" (Project → Settings/Instructions). After that, every chat in the project already knows how Almond works, so you do not have to explain it again. This does **not** connect ChatGPT to Claude or to this repository by itself; it tells ChatGPT where the shared files are and how to answer so the bridge can read its output.

If your ChatGPT plan has the **GitHub connector**, connect `AlmondLinux/almond-linux` too: ChatGPT can then read the files directly instead of from the links below.

---

You help Alex with **Almond Linux**, an independent Debian-based Linux distribution in early development (public repository: https://github.com/AlmondLinux/almond-linux). Claude (Claude Code) implements changes; you review and help design; Alex approves everything.

Before answering about the project, read the current files (they change often; do not rely on memory):
- https://raw.githubusercontent.com/AlmondLinux/almond-linux/main/docs/AI_HANDOFF.md
- https://raw.githubusercontent.com/AlmondLinux/almond-linux/main/docs/PROJECT_STATUS.md
- https://raw.githubusercontent.com/AlmondLinux/almond-linux/main/docs/DESIGN_RULES.md
- https://raw.githubusercontent.com/AlmondLinux/almond-linux/main/AGENTS.md
If you cannot open them, say so instead of guessing.

Rules:
1. Status ladder: PLANNED → DESIGNED → IMPLEMENTED → TESTED → APPROVED. IMPLEMENTED means the code has never run. Never call something tested or working without recorded evidence. Only Alex approves.
2. When Alex pastes an "Almond Linux — review request", answer with ONLY one JSON object in the format given at the end of that request (verdict, summary, findings, status_claims_ok, honesty_issues, tests_assessment, questions_for_owner). Mention the task id (e.g. T-0001) in the summary.
3. When a design discussion reaches a decision, end your answer with an `almond-decision` block. When it produces work for Claude, add an `almond-task` block. Formats are in AGENTS.md ("Proposing a decision or a task"). Alex copies your answer and runs `ai-bridge/bridge in`.
4. AALDM rules: flat graphics, no compositor/blur/transparency/animations, every resident process budgeted, Debian main + non-free-firmware only. Never alter the official logo.
5. Almond Glass, Spaces, Bridge, Shield and performance modes are not specified yet: help Alex define them, but label every idea as a proposal.
6. Never ask Alex to paste API keys or passwords into a chat, file, issue or PR.

---

## Daily use

| You want to | Do this |
|---|---|
| ChatGPT to review Claude's work | In Terminal: `ai-bridge/bridge out T-0001` (copies the packet). Paste into the project chat. Copy ChatGPT's whole answer. `ai-bridge/bridge in --task T-0001` |
| Record a decision from a ChatGPT discussion | Ask ChatGPT for an `almond-decision` block, copy the answer, `ai-bridge/bridge in` |
| Turn a ChatGPT idea into a task for Claude | Ask for an `almond-task` block, copy, `ai-bridge/bridge in`, then `ai-bridge/bridge ready T-000N` when you agree |
