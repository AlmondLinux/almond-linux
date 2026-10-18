#!/usr/bin/env python3
# Test double for the Claude Code and Codex CLIs, used by test_duo.py and
# the duo end-to-end test. Reads the prompt from stdin, answers each duo step
# with a canned JSON object. Never calls a network.
#   FAKE_AI_STATE  directory for a round counter (review: changes, then approve)
#   FAKE_AI_QUESTIONS=1  plan contains a question for the owner
#   FAKE_AI_PLAN_DISAGREE=1  the second plan review still asks for changes
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
    # First review asks for a change; the second (of the revision) agrees
    # unless FAKE_AI_PLAN_DISAGREE=1.
    second = "second and last review" in prompt
    if second and not os.environ.get("FAKE_AI_PLAN_DISAGREE"):
        out = {"verdict": "agree", "concerns": [], "missing_steps": [],
               "implementer_agree": True, "notes": "revision is fine"}
    else:
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
else:
    out = {"answer": "fake answer from %s" % who, "confidence": "low", "sources": ["AGENTS.md"]}

if who == "codex":
    target = args[args.index("-o") + 1]
    open(target, "w").write(json.dumps(out))
    print("codex\n%s\ntokens used\n1,234" % json.dumps(out))
else:
    print(json.dumps({"type": "result", "subtype": "success", "is_error": False, "num_turns": 2,
                      "total_cost_usd": 0.01, "result": json.dumps(out), "structured_output": out}))
