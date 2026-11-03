#!/usr/bin/env python3
"""Generate procedural aquarium textures as SVG, then render them to PNG.

Textures follow art/STYLE_GUIDE.md (palette, brightness cap) and are fully
reproducible from a seed.

Usage:
  python3 tools/gen_textures.py [--out build/phase0/textures] [--seed 7]

Writes:
  gravel_main.svg/png   main-stage gravel strip (parallax 0.85)
  gravel_lip.svg/png    lower lip of the main strip, drawn in front of structure bases
  gravel_front.svg/png  narrow front strip at the bottom edge (parallax 1.0)
  gravel_far.svg/png    far, hazy gravel strip (parallax 0.5)
  water_back.svg/png    back water gradient + hazy back wall (parallax 0.3)
  light_rays.svg/png    soft light shafts overlay
"""
import argparse
import io
import math
import os
import random

import resvg_py
from PIL import Image

CAP = 235
VIEW_W, VIEW_H = 1920, 1080
PAN = 3840          # camera travel at parallax 1.0
DRIFT = 160         # largest vertical drift option (+/-)

# (color, weight): pastels and neutrals dominate, jewel tones add sparkle
PEBBLE_COLORS = [
    ("#E6A3C3", 6), ("#B9A2E0", 6), ("#9ED9C0", 6), ("#D6DCE2", 5), ("#D9C08E", 6),
    ("#A8907A", 3), ("#4FD1D9", 3), ("#EBC42A", 2), ("#E8731C", 2), ("#E0484D", 1.5),
    ("#3F5FC4", 2), ("#22B5A8", 2), ("#C2378E", 1.5), ("#9CD43A", 2), ("#EB5E9E", 2),
    ("#7A3FC4", 1.5),
]
GRAVEL_PRESETS = {
    "pastel": PEBBLE_COLORS,
    "jewel": [(c, 1) for c in ("#E8731C", "#EBC42A", "#E0484D", "#EB5E9E", "#C2378E", "#7A3FC4",
                               "#3F5FC4", "#2E7DE0", "#22B5A8", "#4FD1D9", "#9CD43A", "#4FA83D")],
    "natural": [("#D9C08E", 10), ("#A8907A", 8), ("#6F7A8C", 5), ("#D6DCE2", 5), ("#8A5A3A", 3),
                ("#E6A3C3", 1), ("#4FD1D9", 1), ("#EBC42A", 1), ("#B9A2E0", 1), ("#E0484D", 0.6)],
}
_PEBBLE_POP = [c for c, _ in PEBBLE_COLORS]
_PEBBLE_W = [w for _, w in PEBBLE_COLORS]


def set_gravel_preset(name):
    global _PEBBLE_POP, _PEBBLE_W
    _PEBBLE_POP = [c for c, _ in GRAVEL_PRESETS[name]]
    _PEBBLE_W = [w for _, w in GRAVEL_PRESETS[name]]


def layer_width(f):
    return int(VIEW_W + PAN * f)


def hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgb2hex(c):
    return "#%02X%02X%02X" % tuple(max(0, min(CAP, int(round(v)))) for v in c)


def mix(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def shade(h, k):
    """k<0 darker (toward deep indigo), k>0 lighter (toward soft white)."""
    c = hex2rgb(h)
    if k < 0:
        return rgb2hex(mix(c, (26, 24, 60), -k))
    return rgb2hex(mix(c, (228, 232, 234), k))


def scale_color(h, f):
    c = hex2rgb(h)
    return rgb2hex(tuple(v * f for v in c))


def noise1d(x, seed, octaves=((0.0021, 1.0), (0.0067, 0.45), (0.019, 0.2))):
    v = 0.0
    for i, (fr, amp) in enumerate(octaves):
        v += amp * math.sin(x * fr * 2 * math.pi + seed * (i + 1) * 1.7)
    return v


def render(svg, path_png):
    data = bytes(resvg_py.svg_to_bytes(svg_string=svg))
    with open(path_png, "wb") as f:
        f.write(data)
    return Image.open(io.BytesIO(data))


def svg_doc(w, h, body, defs=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
            f'<defs>{defs}</defs>{body}</svg>')


def gravel(w, h, top, amp, rmin, rmax, bright, seed, haze=None, fill_under=True):
    """Pebble strip: uneven top edge around y=top, pebbles packed down to h."""
    rnd = random.Random(seed)
    parts = []
    # top-edge profile
    def edge(x):
        return top + amp * noise1d(x, seed)
    if fill_under:
        pts = [f"0,{h}"] + [f"{x},{edge(x) + rmax * 0.8:.1f}" for x in range(0, w + 40, 40)] + [f"{w},{h}"]
        parts.append(f'<polygon points="{" ".join(pts)}" fill="{scale_color("#4A3F5A", bright)}"/>')
    # rows from back (top) to front (bottom); pebbles grow toward the front
    y = top - amp - rmax
    while y < h + rmax:
        depth = max(0.0, min(1.0, (y - top + amp) / max(1, h - top + amp)))
        r_lo = rmin + (rmax - rmin) * 0.35 * depth
        r_hi = rmin + (rmax - rmin) * (0.6 + 0.4 * depth)
        x = -rmax + rnd.uniform(0, rmax)
        row = []
        while x < w + rmax:
            r = rnd.uniform(r_lo, r_hi)
            px = x + rnd.uniform(-r * 0.3, r * 0.3)
            py = y + rnd.uniform(-r * 0.35, r * 0.35)
            if py >= edge(px) - r * 0.2:
                row.append((px, py, r))
            x += r * rnd.uniform(1.35, 1.75)
        for px, py, r in row:
            col = scale_color(rnd.choices(_PEBBLE_POP, _PEBBLE_W)[0], bright * rnd.uniform(0.88, 1.0))
            rx, ry = r, r * rnd.uniform(0.62, 0.8)
            rot = rnd.uniform(-25, 25)
            parts.append(
                f'<g transform="translate({px:.1f} {py:.1f}) rotate({rot:.1f})">'
                f'<ellipse rx="{rx:.1f}" ry="{ry:.1f}" fill="{col}" stroke="{shade(col, -0.45)}" stroke-width="1.5"/>'
                f'<ellipse cx="{rx * 0.18:.1f}" cy="{ry * 0.3:.1f}" rx="{rx * 0.8:.1f}" ry="{ry * 0.62:.1f}" fill="{shade(col, -0.22)}"/>'
                f'<ellipse cx="{-rx * 0.1:.1f}" cy="{-ry * 0.05:.1f}" rx="{rx * 0.72:.1f}" ry="{ry * 0.6:.1f}" fill="{col}"/>'
                f'<ellipse cx="{-rx * 0.35:.1f}" cy="{-ry * 0.4:.1f}" rx="{rx * 0.3:.1f}" ry="{ry * 0.22:.1f}" fill="{shade(col, 0.4)}"/>'
                f'</g>')
        y += (r_lo + r_hi) * 0.42
    body = "".join(parts)
    defs = ""
    if haze:
        color, opacity = haze
        body += f'<rect width="{w}" height="{h}" fill="{color}" opacity="{opacity}"/>'
    return svg_doc(w, h, body, defs)


def water_back(w, h, seed):
    rnd = random.Random(seed)
    defs = ('<linearGradient id="wg" x1="0" y1="0" x2="0" y2="1">'
            '<stop offset="0" stop-color="#2C86A6"/>'
            '<stop offset="0.45" stop-color="#17608A"/>'
            '<stop offset="1" stop-color="#0C2C52"/></linearGradient>'
            '<filter id="blur" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="18"/></filter>'
            '<filter id="blur2" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="40"/></filter>')
    parts = [f'<rect width="{w}" height="{h}" fill="url(#wg)"/>']
    # soft brighter glow patches near the top (light from surface)
    for i in range(5):
        cx = rnd.uniform(0, w)
        parts.append(f'<ellipse cx="{cx:.0f}" cy="{rnd.uniform(-40, 120):.0f}" rx="{rnd.uniform(300, 600):.0f}" ry="{rnd.uniform(120, 220):.0f}" '
                     f'fill="#5FB4C8" opacity="0.18" filter="url(#blur2)"/>')
    # hazy back-wall rock silhouettes
    for band, (col, op, base) in enumerate([("#1B5A7E", 0.55, h * 0.70), ("#164C70", 0.7, h * 0.80)]):
        pts = [f"0,{h}"]
        for x in range(0, w + 60, 60):
            y = base - 90 * (0.5 + 0.5 * noise1d(x, seed + band * 13, ((0.0015, 1.0), (0.005, 0.5), (0.013, 0.25))))
            pts.append(f"{x},{y:.0f}")
        pts.append(f"{w},{h}")
        parts.append(f'<polygon points="{" ".join(pts)}" fill="{col}" opacity="{op}" filter="url(#blur)"/>')
    return svg_doc(w, h, "".join(parts), defs)


def light_rays(w, h, seed):
    rnd = random.Random(seed)
    defs = ('<filter id="rb" x="-30%" y="-10%" width="160%" height="120%"><feGaussianBlur stdDeviation="22"/></filter>'
            '<linearGradient id="rg" x1="0" y1="0" x2="0" y2="1">'
            '<stop offset="0" stop-color="#8FD3E0" stop-opacity="1"/>'
            '<stop offset="1" stop-color="#8FD3E0" stop-opacity="0"/></linearGradient>')
    parts = []
    x = rnd.uniform(80, 300)
    while x < w:
        top_w = rnd.uniform(60, 160)
        spread = rnd.uniform(140, 320)
        lean = rnd.uniform(60, 220)
        op = rnd.uniform(0.07, 0.14)
        pts = f"{x:.0f},-40 {x + top_w:.0f},-40 {x + top_w + spread + lean:.0f},{h} {x + lean - spread * 0.3:.0f},{h}"
        parts.append(f'<polygon points="{pts}" fill="url(#rg)" opacity="{op:.3f}" filter="url(#rb)"/>')
        x += rnd.uniform(380, 760)
    return svg_doc(w, h, "".join(parts), defs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="build/phase0/textures")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--gravel", default="pastel", choices=sorted(GRAVEL_PRESETS))
    ap.add_argument("--swatches", action="store_true", help="also render a swatch of every gravel preset")
    a = ap.parse_args()
    if a.swatches:
        os.makedirs(a.out, exist_ok=True)
        for name in GRAVEL_PRESETS:
            set_gravel_preset(name)
            im = render(gravel(1200, 240, top=60, amp=22, rmin=8, rmax=17, bright=0.95, seed=a.seed),
                        os.path.join(a.out, f"swatch_gravel_{name}.png"))
            print("swatch", name, im.size)
    set_gravel_preset(a.gravel)
    os.makedirs(a.out, exist_ok=True)
    s = a.seed
    jobs = {
        # name: (svg, ...)
        "gravel_main": gravel(layer_width(0.85), 300, top=70, amp=26, rmin=8, rmax=17, bright=0.92, seed=s),
        "gravel_lip": gravel(layer_width(0.85), 230, top=60, amp=14, rmin=9, rmax=18, bright=0.95, seed=s + 1),
        "gravel_front": gravel(layer_width(1.0), 240, top=50, amp=20, rmin=12, rmax=24, bright=1.0, seed=s + 2),
        "gravel_far": gravel(layer_width(0.5), 200, top=50, amp=18, rmin=5, rmax=10, bright=0.8, seed=s + 3,
                             haze=("#2E6E92", 0.55)),
        "water_back": water_back(layer_width(0.3), VIEW_H + 2 * int(DRIFT * 0.3) + 40, seed=s),
        "light_rays": light_rays(layer_width(0.9), VIEW_H + 2 * int(DRIFT * 0.9), seed=s),
    }
    for name, svg in jobs.items():
        with open(os.path.join(a.out, f"{name}.svg"), "w") as f:
            f.write(svg)
        im = render(svg, os.path.join(a.out, f"{name}.png"))
        print(f"{name}: {im.size}")


if __name__ == "__main__":
    main()
