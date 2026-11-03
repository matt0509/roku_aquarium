# Roku Aquarium Screensaver — Development Plan (Draft)

Status: **planning — no code yet.** This document is meant to be revised as decisions are made.

## 0. Decisions So Far

| Topic | Decision |
|---|---|
| Distribution | **Personal use only.** Sideloaded through Roku developer mode onto the owner's own devices. No Channel Store submission and no signed package. |
| Devices | **Roku Ultra only.** Currently a **4660** and a **4800**. Any future devices will be newer Ultra generations. No sticks, TVs with Roku built in, or older boxes. |
| Displays | **All 4K TVs.** |
| Art source | **SVG files authored in the repo**, rasterized to PNG by a build script. |
| Style | **Illustrated and colorful**, not photoreal. |
| Tank type | **Stylized mix.** Freshwater and saltwater fish, coral and plants together. The goal is an interesting scene with lots of motion, not species accuracy. |
| Fish | No required species. Favor **brightly colored or interestingly shaped** fish. Include **one or two clownfish**. |
| Extras | **Treasure chest**, **castle**, **grotto** (fish swim in and out, crabs hide under it), **Neocaridina shrimp in several colors**, **one or two crabs** (§4.3). |
| Clock | **None.** The screen has no text or UI at all. |
| Brightness | **Slow brightness cycle** is in v1 (§4.5). |
| Options screen | Yes. It includes the OLED protection options that change the look (§5, §4.6). |

## 1. Goals

- A Roku **screensaver** showing an animated, front-on view of a colorful aquarium.
- **Real-time rendering, not video.** Fish move on randomized paths, so it never visibly loops.
- **Full screen, no borders.** The tank fills the display edge to edge.
- **OLED-safe.** Over time every pixel changes. No static element stays put, including the gravel line and the water surface.
- The camera shows **part of a larger tank** and **pans slowly** across it.
- Content: many colorful fish, coral, plants, shrimp, crabs, a castle, a grotto, a treasure chest and colorful gravel on the bottom.

### Non-goals (for v1)
- 3D rendering or a rotating camera. The view is always front-on, 2D with layered depth.
- Interaction such as feeding the fish. A screensaver exits on any key press.
- Sound. Screensavers are silent by convention.
- Channel Store publishing, certification, or support for non-Ultra devices.

## 2. Platform Overview

| Topic | Notes |
|---|---|
| Language / UI | BrightScript plus **SceneGraph** (XML components). |
| Screensaver entry | `manifest` declares `screensaver_title=...`. Roku calls `RunScreenSaver()`. `RunScreenSaverSettings()` provides the options screen. |
| Dev entry | We also provide `Main()` so the app can run as a normal channel. That makes iteration and debugging much faster. |
| Install | Developer mode allows **one sideloaded channel per device**. The aquarium takes that slot on each Ultra, and installing a different dev channel would replace it. Phase 0 confirms that a sideloaded channel can be chosen in Settings → Theme → Screensavers. |
| Resolution | Roku app graphics are drawn at **1080p at most**, even on 4K players (the highest manifest UI option is `fhd`). The Roku then upscales to 4K. So art is made for **1920×1080**. Clean illustrated art with smooth shapes upscales well, which is one more reason for the SVG style. Phase 0 checks this on the 4K TVs. |
| Rendering | Use `Poster` nodes (bitmaps) and `Rectangle`s. There is no vector or canvas API at runtime, so all art ships as PNG/JPG. |
| Animation | `Animation` + `Vector2DFieldInterpolator` / `FloatFieldInterpolator` run on the **render thread**, so motion is smooth without a per-frame BrightScript loop. |
| Performance floor | The **4660** is the older and weaker of the two devices, so all budgets are tuned on it. The 4800 will have headroom. **Texture memory** is still limited, so large bitmaps need tiling. |
| Debug | Developer mode with a web sideloader on port 80, telnet debug console on port 8085, and the VS Code "BrightScript Language" extension. |

## 3. Visual Design

### 3.1 The "world" vs. the "viewport"
- The **tank (world)** is larger than the screen: about **3× screen width × 1.3× screen height**, roughly 5760×1400 FHD units. The extra height leaves room for the larger vertical drift option (§5).
- The **viewport** is the 1920×1080 window the camera shows.
- The camera **never shows the edge of the world**, so no border ever appears.

### 3.2 Parallax layers (back to front)
| # | Layer | Contents | Parallax factor |
|---|---|---|---|
| 0 | Back water | Deep blue-to-teal vertical gradient and a hazy back wall | 0.3 |
| 1 | Far scenery | Silhouetted rocks, plants and a far gravel strip, desaturated and blue-tinted | 0.5 |
| 2 | Far fish | Small, tinted, slower fish | 0.55 |
| 3 | Main stage, back | Main gravel strip, coral, rocks, driftwood, plants, anemone, **back and interior parts** of the castle and grotto, treasure chest, crabs, shrimp | 0.85 |
| 4 | Mid fish | Most of the fish | 0.85 |
| 5 | Main stage, front | **Front parts** of the castle (front wall, door arch, window frames) and grotto (overhang), plus a few plants that fish pass behind | 0.85 |
| 6 | Front gravel | A narrow strip of gravel at the bottom edge, with a few shrimp | 1.0 |
| 7 | Near fish | A few large fish crossing close to the "glass" | 1.1 |
| 8 | Foreground plants | Partially out-of-focus plants at the bottom corners | 1.2 |
| 9 | Light overlay | Animated light rays and caustics, additive and semi-transparent | 0.9 |
| 10 | Brightness overlay | Full-screen dimming layer for the brightness cycle and fade-to-black (§4.5, §4.6). Not part of the parallax. | — |

Each layer is a `Group` whose translation equals `-camera × parallaxFactor`. Front-on parallax gives a sense of depth while the angle stays straight-on.

Two rules keep the parallax from looking wrong:
- **Anything resting on gravel shares that gravel strip's parallax factor**, so objects don't appear to slide across the ground as the camera pans. That's why the gravel is split into strips at different depths.
- **The castle, grotto and mid fish share one factor (0.85).** Fish can then swim *through* the castle door or *into* the grotto: the back of the structure is drawn behind the fish and the front is drawn in front of them, and the pieces line up at every camera position.

Creatures that walk on scenery (shrimp, crabs) are children of the layer they walk on, so they move with it.

### 3.3 Art direction
- Bright, saturated palette with a clean, illustrated look. It reads well on TV and compresses well.
- **Stylized mix:** reef fish, freshwater fish, coral and planted-tank plants share the same tank.
- **Fish selection:** brightly colored or interestingly shaped species, with a variety of body shapes and swimming styles so the screen stays lively.
- **Fish are drawn in light neutral tones and tinted at runtime** with `Poster.blendColor`. A few base shapes × color palettes give many varieties at little memory cost. Fish with fixed patterns get dedicated art.
- **No pure white or maximum-brightness colors** in the art. The brightest highlights (bubbles, fish highlights, the chest glow) are capped at a soft, slightly tinted light tone. This barely changes the look, and it's kinder to OLED (§5).
- Depth cue: far layers get smaller scale, blue tint, lower opacity and slower speed.
- Gravel: pastel and jewel-tone pebbles in a few repeating tiles with a randomized top silhouette.

**Candidate cast** (to be trimmed or added to):

| Group | Species / items | Why | Art approach |
|---|---|---|---|
| Bright showpieces | **Clownfish (×2)**, blue tang, mandarin dragonet, royal gramma, flame angelfish | Vivid colors and patterns | Dedicated art |
| Interesting shapes | Lionfish, Moorish idol, yellow boxfish, freshwater angelfish, betta, puffer, seahorse | Unusual silhouettes and slow, showy movement | Dedicated art, some tinted |
| Tinted varieties | Tangs (yellow, purple), discus, fancy guppies, butterflyfish | Many colors from a few base shapes | One base shape each, several tints |
| Schools | Neon tetras, cardinal tetras, rasboras | Lots of small coordinated motion | Small dedicated sprite, schooling behavior |
| Bottom dwellers | Neocaridina shrimp, crabs | See §4.3 | Tinted shrimp base, dedicated crab art |
| Coral | Brain coral, staghorn, sea fan, anemone (sways, clownfish stay near it) | Color and shape | Dedicated art, some tinted |
| Plants | Vallisneria, Amazon sword, cabomba, java fern, moss on driftwood | Gentle motion | Separate swaying segments |
| Structures | Castle, grotto, treasure chest, rocks, driftwood | Places to swim through and hide | Split into back and front pieces where fish pass through |

### 3.4 Asset pipeline (decided: SVG)
- Source art lives in `art/` as **SVG**, one file per sprite or sprite part (for example a fish body and its tail are separate files so the tail can rock, and the castle front and back are separate files).
- A build script rasterizes SVG → PNG with **resvg**, which is fast and gives the same output every time. Output is sized for the 1080p graphics plane.
- Procedural textures (gravel tiles, background gradient, caustics) come from a small **Python + Pillow** script, so they can be regenerated with new colors or seeds.
- Generated PNGs go to `images/` and are **not committed**. The build recreates them, so the repo holds only sources.
- A short **style guide** (palette, brightness cap, outline weight, shading style, size per depth layer) is written before mass-producing art, so everything matches.

## 4. Motion & Behavior

### 4.1 Camera
- Slow, eased **side-to-side pan** across the world. One full sweep takes several minutes, with easeInOut at each end.
- A **slow vertical drift** on a different, non-harmonic period. Horizontal panning alone does not move horizontal edges such as the gravel line, the water surface or coral tops, so this matters for OLED. The drift amount is an option (§5).
- Optional very slow **zoom "breathing"** (scale 1.00–1.06) so that layer 0, which barely moves, still shifts.
- The path is effectively Lissajous-like with randomized periods, so it never settles into a repeating pattern.
- Implement it as a few long-running looping interpolators on the camera/layer groups. That costs zero per-frame script.

### 4.2 Fish
- Each fish follows a **waypoint wander** pattern:
  1. Pick a random target inside its depth band, biased toward horizontal travel (fish mostly swim sideways in a front-on view).
  2. Set up a `Vector2DFieldInterpolator` from the current position to the target. The duration comes from distance ÷ species speed (± jitter), with easeInOut.
  3. When the animation stops, an observer picks the next target. Occasionally the fish **hovers** or **reverses**.
- **Home anchors (optional per species):** some fish wander within a radius of a point instead of the whole tank. Clownfish stay near the anemone and the seahorse stays near the plants.
- **Swim-through routes:** the layout defines short routes through the castle door and windows and into and out of the grotto. Mid-layer fish sometimes take one of these routes instead of a random waypoint (§4.3).
- **Turning:** when direction changes, a short `scale.x` animation from 1 to −1 makes the fish flip, which looks like turning toward or away from the viewer.
- **Swim cycle:** a separate tail `Poster` rocks via a `rotation` interpolator around the tail joint. Tail speed scales with swim speed.
- **Gentle bob:** small looping vertical offset on an inner group.
- **Schools:** small schooling species follow a leader with offsets and a little lag.
- Fish swim across the **whole world**, not only the viewport, so the visible population changes as the camera pans.
- Target count is about 25–40 fish across all depth bands, tuned on the 4660.
- BrightScript only runs when a fish finishes a segment, which is every few seconds per fish. The CPU cost is very low.

### 4.3 Structures, bottom dwellers and decorations

**Walkable surfaces.** The tank layout defines **walk paths**: the top edge of the gravel, plus the tops of rocks, driftwood, the grotto and some large leaves, each as a list of points. Shrimp and crabs move along these paths using multi-key `Vector2DFieldInterpolator`s, so they follow the surface without per-frame script.

**Castle**
- A colorful, storybook-style castle on the main gravel strip, with turrets, an arched doorway and a couple of windows.
- Drawn in **back and front pieces**, so fish can swim **in through the doorway and out the other side** or pass behind a window.
- The tallest turret can double as a **bubbler**, sending a stream of bubbles up from the top.

**Grotto**
- A rock arch or small cave with a dark interior and an overhang, partly covered in moss and small plants.
- Fish **swim in and out**. As a fish enters, its color is gently darkened (a `blendColor` tween), so it looks like it's in shadow, and it brightens again as it comes out.
- Crabs **hide under the overhang**, sometimes with just their eyes or claws showing, then come back out.
- Shrimp can graze on the grotto's top surface.

**Neocaridina shrimp**
- About **10–16 shrimp** spread across the tank, small (roughly 50–70 px long at FHD) so they read as tiny details.
- **Colors** via tinting one light-toned base sprite: red cherry, orange sakura, yellow, blue dream, green jade and black/chocolate. Rili (partly clear with color patches) gets its own art.
- **Behavior:**
  - Crawl along a walk path, pause, and **graze**: a small head bob with fluttering front legs.
  - Antennae sway constantly via small rotation loops.
  - Now and then, swim a short arc to a different surface.
  - Rarely, a quick **backward flick** (the shrimp escape move), then settle.
- Most shrimp live on the main stage and a few on the front gravel strip, so they appear at two depths.

**Crabs**
- **One or two crabs** on the main gravel strip, in stylized red/orange plus one optional tinted color.
- **Behavior:**
  - Walk **sideways** along the gravel. Legs animate with small looping rotations.
  - Pause, open and close claws, sometimes raise both claws.
  - Occasionally scuttle quickly.
  - Now and then duck **under the grotto** or behind the chest or castle, wait, then come out, sometimes somewhere else.

**Treasure chest**
- Sits on the gravel, slightly tilted and half buried.
- Every few minutes (randomized), the **lid opens** on its hinge, releases a **burst of bubbles** and a brief soft glow, then closes.
- The glow is short and low-brightness, so it doesn't create a bright static spot.

### 4.4 Ambient life
- **Plants sway:** stems or fronds rotate gently around their base (`scaleRotateCenter`) with random phase and period.
- **Bubbles:** the castle turret, one other bubbler and the treasure chest emit bubbles that rise with slight wobble, recycled from a shared pool of Posters.
- **Light rays:** a few large, soft, semi-transparent shafts slowly drift and fade.
- **Caustics:** a tiling caustic texture at low opacity, slowly translated over the scene and gravel.
- **Water surface:** an optional faint shimmering band at the top that moves with the camera's vertical drift.
- **Anemone:** tentacles pulse and sway, with clownfish swimming around it.

### 4.5 Slow brightness cycle
- The whole scene gets gradually brighter and dimmer, like a tank over a day.
- **Depth (option):** Off / Subtle (down to about 85%) / Medium (about 75%) / Deep (about 60%). It never goes fully dark.
- **Cycle length (option):** about 20–40 minutes per full cycle by default, with a smooth sine-style ease so there is no visible step. The period is randomized slightly each cycle.
- **Implementation:** the full-screen black `Rectangle` on layer 10, with its `opacity` animated by a looping `FloatFieldInterpolator`. This runs on the render thread, so it costs almost no script time.
- **Color shift (optional):** during the dim phase, add a faint blue-to-teal tint overlay, so it feels like evening light rather than just a darker picture.
- **Light rays and caustics** fade with the cycle, so the "sun" dims along with the scene.

### 4.6 Fade to black (option)
- After a chosen time (Never / 1 h / 2 h / 4 h), the scene slowly fades to **full black** over about a minute, using the same overlay as the brightness cycle.
- On an OLED, black means the pixels are off, so this is the same as the screen resting.
- Any remote button still exits the screensaver as normal.

## 5. OLED Protection

### 5.1 What causes burn-in
OLED pixels wear a little each time they light up, and brighter colors wear them faster. Burn-in happens when some pixels wear much more than their neighbors. The classic case is a static logo or a news ticker that sits in the same spot for hundreds of hours and leaves a sharp-edged ghost.

The design avoids this by keeping everything moving, so no hard-edged shape stays in one place. One limit to be honest about: even in a moving scene, the top of the screen is mostly water and the bottom is mostly gravel. Over a very long time, those regions can wear slightly differently. That kind of wear is soft-edged and much less visible than a burned-in logo, and the TV's own **pixel refresh** routine is designed to even it out. The larger drift, brightness cycle and fade-to-black options reduce it further.

### 5.2 Always on (little or no visible effect)

| Measure | What it does | Effect on look and feel |
|---|---|---|
| Camera pan | Moves every vertical edge across the screen | Core to the design |
| Small vertical drift (±60 px) | Moves the gravel line, water surface and coral tops up and down | Barely noticeable, slow framing change |
| No static UI | No logos, clock or text | None |
| Brightness cap in the art | No pure white or maximum-brightness colors | Highlights are a touch softer; colors stay vivid |
| Moving light effects | Light rays, caustics and glows always drift and fade | None; they look better moving anyway |

### 5.3 Options screen: OLED settings that change the look

| Option | Choices | Protection | Effect on look and feel |
|---|---|---|---|
| **Brightness cycle** (§4.5) | Off / Subtle / **Medium** / Deep, plus cycle length | Lowers average brightness and wear | Scene slowly dims and brightens like day and evening. Deep is clearly darker at the low point. |
| **Vertical drift** | **Normal (±60 px)** / Large (±160 px) | Spreads the gravel and water bands over a wider area | At times you see more gravel, at times more open water. The view feels like it's slowly "bobbing". |
| **Zoom breathing** | **On** / Off | Shifts even the slow back layers | Very slow push-in and pull-out. Edges can look very slightly softer while zoomed. |
| **Fade to black** (§4.6) | **Never** / 1 h / 2 h / 4 h | Strongest protection for long idle times | The aquarium eventually goes dark until you press a button. |

A **preset** sets these in one step, and each one can still be changed on its own:
- **Standard** (default, bold above): Medium brightness cycle, normal drift, zoom on, no fade to black.
- **Maximum:** Deep brightness cycle, large drift, zoom on, fade to black after 2 h.

### 5.4 Leave the TV's own protection on
OLED TVs have their own features such as pixel shift, static-logo dimming and pixel refresh. Keep them enabled. Because the scene is always moving, the TV's static-logo dimming shouldn't kick in and dull the picture.

### 5.5 Checklist
- [ ] No static UI: no logos, clocks or text.
- [ ] Every layer, including the background gradient, moves (camera parallax plus vertical drift plus optional zoom).
- [ ] Horizontal features (gravel line, surface) move **vertically** over time.
- [ ] Vertical features (plant stems, rock edges, castle walls) move **horizontally** over time.
- [ ] Art follows the brightness cap. Highlights, including the chest glow, stay soft, brief and moving.
- [ ] Brightness cycle, drift, zoom and fade-to-black options all work and are saved.
- [ ] Verification: capture screenshots over time with the Roku developer screenshot utility, then compute per-pixel variance and per-region average brightness offline. Confirm that no region stays static and that no sharp-edged pattern builds up.

## 6. Options Screen

Shown from Settings → Theme → Screensavers → Aquarium → Custom settings (via `RunScreenSaverSettings()`). It's a simple list navigated with the remote, and choices are saved with `roRegistrySection`.

| Section | Option | Choices |
|---|---|---|
| Tank | Fish count | Fewer / **Normal** / More |
| Tank | Shrimp and crabs | **On** / Off |
| Tank | Pan speed | Slow / **Normal** / Fast |
| Tank | Light rays and caustics | **On** / Off |
| OLED protection | Preset | **Standard** / Maximum / Custom |
| OLED protection | Brightness cycle | Off / Subtle / **Medium** / Deep |
| OLED protection | Cycle length | 20 / **30** / 45 / 60 min |
| OLED protection | Vertical drift | **Normal** / Large |
| OLED protection | Zoom breathing | **On** / Off |
| OLED protection | Fade to black | **Never** / 1 h / 2 h / 4 h |

Changing any individual OLED option switches the preset to Custom. "More" fish is only offered up to what the 4660 handles smoothly (decided in Phase 0).

## 7. Architecture

```
roku_aquarium/
├── manifest                    # title, screensaver_title, icons, ui_resolutions=fhd
├── source/
│   └── main.brs                # Main() (dev channel), RunScreenSaver(), RunScreenSaverSettings()
├── components/
│   ├── AquariumScene.xml/.brs  # root Scene: builds layers, owns camera
│   ├── Camera.brs              # pan/drift/zoom animations
│   ├── Layer.xml/.brs          # parallax group
│   ├── Fish.xml/.brs           # one fish: body+tail posters, wander logic, routes, turning
│   ├── School.xml/.brs         # leader/follower group of small fish
│   ├── Shrimp.xml/.brs         # walk-path crawling, grazing, hops
│   ├── Crab.xml/.brs           # sideways walking, claw gestures, hiding
│   ├── Structure.xml/.brs      # castle / grotto: back + front pieces, swim-through routes, hiding spots
│   ├── TreasureChest.xml/.brs  # lid open/close, bubble burst, glow
│   ├── Plant.xml/.brs          # swaying plant
│   ├── BubbleEmitter.xml/.brs  # pooled bubbles
│   ├── LightRays.xml/.brs      # light shafts + caustics
│   ├── Brightness.xml/.brs     # brightness cycle + fade-to-black overlay
│   └── Settings*.xml/.brs      # options screen
├── data/
│   ├── species.json            # fish, shrimp, crab: art, size, speed, depth band, palettes, anchors
│   └── tank_layout.json        # scenery placement per layer, walk paths, swim-through routes
├── art/                        # source SVGs + style guide
├── images/                     # build output: PNGs (generated, not committed)
└── tools/
    ├── build_assets.*          # rasterize SVG → PNG (resvg), generate gravel/caustics (Pillow)
    ├── oled_check.*            # per-pixel variance / regional brightness from screenshots
    └── deploy.*                # build, zip and sideload to one or both Ultras
```

Key design choices:
- **Data-driven species and scenery** (JSON) so new fish, shrimp colors or structures do not require code changes.
- **Seeded randomness:** scenery details and starting positions come from a seed at startup, so each session looks a little different. A fixed seed is available for debugging.
- **Single performance profile** tuned on the 4660. The 4800 runs the same build.
- **Device config:** IP addresses and the developer-mode password for each Ultra live in a local, **git-ignored** config file that the deploy script reads. Nothing secret is committed.

## 8. Phased Roadmap

| Phase | Deliverable | Exit criteria |
|---|---|---|
| **0. Spikes** | (a) Performance test: N animated Posters with interpolators on the **4660**. (b) Confirm a sideloaded channel can be selected as the screensaver and that its settings screen opens. (c) Find the texture memory ceiling on the 4660. (d) Confirm 1080p illustrated art looks good upscaled on the 4K TVs. | Fish/layer budget known, screensaver install confirmed, art size confirmed. |
| **1. Skeleton** | Manifest, `Main()` + `RunScreenSaver()`, empty full-screen Scene, build and deploy scripts for both Ultras. | Sideloads to both devices, runs as channel and as screensaver. |
| **2. World & camera** | Placeholder colored layers in the world, parallax groups, pan + vertical drift + zoom. | Smooth pan with no edges visible at any point in the cycle, at both drift settings. |
| **3. Scenery art & pipeline** | Style guide, SVG → PNG pipeline, back gradient, gravel strips, rocks, coral, plants, driftwood, castle, grotto, treasure chest (static). | Tank looks "full" and colorful at any camera position. Castle and grotto line up across layers. |
| **4. Fish** | Species data, wander behavior, home anchors, swim-through routes, turning, tail animation, depth bands, schools. | 30+ fish swimming naturally on the 4660, some passing through the castle and grotto. |
| **5. Bottom dwellers & chest** | Walk paths, shrimp (all colors), crabs with grotto hiding, treasure chest lid and bubble burst. | Shrimp and crabs move believably along surfaces. Chest opens on a random timer. |
| **6. Ambient effects** | Plant sway, anemone, bubbles (castle, bubbler, chest), light rays, caustics. | Scene feels alive and stays within the performance budget. |
| **7. OLED protection** | Brightness cycle, fade to black, drift and zoom options, checklist in §5.5, screenshot analysis tool. | No static region across a 30-minute capture at Standard settings. |
| **8. Options screen & polish** | Options screen (§6), presets, saved settings, icons and splash. | Every option takes effect the next time the screensaver starts. |
| **9. Install & docs** | README with developer-mode setup, one-command build + deploy to both Ultras. | A fresh Ultra can be set up from the README in a few minutes. |

Optional **Phase 0.5:** a quick browser (HTML canvas) prototype to tune the motion "feel" (pan speed, wander, schooling, shrimp grazing) before porting the constants to BrightScript. It is cheap, but it duplicates logic, so it is only worth doing if tuning on device turns out slow.

## 9. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Performance on the 4660 | Render-thread interpolators instead of per-frame script, pooled nodes, few large alpha-blended overlays. Test on the 4660 from Phase 0 onward. |
| Texture memory limits with a 3×-wide, 1.3×-tall world | Tile large layers into ≤1920-px-wide chunks. Reuse tinted sprites. Use JPG for opaque backgrounds. |
| Castle and grotto front/back pieces don't line up while panning | Keep them and the mid fish on one parallax factor. Check alignment at the pan extremes in Phase 3. |
| Developer mode allows only one sideloaded channel, and a factory reset or disabling dev mode removes it | Keep a one-command deploy script and README so reinstalling takes a minute. |
| A Roku OS update changes how sideloaded screensavers work | Confirm in Phase 0, and re-check after OS updates. |
| Art quality / consistency | One style guide and one source format (SVG). Build the pipeline before mass-producing assets. |
| Visible looping or repetition | Randomized waypoints and routes, non-harmonic camera periods, random chest timer, seeded layout variation per session. |

## 10. Open Questions

1. **Presets:** are the Standard and Maximum presets in §5.3 the right defaults, or would you rather default to Maximum?
2. **Castle style:** storybook/fairy-tale castle (colorful turrets) or a ruined stone castle with moss?
3. **Anything else** to add before work starts?
