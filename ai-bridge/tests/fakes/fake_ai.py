#!/usr/bin/env python3
# Test double for the Claude Code and Codex CLIs, used by test_duo.py and
# the duo end-to-end test. Reads the prompt from stdin, answers each duo step
# with a canned JSON object. Never calls a network.
#   FAKE_AI_STATE  directory for a round counter (review: changes, then approve)
#   FAKE_AI_QUESTIONS=1  plan contains a question for the owner
import json, os, sys

who = "codex" if os.path.basename(sys.argv[0]).startswith("fake_codex") else "claude"
args = sys.argv[1:]
prompt = sys.stdin.read()
state = os.environ.get("FAKE_AI_STATE", "")

def bump(name):
    if not state:
        return 1
    os.makedirs(state, exist_ok=True)
    path = os.path.join(state, name)
    n = int(open(path).read()) + 1 if os.path.exists(path) else 1
    open(path, "w").write(str(n))
    return n

if "Current step: PLAN REVIEW" in prompt:
    out = {"verdict": "change", "concerns": ["add a test"], "missing_steps": ["run bridge check"],
           "implementer_agree": True, "notes": "fine otherwise"}
elif "Current step: PLAN" in prompt:
    out = {"summary": "Add docs/DUO-DEMO.md.", "steps": [{"what": "write the file", "files": ["docs/DUO-DEMO.md"]}],
           "tests": ["ai-bridge/bridge check"], "risks": [], "implementer": "codex",
           "implementer_reason": "small self-contained change", "sensitive_paths": [],
           "questions_for_owner": ["Which wording?"] if os.environ.get("FAKE_AI_QUESTIONS") else []}
elif "Current step: IMPLEMENT" in prompt or "Current step: FIX" in prompt:
    n = bump("implement")
    with open("docs/DUO-DEMO.md", "a") as f:
        f.write("Demo line %d written by fake %s.\n" % (n, who))
    out = {"summary": "wrote demo line %d" % n, "files_changed": ["docs/DUO-DEMO.md"],
           "tests_run": [{"command": "none", "result": "fake"}], "not_done": ["needs the PC"],
           "notes_for_reviewer": "fake"}
elif "Current step: REVIEW" in prompt:
    n = bump("review")
    out = {"verdict": "request_changes" if n == 1 else "approve", "summary": "fake review %d" % n,
           "findings": [{"severity": "minor", "file": "docs/DUO-DEMO.md", "line": 1, "issue": "x", "suggestion": "y"}] if n == 1 else [],
           "status_claims_ok": True, "honesty_issues": [], "tests_assessment": "fake", "questions_for_owner": []}
elif "Check the answer against the repository" in prompt:
    out = {"agrees": True, "answer": "fake %s agrees" % who, "confidence": "medium", "sources": ["AGENTS.md"]}
else:
    out = {"answer": "fake answer from %s" % who, "confidence": "low", "sources": ["AGENTS.md"]}
if state:
    os.makedirs(state, exist_ok=True)
    # Record which session each call used, so tests can check "one chat".
    with open(os.path.join(state, "sessions.log"), "a") as f:
        sid = args[args.index("resume") + 1] if "resume" in args else (
            args[args.index("--resume") + 1] if "--resume" in args else "new")
        f.write("%s %s\n" % (who, sid))

if who == "codex":
    target = args[args.index("-o") + 1]
    open(target, "w").write(json.dumps(out))
    if "--json" in args:
        if "resume" not in args:
            print(json.dumps({"type": "thread.started", "thread_id": "fake-codex-thread"}))
        print(json.dumps({"type": "turn.completed", "usage": {"input_tokens": 1000, "output_tokens": 234}}))
    else:
        print("codex\n%s\ntokens used\n1,234" % json.dumps(out))
else:
    sid = args[args.index("--resume") + 1] if "--resume" in args else (
        args[args.index("--session-id") + 1] if "--session-id" in args else "fake-claude-session")
    print(json.dumps({"type": "result", "subtype": "success", "is_error": False, "num_turns": 2,
                      "total_cost_usd": 0.01, "session_id": sid, "result": json.dumps(out), "structured_output": out}))
