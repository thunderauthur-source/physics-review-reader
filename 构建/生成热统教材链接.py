# -*- coding: utf-8 -*-
"""把热统教材接到提纲卡片：教材页链接 + 讲义页链接，并更新 manifest。"""
import io
import json
import os
import re

import fitz

BASE = r"F:\物理复习提纲合集\程序\resources\app"
DATA = os.path.join(BASE, "data")
RENDER = os.path.join(BASE, "renderer")
SRC = r"F:\workspace\热统复习提纲\交付\热力学统计物理_复习提纲_第1-3章.html"
DST = os.path.join(RENDER, "outline_thermo.html")

LECTURES = {
    "thermo-1": r"C:\Users\aaaa\Desktop\学习\热统\热统第一章-2026.pdf",
    "thermo-2": r"C:\Users\aaaa\Desktop\学习\热统\热统第二章.pdf",
    "thermo-3": r"C:\Users\aaaa\Desktop\学习\热统\热统第三章.pdf",
}
BOOK_OFFSET = 15
BOOK_PRINTED = {
    "1.1": (2, 3), "1.2": (4, 5), "1.3": (6, 10), "1.4": (11, 14), "1.5": (15, 16),
    "1.6": (17, 17), "1.7": (18, 19), "1.8": (20, 21), "1.9": (22, 23),
    "1.10": (24, 26), "1.11": (27, 27), "1.12": (28, 28), "1.13": (29, 30),
    "1.14": (31, 31), "1.15": (32, 33), "1.16": (34, 35), "1.17": (36, 36), "1.18": (37, 38),
    "2.1": (42, 42), "2.2": (43, 45), "2.3": (46, 48), "2.4": (49, 51), "2.5": (52, 53),
    "2.6": (54, 56), "2.7": (57, 58), "2.8": (59, 60),
    "3.0": (63, 63), "3.1": (63, 65), "3.2": (66, 67), "3.3": (68, 68), "3.4": (69, 72),
    "3.5": (73, 76), "3.6": (77, 79), "3.7": (80, 81), "3.8": (82, 82), "3.9": (83, 86),
}

# 讲义页眉映射
lecture = {}
for doc_id, path in LECTURES.items():
    pdf = fitz.open(path)
    for i in range(pdf.page_count):
        text = pdf[i].get_text().strip()
        first = text.split("\n")[0].strip() if text else ""
        m = re.match(r"^(\d+\.\d+)\s*(.*)$", first)
        if not m:
            continue
        sec = m.group(1)
        if sec not in lecture:
            lecture[sec] = {"doc": doc_id, "start": i + 1, "end": i + 1}
        else:
            lecture[sec]["end"] = i + 1
    pdf.close()

print("lecture sections", len(lecture), "book sections", len(BOOK_PRINTED))

# ---------- manifest ----------
mp = os.path.join(DATA, "manifest_thermo.json")
mf = json.load(io.open(mp, encoding="utf-8"))
mf["docs"] = [d for d in mf["docs"] if d["id"] != "thermo-book"]
mf["docs"].insert(0, {
    "id": "thermo-book",
    "kind": "book",
    "title": "教材 · 汪志诚《热力学·统计物理》（第六版）",
    "file": "",
    "pages": 340,
    "offset": BOOK_OFFSET,
    "pageDir": "docs/pages/thermo-book",
    "pagePattern": "p%04d.webp",
    "imgWidth": 1400,
})

for c in mf["cards"]:
    sec = re.sub(r"^§", "", c.get("label", "").split()[0]) if c.get("label") else ""
    # label 形如 "§1.1 标题"，上面取到 §1.1；再兜底用已有的 sec 字段
    sec = sec.replace("§", "")
    if not sec and c.get("sec"):
        sec = c["sec"]
    c.pop("bookDoc", None); c.pop("bookStart", None); c.pop("bookEnd", None); c.pop("bookPrinted", None)
    if sec in BOOK_PRINTED:
        a, b = BOOK_PRINTED[sec]
        c["bookDoc"] = "thermo-book"
        c["bookStart"] = a + BOOK_OFFSET
        c["bookEnd"] = b + BOOK_OFFSET
        c["bookPrinted"] = "%d–%d" % (a, b)

io.open(mp, "w", encoding="utf-8", newline="\n").write(json.dumps(mf, ensure_ascii=False, indent=1) + "\n")
print("manifest cards with book:", sum(1 for c in mf["cards"] if c.get("bookDoc")))

# ---------- 重新生成提纲 ----------
html = io.open(SRC, encoding="utf-8").read()
cards = {m.group(1): m.group(0) for m in re.finditer(r'<article class="card [^"]*" id="([^"]+)">[\s\S]*?</article>', html)}


def meta_for(cid):
    c = next(x for x in mf["cards"] if x["id"] == cid)
    parts = []
    if c.get("bookDoc"):
        parts.append('<a class="loc book" data-doc="thermo-book" data-page="%d" data-end="%d" '
                     'data-printed="%s" href="#" title="教材 pp.%s">教材 pp.%s</a>'
                     % (c["bookStart"], c["bookEnd"], c["bookPrinted"], c["bookPrinted"], c["bookPrinted"]))
    else:
        parts.append('<span class="meta-muted">教材未收录</span>')
    if c.get("doc"):
        parts.append('<a class="loc" data-doc="%s" data-page="%d" data-end="%d" data-printed="%s" '
                     'href="#" title="讲义 pp.%s">讲义 pp.%s</a>'
                     % (c["doc"], c["start"], c["end"], c.get("printed", ""), c.get("printed", ""), c.get("printed", "")))
    else:
        parts.append('<span class="meta-muted">讲义未含（补充材料）</span>')
    return '<div class="meta">' + '<span class="sep">·</span>'.join(parts) + '</div>'


def inject(m):
    block = m.group(0)
    cid = re.search(r'id="([^"]+)"', block).group(1)
    block = re.sub(r'<div class="meta">[\s\S]*?</div>', '', block, count=1)
    return re.sub(r'(<div class="chead"[\s\S]*?</div>)(\s*<div class="cbody">)',
                  r'\1' + meta_for(cid) + r'\2', block, count=1)


html2 = re.sub(r'<article class="card [^"]*" id="[^"]+">[\s\S]*?</article>', inject, html)

STYLE = """
<style>
  .card .meta { padding: 2px 18px 8px; color: #7a6b8e; font-size: 12px; }
  .card .meta a { color: inherit; text-decoration: none; border-bottom: 1px dashed currentColor; }
  .card .meta a.book { color: #0f6b5c; }
  .card .meta a:hover { color: #b83f7c; }
  .meta .sep { opacity: .45; margin: 0 5px; }
  .meta-muted { opacity: .6; }
  body.dark .card .meta { color: #a89bbd; }
  body.dark .card .meta a.book { color: #5fd3bd; }
</style>
"""

BRIDGE = r"""
<script>
(function () {
  function send(msg) { parent.postMessage(msg, '*'); }
  document.addEventListener('click', function (e) {
    var a = e.target.closest && e.target.closest('a.loc');
    if (!a) return;
    e.preventDefault();
    send({ type: 'open-doc', doc: a.dataset.doc, page: Number(a.dataset.page),
           end: Number(a.dataset.end) || 0, printed: a.dataset.printed || '' });
  }, true);
  window.addEventListener('message', function (e) {
    var d = e.data || {};
    if (d.type === 'reveal-card') {
      var el = document.getElementById(d.card);
      if (!el) return;
      if (el.classList.contains('closed')) el.classList.remove('closed');
      el.scrollIntoView({ behavior: 'smooth', block: 'center' });
      el.classList.add('flash');
      setTimeout(function () { el.classList.remove('flash'); }, 1800);
    }
    if (d.type === 'focus-search') {
      var q = document.getElementById('q') || document.getElementById('search');
      if (q) { q.focus(); q.select && q.select(); }
    }
    if (d.type === 'request-theme') {
      send({ type: 'theme', dark: document.body.classList.contains('dark') });
    }
  });
  new MutationObserver(function () {
    send({ type: 'theme', dark: document.body.classList.contains('dark') });
  }).observe(document.body, { attributes: true, attributeFilter: ['class'] });
})();
</script>
<style>
  .card.flash { outline: 3px solid #f0b429; outline-offset: -3px; }
</style>
"""

html2 = html2.replace("</head>", STYLE + "</head>", 1)
html2 = html2.replace("</body>", BRIDGE + "</body>", 1)
io.open(DST, "w", encoding="utf-8", newline="\n").write(html2)

# ---------- 合并 manifest JS ----------
qm = json.load(io.open(os.path.join(DATA, "manifest_qm.json"), encoding="utf-8"))
js = ("window.__MANIFESTS__ = window.__MANIFESTS__ || {};\n"
      "window.__MANIFESTS__.qm = " + json.dumps(qm, ensure_ascii=False) + ";\n"
      "window.__MANIFESTS__.thermo = " + json.dumps(mf, ensure_ascii=False) + ";\n"
      "window.__MANIFEST__ = window.__MANIFESTS__.qm;\n")
io.open(os.path.join(DATA, "manifest_qm.js"), "w", encoding="utf-8", newline="\n").write(js)
print("outline written", len(html2), "manifest js updated")
