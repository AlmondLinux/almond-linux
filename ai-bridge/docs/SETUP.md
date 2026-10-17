# Setup

Step 0 is all you need for the free workflow. A, B and C are optional.

## 0. Local setup (free, 2 minutes)

On the Mac (or any computer with the repository):

```sh
cd ~/Documents/"New project"/almond-linux
sh ai-bridge/scripts/setup.sh
```

It checks Python 3.11+, git, `gh` login and `dash`, runs the bridge checks and prints the board. It changes nothing on GitHub unless you add `--github`, which creates the three labels the workflow uses (`ai-review`, `needs-owner-approval`, `ai-task`).

Optional shortcut so you can type `bridge` anywhere inside the repo:

```sh
echo 'alias bridge="git rev-parse --show-toplevel >/dev/null 2>&1 && \"\$(git rev-parse --show-toplevel)/ai-bridge/bridge\""' >> ~/.zshrc
```

**ChatGPT (one time):** create a Project called "Almond Linux" in ChatGPT and paste the instructions from [`chatgpt/PROJECT_INSTRUCTIONS.md`](../chatgpt/PROJECT_INSTRUCTIONS.md). If your plan offers the GitHub connector, connect `AlmondLinux/almond-linux` too.

**Claude:** nothing to set up. Claude Code reads `CLAUDE.md` automatically when it starts in this repository, on the Mac or on the Windows PC.

## A. Codex reviews on GitHub (no API key)

Only if your ChatGPT plan includes Codex. Check at chatgpt.com/codex.

1. Open **chatgpt.com/codex** → connect GitHub → allow access to **AlmondLinux/almond-linux** only.
2. In Codex settings → **Code review**, pick the repository. Leave **Automatic review off** (you decide when a review happens).
3. On a pull request, comment `@codex review`. Codex follows the "Code Review Rules" in `AGENTS.md`.

## B. OpenAI API reviews in GitHub Actions (paid, optional)

Costs money per review (see [COSTS.md](COSTS.md)). Your ChatGPT subscription does **not** include API credit; the API is billed separately.

1. **Account and credit:** go to **platform.openai.com**, sign in, open **Settings → Billing**, add a payment method and a small prepaid amount (for example $5). Turn auto-recharge **off**.
2. **Hard spending limit:** in **Settings → Limits** (or the project's budget settings), set a monthly budget, for example $5. This is the only limit OpenAI itself enforces; the bridge's limits are an extra layer.
3. **Project and key:** create a project named "almond-ai-bridge" (Settings → Projects), then **API keys → Create new secret key** in that project. Copy it once. Never paste it into a file, chat, issue or PR.
4. **Store it as a GitHub secret** (from your own terminal; `gh` asks for the value without echoing it):
   ```sh
   gh secret set OPENAI_API_KEY --repo AlmondLinux/almond-linux
   ```
   or GitHub → repository → **Settings → Secrets and variables → Actions → New repository secret**, name `OPENAI_API_KEY`.
5. **Switch it on:** in a PR, change `enabled = false` to `enabled = true` under `[openai]` in `ai-bridge/config/bridge.toml`, and check the limits there. Merge it. The workflow reads this file from `main`.
6. **Use it:** add the label **ai-review** to a pull request. The review appears as a PR comment within a minute or two; the label is removed automatically. Copy it into the repository with `ai-bridge/bridge in --pr <number>`.

**Kill switch:** delete the secret (`gh secret delete OPENAI_API_KEY --repo AlmondLinux/almond-linux`) or set `enabled = false`. Either stops all paid calls.

**From your own terminal instead** (no GitHub secret needed): put the key in your shell for one session only, then run a review:

```sh
read -rs OPENAI_API_KEY && export OPENAI_API_KEY
ai-bridge/bridge review T-0001                       # dry run: shows the cost
ai-bridge/bridge review T-0001 --live --yes-spend    # paid
```

## C. Claude in GitHub Actions (optional, not active)

Lets you write `@claude …` in an issue or PR comment and have Claude Code work in a GitHub runner. Not needed while you run Claude Code on your own computers.

1. On your Mac: `claude setup-token` (uses your Claude Pro/Max subscription; prints a token once). An Anthropic API key from console.anthropic.com also works but is billed per token.
2. `gh secret set CLAUDE_CODE_OAUTH_TOKEN --repo AlmondLinux/almond-linux` and paste the token.
3. In a PR, copy `ai-bridge/templates/claude-code-action.yml.example` to `.github/workflows/claude.yml`. Read the action's README first: https://github.com/anthropics/claude-code-action
4. Only comments from the repository owner start it. It never merges.

## Recommended GitHub settings (you change these; the bridge does not)

- **Settings → Branches → Add rule for `main`:** require a pull request before merging; require the "Almond checks" status check. (Do not require an approving review if you are the only maintainer: GitHub does not let you approve your own PR.)
- **Settings → Actions → General:** "Fork pull request workflows from outside collaborators: Require approval for all outside collaborators"; Workflow permissions: **Read repository contents** (the workflows ask for more only where they need it).
