# -*- coding: utf-8 -*-
"""打包前自检：页面图、manifest、提纲链接、搜索索引。"""
import io
import json
import os
import re
import sys

BASE = r"F:\物理复习提纲合集"
APP = os.path.join(BASE, "程序", "resources", "app")
DATA = os.path.join(APP, "data")
RENDER = os.path.join(APP, "renderer")

problems = []


def check(cond, msg):
    if not cond:
        problems.append(msg)


qm = json.load(io.open(os.path.join(DATA, "manifest_qm.json"), encoding="utf-8"))
th = json.load(io.open(os.path.join(DATA, "manifest_thermo.json"), encoding="utf-8"))
docs = {}
for mf in (qm, th):
    for d in mf["docs"]:
        docs[d["id"]] = d

# 1. 页面图
for did, d in docs.items():
    folder = os.path.join(APP, d["pageDir"])
    check(os.path.isdir(folder), "缺少目录 " + d["pageDir"])
    if not os.path.isdir(folder):
        continue
    files = [f for f in os.listdir(folder) if not f.startswith(".")]
    check(len(files) == d["pages"], "%s 页数不符：%d/%d" % (did, len(files), d["pages"]))
    check(all(f.endswith(".webp") for f in files), did + " 存在非 webp 文件")
    check(not any(f.endswith(".jpg") for f in files), did + " 残留 jpg")

# 2. 卡片范围
for name, mf in (("qm", qm), ("thermo", th)):
    for c in mf["cards"]:
        if c.get("missing"):
            continue
        if c.get("doc"):
            d = docs.get(c["doc"])
            check(d is not None, "%s/%s 卡片文档不存在" % (name, c["id"]))
            if d:
                check(1 <= c["start"] <= c["end"] <= d["pages"],
                      "%s/%s 卡片页码越界 %s-%s" % (name, c["id"], c["start"], c["end"]))
        elif c.get("deck"):
            d = docs.get(c["deck"])
            check(d is not None, "%s/%s 卡片课件不存在" % (name, c["id"]))
            if d:
                check(1 <= c.get("deckStart", 1) <= c.get("deckEnd", 1) <= d["pages"],
                      "%s/%s 课件页码越界" % (name, c["id"]))
        if c.get("bookDoc"):
            d = docs.get(c["bookDoc"])
            check(d is not None, "%s/%s 教材不存在" % (name, c["id"]))
            if d:
                check(1 <= c["bookStart"] <= c["bookEnd"] <= d["pages"],
                      "%s/%s 教材页码越界 %s-%s" % (name, c["id"], c["bookStart"], c["bookEnd"]))

# 3. 提纲链接
for fn in ("outline_qm.html", "outline_thermo.html"):
    p = os.path.join(RENDER, fn)
    check(os.path.exists(p), "缺提纲 " + fn)
    if not os.path.exists(p):
        continue
    text = io.open(p, encoding="utf-8").read()
    for m in re.finditer(r'<a class="loc" data-doc="([^"]+)" data-page="(\d+)" data-end="(\d+)"', text):
        did, a, b = m.group(1), int(m.group(2)), int(m.group(3))
        d = docs.get(did)
        check(d is not None, "%s 链接指向未知文档 %s" % (fn, did))
        if d:
            check(1 <= a <= b <= d["pages"], "%s 链接越界 %s %d-%d" % (fn, did, a, b))

# 4. 搜索索引
p = os.path.join(DATA, "search_index.js")
check(os.path.exists(p), "缺 search_index.js")
if os.path.exists(p):
    txt = io.open(p, encoding="utf-8").read()
    try:
        data = json.loads(txt.split("=", 1)[1].strip().rstrip(";"))
        check(len(data) == len(qm["cards"]) + len(th["cards"]),
              "搜索索引条目数 %d != 卡片总数 %d" % (len(data), len(qm["cards"]) + len(th["cards"])))
        for e in data:
            if e["doc"]:
                d = docs.get(e["doc"])
                check(d is not None, "搜索索引文档不存在 " + e["doc"])
                if d:
                    check(1 <= e["start"] <= e["end"] <= d["pages"],
                          "搜索索引页码越界 %s" % e["id"])
            if e.get("bookDoc"):
                d = docs.get(e["bookDoc"])
                check(d is not None, "搜索索引教材不存在 " + e["bookDoc"])
                if d:
                    check(1 <= e["bookStart"] <= e["bookEnd"] <= d["pages"],
                          "搜索索引教材页码越界 %s" % e["id"])
    except Exception as exc:
        problems.append("search_index.js 解析失败: %s" % exc)

# 5. 单文件 HTML
for fn in ("量子力学复习提纲_第1-3章.html", "热力学统计物理_复习提纲_第1-3章.html"):
    check(os.path.exists(os.path.join(BASE, "HTML", fn)), "缺单文件 " + fn)

print("docs:", len(docs), "cards:", len(qm["cards"]) + len(th["cards"]))
print("pages:", sum(d["pages"] for d in docs.values()))
if problems:
    print("FAIL", len(problems))
    for p in problems:
        print(" -", p)
    sys.exit(1)
print("PASS 0 problems")
