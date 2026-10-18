# Almond Duo for macOS

A local app for one prompt to Claude Code and Codex, with their visible replies saved together.

- **Ask both:** both answer concurrently, then each responds to the other answer. Read-only.
- **Build together:** Claude plans and implements; Codex reviews the plan and result. Checks and bounded fixes run automatically. Owner questions stop the run.
- The feed shows completed replies, plans, reviews and results, not private reasoning or token streaming. Details shows the current stage, workspace and process log.
- Stop cancels the worker and its child processes. Closing the app stops ongoing work. Keep it open while running.
- History and Markdown transcripts persist in `~/Library/Application Support/Almond Duo`. Download transcript exports the selected conversation.
- Every run uses an isolated clone. A follow-up carries the previous conversation (up to 24,000 characters); after a completed run it also starts from that run’s committed workspace. Other follow-ups start from the bundled project snapshot. These are new runs, not resumptions of a paused task.
- No automatic push, merge or release. Finished branches remain local for review. Details gives their workspace path.

## Requirements and launch

This local build uses the existing Python 3, Claude Code and Codex installations on this Mac. Both CLIs must already be signed in with their subscriptions. It strips API-key environment variables and does not enable paid API review. Plan usage limits still apply.

Build from a committed checkout with `python3 ai-bridge/app/build-macos.py /absolute/path/Almond\ Duo.app`, then open the app. This is an ad-hoc signed local build, not a notarized standalone installer for other Macs. It bundles the current committed project snapshot; it does not auto-update from GitHub.

For development, run `python3 ai-bridge/app/server.py --ready /tmp/almond-ready.json` and open the local URL in that file. The service binds only to loopback and requires a random session token; cross-origin requests and foreign Host headers are rejected.

The agents are fresh CLI sessions with shared repository knowledge, not the existing Claude or ChatGPT chats. The historical ChatGPT archive remains partial as documented in `docs/knowledge/README.md`.
