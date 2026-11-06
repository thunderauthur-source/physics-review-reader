# -*- coding: utf-8 -*-
"""Insert two formula/calculation slides into the edited hydrogen PPT.

Loads the current edited deck, preserves its existing slides, inserts two
slides after slide 2, renumbers the sections/page footers and refreshes notes.
Saves to a new file; the user's current deck is not overwritten.
"""
from __future__ import annotations

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

ROOT = Path(r"F:\物理复习提纲合集")
SRC = ROOT / "发布" / "氢原子电子云_汇报.pptx"
OUT = ROOT / "发布" / "氢原子电子云_汇报_公式版.pptx"

# match the existing deck
BG = RGBColor(0xF7, 0xFA, 0xF8)
INK = RGBColor(0x1B, 0x2D, 0x2B)
INK_SOFT = RGBColor(0x3F, 0x57, 0x53)
MUTED = RGBColor(0x6F, 0x85, 0x80)
TEAL = RGBColor(0x0D, 0x6B, 0x60)
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

FONT_CN = "Microsoft YaHei"
FONT_MATH = "Cambria Math"
FONT_CODE = "Consolas"
W, H = 13.333, 7.5


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
             line_spacing=1.0):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.auto_size = MSO_AUTO_SIZE.NONE
    tf.vertical_anchor = anchor
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.alignment = align
    p.line_spacing = line_spacing
    p.space_before = Pt(0)
    p.space_after = Pt(0)
    r = p.add_run()
    r.text = text
    set_font(r, font, size, color, bold, False)
    return box


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


def add_bg(slide):
    bg = slide.background.fill
    bg.solid()
    bg.fore_color.rgb = BG


def add_frame(slide, section, title, subtitle, page, footer):
    add_bg(slide)
    add_rect(slide, 0, 0, W, 0.055, TEAL)
    add_text(slide, 0.8, 0.34, 7.6, 0.25, section, 10.5, TEAL, True)
    add_text(slide, 0.8, 0.60, 11.7, 0.55, title, 27, INK, True, line_spacing=1.0)
    if subtitle:
        add_text(slide, 0.82, 1.18, 11.4, 0.28, subtitle, 11.3, MUTED, line_spacing=1.0)
    add_rect(slide, 0.8, 1.53, 11.73, 0.012, LINE)
    add_text(slide, 0.8, 7.14, 9.2, 0.18, footer, 8, MUTED)
    add_text(slide, 11.8, 7.14, 0.8, 0.18, page, 8.5, MUTED, align=PP_ALIGN.RIGHT)


def set_notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text


def replace_exact(slide, mapping):
    for sh in slide.shapes:
        if not sh.has_text_frame:
            continue
        for p in sh.text_frame.paragraphs:
            for r in p.runs:
                if r.text in mapping:
                    r.text = mapping[r.text]


# ---------- load and build new slides ----------
prs = Presentation(str(SRC))
old_slides = list(prs.slides)

# new slide A: formula sheet
s_formula = prs.slides.add_slide(prs.slide_layouts[6])
add_frame(
    s_formula,
    "02 · FORMULA",
    "公式：波函数、归一化与能量",
    "教材 §4.2 的归一化波函数与径向函数；取 a = a₀ = 0.529 Å。",
    "03 / 10",
    "教材 §4.2 · pp.96–104 · 式 (4.70)、(4.80)–(4.89) · 表 4.7",
)

# left dark formula card
add_rect(s_formula, 0.8, 1.66, 5.18, 4.40, DARK_2, None, 0.055)
add_text(s_formula, 1.02, 1.86, 4.7, 0.22, "NORMALIZED WAVEFUNCTION", 8.8, RGBColor(0x88, 0xD8, 0xC6), True)
add_text(s_formula, 1.02, 2.15, 4.75, 0.38,
         "ψₙₗₘ(r, θ, φ) = Rₙₗ(r) · Yₗᵐ(θ, φ)",
         15.5, WHITE, True, FONT_MATH, line_spacing=1.0)
add_text(s_formula, 1.02, 2.64, 4.72, 0.34,
         "∭ |ψₙₗₘ|² r² sinθ dr dθ dφ = 1",
         11.5, RGBColor(0xD7, 0xE8, 0xE3), False, FONT_MATH, line_spacing=1.0)
add_rect(s_formula, 1.02, 3.14, 4.58, 0.012, RGBColor(0x3A, 0x59, 0x59))
add_text(s_formula, 1.02, 3.28, 4.7, 0.34,
         "P(r) = r² |Rₙₗ(r)|²",
         18, RGBColor(0x8F, 0xE6, 0xD4), True, FONT_MATH, line_spacing=1.0)
add_text(s_formula, 1.02, 3.70, 4.65, 0.26,
         "径向概率密度；∫₀∞ P(r) dr = 1", 9.6, RGBColor(0xB2, 0xC9, 0xC3))
add_text(s_formula, 1.02, 4.46, 4.65, 0.32,
         "Eₙ = −13.6 eV / n²", 14.5, RGBColor(0xF2, 0xCF, 0x7F), False, FONT_MATH)
add_text(s_formula, 1.02, 4.84, 4.65, 0.28,
         "n = 1, 2, 3, …；能量只由 n 决定", 9.4, RGBColor(0x9D, 0xB9, 0xB2))
add_text(s_formula, 1.02, 5.46, 4.65, 0.28,
         "a = 0.529 Å；l, m 决定角向形状", 9.2, RGBColor(0x9D, 0xB9, 0xB2))

# right radial functions
add_text(s_formula, 6.28, 1.73, 6.0, 0.28, "前几个径向函数 Rₙₗ(r)（表 4.7）", 11.5, INK, True)
radials = [
    ("1s", "R₁₀ = 2 a^(−3/2) exp(−r/a)", TEAL, TEAL_LIGHT),
    ("2s", "R₂₀ = (1/√2) a^(−3/2) (1 − r/2a) exp(−r/2a)", TEAL, TEAL_LIGHT),
    ("2p", "R₂₁ = (1/(2√6)) a^(−3/2) (r/a) exp(−r/2a)", GOLD, GOLD_LIGHT),
    ("3d", "R₃₂ = (4/(81√30)) a^(−3/2) (r/a)² exp(−r/3a)", INDIGO, INDIGO_LIGHT),
]
for i, (lab, formula, color, light) in enumerate(radials):
    y = 2.06 + i * 0.86
    add_rect(s_formula, 6.28, y, 6.22, 0.74, WHITE, LINE, 0.08)
    add_rect(s_formula, 6.28, y, 0.055, 0.74, color)
    add_text(s_formula, 6.48, y + 0.21, 0.44, 0.25, lab, 11, color, True)
    add_text(s_formula, 6.98, y + 0.17, 5.34, 0.34, formula, 10.3, INK, False, FONT_MATH, line_spacing=1.0)

add_text(s_formula, 6.3, 5.57, 6.1, 0.22,
         "3d_z² 与 3d_xy 共用 R₃₂；归一化系数已包含在表中。",
         8.8, MUTED)

# angular-factor callout
add_rect(s_formula, 0.8, 6.20, 11.7, 0.55, GOLD_LIGHT, None, 0.10)
add_text(s_formula, 1.0, 6.31, 11.3, 0.30,
         "角向因子：1s、2s 球对称；2p_z ∝ cosθ；3d_z² ∝ 3cos²θ − 1；3d_xy ∝ sin²θ sin 2φ。",
         9.8, RGBColor(0x6C, 0x4A, 0x12), True)

# new slide B: why these five (n, l, m)
s_select = prs.slides.add_slide(prs.slide_layouts[6])
add_frame(
    s_select,
    "03 · SELECTION",
    "n、ℓ、m 怎么选出这五个图",
    "允许取值由边界条件给出；五个图是按 s/p/d、节点和取向挑出的代表。",
    "04 / 10",
    "教材 §4.2 · 量子数取值与五个代表的选择",
)

# left: allowed combinations
add_rect(s_select, 0.8, 1.66, 5.95, 4.35, WHITE, LINE, 0.055)
add_text(s_select, 1.0, 1.80, 5.5, 0.25,
         "允许值：n = 1,2,…；ℓ = 0,…,n−1；m = −ℓ,…,ℓ",
         9.8, INK, True)
tree = (
    "n=1   ℓ=0   m=0              → 1s\n"
    "n=2   ℓ=0   m=0              → 2s\n"
    "      ℓ=1   m=−1, 0, +1       → 2p\n"
    "n=3   ℓ=0   m=0              → 3s\n"
    "      ℓ=1   m=−1, 0, +1       → 3p\n"
    "      ℓ=2   m=−2 … +2         → 3d"
)
add_text(s_select, 1.0, 2.20, 5.55, 2.20, tree, 10.0, INK_SOFT, False, FONT_CODE, line_spacing=1.32)

# why these five, in one line of reasoning
add_rect(s_select, 1.0, 3.93, 5.53, 0.70, TEAL_LIGHT, None, 0.10)
add_text(s_select, 1.14, 4.02, 5.27, 0.24, "选择顺序", 8.2, TEAL, True)
add_text(s_select, 1.14, 4.25, 5.25, 0.28,
         "最低 n → 1s；同 ℓ=0 加 n → 2s；ℓ=1,m=0 → 2p_z；ℓ=2,m=0 或 |m|=2 → 3d 两个图。",
         7.6, INK_SOFT, line_spacing=1.0)

chips = [
    ("n → 能量 / 尺度", TEAL_LIGHT, TEAL),
    ("ℓ → 角节点 / 形状", INDIGO_LIGHT, INDIGO),
    ("m → 空间取向", GOLD_LIGHT, GOLD),
]
for i, (txt, light, color) in enumerate(chips):
    x = 1.0 + i * 1.78
    add_rect(s_select, x, 4.86, 1.66, 0.36, light, None, 0.18)
    add_text(s_select, x + 0.07, 4.94, 1.52, 0.20, txt, 8.2, color, True)

add_text(s_select, 1.0, 5.38, 5.55, 0.42,
         "n 来自径向边界；ℓ 来自角方程；\nm 来自 e^(imφ) 的 2π 周期性。",
         8.5, MUTED, line_spacing=1.2)

# right: five selected representatives
add_rect(s_select, 6.98, 1.66, 5.52, 4.35, WHITE, LINE, 0.055)
add_text(s_select, 7.18, 1.80, 5.1, 0.24, "五个代表（不是全部）", 10.6, INK, True)

selected = [
    ("1s", "(1,0,0)", "基态；无节点", TEAL),
    ("2s", "(2,0,0)", "径向节点 1", TEAL),
    ("2p_z", "(2,1,0)", "角节点 1；m=0", GOLD),
    ("3d_z²", "(3,2,0)", "角节点 2；m=0", INDIGO),
    ("3d_xy", "(3,2,±2)", "角节点 2；|m|=2 实组合", BLUE),
]
for i, (lab, nlm, why, color) in enumerate(selected):
    y = 2.08 + i * 0.74
    add_rect(s_select, 7.18, y, 5.12, 0.64, WHITE if i % 2 else RGBColor(0xF7, 0xFA, 0xF8), LINE, 0.10)
    add_rect(s_select, 7.18, y, 0.055, 0.64, color)
    add_text(s_select, 7.33, y + 0.18, 0.62, 0.24, lab, 10.2, color, True)
    add_text(s_select, 7.98, y + 0.18, 1.35, 0.24, nlm, 9.8, INK, False, FONT_MATH)
    add_text(s_select, 9.34, y + 0.19, 2.85, 0.22, why, 8.1, MUTED)

add_rect(s_select, 0.8, 6.13, 11.7, 0.58, GOLD_LIGHT, None, 0.10)
add_text(s_select, 1.0, 6.23, 11.28, 0.36,
         "先由 (n,ℓ,m) 的允许值确定 ψ，再按 s/p/d、径向节点、角节点和取向选五个代表；3d_xy 是 m=+2 与 −2 的实组合。",
         9.0, RGBColor(0x6C, 0x4A, 0x12), True, line_spacing=1.0)

# new slide C: most probable radius calculation
s_calc = prs.slides.add_slide(prs.slide_layouts[6])
add_frame(
    s_calc,
    "04 · CALCULATION",
    "最概然半径：从 P(r) 求极值",
    "P(r) = r²|Rₙₗ|²，令 dP/dr = 0；a = a₀ = 0.529 Å；2s 取更高的外峰。",
    "05 / 10",
    "教材 §4.2 · pp.96–104 · 表 4.7 · 径向概率与节点计算",
)

add_rect(s_calc, 0.8, 1.62, 11.7, 0.52, TEAL_LIGHT, None, 0.10)
add_text(s_calc, 1.0, 1.72, 11.2, 0.28,
         "P(r) = r² |Rₙₗ(r)|²       dP/dr = 0       ∫₀∞ P(r) dr = 1",
         13.2, TEAL, True, FONT_MATH, line_spacing=1.0)

# table
rows, cols = 5, 5
table_shape = s_calc.shapes.add_table(rows, cols, Inches(0.82), Inches(2.37), Inches(11.66), Inches(2.92))
table = table_shape.table
table.first_row = True
table.horz_banding = False
col_widths = [0.95, 3.05, 3.35, 2.35, 1.96]
for i, w in enumerate(col_widths):
    table.columns[i].width = Inches(w)
table.rows[0].height = Inches(0.47)
for i in range(1, rows):
    table.rows[i].height = Inches(0.61)

headers = ["轨道", "P(r) ∝", "极值方程", "最概然半径", "备注"]
body = [
    ("1s", "r² exp(−2r/a)", "2r − 2r²/a = 0", "a", "单峰"),
    ("2s", "r²(2 − r/a)² exp(−r/a)", "x² − 6x + 4 = 0，x = r/a", "5.236a（外峰）", "内峰 0.764a"),
    ("2p", "r⁴ exp(−r/a)", "4r³ − r⁴/a = 0", "4a", "单峰"),
    ("3d", "r⁶ exp(−2r/3a)", "6r⁵ − (2/(3a))r⁶ = 0", "9a", "3d_z² / 3d_xy 共用"),
]
for c, text in enumerate(headers):
    cell = table.cell(0, c)
    cell.fill.solid(); cell.fill.fore_color.rgb = TEAL
    cell.margin_left = Inches(0.07); cell.margin_right = Inches(0.05)
    cell.margin_top = Inches(0.03); cell.margin_bottom = Inches(0.03)
    cell.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf = cell.text_frame; tf.clear()
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.LEFT
    r = p.add_run(); r.text = text
    set_font(r, FONT_CN, 9.4, WHITE, True)

for ri, row in enumerate(body, 1):
    for ci, text in enumerate(row):
        cell = table.cell(ri, ci)
        cell.fill.solid()
        cell.fill.fore_color.rgb = WHITE if ri % 2 else RGBColor(0xF7, 0xFA, 0xF8)
        cell.margin_left = Inches(0.07); cell.margin_right = Inches(0.05)
        cell.margin_top = Inches(0.03); cell.margin_bottom = Inches(0.03)
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf = cell.text_frame; tf.clear()
        p = tf.paragraphs[0]; p.alignment = PP_ALIGN.LEFT
        r = p.add_run(); r.text = text
        font = FONT_MATH if ci in (1, 2) else FONT_CN
        size = 9.0 if ci in (1, 2) else (9.7 if ci != 3 else 9.4)
        set_font(r, font, size, INK if ci != 3 else TEAL, ci == 3)

# table notes
add_rect(s_calc, 0.82, 5.55, 11.66, 0.62, GOLD_LIGHT, None, 0.10)
add_text(s_calc, 1.0, 5.66, 11.25, 0.38,
         "所有方程都已约去正常数和 exp(−…)；只解 r 的多项式。2s 取更高的外峰 5.236a，内峰仅 0.764a。",
         9.6, RGBColor(0x6C, 0x4A, 0x12), True, line_spacing=1.0)

# small derivation callout
add_text(s_calc, 0.84, 6.35, 11.5, 0.28,
         "例（2p）：dP/dr ∝ (4r³ − r⁴/a) exp(−r/a) = 0  ⇒  r = 4a。",
         10.5, INK_SOFT, False, FONT_MATH)

# ---------- reorder: formula, selection, calculation after slide 2 ----------
sldIdLst = prs.slides._sldIdLst
ids = list(sldIdLst)
formula_id, select_id, calc_id = ids[-3], ids[-2], ids[-1]
for item in (formula_id, select_id, calc_id):
    sldIdLst.remove(item)
sldIdLst.insert(2, formula_id)
sldIdLst.insert(3, select_id)
sldIdLst.insert(4, calc_id)

# ---------- renumber old sections and page footers ----------
section_map = {
    "02 · OVERVIEW": "05 · OVERVIEW",
    "03 · METHOD": "06 · METHOD",
    "04 · CODE": "07 · CODE",
    "05 · STRUCTURE": "08 · STRUCTURE",
}
page_map = {
    "02 / 07": "02 / 10",
    "03 / 07": "06 / 10",
    "04 / 07": "07 / 10",
    "05 / 07": "08 / 10",
    "06 / 07": "09 / 10",
    "07 / 07": "10 / 10",
}
for slide in prs.slides:
    replace_exact(slide, section_map)
    replace_exact(slide, page_map)

# ---------- concise notes, total ~4:40 ----------
all_slides = list(prs.slides)
notes = [
    "【约 10 秒】各位老师、同学好。我汇报氢原子电子云，重点讲 |ψ|² 的概率密度、五个轨道的公式计算，以及这些图是怎么画出来的。",
    "【约 30 秒】电子云不是电子轨迹，而是 |ψ|²。氢原子波函数分解成径向部分 R 和角向部分 Y：n 决定能量和尺度，l 决定角节点数，m 决定空间取向。",
    "【约 35 秒】教材 §4.2 给出的归一化波函数是 ψ=R·Y，概率密度可以写成 P(r)=r²|R|²。右边是 1s、2s、2p、3d 的径向函数；能量只由 n 决定，Eₙ=−13.6/n² eV。",
    "【约 35 秒】n 来自径向边界，取 1、2、3…；l 来自角方程，取 0 到 n−1；m 来自 e^(imφ) 的 2π 周期性，取 −l 到 l。五个图不是全部，只是按 s/p/d、径向节点、角节点和取向挑出的代表。3d_xy 用 m=+2 与 −2 的实组合。",
    "【约 35 秒】最概然半径通过 P(r) 求极值得到。1s 在 a，2p 在 4a，3d 在 9a；2s 有两个峰，外峰 5.236a，内峰只有 0.764a，所以我们取外峰。",
    "【约 30 秒】五个轨道覆盖 s、p、d：1s 球对称，2s 有径向节点壳，2p_z 是双瓣，3d_z² 是双瓣加腰部环，3d_xy 是四瓣。",
    "【约 30 秒】画图分四步：选截面、在网格上逐点算 ψ、取模方得到 ρ、再用 gamma 和配色映射成图。这里画的是固定平面上的截面，不是沿视线积分。",
    "【约 25 秒】代码以 2p_z 为例：r 除以 a 无量纲化，cosθ 给出 xy 节面；rho=|ψ|²，最后用 gamma 调整亮暗。换掉波函数和截面，就能得到其余四个轨道。",
    "【约 30 秒】节点是电子云的骨架：2s 在 r=2a 有径向节点，3d_z² 有两个锥形角节点，3d_xy 有 x=0 和 y=0 两个节面。总节点数是 n−1。",
    "【约 20 秒】总结三句话：电子云是 |ψ|² 的概率密度；n、l、m 决定能量、节点和取向；画图就是截面、网格、模方和色调映射。谢谢。",
]
for slide, text in zip(all_slides, notes):
    set_notes(slide, text)

prs.core_properties.title = "氢原子电子云：从波函数到图像（公式版）"
prs.core_properties.subject = "量子力学课程汇报，3–5 分钟"
prs.core_properties.comments = "在用户修改版基础上插入公式、nlm 选择与最概然半径三页。"

OUT.parent.mkdir(parents=True, exist_ok=True)
prs.save(str(OUT))
print("saved", OUT, OUT.stat().st_size)
