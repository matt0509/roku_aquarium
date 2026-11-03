#!/usr/bin/env python3
"""Render aquarium SVG sprites to PNG and make review previews.

Usage:
  python3 tools/render_svg.py render FILE.svg [FILE.svg ...] [--out DIR] [--scale N]
        [--tint name=#RRGGBB ...] [--preview]
  python3 tools/render_svg.py compose OUT_NAME FILE.svg [FILE.svg ...] [--out DIR] [--preview]

render   Rasterize each SVG at its own width/height (1080p pixels) times --scale.
         Writes DIR/<name>.png and, with --tint, DIR/<name>__<tint>.png.
         Tints multiply RGB like Roku's Poster.blendColor.
compose  Stack several same-size SVGs (first = bottom) into DIR/<OUT_NAME>.png.
--preview  Also write DIR/<name>_preview.png: the sprite on a checkerboard and on
           aquarium water, plus every tint. Small sprites are zoomed 2x.

Every render prints a brightness-cap check: no opaque pixel may have a channel
above 235 (see art/STYLE_GUIDE.md).
"""
import argparse
import io
import os
import sys

import resvg_py
from PIL import Image, ImageChops, ImageDraw

CAP = 235
ALPHA_MIN = 32


def render_svg(path, scale=1.0):
    with open(path, "r", encoding="utf-8") as f:
        svg = f.read()
    im = Image.open(io.BytesIO(bytes(resvg_py.svg_to_bytes(svg_string=svg, zoom=scale)))).convert("RGBA")
    return im


def cap_report(im, label):
    r, g, b, a = im.split()
    mx = ImageChops.lighter(ImageChops.lighter(r, g), b)
    amask = a.point(lambda v: 255 if v >= ALPHA_MIN else 0)
    opaque = amask.histogram()[255]
    overmask = ImageChops.multiply(mx.point(lambda v: 255 if v > CAP else 0), amask)
    over = overmask.histogram()[255]
    worst = 0
    if over:
        hist = ImageChops.darker(mx, overmask).histogram()
        worst = max(i for i, c in enumerate(hist) if c)
    pct = (100.0 * over / opaque) if opaque else 0.0
    status = "OK" if over == 0 else "OVER CAP"
    print(f"  {label}: {im.width}x{im.height}px, opaque px={opaque}, over cap={over} ({pct:.2f}%) max={worst or '-'} [{status}]")
    return over


def tint(im, hexcolor):
    hexcolor = hexcolor.lstrip("#")
    tr, tg, tb = (int(hexcolor[i:i + 2], 16) for i in (0, 2, 4))
    r, g, b, a = im.split()
    r = r.point(lambda v: v * tr // 255)
    g = g.point(lambda v: v * tg // 255)
    b = b.point(lambda v: v * tb // 255)
    return Image.merge("RGBA", (r, g, b, a))


def checker(w, h, s=16):
    bg = Image.new("RGBA", (w, h), (150, 150, 158, 255))
    d = ImageDraw.Draw(bg)
    for y in range(0, h, s):
        for x in range(0, w, s):
            if (x // s + y // s) % 2:
                d.rectangle([x, y, x + s - 1, y + s - 1], fill=(120, 120, 130, 255))
    return bg


def water(w, h):
    top, bot = (44, 134, 166), (10, 35, 66)
    bg = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(bg)
    for y in range(h):
        t = y / max(1, h - 1)
        c = tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3)) + (255,)
        d.line([(0, y), (w, y)], fill=c)
    return bg


def on_bg(im, bg_fn, pad=24):
    w, h = im.width + 2 * pad, im.height + 2 * pad
    bg = bg_fn(w, h)
    bg.alpha_composite(im, (pad, pad))
    return bg


def preview(images, out_path, max_width=2400):
    """images: list of (label, RGBA image). Lays out tiles on checker + water."""
    base = images[0][1]
    zoom = 2 if max(base.width, base.height) <= 400 else 1
    tiles = []
    first = True
    for label, im in images:
        if zoom != 1:
            im = im.resize((im.width * zoom, im.height * zoom), Image.LANCZOS)
        if first:
            tiles.append(on_bg(im, checker))
            first = False
        tiles.append(on_bg(im, water))
    gap = 12
    cols = max(1, min(len(tiles), max_width // (tiles[0].width + gap)))
    rows = (len(tiles) + cols - 1) // cols
    tw, th = tiles[0].width, tiles[0].height
    sheet = Image.new("RGBA", (cols * (tw + gap) + gap, rows * (th + gap) + gap), (30, 30, 36, 255))
    for i, t in enumerate(tiles):
        x = gap + (i % cols) * (tw + gap)
        y = gap + (i // cols) * (th + gap)
        sheet.alpha_composite(t, (x, y))
    if sheet.width > max_width:
        f = max_width / sheet.width
        sheet = sheet.resize((max_width, int(sheet.height * f)), Image.LANCZOS)
    sheet.convert("RGB").save(out_path)
    print(f"  preview -> {out_path} (zoom {zoom}x)")


def parse_tints(items):
    tints = []
    for it in items or []:
        name, _, hx = it.partition("=")
        tints.append((name, hx))
    return tints


def cmd_render(a):
    os.makedirs(a.out, exist_ok=True)
    tints = parse_tints(a.tint)
    total_over = 0
    for path in a.files:
        name = os.path.splitext(os.path.basename(path))[0]
        print(path)
        im = render_svg(path, a.scale)
        total_over += cap_report(im, "base")
        im.save(os.path.join(a.out, f"{name}.png"))
        variants = [("base", im)]
        for tname, hx in tints:
            ti = tint(im, hx)
            ti.save(os.path.join(a.out, f"{name}__{tname}.png"))
            variants.append((tname, ti))
        if a.preview:
            preview(variants, os.path.join(a.out, f"{name}_preview.png"))
    sys.exit(1 if total_over else 0)


def cmd_compose(a):
    os.makedirs(a.out, exist_ok=True)
    layers = [render_svg(p, a.scale) for p in a.files]
    w, h = layers[0].size
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for p, im in zip(a.files, layers):
        if im.size != (w, h):
            sys.exit(f"size mismatch: {p} is {im.size}, expected {(w, h)}")
        canvas.alpha_composite(im)
    out = os.path.join(a.out, f"{a.name}.png")
    canvas.save(out)
    print(out)
    over = cap_report(canvas, "composite")
    if a.preview:
        preview([("composite", canvas)], os.path.join(a.out, f"{a.name}_preview.png"))
    sys.exit(1 if over else 0)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("render")
    r.add_argument("files", nargs="+")
    r.add_argument("--out", default="build/phase0")
    r.add_argument("--scale", type=float, default=1.0)
    r.add_argument("--tint", action="append", help="name=#RRGGBB (repeatable)")
    r.add_argument("--preview", action="store_true")
    r.set_defaults(fn=cmd_render)
    c = sub.add_parser("compose")
    c.add_argument("name")
    c.add_argument("files", nargs="+")
    c.add_argument("--out", default="build/phase0")
    c.add_argument("--scale", type=float, default=1.0)
    c.add_argument("--preview", action="store_true")
    c.set_defaults(fn=cmd_compose)
    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
