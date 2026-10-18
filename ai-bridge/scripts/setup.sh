#!/bin/sh
# SPDX-License-Identifier: MIT
# Almond AI Bridge - local setup check.
#
#     sh ai-bridge/scripts/setup.sh            # check this computer, run the bridge checks
#     sh ai-bridge/scripts/setup.sh --github   # also create the GitHub labels the workflows use
#
# Installs nothing and makes no paid calls. --github only creates labels.
set -u
here=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
root=$(dirname -- "$here")
cd "$root" || exit 1
ok=0

say() { printf '%s\n' "$*"; }
need() {
	if command -v "$1" >/dev/null 2>&1; then say "  ok    $1"; else say "  MISSING $1 - $2"; ok=1; fi
}

say "Almond AI Bridge setup check ($root)"
need git "install Xcode command line tools (xcode-select --install) or git from git-scm.com"
need python3 "install Python 3.11 or newer (brew install python)"
if command -v python3 >/dev/null 2>&1; then
	if python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)'; then
		say "  ok    python3 is $(python3 -c 'import platform; print(platform.python_version())')"
	else
		say "  OLD   python3 must be 3.11 or newer (tomllib)"; ok=1
	fi
fi
if command -v gh >/dev/null 2>&1; then
	if gh auth status >/dev/null 2>&1; then say "  ok    gh is logged in"; else say "  WARN  gh is not logged in: run 'gh auth login' (needed for PRs and review comments)"; fi
else
	say "  WARN  gh not found: brew install gh (needed for PRs and review comments)"
fi
if command -v dash >/dev/null 2>&1; then say "  ok    dash (Debian's /bin/sh) for shell checks"; else say "  INFO  dash not found: shell scripts are only checked with sh (brew install dash)"; fi
[ "$ok" -eq 0 ] || { say "Fix the items above, then run this again."; exit 1; }

if [ "${1:-}" = "--github" ]; then
	repo=$(gh repo view --json nameWithOwner --jq .nameWithOwner) || exit 1
	say "Creating labels in $repo (existing ones are updated)"
	gh label create ai-review --repo "$repo" --color 8B5A2B --force \
		--description "Owner: run one paid OpenAI review of this PR" && \
	gh label create needs-owner-approval --repo "$repo" --color D93F0B --force \
		--description "Touches sensitive paths or deletes files" && \
	gh label create ai-task --repo "$repo" --color D2A679 --force \
		--description "Work tracked by the Almond AI Bridge" || ok=1
fi

say ""
say "Running the bridge checks:"
python3 ai-bridge/scripts/bridge.py check || ok=1
say ""
python3 ai-bridge/scripts/bridge.py status
say ""
say "Next: read ai-bridge/README.md. Optional paid reviews: ai-bridge/docs/SETUP.md step B."
exit "$ok"
