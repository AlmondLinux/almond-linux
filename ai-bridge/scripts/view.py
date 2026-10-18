#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Almond Linux - Almond AI Bridge: live viewer for Claude <-> Codex
# conversations (ai-bridge/conversations/*.md).
#
#     python3 ai-bridge/scripts/view.py            # http://127.0.0.1:4820
#     python3 ai-bridge/scripts/view.py --port 4821 --dir path/to/conversations
#
# Shows each turn as a chat bubble (Claude, Codex, Owner, Checks), updates
# every few seconds while a duo run is going, and says when one is running.
# Local only (127.0.0.1), read-only, standard library only.

import argparse
import html
import json
import os
import re
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DIR = os.path.join(os.path.dirname(HERE), "conversations")
TURN = re.compile(r"^## (?P<when>\d{4}-\d{2}-\d{2} \d{2}:\d{2}|\d{2}:\d{2}) · (?P<who>[^→\n]+?)(?: → (?P<to>[^:\n]+))?(?:: (?P<step>.*))?$")


def inline(text):
    t = html.escape(text)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<![\w*])_(.+?)_(?![\w*])", r"<i>\1</i>", t)
    t = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2">\1</a>', t)
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
    for key in ("claude + codex", "claude", "codex", "owner", "checks"):
        if w.startswith(key):
            return key.replace(" + ", "-")
    return "other"


def render(text):
    lines = text.splitlines()
    title, intro, turns, cur = "", [], [], None
    for line in lines:
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
        foot = ""
        body_lines = t["lines"]
        if body_lines and re.fullmatch(r"\s*_.*_\s*", body_lines[-1] or ""):
            foot = '<div class="foot">%s</div>' % inline(body_lines[-1].strip().strip("_"))
            body_lines = body_lines[:-1]
        cls = speaker_class(who)
        parts.append(
            '<article class="msg %s"><header><span class="who">%s</span>%s'
            '<span class="step">%s</span><time>%s</time></header><div class="body">%s</div>%s</article>' % (
                cls, html.escape(who), (' <span class="to">→ %s</span>' % html.escape(to)) if to else "",
                html.escape(meta.get("step") or ""), html.escape(meta["when"]), blocks(body_lines), foot))
    return {"title": title, "intro": blocks(intro), "turns": "".join(parts), "count": len(turns)}


def duo_running():
    try:
        out = subprocess.run(["ps", "-axo", "command"], capture_output=True, text=True, timeout=3).stdout
    except Exception:
        return False
    return any("bridge.py duo" in l or "bridge duo" in l for l in out.splitlines())


PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Almond Duo</title>
<style>
:root{--bg:#f5f2eb;--panel:#fbf9f4;--ink:#2b2118;--muted:#6b5a4a;--line:#e3d9c8;--brown:#8b5a2b;
--claude:#f6e3cf;--claude-b:#b8672a;--codex:#e3edf7;--codex-b:#2f5a8a;--owner:#ece6dc;--owner-b:#6b5a4a;
--checks:#e4efe0;--checks-b:#4a7a3f;--both:#f3ecd9;--both-b:#8b5a2b}
@media (prefers-color-scheme:dark){:root{--bg:#1b1c20;--panel:#24211d;--ink:#f5deb3;--muted:#c9b48f;--line:#3d3328;
--brown:#d2a679;--claude:#3a2a1c;--claude-b:#e09a5f;--codex:#1c2a3a;--codex-b:#7fb0e6;--owner:#2c2824;--owner-b:#c9b48f;
--checks:#1f3020;--checks-b:#8cc47f;--both:#33291c;--both-b:#d2a679}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 "Atkinson Hyperlegible",system-ui,sans-serif}
.app{display:grid;grid-template-columns:260px 1fr;min-height:100vh}
@media (max-width:760px){.app{grid-template-columns:1fr}nav{border-right:0;border-bottom:1px solid var(--line)}}
nav{background:var(--panel);border-right:1px solid var(--line);padding:16px}
nav h1{font-size:18px;margin:0 0 4px}nav .sub{color:var(--muted);font-size:12.5px;margin-bottom:14px}
nav button{display:block;width:100%;text-align:left;background:none;border:1px solid transparent;border-radius:6px;
padding:8px 10px;margin:2px 0;color:var(--ink);font:inherit;cursor:pointer}
nav button:hover{border-color:var(--line)}nav button.on{background:var(--bg);border-color:var(--brown)}
nav .n{color:var(--muted);font-size:12px}
main{padding:16px;max-width:900px;width:100%}
.top{display:flex;flex-wrap:wrap;gap:10px;align-items:center;justify-content:space-between;margin-bottom:10px}
.top h2{margin:0;font-size:20px}.live{font-size:13px;padding:3px 10px;border-radius:12px;background:var(--line);color:var(--muted)}
.live.on{background:var(--checks);color:var(--checks-b)}.live.on::before{content:"● ";}
.intro{color:var(--muted);font-size:13.5px}
.msg{border-radius:10px;padding:10px 14px;margin:12px 0;border-left:4px solid var(--owner-b);background:var(--owner);max-width:92%}
.msg.claude{background:var(--claude);border-color:var(--claude-b)}
.msg.codex{background:var(--codex);border-color:var(--codex-b);margin-left:auto}
.msg.checks{background:var(--checks);border-color:var(--checks-b);margin-left:auto}
.msg.claude-codex{background:var(--both);border-color:var(--both-b)}
.msg header{display:flex;flex-wrap:wrap;gap:6px;align-items:baseline;font-size:13px;margin-bottom:4px}
.who{font-weight:bold;font-size:14px}.to{color:var(--muted)}.step{background:rgba(0,0,0,.06);padding:0 6px;border-radius:4px}
time{margin-left:auto;color:var(--muted);font-family:"DejaVu Sans Mono",ui-monospace,monospace;font-size:12px}
.body p{margin:4px 0}.body ul{margin:2px 0;padding-left:20px}.foot{color:var(--muted);font-size:12px;margin-top:6px}
code,pre{font-family:"DejaVu Sans Mono",ui-monospace,monospace;font-size:12.5px}
pre{white-space:pre-wrap;background:rgba(0,0,0,.05);padding:8px;border-radius:6px}
.tw{overflow-x:auto}table{border-collapse:collapse;font-size:13px;margin:4px 0}td,th{border:1px solid var(--line);padding:3px 7px;text-align:left}
.empty{color:var(--muted);margin-top:40px}a{color:var(--brown)}
</style></head><body><div class="app">
<nav><h1>Almond Duo</h1><div class="sub">Claude and Codex, talking through the Almond AI Bridge. Updates every 3 s.</div><div id="list"></div></nav>
<main><div class="top"><h2 id="title">…</h2><span id="live" class="live">idle</span></div>
<div id="intro" class="intro"></div><div id="turns"></div></main></div>
<script>
let current = new URLSearchParams(location.search).get("c"), stamp = "";
async function j(u){ const r = await fetch(u, {cache:"no-store"}); return r.json(); }
async function tick(){
  try {
    const l = await j("api/list");
    const live = document.getElementById("live");
    live.textContent = l.running ? "Claude and Codex are working" : "idle"; live.className = "live" + (l.running ? " on" : "");
    if (!current && l.items.length) current = l.items[0].name;
    document.getElementById("list").innerHTML = l.items.map(i =>
      `<button class="${i.name===current?"on":""}" data-n="${i.name}">${i.label}<br><span class="n">${i.turns} turns · ${i.updated}</span></button>`).join("")
      || '<p class="empty">No conversations yet.</p>';
    document.querySelectorAll("nav button").forEach(b => b.onclick = () => { current = b.dataset.n; stamp = ""; history.replaceState(null, "", "?c=" + current); tick(); });
    if (!current) return;
    const item = l.items.find(i => i.name === current); if (!item || item.mtime === stamp) return;
    const nearBottom = innerHeight + scrollY >= document.body.scrollHeight - 80;
    const c = await j("api/conv?name=" + encodeURIComponent(current));
    document.getElementById("title").textContent = c.title || current;
    document.getElementById("intro").innerHTML = c.intro;
    document.getElementById("turns").innerHTML = c.turns || '<p class="empty">No turns yet.</p>';
    if (nearBottom || !stamp) scrollTo(0, document.body.scrollHeight);
    stamp = item.mtime;
  } catch (e) { document.getElementById("live").textContent = "viewer offline"; }
}
tick(); setInterval(tick, 3000);
</script></body></html>"""


class Handler(BaseHTTPRequestHandler):
    conv_dir = DEFAULT_DIR

    def send(self, code, body, ctype):
        data = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        url = urlparse(self.path)
        if url.path in ("/", "/index.html"):
            return self.send(200, PAGE, "text/html; charset=utf-8")
        if url.path == "/api/list":
            items = []
            if os.path.isdir(self.conv_dir):
                for f in os.listdir(self.conv_dir):
                    if not f.endswith(".md"):
                        continue
                    p = os.path.join(self.conv_dir, f)
                    st = os.stat(p)
                    with open(p, encoding="utf-8", errors="replace") as fh:
                        text = fh.read()
                    first = next((l[2:] for l in text.splitlines() if l.startswith("# ")), f[:-3])
                    turns = sum(1 for l in text.splitlines() if l.startswith("## "))
                    items.append({"name": f, "label": html.escape(first), "turns": turns,
                                  "mtime": str(st.st_mtime_ns),
                                  "updated": __import__("time").strftime("%d %b %H:%M", __import__("time").localtime(st.st_mtime)),
                                  "_m": st.st_mtime})
            items.sort(key=lambda i: i["_m"], reverse=True)
            for i in items:
                i.pop("_m")
            return self.send(200, json.dumps({"items": items, "running": duo_running()}), "application/json")
        if url.path == "/api/conv":
            name = os.path.basename(parse_qs(url.query).get("name", [""])[0])
            p = os.path.join(self.conv_dir, name)
            if not name.endswith(".md") or not os.path.isfile(p):
                return self.send(404, json.dumps({"error": "not found"}), "application/json")
            with open(p, encoding="utf-8", errors="replace") as fh:
                return self.send(200, json.dumps(render(fh.read())), "application/json")
        self.send(404, "not found", "text/plain")

    def log_message(self, *a):
        pass


def main():
    ap = argparse.ArgumentParser(description="Live viewer for Almond Duo conversations")
    ap.add_argument("--port", type=int, default=4820)
    ap.add_argument("--dir", default=DEFAULT_DIR)
    args = ap.parse_args()
    Handler.conv_dir = os.path.abspath(args.dir)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print("Almond Duo viewer: http://127.0.0.1:%d  (conversations: %s)" % (args.port, Handler.conv_dir))
    sys.stdout.flush()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
