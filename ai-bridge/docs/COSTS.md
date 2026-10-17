# Costs

Checked 2026-10-17. Prices change; the sources are linked. **The free workflow costs nothing beyond subscriptions you already have.**

## What costs what

| Part | Cost |
|---|---|
| Shared docs, tasks, reports, `bridge` command | Free |
| GitHub Actions "Almond checks" | Free (public repositories get free Actions minutes) |
| Claude Code on your Mac/PC (implementer) | Included in your Claude subscription, within its usage limits. **Not** API credit |
| ChatGPT paste reviews (lane b) | Included in your ChatGPT subscription |
| Codex `@codex review` (lane a) | Included in ChatGPT plans that include Codex, within their limits. Check your plan; this was not verified for your account |
| OpenAI API reviews (lane c) | **Paid per token.** Separate billing at platform.openai.com; a ChatGPT subscription does not include it |
| Claude in GitHub Actions (phase 3) | With `claude setup-token`: uses your subscription's limits. With an Anthropic API key: paid per token |

## OpenAI API prices (USD per 1 million tokens)

From https://developers.openai.com/api/docs/pricing (standard tier):

| Model | Input | Output | Notes |
|---|---|---|---|
| `gpt-5-nano` | 0.05 | 0.40 | Cheapest; weaker reviews |
| **`gpt-5-mini`** | **0.25** | **2.00** | **Default.** Good value for code review |
| `gpt-5.4-mini` | 0.75 | 4.50 | |
| `gpt-5.4` | 2.50 | 15.00 | For big or tricky PRs |

Reasoning models bill their hidden reasoning as output tokens; `reasoning_effort = "low"` keeps that small.

## What one review costs

A review packet = rules + task + implementation report + diff. Output = the JSON review plus reasoning.

| PR size | Input tokens | Output tokens | `gpt-5-mini` | `gpt-5.4` |
|---|---|---|---|---|
| Small (docs, one script) | ~8,000 | ~2,000 | ~$0.006 | ~$0.05 |
| Medium | ~20,000 | ~3,000 | ~$0.011 | ~$0.10 |
| Largest allowed by the default limits | ~40,000 | 6,000 (cap) | ~$0.022 | ~$0.19 |

Estimates: 4 characters ≈ 1 token. The bridge logs the real numbers from the API after each call.

With `gpt-5.4` the default `per_call_limit_usd` ($0.10) refuses the largest packets; raise it if you switch models.

**A month:** 30 tasks × 2 review rounds × ~$0.01 ≈ **$0.60 with `gpt-5-mini`**.

## Claude API prices (only if you ever use an Anthropic API key)

Anthropic first-party rates, USD per 1 million tokens: Claude Haiku 5.5 $0.10 / $0.50 (prompts up to 100K tokens), Claude Sonnet 5.5 $2 / $10, Claude Opus 5.5 $4 / $20 (input / output). Source: https://www.anthropic.com/pricing. Not used by default: Claude works through your subscription.

## The limits built in

All in `ai-bridge/config/bridge.toml`:

| Setting | Default | Effect |
|---|---|---|
| `openai.enabled` | `false` | Master switch. Off = no paid call can happen |
| `max_review_rounds` | 2 | AI reviews per task / per PR before you must decide |
| `max_input_chars` | 160,000 | Bigger packets are refused (≈ 40k tokens) |
| `max_output_tokens` | 6,000 | Cap on the answer, reasoning included |
| `per_call_limit_usd` | $0.10 | Refuses a call whose worst case is above this |
| `monthly_limit_usd` | $2.00 | Refuses new calls once the month would pass this |

Plus two triggers that only you can pull: `--live --yes-spend` locally, or the `ai-review` label on GitHub (adding a label needs write access to the repository).

**The only hard limit is the budget you set on the OpenAI project** (SETUP step B.2). The bridge's limits depend on its own records (the local log, the PR comments) and are a second layer, not a guarantee.

## Cheapest setup

Keep `openai.enabled = false`. Use Codex (`@codex review`) or the ChatGPT paste lane. Total extra cost: $0.
