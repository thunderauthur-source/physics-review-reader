# -*- coding: utf-8 -*-
"""Render and insert the new chapters from 添加热统第467章.py."""
from pathlib import Path
import importlib.util
import html

BASE = Path(r"F:\物理复习提纲合集")
SRC = BASE / "程序/resources/app/renderer/outline_thermo.html"
COPIES = [BASE / "docs/app/renderer/outline_thermo.html",
          BASE / "发布/网页版/app/renderer/outline_thermo.html"]

sname = BASE / "构建/添加热统第467章.py"
spec = importlib.util.spec_from_file_location("thermo467", sname)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
CARDS, CHAPTERS = mod.CARDS, mod.CHAPTERS


def render_card(c):
    cls = {"4": "c1", "6": "c2", "7": "c3"}[c["ch"]]
    deck_label = "课件 " + c["deck"].split("-")[-1]
    fig_html = ""
    if c.get("fig"):
        page = c["fig"]
        fig_html = f'''
        <figure class="qfig">
          <img src="../docs/pages/{c["deck"]}/p{page:04d}.webp" alt="{html.escape(c["title"])} 课件图">
          <figcaption>{c["figcap"]} <a class="loc" data-doc="{c["deck"]}" data-page="{page}" data-end="{page}" data-printed="{page}" href="#" title="{deck_label} 第 {page} 页">{deck_label} p{page:02d}</a></figcaption>
        </figure>'''
    steps = []
    for t, b, w in c["steps"]:
        why = f'<p class="step-why"><b>依据：</b>{w}</p>' if w else ""
        steps.append(f'''
          <li class="step">
            <div class="step-title">{t}</div>
            <div class="step-body"><p>{b}</p>{why}</div>
          </li>''')
    keys = "".join(f"<p>{k}</p>" for k in c["keys"])
    warns = "".join(f"<li>{x}</li>" for x in c["warns"])
    map_items = "".join(f"<li>{x}</li>" for x in c["map"])
    return f'''
<!-- {c["sec"]} -->
<article class="card {cls}" id="{c["id"]}">
  <div class="chead" onclick="foldCard(event,this)">
    <span class="secnum">{c["sec"]}</span>
    <h3>{c["title"]} <span class="tag">课件 {c["deck"].split("-")[-1]}</span></h3>
    <div class="mark" onclick="markDone(event,this)">✓</div>
    <span class="caret">▼</span>
  </div>
  <div class="cbody">
    <div class="meta">
      <a class="loc book" data-doc="thermo-book" data-page="{c["book"][0]}" data-end="{c["book"][1]}" data-printed="{c["printed"]}" href="#" title="教材 pp.{c["printed"]}">教材 pp.{c["printed"]}</a>
      <span class="sep">·</span>
      <a class="loc" data-doc="{c["deck"]}" data-page="{c["dp"]}" data-end="{c["de"]}" data-printed="{c["dp"]}–{c["de"]}" href="#" title="讲义 pp.{c["dp"]}–{c["de"]}">讲义 pp.{c["dp"]}–{c["de"]}</a>
    </div>
    <div class="blk b-img">
      <h4>物理图像</h4>
      <p>{c["phys"]}</p>
    </div>
    <details class="blk b-deriv" data-hint="先自己想一遍再展开">
      <summary>推导脉络</summary>
      <div class="dbody"><ol>{map_items}</ol></div>
    </details>
    <details class="blk b-deriv b-full" id="full-{c["id"]}">
      <summary>完整推导 · {len(c["steps"])} 步：{c["title"]}</summary>
      <div class="dbody">
        <div class="deriv-note">目标：把本节的定义、方程和结论串成一条可复算的链；所有公式都可回代检查。约定：\(k\) 为 Boltzmann 常数，\(\beta=1/kT\)。</div>
        <ol class="steps">{"".join(steps)}</ol>
        {fig_html}
      </div>
    </details>
    <div class="blk b-key">
      <h4>关键结论</h4>
      <div class="concl">{keys}</div>
    </div>
    <div class="blk b-warn">
      <h4>易错点</h4>
      <ul>{warns}</ul>
    </div>
  </div>
</article>
'''


def cards_block():
    out = []
    for ch, title, sub in CHAPTERS:
        cls = {"4": "chap1", "6": "chap2", "7": "chap3"}[ch]
        out.append(f'<div class="chap {cls}" id="ch{ch}">\n  <span class="cn">CH.{ch}</span> {title}\n  <span class="cm">{sub}</span>\n</div>')
        for c in CARDS:
            if c["ch"] == ch:
                out.append(render_card(c))
    return "\n".join(out)


FORMULAS = [
    ("4", "4.1", "欧勒定理", r"V=\sum_i n_i v_i,\quad U=\sum_i n_i u_i,\quad S=\sum_i n_i s_i", "偏摩尔量"),
    ("4", "4.1", "化学势", r"\mu_i=(\partial G/\partial n_i)_{T,p,n_j}", "偏摩尔吉布斯函数"),
    ("4", "4.1", "多元系基本方程", r"dG=-S\,dT+V\,dp+\sum_i\mu_i\,dn_i", "四式同构"),
    ("4", "4.1", "Gibbs–Duhem", r"S\,dT-V\,dp+\sum_i n_i\,d\mu_i=0", "强度量约束"),
    ("4", "4.2", "复相平衡", r"T^\alpha=T^\beta,\quad p^\alpha=p^\beta,\quad \mu_i^\alpha=\mu_i^\beta", "逐组元"),
    ("4", "4.3", "吉布斯相律", r"f=k-\varphi+2", "凝聚相近似 f=k-φ+1"),
    ("4", "4.5", "化学平衡", r"\sum_i\nu_i\mu_i=0", "反应进度极值"),
    ("4", "4.5", "质量作用定律", r"K(T)=\prod_i(p_i/p^0)_{\rm eq}^{\nu_i}=e^{-\Delta G^0/RT}", "理想气体"),
    ("4", "4.6", "混合熵", r"\Delta S_{\rm mix}=-R\sum_i n_i\ln x_i", "不同种理想气体"),
    ("4", "4.8", "第三定律", r"S(0)=0,\qquad S(T)=\int_0^T C_V/T\,dT", "完美晶体"),
    ("6", "6.1", "\(\mu\) 空间", r"(q_1,\dots,q_r,p_1,\dots,p_r)\in\mathbb R^{2r}", "单粒子相空间"),
    ("6", "6.2", "谐振子能级", r"\varepsilon_n=(n+\tfrac12)\hbar\omega", "非简并"),
    ("6", "6.2", "转子能级", r"\varepsilon_l=l(l+1)\hbar^2/(2I)", "简并度 \(2l+1\)"),
    ("6", "6.2", "自由粒子态密度", r"D(\varepsilon)=\frac{2\pi V}{h^3}(2m)^{3/2}\varepsilon^{1/2}", "每个自旋态"),
    ("6", "6.5", "MB 微观状态数", r"\Omega_{\rm MB}=N!\prod_l\omega_l^{a_l}/a_l!", "可分辨粒子"),
    ("6", "6.5", "BE 微观状态数", r"\Omega_{\rm BE}=\prod_l(\omega_l+a_l-1)!/[a_l!(\omega_l-1)!]", "玻色子"),
    ("6", "6.5", "FD 微观状态数", r"\Omega_{\rm FD}=\prod_l\omega_l!/[a_l!(\omega_l-a_l)!]", "费米子"),
    ("6", "6.6", "玻尔兹曼分布", r"a_l=\omega_l e^{-\alpha-\beta\varepsilon_l}", "β=1/kT"),
    ("6", "6.7", "玻色分布", r"a_l=\omega_l/(e^{\alpha+\beta\varepsilon_l}-1)", "BE"),
    ("6", "6.7", "费米分布", r"a_l=\omega_l/(e^{\alpha+\beta\varepsilon_l}+1)", "FD"),
    ("6", "6.8", "经典极限", r"e^\alpha\gg1\iff a_l\ll\omega_l", "BE/FD → MB"),
    ("7", "7.1", "配分函数", r"Z_1=\sum_l\omega_l e^{-\beta\varepsilon_l}", "单粒子"),
    ("7", "7.1", "内能与广义力", r"U=-N\partial_\beta\ln Z_1,\quad p=(N/\beta)\partial_V\ln Z_1", "统计表达式"),
    ("7", "7.1", "熵与自由能", r"S=k(\ln Z_1+\beta U),\quad F=-NkT\ln Z_1", "可分辨粒子"),
    ("7", "7.2", "理想气体配分函数", r"Z_1=V(2\pi mkT/h^2)^{3/2}", "λ_T=h/√(2πmkT)"),
    ("7", "7.2", "物态方程", r"pV=NkT", "单原子理想气体"),
    ("7", "7.3", "Boltzmann 关系", r"S=k\ln\Omega", "熵的统计解释"),
    ("7", "7.4", "能量均分", r"\langle\frac12a_i x_i^2\rangle=\frac12kT", "每个平方项"),
    ("7", "7.6", "Sackur–Tetrode", r"S=Nk[\ln(V/(N\lambda_T^3))+5/2]", "单原子理想气体"),
    ("7", "7.7", "爱因斯坦热容", r"C_V=3Nk(\theta_E/T)^2e^{\theta_E/T}/(e^{\theta_E/T}-1)^2", "θ_E=ħω/k"),
    ("7", "7.8", "顺磁磁化", r"M=(N\mu/V)\tanh(\mu B/kT)", "两能级模型"),
]


def formula_block():
    groups = {}
    for ch, sec, name, formula, note in FORMULAS:
        groups.setdefault(ch, []).append((sec, name, formula, note))
    titles = {"4": "第4章 多元系的复相平衡和化学平衡（pp.90–111）",
              "6": "第6章 近独立粒子的最概然分布（pp.136–155）",
              "7": "第7章 玻尔兹曼统计（pp.157–182）"}
    cls = {"4": "c1", "6": "c2", "7": "c3"}
    out = []
    for ch in ["4", "6", "7"]:
        rows = []
        for sec, name, formula, note in groups[ch]:
            rows.append(f'<tr class="frow" data-ch="{ch}"><td class="fname">{name}</td><td class="fml">{formula}</td><td class="fnote">{sec}；{note}</td></tr>')
        out.append(f'''<div class="fsheet">
  <h4 class="fgroup-h {cls[ch]}">{titles[ch]}</h4>
  <table class="tab">
    <thead><tr><th style="width:18%">名称</th><th style="width:52%">公式</th><th>要点 / 定位</th></tr></thead>
    <tbody>{"".join(rows)}</tbody>
  </table>
</div>''')
    return "\n".join(out)


EX_BLOCK = '''
<div class="ex-type" style="border-left-color:var(--c1)">
  <h4>第四章题型 S：偏摩尔量、相律与化学平衡</h4>
  <div class="feat">识别特征：多元系、偏摩尔量、Gibbs–Duhem、复相平衡、相律、反应平衡常数。</div>
  <ul>
    <li>偏摩尔量：固定 \(T,p,n_j\) 求导；\(G=\\sum n_i\\mu_i\)，\(S dT-V dp+\\sum n_i d\\mu_i=0\)。</li>
    <li>相平衡：逐组元写 \\(\\mu_i^\\alpha=\\mu_i^\\beta\\)；相律 \\(f=k-\\varphi+2\\)，凝聚相近似减 1。</li>
    <li>化学平衡：\\(\\sum\\nu_i\\mu_i=0\\)，理想气体 \\(K=\\prod(p_i/p^0)_{\\rm eq}^{\\nu_i}\\)，\\(\\Delta G^0=-RT\\ln K\\)。</li>
    <li><b>易错</b>：偏摩尔量不是纯组元摩尔量；相律中 \\(k\\) 是组元数；反应物系数取负。</li>
  </ul>
</div>

<div class="ex-type" style="border-left-color:var(--c2)">
  <h4>第六章题型 T：微观状态计数与三种分布</h4>
  <div class="feat">识别特征：给 \\(N,E,V,\\omega_l\\)，求 \\(\\Omega\\)、最概然分布、经典极限条件。</div>
  <ul>
    <li>先写约束 \\(\\sum a_l=N\\)、\\(\\sum\\varepsilon_l a_l=E\\)，再选 MB/BE/FD 的 \\(\\Omega\\) 公式。</li>
    <li>取对数 + 斯特林 + 拉格朗日乘子；MB 得 \\(a_l=\\omega_l e^{-\\alpha-\\beta\\varepsilon_l}\\)。</li>
    <li>BE/FD 分母分别为 \\(e^{\\alpha+\\beta\\varepsilon_l}-1\\) 与 \\(+1\\)；\\(e^\\alpha\\gg1\\) 时回到 MB。</li>
    <li><b>易错</b>：FD 的 \\(a_l\\le\\omega_l\\)；\\(a_l\\) 是能级粒子数；\\(\\alpha\\) 与 \\(\\mu\\) 的符号。</li>
  </ul>
</div>

<div class="ex-type" style="border-left-color:var(--c3)">
  <h4>第七章题型 U：配分函数与热容量</h4>
  <div class="feat">识别特征：给能级/配分函数，求 \\(U,p,S,F,C_V\\)，或分析高低温极限。</div>
  <ul>
    <li>先写 \\(Z_1=\\sum\\omega_l e^{-\\beta\\varepsilon_l}\\)，再用 \\(U=-N\\partial_\\beta\\ln Z_1\\)、\\(p=(N/\\beta)\\partial_V\\ln Z_1\\)。</li>
    <li>熵和自由能：\\(S=k(\\ln Z_1+\\beta U)\\)，\\(F=-NkT\\ln Z_1\\)；全同粒子加 \\(1/N!\\)。</li>
    <li>热容：\\(C_V=(\\partial U/\\partial T)_V\\)；振动/转动用特征温度 \\(\\theta_v,\\theta_r\\) 判断是否解冻。</li>
    <li><b>易错</b>：\\(Z_1\\) 是单粒子；全同粒子 \\(Z_N=Z_1^N/N!\\)；低温经典均分失效。</li>
  </ul>
</div>
'''


def main():
    s = SRC.read_text(encoding="utf-8")
    if 'id="ch4"' in s:
        print("already inserted; abort")
        return
    marker = '<div class="chap chapfx" id="fx">'
    assert marker in s
    s = s.replace(marker, cards_block() + "\n\n" + marker, 1)
    marker2 = '<div class="chap chap1" id="ex"'
    assert marker2 in s
    s = s.replace(marker2, formula_block() + "\n\n" + marker2, 1)
    marker3 = '<!-- ══════════════ 自测题 ══════════════ -->'
    assert marker3 in s
    s = s.replace(marker3, EX_BLOCK + "\n\n" + marker3, 1)
    SRC.write_text(s, encoding="utf-8")
    for p in COPIES:
        p.write_text(s, encoding="utf-8")
    print("inserted", len(s), "chars")


if __name__ == "__main__":
    main()
