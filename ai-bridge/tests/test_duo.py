# SPDX-License-Identifier: MIT
# Self-tests for duo mode. Uses fake CLIs (tests/fakes/), never the real
# Claude or Codex. The full duo flow is exercised in a scratch clone by the
# end-to-end check described in ai-bridge/docs/TESTING.md.
import io
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
import bridge  # noqa: E402
import duo  # noqa: E402

FAKES = os.path.join(HERE, "fakes")


class Basics(unittest.TestCase):
    def test_other(self):
        self.assertEqual(duo.other("claude"), "codex")
        self.assertEqual(duo.other("codex"), "claude")

    def test_find_bin_env_override(self):
        with mock.patch.dict(os.environ, {"ALMOND_DUO_CODEX": os.path.join(FAKES, "fake_codex")}):
            self.assertTrue(duo.find_bin("codex", {"duo": {}}).endswith("fake_codex"))
        with mock.patch.dict(os.environ, {"ALMOND_DUO_CODEX": "/nonexistent/codex"}):
            with self.assertRaises(duo.DuoError):
                duo.find_bin("codex", {"duo": {}})

    def test_clean_env_drops_api_keys(self):
        with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "x", "ANTHROPIC_API_KEY": "y"}):
            env = duo.clean_env(["OPENAI_API_KEY", "ANTHROPIC_API_KEY"])
        self.assertNotIn("OPENAI_API_KEY", env)
        self.assertNotIn("ANTHROPIC_API_KEY", env)

    def test_render(self):
        lines = duo.render({"summary": "s", "steps": [{"what": "w", "files": ["a"]}], "risks": []})
        self.assertIn("- **summary:** s", lines)
        self.assertIn("- **risks:** none", lines)
        self.assertTrue(any("w" in l for l in lines))

    def test_schemas_are_strict(self):
        # Codex structured output needs every property required and no extras.
        for name in ("plan-schema.json", "plan-review-schema.json", "implement-schema.json",
                     "answer-schema.json", "review-schema.json"):
            def walk(s, where):
                if s.get("type") == "object":
                    self.assertFalse(s.get("additionalProperties", True), where)
                    self.assertEqual(sorted(s["required"]), sorted(s["properties"]), where)
                    for k, v in s["properties"].items():
                        walk(v, where + "." + k)
                if s.get("type") == "array":
                    walk(s["items"], where + "[]")
            walk(duo.load_schema(name), name)

    def test_tool_lists(self):
        self.assertNotIn("Edit", duo.CLAUDE_READ_TOOLS)
        self.assertIn("Edit", duo.CLAUDE_WRITE_TOOLS)
        self.assertTrue(any("git push" in t for t in duo.CLAUDE_DENIED))
        self.assertTrue(any("git commit" in t for t in duo.CLAUDE_DENIED))


class FakeCalls(unittest.TestCase):
    def setUp(self):
        self.env = mock.patch.dict(os.environ, {
            "ALMOND_DUO_CODEX": os.path.join(FAKES, "fake_codex"),
            "ALMOND_DUO_CLAUDE": os.path.join(FAKES, "fake_claude")})
        self.env.start()
        self.cfg = bridge.load_config()

    def tearDown(self):
        self.env.stop()

    def test_codex_answer_parsed_and_validated(self):
        result, usage = duo.call("codex", self.cfg, "a question", "answer-schema.json")
        self.assertEqual(result["answer"], "fake answer from codex")
        self.assertEqual(usage["tokens"], 1234)

    def test_claude_answer_parsed_and_validated(self):
        result, usage = duo.call("claude", self.cfg, "a question", "answer-schema.json")
        self.assertEqual(result["answer"], "fake answer from claude")
        self.assertEqual(usage["turns"], 2)

    def test_schema_mismatch_is_an_error(self):
        # The fake answers a "question" shape; asking for a plan must fail validation.
        with self.assertRaises(duo.DuoError):
            duo.call("codex", self.cfg, "a question", "plan-schema.json")

    def test_ask_writes_log(self):
        tmp = tempfile.mkdtemp()
        with mock.patch.object(duo, "CONV", tmp), mock.patch("sys.stdout", io.StringIO()) as out:
            args = mock.Mock(who="codex", question=["is", "this", "ok?"], from_ai=True)
            self.assertEqual(duo.cmd_ask(args, self.cfg), 0)
        self.assertIn("fake answer from codex", out.getvalue())
        logs = os.listdir(tmp)
        self.assertEqual(len(logs), 1)
        with open(os.path.join(tmp, logs[0])) as log:
            self.assertIn("Claude → Codex", log.read())


class CodexBinary(unittest.TestCase):
    def test_bundled_macos_paths(self):
        self.assertIn("/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex",
                      duo.CODEX_CANDIDATES)
        self.assertIn("/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/"
                      "Contents/MacOS/codex", duo.CODEX_CANDIDATES)
        self.assertTrue(any(c.startswith(os.path.expanduser("~/Applications/"))
                            for c in duo.CODEX_CANDIDATES))

    def test_fallback_used_when_not_on_path(self):
        target = duo.CODEX_CANDIDATES[1]
        with mock.patch.dict(os.environ, {}, clear=False), \
                mock.patch.object(duo.shutil, "which", return_value=None), \
                mock.patch.object(duo.os, "access", side_effect=lambda p, m: p == target):
            os.environ.pop("ALMOND_DUO_CODEX", None)
            self.assertEqual(duo.find_bin("codex", {"duo": {}}), target)

    def test_api_key_variables_dropped(self):
        self.assertIn("CODEX_API_KEY", duo.CODEX_DROP_ENV)
        self.assertIn("OPENAI_API_KEY", duo.CODEX_DROP_ENV)
        self.assertIn("ANTHROPIC_AUTH_TOKEN", duo.CLAUDE_DROP_ENV)

    def test_timeout_removes_result_file(self):
        tmp = tempfile.mkdtemp()
        made = []
        real = tempfile.NamedTemporaryFile

        def tracked(*a, **kw):
            f = real(*a, dir=tmp, **{k: v for k, v in kw.items() if k != "dir"})
            made.append(f.name)
            return f

        def boom(*a, **kw):
            raise duo.subprocess.TimeoutExpired(a[0], 60)

        with mock.patch.dict(os.environ, {"ALMOND_DUO_CODEX": os.path.join(FAKES, "fake_codex")}), \
                mock.patch.object(duo.tempfile, "NamedTemporaryFile", tracked), \
                mock.patch.object(duo.subprocess, "run", boom):
            with self.assertRaises(duo.DuoError):
                duo.call_codex({"duo": {}}, "q", "answer-schema.json", timeout=60)
        self.assertEqual(len(made), 1)
        self.assertFalse(os.path.exists(made[0]))


class DirtyTree(unittest.TestCase):
    """git_dirty must see tracked and untracked changes, even when the user's
    git config hides untracked files, and must ignore .gitignore'd caches."""

    def setUp(self):
        self.repo = tempfile.mkdtemp()
        self.git("init", "-q")
        self.git("config", "user.email", "t@example.invalid")
        self.git("config", "user.name", "t")
        self.git("config", "status.showUntrackedFiles", "no")
        shutil.copy(os.path.join(bridge.ROOT, ".gitignore"), self.repo)
        with open(os.path.join(self.repo, "a.txt"), "w") as f:
            f.write("a\n")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "init")
        self.patch = mock.patch.object(bridge, "git", lambda *a, check=False: bridge.run(
            ["git", *a], check=check, cwd=self.repo))
        self.patch.start()

    def tearDown(self):
        self.patch.stop()

    def git(self, *a):
        bridge.run(["git", *a], check=True, cwd=self.repo)

    def test_clean(self):
        self.assertEqual(duo.git_dirty(), [])

    def test_untracked_file_in_new_dir(self):
        os.makedirs(os.path.join(self.repo, "new", "deep"))
        open(os.path.join(self.repo, "new", "deep", "x.txt"), "w").close()
        self.assertEqual(duo.git_dirty(), ["new/deep/x.txt"])

    def test_tracked_change(self):
        with open(os.path.join(self.repo, "a.txt"), "a") as f:
            f.write("b\n")
        self.assertEqual(duo.git_dirty(), ["a.txt"])

    def test_python_caches_ignored(self):
        d = os.path.join(self.repo, "ai-bridge", "scripts", "__pycache__")
        os.makedirs(d)
        open(os.path.join(d, "duo.cpython-315.pyc"), "w").close()
        open(os.path.join(self.repo, "stray.pyo"), "w").close()
        self.assertEqual(duo.git_dirty(), [])


def plan(questions=(), implementer="codex"):
    return {"summary": "s", "steps": [], "tests": [], "risks": [], "implementer": implementer,
            "implementer_reason": "r", "sensitive_paths": [], "questions_for_owner": list(questions)}


def plan_review(verdict="agree", implementer_agree=True):
    return {"verdict": verdict, "concerns": ["c"] if verdict == "change" else [], "missing_steps": [],
            "implementer_agree": implementer_agree, "notes": "n"}


class PlanAgreement(unittest.TestCase):
    def run_plan(self, plans, reviews, forced=False):
        calls = {"review": [], "revise": 0}

        def review(cfg, task, critic, p, earlier=None):
            calls["review"].append(earlier)
            return reviews.pop(0), None

        def revise(*a):
            calls["revise"] += 1
            return plans.pop(0), None

        with mock.patch.object(duo, "step_plan", return_value=(plans.pop(0), None)), \
                mock.patch.object(duo, "step_plan_review", review), \
                mock.patch.object(duo, "step_plan_revise", revise), \
                mock.patch.object(duo, "say"), mock.patch.object(bridge, "write"):
            result = duo.agree_plan({}, {"id": "T-0001"}, "claude", "codex", implementer_forced=forced)
        return result, calls

    def test_agree_first_time_no_revision(self):
        (p, problems), calls = self.run_plan([plan()], [plan_review()])
        self.assertEqual(problems, [])
        self.assertEqual(calls["revise"], 0)
        self.assertEqual(len(calls["review"]), 1)

    def test_revision_is_reviewed_again(self):
        first = plan_review("change")
        (p, problems), calls = self.run_plan([plan(), plan()], [first, plan_review()])
        self.assertEqual(problems, [])
        self.assertEqual(calls["revise"], 1)
        self.assertEqual(calls["review"], [None, first])

    def test_unresolved_change_stops(self):
        (p, problems), calls = self.run_plan([plan(), plan()], [plan_review("change"), plan_review("change")])
        self.assertEqual(len(problems), 1)
        self.assertIn("still asks for changes", problems[0])
        self.assertEqual(calls["revise"], 1)   # revised once only

    def test_implementer_disagreement_triggers_revision_and_stops(self):
        (p, problems), calls = self.run_plan(
            [plan(), plan()], [plan_review("agree", False), plan_review("agree", False)])
        self.assertEqual(calls["revise"], 1)
        self.assertEqual(len(calls["review"]), 2)
        self.assertIn("implementer", problems[0])

    def test_forced_implementer_ignores_implementer_disagreement(self):
        (p, problems), calls = self.run_plan([plan()], [plan_review("agree", False)], forced=True)
        self.assertEqual(problems, [])
        self.assertEqual(calls["revise"], 0)

    def test_revision_cannot_drop_owner_questions(self):
        (p, problems), _ = self.run_plan(
            [plan(["Which wording?"]), plan(["Which colour?", "Which wording?"])],
            [plan_review("change"), plan_review()])
        self.assertEqual(p["questions_for_owner"], ["Which wording?", "Which colour?"])


class Sandbox(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = self.tmp.name
        self.patches = [mock.patch.object(bridge, name, os.path.join(d, sub)) for name, sub in
                        (("TASKS", "tasks"), ("REPORTS", "reports"), ("DECISIONS", "decisions"),
                         ("USAGE_LOG", "usage/usage.jsonl"), ("OUT", "out"))]
        self.patches.append(mock.patch.object(duo, "CONV", os.path.join(d, "conversations")))
        self.patches.append(mock.patch("sys.stdout", io.StringIO()))
        for p in self.patches:
            p.start()
        os.makedirs(bridge.TASKS)
        self.cfg = bridge.load_config()
        self.tid, _ = bridge.create_task("Duo test")

    def tearDown(self):
        for p in reversed(self.patches):
            p.stop()
        self.tmp.cleanup()


class StopForOwner(Sandbox):
    def test_needs_owner_and_questions_kept_in_task(self):
        with mock.patch.object(duo, "commit_all"):
            rc = duo.stop_for_owner(self.tid, "the plan is not agreed", ["they disagree"], ["Which wording?"])
        self.assertEqual(rc, 3)
        task = bridge.find_task(self.tid)
        self.assertEqual(task["status"], "needs-owner")
        self.assertIn("- [ ] Disagreement: they disagree", task["_body"])
        self.assertIn("- [ ] Which wording?", task["_body"])


def review(verdict):
    return {"verdict": verdict, "summary": "s", "findings": [], "status_claims_ok": True,
            "honesty_issues": [], "tests_assessment": "t", "questions_for_owner": []}


class ImplementRounds(Sandbox):
    def run_rounds(self, check_results, verdicts):
        seen = {"failed_passed": []}

        def implement(cfg, task, who, p, findings=None, failed_checks=None):
            seen["failed_passed"].append(list(failed_checks or []))
            return {"summary": "x", "files_changed": [], "tests_run": [], "not_done": [],
                    "notes_for_reviewer": ""}, None

        checks = iter([[{"name": "shell syntax", "status": s, "detail": ""}] for s in check_results])
        verdicts = iter(verdicts)
        with mock.patch.object(duo, "step_implement", implement), \
                mock.patch.object(bridge, "run_checks", lambda *a: next(checks)), \
                mock.patch.object(bridge, "format_checks", return_value=""), \
                mock.patch.object(duo, "commit_all"), \
                mock.patch.object(duo, "step_review", lambda *a: (review(next(verdicts)), None)):
            out = duo.implement_rounds(self.cfg, self.tid, "codex", "claude", plan(), "main")
        return out, seen

    def test_approved_with_passing_checks(self):
        (outcome, rnd, *_), _ = self.run_rounds(["pass"], ["approve"])
        self.assertEqual((outcome, rnd), ("approved", 1))

    def test_approval_does_not_hide_failed_checks(self):
        (outcome, rnd, *_), seen = self.run_rounds(["fail", "pass"], ["approve", "approve"])
        self.assertEqual((outcome, rnd), ("approved", 2))
        self.assertEqual(seen["failed_passed"], [[], ["shell syntax"]])

    def test_checks_still_failing_is_failed_and_bounded(self):
        (outcome, rnd, *_), _ = self.run_rounds(["fail", "fail", "fail"], ["approve", "approve", "approve"])
        self.assertEqual(outcome, "failed")
        self.assertEqual(rnd, int(self.cfg["limits"]["max_review_rounds"]))
        self.assertEqual(bridge.find_task(self.tid)["status"], "needs-owner")

    def test_unresolved_review_is_needs_owner(self):
        (outcome, rnd, *_), _ = self.run_rounds(["pass", "pass"], ["request_changes", "request_changes"])
        self.assertEqual((outcome, rnd), ("needs-owner", 2))


class Viewer(unittest.TestCase):
    def setUp(self):
        import importlib
        self.view = importlib.import_module("view")

    def test_render_turns_and_speakers(self):
        text = ("# T-0001 — duo conversation\n\nintro\n\n"
                "## 2026-10-18 15:10 · Claude → Codex: plan\n\n- **summary:** s\n  - nested\n\n_3s · 2 turns_\n"
                "## 2026-10-18 15:11 · Codex → Claude: review round 1 (approve)\n\n| a | b |\n|---|---|\n| 1 | 2 |\n"
                "## 2026-10-18 15:12 · Claude + Codex → Owner: done\n\nok\n")
        r = self.view.render(text)
        self.assertEqual(r["count"], 3)
        self.assertEqual(r["title"], "T-0001 — duo conversation")
        self.assertIn('class="msg claude"', r["turns"])
        self.assertIn('class="msg codex"', r["turns"])
        self.assertIn('class="msg claude-codex"', r["turns"])
        self.assertIn("<table>", r["turns"])
        self.assertIn('<div class="foot">3s · 2 turns</div>', r["turns"])
        self.assertIn("<ul><li><b>summary:</b> s</li><ul><li>nested</li></ul></ul>", r["turns"])

    def test_html_is_escaped(self):
        r = self.view.render("## 2026-10-18 15:10 · Codex → Claude: x\n\n<script>alert(1)</script>\n")
        self.assertNotIn("<script>", r["turns"])

    def test_only_serves_conversation_files(self):
        import http.client, threading
        from http.server import ThreadingHTTPServer
        tmp = tempfile.mkdtemp()
        with open(os.path.join(tmp, "T-0001.md"), "w") as f:
            f.write("# T\n\n## 2026-10-18 15:10 · Claude → Codex: plan\n\nhi\n")
        self.view.Handler.conv_dir = tmp
        server = ThreadingHTTPServer(("127.0.0.1", 0), self.view.Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            def get(path):
                c = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
                c.request("GET", path)
                r = c.getresponse()
                return r.status, r.read().decode()
            self.assertEqual(get("/")[0], 200)
            status, body = get("/api/list")
            self.assertIn("T-0001.md", body)
            self.assertEqual(get("/api/conv?name=T-0001.md")[0], 200)
            self.assertEqual(get("/api/conv?name=../../bridge.toml")[0], 404)
            self.assertEqual(get("/api/conv?name=%2E%2E%2Fsecret.md")[0], 404)
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    unittest.main()
