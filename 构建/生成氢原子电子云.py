# -*- coding: utf-8 -*-
"""Generate five hydrogen electron-cloud cross-sections for the QM reader.

Units: Bohr radius a0 = 1.  Brightness is proportional to |psi|^2, with a
per-orbital gamma/fade for print legibility (stated on the page).
"""
from math import factorial
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from PIL import Image
from scipy.special import eval_genlaguerre

OUT = Path(r"F:\物理复习提纲合集\程序\resources\app\renderer\hydrogen")
OUT.mkdir(parents=True, exist_ok=True)


def radial(n, l, r):
    rho = 2.0 * r / n
    norm = np.sqrt((2.0 / n) ** 3 * factorial(n - l - 1) / (2 * n * factorial(n + l) ** 3))
    return norm * np.exp(-rho / 2.0) * rho ** l * eval_genlaguerre(n - l - 1, 2 * l + 1, rho)


def angular(l, m, theta, phi):
    if l == 0:
        return np.ones_like(theta) / np.sqrt(4 * np.pi)
    if l == 1 and m == 0:
        return np.sqrt(3 / (4 * np.pi)) * np.cos(theta)
    if l == 2 and m == 0:
        return np.sqrt(5 / (16 * np.pi)) * (3 * np.cos(theta) ** 2 - 1)
    if l == 2 and m == 2:
        # real d_xy: sqrt(15/16pi) sin^2(theta) sin(2phi)
        return np.sqrt(15 / (16 * np.pi)) * np.sin(theta) ** 2 * np.sin(2 * phi)
    raise ValueError((l, m))


def make(name, n, l, m, plane, L, gamma, scale, palette, floor=0.0, fade_edge=0.94, N=1100):
    q = np.linspace(-L, L, N)
    A, B = np.meshgrid(q, q, indexing="xy")
    if plane == "xz":
        X, Z = A, B
        Y = np.zeros_like(A)
    else:
        X, Y = A, B
        Z = np.zeros_like(A)
    r = np.sqrt(X ** 2 + Y ** 2 + Z ** 2)
    theta = np.arccos(np.clip(Z / np.maximum(r, 1e-12), -1.0, 1.0))
    phi = np.arctan2(Y, X)
    psi = radial(n, l, r) * angular(l, m, theta, phi)
    rho = psi ** 2
    rho = rho / rho.max()

    # Perceptual tone curve; fade the outer frame so the cloud sits in the dark.
    I = rho ** gamma
    if floor:
        I = np.clip((I - floor) / (1.0 - floor), 0.0, 1.0)
    R = np.sqrt(A ** 2 + B ** 2)
    fade = np.clip(1.0 - (R / (fade_edge * L)) ** 8, 0.0, 1.0)
    I = np.clip(I * fade, 0.0, 1.0)

    cmap = LinearSegmentedColormap.from_list("cloud", palette, N=512)
    fig = plt.figure(figsize=(6, 6), dpi=180, facecolor="#050b12")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_facecolor("#050b12")
    ax.imshow(I, extent=[-L, L, -L, L], origin="lower", cmap=cmap,
              interpolation="bicubic", vmin=0, vmax=1)
    ax.contour(q, q, rho * fade, levels=[0.006, 0.025, 0.09],
               colors=["#e6fff9"], linewidths=0.55, alpha=0.20)
    ax.set_xlim(-L, L)
    ax.set_ylim(-L, L)
    ax.axis("off")

    # nucleus marker
    ax.scatter([0], [0], s=14, c="#ffffff", edgecolors="none", zorder=20)

    # scale bar
    x0 = -L * 0.84
    y0 = -L * 0.87
    ax.plot([x0, x0 + scale], [y0, y0], color="#e3fff9", lw=5,
            solid_capstyle="butt", alpha=0.82, zorder=30)
    ax.text(x0 + scale / 2, y0 + 0.045 * L, rf"${scale:g}\,a_0$",
            ha="center", va="bottom", color="#e3fff9", fontsize=17,
            alpha=0.9, zorder=30)

    png = OUT / f"{name}.png"
    webp = OUT / f"{name}.webp"
    fig.savefig(png, facecolor=fig.get_facecolor())
    plt.close(fig)
    Image.open(png).convert("RGB").save(webp, "WEBP", quality=90, method=6)
    png.unlink()
    print(webp, webp.stat().st_size)


TEAL = ["#050b12", "#06202d", "#074857", "#0d8b92", "#4bd6c6", "#d7fff7"]
TEAL_SOFT = ["#050b12", "#071923", "#0c3541", "#126f76", "#3ac9bd", "#d7fff7"]
GOLD = ["#0a0703", "#241606", "#5b3507", "#b97512", "#f6c04b", "#fff8df"]
VIOLET = ["#07050d", "#1d1232", "#43266b", "#7f55c7", "#c69bff", "#fbf1ff"]
BLUE = ["#040912", "#081a31", "#103c74", "#246eb5", "#71bdf0", "#e9f8ff"]

make("1s", 1, 0, 0, "xz", 3.8, 0.50, 2, TEAL)
# The 2s slice has a very bright core and a low-contrast outer shell; use a
# small floor so the radial node reads without washing the frame in teal.
make("2s", 2, 0, 0, "xz", 8.2, 0.30, 5, TEAL_SOFT, floor=0.05, fade_edge=0.90)
make("2pz", 2, 1, 0, "xz", 13.0, 0.48, 5, GOLD)
make("3dz2", 3, 2, 0, "xz", 22.0, 0.52, 10, VIOLET)
make("3dxy", 3, 2, 2, "xy", 22.0, 0.52, 10, BLUE)
