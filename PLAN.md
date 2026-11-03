# Roku Aquarium Screensaver — Development Plan (Draft)

Status: **planning — no code yet.** This document is meant to be revised as decisions are made.

## 0. Decisions So Far

| Topic | Decision |
|---|---|
| Distribution | **Personal use only.** Sideloaded through Roku developer mode onto the owner's own devices. No Channel Store submission and no signed package. |
| Devices | **Roku Ultra only.** Currently a **4660** and a **4800**. Any future devices will be newer Ultra generations. No sticks, TVs with Roku built in, or older boxes. |
| Art source | **SVG files authored in the repo**, rasterized to PNG by a build script. |
| Style | **Illustrated and colorful**, not photoreal. |
| Tank type | **Stylized mix.** Freshwater and saltwater fish, coral and plants together. The goal is an interesting scene with lots of motion, not species accuracy. |
| Brightness | **Slow brightness cycle** is in v1 (§4.5). |
| Extras | **Treasure chest**, **Neocaridina shrimp in several colors** and **one or two crabs** (§4.3). |
| Clock | **None.** The screen has no text or UI at all. |

## 1. Goals

- A Roku **screensaver** showing an animated, front-on view of a colorful aquarium.
- **Real-time rendering, not video.** Fish move on randomized paths, so it never visibly loops.
- **Full screen, no borders.** The tank fills the display edge to edge.
- **OLED-safe.** Over time every pixel changes. No static element stays put, including the gravel line and the water surface.
- The camera shows **part of a larger tank** and **pans slowly** across it.
- Content: many colorful fish, coral, plants, shrimp, crabs, a treasure chest and colorful gravel on the bottom.

### Non-goals (for v1)
- 3D rendering or a rotating camera. The view is always front-on, 2D with layered depth.
- Interaction such as feeding the fish. A screensaver exits on any key press.
- Sound. Screensavers are silent by convention.
- Channel Store publishing, certification, or support for non-Ultra devices.

## 2. Platform Overview

| Topic | Notes |
|---|---|
| Language / UI | BrightScript plus **SceneGraph** (XML components). |
| Screensaver entry | `manifest` declares `screensaver_title=...`. Roku calls `RunScreenSaver()`. An optional `RunScreenSaverSettings()` adds a settings screen. |
| Dev entry | We also provide `Main()` so the app can run as a normal channel. That makes iteration and debugging much faster. |
| Install | Developer mode allows **one sideloaded channel per device**. The aquarium takes that slot on each Ultra, and installing a different dev channel would replace it. Phase 0 confirms that a sideloaded channel can be chosen in Settings → Theme → Screensavers. |
| Resolution | Author at **FHD (1920×1080)** UI coordinates. Both Ultras output 4K and upscale the UI layer. Phase 0 checks whether FHD art looks soft on a 4K TV. Because the art is SVG, rendering it at 2× is just a build flag. |
| Rendering | Use `Poster` nodes (bitmaps) and `Rectangle`s. There is no vector or canvas API at runtime, so all art ships as PNG/JPG. |
| Animation | `Animation` + `Vector2DFieldInterpolator` / `FloatFieldInterpolator` run on the **render thread**, so motion is smooth without a per-frame BrightScript loop. |
| Performance floor | The **4660** is the older and weaker of the two devices, so all budgets are tuned on it. The 4800 will have headroom. **Texture memory** is still limited, so large bitmaps need tiling. |
| Debug | Developer mode with a web sideloader on port 80, telnet debug console on port 8085, and the VS Code "BrightScript Language" extension. |

## 3. Visual Design

### 3.1 The "world" vs. the "viewport"
- The **tank (world)** is larger than the screen: about **3× screen width × 1.15× screen height**, roughly 5760×1240 FHD units.
- The **viewport** is the 1920×1080 window the camera shows.
- The camera **never shows the edge of the world**, so no border ever appears.

### 3.2 Parallax layers (back to front)
| # | Layer | Contents | Parallax factor |
|---|---|---|---|
| 0 | Back water | Deep blue-to-teal vertical gradient and a hazy back wall | 0.3 |
| 1 | Far scenery | Silhouetted rocks and plants, desaturated and blue-tinted | 0.5 |
| 2 | Far fish | Small, tinted, slower fish | 0.55 |
| 3 | Mid scenery | Main coral, rocks, driftwood, anemones, swaying plants, shrimp on rocks and leaves | 0.8 |
| 4 | Mid fish | Most of the fish | 0.85 |
| 5 | Gravel bed | Multicolor pebbles with an uneven top edge, treasure chest, crabs, shrimp on the gravel | 1.0 |
| 6 | Near fish | A few large fish crossing close to the "glass" | 1.1 |
| 7 | Foreground plants | Partially out-of-focus plants at the bottom corners | 1.2 |
| 8 | Light overlay | Animated light rays and caustics, additive and semi-transparent | 0.9 |
| 9 | Brightness overlay | Full-screen dimming layer for the brightness cycle (§4.5). Not part of the parallax. | — |

Each layer is a `Group` whose translation equals `-camera × parallaxFactor`. Front-on parallax gives a sense of depth while the angle stays straight-on. Creatures that walk on scenery (shrimp, crabs) are children of the layer they walk on, so they move with it.

### 3.3 Art direction
- Bright, saturated palette with a clean, illustrated look. It reads well on TV and compresses well.
- **Stylized mix:** reef fish, freshwater fish, coral and planted-tank plants share the same tank. Pick species for color, shape and movement variety.
- **Fish are drawn in light neutral tones and tinted at runtime** with `Poster.blendColor`. A few base shapes × color palettes give many varieties at little memory cost. Fish with fixed patterns get dedicated art.
- Depth cue: far layers get smaller scale, blue tint, lower opacity and slower speed.
- Gravel: pastel and jewel-tone pebbles in a few repeating tiles with a randomized top silhouette.

**Candidate cast** (to be trimmed or added to):

| Group | Species / items | Art approach |
|---|---|---|
| Showpiece fish | Clownfish, blue tang, mandarin dragonet, royal gramma | Dedicated art (fixed patterns) |
| Tinted fish | Tang (yellow/purple), angelfish, discus, betta, fancy guppy, gourami, butterflyfish, puffer | One base shape each, several tints |
| Schools | Neon tetras, rasboras | Small dedicated sprite, schooling behavior |
| Oddballs | Seahorse near the plants (slow vertical bobbing) | Dedicated art |
| Bottom dwellers | Neocaridina shrimp, crabs | See §4.3 |
| Coral | Brain coral, staghorn, sea fan, anemone (sways, clownfish stay near it) | Dedicated art, some tinted |
| Plants | Vallisneria, Amazon sword, cabomba, java fern, moss on driftwood | Dedicated art, separate swaying segments |
| Decorations | Treasure chest, rocks, driftwood | Dedicated art |

### 3.4 Asset pipeline (decided: SVG)
- Source art lives in `art/` as **SVG**, one file per sprite or sprite part (for example a fish body and its tail are separate files so the tail can rock).
- A build script rasterizes SVG → PNG with **resvg**, which is fast and gives the same output every time. Output scale is a flag: 1× for FHD, or 2× if Phase 0 shows 4K art is worth it.
- Procedural textures (gravel tiles, background gradient, caustics) come from a small **Python + Pillow** script, so they can be regenerated with new colors or seeds.
- Generated PNGs go to `images/` and are **not committed**. The build recreates them, so the repo holds only sources.
- A short **style guide** (palette, outline weight, shading style, size per depth layer) is written before mass-producing art, so everything matches.

## 4. Motion & Behavior

### 4.1 Camera
- Slow, eased **side-to-side pan** across the world. One full sweep takes several minutes, with easeInOut at each end.
- Add a **slow vertical drift** of about ±60 px on a different, non-harmonic period. This is critical for OLED: horizontal panning alone does not move horizontal edges such as the gravel line, the water surface or coral tops.
- Very slow **zoom "breathing"** (scale 1.00–1.06) so that layer 0, which barely moves, still shifts.
- The path is effectively Lissajous-like with randomized periods, so it never settles into a repeating pattern.
- Implement it as a few long-running looping interpolators on the camera/layer groups. That costs zero per-frame script.

### 4.2 Fish
- Each fish follows a **waypoint wander** pattern:
  1. Pick a random target inside its depth band, biased toward horizontal travel (fish mostly swim sideways in a front-on view).
  2. Set up a `Vector2DFieldInterpolator` from the current position to the target. The duration comes from distance ÷ species speed (± jitter), with easeInOut.
  3. When the animation stops, an observer picks the next target. Occasionally the fish **hovers** or **reverses**.
- **Home anchors (optional per species):** some fish wander within a radius of a point instead of the whole tank. Clownfish stay near the anemone and the seahorse stays near the plants.
- **Turning:** when direction changes, a short `scale.x` animation from 1 to −1 makes the fish flip, which looks like turning toward or away from the viewer.
- **Swim cycle:** a separate tail `Poster` rocks via a `rotation` interpolator around the tail joint. Tail speed scales with swim speed.
- **Gentle bob:** small looping vertical offset on an inner group.
- **Schools:** small schooling species follow a leader with offsets and a little lag.
- Fish swim across the **whole world**, not only the viewport, so the visible population changes as the camera pans.
- Target count is about 25–40 fish across all depth bands, tuned on the 4660.
- BrightScript only runs when a fish finishes a segment, which is every few seconds per fish. The CPU cost is very low.

### 4.3 Bottom dwellers and decorations

**Walkable surfaces.** The tank layout defines **walk paths**: the top edge of the gravel, plus the tops of rocks, driftwood and some large leaves, each as a list of points. Shrimp and crabs move along these paths using multi-key `Vector2DFieldInterpolator`s, so they follow the surface without per-frame script.

**Neocaridina shrimp**
- About **10–16 shrimp** spread across the tank, small (roughly 50–70 px long at FHD) so they read as tiny details.
- **Colors** via tinting one light-toned base sprite: red cherry, orange sakura, yellow, blue dream, green jade and black/chocolate. Rili (partly clear with color patches) gets its own art.
- **Behavior:**
  - Crawl along a walk path, pause, and **graze**: a small head bob with fluttering front legs.
  - Antennae sway constantly via small rotation loops.
  - Now and then, swim a short arc to a different surface.
  - Rarely, a quick **backward flick** (the shrimp escape move), then settle.
- Some shrimp live on the gravel layer and some on the mid-scenery layer, so they appear at two depths.

**Crabs**
- **One or two crabs** on the gravel layer, in stylized red/orange plus one optional tinted color.
- **Behavior:**
  - Walk **sideways** along the gravel. Legs animate with small looping rotations.
  - Pause, open and close claws, sometimes raise both claws.
  - Occasionally scuttle quickly.
  - Now and then walk behind the treasure chest or a rock and come out somewhere else, which keeps the scene changing.

**Treasure chest**
- Sits on the gravel, slightly tilted and half buried.
- Every few minutes (randomized), the **lid opens** on its hinge, releases a **burst of bubbles** and a brief soft glow, then closes.
- The glow is short and low-brightness, so it doesn't create a bright static spot.

### 4.4 Ambient life
- **Plants sway:** stems or fronds rotate gently around their base (`scaleRotateCenter`) with random phase and period.
- **Bubbles:** one or two bubblers plus the treasure chest emit bubbles that rise with slight wobble, recycled from a shared pool of Posters.
- **Light rays:** a few large, soft, semi-transparent shafts slowly drift and fade.
- **Caustics:** a tiling caustic texture at low opacity, slowly translated over the scene and gravel.
- **Water surface:** an optional faint shimmering band at the top that moves with the camera's vertical drift.
- **Anemone:** tentacles pulse and sway, with clownfish swimming around it.

### 4.5 Slow brightness cycle
- The whole scene gets gradually brighter and dimmer, like a tank over a day. This also spreads wear across the screen over time, because pixel brightness changes.
- **Range:** about 100% down to about 75% brightness (final values tuned on the actual TV). It never goes fully dark, so it stays pleasant as a screensaver.
- **Period:** about 20–40 minutes per full cycle, with a smooth sine-style ease so there is no visible step. The period is randomized slightly each cycle.
- **Implementation:** one full-screen black `Rectangle` at the top of the scene, with its `opacity` animated between 0.0 and about 0.25 by a looping `FloatFieldInterpolator`. This runs on the render thread, so it costs almost no script time.
- **Color shift (optional):** during the dim phase, add a faint blue-to-teal tint overlay, so it feels like evening light rather than just a darker picture.
- **Light rays and caustics** can fade with the cycle, so the "sun" dims along with the scene.
- **Settings (Phase 8):** on/off, dimming depth (subtle / medium / deep) and cycle length.

## 5. OLED Safety Checklist

- [ ] No static UI: no logos, clocks or text.
- [ ] Every layer, including the background gradient, moves (camera parallax plus vertical drift plus zoom breathing).
- [ ] Horizontal features (gravel line, surface) move **vertically** over time.
- [ ] Vertical features (plant stems, rock edges) move **horizontally** over time.
- [ ] Avoid large areas of pure white or max-brightness color. Highlights, including the chest glow, stay soft, brief and moving.
- [ ] Slow global **brightness cycle** (§4.5): about 100% to 75% over a 20–40 minute period, via a top-level overlay.
- [ ] Verification: capture screenshots over time with the Roku developer screenshot utility, then compute per-pixel variance offline to confirm that no region stays static.

## 6. Architecture

```
roku_aquarium/
├── manifest                    # title, screensaver_title, icons, ui_resolutions=fhd
├── source/
│   └── main.brs                # Main() (dev channel), RunScreenSaver(), RunScreenSaverSettings()
├── components/
│   ├── AquariumScene.xml/.brs  # root Scene: builds layers, owns camera
│   ├── Camera.brs              # pan/drift/zoom animations
│   ├── Layer.xml/.brs          # parallax group
│   ├── Fish.xml/.brs           # one fish: body+tail posters, wander logic, turning
│   ├── School.xml/.brs         # leader/follower group of small fish
│   ├── Shrimp.xml/.brs         # walk-path crawling, grazing, hops
│   ├── Crab.xml/.brs           # sideways walking, claw gestures, hiding
│   ├── TreasureChest.xml/.brs  # lid open/close, bubble burst, glow
│   ├── Plant.xml/.brs          # swaying plant
│   ├── BubbleEmitter.xml/.brs  # pooled bubbles
│   ├── LightRays.xml/.brs      # light shafts + caustics
│   ├── Brightness.xml/.brs     # brightness cycle overlay
│   └── Settings*.xml/.brs      # screensaver settings UI
├── data/
│   ├── species.json            # fish, shrimp, crab: art, size, speed, depth band, palettes, anchors
│   └── tank_layout.json        # scenery placement per layer + walk paths
├── art/                        # source SVGs + style guide
├── images/                     # build output: PNGs (generated, not committed)
└── tools/
    ├── build_assets.*          # rasterize SVG → PNG (resvg), generate gravel/caustics (Pillow)
    └── deploy.*                # build, zip and sideload to one or both Ultras
```

Key design choices:
- **Data-driven species and scenery** (JSON) so new fish, shrimp colors or coral do not require code changes.
- **Seeded randomness:** scenery details and starting positions come from a seed at startup, so each session looks a little different. A fixed seed is available for debugging.
- **Single performance profile** tuned on the 4660. A "more fish" option for the 4800 and newer Ultras can come later if wanted.
- **Device config:** IP addresses and the developer-mode password for each Ultra live in a local, **git-ignored** config file that the deploy script reads. Nothing secret is committed.

## 7. Phased Roadmap

| Phase | Deliverable | Exit criteria |
|---|---|---|
| **0. Spikes** | (a) Performance test: N animated Posters with interpolators on the **4660**. (b) Confirm a sideloaded channel can be selected as the screensaver, and that settings work. (c) Find the texture memory ceiling on the 4660. (d) Check FHD vs. 2× art on the 4K TV. | Fish/layer budget known, screensaver install confirmed, art resolution decided. |
| **1. Skeleton** | Manifest, `Main()` + `RunScreenSaver()`, empty full-screen Scene, build and deploy scripts for both Ultras. | Sideloads to both devices, runs as channel and as screensaver. |
| **2. World & camera** | Placeholder colored layers in the world, parallax groups, pan + vertical drift + zoom. | Smooth pan with no edges visible at any point in the cycle. |
| **3. Scenery art & pipeline** | Style guide, SVG → PNG pipeline, back gradient, rocks, coral, plants, driftwood, gravel tiles, treasure chest (static). | Tank looks "full" and colorful at any camera position. |
| **4. Fish** | Species data, wander behavior, home anchors, turning, tail animation, depth bands, schools. | 30+ fish swimming naturally at a solid frame rate on the 4660. |
| **5. Bottom dwellers & chest** | Walk paths, shrimp (all colors), crabs, treasure chest lid and bubble burst. | Shrimp and crabs move believably along surfaces. Chest opens on a random timer. |
| **6. Ambient effects** | Plant sway, anemone, bubbles, light rays, caustics. | Scene feels alive and stays within the performance budget. |
| **7. OLED hardening** | Checklist in §5, brightness cycle (§4.5), pixel-variance test. | No static region across a 30-minute capture. |
| **8. Settings & polish** | Settings screen (fish count, shrimp/crab on/off, pan speed, effects on/off, brightness cycle). Icons and splash. | Settings persist via `roRegistrySection`. |
| **9. Install & docs** | README with developer-mode setup, one-command build + deploy to both Ultras. | A fresh Ultra can be set up from the README in a few minutes. |

Optional **Phase 0.5:** a quick browser (HTML canvas) prototype to tune the motion "feel" (pan speed, wander, schooling, shrimp grazing) before porting the constants to BrightScript. It is cheap, but it duplicates logic, so it is only worth doing if tuning on device turns out slow.

## 8. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Performance on the 4660 | Render-thread interpolators instead of per-frame script, pooled nodes, few large alpha-blended overlays. Test on the 4660 from Phase 0 onward. |
| Texture memory limits with a 3×-wide world | Tile large layers into ≤1920-px-wide chunks. Reuse tinted sprites. Use JPG for opaque backgrounds. |
| Developer mode allows only one sideloaded channel, and a factory reset or disabling dev mode removes it | Keep a one-command deploy script and README so reinstalling takes a minute. |
| A Roku OS update changes how sideloaded screensavers work | Confirm in Phase 0, and re-check after OS updates. |
| Art quality / consistency | One style guide and one source format (SVG). Build the pipeline before mass-producing assets. |
| Visible looping or repetition | Randomized waypoints, non-harmonic camera periods, random chest timer, seeded layout variation per session. |

## 9. Open Questions

1. **TV:** is the TV 4K, and is it OLED? This affects the art resolution decision and how the brightness cycle is tuned.
2. **Cast:** any must-have fish, or any in the candidate list (§3.3) you'd rather leave out?
3. **More decorations:** anything beyond the treasure chest, such as a sunken ship, a small castle or a diver figure?
4. **Settings:** which user-adjustable options matter to you? The Phase 8 list is a starting point.
