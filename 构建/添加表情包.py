# -*- coding: utf-8 -*-
"""把大肥鱼表情包里的 GIF 转成适合阅读器使用的动画 WebP。

- 源目录：大肥鱼图片包/表情包
- 目标：程序/resources/app/renderer/mascot
- 统一 240x240、12 fps、质量 50，保留循环播放
- 生成 构建/表情包映射.json，供提纲 MASCOTS 列表使用
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "大肥鱼图片包" / "表情包"
DST = ROOT / "程序" / "resources" / "app" / "renderer" / "mascot"
MAP = ROOT / "构建" / "表情包映射.json"
FFMPEG = shutil.which("ffmpeg") or "ffmpeg"


def sort_key(p: Path):
    stem = p.stem
    m = re.match(r"EX(\d+)", stem)
    if m:
        return (0, int(m.group(1)))
    m = re.match(r"15N(\d+)", stem)
    if m:
        return (1, int(m.group(1)))
    m = re.match(r"16N(\d+)", stem)
    if m:
        return (2, int(m.group(1)))
    m = re.match(r"特殊(\d+)", stem)
    if m:
        return (3, int(m.group(1)))
    return (9, stem)


def make_id(p: Path) -> str:
    stem = p.stem
    m = re.match(r"EX(\d+)", stem)
    if m:
        return f"ex{int(m.group(1)):02d}"
    m = re.match(r"15N(\d+)", stem)
    if m:
        return f"n15_{int(m.group(1)):02d}"
    m = re.match(r"16N(\d+)", stem)
    if m:
        return f"n16_{int(m.group(1)):02d}"
    m = re.match(r"特殊(\d+)", stem)
    if m:
        return f"sp{int(m.group(1)):02d}"
    return re.sub(r"[^a-z0-9]+", "_", stem.lower()).strip("_")


def make_label(p: Path) -> str:
    stem = p.stem
    stem = re.sub(r"^(EX\d+|15N\d+|16N\d+|特殊\d+)_?", "", stem)
    stem = stem.replace("-", " ")
    stem = re.sub(r"(?<=[\u4e00-\u9fff])(\d+)$", r" \1", stem)
    return stem.strip() or p.stem


def main() -> None:
    gifs = sorted(SRC.glob("*.gif"), key=sort_key)
    DST.mkdir(parents=True, exist_ok=True)
    rows = []
    seen = {}
    for i, src in enumerate(gifs, 1):
        ident = make_id(src)
        if ident in seen:
            seen[ident] += 1
            ident = f"{ident}_{seen[ident]}"
        else:
            seen[ident] = 1
        out = DST / f"{ident}.webp"
        cmd = [
            FFMPEG, "-y", "-loglevel", "error", "-i", str(src),
            "-vf", "fps=12,scale=240:240:flags=lanczos",
            "-c:v", "libwebp_anim", "-lossless", "0", "-q:v", "50",
            "-loop", "0", "-an", str(out),
        ]
        subprocess.run(cmd, check=True)
        rows.append({
            "id": ident,
            "label": make_label(src),
            "file": out.name,
            "source": src.name,
            "bytes": out.stat().st_size,
        })
        print(f"[{i:02d}/{len(gifs)}] {src.name} -> {out.name} ({out.stat().st_size // 1024} KB)")

    MAP.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    total = sum(r["bytes"] for r in rows)
    print(f"converted {len(rows)} files, {total / 1024 / 1024:.1f} MB -> {MAP}")


if __name__ == "__main__":
    main()
