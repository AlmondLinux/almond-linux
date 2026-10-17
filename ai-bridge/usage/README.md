# Usage log

`usage.jsonl` gets one line per paid OpenAI API call made from a local terminal (`bridge review --live --yes-spend`): time, task, model, tokens, cost in USD. `bridge status` and the dashboard add up the current month from it.

Calls made by GitHub Actions are not written here (that would need the workflow to commit to the repository). Their cost is written into each AI review comment on the pull request, and the workflow adds those up to enforce the monthly limit.
