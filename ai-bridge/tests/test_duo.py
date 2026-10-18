# SPDX-License-Identifier: MIT
# Self-tests for duo mode. Uses fake CLIs (tests/fakes/), never the real
# Claude or Codex. The full duo flow is exercised in a scratch clone by the
# end-to-end check described in ai-bridge/docs/TESTING.md.
import io
import os
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
        self.assertIn("Claude → Codex", open(os.path.join(tmp, logs[0])).read())


if __name__ == "__main__":
    unittest.main()


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
