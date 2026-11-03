#!/usr/bin/env python3
"""Phase 0 mockup layout: writes art/mockup/layout.json for tools/make_mockup.py.

Coordinates: each layer is 1920 + 3840*f wide (f = parallax factor). y is the
screen y with the camera at its vertical center. Items anchor at their
bottom-left unless "anchor" says otherwise.
"""
import json
import os
import random

S = "art/samples/"
T = "build/phase0/textures/"
HERE = os.path.dirname(os.path.abspath(__file__))
rnd = random.Random(11)

FAR_HAZE = ["#1E6A90", 0.5]


def sp(name, x, y, **kw):
    d = {"src": S + name + ".svg", "x": x, "y": y}
    d.update(kw)
    return d


def school(cx, cy, n, spread=(170, 70), flip=False, scale=1.0, **kw):
    out = []
    for i in range(n):
        out.append(sp("fish_neon_tetra", cx + rnd.uniform(-spread[0], spread[0]), cy + rnd.uniform(-spread[1], spread[1]),
                      anchor="center", flip=flip, scale=round(scale * rnd.uniform(0.92, 1.05), 2), **kw))
    return out


# ---- structure placement (main stage) and features inside them ----
GROTTO = {"x": 700, "bottom": 990}
CASTLE = {"x": 3480, "bottom": 995}

layers = []

layers.append({"id": "water", "parallax": 0.3, "items": [
    {"src": T + "water_back.png", "x": 0, "y": -68, "anchor": "top", "stretch": True, "fill": True}]})

far = [{"src": T + "gravel_far.png", "x": 0, "y": 840, "anchor": "top", "stretch": True}]
for x, s in [(120, 0.55), (690, 0.5), (1480, 0.6), (2280, 0.52), (3080, 0.58), (3620, 0.5)]:
    far.append(sp("plant_vallisneria", x, 905, scale=s, haze=FAR_HAZE, opacity=0.9))
for x in (1050, 2650):
    far.append(sp("plant_amazon_sword", x, 905, scale=0.5, haze=FAR_HAZE, opacity=0.9))
for x, fl in [(380, False), (1850, True), (3300, False)]:
    far.append(sp("coral_cluster", x, 908, scale=0.55, flip=fl, haze=FAR_HAZE, opacity=0.9))
layers.append({"id": "far_scenery", "parallax": 0.5, "items": far})

farfish = []
for x, y, tint, fl in [(400, 300, "#3F8EE6", False), (1300, 520, "#EBD23A", True), (2100, 260, "#8E5BD8", False),
                       (2900, 600, "#EB8A3A", True), (3600, 380, "#3F8EE6", True),
                       (700, 140, "#EBD23A", True), (1600, 190, "#3F8EE6", False), (2600, 330, "#8E5BD8", True),
                       (3300, 560, "#EBD23A", False), (3850, 170, "#EB8A3A", True), (250, 520, "#8E5BD8", False)]:
    farfish.append(sp("fish_tang_base", x, y, anchor="center", scale=0.5, tint=tint, flip=fl, haze=["#1E6A90", 0.45], opacity=0.9))
farfish += school(1750, 420, 9, spread=(120, 50), scale=0.6, haze=["#1E6A90", 0.45], opacity=0.9)
farfish += school(3200, 230, 8, spread=(110, 45), flip=True, scale=0.6, haze=["#1E6A90", 0.45], opacity=0.9)
farfish += school(2500, 620, 9, spread=(120, 45), scale=0.6, haze=["#1E6A90", 0.45], opacity=0.9)
farfish.append(sp("fish_clownfish", 800, 640, anchor="center", scale=0.55, haze=["#1E6A90", 0.45], opacity=0.9))
farfish.append(sp("fish_lionfish", 2050, 700, anchor="center", scale=0.5, flip=True, haze=["#1E6A90", 0.45], opacity=0.9))
layers.append({"id": "far_fish", "parallax": 0.55, "items": farfish})

main_back = [{"src": T + "gravel_main.png", "x": 0, "y": 850, "anchor": "top", "stretch": True}]
# plants and coral behind everything else on the main stage
for x, s in [(40, 1.0), (1600, 0.85), (2230, 0.7), (2950, 1.05), (4120, 0.95), (4880, 1.0)]:
    main_back.append(sp("plant_vallisneria", x, 990, scale=s))
for x, fl in [(430, False), (4260, True), (4700, False)]:
    main_back.append(sp("plant_amazon_sword", x, 992, flip=fl))
for x, fl, s in [(150, False, 1.0), (1480, False, 0.8), (2700, True, 1.0), (4350, False, 1.0)]:
    main_back.append(sp("coral_cluster", x, 985, flip=fl, scale=s))
main_back.append(sp("anemone", 1820, 978))
main_back.append(sp("grotto_back", GROTTO["x"], GROTTO["bottom"]))
main_back.append(sp("castle_back", CASTLE["x"], CASTLE["bottom"]))
main_back.append(sp("chest_open", 2420, 1000, rotate=0))
# crab tucked in the grotto crevice (drawn between grotto back and front)
# crevice is x 41-243, y 325-411 inside the 760x420 grotto; crab feet at y ~394
main_back.append(sp("crab", GROTTO["x"] + 78, GROTTO["bottom"] - 420 + 398))
main_back.append(sp("crab", 4420, 968, flip=True))
# shrimp on the gravel
for x, y, tint, fl in [(2330, 958, "#D8323A", False), (2760, 962, "#2F6FD8", True), (4150, 960, "#EBC82E", False),
                       (1300, 958, "#3FA860", True), (4600, 962, "#EB7A2A", False)]:
    main_back.append(sp("shrimp_base", x, y, tint=tint, flip=fl))
main_back.append(sp("shrimp_rili", 2050, 965, flip=True))
layers.append({"id": "main_back", "parallax": 0.85, "items": main_back})

mid = []
mid.append(sp("fish_clownfish", 1960, 770, anchor="center"))
mid.append(sp("fish_clownfish", 2075, 840, anchor="center", flip=True))
mid.append(sp("fish_lionfish", 2760, 520, anchor="center"))
for x, y, tint, fl in [(520, 420, "#EBD23A", False), (1640, 590, "#8E5BD8", True), (3980, 470, "#3F8EE6", False),
                       (4700, 690, "#EB8A3A", True), (2260, 330, "#EBD23A", True), (1000, 230, "#3F8EE6", False),
                       (300, 170, "#EB8A3A", True), (3050, 190, "#8E5BD8", True), (4900, 250, "#EBD23A", True),
                       (1750, 140, "#EB8A3A", False), (3700, 120, "#EBD23A", False)]:
    mid.append(sp("fish_tang_base", x, y, anchor="center", tint=tint, flip=fl))
# a tang passing through the castle doorway (between castle back and front)
# doorway is x 180-380, y 470-690 inside the 560x700 castle; the fish's head is hidden by the wall at x=380
mid.append(sp("fish_tang_base", CASTLE["x"] + 340, CASTLE["bottom"] - 700 + 600, anchor="center", tint="#EB8A3A"))
# a clownfish half inside the grotto mouth, shaded
# cave mouth is x 331-668, y 160-354; this one swims in, its tail still behind the right pillar
mid.append(sp("fish_clownfish", GROTTO["x"] + 640, GROTTO["bottom"] - 420 + 270, anchor="center", flip=True, tint="#8C96A8"))
mid += school(1150, 340, 12)
mid += school(4320, 300, 10, flip=True)
mid += school(2980, 760, 8, spread=(120, 50))
mid += school(2450, 170, 10, spread=(150, 50), flip=True)
layers.append({"id": "mid_fish", "parallax": 0.85, "items": mid})

main_front = [sp("grotto_front", GROTTO["x"], GROTTO["bottom"]), sp("castle_front", CASTLE["x"], CASTLE["bottom"]),
              {"src": T + "gravel_lip.png", "x": 0, "y": 905, "anchor": "top", "stretch": True}]
# shrimp grazing on the grotto's moss
# moss walk path points (grotto coords): (160,24) (380,17) (620,53)
for px, py, tint, fl in [(160, 24, "#D8323A", False), (380, 17, "#2F6FD8", True), (620, 53, "#EBC82E", False)]:
    main_front.append(sp("shrimp_base", GROTTO["x"] + px - 60, GROTTO["bottom"] - 420 + py + 8, tint=tint, flip=fl))
layers.append({"id": "main_front", "parallax": 0.85, "items": main_front})

front = [{"src": T + "gravel_front.png", "x": 0, "y": 1000, "anchor": "top", "stretch": True}]
for x, tint, fl in [(700, "#EB7A2A", False), (2900, "#D8323A", True), (4700, "#3FA860", False)]:
    front.append(sp("shrimp_base", x, 1062, tint=tint, flip=fl, scale=1.15))
layers.append({"id": "front_gravel", "parallax": 1.0, "items": front})

layers.append({"id": "near_fish", "parallax": 1.1, "items": [
    sp("fish_lionfish", 1450, 300, anchor="center", scale=1.35, flip=True),
    sp("fish_tang_base", 5470, 170, anchor="center", scale=1.35, tint="#8E5BD8", flip=True),
]})

fg = []
for x in (-60, 4190, 6280):
    fg.append(sp("plant_vallisneria", x, 1130, scale=1.4, blur=4, tint="#A9BCC4"))
layers.append({"id": "foreground", "parallax": 1.2, "overview": False, "items": fg})

layers.append({"id": "light", "parallax": 0.9, "items": [
    {"src": T + "light_rays.png", "x": 0, "y": -144, "anchor": "top", "stretch": True}]})

layout = {
    "views": {"left": 0, "middle": 1920, "right": 3840},
    "bubble_streams": [
        {"id": "castle", "layer": "main_back", "x": CASTLE["x"] + 280, "y": CASTLE["bottom"] - 700 + 14, "height": 600, "count": 14, "seed": 3},
        {"id": "chest", "layer": "main_front", "x": 2535, "y": 860, "height": 300, "count": 7, "seed": 5},
        {"id": "bubbler", "layer": "main_back", "x": 1540, "y": 940, "height": 900, "count": 22, "seed": 9},
    ],
    "layers": layers,
}

with open(os.path.join(HERE, "layout.json"), "w") as fh:
    json.dump(layout, fh, indent=1)
print("wrote layout.json:", sum(len(l["items"]) for l in layers), "items")
