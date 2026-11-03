# Aquarium Art Style Guide (Phase 0 draft)

All art for the screensaver follows this guide so that pieces drawn separately look like one tank.

## 1. Look

- **Illustrated storybook style:** clean shapes, bold but friendly outlines, flat color with simple cel shading. It should feel like a picture-book illustration, not a cartoon character sheet and not a photo.
- **Bright and saturated**, but no neon glare and **no pure white** (see §4).
- Creatures have **natural anatomy, simplified**: correct fin layout and body proportions for the species, with fewer details. Eyes are round with a pupil and a small highlight dot. **No smiles, eyebrows or human expressions.**
- Fish **face right** by default. The Roku flips them horizontally to swim left.
- **Light comes from above** (the water surface), slightly from the left. Tops of shapes are lighter, undersides darker.

## 2. Outline and line work

| Use | Width | Color |
|---|---|---|
| Large structures (castle, grotto, big rocks) | 4 px | `#2A2745` |
| Normal sprites (fish ≥ 120 px, crab, chest, coral, anemone, plants) | 3 px | `#2A2745` |
| Small sprites (tetra, shrimp, anything < 100 px) | 2 px | `#2A2745` |
| Inner detail lines (scales, fin rays, stone joints, moss texture) | 1.5–2 px | A darker shade of the local fill, never black |

- `stroke-linejoin="round"` and `stroke-linecap="round"` everywhere.
- Thin, transparent parts (fin membranes, lionfish spines) may use a thinner outline or none.

## 3. Shading

- **Three tones per surface:** base, shadow and highlight.
  - Shadow: about 25% darker than the base, shifted slightly toward blue or purple. Placed on the underside and the side away from the light.
  - Highlight: about 20% lighter than the base, on the top edge. It must stay under the brightness cap.
- Subtle linear gradients inside a shape are allowed (lighter at the top). Avoid photo-style airbrushing.
- Small soft glows are allowed using `feGaussianBlur`, sparingly.
- Transparent fins: base fill at 55–75% opacity.

## 4. Brightness cap (OLED)

- **No color channel above 235** (`#EB`) anywhere in the art. Pure white `#FFFFFF` is never used.
- The lightest allowed "white" is **soft white `#E4E8EA`**.
- `tools/render_svg.py` checks this on every render and reports `OVER CAP` if anything exceeds it.

## 5. Palette

All colors below are already under the cap. Stay close to them, and use darker or lighter shades of them for shading.

| Group | Colors |
|---|---|
| Outline & eyes | outline `#2A2745`, pupil `#1A1830`, soft white `#E4E8EA` |
| Water | deep `#0A2342`, mid `#134E78`, near surface `#2C86A6`, light ray `#8FD3E0` (low opacity only) |
| Warm brights | tangerine `#E8731C`, sunflower `#EBC42A`, coral red `#E0484D`, hot pink `#EB5E9E`, magenta `#C2378E` |
| Cool brights | royal purple `#7A3FC4`, lavender `#B9A2E0`, electric blue `#2E7DE0`, royal blue `#3F5FC4`, teal `#22B5A8`, aqua `#4FD1D9` |
| Greens | lime `#9CD43A`, leaf `#4FA83D`, deep green `#2E7A3A`, moss light `#A5D24C`, moss dark `#3E6E2E` |
| Stone & earth | sand `#D9C08E`, warm stone `#A8907A`, cool stone `#6F7A8C`, dark stone `#474F63`, wood `#8A5A3A`, dark wood `#5A3826` |
| Metal | gold `#E0B23A`, light gold `#EBD27A`, dark gold `#A87A1E` |
| Storybook castle | walls lavender `#B9A2E0`, pink `#E6A3C3`, mint `#9ED9C0`; roofs royal blue `#3F5FC4`, magenta `#C24A8E`; flags sunflower `#EBC42A`; doorway `#3A2A4A` |

## 6. Tintable sprites

Some sprites are drawn once in **grays** and colored on the Roku with `Poster.blendColor`, which **multiplies** each pixel by the tint color.

- Use only grays (and the outline color): base `#DADADA`, shadow `#A0A0A0`, highlight `#EAEAEA`, detail lines `#6A6A6A`.
- Pattern areas that should stay darker (stripes, spots) use darker grays.
- Preview with `--tint`, for example `--tint yellow=#EBD23A`.

**Tint sets**

| Sprite | Tints |
|---|---|
| Tang (base fish) | yellow `#EBD23A`, purple `#8E5BD8`, blue `#3F8EE6`, orange `#EB8A3A` |
| Neocaridina shrimp | cherry `#D8323A`, sakura `#EB7A2A`, yellow `#EBC82E`, blue dream `#2F6FD8`, green jade `#3FA860`, chocolate `#6A4A40` |

## 7. Sizes (main stage, 1080p pixels)

The SVG's `width` and `height` are the **final on-screen size in 1080p pixels** for the main stage, with a `viewBox` of the same size. Leave about 4–8 px of empty padding around the drawing.

| Sprite | Approximate size (w × h) |
|---|---|
| Neon tetra | 64 long |
| Clownfish | 150 long |
| Tang | 210 long |
| Lionfish (with fins) | 280 long |
| Neocaridina shrimp | body 64 long; canvas about 120 × 60 with antennae |
| Crab | 140 wide (leg span) × 90 tall |
| Treasure chest | 230 × 170 closed; open canvas about 230 × 250 |
| Anemone | 280 × 220 |
| Coral piece | about 300 × 260 |
| Plants | vallisneria clump about 220 × 620; Amazon sword about 360 × 460 |
| Castle | about 560 × 700 |
| Grotto | about 760 × 420 |

Depth layers reuse the same art at runtime: far layer about 0.55× with a blue tint, near layer about 1.35× (rendered from the SVG at the larger size so it stays sharp).

## 8. SVG rules

- Root: `<svg xmlns="http://www.w3.org/2000/svg" width="W" height="H" viewBox="0 0 W H">`. Transparent background.
- Allowed: `path`, `circle`, `ellipse`, `rect`, `polygon`, `polyline`, `g`, `defs`, `linearGradient`, `radialGradient`, `clipPath`, `mask`, `use`, and `filter` with `feGaussianBlur`.
- **Not allowed:** `<text>`, `<image>`, external references, `<style>` blocks or CSS classes. Use presentation attributes (`fill=`, `stroke=`).
- **Animation parts** are top-level groups with fixed ids and a pivot point, for example `<g id="tail" data-pivot="42 75">`. The build will later export each group as its own image.

| Sprite type | Group ids |
|---|---|
| Fish | `tail`, `body` (body includes head, eye and non-moving fins; draw `tail` first so the body overlaps it). Optional `fin-pectoral`. |
| Shrimp | `legs`, `body`, `antennae` |
| Crab | `legs-back`, `claw-left`, `body`, `claw-right`, `legs-front` |
| Chest | `base`, `lid` (with the hinge pivot) |
| Plants | one group per swaying frond/stem, each with a pivot at its base |
| Anemone | `base`, `tentacles` |
| Castle, grotto | Separate files: `<name>_back.svg` (drawn behind fish) and `<name>_front.svg` (drawn in front of fish), with **identical width, height and viewBox**, so stacking them gives the whole structure. |

- File names: `<category>_<name>.svg`, lowercase, in `art/samples/` for Phase 0.

## 9. Checking your work

```
python3 tools/render_svg.py render art/samples/fish_clownfish.svg --preview
python3 tools/render_svg.py render art/samples/fish_tang_base.svg --preview --tint yellow=#EBD23A --tint purple=#8E5BD8
python3 tools/render_svg.py compose castle_whole art/samples/castle_back.svg art/samples/castle_front.svg --preview
```

Output goes to `build/phase0/`. Open the `_preview.png` images to inspect the art on a checkerboard and on aquarium water.
