# SPDX-License-Identifier: MIT
# Self-tests for the Almond AI Bridge. No network, no paid calls: the OpenAI
# API is replaced by a fake. Run: python3 -m unittest discover -s ai-bridge/tests
import io
import json
import os
import sys
import tempfile
import unittest
import urllib.error
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
import bridge  # noqa: E402

GOOD_REVIEW = {
    "verdict": "request_changes",
    "summary": "T-0099 adds a script. One blocker.",
    "findings": [{"severity": "blocker", "file": "scripts/x.sh", "line": 3,
                  "issue": "bashism", "suggestion": "use POSIX test"}],
    "status_claims_ok": True,
    "honesty_issues": [],
    "tests_assessment": "Only syntax checked.",
    "questions_for_owner": [],
}


def cfg(**openai):
    c = bridge.load_config()
    c["openai"] = dict(c["openai"], **openai)
    return c


class Sandbox(unittest.TestCase):
    """Points the bridge's task/report/decision/usage folders at a temp dir."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = self.tmp.name
        self.patches = [mock.patch.object(bridge, name, os.path.join(d, sub)) for name, sub in
                        (("TASKS", "tasks"), ("REPORTS", "reports"), ("DECISIONS", "decisions"),
                         ("USAGE_LOG", "usage/usage.jsonl"), ("OUT", "out"))]
        for p in self.patches:
            p.start()
        os.makedirs(bridge.TASKS)

    def tearDown(self):
        for p in self.patches:
            p.stop()
        self.tmp.cleanup()


class FrontMatter(unittest.TestCase):
    def test_round_trip(self):
        meta = {"id": "T-0001", "title": "A: tricky title", "status": "ready", "review_round": 0, "pr": ""}
        text = bridge.dump_front_matter(meta, "\n## Goal\n\nx\n")
        back, body = bridge.parse_front_matter(text)
        self.assertEqual(back, meta)
        self.assertEqual(body, "\n## Goal\n\nx\n")

    def test_normalise_id(self):
        self.assertEqual(bridge.normalise_id("t-7"), "T-0007")
        self.assertEqual(bridge.normalise_id("12"), "T-0012")
        with self.assertRaises(bridge.BridgeError):
            bridge.normalise_id("task seven")


class Schema(unittest.TestCase):
    def test_good_review(self):
        self.assertEqual(bridge.validate(GOOD_REVIEW, bridge.load_schema()), [])

    def test_bad_reviews(self):
        schema = bridge.load_schema()
        bad = dict(GOOD_REVIEW, verdict="ship it")
        self.assertTrue(bridge.validate(bad, schema))
        missing = {k: v for k, v in GOOD_REVIEW.items() if k != "summary"}
        self.assertTrue(bridge.validate(missing, schema))
        extra = dict(GOOD_REVIEW, mood="happy")
        self.assertTrue(bridge.validate(extra, schema))
        not_bool = dict(GOOD_REVIEW, status_claims_ok=1)
        self.assertTrue(bridge.validate(not_bool, schema))
        null_line = json.loads(json.dumps(GOOD_REVIEW))
        null_line["findings"][0]["line"] = None
        self.assertEqual(bridge.validate(null_line, schema), [])

    def test_extract_json(self):
        fenced = "Here you go:\n```json\n%s\n```\nthanks" % json.dumps(GOOD_REVIEW)
        self.assertEqual(bridge.extract_json(fenced)["verdict"], "request_changes")
        self.assertEqual(bridge.extract_json(json.dumps(GOOD_REVIEW))["summary"], GOOD_REVIEW["summary"])
        with self.assertRaises(bridge.BridgeError):
            bridge.extract_json("no json here")


class TasksAndRounds(Sandbox):
    def test_create_and_validate(self):
        task_id, path = bridge.create_task("Test the launcher")
        self.assertEqual(task_id, "T-0001")
        self.assertTrue(os.path.basename(path).startswith("T-0001-test-the-launcher"))
        status, detail = bridge.check_bridge_files([])
        self.assertEqual(status, "pass", detail)
        self.assertEqual(bridge.create_task("Second")[0], "T-0002")

    def test_round_limit_stops_the_loop(self):
        task_id, _ = bridge.create_task("Loop test")
        bridge.record_review(bridge.find_task(task_id), GOOD_REVIEW, "test")
        self.assertEqual(bridge.find_task(task_id)["status"], "changes-requested")
        bridge.record_review(bridge.find_task(task_id), GOOD_REVIEW, "test")
        t = bridge.find_task(task_id)
        self.assertEqual(t["status"], "needs-owner")  # round 2 of 2: the owner decides
        self.assertEqual(t["review_round"], 2)
        with self.assertRaises(bridge.BridgeError):
            bridge.record_review(t, GOOD_REVIEW, "test")
        self.assertTrue(os.path.exists(os.path.join(bridge.REPORTS, "T-0001-review-2.json")))
        self.assertFalse(os.path.exists(os.path.join(bridge.REPORTS, "T-0001-review-3.json")))

    def test_approve_verdict_goes_to_owner(self):
        task_id, _ = bridge.create_task("Approve test")
        bridge.record_review(bridge.find_task(task_id), dict(GOOD_REVIEW, verdict="approve", findings=[]), "test")
        self.assertEqual(bridge.find_task(task_id)["status"], "needs-owner")

    def test_invalid_review_is_not_saved(self):
        task_id, _ = bridge.create_task("Bad review")
        with self.assertRaises(bridge.BridgeError):
            bridge.record_review(bridge.find_task(task_id), {"verdict": "approve"}, "test")
        self.assertEqual(bridge.find_task(task_id)["review_round"], 0)

    def test_in_decision_and_task_blocks(self):
        src = os.path.join(self.tmp.name, "answer.txt")
        with open(src, "w") as f:
            f.write("Sure.\n```almond-decision\ntitle: Use LXQt\ndecision: LXQt for AALDM\nreason: light\n```\n")
        out = io.StringIO()
        with mock.patch("sys.stdout", out):
            self.assertEqual(bridge.main(["in", "--file", src]), 0)
        files = os.listdir(bridge.DECISIONS)
        self.assertEqual(len(files), 1)
        text = bridge.read(os.path.join(bridge.DECISIONS, files[0]))
        self.assertIn("LXQt for AALDM", text)
        self.assertIn("proposed", text)
        with open(src, "w") as f:
            f.write("```almond-task\ntitle: Measure boot\npriority: high\ngoal: know the time\n"
                    "acceptance:\n- systemd-analyze recorded\n- five boots\n```\n")
        with mock.patch("sys.stdout", out):
            self.assertEqual(bridge.main(["in", "--file", src]), 0)
        t = bridge.find_task("T-0001")
        self.assertEqual((t["status"], t["proposed_by"], t["priority"]), ("backlog", "openai", "high"))
        self.assertIn("- [ ] five boots", t["_body"])

    def test_in_review_from_file(self):
        bridge.create_task("Review me")
        src = os.path.join(self.tmp.name, "review.txt")
        with open(src, "w") as f:
            f.write("```json\n%s\n```" % json.dumps(GOOD_REVIEW))
        with mock.patch("sys.stdout", io.StringIO()), mock.patch.object(bridge, "refresh_docs"):
            self.assertEqual(bridge.main(["in", "--file", src, "--task", "T-0001"]), 0)
        self.assertEqual(bridge.find_task("T-0001")["status"], "changes-requested")

    def test_approve_refuses_without_terminal(self):
        bridge.create_task("Owner only")
        err = io.StringIO()
        with mock.patch("sys.stdin", io.StringIO("T-0001\n")), mock.patch("sys.stderr", err):
            self.assertEqual(bridge.main(["approve", "T-0001"]), 2)
        self.assertIn("owner's own terminal", err.getvalue())
        self.assertEqual(bridge.find_task("T-0001")["status"], "ready")


class Costs(Sandbox):
    def test_disabled_blocks_everything(self):
        with self.assertRaises(bridge.BridgeError) as e:
            bridge.guard_spend(cfg(enabled=False), 1000, 0.0)
        self.assertIn("switched off", str(e.exception))

    def test_limits(self):
        c = cfg(enabled=True, model="gpt-5-mini", max_output_tokens=6000,
                per_call_limit_usd=0.10, monthly_limit_usd=2.0, max_input_chars=160000)
        tokens, worst = bridge.guard_spend(c, 40000, 0.0)
        self.assertAlmostEqual(worst, 10001 * 0.25 / 1e6 + 6000 * 2.0 / 1e6, places=6)
        with self.assertRaises(bridge.BridgeError):
            bridge.guard_spend(c, 40000, 1.999)          # monthly
        with self.assertRaises(bridge.BridgeError):
            bridge.guard_spend(c, 200000, 0.0)           # too big
        with self.assertRaises(bridge.BridgeError):
            bridge.guard_spend(cfg(enabled=True, per_call_limit_usd=0.001), 40000, 0.0)

    def test_month_spend(self):
        month = bridge.now().strftime("%Y-%m")
        bridge.log_usage({"time": month + "-02T10:00:00", "cost_usd": 0.25})
        bridge.log_usage({"time": month + "-03T10:00:00", "cost_usd": 0.5})
        bridge.log_usage({"time": "1999-01-01T00:00:00", "cost_usd": 9.0})
        self.assertAlmostEqual(bridge.month_spend(), 0.75)

    def test_unknown_model_price(self):
        with self.assertRaises(bridge.BridgeError):
            bridge.estimate_cost(cfg(model="no-such-model"), 100)


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class OpenAICall(unittest.TestCase):
    def test_success_parses_and_prices(self):
        seen = {}

        def opener(req, timeout):
            seen["body"] = json.loads(req.data)
            seen["auth"] = req.get_header("Authorization")
            return FakeResponse(json.dumps({
                "status": "completed", "model": "gpt-5-mini",
                "output": [{"type": "message", "content": [{"type": "output_text", "text": json.dumps(GOOD_REVIEW)}]}],
                "usage": {"input_tokens": 10000, "output_tokens": 2000}}).encode())

        review, usage = bridge.call_openai(cfg(model="gpt-5-mini"), "packet", "test-key", opener)
        self.assertEqual(review["verdict"], "request_changes")
        self.assertAlmostEqual(usage["cost_usd"], 10000 * 0.25 / 1e6 + 2000 * 2.0 / 1e6)
        self.assertEqual(seen["auth"], "Bearer test-key")
        self.assertEqual(seen["body"]["text"]["format"]["type"], "json_schema")
        self.assertTrue(seen["body"]["text"]["format"]["strict"])
        self.assertFalse(seen["body"]["store"])

    def test_http_error_message(self):
        def opener(req, timeout):
            raise urllib.error.HTTPError(req.full_url, 401, "Unauthorized", {},
                                         io.BytesIO(b'{"error": {"message": "Incorrect API key"}}'))
        with self.assertRaises(bridge.BridgeError) as e:
            bridge.call_openai(cfg(), "packet", "bad", opener)
        self.assertIn("401", str(e.exception.args[0]))
        self.assertIn("Incorrect API key", e.exception.args[0])

    def test_incomplete_reports_billed_tokens(self):
        def opener(req, timeout):
            return FakeResponse(json.dumps({"status": "incomplete", "incomplete_details": {"reason": "max_output_tokens"},
                                            "output": [], "usage": {"input_tokens": 5, "output_tokens": 6000}}).encode())
        with self.assertRaises(bridge.BridgeError) as e:
            bridge.call_openai(cfg(model="gpt-5-mini"), "p", "k", opener)
        self.assertEqual(e.exception.args[1]["output_tokens"], 6000)


class DryRun(Sandbox):
    def test_review_without_flags_never_calls_the_api(self):
        bridge.create_task("Dry run")
        with mock.patch.object(bridge, "call_openai", side_effect=AssertionError("network!")), \
                mock.patch("sys.stdout", io.StringIO()) as out:
            self.assertEqual(bridge.main(["review", "T-0001", "--live"]), 0)   # --yes-spend missing
        self.assertIn("DRY RUN", out.getvalue())
        self.assertTrue(os.path.exists(os.path.join(bridge.OUT, "review-T-0001.md")))

    def test_live_refused_when_disabled(self):
        bridge.create_task("Disabled")
        with mock.patch.object(bridge, "call_openai", side_effect=AssertionError("network!")), \
                mock.patch.dict(os.environ, {"OPENAI_API_KEY": "x"}), \
                mock.patch("sys.stdout", io.StringIO()), mock.patch("sys.stderr", io.StringIO()) as err:
            self.assertEqual(bridge.main(["review", "T-0001", "--live", "--yes-spend"]), 2)
        self.assertIn("switched off", err.getvalue())


class Scanners(unittest.TestCase):
    def test_secret_patterns(self):
        fake = {
            "OpenAI key": "sk-" + "proj-" + "A1b2" * 12,
            "Anthropic key": "sk-" + "ant-" + "api03-" + "x" * 30,
            "GitHub token": "gh" + "p_" + "Z" * 36,
            "Private key": "-----BEGIN " + "OPENSSH PRIVATE KEY-----",
        }
        for label, value in fake.items():
            hit = any(label == lab and pat.search("token = %s\n" % value) for lab, pat in bridge.SECRET_PATTERNS)
            self.assertTrue(hit, label)
        clean = "OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}\nsk-short\ntask-runner"
        self.assertFalse(any(p.search(clean) for _, p in bridge.SECRET_PATTERNS))

    def test_sensitive_paths(self):
        c = bridge.load_config()
        hits = bridge.sensitive_hits([("M", ".github/workflows/x.yml"), ("M", "docs/ROADMAP.md"),
                                      ("D", "docs/old.md"), ("A", "config/hooks/live/0300.hook.chroot"),
                                      ("M", "scripts/build.sh")], c)
        self.assertEqual(hits, [".github/workflows/x.yml", "docs/old.md (deleted)",
                                "config/hooks/live/0300.hook.chroot", "scripts/build.sh"])

    def test_filter_diff(self):
        diff = ("diff --git a/a.svg b/a.svg\n+<svg/>\n"
                "diff --git a/s.sh b/s.sh\n+echo hi\n")
        out = bridge.filter_diff(diff, ["*.svg"])
        self.assertNotIn("<svg/>", out)
        self.assertIn("echo hi", out)
        self.assertIn("a.svg left out", out)

    def test_replace_block(self):
        text = "a\n<!-- bridge:x:start -->\nold\n<!-- bridge:x:end -->\nb"
        self.assertEqual(bridge.replace_block(text, "x", "new"),
                         "a\n<!-- bridge:x:start -->\nnew\n<!-- bridge:x:end -->\nb")
        with self.assertRaises(bridge.BridgeError):
            bridge.replace_block("no markers", "x", "new")


if __name__ == "__main__":
    unittest.main()
