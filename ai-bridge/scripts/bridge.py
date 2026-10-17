#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Almond Linux - Almond AI Bridge: the task / report / review workflow that
# lets Claude (implementer) and an OpenAI model (reviewer) work on this
# repository through Git files instead of copy and paste.
#
#     ai-bridge/bridge                     # status board
#     ai-bridge/bridge new "Title"         # create a task
#     ai-bridge/bridge start T-0001        # mark in progress, make a branch
#     ai-bridge/bridge check               # run every free local check
#     ai-bridge/bridge finish T-0001       # record results, ask for review
#     ai-bridge/bridge out T-0001          # review packet -> clipboard
#     ai-bridge/bridge in                  # ChatGPT's answer <- clipboard
#     ai-bridge/bridge review T-0001       # paid OpenAI review (dry run unless
#                                          #   enabled AND --live --yes-spend)
#     ai-bridge/bridge handoff             # refresh generated doc sections
#     ai-bridge/bridge dashboard --open    # local HTML status page
#     ai-bridge/bridge approve T-0001      # OWNER ONLY (needs a real terminal)
#
# Standard library only (Python 3.11+ for tomllib). No command makes a paid
# API call unless openai.enabled is true in the config AND the caller passes
# --live --yes-spend (locally) or the owner adds the ai-review label (CI).

import argparse
import datetime as dt
import fnmatch
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tomllib
import urllib.error
import urllib.request

BRIDGE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(BRIDGE)
CONFIG_PATH = os.path.join(BRIDGE, "config", "bridge.toml")
SCHEMA_PATH = os.path.join(BRIDGE, "config", "review-schema.json")
TASKS = os.path.join(BRIDGE, "tasks")
REPORTS = os.path.join(BRIDGE, "reports")
DECISIONS = os.path.join(BRIDGE, "decisions")
TEMPLATES = os.path.join(BRIDGE, "templates")
USAGE_LOG = os.path.join(BRIDGE, "usage", "usage.jsonl")
OUT = os.path.join(ROOT, ".bridge-out")
HANDOFF = os.path.join(ROOT, "docs", "AI_HANDOFF.md")
STATUS_DOC = os.path.join(ROOT, "docs", "PROJECT_STATUS.md")

STATUSES = ["backlog", "ready", "in-progress", "review", "changes-requested",
            "needs-owner", "approved", "done", "blocked", "cancelled"]
OPEN_STATUSES = ["ready", "in-progress", "review", "changes-requested",
                 "needs-owner", "approved", "blocked"]
TASK_KEYS = ["id", "title", "status", "priority", "area", "assignee",
             "created", "updated", "branch", "pr", "review_round",
             "max_review_rounds", "approval", "proposed_by"]
REQUIRED_TASK_KEYS = ["id", "title", "status", "priority", "created"]
TASK_ID_RE = re.compile(r"\bT-(\d{4})\b")
REVIEW_MARKER = "<!-- almond-ai-review"

SECRET_PATTERNS = [
    ("OpenAI key", re.compile(r"\bsk-(?:proj-|svcacct-|admin-)?[A-Za-z0-9_-]{32,}")),
    ("Anthropic key", re.compile(r"\bsk-ant-[a-z]{2,4}\d{2}-[A-Za-z0-9_-]{20,}")),
    ("GitHub token", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})")),
    ("AWS key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("Private key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")),
]


class BridgeError(Exception):
    pass


# ----------------------------------------------------------------- basics

def now():
    return dt.datetime.now(dt.timezone.utc).astimezone()


def today():
    return now().strftime("%Y-%m-%d")


def load_config(path=CONFIG_PATH):
    with open(path, "rb") as f:
        return tomllib.load(f)


def run(cmd, check=False, cwd=ROOT, input_text=None, env=None):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                       input=input_text, env=env)
    if check and p.returncode != 0:
        raise BridgeError("%s failed (%d): %s" % (" ".join(cmd), p.returncode,
                                                   (p.stderr or p.stdout).strip()))
    return p


def git(*args, check=False):
    return run(["git", *args], check=check)


def slugify(text, limit=48):
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:limit].rstrip("-") or "task"


def rel(path):
    return os.path.relpath(path, ROOT)


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


# ------------------------------------------------------------ front matter

def parse_front_matter(text):
    """Return (meta, body). Front matter is simple `key: value` lines between
    two `---` lines at the top of the file. Integers become ints."""
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}, text
    meta = {}
    for line in text[4:end].splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, sep, value = line.partition(":")
        if not sep:
            raise BridgeError("bad front-matter line: %r" % line)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        elif re.fullmatch(r"-?\d+", value):
            value = int(value)
        meta[key.strip()] = value
    return meta, text[end + 5:]


def dump_front_matter(meta, body):
    keys = [k for k in TASK_KEYS if k in meta] + \
        [k for k in meta if k not in TASK_KEYS]
    lines = ["---"]
    for k in keys:
        v = meta[k]
        v = "" if v is None else str(v)
        if v and (v[0] in "\"'#" or ": " in v or v != v.strip()):
            v = json.dumps(v, ensure_ascii=False)
        lines.append("%s: %s" % (k, v))
    lines.append("---")
    return "\n".join(lines) + "\n" + body


# ------------------------------------------------------------------ tasks

def task_files():
    if not os.path.isdir(TASKS):
        return []
    return sorted(os.path.join(TASKS, f) for f in os.listdir(TASKS)
                  if re.match(r"T-\d{4}-.*\.md$", f))


def load_tasks():
    tasks = []
    for path in task_files():
        meta, body = parse_front_matter(read(path))
        meta["_path"] = path
        meta["_body"] = body
        tasks.append(meta)
    return tasks


def find_task(task_id):
    task_id = normalise_id(task_id)
    for t in load_tasks():
        if t.get("id") == task_id:
            return t
    raise BridgeError("no task %s in %s" % (task_id, rel(TASKS)))


def normalise_id(task_id):
    m = re.fullmatch(r"(?:T-?)?(\d{1,4})", str(task_id).strip(), re.I)
    if not m:
        raise BridgeError("task ids look like T-0001, got %r" % task_id)
    return "T-%04d" % int(m.group(1))


def save_task(task, log=None):
    meta = {k: v for k, v in task.items() if not k.startswith("_")}
    meta["updated"] = today()
    body = task["_body"]
    if log:
        stamp = now().strftime("%Y-%m-%d %H:%M")
        if "\n## Log\n" not in body:
            body = body.rstrip("\n") + "\n\n## Log\n"
        body = body.rstrip("\n") + "\n- %s — %s\n" % (stamp, log)
        task["_body"] = body
    write(task["_path"], dump_front_matter(meta, body))


def next_number(directory, prefix):
    nums = [0]
    if os.path.isdir(directory):
        for f in os.listdir(directory):
            m = re.match(re.escape(prefix) + r"-(\d{4})", f)
            if m:
                nums.append(int(m.group(1)))
    return max(nums) + 1


def create_task(title, priority="medium", area="general", assignee="claude",
                status="ready", proposed_by="owner", goal="", acceptance=None):
    num = next_number(TASKS, "T")
    task_id = "T-%04d" % num
    cfg = load_config()
    meta = {
        "id": task_id, "title": title, "status": status, "priority": priority,
        "area": area, "assignee": assignee, "created": today(),
        "updated": today(), "branch": "", "pr": "", "review_round": 0,
        "max_review_rounds": cfg["limits"]["max_review_rounds"],
        "approval": "required", "proposed_by": proposed_by,
    }
    body = read(os.path.join(TEMPLATES, "task.md"))
    _, body = parse_front_matter(body)
    if goal:
        body = body.replace("<!-- What should be true when this task is done? -->", goal)
    if acceptance:
        body = body.replace("- [ ] <!-- criterion -->",
                            "\n".join("- [ ] %s" % a for a in acceptance))
    path = os.path.join(TASKS, "%s-%s.md" % (task_id, slugify(title)))
    write(path, dump_front_matter(meta, body))
    return task_id, path


# ------------------------------------------------------------ JSON schema

def load_schema():
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        return json.load(f)


def validate(value, schema, where="review"):
    """Small validator for the subset of JSON Schema used by
    review-schema.json. Returns a list of error strings."""
    errors = []
    types = schema.get("type")
    types = types if isinstance(types, list) else [types] if types else []
    py = {"object": dict, "array": list, "string": str, "boolean": bool,
          "integer": int, "number": (int, float), "null": type(None)}
    if types:
        ok = False
        for t in types:
            if isinstance(value, py[t]) and not (t in ("integer", "number")
                                                 and isinstance(value, bool)):
                ok = True
        if not ok:
            return ["%s: expected %s" % (where, "/".join(types))]
    if "enum" in schema and value not in schema["enum"]:
        errors.append("%s: %r not one of %s" % (where, value, schema["enum"]))
    if isinstance(value, dict):
        props = schema.get("properties", {})
        for k in schema.get("required", []):
            if k not in value:
                errors.append("%s: missing %r" % (where, k))
        if schema.get("additionalProperties") is False:
            for k in value:
                if k not in props:
                    errors.append("%s: unexpected key %r" % (where, k))
        for k, sub in props.items():
            if k in value:
                errors += validate(value[k], sub, "%s.%s" % (where, k))
    if isinstance(value, list) and "items" in schema:
        for i, item in enumerate(value):
            errors += validate(item, schema["items"], "%s[%d]" % (where, i))
    return errors


def extract_json(text):
    m = re.search(r"```(?:json)?\s*\n(\{.*?\})\s*```", text, re.S)
    if m:
        candidate = m.group(1)
    else:
        start, end = text.find("{"), text.rfind("}")
        if start < 0 or end <= start:
            raise BridgeError("no JSON object found in the input")
        candidate = text[start:end + 1]
    try:
        return json.loads(candidate)
    except json.JSONDecodeError as e:
        raise BridgeError("the JSON could not be read: %s" % e)


# ------------------------------------------------------------------ checks

def tracked_files():
    p = git("ls-files", "-z")
    if p.returncode != 0:
        raise BridgeError("not inside a git repository")
    files = [f for f in p.stdout.split("\0") if f]
    # Include new files that are not committed yet, so checks see them.
    q = git("ls-files", "-z", "--others", "--exclude-standard")
    files += [f for f in q.stdout.split("\0") if f]
    return sorted(set(f for f in files if os.path.isfile(os.path.join(ROOT, f))))


def is_shell(path):
    if path.endswith(".sh") or path.endswith(".hook.chroot") or path == "auto/config":
        return True
    try:
        with open(os.path.join(ROOT, path), "rb") as f:
            first = f.readline(100)
    except OSError:
        return False
    return first.startswith(b"#!") and (b"/sh" in first or b"env sh" in first)


def check_shell(files):
    shells = [f for f in files if is_shell(f)]
    tools = [t for t in ("sh", "dash") if shutil.which(t)]
    bad = []
    for f in shells:
        for t in tools:
            p = run([t, "-n", f])
            if p.returncode != 0:
                bad.append("%s (%s): %s" % (f, t, p.stderr.strip()[:200]))
    detail = "%d scripts, %s" % (len(shells), " + ".join(t + " -n" for t in tools))
    if "dash" not in tools:
        detail += " (dash not installed: Debian's /bin/sh not checked)"
    return ("fail", "\n".join(bad)) if bad else ("pass", detail)


def check_python(files):
    bad = []
    pys = [f for f in files if f.endswith(".py")]
    for f in pys:
        try:
            compile(read(os.path.join(ROOT, f)), f, "exec")
        except SyntaxError as e:
            bad.append("%s:%s %s" % (f, e.lineno, e.msg))
    return ("fail", "\n".join(bad)) if bad else ("pass", "%d files compile" % len(pys))


def check_icons(_files):
    script = os.path.join(ROOT, "tools", "check-icons.py")
    if not os.path.exists(script):
        return "skip", "tools/check-icons.py not present"
    p = run([sys.executable, script])
    tail = (p.stdout + p.stderr).strip().splitlines()[-3:]
    return ("pass" if p.returncode == 0 else "fail"), " / ".join(tail) or "ok"


def check_bridge_files(_files):
    problems = []
    schema = load_schema()
    seen = set()
    for t in load_tasks():
        name = os.path.basename(t["_path"])
        for k in REQUIRED_TASK_KEYS:
            if not t.get(k) and t.get(k) != 0:
                problems.append("%s: missing %s" % (name, k))
        if t.get("status") not in STATUSES:
            problems.append("%s: status %r not in %s" % (name, t.get("status"), STATUSES))
        if t.get("id") and not name.startswith(str(t["id"]) + "-"):
            problems.append("%s: id %s does not match the file name" % (name, t["id"]))
        if t.get("id") in seen:
            problems.append("%s: duplicate id %s" % (name, t["id"]))
        seen.add(t.get("id"))
        rr, mx = t.get("review_round", 0), t.get("max_review_rounds", 0)
        if isinstance(rr, int) and isinstance(mx, int) and mx and rr > mx:
            problems.append("%s: review_round %d is above max %d" % (name, rr, mx))
    if os.path.isdir(REPORTS):
        for f in sorted(os.listdir(REPORTS)):
            if f.endswith(".json"):
                try:
                    with open(os.path.join(REPORTS, f), encoding="utf-8") as fh:
                        errs = validate(json.load(fh), schema, f)
                except json.JSONDecodeError as e:
                    errs = ["%s: %s" % (f, e)]
                problems += errs
    try:
        load_config()
    except (OSError, tomllib.TOMLDecodeError) as e:
        problems.append("bridge.toml: %s" % e)
    if problems:
        return "fail", "\n".join(problems)
    return "pass", "%d tasks, config and review files valid" % len(seen)


def scan_secrets(files):
    hits = []
    for f in files:
        path = os.path.join(ROOT, f)
        try:
            if os.path.getsize(path) > 2_000_000:
                continue
            with open(path, "rb") as fh:
                data = fh.read()
        except OSError:
            continue
        if b"\0" in data[:4096]:
            continue
        text = data.decode("utf-8", "replace")
        for label, pat in SECRET_PATTERNS:
            for m in pat.finditer(text):
                line = text.count("\n", 0, m.start()) + 1
                hits.append("%s:%d looks like a %s" % (f, line, label))
    return hits


def check_secrets(files):
    hits = scan_secrets(files)
    return ("fail", "\n".join(hits)) if hits else ("pass", "%d files scanned" % len(files))


def changed_files(base):
    """[(status, path)] for base...HEAD plus uncommitted changes."""
    out = []
    p = git("diff", "--name-status", "%s...HEAD" % base)
    if p.returncode != 0:
        raise BridgeError("cannot diff against %s: %s" % (base, p.stderr.strip()))
    for src in (p.stdout, git("diff", "--name-status", "HEAD").stdout):
        for line in src.splitlines():
            parts = line.split("\t")
            if len(parts) >= 2:
                out.append((parts[0][0], parts[-1]))
    for f in git("ls-files", "--others", "--exclude-standard").stdout.splitlines():
        out.append(("A", f))
    seen, result = set(), []
    for st, f in out:
        if f not in seen:
            seen.add(f)
            result.append((st, f))
    return result


def sensitive_hits(changes, cfg):
    pats = cfg.get("sensitive", {}).get("paths", [])
    hits = []
    for st, f in changes:
        if st == "D":
            hits.append("%s (deleted)" % f)
        elif any(fnmatch.fnmatch(f, p) for p in pats):
            hits.append(f)
    return hits


def check_sensitive(base, cfg):
    def inner(_files):
        if not base:
            return "skip", "no base branch given"
        try:
            hits = sensitive_hits(changed_files(base), cfg)
        except BridgeError as e:
            return "skip", str(e)
        if hits:
            return "warn", "OWNER APPROVAL REQUIRED for: " + ", ".join(hits)
        return "pass", "no sensitive paths changed against %s" % base
    return inner


def check_selftest(_files):
    tests = os.path.join(BRIDGE, "tests")
    if not os.path.isdir(tests):
        return "skip", "no tests"
    p = run([sys.executable, "-m", "unittest", "discover", "-s", tests, "-q"])
    tail = (p.stderr or p.stdout).strip().splitlines()
    summary = " / ".join(l for l in tail if l.startswith(("Ran", "OK", "FAILED")))
    if p.returncode != 0:
        return "fail", "\n".join(tail[-25:])
    return "pass", summary or "ok"


def run_checks(base=None, cfg=None):
    cfg = cfg or load_config()
    files = tracked_files()
    checks = [
        ("Shell syntax", check_shell),
        ("Python syntax", check_python),
        ("Icon theme", check_icons),
        ("Bridge files", check_bridge_files),
        ("Secret scan", check_secrets),
        ("Sensitive paths", check_sensitive(base, cfg)),
        ("Bridge self-test", check_selftest),
    ]
    results = []
    for name, fn in checks:
        try:
            status, detail = fn(files)
        except Exception as e:  # report, never crash the whole check run
            status, detail = "fail", "%s: %s" % (type(e).__name__, e)
        results.append({"name": name, "status": status, "detail": detail})
    return results


def format_checks(results, markdown=False):
    icon = {"pass": "PASS", "fail": "FAIL", "warn": "WARN", "skip": "SKIP"}
    lines = []
    if markdown:
        lines += ["| Check | Result | Detail |", "|---|---|---|"]
        for r in results:
            d = r["detail"].replace("\n", "<br>").replace("|", "\\|")
            lines.append("| %s | %s | %s |" % (r["name"], icon[r["status"]], d))
    else:
        for r in results:
            first, *rest = r["detail"].splitlines() or [""]
            lines.append("%-5s %-17s %s" % (icon[r["status"]], r["name"], first))
            lines += ["      " + x for x in rest]
    return "\n".join(lines)


# -------------------------------------------------------------- reporting

def latest(prefix, kind, ext=".md"):
    if not os.path.isdir(REPORTS):
        return None, 0
    best, n = None, 0
    for f in os.listdir(REPORTS):
        m = re.fullmatch(re.escape(prefix) + r"-" + kind + r"-(\d+)" + re.escape(ext), f)
        if m and int(m.group(1)) > n:
            best, n = os.path.join(REPORTS, f), int(m.group(1))
    return best, n


def commits_since(base):
    p = git("log", "--format=%h %s", "%s..HEAD" % base)
    return p.stdout.strip().splitlines() if p.returncode == 0 else []


def current_branch():
    return git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip()


def build_impl_report(task, n, base, results, changes, cfg, summary=""):
    hits = sensitive_hits(changes, cfg)
    lines = [
        "---",
        "task: %s" % task["id"],
        "kind: implementation",
        "round: %d" % n,
        "date: %s" % now().strftime("%Y-%m-%d %H:%M %Z"),
        "branch: %s" % current_branch(),
        "base: %s" % base,
        "head: %s" % git("rev-parse", "--short", "HEAD").stdout.strip(),
        "---",
        "",
        "# %s — implementation report %d" % (task["id"], n),
        "",
        "**Task:** %s" % task.get("title", ""),
        "",
        "## What changed and why",
        "",
        summary.strip() or "<!-- Implementer: describe what changed and why, in plain words. "
                           "Say what was NOT done. Do not claim anything you did not test. -->",
        "",
        "## Files changed",
        "",
    ]
    if changes:
        names = {"A": "added", "M": "modified", "D": "DELETED", "R": "renamed", "C": "copied"}
        lines += ["- `%s` (%s)" % (f, names.get(st, st)) for st, f in changes]
    else:
        lines.append("- none")
    lines += ["", "## Commits", ""]
    cs = commits_since(base)
    lines += ["- %s" % c for c in cs] if cs else ["- none yet (changes are uncommitted)"]
    lines += ["", "## Checks (run by `bridge finish`)", "", format_checks(results, markdown=True), ""]
    failed = [r["name"] for r in results if r["status"] == "fail"]
    lines += ["Passed: %d · Failed: %d · Warnings: %d · Skipped: %d" % tuple(
        sum(1 for r in results if r["status"] == s) for s in ("pass", "fail", "warn", "skip")), ""]
    if failed:
        lines += ["**Failing checks:** %s" % ", ".join(failed), ""]
    lines += [
        "These checks only cover files, on the machine they ran on. "
        "They do not build, boot or measure an Almond image.",
        "",
        "## Owner approval",
        "",
    ]
    if hits:
        lines += ["**Required.** Sensitive paths changed: %s" % ", ".join("`%s`" % h for h in hits), ""]
    else:
        lines += ["Not triggered by sensitive paths. The owner still approves the merge.", ""]
    lines += [
        "## Known limitations",
        "",
        "<!-- Implementer: what is untested, unknown or deliberately left out. -->",
        "",
        "## Next steps",
        "",
        "<!-- Implementer: what should happen next. -->",
        "",
    ]
    return "\n".join(lines)


def build_packet(task, cfg, base, diff_text=None, extra_context=""):
    """The review request sent to an OpenAI model (pasted or via API)."""
    rv = cfg["review"]
    parts = [
        "# Almond Linux — review request",
        "",
        "You are a code and documentation reviewer for Almond Linux, an independent "
        "Debian-based Linux distribution project (public repository "
        "github.com/AlmondLinux/almond-linux). Another AI (Claude) implemented the "
        "change below. Review it and answer with ONE JSON object that matches the "
        "schema at the end. No text outside the JSON.",
        "",
        "## Review rules",
        "",
        read(os.path.join(BRIDGE, "config", "review-rules.md")).strip(),
        "",
    ]
    if task:
        meta = {k: v for k, v in task.items() if not k.startswith("_")}
        parts += ["## Task %s" % task["id"], "", "```", dump_front_matter(meta, task["_body"]).strip(), "```", ""]
        rpt, n = latest(task["id"], "impl")
        if rpt:
            parts += ["## Implementation report %d" % n, "", read(rpt).strip(), ""]
        prev, pn = latest(task["id"], "review", ".json")
        if prev:
            parts += ["## Previous review (round %d)" % pn, "", "```json", read(prev).strip(), "```", ""]
    if extra_context:
        parts += [extra_context.strip(), ""]
    if diff_text is None:
        excludes = [":(exclude)%s" % p for p in rv.get("exclude_paths", [])]
        p = git("diff", "--stat", "%s...HEAD" % base)
        parts += ["## Diff summary", "", "```", p.stdout.strip() or "(empty)", "```", ""]
        diff_text = git("diff", "%s...HEAD" % base, "--", ".", *excludes).stdout
    limit = int(rv["max_diff_chars"])
    note = ""
    if len(diff_text) > limit:
        note = "\n[... diff truncated: %d of %d characters shown ...]" % (limit, len(diff_text))
        diff_text = diff_text[:limit]
    parts += ["## Diff", "", "```diff", diff_text.rstrip() + note, "```", ""]
    parts += ["## Required answer: JSON matching this schema", "",
              "```json", json.dumps(load_schema(), indent=2), "```", ""]
    return "\n".join(parts)


def review_markdown(task_id, n, review, source, usage=None):
    lines = [
        "---",
        "task: %s" % task_id,
        "kind: review",
        "round: %d" % n,
        "date: %s" % now().strftime("%Y-%m-%d %H:%M %Z"),
        "source: %s" % source,
        "verdict: %s" % review["verdict"],
        "---",
        "",
        "# %s — review %d (%s)" % (task_id, n, review["verdict"]),
        "",
        "Reviewer: %s. This is a review produced through the Almond AI Bridge; it is "
        "not a message from the owner's ChatGPT conversation." % source,
        "",
        "## Summary", "", review["summary"], "",
        "## Findings", "",
    ]
    if review["findings"]:
        lines += ["| Severity | Where | Issue | Suggestion |", "|---|---|---|---|"]
        for f in review["findings"]:
            where = f["file"] + (":%d" % f["line"] if f.get("line") else "")
            lines.append("| %s | `%s` | %s | %s |" % (
                f["severity"], where, f["issue"].replace("|", "\\|"),
                f["suggestion"].replace("|", "\\|")))
    else:
        lines.append("None.")
    lines += ["", "## Status claims", "",
              "Status claims accurate: **%s**" % ("yes" if review["status_claims_ok"] else "NO")]
    lines += ["- %s" % h for h in review["honesty_issues"]]
    lines += ["", "## Tests", "", review["tests_assessment"], ""]
    if review["questions_for_owner"]:
        lines += ["## Questions for the owner", ""] + ["- %s" % q for q in review["questions_for_owner"]] + [""]
    if usage:
        lines += ["## Cost", "", "%s: %d input + %d output tokens, about $%.4f" % (
            usage["model"], usage["input_tokens"], usage["output_tokens"], usage["cost_usd"]), ""]
    return "\n".join(lines)


def record_review(task, review, source, usage=None):
    """Save a review, advance the round, set the next status. Enforces the
    round limit so two AIs cannot loop forever."""
    errs = validate(review, load_schema())
    if errs:
        raise BridgeError("review does not match the schema:\n  " + "\n  ".join(errs))
    rnd = int(task.get("review_round") or 0)
    mx = int(task.get("max_review_rounds") or load_config()["limits"]["max_review_rounds"])
    if rnd >= mx:
        raise BridgeError("%s already had %d of %d review rounds. The owner decides now "
                          "(ai-bridge/bridge approve, or raise max_review_rounds in the task)."
                          % (task["id"], rnd, mx))
    rnd += 1
    _, last = latest(task["id"], "review", ".json")
    n = last + 1
    base = os.path.join(REPORTS, "%s-review-%d" % (task["id"], n))
    write(base + ".json", json.dumps(review, indent=2, ensure_ascii=False) + "\n")
    write(base + ".md", review_markdown(task["id"], n, review, source, usage))
    task["review_round"] = rnd
    if review["verdict"] == "request_changes" and rnd < mx:
        task["status"] = "changes-requested"
    else:
        task["status"] = "needs-owner"
    save_task(task, "review %d recorded (%s, %s) -> %s" % (n, source, review["verdict"], task["status"]))
    return base + ".md"


# ------------------------------------------------------------------ costs

def price(cfg, model):
    p = cfg.get("pricing", {}).get(model)
    if not p:
        raise BridgeError("no price for model %r in [pricing] of bridge.toml; add it "
                          "from https://developers.openai.com/api/docs/pricing" % model)
    return float(p["input"]), float(p["output"])


def estimate_cost(cfg, prompt_chars):
    oa = cfg["openai"]
    pin, pout = price(cfg, oa["model"])
    tokens_in = prompt_chars // 4 + 1
    return tokens_in, tokens_in * pin / 1e6 + int(oa["max_output_tokens"]) * pout / 1e6


def month_spend(log_path=None, month=None):
    log_path = log_path or USAGE_LOG
    month = month or now().strftime("%Y-%m")
    total = 0.0
    if os.path.exists(log_path):
        with open(log_path, encoding="utf-8") as f:
            for line in f:
                try:
                    e = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if str(e.get("time", "")).startswith(month):
                    total += float(e.get("cost_usd", 0))
    return total


def log_usage(entry, log_path=None):
    log_path = log_path or USAGE_LOG
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def guard_spend(cfg, prompt_chars, spent):
    """Raise unless this call fits under both limits. Returns (tokens, max_cost)."""
    oa = cfg["openai"]
    if not oa.get("enabled"):
        raise BridgeError("paid OpenAI reviews are switched off (openai.enabled = false in "
                          "ai-bridge/config/bridge.toml). Only the owner turns this on.")
    if prompt_chars > int(oa["max_input_chars"]):
        raise BridgeError("review packet is %d characters, above max_input_chars %d. "
                          "Split the change or lower review.max_diff_chars."
                          % (prompt_chars, oa["max_input_chars"]))
    tokens, worst = estimate_cost(cfg, prompt_chars)
    if worst > float(oa["per_call_limit_usd"]):
        raise BridgeError("worst-case cost $%.4f is above per_call_limit_usd $%.2f"
                          % (worst, oa["per_call_limit_usd"]))
    if spent + worst > float(oa["monthly_limit_usd"]):
        raise BridgeError("monthly limit reached: spent $%.4f, this call could add $%.4f, "
                          "limit $%.2f" % (spent, worst, oa["monthly_limit_usd"]))
    return tokens, worst


def call_openai(cfg, prompt, api_key, opener=urllib.request.urlopen):
    """One Responses API call with a strict JSON-schema answer. Returns
    (review_dict, usage_dict)."""
    oa = cfg["openai"]
    payload = {
        "model": oa["model"],
        "instructions": "You review changes to the Almond Linux repository. Be precise, "
                        "cite files, never invent facts. Answer only with the JSON object.",
        "input": prompt,
        "max_output_tokens": int(oa["max_output_tokens"]),
        "store": False,
        "text": {"format": {"type": "json_schema", "name": "almond_review",
                            "schema": load_schema(), "strict": True}},
    }
    if oa.get("reasoning_effort"):
        payload["reasoning"] = {"effort": oa["reasoning_effort"]}
    req = urllib.request.Request(
        oa["api_url"], data=json.dumps(payload).encode(), method="POST",
        headers={"Authorization": "Bearer " + api_key, "Content-Type": "application/json"})
    try:
        with opener(req, timeout=int(oa.get("timeout_seconds", 180))) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        e.close()
        try:
            msg = json.loads(body)["error"]["message"]
        except (ValueError, KeyError, TypeError):
            msg = body[:500]
        raise BridgeError("OpenAI API error %d: %s" % (e.code, msg))
    except urllib.error.URLError as e:
        raise BridgeError("could not reach the OpenAI API: %s" % e.reason)
    text = data.get("output_text") or ""
    if not text:
        for item in data.get("output", []):
            for c in item.get("content", []) or []:
                if c.get("type") == "output_text":
                    text += c.get("text", "")
    u = data.get("usage", {}) or {}
    pin, pout = price(cfg, oa["model"])
    usage = {
        "model": data.get("model", oa["model"]),
        "input_tokens": int(u.get("input_tokens", 0)),
        "output_tokens": int(u.get("output_tokens", 0)),
    }
    usage["cost_usd"] = round(usage["input_tokens"] * pin / 1e6 + usage["output_tokens"] * pout / 1e6, 6)
    if data.get("status") == "incomplete":
        reason = (data.get("incomplete_details") or {}).get("reason", "unknown")
        raise BridgeError("the model stopped early (%s); %d output tokens were billed. "
                          "Raise openai.max_output_tokens or lower reasoning_effort."
                          % (reason, usage["output_tokens"]), usage)
    if not text:
        raise BridgeError("the API answered without any text", usage)
    return json.loads(text), usage


# --------------------------------------------------------------- clipboard

def clipboard_read():
    for cmd in (["pbpaste"], ["wl-paste", "-n"], ["xclip", "-o", "-selection", "clipboard"],
                ["powershell.exe", "-NoProfile", "-Command", "Get-Clipboard"]):
        if shutil.which(cmd[0]):
            p = run(cmd)
            if p.returncode == 0:
                return p.stdout
    raise BridgeError("no clipboard tool found; use --file instead")


def clipboard_write(text):
    for cmd in (["pbcopy"], ["wl-copy"], ["xclip", "-selection", "clipboard"], ["clip.exe"]):
        if shutil.which(cmd[0]):
            return run(cmd, input_text=text).returncode == 0
    return False


# ---------------------------------------------------- generated doc blocks

def replace_block(text, name, content):
    start, end = "<!-- bridge:%s:start -->" % name, "<!-- bridge:%s:end -->" % name
    i, j = text.find(start), text.find(end)
    if i < 0 or j < i:
        raise BridgeError("markers for block %r not found" % name)
    return text[:i + len(start)] + "\n" + content.rstrip() + "\n" + text[j:]


def task_table(tasks):
    if not tasks:
        return "No tasks."
    lines = ["| Task | Title | Status | Assignee | Review rounds | PR |", "|---|---|---|---|---|---|"]
    order = {s: i for i, s in enumerate(STATUSES)}
    for t in sorted(tasks, key=lambda t: (order.get(t.get("status"), 99), t.get("id", ""))):
        link = "../ai-bridge/tasks/" + os.path.basename(t["_path"])
        pr = t.get("pr") or ""
        lines.append("| [%s](%s) | %s | %s | %s | %s/%s | %s |" % (
            t["id"], link, t.get("title", ""), t.get("status", ""), t.get("assignee", ""),
            t.get("review_round", 0), t.get("max_review_rounds", ""), ("#%s" % pr) if pr else ""))
    return "\n".join(lines)


def recent_reports(limit=6):
    if not os.path.isdir(REPORTS):
        return []
    items = []
    for f in os.listdir(REPORTS):
        if f.endswith(".md") and f != "README.md":
            meta, _ = parse_front_matter(read(os.path.join(REPORTS, f)))
            items.append((str(meta.get("date", "")), f, meta))
    return sorted(items, reverse=True)[:limit]


def handoff_block(cfg):
    tasks = load_tasks()
    lines = ["_Generated %s by `ai-bridge/bridge handoff`. Do not edit by hand._" % now().strftime("%Y-%m-%d %H:%M %Z"), ""]
    lines += ["**Branch:** `%s`" % current_branch(), ""]
    waiting = [t for t in tasks if t.get("status") == "needs-owner"]
    lines += ["### Waiting for the owner", ""]
    lines += (["- %s %s" % (t["id"], t.get("title", "")) for t in waiting] or ["- nothing"]) + [""]
    lines += ["### Open tasks", "", task_table([t for t in tasks if t.get("status") in OPEN_STATUSES]), ""]
    lines += ["### Latest reports and reviews", ""]
    reps = recent_reports()
    lines += (["- [%s](../ai-bridge/reports/%s) — %s %s" % (
        f, f, m.get("kind", ""), ("(%s)" % m["verdict"]) if m.get("verdict") else "") for _, f, m in reps]
        or ["- none yet"]) + [""]
    lines += ["### Last commits on this branch", "", "```"]
    lines += git("log", "-8", "--format=%h %ad %s", "--date=short").stdout.strip().splitlines()
    lines += ["```", ""]
    oa = cfg["openai"]
    lines += ["### Paid API reviews", "",
              "OpenAI reviews: **%s** · model `%s` · spent this month (local log) $%.4f of $%.2f" % (
                  "on" if oa.get("enabled") else "off", oa["model"], month_spend(), float(oa["monthly_limit_usd"]))]
    return "\n".join(lines)


def refresh_docs(cfg):
    changed = []
    for path, name, content in ((HANDOFF, "handoff", handoff_block(cfg)),
                                (STATUS_DOC, "tasks", task_table(load_tasks()))):
        old = read(path)
        new = replace_block(old, name, content)
        if new != old:
            write(path, new)
            changed.append(rel(path))
    return changed


# --------------------------------------------------------------- dashboard

def parse_md_table(text, heading):
    i = text.find(heading)
    if i < 0:
        return []
    rows = []
    for line in text[i:].splitlines()[1:]:
        if line.startswith("## "):
            break
        if line.startswith("|") and not re.match(r"\|\s*-", line):
            rows.append([c.strip() for c in line.strip().strip("|").split("|")])
    return rows[1:] if rows else []


def md_inline(s):
    s = html.escape(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"`(.+?)`", r"<code>\1</code>", s)
    s = re.sub(r"\[(.+?)\]\((.+?)\)", r"\1", s)
    return s


def build_dashboard(cfg):
    tasks = load_tasks()
    comps = parse_md_table(read(STATUS_DOC), "## Components")
    columns = [("Ready", ["ready", "backlog"]), ("In progress", ["in-progress", "changes-requested"]),
               ("In review", ["review"]), ("Owner decides", ["needs-owner", "approved", "blocked"]),
               ("Done", ["done", "cancelled"])]
    rung_class = {"PLANNED": "planned", "DESIGNED": "designed", "IMPLEMENTED": "impl",
                  "TESTED": "tested", "APPROVED": "approved"}
    col_html = []
    for title, sts in columns:
        cards = []
        for t in tasks:
            if t.get("status") in sts:
                cards.append('<div class="card"><div class="id">%s · %s</div><div class="t">%s</div>'
                             '<div class="meta">%s · review %s/%s%s</div></div>' % (
                                 html.escape(t["id"]), html.escape(str(t.get("status"))),
                                 html.escape(str(t.get("title", ""))), html.escape(str(t.get("assignee", ""))),
                                 t.get("review_round", 0), t.get("max_review_rounds", ""),
                                 (" · PR #%s" % html.escape(str(t["pr"]))) if t.get("pr") else ""))
        col_html.append('<section class="col"><h3>%s <span>%d</span></h3>%s</section>' % (
            title, len(cards), "".join(cards) or '<p class="empty">Nothing here</p>'))
    comp_rows = []
    for row in comps:
        if len(row) < 3:
            continue
        rung = re.sub(r"[^A-Z].*$", "", re.sub(r"^\W+", "", row[2]))
        cls = rung_class.get(rung, "other")
        comp_rows.append('<tr><td>%s</td><td><span class="rung %s">%s</span></td><td>%s</td></tr>' % (
            md_inline(row[0]), cls, md_inline(row[2]), md_inline(row[3] if len(row) > 3 else "")))
    reps = "".join('<li><code>%s</code> %s</li>' % (html.escape(f), html.escape(
        "%s %s" % (m.get("kind", ""), m.get("verdict", "")))) for _, f, m in recent_reports(8)) \
        or "<li>No reports yet</li>"
    oa = cfg["openai"]
    spend = month_spend()
    pct = min(100, int(100 * spend / max(float(oa["monthly_limit_usd"]), 0.01)))
    return DASHBOARD_HTML.format(
        generated=html.escape(now().strftime("%Y-%m-%d %H:%M")), branch=html.escape(current_branch()),
        columns="".join(col_html), components="".join(comp_rows), reports=reps,
        api="on" if oa.get("enabled") else "off", model=html.escape(oa["model"]),
        spend="%.4f" % spend, limit="%.2f" % float(oa["monthly_limit_usd"]), pct=pct,
        rounds=cfg["limits"]["max_review_rounds"])


DASHBOARD_HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Almond AI Bridge</title>
<style>
:root{{--bg:#f5f2eb;--panel:#fbf9f4;--ink:#2b2118;--muted:#6b5a4a;--line:#e3d9c8;--brown:#8b5a2b;
--planned:#e9e1d3;--designed:#f1e0c2;--impl:#f5deb3;--tested:#d6e8d0;--approved:#b9dbb0}}
@media (prefers-color-scheme:dark){{:root{{--bg:#202125;--panel:#2b2118;--ink:#f5deb3;--muted:#c9b48f;
--line:#3d3328;--brown:#d2a679;--planned:#3a3229;--designed:#4a3b28;--impl:#5a4325;--tested:#2f4a2c;--approved:#3c6234}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);
font:15px/1.45 "Atkinson Hyperlegible",system-ui,sans-serif}}
main{{max-width:1180px;margin:0 auto;padding:24px 16px 48px}}
header{{display:flex;flex-wrap:wrap;justify-content:space-between;gap:8px;align-items:baseline;
border-bottom:2px solid var(--brown);padding-bottom:10px;margin-bottom:20px}}
h1{{margin:0;font-size:24px}}h2{{font-size:17px;margin:28px 0 10px}}.sub{{color:var(--muted);font-size:13px}}
.board{{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:10px}}
@media (max-width:900px){{.board{{grid-template-columns:1fr 1fr}}}}@media (max-width:560px){{.board{{grid-template-columns:1fr}}}}
.col{{background:var(--panel);border:1px solid var(--line);border-radius:6px;padding:10px;min-height:90px}}
.col h3{{margin:0 0 8px;font-size:13px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted)}}
.col h3 span{{float:right}}.card{{border:1px solid var(--line);border-left:3px solid var(--brown);
border-radius:4px;padding:8px;margin-bottom:8px;background:var(--bg)}}
.id{{font-size:12px;color:var(--muted)}}.t{{font-weight:bold}}.meta{{font-size:12px;color:var(--muted)}}
.empty{{color:var(--muted);font-size:13px;margin:0}}
table{{width:100%;border-collapse:collapse;background:var(--panel);border:1px solid var(--line)}}
td,th{{text-align:left;padding:7px 9px;border-bottom:1px solid var(--line);vertical-align:top;font-size:14px}}
.tablewrap{{overflow-x:auto}}code{{font-family:"DejaVu Sans Mono",ui-monospace,monospace;font-size:12.5px}}
.rung{{display:inline-block;padding:1px 7px;border-radius:3px;background:var(--planned);font-size:12.5px}}
.rung.designed{{background:var(--designed)}}.rung.impl{{background:var(--impl)}}
.rung.tested{{background:var(--tested)}}.rung.approved{{background:var(--approved)}}
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}@media (max-width:760px){{.grid2{{grid-template-columns:1fr}}}}
.box{{background:var(--panel);border:1px solid var(--line);border-radius:6px;padding:12px 14px}}
.bar{{height:8px;background:var(--line);border-radius:4px;overflow:hidden;margin-top:6px}}
.bar i{{display:block;height:100%;background:var(--brown);width:{pct}%}}ul{{margin:0;padding-left:18px}}
</style></head><body><main>
<header><h1>Almond AI Bridge</h1><div class="sub">Generated {generated} · branch <code>{branch}</code> ·
regenerate with <code>ai-bridge/bridge dashboard</code></div></header>
<h2>Tasks</h2><div class="board">{columns}</div>
<div class="grid2">
<div><h2>Latest reports and reviews</h2><div class="box"><ul>{reports}</ul></div></div>
<div><h2>Cost guard</h2><div class="box">Paid OpenAI reviews: <b>{api}</b> · model <code>{model}</code><br>
Spent this month (local log): <b>${spend}</b> of ${limit}<div class="bar"><i></i></div>
<div class="sub" style="margin-top:6px">At most {rounds} automated review rounds per task, then the owner decides.
GitHub Actions spending is shown in each PR's review comment.</div></div></div>
</div>
<h2>Component status (from docs/PROJECT_STATUS.md)</h2>
<div class="tablewrap"><table><tr><th>Component</th><th>Rung</th><th>Notes</th></tr>{components}</table></div>
</main></body></html>
"""


# ------------------------------------------------------------- GitHub (CI)

def gh_json(*args):
    p = run(["gh", *args], check=True)
    return json.loads(p.stdout or "null")


def ci_month_spend(repo, month_start):
    """Sum the cost written into this repository's AI review comments this month."""
    total, count = 0.0, 0
    page = 1
    while True:
        comments = gh_json("api", "repos/%s/issues/comments?since=%s&per_page=100&page=%d"
                           % (repo, month_start, page))
        if not comments:
            break
        for c in comments:
            body = c.get("body") or ""
            if REVIEW_MARKER in body and c.get("created_at", "") >= month_start:
                m = re.search(r"cost_usd=([0-9.]+)", body)
                total += float(m.group(1)) if m else 0.0
                count += 1
        if len(comments) < 100:
            break
        page += 1
    return total, count


def cmd_ci_review(args, cfg):
    repo = os.environ.get("GITHUB_REPOSITORY") or args.repo
    key = os.environ.get("OPENAI_API_KEY", "")
    pr = str(args.pr)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")

    def say(msg):
        print(msg)
        if summary:
            with open(summary, "a", encoding="utf-8") as f:
                f.write(msg + "\n\n")

    if not key:
        say("No OPENAI_API_KEY secret is set, so no review was made. Setup: ai-bridge/docs/SETUP.md, step B.")
        return 0
    if not cfg["openai"].get("enabled"):
        say("openai.enabled is false in ai-bridge/config/bridge.toml on the default branch, so no "
            "review was made. Only the owner switches it on.")
        return 0
    info = gh_json("pr", "view", pr, "--repo", repo, "--json", "title,body,headRefName,files,number")
    comments = gh_json("api", "repos/%s/issues/%s/comments?per_page=100" % (repo, pr))
    done_here = sum(1 for c in comments if REVIEW_MARKER in (c.get("body") or ""))
    mx = int(cfg["limits"]["max_review_rounds"])
    if done_here >= mx:
        say("PR #%s already has %d AI reviews (limit %d). The owner decides now; no API call made."
            % (pr, done_here, mx))
        return 0
    month_start = now().strftime("%Y-%m-01T00:00:00Z")
    spent, n_month = ci_month_spend(repo, month_start)
    diff = run(["gh", "pr", "diff", pr, "--repo", repo], check=True).stdout
    excl = cfg["review"].get("exclude_paths", [])
    diff = filter_diff(diff, excl)
    files = "\n".join("- `%s` (+%s −%s)" % (f["path"], f.get("additions", 0), f.get("deletions", 0))
                      for f in info.get("files", []))
    hits = sensitive_hits([("M", f["path"]) for f in info.get("files", [])], cfg)
    ctx = "## Pull request #%s: %s\n\nBranch: `%s`\n\n%s\n\n### Files\n\n%s\n\n### Sensitive paths\n\n%s" % (
        pr, info["title"], info["headRefName"], (info.get("body") or "").strip()[:6000], files,
        ", ".join(hits) if hits else "none")
    prompt = build_packet(None, cfg, None, diff_text=diff, extra_context=ctx)
    try:
        tokens, worst = guard_spend(cfg, len(prompt), spent)
    except BridgeError as e:
        say("No review made: %s" % e)
        return 0
    say("Calling %s: about %d input tokens, worst case $%.4f. Spent this month: $%.4f in %d reviews."
        % (cfg["openai"]["model"], tokens, worst, spent, n_month))
    try:
        review, usage = call_openai(cfg, prompt, key)
    except BridgeError as e:
        usage = e.args[1] if len(e.args) > 1 else None
        if usage:
            note = "%s <!-- almond-ai-review failed cost_usd=%.6f -->" % (e.args[0], usage["cost_usd"])
            run(["gh", "pr", "comment", pr, "--repo", repo, "--body", "AI review failed: " + note])
        say("Review failed: %s" % e.args[0])
        return 1
    errs = validate(review, load_schema())
    if errs:
        say("The model's answer did not match the schema: %s" % "; ".join(errs))
        return 1
    task_ids = sorted(set(TASK_ID_RE.findall(info["title"] + " " + info["headRefName"])))
    label = ("T-" + task_ids[0]) if task_ids else "PR #%s" % pr
    body = review_markdown(label, done_here + 1, review, "OpenAI API (%s) via GitHub Actions" % usage["model"], usage)
    body = re.sub(r"^---\n.*?\n---\n\n", "", body, flags=re.S)
    body += "\n\nRound %d of %d. To keep a copy in the repository: `ai-bridge/bridge in --pr %s`.\n" % (
        done_here + 1, mx, pr)
    body += "\n%s round=%d cost_usd=%.6f model=%s -->\n" % (REVIEW_MARKER, done_here + 1, usage["cost_usd"], usage["model"])
    body += "\n```json\n%s\n```\n" % json.dumps(review, indent=2, ensure_ascii=False)
    run(["gh", "pr", "comment", pr, "--repo", repo, "--body-file", "-"], check=True, input_text=body)
    say("Review posted: verdict %s, %d findings, cost $%.4f." % (review["verdict"], len(review["findings"]), usage["cost_usd"]))
    return 0


def filter_diff(diff, exclude_paths):
    if not exclude_paths:
        return diff
    out, keep = [], True
    for line in diff.splitlines(keepends=True):
        if line.startswith("diff --git "):
            m = re.match(r"diff --git a/(\S+) b/", line)
            path = m.group(1) if m else ""
            keep = not any(fnmatch.fnmatch(path, p) for p in exclude_paths)
            if not keep:
                out.append("[diff of %s left out: excluded path]\n" % path)
        if keep:
            out.append(line)
    return "".join(out)


# ---------------------------------------------------------------- commands

def cmd_status(args, cfg):
    tasks = load_tasks()
    print("Almond AI Bridge — %s — branch %s" % (now().strftime("%Y-%m-%d %H:%M"), current_branch()))
    print()
    if not tasks:
        print("No tasks. Create one: ai-bridge/bridge new \"Title\"")
    order = {s: i for i, s in enumerate(STATUSES)}
    for t in sorted(tasks, key=lambda t: (order.get(t.get("status"), 99), t["id"])):
        if t.get("status") in ("done", "cancelled") and not args.all:
            continue
        print("  %-7s %-18s %-9s %s" % (t["id"], t.get("status"), t.get("assignee", ""), t.get("title", "")))
    waiting = [t["id"] for t in tasks if t.get("status") == "needs-owner"]
    print()
    if waiting:
        print("Waiting for the owner: %s  (review, then: ai-bridge/bridge approve <id>)" % ", ".join(waiting))
    oa = cfg["openai"]
    print("OpenAI API reviews: %s (model %s). Spent this month (local log): $%.4f of $%.2f." % (
        "ON" if oa.get("enabled") else "off", oa["model"], month_spend(), float(oa["monthly_limit_usd"])))
    return 0


def cmd_new(args, cfg):
    task_id, path = create_task(args.title, args.priority, args.area, args.assignee,
                                "backlog" if args.backlog else "ready")
    print("Created %s: %s" % (task_id, rel(path)))
    print("Fill in Goal, Specs to read, Acceptance criteria and Tests, then commit it.")
    return 0


def cmd_start(args, cfg):
    t = find_task(args.task)
    if t.get("status") not in ("ready", "changes-requested", "in-progress"):
        raise BridgeError("%s is %s; only ready or changes-requested tasks can be started"
                          % (t["id"], t.get("status")))
    if not args.no_branch:
        branch = t.get("branch") or "task/%s-%s" % (t["id"], slugify(t.get("title", ""), 32))
        if current_branch() != branch:
            exists = git("rev-parse", "--verify", "--quiet", branch).returncode == 0
            p = git("checkout", branch) if exists else git("checkout", "-b", branch)
            if p.returncode != 0:
                raise BridgeError("could not switch to %s: %s" % (branch, p.stderr.strip()))
        t["branch"] = branch
    t["status"] = "in-progress"
    save_task(t, "started on branch %s" % (t.get("branch") or current_branch()))
    print("%s in progress on %s. Specs to read are listed in %s." % (t["id"], current_branch(), rel(t["_path"])))
    return 0


def cmd_check(args, cfg):
    base = args.base
    if base is None and git("rev-parse", "--verify", "--quiet", cfg["project"]["default_base"]).returncode == 0:
        base = cfg["project"]["default_base"]
    results = run_checks(base, cfg)
    print(format_checks(results))
    os.makedirs(OUT, exist_ok=True)
    write(os.path.join(OUT, "check.json"), json.dumps(results, indent=2))
    if args.ci:
        for r in results:
            if r["status"] == "fail":
                print("::error title=%s::%s" % (r["name"], r["detail"].replace("\n", "%0A")))
            elif r["status"] == "warn":
                print("::warning title=%s::%s" % (r["name"], r["detail"].replace("\n", "%0A")))
        summary = os.environ.get("GITHUB_STEP_SUMMARY")
        if summary:
            with open(summary, "a", encoding="utf-8") as f:
                f.write("## Almond checks\n\n" + format_checks(results, markdown=True) + "\n\n"
                        "Free checks only: no API calls, no secrets. They do not build or boot an image.\n")
    return 1 if any(r["status"] == "fail" for r in results) else 0


def cmd_finish(args, cfg):
    t = find_task(args.task)
    base = args.base or cfg["project"]["default_base"]
    results = run_checks(base, cfg)
    changes = changed_files(base)
    _, n = latest(t["id"], "impl")
    summary = read(args.summary) if args.summary else ""
    path = os.path.join(REPORTS, "%s-impl-%d.md" % (t["id"], n + 1))
    write(path, build_impl_report(t, n + 1, base, results, changes, cfg, summary))
    failed = [r["name"] for r in results if r["status"] == "fail"]
    t["status"] = "review"
    if args.pr:
        t["pr"] = args.pr
    save_task(t, "implementation report %d written (%s)" % (
        n + 1, "checks failed: " + ", ".join(failed) if failed else "all checks passed"))
    refresh_docs(cfg)
    print(format_checks(results))
    print()
    print("Report: %s" % rel(path))
    print("Next: fill in its 'What changed and why', 'Known limitations' and 'Next steps', "
          "commit, push, open a PR, then ask for a review (ai-bridge/README.md, 'Which review lane should I use?').")
    return 1 if failed else 0


def cmd_out(args, cfg):
    t = find_task(args.task)
    base = args.base or cfg["project"]["default_base"]
    packet = build_packet(t, cfg, base)
    path = os.path.join(OUT, "review-%s.md" % t["id"])
    write(path, packet)
    tokens, worst = estimate_cost(cfg, len(packet))
    print("Review packet: %s (%d characters, about %d tokens)" % (rel(path), len(packet), tokens))
    if not args.no_copy and clipboard_write(packet):
        print("Copied to the clipboard. Paste it into ChatGPT, copy ChatGPT's whole answer, "
              "then run: ai-bridge/bridge in --task %s" % t["id"])
    return 0


def parse_block(text, name):
    m = re.search(r"```%s\s*\n(.*?)```" % re.escape(name), text, re.S)
    if not m:
        return None
    fields, current = {}, None
    for line in m.group(1).splitlines():
        km = re.match(r"([a-z_]+):\s*(.*)$", line)
        if km:
            current = km.group(1)
            fields[current] = km.group(2).strip()
        elif current and line.strip():
            fields[current] = (fields[current] + "\n" + line.rstrip()).strip()
    return fields


def cmd_in(args, cfg):
    if args.pr:
        repo = args.repo or gh_json("repo", "view", "--json", "nameWithOwner")["nameWithOwner"]
        comments = gh_json("api", "repos/%s/issues/%s/comments?per_page=100" % (repo, args.pr))
        bodies = [c["body"] for c in comments
                  if REVIEW_MARKER in (c.get("body") or "") and "```json" in c["body"]]
        if not bodies:
            raise BridgeError("PR #%s has no AI review comment" % args.pr)
        text, source = bodies[-1], "OpenAI API via GitHub Actions (PR #%s)" % args.pr
    elif args.file:
        text, source = read(args.file), "pasted from ChatGPT (file)"
    else:
        text, source = clipboard_read(), "pasted from ChatGPT"
    if args.source:
        source = args.source
    dec = parse_block(text, "almond-decision")
    if dec:
        num = next_number(DECISIONS, "D")
        path = os.path.join(DECISIONS, "D-%04d-%s.md" % (num, slugify(dec.get("title", "decision"))))
        body = read(os.path.join(TEMPLATES, "decision.md"))
        body = body.replace("{id}", "D-%04d" % num).replace("{date}", today())
        for k in ("title", "context", "decision", "reason", "alternatives", "consequences"):
            body = body.replace("{%s}" % k, dec.get(k, "") or "_not given_")
        body = body.replace("{source}", source)
        write(path, body)
        print("Decision proposal saved: %s (status: proposed — only the owner accepts it)" % rel(path))
        return 0
    tb = parse_block(text, "almond-task")
    if tb:
        acc = [a.lstrip("-* ").strip() for a in tb.get("acceptance", "").splitlines() if a.strip()]
        task_id, path = create_task(tb.get("title", "Untitled task"), tb.get("priority", "medium"),
                                    tb.get("area", "general"), tb.get("assignee", "claude"),
                                    "backlog", "openai", tb.get("goal", ""), acc)
        print("Task proposal saved: %s %s (status: backlog — the owner moves it to ready)" % (task_id, rel(path)))
        return 0
    review = extract_json(text)
    task_id = args.task
    if not task_id:
        ids = TASK_ID_RE.findall(text)
        if ids:
            task_id = "T-" + ids[0]
    if not task_id:
        raise BridgeError("which task is this review for? pass --task T-0001")
    t = find_task(task_id)
    path = record_review(t, review, source)
    refresh_docs(cfg)
    t = find_task(task_id)
    print("Review saved: %s" % rel(path))
    print("Verdict: %s · %d findings · task is now %s (round %s of %s)" % (
        review["verdict"], len(review["findings"]), t["status"], t["review_round"], t["max_review_rounds"]))
    return 0


def cmd_review(args, cfg):
    t = find_task(args.task)
    base = args.base or cfg["project"]["default_base"]
    packet = build_packet(t, cfg, base)
    spent = month_spend()
    tokens, worst = estimate_cost(cfg, len(packet))
    oa = cfg["openai"]
    print("Model %s · about %d input tokens · max %d output tokens" % (oa["model"], tokens, oa["max_output_tokens"]))
    print("Worst-case cost of this call: $%.4f · spent this month: $%.4f of $%.2f" % (
        worst, spent, float(oa["monthly_limit_usd"])))
    if not (args.live and args.yes_spend):
        write(os.path.join(OUT, "review-%s.md" % t["id"]), packet)
        print("DRY RUN: no API call was made. The packet is in .bridge-out/. "
              "A paid call needs openai.enabled = true AND --live --yes-spend.")
        return 0
    guard_spend(cfg, len(packet), spent)
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise BridgeError("OPENAI_API_KEY is not set in this terminal (see ai-bridge/docs/SETUP.md)")
    try:
        review, usage = call_openai(cfg, packet, key)
    except BridgeError as e:
        if len(e.args) > 1 and e.args[1]:
            u = e.args[1]
            log_usage({"time": now().isoformat(), "task": t["id"], "model": u["model"], "input_tokens":
                       u["input_tokens"], "output_tokens": u["output_tokens"], "cost_usd": u["cost_usd"], "ok": False})
        raise BridgeError(e.args[0])
    log_usage({"time": now().isoformat(), "task": t["id"], "model": usage["model"],
               "input_tokens": usage["input_tokens"], "output_tokens": usage["output_tokens"],
               "cost_usd": usage["cost_usd"], "ok": True})
    path = record_review(t, review, "OpenAI API (%s)" % usage["model"], usage)
    refresh_docs(cfg)
    print("Review saved: %s · verdict %s · cost $%.4f" % (rel(path), review["verdict"], usage["cost_usd"]))
    return 0


def cmd_handoff(args, cfg):
    changed = refresh_docs(cfg)
    print("Updated: %s" % (", ".join(changed) if changed else "nothing changed"))
    return 0


def cmd_dashboard(args, cfg):
    path = os.path.join(OUT, "dashboard.html")
    write(path, build_dashboard(cfg))
    print("Dashboard: %s" % path)
    if args.open:
        opener = "open" if sys.platform == "darwin" else "xdg-open"
        if shutil.which(opener):
            run([opener, path])
    return 0


def cmd_ready(args, cfg):
    t = find_task(args.task)
    if t.get("status") != "backlog":
        raise BridgeError("%s is %s, not backlog" % (t["id"], t.get("status")))
    t["status"] = "ready"
    save_task(t, "moved to ready (owner)")
    print("%s is ready." % t["id"])
    return 0


def cmd_approve(args, cfg):
    t = find_task(args.task)
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        raise BridgeError("approve only runs in the owner's own terminal (no AI agent can approve)")
    print("%s — %s (status %s, review rounds %s/%s)" % (
        t["id"], t.get("title"), t.get("status"), t.get("review_round"), t.get("max_review_rounds")))
    rpt, _ = latest(t["id"], "review")
    if rpt:
        print("Latest review: %s" % rel(rpt))
    answer = input("Type the task id to approve it: ").strip()
    if normalise_id(answer or "0") != t["id"]:
        print("Not approved.")
        return 1
    t["status"] = "approved"
    save_task(t, "APPROVED by the owner")
    print("%s approved. Commit and push this change with the PR." % t["id"])
    if t.get("pr") and shutil.which("gh"):
        print(run(["gh", "pr", "checks", str(t["pr"])]).stdout)
        if input("Merge PR #%s now (squash)? [y/N] " % t["pr"]).strip().lower() == "y":
            p = run(["gh", "pr", "merge", str(t["pr"]), "--squash"])
            print(p.stdout or p.stderr)
            if p.returncode == 0:
                t = find_task(t["id"])
                t["status"] = "done"
                save_task(t, "merged (PR #%s)" % t["pr"])
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="bridge", description="Almond AI Bridge")
    sub = ap.add_subparsers(dest="cmd")
    s = sub.add_parser("status", help="show the task board")
    s.add_argument("--all", action="store_true", help="include done and cancelled tasks")
    s = sub.add_parser("new", help="create a task")
    s.add_argument("title")
    s.add_argument("--priority", default="medium", choices=["low", "medium", "high"])
    s.add_argument("--area", default="general")
    s.add_argument("--assignee", default="claude")
    s.add_argument("--backlog", action="store_true", help="create as backlog, not ready")
    s = sub.add_parser("start", help="start a ready task (makes a branch)")
    s.add_argument("task")
    s.add_argument("--no-branch", action="store_true")
    s = sub.add_parser("check", help="run the free local checks")
    s.add_argument("--base", default=None)
    s.add_argument("--ci", action="store_true")
    s = sub.add_parser("finish", help="run checks and write the implementation report")
    s.add_argument("task")
    s.add_argument("--base")
    s.add_argument("--pr")
    s.add_argument("--summary", help="file with the 'what changed and why' text")
    s = sub.add_parser("out", help="build a review packet and copy it for ChatGPT")
    s.add_argument("task")
    s.add_argument("--base")
    s.add_argument("--no-copy", action="store_true")
    s = sub.add_parser("in", help="record ChatGPT's answer (review, decision or task)")
    s.add_argument("--task")
    s.add_argument("--file")
    s.add_argument("--pr", help="copy the AI review comment from this PR")
    s.add_argument("--repo")
    s.add_argument("--source")
    s = sub.add_parser("review", help="OpenAI API review (dry run unless --live --yes-spend)")
    s.add_argument("task")
    s.add_argument("--base")
    s.add_argument("--live", action="store_true")
    s.add_argument("--yes-spend", action="store_true")
    s = sub.add_parser("ci-review", help="used by .github/workflows/ai-review.yml")
    s.add_argument("--pr", required=True)
    s.add_argument("--repo")
    sub.add_parser("handoff", help="refresh generated sections of the docs")
    s = sub.add_parser("dashboard", help="write .bridge-out/dashboard.html")
    s.add_argument("--open", action="store_true")
    s = sub.add_parser("ready", help="move a backlog task to ready (owner)")
    s.add_argument("task")
    s = sub.add_parser("approve", help="OWNER ONLY: approve a task, optionally merge its PR")
    s.add_argument("task")
    args = ap.parse_args(argv)
    cfg = load_config()
    handlers = {"status": cmd_status, None: cmd_status, "new": cmd_new, "start": cmd_start,
                "check": cmd_check, "finish": cmd_finish, "out": cmd_out, "in": cmd_in,
                "review": cmd_review, "ci-review": cmd_ci_review, "handoff": cmd_handoff,
                "dashboard": cmd_dashboard, "ready": cmd_ready, "approve": cmd_approve}
    if args.cmd is None:
        args.all = False
    try:
        return handlers[args.cmd](args, cfg)
    except BridgeError as e:
        print("bridge: %s" % e.args[0], file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
