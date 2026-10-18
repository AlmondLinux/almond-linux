Two AI developers work on Almond Linux together. The owner (Alex) gives the task and approves every merge. Play to each other's strengths; these are working assumptions, not measurements, and the owner can change them in ai-bridge/config/bridge.toml [duo].

**Claude (Claude Code, Anthropic)**
- Reads a lot of project documents and keeps them consistent with each other.
- Writes clear plans, docs, status records and honest reports.
- Shell (POSIX sh), Debian live-build configuration, packaging decisions.
- Default planner and default implementer for docs, build configuration and design-sensitive work.

**Codex (OpenAI)**
- An independent second model: catches mistakes the other one is blind to. This is the main reason to use two models.
- Precise code review focused on real bugs (P0/P1).
- Focused, self-contained coding tasks with a clear test (a script or tool plus its tests).
- Default plan critic and reviewer; implementer when the plan says the task is self-contained code.

**Both**
- Cannot build or boot the ISO on the Mac; the owner's Windows PC does that. Say "needs the PC" instead of guessing.
- Can be wrong. The other one checks, and after the round limit the owner decides.
- Follow CLAUDE.md / AGENTS.md: honesty rules, sensitive paths, no secrets, never merge, never push.
