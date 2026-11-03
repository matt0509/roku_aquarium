#!/usr/bin/env python3
"""Compose the Phase 0 layout mockup from the sample SVGs and procedural textures.

It simulates the Roku's parallax layers: each layer has a parallax factor f,
a width of 1920 + 3840*f, and moves by -camera*f. Screenshots are rendered at
several camera positions, plus a whole-tank overview with viewport outlines.

Usage:
  python3 tools/gen_textures.py            # once, for gravel/water/light rays
  python3 tools/make_mockup.py [--layout art/mockup/layout.json] [--out build/phase0/mockup]
"""
import argparse
import io
import json
import math
import os
import random
import re

import resvg_py
from PIL import Image, ImageChops, ImageDraw, ImageFilter

VIEW_W, VIEW_H = 1920, 1080
PAN = 3840
MAIN_F = 0.85
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_cache = {}


def layer_width(f):
    return int(VIEW_W + PAN * f)


def svg_size(path):
    with open(path) as fh:
        head = fh.read(2000)
    w = float(re.search(r'\bwidth="([\d.]+)', head).group(1))
    h = float(re.search(r'\bheight="([\d.]+)', head).group(1))
    return w, h


def load_sprite(src, scale=1.0):
    key = (src, scale)
    if key in _cache:
        return _cache[key]
    path = os.path.join(ROOT, src)
    if src.endswith(".svg"):
        with open(path) as fh:
            data = bytes(resvg_py.svg_to_bytes(svg_string=fh.read(), zoom=scale))
        im = Image.open(io.BytesIO(data)).convert("RGBA")
    else:
        im = Image.open(path).convert("RGBA")
        if scale != 1.0:
            im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
    _cache[key] = im
    return im


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def tint(im, hx):
    tr, tg, tb = hex_rgb(hx)
    r, g, b, a = im.split()
    return Image.merge("RGBA", (r.point(lambda v: v * tr // 255), g.point(lambda v: v * tg // 255),
                                b.point(lambda v: v * tb // 255), a))


def haze(im, hx, amount):
    """Blend RGB toward a water color (atmospheric depth)."""
    solid = Image.new("RGBA", im.size, hex_rgb(hx) + (255,))
    mixed = Image.blend(im, solid, amount)
    mixed.putalpha(im.getchannel("A"))
    return mixed


def fade(im, opacity):
    a = im.getchannel("A").point(lambda v: int(v * opacity))
    out = im.copy()
    out.putalpha(a)
    return out


def prepare(item):
    im = load_sprite(item["src"], item.get("scale", 1.0))
    if item.get("tint"):
        im = tint(im, item["tint"])
    if item.get("flip"):
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    if item.get("rotate"):
        im = im.rotate(item["rotate"], resample=Image.BICUBIC, expand=True)
    if item.get("haze"):
        im = haze(im, item["haze"][0], item["haze"][1])
    if item.get("blur"):
        im = im.filter(ImageFilter.GaussianBlur(item["blur"]))
    if item.get("opacity", 1.0) != 1.0:
        im = fade(im, item["opacity"])
    return im


def bubbles_svg(n, seed, height=420, width=60):
    rnd = random.Random(seed)
    parts = []
    y = height - 10
    for i in range(n):
        r = rnd.uniform(3.5, 9)
        x = width / 2 + 10 * math.sin(i * 1.3 + seed) + rnd.uniform(-4, 4)
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="#8FD3E0" fill-opacity="0.22" '
                     f'stroke="#D6E6EA" stroke-opacity="0.75" stroke-width="1.5"/>'
                     f'<circle cx="{x - r * 0.35:.1f}" cy="{y - r * 0.35:.1f}" r="{r * 0.28:.1f}" fill="#E4E8EA" fill-opacity="0.8"/>')
        y -= rnd.uniform(26, 48)
        if y < 10:
            break
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}">{"".join(parts)}</svg>')


def build_bubbles(layout, out_dir):
    for b in layout.get("bubble_streams", []):
        path = os.path.join(out_dir, f"bubbles_{b['id']}.svg")
        with open(path, "w") as fh:
            fh.write(bubbles_svg(b.get("count", 12), b.get("seed", 1), b.get("height", 420)))
        b["_src"] = os.path.relpath(path, ROOT)


def place(canvas, im, x, y, anchor):
    """anchor: 'bottom' -> (x, y) is left/bottom; 'center' -> center; default top-left."""
    if anchor == "bottom":
        y = y - im.height
    elif anchor == "center":
        x, y = x - im.width / 2, y - im.height / 2
    canvas.alpha_composite(im, (int(round(x)), int(round(y)))) if 0 <= x and 0 <= y and \
        x + im.width <= canvas.width and y + im.height <= canvas.height else paste_clipped(canvas, im, x, y)


def paste_clipped(canvas, im, x, y):
    x, y = int(round(x)), int(round(y))
    l, t = max(0, -x), max(0, -y)
    r, b = min(im.width, canvas.width - x), min(im.height, canvas.height - y)
    if r <= l or b <= t:
        return
    canvas.alpha_composite(im.crop((l, t, r, b)), (x + l, y + t))


def items_for_layer(layout, layer):
    items = list(layer.get("items", []))
    for b in layout.get("bubble_streams", []):
        if b["layer"] == layer["id"]:
            items.append({"src": b["_src"], "x": b["x"] - 30, "y": b["y"], "anchor": "bottom"})
    return items


def render_view(layout, cx, cy, dim=0.0):
    canvas = Image.new("RGBA", (VIEW_W, VIEW_H), (10, 35, 66, 255))
    for layer in layout["layers"]:
        f = layer["parallax"]
        ox, oy = -cx * f, -cy * f
        for it in items_for_layer(layout, layer):
            im = prepare(it)
            place(canvas, im, it["x"] + ox, it["y"] + oy, it.get("anchor", "bottom"))
    if dim:
        teal = Image.new("RGBA", canvas.size, (20, 60, 90, int(255 * dim * 0.35)))
        black = Image.new("RGBA", canvas.size, (0, 0, 0, int(255 * dim)))
        canvas.alpha_composite(teal)
        canvas.alpha_composite(black)
    return canvas.convert("RGB")


def render_overview(layout, top=-170, height=1420):
    """Whole tank in main-stage coordinates, each layer aligned as seen at screen center."""
    W = layer_width(MAIN_F)
    canvas = Image.new("RGBA", (W, height), (10, 35, 66, 255))
    for layer in layout["layers"]:
        f = layer["parallax"]
        for it in items_for_layer(layout, layer):
            im = prepare(it)
            if it.get("stretch"):
                # backgrounds/gravel: map the whole strip onto the overview width
                xs = [(0 - 960) * MAIN_F / f + 960, (im.width - 960) * MAIN_F / f + 960]
                nw = int(xs[1] - xs[0])
                im = im.resize((max(1, nw), im.height), Image.LANCZOS)
                x = xs[0]
            else:
                x = 960 + (it["x"] - 960) * MAIN_F / f
            place(canvas, im, x, it["y"] - top, it.get("anchor", "bottom"))
    d = ImageDraw.Draw(canvas)
    colors = [(235, 210, 122), (228, 232, 234), (235, 94, 158)]
    for (name, cx), col in zip(layout["views"].items(), colors):
        x0 = cx * MAIN_F
        for k in range(4):
            d.rectangle([x0 + k, -top + k, x0 + VIEW_W - k, -top + VIEW_H - k], outline=col)
        dy = 160 * MAIN_F
        for x in range(int(x0), int(x0 + VIEW_W), 28):
            d.line([(x, -top - dy), (x + 14, -top - dy)], fill=col, width=3)
            d.line([(x, -top + VIEW_H + dy), (x + 14, -top + VIEW_H + dy)], fill=col, width=3)
    return canvas.convert("RGB")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--layout", default=os.path.join(ROOT, "art/mockup/layout.json"))
    ap.add_argument("--out", default=os.path.join(ROOT, "build/phase0/mockup"))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    with open(a.layout) as fh:
        layout = json.load(fh)
    build_bubbles(layout, a.out)
    for name, cx in layout["views"].items():
        im = render_view(layout, cx, 0)
        im.save(os.path.join(a.out, f"view_{name}.jpg"), quality=92)
        print("view", name)
    mid = list(layout["views"].values())[1]
    render_view(layout, mid, 0, dim=0.25).save(os.path.join(a.out, "view_middle_dim.jpg"), quality=92)
    render_view(layout, mid, -60, 0).save(os.path.join(a.out, "view_middle_drift_up.jpg"), quality=92)
    render_view(layout, mid, 160, 0).save(os.path.join(a.out, "view_middle_drift_down_large.jpg"), quality=92)
    ov = render_overview(layout)
    ov.save(os.path.join(a.out, "overview_full.jpg"), quality=90)
    ov.resize((ov.width // 2, ov.height // 2), Image.LANCZOS).save(os.path.join(a.out, "overview.jpg"), quality=90)
    print("overview", ov.size)


if __name__ == "__main__":
    main()
