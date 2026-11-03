#!/usr/bin/env python3
"""Build the Phase 0 art review page from rendered previews and mockup views.

Run after tools/render_svg.py, tools/gen_textures.py --swatches and
tools/make_mockup.py. Writes build/phase0/review/index.html plus an img/ folder.
"""
import html
import os
import shutil

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P0 = os.path.join(ROOT, "build/phase0")
OUT = os.path.join(P0, "review")
IMG = os.path.join(OUT, "img")

PALETTE = [
    ("Outline", "#2A2745"), ("Soft white", "#E4E8EA"), ("Tangerine", "#E8731C"), ("Sunflower", "#EBC42A"),
    ("Coral red", "#E0484D"), ("Hot pink", "#EB5E9E"), ("Magenta", "#C2378E"), ("Royal purple", "#7A3FC4"),
    ("Lavender", "#B9A2E0"), ("Electric blue", "#2E7DE0"), ("Royal blue", "#3F5FC4"), ("Teal", "#22B5A8"),
    ("Aqua", "#4FD1D9"), ("Lime", "#9CD43A"), ("Leaf", "#4FA83D"), ("Moss dark", "#3E6E2E"),
    ("Sand", "#D9C08E"), ("Cool stone", "#6F7A8C"), ("Wood", "#8A5A3A"), ("Gold", "#E0B23A"),
    ("Water, surface", "#2C86A6"), ("Water, mid", "#134E78"), ("Water, deep", "#0A2342"),
]

# Sections of review items. Each item: id, title, note, images [(file in P0, caption)]
SECTIONS = []


def add_section(sid, title, intro, items):
    SECTIONS.append({"id": sid, "title": title, "intro": intro, "items": items})


def copy_img(rel, max_w=2400):
    src = os.path.join(P0, rel)
    if not os.path.exists(src):
        return None
    base = os.path.splitext(rel.replace("/", "__"))[0]
    im = Image.open(src)
    has_alpha = im.mode in ("RGBA", "LA") and im.getextrema()[-1][0] < 255
    if im.width > max_w:
        im = im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)
    if has_alpha:
        name = base + ".png"
        im.save(os.path.join(IMG, name), optimize=True)
    else:
        name = base + ".jpg"
        im.convert("RGB").save(os.path.join(IMG, name), quality=88)
    return "img/" + name, im.width, im.height


def esc(s):
    return html.escape(s, quote=True)


def card(item):
    figs = []
    for entry in item["images"]:
        rel, cap = entry[0], entry[1]
        wide = len(entry) > 2 and entry[2] == "wide"
        r = copy_img(rel, max_w=4000 if wide else 2400)
        if not r:
            figs.append(f'<p class="missing">Missing: {esc(rel)}</p>')
            continue
        src, w, h = r
        img = (f'<a href="{src}" target="_blank" rel="noopener"><img src="{src}" width="{w}" height="{h}" '
               f'loading="lazy" alt="{esc(cap or item["title"])}"></a>')
        if wide:
            img = f'<div class="wide">{img}</div>'
        figs.append('<figure>' + img + (f'<figcaption>{cap}</figcaption>' if cap else "") + '</figure>')
    note = f'<p class="note">{item["note"]}</p>' if item.get("note") else ""
    choices = item.get("choices")
    if choices:
        opts = "".join(
            f'<label class="choice"><input type="radio" name="pick-{item["id"]}" value="{esc(c)}" id="pick-{item["id"]}-{i}"> {esc(c)}</label>'
            for i, c in enumerate(choices))
        control = f'<fieldset class="pick" data-pick><legend>Your pick</legend>{opts}</fieldset>'
    else:
        control = ('<div class="verdict" role="group" aria-label="Verdict">'
                   '<button type="button" data-v="good">Looks good</button>'
                   '<button type="button" data-v="change">Needs changes</button></div>')
    return f'''<article class="item" data-id="{item["id"]}" id="item-{item["id"]}">
  <header><h3>{esc(item["title"])}</h3><span class="state" aria-live="polite"></span></header>
  {note}
  <div class="figs">{"".join(figs)}</div>
  <div class="feedback" hidden>
    {control}
    <label class="notes-label" for="note-{item["id"]}">Notes (optional)</label>
    <textarea id="note-{item["id"]}" rows="2" placeholder="What would you change?"></textarea>
  </div>
</article>'''


def build():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(IMG)
    swatches = "".join(f'<li><span class="sw" style="background:{c}"></span><span>{esc(n)}</span><code>{c}</code></li>'
                       for n, c in PALETTE)
    sections_html = []
    nav = []
    for s in SECTIONS:
        nav.append(f'<a href="#{s["id"]}">{esc(s["title"])}</a>')
        items = "".join(card(i) for i in s["items"])
        sections_html.append(f'<section id="{s["id"]}"><h2>{esc(s["title"])}</h2>'
                             f'<p class="intro">{s["intro"]}</p><div class="items">{items}</div></section>')
    with open(os.path.join(ROOT, "tools/review_template.html")) as fh:
        tpl = fh.read()
    page = (tpl.replace("{{NAV}}", "".join(nav))
               .replace("{{SWATCHES}}", swatches)
               .replace("{{SECTIONS}}", "".join(sections_html)))
    with open(os.path.join(OUT, "index.html"), "w") as fh:
        fh.write(page)
    total = sum(os.path.getsize(os.path.join(IMG, f)) for f in os.listdir(IMG))
    print(f"wrote {OUT}/index.html with {len(os.listdir(IMG))} images ({total / 1e6:.1f} MB)")


def define_items():
    add_section("layout", "Layout mockup", (
        "The whole tank is about three screens wide. The camera shows one screen's worth at a time and drifts "
        "slowly between the left, middle and right. These views are what the TV would show at each point."), [
        {"id": "layout-overview", "title": "Whole tank", "images": [
            ("mockup/overview.jpg", "Scroll sideways to see the whole tank. Solid outlines: what the TV shows at the left, middle and "
             "right. Dashed lines: how far the view drifts up and down on the Large drift setting.", "wide")],
         "note": '<span class="legend"><span><i style="border-color:#EBD27A"></i>Left view</span>'
                 '<span><i style="border-color:#E4E8EA"></i>Middle view</span>'
                 '<span><i style="border-color:#EB5E9E"></i>Right view</span>'
                 '<span><i class="dash" style="border-color:#9db4c6"></i>Large drift range</span></span>'},
        {"id": "view-left", "title": "TV view: left", "images": [("mockup/view_left.jpg", "")]},
        {"id": "view-middle", "title": "TV view: middle", "images": [("mockup/view_middle.jpg", "")]},
        {"id": "view-right", "title": "TV view: right", "images": [("mockup/view_right.jpg", "")]},
        {"id": "view-dim", "title": "Brightness cycle at its dimmest", "two": True,
         "note": "The middle view at the low point of the Standard brightness cycle (about 75%), with a faint evening tint.",
         "images": [("mockup/view_middle.jpg", "Full brightness"), ("mockup/view_middle_dim.jpg", "Dimmest point")]},
        {"id": "view-drift", "title": "Vertical drift", "two": True,
         "note": "The same spot with the camera drifted up (Normal setting) and down (Large setting). The gravel line and "
                 "water move so no edge stays on the same pixels.",
         "images": [("mockup/view_middle_drift_up.jpg", "Drifted up, Normal"),
                    ("mockup/view_middle_drift_down_large.jpg", "Drifted down, Large")]},
    ])
    add_section("fish", "Fish", (
        "Fish are drawn facing right; the Roku flips them to swim left. The tail is a separate piece so it can wag."), [
        {"id": "fish-clownfish", "title": "Clownfish", "images": [("fish_clownfish_preview.png", "On a checkerboard and on tank water, zoomed 2x")]},
        {"id": "fish-lionfish", "title": "Lionfish", "images": [("fish_lionfish_preview.png", "")]},
        {"id": "fish-tang", "title": "Tang, recolored four ways",
         "note": "One gray drawing, recolored on the Roku. This is how many color varieties come from a few drawings.",
         "images": [("fish_tang_base_preview.png", "Gray original, then yellow, purple, blue and orange")]},
        {"id": "fish-tetra", "title": "Neon tetra", "note": "Small school fish. They will swim in groups of 8 to 12.",
         "images": [("fish_neon_tetra_preview.png", "Zoomed 2x"), ("tetra_school_2x.png", "A school of ten next to a tang, zoomed 2x")]},
    ])
    add_section("critters", "Shrimp and crabs", "Bottom dwellers that walk along the gravel, rocks and the grotto's moss.", [
        {"id": "shrimp-colors", "title": "Neocaridina shrimp colors",
         "images": [("shrimp_base_preview.png", "Gray original, then cherry, sakura orange, yellow, blue dream, green jade and chocolate")]},
        {"id": "shrimp-rili", "title": "Rili shrimp", "images": [("shrimp_rili_preview.png", "Zoomed 2x")]},
        {"id": "crab", "title": "Crab", "note": "Seen from the front, because it walks sideways along the gravel.",
         "images": [("crab_preview.png", "Zoomed 2x")]},
    ])
    add_section("structures", "Castle, grotto and chest", (
        "The castle and grotto are drawn in a back piece and a front piece. Fish swim between the two, so they can "
        "pass through the doorway, behind windows and into the cave."), [
        {"id": "castle", "title": "Storybook castle", "two": True,
         "images": [("castle_whole_preview.png", "Whole castle"), ("castle_test_preview.png", "Swim-through test with a stand-in fish")]},
        {"id": "grotto", "title": "Mossy grotto", "two": True,
         "images": [("grotto_whole_preview.png", "Whole grotto"), ("grotto_test_preview.png", "Test with a stand-in fish and crab")]},
        {"id": "chest", "title": "Treasure chest", "two": True,
         "note": "Every few minutes the lid opens, lets out a burst of bubbles and a soft glow, then closes.",
         "images": [("chest_closed_preview.png", "Closed"), ("chest_open_preview.png", "Open")]},
    ])
    add_section("plants", "Plants, coral and anemone", "Each leaf is a separate piece so it can sway on its own.", [
        {"id": "plant-vallisneria", "title": "Vallisneria", "images": [("plant_vallisneria_preview.png", "")]},
        {"id": "plant-sword", "title": "Amazon sword", "images": [("plant_amazon_sword_preview.png", "")]},
        {"id": "coral", "title": "Coral cluster", "images": [("coral_cluster_preview.png", "")]},
        {"id": "anemone", "title": "Anemone", "note": "The clownfish stay close to it.", "images": [("anemone_preview.png", "")]},
    ])
    add_section("gravel", "Gravel", "Three color mixes for the gravel. The mockup above uses the pastel mix.", [
        {"id": "gravel-mix", "title": "Pick a gravel mix", "choices": ["Pastel mix", "Jewel tones", "Natural with color accents"],
         "images": [("textures/swatch_gravel_pastel.png", "Pastel mix"), ("textures/swatch_gravel_jewel.png", "Jewel tones"),
                    ("textures/swatch_gravel_natural.png", "Natural with color accents")]},
    ])


if __name__ == "__main__":
    define_items()
    build()
