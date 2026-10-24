# -*- coding: utf-8 -*-
"""从两份提纲生成全局搜索索引。"""
import html
import io
import json
import os
import re

BASE = r"F:\物理复习提纲合集\程序\resources\app"
DATA = os.path.join(BASE, "data")
RENDER = os.path.join(BASE, "renderer")

COURSES = {
    "qm": ("量子力学", "outline_qm.html", "manifest_qm.json"),
    "thermo": ("热力学统计物理", "outline_thermo.html", "manifest_thermo.json"),
}


def strip(s):
    s = re.sub(r"<(script|style)[\s\S]*?</\1>", " ", s, flags=re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    return re.sub(r"\s+", " ", s).strip()


index = []
for course, (title, outline, manifest_file) in COURSES.items():
    mf = json.load(io.open(os.path.join(DATA, manifest_file), encoding="utf-8"))
    cards = {c["id"]: c for c in mf["cards"]}
    text = io.open(os.path.join(RENDER, outline), encoding="utf-8").read()
    for m in re.finditer(r'<article class="card [^"]*" id="([^"]+)">([\s\S]*?)</article>', text):
        cid, inner = m.group(1), m.group(2)
        sec = re.search(r'<span class="secnum">([^<]*)</span>', inner)
        h3 = re.search(r"<h3>([\s\S]*?)</h3>", inner)
        sec_text = strip(sec.group(1)) if sec else ""
        head = strip(h3.group(1)) if h3 else ""
        body = strip(inner)
        body = body[len(sec_text) + len(head):] if body.startswith(sec_text + head) else body
        c = cards.get(cid, {})
        index.append({
            "course": course,
            "courseTitle": title,
            "id": cid,
            "sec": sec_text,
            "title": head,
            "text": body[:600],
            "doc": c.get("doc", ""),
            "start": c.get("start", 0),
            "end": c.get("end", 0),
            "printed": c.get("printed", ""),
            "bookDoc": c.get("bookDoc", ""),
            "bookStart": c.get("bookStart", 0),
            "bookEnd": c.get("bookEnd", 0),
            "bookPrinted": c.get("bookPrinted", ""),
            "deck": c.get("deck", ""),
            "missing": bool(c.get("missing")),
        })

js = "window.__SEARCH_INDEX__ = " + json.dumps(index, ensure_ascii=False) + ";\n"
io.open(os.path.join(DATA, "search_index.js"), "w", encoding="utf-8", newline="\n").write(js)
print("entries", len(index), "size", len(js))
for e in index[:3]:
    print(e["course"], e["sec"], e["title"][:30], e["doc"], e["start"])
