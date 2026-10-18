#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Almond Linux - Almond AI Bridge: the one Almond chat.
#
#     ai-bridge/bridge view --open        # http://127.0.0.1:4820
#
# One conversation between the owner, Claude and Codex (.bridge-out/chat.md).
# Type a task or a question at the bottom:
#   - Task: Claude and Codex plan, build and review it (ai-bridge/bridge duo)
#     and open a PR when done. If they ask you something, your next message
#     is the answer and the task carries on by itself.
#   - Question: Claude answers, Codex checks the answer (ai-bridge/bridge discuss).
# Messages are handled one at a time, in order.
#
# Local only: listens on 127.0.0.1, checks the Host header and requires a
# per-start token on every message, so other web pages cannot send commands.
# Standard library only.

import argparse
import html
import json
import os
import queue
import re
import secrets
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bridge  # noqa: E402
import duo  # noqa: E402

BRIDGE_PY = os.path.join(HERE, "bridge.py")
RUN_LOGS = os.path.join(bridge.OUT, "runs")
TURN = re.compile(r"^## (?P<when>\d{4}-\d{2}-\d{2} \d{2}:\d{2}|\d{2}:\d{2}) · (?P<who>[^→\n]+?)(?: → (?P<to>[^:\n]+))?(?:: (?P<step>.*))?$")
MAX_MESSAGE = 4000


# ------------------------------------------------------------ rendering

def inline(text):
    t = html.escape(text)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<![\w*])_(.+?)_(?![\w*])", r"<i>\1</i>", t)
    t = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", r'<a href="\2" target="_blank" rel="noopener">\1</a>', t)
    t = re.sub(r"(?<![\"'>])(https://github\.com/[\w./#-]+)", r'<a href="\1" target="_blank" rel="noopener">\1</a>', t)
    return t


def blocks(lines):
    """Small Markdown subset: lists (nested by indent), tables, code, paragraphs."""
    out, i = [], 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("```"):
            j = i + 1
            while j < len(lines) and not lines[j].startswith("```"):
                j += 1
            out.append("<pre>%s</pre>" % html.escape("\n".join(lines[i + 1:j])))
            i = j + 1
        elif line.lstrip().startswith("|"):
            rows = []
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-+:?", c) for c in cells if c):
                    rows.append(cells)
                i += 1
            if rows:
                head = "".join("<th>%s</th>" % inline(c) for c in rows[0])
                body = "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % inline(c.replace("<br>", " / ")) for c in r)
                               for r in rows[1:])
                out.append('<div class="tw"><table><tr>%s</tr>%s</table></div>' % (head, body))
        elif re.match(r"^\s*[-*] ", line):
            html_list, stack = [], []
            while i < len(lines) and re.match(r"^\s*[-*] ", lines[i]):
                depth = (len(lines[i]) - len(lines[i].lstrip())) // 2
                while len(stack) < depth + 1:
                    html_list.append("<ul>")
                    stack.append(1)
                while len(stack) > depth + 1:
                    html_list.append("</ul>")
                    stack.pop()
                html_list.append("<li>%s</li>" % inline(lines[i].lstrip()[2:]))
                i += 1
            html_list += ["</ul>"] * len(stack)
            out.append("".join(html_list))
        elif line.strip():
            para = [line]
            i += 1
            while i < len(lines) and lines[i].strip() and not re.match(r"^\s*([-*] |\||```)", lines[i]):
                para.append(lines[i])
                i += 1
            out.append("<p>%s</p>" % inline(" ".join(para)))
        else:
            i += 1
    return "".join(out)


def speaker_class(who):
    w = who.lower()
    for key in ("claude + codex", "claude", "codex", "owner", "checks", "bridge"):
        if w.startswith(key):
            return key.replace(" + ", "-")
    return "other"


def render(text):
    title, intro, turns, cur = "", [], [], None
    for line in text.splitlines():
        if line.startswith("# ") and not title:
            title = line[2:].strip()
            continue
        m = TURN.match(line)
        if m:
            cur = {"meta": m.groupdict(), "lines": []}
            turns.append(cur)
        elif cur is None:
            intro.append(line)
        else:
            cur["lines"].append(line)
    parts = []
    for t in turns:
        meta = t["meta"]
        who = meta["who"].strip()
        to = (meta.get("to") or "").strip()
        body_lines, foot = t["lines"], ""
        while body_lines and not body_lines[-1].strip():
            body_lines = body_lines[:-1]
        if body_lines and re.fullmatch(r"\s*_.*_\s*", body_lines[-1]):
            foot = '<div class="foot">%s</div>' % inline(body_lines[-1].strip().strip("_"))
            body_lines = body_lines[:-1]
        parts.append(
            '<article class="msg %s"><header><span class="who">%s</span>%s'
            '<span class="step">%s</span><time>%s</time></header><div class="body">%s</div>%s</article>' % (
                speaker_class(who), html.escape(who), (' <span class="to">→ %s</span>' % html.escape(to)) if to else "",
                html.escape(meta.get("step") or ""), html.escape(meta["when"]), blocks(body_lines), foot))
    return {"title": title, "intro": blocks(intro), "turns": "".join(parts), "count": len(turns)}


# --------------------------------------------------------------- worker

class Chat:
    """Handles owner messages one at a time, in order."""

    def __init__(self):
        self.q = queue.Queue()
        self.busy = False
        self.thread = threading.Thread(target=self.loop, daemon=True)
        self.thread.start()

    def submit(self, text, mode):
        paused = duo.load_state().get("paused")
        if mode == "task" and paused:
            kind = "answer"            # duo writes the answer into the chat itself
        else:
            kind = mode
            duo.chat_say("Owner", "Claude + Codex", "question" if mode == "question" else "task", text)
        self.q.put((kind, text, paused))
        return kind, self.q.qsize() + (1 if self.busy else 0)

    def loop(self):
        while True:
            kind, text, paused = self.q.get()
            self.busy = True
            try:
                if kind == "question":
                    cmd = ["discuss", text, "--no-echo"]
                elif kind == "answer":
                    cmd = ["duo", paused["task"], "--answer", text]
                else:
                    cmd = ["duo", text]
                self.run(cmd)
            finally:
                self.busy = False

    def run(self, args):
        os.makedirs(RUN_LOGS, exist_ok=True)
        log = os.path.join(RUN_LOGS, time.strftime("%Y%m%d-%H%M%S") + ".log")
        with open(log, "w", encoding="utf-8") as f:
            env = dict(os.environ, ALMOND_CHAT_SERVER="1")
            p = subprocess.run([sys.executable, BRIDGE_PY] + args, cwd=bridge.ROOT,
                               stdout=f, stderr=subprocess.STDOUT, text=True, env=env)
        if p.returncode not in (0, 3):
            tail = bridge.read(log).strip().splitlines()[-6:]
            if not any("The run stopped" in l or "could not be answered" in l for l in tail):
                duo.chat_say("Bridge", "Owner", "error", "Something went wrong (log: `%s`):\n\n```\n%s\n```"
                             % (bridge.rel(log), "\n".join(tail)))


CHAT = None


# ---------------------------------------------------------------- page

PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="almond-token" content="__TOKEN__">
<title>Almond Chat</title>
<style>
:root{--bg:#f5f2eb;--panel:#fbf9f4;--ink:#2b2118;--muted:#6b5a4a;--line:#e3d9c8;--brown:#8b5a2b;
--claude:#f6e3cf;--claude-b:#b8672a;--codex:#e3edf7;--codex-b:#2f5a8a;--owner:#efe8dc;--owner-b:#6b5a4a;
--checks:#e4efe0;--checks-b:#4a7a3f;--both:#f3ecd9;--both-b:#8b5a2b;--bridge:#f6e1e1;--bridge-b:#a33}
@media (prefers-color-scheme:dark){:root{--bg:#1b1c20;--panel:#24211d;--ink:#f5deb3;--muted:#c9b48f;--line:#3d3328;
--brown:#d2a679;--claude:#3a2a1c;--claude-b:#e09a5f;--codex:#1c2a3a;--codex-b:#7fb0e6;--owner:#2c2824;--owner-b:#c9b48f;
--checks:#1f3020;--checks-b:#8cc47f;--both:#33291c;--both-b:#d2a679;--bridge:#3a1f1f;--bridge-b:#e08a8a}}
*{box-sizing:border-box}html,body{height:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 "Atkinson Hyperlegible",system-ui,sans-serif;display:flex;flex-direction:column}
header.top{display:flex;flex-wrap:wrap;gap:8px;align-items:center;justify-content:space-between;padding:10px 16px;border-bottom:1px solid var(--line);background:var(--panel)}
header.top h1{margin:0;font-size:18px}.sub{color:var(--muted);font-size:12.5px}
.live{font-size:13px;padding:3px 10px;border-radius:12px;background:var(--line);color:var(--muted)}
.live.on{background:var(--checks);color:var(--checks-b)}.live.on::before{content:"● "}
.live.wait{background:var(--claude);color:var(--claude-b)}
#scroll{flex:1;overflow-y:auto}main{padding:8px 16px 16px;max-width:920px;margin:0 auto}
.intro{color:var(--muted);font-size:13.5px}
.msg{border-radius:10px;padding:10px 14px;margin:12px 0;border-left:4px solid var(--owner-b);background:var(--owner);max-width:92%}
.msg.claude{background:var(--claude);border-color:var(--claude-b)}
.msg.codex{background:var(--codex);border-color:var(--codex-b);margin-left:auto}
.msg.checks{background:var(--checks);border-color:var(--checks-b);margin-left:auto}
.msg.claude-codex{background:var(--both);border-color:var(--both-b)}
.msg.bridge{background:var(--bridge);border-color:var(--bridge-b)}
.msg.owner{margin-left:auto;border-left:0;border-right:4px solid var(--owner-b)}
.msg header{display:flex;flex-wrap:wrap;gap:6px;align-items:baseline;font-size:13px;margin-bottom:4px}
.who{font-weight:bold;font-size:14px}.to{color:var(--muted)}.step{background:rgba(127,127,127,.15);padding:0 6px;border-radius:4px}
time{margin-left:auto;color:var(--muted);font-family:"DejaVu Sans Mono",ui-monospace,monospace;font-size:12px}
.body p{margin:4px 0}.body ul{margin:2px 0;padding-left:20px}.foot{color:var(--muted);font-size:12px;margin-top:6px}
code,pre{font-family:"DejaVu Sans Mono",ui-monospace,monospace;font-size:12.5px}
pre{white-space:pre-wrap;background:rgba(127,127,127,.12);padding:8px;border-radius:6px}
.tw{overflow-x:auto}table{border-collapse:collapse;font-size:13px;margin:4px 0}td,th{border:1px solid var(--line);padding:3px 7px;text-align:left}
.empty{color:var(--muted);margin-top:40px;text-align:center}a{color:var(--brown)}
#waiting{display:none;max-width:920px;margin:0 auto;padding:8px 16px;color:var(--claude-b);font-size:14px}
form{border-top:1px solid var(--line);background:var(--panel);padding:10px 16px}
.row{max-width:920px;margin:0 auto;display:flex;gap:8px;align-items:flex-end}
textarea{flex:1;resize:vertical;min-height:44px;max-height:200px;padding:9px 11px;border-radius:8px;border:1px solid var(--line);
background:var(--bg);color:var(--ink);font:inherit}
.modes{display:flex;border:1px solid var(--line);border-radius:8px;overflow:hidden}
.modes label{padding:9px 10px;cursor:pointer;font-size:13.5px;user-select:none}
.modes input{position:absolute;opacity:0;pointer-events:none}
.modes input:checked+span{font-weight:bold;color:var(--brown)}
.modes label:has(input:checked){background:var(--bg)}
.modes input:focus-visible+span{outline:2px solid var(--brown);outline-offset:2px}
button.send{padding:10px 16px;border-radius:8px;border:0;background:var(--brown);color:var(--panel);font:inherit;font-weight:bold;cursor:pointer}
button.send:disabled{opacity:.5;cursor:default}.hint{max-width:920px;margin:4px auto 0;color:var(--muted);font-size:12px}
@media (max-width:560px){.row{flex-wrap:wrap}textarea{flex-basis:100%}}
</style></head><body>
<header class="top"><div><h1>Almond Chat</h1><div class="sub">You, Claude and Codex, in one conversation</div></div>
<span id="live" class="live">idle</span></header>
<div id="scroll"><main><div id="intro" class="intro"></div><div id="turns"><p class="empty">Loading…</p></div></main></div>
<div id="waiting"></div>
<form id="f" autocomplete="off">
  <div class="row">
    <textarea id="text" placeholder="Give Claude and Codex a task, or ask them something…" aria-label="Message"></textarea>
    <div class="modes" role="radiogroup" aria-label="Message type">
      <label><input type="radio" name="mode" value="task" checked><span>Task</span></label>
      <label><input type="radio" name="mode" value="question"><span>Question</span></label>
    </div>
    <button class="send" id="send" type="submit">Send</button>
  </div>
  <div class="hint" id="hint">Tasks: they plan, build, review and open a PR; nothing is merged without you. Questions: Claude answers, Codex checks. ⌘/Ctrl + Enter sends.</div>
</form>
<script>
const token = document.querySelector('meta[name="almond-token"]').content;
let stamp = "", state = {};
const sc = document.getElementById("scroll"), ta = document.getElementById("text");
async function j(u, o){ const r = await fetch(u, Object.assign({cache:"no-store"}, o||{})); return r.json(); }
function setMode(m){ document.querySelector('input[value="'+m+'"]').checked = true; }
ta.addEventListener("input", () => { if (!state.paused) setMode(/\\?\\s*$/.test(ta.value) ? "question" : "task"); });
ta.addEventListener("keydown", e => { if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) { e.preventDefault(); document.getElementById("f").requestSubmit(); } });
document.getElementById("f").addEventListener("submit", async e => {
  e.preventDefault(); const text = ta.value.trim(); if (!text) return;
  const mode = document.querySelector('input[name="mode"]:checked').value;
  const btn = document.getElementById("send"); btn.disabled = true;
  try {
    const r = await j("api/send", {method:"POST", headers:{"Content-Type":"application/json","X-Almond-Token":token}, body: JSON.stringify({text, mode})});
    if (r.error) alert(r.error); else { ta.value = ""; setMode("task"); }
  } catch (err) { alert("The chat server is not reachable."); }
  btn.disabled = false; stamp = ""; tick();
});
async function tick(){
  try {
    const s = await j("api/state"); state = s;
    const live = document.getElementById("live"), w = document.getElementById("waiting");
    if (s.paused) { live.textContent = "waiting for your answer"; live.className = "live wait";
      w.style.display = "block"; w.innerHTML = "<b>" + s.paused.task + " is waiting for your answer:</b> " + s.paused.questions.map(q => q.replace(/[<&]/g, c => c === "<" ? "&lt;" : "&amp;")).join(" · ") + "<br>Type it below and press Send: the task continues by itself.";
      setMode("task"); }
    else { w.style.display = "none";
      live.textContent = s.working ? (s.queued > 1 ? "Claude and Codex are working (" + (s.queued - 1) + " more queued)" : "Claude and Codex are working") : "idle";
      live.className = "live" + (s.working ? " on" : ""); }
    if (s.mtime === stamp) return;
    const nearBottom = sc.scrollTop + sc.clientHeight >= sc.scrollHeight - 80;
    const c = await j("api/chat");
    document.getElementById("intro").innerHTML = c.intro;
    document.getElementById("turns").innerHTML = c.turns || '<p class="empty">No messages yet. Type a task or a question below.</p>';
    if (nearBottom || !stamp) sc.scrollTop = sc.scrollHeight;
    stamp = s.mtime;
  } catch (e) { document.getElementById("live").textContent = "chat server offline"; }
}
tick(); setInterval(tick, 2500);
</script></body></html>"""


class Handler(BaseHTTPRequestHandler):
    token = ""
    port = 4820

    def send(self, code, body, ctype="application/json"):
        data = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def host_ok(self):
        # DNS-rebinding guard: only answer for our own loopback names.
        return self.headers.get("Host", "") in ("127.0.0.1:%d" % self.port, "localhost:%d" % self.port)

    def do_GET(self):
        if not self.host_ok():
            return self.send(403, json.dumps({"error": "forbidden"}))
        url = urlparse(self.path)
        if url.path in ("/", "/index.html"):
            return self.send(200, PAGE.replace("__TOKEN__", self.token), "text/html; charset=utf-8")
        if url.path == "/api/state":
            st = duo.load_state()
            try:
                mtime = str(os.stat(duo.LIVE_CHAT).st_mtime_ns)
            except OSError:
                mtime = "0"
            busy = bool(CHAT and (CHAT.busy or not CHAT.q.empty())) or bool(st.get("running"))
            return self.send(200, json.dumps({"working": busy, "queued": (CHAT.q.qsize() + (1 if CHAT.busy else 0)) if CHAT else 0,
                                              "paused": st.get("paused"), "mtime": mtime}))
        if url.path == "/api/chat":
            try:
                text = bridge.read(duo.LIVE_CHAT)
            except OSError:
                text = "# Almond chat\n"
            return self.send(200, json.dumps(render(text)))
        self.send(404, json.dumps({"error": "not found"}))

    def do_POST(self):
        if not self.host_ok() or self.headers.get("X-Almond-Token", "") != self.token:
            return self.send(403, json.dumps({"error": "forbidden"}))
        if urlparse(self.path).path != "/api/send":
            return self.send(404, json.dumps({"error": "not found"}))
        try:
            n = int(self.headers.get("Content-Length", "0"))
            data = json.loads(self.rfile.read(min(n, 20000)) or b"{}")
        except (ValueError, TypeError):
            return self.send(400, json.dumps({"error": "bad request"}))
        text = str(data.get("text", "")).strip()
        mode = data.get("mode") if data.get("mode") in ("task", "question") else "task"
        if not text:
            return self.send(400, json.dumps({"error": "empty message"}))
        if len(text) > MAX_MESSAGE:
            return self.send(400, json.dumps({"error": "message too long (max %d characters)" % MAX_MESSAGE}))
        kind, position = CHAT.submit(text, mode)
        self.send(200, json.dumps({"ok": True, "kind": kind, "position": position}))

    def log_message(self, *a):
        pass


def main():
    global CHAT
    ap = argparse.ArgumentParser(description="The one Almond chat (owner, Claude, Codex)")
    ap.add_argument("--port", type=int, default=4820)
    args = ap.parse_args()
    Handler.token = secrets.token_urlsafe(24)
    Handler.port = args.port
    CHAT = Chat()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print("Almond chat: http://127.0.0.1:%d  (log: %s)" % (args.port, bridge.rel(duo.LIVE_CHAT)))
    sys.stdout.flush()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
