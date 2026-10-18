# SPDX-License-Identifier: MIT
# Self-tests for duo mode. Uses fake CLIs (tests/fakes/), never the real
# Claude or Codex. The full duo flow is exercised in a scratch clone by the
# end-to-end check described in ai-bridge/docs/TESTING.md.
import io
import json
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
        tmp = tempfile.mkdtemp()
        self.patches = [mock.patch.dict(os.environ, {
            "ALMOND_DUO_CODEX": os.path.join(FAKES, "fake_codex"),
            "ALMOND_DUO_CLAUDE": os.path.join(FAKES, "fake_claude")}),
            # Never touch the real chat, sessions or state.
            mock.patch.object(duo, "SESSIONS", os.path.join(tmp, "sessions.json")),
            mock.patch.object(duo, "LIVE_CHAT", os.path.join(tmp, "chat.md")),
            mock.patch.object(duo, "STATE", os.path.join(tmp, "state.json"))]
        for p in self.patches:
            p.start()
        self.cfg = bridge.load_config()

    def tearDown(self):
        for p in self.patches:
            p.stop()

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
        self.assertIn("Claude → Codex", bridge.read(os.path.join(tmp, logs[0])))


if __name__ == "__main__":
    unittest.main()


class Sessions(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.patches = [mock.patch.object(duo, "SESSIONS", os.path.join(self.tmp, "sessions.json")),
                        mock.patch.object(duo, "LIVE_CHAT", os.path.join(self.tmp, "chat.md")),
                        mock.patch.object(duo, "STATE", os.path.join(self.tmp, "state.json")),
                        mock.patch.dict(os.environ, {
                            "ALMOND_DUO_CODEX": os.path.join(FAKES, "fake_codex"),
                            "ALMOND_DUO_CLAUDE": os.path.join(FAKES, "fake_claude"),
                            "FAKE_AI_STATE": self.tmp})]
        for p in self.patches:
            p.start()
        self.cfg = bridge.load_config()

    def tearDown(self):
        for p in self.patches:
            p.stop()

    def test_one_session_per_ai_is_reused(self):
        for _ in range(3):
            duo.call("codex", self.cfg, "q", "answer-schema.json")
            duo.call("claude", self.cfg, "q", "answer-schema.json")
        ses = duo.load_sessions()
        self.assertEqual(ses["codex"], "fake-codex-thread")
        self.assertTrue(ses["claude"])
        log = bridge.read(os.path.join(self.tmp, "sessions.log")).split("\n")
        codex = [l.split()[1] for l in log if l.startswith("codex")]
        claude = [l.split()[1] for l in log if l.startswith("claude")]
        self.assertEqual(codex, ["new", "fake-codex-thread", "fake-codex-thread"])
        self.assertEqual(claude[0], "new")
        self.assertEqual(claude[1], claude[2])
        self.assertEqual(claude[1], ses["claude"])

    def test_chat_new_forgets_sessions(self):
        duo.save_session("codex", "x")
        duo.save_session("claude", "y")
        with mock.patch("sys.stdout", io.StringIO()):
            duo.cmd_chat(mock.Mock(new=True), self.cfg)
        self.assertEqual(duo.load_sessions(), {})
        self.assertIn("fresh sessions", bridge.read(duo.LIVE_CHAT))

    def test_discuss_both_answer_in_one_chat(self):
        with mock.patch("sys.stdout", io.StringIO()):
            duo.cmd_discuss(mock.Mock(question=["is", "it", "ok?"], first=None, no_echo=False), self.cfg)
        chat = bridge.read(duo.LIVE_CHAT)
        self.assertIn("Owner → Claude + Codex: question", chat)
        self.assertIn("Claude → Owner: answer", chat)
        self.assertIn("Codex → Owner: agrees", chat)
        self.assertNotIn("running", duo.load_state())


class ChatServer(unittest.TestCase):
    def setUp(self):
        import importlib
        self.view = importlib.import_module("view")
        self.tmp = tempfile.mkdtemp()
        self.patches = [mock.patch.object(duo, "LIVE_CHAT", os.path.join(self.tmp, "chat.md")),
                        mock.patch.object(duo, "STATE", os.path.join(self.tmp, "state.json"))]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.patches:
            p.stop()

    def test_render_turns_and_speakers(self):
        text = ("# Almond chat\n\nintro\n\n"
                "## 2026-10-18 15:10 · Claude → Codex: T-0001 · plan\n\n- **summary:** s\n  - nested\n\n_3s · 2 turns_\n"
                "## 2026-10-18 15:11 · Codex → Claude: review round 1 (approve)\n\n| a | b |\n|---|---|\n| 1 | 2 |\n"
                "## 2026-10-18 15:12 · Owner → Claude + Codex: task\n\nok\n")
        r = self.view.render(text)
        self.assertEqual(r["count"], 3)
        self.assertIn('class="msg claude"', r["turns"])
        self.assertIn('class="msg codex"', r["turns"])
        self.assertIn('class="msg owner"', r["turns"])
        self.assertIn("<table>", r["turns"])
        self.assertIn('<div class="foot">3s · 2 turns</div>', r["turns"])
        self.assertIn("<ul><li><b>summary:</b> s</li><ul><li>nested</li></ul></ul>", r["turns"])

    def test_html_is_escaped(self):
        r = self.view.render("## 2026-10-18 15:10 · Codex → Claude: x\n\n<script>alert(1)</script>\n")
        self.assertNotIn("<script>", r["turns"])

    def serve(self):
        import threading
        from http.server import ThreadingHTTPServer
        server = ThreadingHTTPServer(("127.0.0.1", 0), self.view.Handler)
        self.view.Handler.port = server.server_address[1]
        self.view.Handler.token = "secret-token"
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        return server.server_address[1]

    def request(self, port, method, path, body=None, headers=None, host=None):
        import http.client
        c = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        h = {"Host": host or "127.0.0.1:%d" % port}
        h.update(headers or {})
        c.request(method, path, body=body, headers=h)
        r = c.getresponse()
        return r.status, r.read().decode()

    def test_security_token_and_host(self):
        submitted = []
        fake_chat = mock.Mock(busy=False, q=mock.Mock(empty=lambda: True, qsize=lambda: 0),
                              submit=lambda t, m: (submitted.append((t, m)) or ("task", 1)))
        with mock.patch.object(self.view, "CHAT", fake_chat):
            port = self.serve()
            status, page = self.request(port, "GET", "/")
            self.assertEqual(status, 200)
            self.assertIn("secret-token", page)
            # DNS-rebinding style request with a foreign Host header
            self.assertEqual(self.request(port, "GET", "/", host="evil.example:%d" % port)[0], 403)
            body = json.dumps({"text": "do it", "mode": "task"})
            # no token / wrong token / foreign host -> refused, nothing submitted
            self.assertEqual(self.request(port, "POST", "/api/send", body)[0], 403)
            self.assertEqual(self.request(port, "POST", "/api/send", body, {"X-Almond-Token": "nope"})[0], 403)
            self.assertEqual(self.request(port, "POST", "/api/send", body, {"X-Almond-Token": "secret-token"},
                                          host="evil.example")[0], 403)
            self.assertEqual(submitted, [])
            status, _ = self.request(port, "POST", "/api/send", body, {"X-Almond-Token": "secret-token"})
            self.assertEqual(status, 200)
            self.assertEqual(submitted, [("do it", "task")])
            too_long = json.dumps({"text": "x" * 5000, "mode": "task"})
            self.assertEqual(self.request(port, "POST", "/api/send", too_long, {"X-Almond-Token": "secret-token"})[0], 400)
            self.assertEqual(self.request(port, "GET", "/api/state")[0], 200)

    def test_answer_goes_to_paused_task(self):
        duo.save_state(paused={"task": "T-0042", "branch": "task/T-0042-x", "base": "b", "questions": ["q?"]})
        chat = self.view.Chat.__new__(self.view.Chat)
        chat.q = __import__("queue").Queue()
        chat.busy = False
        kind, _ = chat.submit("use the short wording", "task")
        self.assertEqual(kind, "answer")
        self.assertEqual(chat.q.get()[0:2], ("answer", "use the short wording"))
        kind, _ = chat.submit("what is AALDM?", "question")
        self.assertEqual(kind, "question")
        self.assertIn("what is AALDM?", bridge.read(duo.LIVE_CHAT))


if __name__ == "__main__":
    unittest.main()
