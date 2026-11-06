# -*- coding: utf-8 -*-
"""Build a 3–5 minute Chinese presentation on hydrogen electron clouds.

Run with the bundled python (python-pptx + Pillow are available):
    python 构建/生成氢原子汇报PPT.py
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
from pptx.util import Inches, Pt
from pptx.oxml.ns import qn

ROOT = Path(r"F:\物理复习提纲合集")
SRC = ROOT / "程序" / "resources" / "app" / "renderer" / "hydrogen"
ASSETS = ROOT / "构建" / "_ppt_hydrogen_assets"
OUT = ROOT / "发布" / "氢原子电子云_汇报.pptx"
ASSETS.mkdir(parents=True, exist_ok=True)

# ---------- palette ----------
BG = RGBColor(0xF7, 0xFA, 0xF8)
INK = RGBColor(0x1B, 0x2D, 0x2B)
INK_SOFT = RGBColor(0x3F, 0x57, 0x53)
MUTED = RGBColor(0x6F, 0x85, 0x80)
TEAL = RGBColor(0x0D, 0x6B, 0x60)
TEAL_DARK = RGBColor(0x08, 0x37, 0x35)
TEAL_LIGHT = RGBColor(0xDD, 0xF2, 0xEC)
GOLD = RGBColor(0xC2, 0x8A, 0x2E)
GOLD_LIGHT = RGBColor(0xFB, 0xF1, 0xDE)
INDIGO = RGBColor(0x5A, 0x4A, 0x9B)
INDIGO_LIGHT = RGBColor(0xEF, 0xEC, 0xFA)
BLUE = RGBColor(0x23, 0x6B, 0x9E)
BLUE_LIGHT = RGBColor(0xE8, 0xF4, 0xFB)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
DARK = RGBColor(0x0A, 0x14, 0x19)
DARK_2 = RGBColor(0x10, 0x23, 0x28)
LINE = RGBColor(0xD8, 0xE5, 0xE1)
CODE_BG = RGBColor(0x0A, 0x11, 0x1B)
CODE_HEAD = RGBColor(0x0E, 0x18, 0x25)
CODE_TEXT = RGBColor(0xD8, 0xE6, 0xF5)
CODE_COMMENT = RGBColor(0x71, 0x89, 0xA1)
CODE_KEYWORD = RGBColor(0xFF, 0x9C, 0xC7)
CODE_FUNC = RGBColor(0x7D, 0xD3, 0xFC)
CODE_NUM = RGBColor(0xF6, 0xC1, 0x77)

FONT_CN = "Microsoft YaHei"
FONT_SERIF = "Georgia"
FONT_MATH = "Cambria Math"
FONT_CODE = "Consolas"

W, H = 13.333, 7.5


# ---------- image / background assets ----------
def convert_images() -> None:
    for name in ("1s", "2s", "2pz", "3dz2", "3dxy"):
        im = Image.open(SRC / f"{name}.webp").convert("RGB")
        im.save(ASSETS / f"{name}.png", "PNG")
    # A slightly brighter 2s copy is used where the dark radial node is the point.
    s2 = Image.open(SRC / "2s.webp").convert("RGB")
    s2 = ImageEnhance.Brightness(s2).enhance(1.28)
    s2 = ImageEnhance.Contrast(s2).enhance(1.04)
    s2.save(ASSETS / "2s_bright.png", "PNG")


def make_title_bg() -> Path:
    w, h = 1920, 1080
    yy, xx = np.mgrid[0:h, 0:w]

    # diagonal three-stop gradient
    t = np.clip((xx / w) * 0.55 + (yy / h) * 0.45, 0, 1)
    stops = [(0.0, np.array([5, 16, 22])),
             (0.52, np.array([12, 48, 54])),
             (1.0, np.array([27, 24, 50]))]
    img = np.zeros((h, w, 3), dtype=np.float32)
    for (a, ca), (b, cb) in zip(stops, stops[1:]):
        m = (t >= a) & (t <= b)
        u = ((t[m] - a) / (b - a))[..., None]
        img[m] = ca * (1 - u) + cb * u

    # soft atmospheric glows
    glows = [
        (1500, 290, 410, np.array([45, 210, 182]), 0.20),
        (200, 1000, 560, np.array([64, 78, 170]), 0.16),
        (1180, 850, 430, np.array([185, 130, 55]), 0.08),
    ]
    for cx, cy, radius, color, amp in glows:
        g = np.exp(-(((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * radius ** 2))).astype(np.float32)
        img += color[None, None, :] * (g[..., None] * amp)

    # fine dot field
    rng = np.random.default_rng(12)
    for _ in range(90):
        x = int(rng.integers(0, w)); y = int(rng.integers(0, h))
        r = int(rng.integers(1, 3))
        a = float(rng.uniform(0.08, 0.22))
        col = np.array([160, 255, 235]) * a
        img[max(0, y - r):y + r + 1, max(0, x - r):x + r + 1] += col[None, None, :]

    # tilted concentric rings, kept very faint
    ring = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    rd = ImageDraw.Draw(ring)
    cx, cy = 1510, 370
    for rx, ry, alpha in [(590, 235, 16), (455, 180, 20), (330, 130, 16), (220, 86, 12)]:
        rd.ellipse([cx - rx, cy - ry, cx + rx, cy + ry],
                   outline=(150, 255, 237, alpha), width=2)
    ring = ring.rotate(-13, resample=Image.BICUBIC, center=(cx, cy))
    base = Image.fromarray(np.uint8(np.clip(img, 0, 255))).convert("RGBA")
    base = Image.alpha_composite(base, ring)

    # large ψ watermark at right
    mark = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    md = ImageDraw.Draw(mark)
    try:
        font = ImageFont.truetype(r"C:\Windows\Fonts\georgia.ttf", 520)
        md.text((1170, 180), "ψ", font=font, fill=(150, 255, 235, 15))
    except Exception:
        pass
    base = Image.alpha_composite(base, mark)

    # vignette
    arr = np.asarray(base.convert("RGB")).astype(np.float32)
    vx = (xx - w / 2) / (w / 2)
    vy = (yy - h / 2) / (h / 2)
    vig = np.clip(1.06 - 0.20 * (vx ** 2 + vy ** 2), 0, 1).astype(np.float32)
    arr *= vig[..., None]
    base = Image.fromarray(np.uint8(np.clip(arr, 0, 255))).convert("RGB")
    out = ASSETS / "title_bg.png"
    base.save(out, "PNG")
    return out


# ---------- pptx helpers ----------
def set_font(run, font=FONT_CN, size=14, color=INK, bold=False, italic=False, baseline=None):
    run.font.name = font
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    rpr = run._r.get_or_add_rPr()
    for tag in ("a:ea", "a:cs"):
        el = rpr.find(qn(tag))
        if el is None:
            el = rpr.makeelement(qn(tag), {})
            rpr.append(el)
        el.set("typeface", font)
    if baseline is not None:
        rpr.set("baseline", str(baseline))


def add_text(slide, x, y, w, h, text, size=14, color=INK, bold=False,
             font=FONT_CN, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP,
             line_spacing=1.0, margins=(0, 0, 0, 0), italic=False):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.auto_size = MSO_AUTO_SIZE.NONE
    tf.vertical_anchor = anchor
    tf.margin_left, tf.margin_right, tf.margin_top, tf.margin_bottom = [Inches(v) for v in margins]
    p = tf.paragraphs[0]
    p.alignment = align
    p.line_spacing = line_spacing
    p.space_before = Pt(0)
    p.space_after = Pt(0)
    r = p.add_run()
    r.text = text
    set_font(r, font, size, color, bold, italic)
    return box


def add_runs(slide, x, y, w, h, runs, align=PP_ALIGN.LEFT,
             anchor=MSO_ANCHOR.TOP, line_spacing=1.0, margins=(0, 0, 0, 0)):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.auto_size = MSO_AUTO_SIZE.NONE
    tf.vertical_anchor = anchor
    tf.margin_left, tf.margin_right, tf.margin_top, tf.margin_bottom = [Inches(v) for v in margins]
    p = tf.paragraphs[0]
    p.alignment = align
    p.line_spacing = line_spacing
    p.space_before = Pt(0)
    p.space_after = Pt(0)
    for item in runs:
        text, opts = item
        r = p.add_run()
        r.text = text
        set_font(r, opts.get("font", FONT_CN), opts.get("size", 14),
                 opts.get("color", INK), opts.get("bold", False), opts.get("italic", False),
                 opts.get("baseline"))
    return box


def add_orbital_label(slide, x, y, w, label, size=13.5, color=INK):
    """Orbital label with true subscripts: 2p_z, 3d_z², 3d_xy."""
    if label == "2p_z":
        parts = [("2p", {"size": size}), ("z", {"size": size * 0.68, "baseline": -25000})]
    elif label == "3d_z²":
        parts = [("3d", {"size": size}),
                 ("z", {"size": size * 0.68, "baseline": -25000}),
                 ("²", {"size": size * 0.78})]
    elif label == "3d_xy":
        parts = [("3d", {"size": size}),
                 ("xy", {"size": size * 0.68, "baseline": -25000})]
    else:
        parts = [(label, {"size": size})]
    for text, opts in parts:
        opts.setdefault("color", color)
        opts.setdefault("bold", True)
    add_runs(slide, x, y, w, 0.30, parts, line_spacing=1.0)
    return parts


def add_rect(slide, x, y, w, h, fill, line=None, radius=None, line_width=0.75):
    shape_type = MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE
    shp = slide.shapes.add_shape(shape_type, Inches(x), Inches(y), Inches(w), Inches(h))
    if radius:
        try:
            shp.adjustments[0] = radius
        except Exception:
            pass
    shp.fill.solid()
    shp.fill.fore_color.rgb = fill
    if line is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = line
        shp.line.width = Pt(line_width)
    shp.shadow.inherit = False
    return shp


def add_picture(slide, path, x, y, w, h, border=LINE, alt=""):
    pic = slide.shapes.add_picture(str(path), Inches(x), Inches(y), Inches(w), Inches(h))
    try:
        pic.line.color.rgb = border
        pic.line.width = Pt(0.75)
    except Exception:
        pass
    if alt:
        try:
            pic._element.nvPicPr.cNvPr.set("descr", alt)
        except Exception:
            pass
    return pic


def add_circle_num(slide, x, y, d, text, fill, color, size=13):
    shp = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x), Inches(y), Inches(d), Inches(d))
    shp.fill.solid(); shp.fill.fore_color.rgb = fill
    shp.line.fill.background(); shp.shadow.inherit = False
    tf = shp.text_frame
    tf.clear(); tf.margin_left = 0; tf.margin_right = 0; tf.margin_top = 0; tf.margin_bottom = 0
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = text
    set_font(r, FONT_CN, size, color, True)
    return shp


def add_bg(slide, color=BG):
    bg = slide.background.fill
    bg.solid()
    bg.fore_color.rgb = color


def content_slide(prs, section, title, subtitle="", page=None):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_bg(slide)
    add_rect(slide, 0, 0, W, 0.055, TEAL)
    add_text(slide, 0.8, 0.34, 7.6, 0.25, section, 10.5, TEAL, True, line_spacing=1.0)
    add_text(slide, 0.8, 0.60, 11.7, 0.55, title, 28, INK, True, line_spacing=1.0)
    if subtitle:
        add_text(slide, 0.82, 1.18, 11.4, 0.28, subtitle, 11.5, MUTED, line_spacing=1.0)
    add_rect(slide, 0.8, 1.53, 11.73, 0.012, LINE)
    # footer
    add_text(slide, 0.8, 7.14, 8.8, 0.18, "Griffiths §4.2 · 图像由归一化氢原子波函数数值计算", 8, MUTED)
    if page:
        add_text(slide, 11.8, 7.14, 0.8, 0.18, page, 8.5, MUTED, align=PP_ALIGN.RIGHT)
    return slide


def add_notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text


# ---------- build ----------
convert_images()
title_bg = make_title_bg()

prs = Presentation()
prs.slide_width = Inches(W)
prs.slide_height = Inches(H)
prs.core_properties.title = "氢原子电子云：从波函数到图像"
prs.core_properties.subject = "量子力学课程汇报，3–5 分钟"
prs.core_properties.author = ""
prs.core_properties.comments = "五张氢原子 |ψ|² 截面图、量子数、节点与绘图流程。"

# ===== slide 1: title =====
s = prs.slides.add_slide(prs.slide_layouts[6])
s.shapes.add_picture(str(title_bg), 0, 0, width=prs.slide_width, height=prs.slide_height)
add_text(s, 0.86, 0.55, 7.5, 0.25, "量子力学 · 课程汇报", 12.5, RGBColor(0xA9, 0xEF, 0xDD), True)
add_text(s, 0.86, 0.98, 8.0, 0.24, "HYDROGEN ATOM · ELECTRON CLOUD", 9.5, RGBColor(0xD9, 0xC5, 0x93), True)
add_text(s, 0.86, 1.55, 8.4, 0.9, "氢原子电子云", 46, WHITE, True, FONT_SERIF, line_spacing=1.0)
add_text(s, 0.88, 2.67, 8.4, 0.45,
         "从波函数 |ψ|² 到五个轨道的截面图", 20, RGBColor(0xDC, 0xEC, 0xE8), False, line_spacing=1.0)
add_rect(s, 0.9, 3.38, 1.35, 0.045, GOLD)
add_text(s, 0.9, 6.48, 5.6, 0.28, "3–5 分钟 · 原理与绘图流程", 12, RGBColor(0xA7, 0xC3, 0xBC))
add_text(s, 11.0, 6.48, 1.5, 0.28, "2026.11", 12, RGBColor(0xA7, 0xC3, 0xBC), align=PP_ALIGN.RIGHT)
add_notes(s, """【约 15 秒】
各位老师、同学好。我汇报的是氢原子电子云。重点讲两件事：电子云的概率密度原理，以及这五张图是怎么用氢原子波函数画出来的。大约四分钟。""")

# ===== slide 2: principle =====
s = content_slide(prs, "01 · PRINCIPLE", "电子云是概率密度，不是电子轨迹",
                  "氢原子定态由三个量子数标记；波函数先分离，再取模方。", "02 / 07")

# left dark formula card
add_rect(s, 0.8, 1.68, 5.35, 4.52, DARK_2, None, 0.055)
add_text(s, 1.02, 1.88, 4.9, 0.24, "HYDROGEN WAVEFUNCTION", 9.1, RGBColor(0x88, 0xD8, 0xC6), True)
add_text(s, 1.02, 2.22, 4.9, 0.5,
         "ψₙₗₘ(r, θ, φ)", 23, WHITE, True, FONT_MATH, line_spacing=1.0)
add_text(s, 1.02, 2.72, 4.9, 0.34,
         "= Rₙₗ(r) · Yₗᵐ(θ, φ)", 18, RGBColor(0xBF, 0xE3, 0xDC), False, FONT_MATH, line_spacing=1.0)
add_rect(s, 1.02, 3.22, 4.75, 0.012, RGBColor(0x3A, 0x59, 0x59))
add_text(s, 1.02, 3.40, 4.85, 0.7,
         "P = |ψₙₗₘ|²", 31, RGBColor(0x8F, 0xE6, 0xD4), True, FONT_MATH, line_spacing=1.0)
add_text(s, 1.02, 4.13, 4.75, 0.28, "概率密度：亮的地方，电子出现的概率密度高", 10.5, RGBColor(0xB2, 0xC9, 0xC3))
add_text(s, 1.02, 5.02, 4.6, 0.32,
         "Eₙ = −13.6 eV / n²", 14, RGBColor(0xF2, 0xCF, 0x7F), False, FONT_MATH)
add_text(s, 1.02, 5.44, 4.6, 0.28, "n = 1, 2, 3, …；能量只由 n 决定", 10, RGBColor(0x9D, 0xB9, 0xB2))

# right quantum number cards
rows = [
    ("n", "主量子数", "决定能量与轨道尺度", TEAL, TEAL_LIGHT),
    ("ℓ", "角量子数", "决定角节点数：ℓ 个", INDIGO, INDIGO_LIGHT),
    ("m", "磁量子数", "决定空间取向；−ℓ … +ℓ", GOLD, GOLD_LIGHT),
]
for i, (letter, name, desc, color, light) in enumerate(rows):
    y = 1.68 + i * 1.28
    add_rect(s, 6.55, y, 5.95, 1.10, WHITE, LINE, 0.08)
    add_circle_num(s, 6.75, y + 0.27, 0.54, letter, light, color, 18)
    add_text(s, 7.47, y + 0.17, 4.7, 0.30, name, 13.5, INK, True)
    add_text(s, 7.47, y + 0.53, 4.8, 0.28, desc, 10.5, MUTED)

add_text(s, 6.58, 5.66, 5.9, 0.28,
         "同一套 |ψ|²，不同 (n, l, m) → 不同节点与形状",
         10.5, INK_SOFT, line_spacing=1.0)
add_rect(s, 0.8, 6.35, 11.7, 0.48, GOLD_LIGHT, None, 0.10)
add_text(s, 1.0, 6.45, 11.3, 0.26,
         "本页所有图像都是二维截面：固定一个平面，画该平面上的概率密度。",
         10.5, RGBColor(0x6C, 0x4A, 0x12), True)

add_notes(s, """【约 40 秒】
电子云不是电子绕核运动的轨迹。氢原子定态由 n、l、m 三个量子数标记，波函数分解成径向部分 R 和球谐函数 Y。我们画的是它的模方 |ψ|²，也就是概率密度。
n 主要决定能量和尺度，l 决定角节点数，m 决定空间取向。后面五张图，本质上就是在不同的 n、l、m 下取 |ψ|²。""")

# ===== slide 3: five orbitals =====
s = content_slide(prs, "02 · OVERVIEW", "五个代表性轨道",
                  "1s → 3d：球、节点壳、双瓣、环与四瓣。", "03 / 07")
items = [
    ("1s", "1s", "球对称 · 无节点", TEAL),
    ("2s", "2s", "径向节点 r = 2a₀", TEAL),
    ("2pz", "2p_z", "双瓣 · xy 节面", GOLD),
    ("3dz2", "3d_z²", "双瓣 + 腰部环", INDIGO),
    ("3dxy", "3d_xy", "xy 平面四瓣", BLUE),
]
positions = [0.8, 3.08, 5.36, 7.64, 9.92]
for (key, label, desc, color), x in zip(items, positions):
    add_rect(s, x, 1.84, 2.05, 0.045, color)
    add_picture(s, ASSETS / f"{key}.png", x, 1.92, 2.05, 2.05, border=LINE,
                alt=f"{label} 氢原子电子云截面")
    add_orbital_label(s, x, 4.06, 2.05, label, 13.5)
    add_text(s, x, 4.36, 2.05, 0.42, desc, 9.2, MUTED, line_spacing=1.03)

add_rect(s, 0.8, 5.18, 11.7, 0.78, WHITE, LINE, 0.08)
add_text(s, 1.0, 5.31, 11.25, 0.48,
         "s：球对称    ·    p：双瓣    ·    d：四瓣或“双瓣 + 环”。形状差异，来自角向波函数。",
         12, INK_SOFT, line_spacing=1.05)
add_text(s, 0.82, 6.24, 11.2, 0.24,
         "每个轨道独立归一化亮度；尺寸看左下角标尺。",
         9.5, MUTED)
add_notes(s, """【约 45 秒】
我选了五个轨道：1s、2s、2p_z、3d_z²、3d_xy。
1s 是球对称基态，没有节点；2s 多了一个径向节点，所以看起来像“亮核 + 外壳”；2p_z 是沿 z 轴的双瓣，xy 平面是节面；3d_z² 是两极两瓣加腰部一个环；3d_xy 是 xy 平面上的四瓣。
这五张图覆盖了 s、p、d 三种典型形状。""")

# ===== slide 4: method =====
s = content_slide(prs, "03 · METHOD", "怎么把波函数变成一张图",
                  "选截面 → 算 ψ → 取模方 → 归一化与上色。", "04 / 07")
add_text(s, 0.8, 1.60, 6.2, 0.35,
         "ρ(x, z) = |ψₙₗₘ(x, 0, z)|²", 17, TEAL, True, FONT_MATH)
steps = [
    ("01", "选截面", "xz 取 y=0；xy 取 z=0；1000×1000 网格"),
    ("02", "逐点算 ψ", "代入径向函数与球谐函数"),
    ("03", "取模方", "ρ = |ψ|²；再除以 ρmax 归一化"),
    ("04", "映射成图", "I = (ρ/ρmax)^γ；配色、等高线、标尺"),
]
for i, (num, head, desc) in enumerate(steps):
    y = 2.10 + i * 0.90
    add_rect(s, 0.8, y, 6.25, 0.76, WHITE, LINE, 0.06)
    add_circle_num(s, 0.96, y + 0.16, 0.42, num, TEAL_LIGHT, TEAL, 9.5)
    add_text(s, 1.53, y + 0.08, 5.2, 0.27, head, 12.5, INK, True)
    add_text(s, 1.53, y + 0.38, 5.2, 0.26, desc, 9.8, MUTED)

add_picture(s, ASSETS / "2s_bright.png", 7.58, 1.60, 4.62, 4.62, border=LINE,
            alt="2s 电子云截面，标注径向节点")
add_text(s, 7.6, 6.26, 4.6, 0.24, "2s · x–z 截面  ·  暗环 = 径向节点 r = 2a₀", 9.4, MUTED)
add_rect(s, 0.8, 6.54, 11.7, 0.35, GOLD_LIGHT, None, 0.16)
add_text(s, 1.0, 6.59, 11.3, 0.24,
         "关键：画的是固定平面上的 |ψ|²，不是沿视线把三维密度积分掉。",
         10.3, RGBColor(0x6C, 0x4A, 0x12), True)
add_notes(s, """【约 50 秒】
画图分四步。
第一，选一个截面：大多数轨道取 x–z 平面，也就是 y=0；3d_xy 取 x–y 平面。
第二，在 1000×1000 的网格上逐点算波函数 ψ。
第三，取模方得到概率密度 ρ，再除以最大值做归一化。
第四，用 gamma 压缩动态范围，配色，加等高线和标尺。
注意：这是截面，不是沿视线积分。所以 3d_z² 的环在截面上会看起来像左右两个小瓣。""")

# ===== slide 5: code =====
s = content_slide(prs, "04 · CODE", "核心代码：波函数 → 模方 → 亮度",
                  "以 2p_z 为例，换掉 ψ 和截面，就能得到其余轨道。", "05 / 07")

# code panel
add_rect(s, 0.8, 1.62, 7.35, 5.0, CODE_BG, None, 0.055)
add_rect(s, 0.8, 1.62, 7.35, 0.42, CODE_HEAD, None, 0.055)
for i, c in enumerate([RGBColor(0xE8, 0x6C, 0x6C), RGBColor(0xF0, 0xC0, 0x5A), RGBColor(0x63, 0xC6, 0x9A)]):
    d = 0.10
    add_rect(s, 1.0 + i * 0.18, 1.77, d, d, c, None, 0.5)
add_text(s, 1.72, 1.71, 5.4, 0.22, "psi_2pz.py", 9.4, RGBColor(0x9F, 0xB5, 0xC9), False, FONT_CODE)
add_text(s, 7.35, 1.71, 0.65, 0.22, "NumPy", 8.6, RGBColor(0x6F, 0x8A, 0x9E), False, FONT_CODE, align=PP_ALIGN.RIGHT)

code_lines = [
    "def psi_2pz(r, theta):",
    "    x = r / A0",
    "    return (x * np.exp(-x / 2) * np.cos(theta)",
    "            / (4 * np.sqrt(2 * np.pi) * A0**1.5))",
    "",
    "# x-z 截面：y = 0",
    "R = np.hypot(X, Z)",
    "THETA = np.arccos(Z / R)",
    "",
    "rho = np.abs(psi_2pz(R, THETA))**2",
    "img = (rho / rho.max()) ** gamma",
]
code_box = s.shapes.add_textbox(Inches(1.0), Inches(2.22), Inches(6.9), Inches(4.1))
tf = code_box.text_frame
tf.clear(); tf.word_wrap = True; tf.auto_size = MSO_AUTO_SIZE.NONE
tf.margin_left = 0; tf.margin_right = 0; tf.margin_top = 0; tf.margin_bottom = 0
for idx, line in enumerate(code_lines):
    p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
    p.line_spacing = 1.12
    p.space_before = Pt(0); p.space_after = Pt(0)
    if line.startswith("#"):
        r = p.add_run(); r.text = line
        set_font(r, FONT_CODE, 12.3, CODE_COMMENT)
    else:
        parts = re.split(r"(#.*$|\b(?:def|return|import|as|in)\b|\b\d+(?:\.\d+)?\b|\b(?:np\.\w+|psi_\w+)\b)", line)
        for part in parts:
            if not part:
                continue
            color = CODE_TEXT
            if part.startswith("#"):
                color = CODE_COMMENT
            elif re.fullmatch(r"\b(?:def|return|import|as|in)\b", part):
                color = CODE_KEYWORD
            elif re.fullmatch(r"\d+(?:\.\d+)?", part):
                color = CODE_NUM
            elif re.fullmatch(r"np\.\w+|psi_\w+", part):
                color = CODE_FUNC
            r = p.add_run(); r.text = part
            set_font(r, FONT_CODE, 12.3, color)

add_text(s, 5.95, 4.46, 1.8, 0.18, "OUTPUT · 2p_z", 7.2, RGBColor(0x6F, 0x8A, 0x9E), False, FONT_CODE)
add_picture(s, ASSETS / "2pz.png", 5.95, 4.67, 1.55, 1.55,
            border=RGBColor(0x2A, 0x40, 0x54), alt="2p_z 代码输出示意图")
add_text(s, 5.95, 6.26, 1.7, 0.16, "生成的 |ψ|² 截面", 7.2, RGBColor(0x6F, 0x8A, 0x9E), False, FONT_CODE)

annotations = [
    ("r / A0", "无量纲化", "让公式里的长度以 a₀ 为单位"),
    ("cos θ", "角向因子", "在 xy 平面为零，形成节面"),
    ("|ψ|²", "概率密度", "亮暗表示电子出现的概率"),
    ("gamma", "显示参数", "压缩动态范围，照亮外层"),
]
for i, (code, head, desc) in enumerate(annotations):
    y = 1.62 + i * 1.06
    add_rect(s, 8.55, y, 3.95, 0.90, WHITE, LINE, 0.08)
    add_text(s, 8.73, y + 0.12, 1.6, 0.26, code, 11, TEAL, True, FONT_CODE)
    add_text(s, 10.25, y + 0.12, 2.05, 0.26, head, 10, INK, True)
    add_text(s, 8.74, y + 0.48, 3.5, 0.25, desc, 8.6, MUTED)

add_rect(s, 8.55, 5.95, 3.95, 0.62, GOLD_LIGHT, None, 0.12)
add_text(s, 8.73, 6.06, 3.6, 0.38,
         "换 ψ 和截面，就能画出其余四个轨道。",
         10.2, RGBColor(0x6C, 0x4A, 0x12), True, line_spacing=1.0)
add_notes(s, """【约 40 秒】
代码核心就这几行。以 2p_z 为例：r 除以 a₀ 做无量纲化，cosθ 给出 xy 节面；取模方得到 rho，再除以最大值，用 gamma 上色。
换掉 psi 函数和截面，就能得到其他四个轨道。完整渲染器还包含配色、等高线和标尺。""")

# ===== slide 6: nodes =====
s = content_slide(prs, "05 · STRUCTURE", "节点决定电子云的“骨架”",
                  "暗线、暗环不是画错，而是 |ψ|² = 0 的位置。", "06 / 07")
nodes = [
    ("2s_bright.png", "2s", "r = 2a₀ 的径向节点", "亮核与外壳之间的暗环", TEAL),
    ("3dz2.png", "3d_z²", "两个锥形角节点", "腰部环在截面上被切成两瓣", INDIGO),
    ("3dxy.png", "3d_xy", "x = 0 与 y = 0 两个节面", "xy 平面内的四瓣结构", BLUE),
]
positions = [0.85, 4.68, 8.51]
for (file, label, l1, l2, color), x in zip(nodes, positions):
    add_picture(s, ASSETS / file, x, 1.60, 3.35, 3.35, border=LINE,
                alt=f"{label} 电子云截面与节点")
    add_rect(s, x, 1.55, 3.35, 0.045, color)
    add_orbital_label(s, x, 5.01, 3.35, label, 14)
    add_text(s, x, 5.30, 3.35, 0.26, l1, 10.0, INK_SOFT, True)
    add_text(s, x, 5.57, 3.35, 0.26, l2, 8.8, MUTED)

add_rect(s, 0.8, 5.98, 11.7, 0.66, WHITE, LINE, 0.08)
add_text(s, 1.0, 6.09, 11.25, 0.42,
         "总节点数  n − 1  =  径向节点 (n − ℓ − 1)  +  角节点 (ℓ)",
         14.2, TEAL, True, FONT_MATH, line_spacing=1.0)
add_notes(s, """【约 35 秒】
节点是电子云的骨架。
2s 的暗环是 r = 2a₀ 的径向节点；
3d_z² 有两个锥形角节点，中间那个环在截面上被切成左右两个小瓣；
3d_xy 的 x=0 和 y=0 两个平面是节面，把电子云分成四瓣。
规律是：总节点数 n−1，径向节点 n−ℓ−1，角节点 ℓ。""")

# ===== slide 7: summary =====
s = prs.slides.add_slide(prs.slide_layouts[6])
s.shapes.add_picture(str(title_bg), 0, 0, width=prs.slide_width, height=prs.slide_height)
add_text(s, 0.86, 0.55, 7.5, 0.25, "TAKEAWAYS", 10.5, RGBColor(0xA9, 0xEF, 0xDD), True)
add_text(s, 0.86, 1.18, 7.4, 0.70, "把波函数变成图像", 34, WHITE, True, FONT_SERIF)
add_text(s, 0.88, 1.92, 7.4, 0.30, "一张电子云图的四件事", 12, RGBColor(0xC9, 0xDD, 0xD8))

summary = [
    ("1", "电子云 = |ψ|² 的概率密度", "不是电子运动的轨迹"),
    ("2", "n 定能量，ℓ 定角节点，m 定取向", "五个轨道只是不同的量子数组合"),
    ("3", "截面 + 网格 + 模方 + 色调映射", "先算密度，再把密度翻译成亮度和颜色"),
]
for i, (num, head, desc) in enumerate(summary):
    y = 2.55 + i * 1.05
    add_circle_num(s, 0.9, y, 0.46, num, RGBColor(0x27, 0x5A, 0x56), RGBColor(0xF2, 0xCF, 0x7F), 10)
    add_text(s, 1.55, y - 0.04, 6.9, 0.32, head, 17, WHITE, True)
    add_text(s, 1.57, y + 0.34, 6.8, 0.26, desc, 9.8, RGBColor(0xBE, 0xD0, 0xCB))

add_picture(s, ASSETS / "3dxy.png", 8.82, 1.55, 3.62, 3.62, border=RGBColor(0x5D, 0x7C, 0x77),
            alt="3d_xy 电子云四瓣截面")
add_runs(s, 8.84, 5.27, 3.6, 0.24, [
    ("3d", {"size": 9.5, "color": RGBColor(0xC9, 0xDD, 0xD8)}),
    ("xy", {"size": 7.0, "baseline": -25000, "color": RGBColor(0xC9, 0xDD, 0xD8)}),
    (" · xy 平面四瓣", {"size": 9.5, "color": RGBColor(0xC9, 0xDD, 0xD8)}),
], line_spacing=1.0)
add_text(s, 0.9, 6.15, 5.4, 0.40, "谢谢 / Q&A", 23, WHITE, True, FONT_SERIF)
add_text(s, 0.92, 6.62, 8.4, 0.24,
         "完整五轨道图、代码版与 PDF 已放入量子力学提纲。",
         9.5, RGBColor(0xA7, 0xC3, 0xBC))
add_text(s, 11.8, 7.14, 0.8, 0.18, "07 / 07", 8.5, RGBColor(0x8F, 0xAB, 0xA4), align=PP_ALIGN.RIGHT)
add_notes(s, """【约 25 秒】
最后总结三句话：
第一，电子云是 |ψ|² 的概率密度，不是轨迹；
第二，n 决定能量，l 决定角节点，m 决定取向；
第三，画图就是选截面、建网格、取模方、做色调映射。
谢谢，欢迎提问。""")

# ensure notes / save
OUT.parent.mkdir(parents=True, exist_ok=True)
prs.save(str(OUT))
print("saved", OUT, OUT.stat().st_size)
