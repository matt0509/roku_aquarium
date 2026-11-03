# Roku Aquarium Screensaver — Development Plan (Draft)

Status: **planning — no code yet.** This document is meant to be revised as decisions are made.

## 1. Goals

- A Roku **screensaver** showing an animated, front-on view of a colorful aquarium.
- **Real-time rendering, not video.** Fish move on randomized paths, so it never visibly loops.
- **Full screen, no borders.** The tank fills the display edge to edge.
- **OLED-safe.** Over time every pixel changes. No static element stays put, including the gravel line, the water surface and any UI.
- The camera shows **part of a larger tank** and **pans slowly** across it.
- Content: many colorful fish, coral, sea plants and colorful gravel on the bottom.

- **Slow brightness cycle** (a gentle day/evening swing) is part of v1. See §4.4.
- **Target hardware: Roku Ultra players only, model 4660 and newer.** No sticks, TVs or older boxes.

### Non-goals (for v1)
- 3D rendering or a rotating camera. The view is always front-on, 2D with layered depth.
- Interaction such as feeding the fish. A screensaver exits on any key press.
- Sound. Screensavers are silent by convention.

## 2. Platform Overview

| Topic | Notes |
|---|---|
| Language / UI | BrightScript plus **SceneGraph** (XML components). |
| Screensaver entry | `manifest` declares `screensaver_title=...`. Roku calls `RunScreenSaver()`. An optional `RunScreenSaverSettings()` adds a settings screen. |
| Dev entry | We also provide `Main()` so the app can run as a normal channel. That makes iteration and debugging much faster. |
| Resolution | Author at **FHD (1920×1080)** UI coordinates. All target Ultras output 4K and upscale the UI layer. We will test whether FHD art looks soft on a 4K TV (see Phase 0). No HD asset set is needed. |
| Rendering | Use `Poster` nodes (bitmaps) and `Rectangle`s. There is no vector or canvas API, so all art ships as PNG/JPG. |
| Animation | `Animation` + `Vector2DFieldInterpolator` / `FloatFieldInterpolator` run on the **render thread**, so motion is smooth without a per-frame BrightScript loop. |
| Constraints | Targeting Ultra 4660+ only, so we can budget for the strongest Roku hardware and skip low-end tiers. **Texture memory** is still limited, so large bitmaps need tiling and the asset budget needs care. The 4660 is the oldest and weakest target, so it sets the performance floor and must be tested directly. |
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
| 3 | Mid scenery | Main coral, rocks, anemones, swaying plants | 0.8 |
| 4 | Mid fish | Most of the fish | 0.85 |
| 5 | Gravel bed | Multicolor pebbles with an uneven top edge | 1.0 |
| 6 | Near fish | A few large fish crossing close to the "glass" | 1.1 |
| 7 | Foreground plants | Partially out-of-focus plants at the bottom corners | 1.2 |
| 8 | Light overlay | Animated light rays and caustics, additive and semi-transparent | 0.9 |

Each layer is a `Group` whose translation equals `-camera × parallaxFactor`. Front-on parallax gives a sense of depth while the angle stays straight-on.

### 3.3 Art direction
- Bright, saturated reef palette with a clean, illustrated look rather than photoreal. It reads well on TV and compresses well.
- **Fish are drawn in neutral tones and tinted at runtime** with `Poster.blendColor`. A few base shapes (tang, clownfish, angelfish, tetra, betta, puffer, butterflyfish, guppy) × color palettes give many varieties at little memory cost. Fixed-pattern species such as clownfish get dedicated art.
- Depth cue: far layers get smaller scale, blue tint, lower opacity and slower speed.
- Gravel: pastel and jewel-tone pebbles in a few repeating tiles with a randomized top silhouette.

### 3.4 Asset strategy (decision needed, see §9)
Options:
1. **Author SVGs in the repo and rasterize to PNG in the build** (Inkscape, resvg or a script). This is reproducible, resolution-independent and easy to tweak. **Recommended.**
2. Hand-drawn or commissioned PNG art.
3. AI-generated art, cleaned up by hand. Licensing and consistency need checking.
4. Procedurally generated PNGs from a Python/Pillow script for gravel, gradients and caustics. This combines well with option 1.

## 4. Motion & Behavior

### 4.1 Camera
- Slow, eased **side-to-side pan** across the world. One full sweep takes several minutes, with easeInOut at each end.
- Add a **slow vertical drift** of about ±60 px on a different, non-harmonic period. This is critical for OLED: horizontal panning alone does not move horizontal edges such as the gravel line, the water surface or coral tops.
- Optional very slow **zoom "breathing"** (scale 1.00–1.06) so that layer 0, which barely moves, still shifts.
- The path is effectively Lissajous-like with randomized periods, so it never settles into a repeating pattern.
- Implement it as a few long-running looping interpolators on the camera/layer groups. That costs zero per-frame script.

### 4.2 Fish
- Each fish follows a **waypoint wander** pattern:
  1. Pick a random target inside its depth band, biased toward horizontal travel (fish mostly swim sideways in a front-on view).
  2. Set up a `Vector2DFieldInterpolator` from the current position to the target. The duration comes from distance ÷ species speed (± jitter), with easeInOut.
  3. When the animation stops, an observer picks the next target. Occasionally the fish **hovers** or **reverses**.
- **Turning:** when direction changes, a short `scale.x` animation from 1 to −1 makes the fish flip, which looks like turning toward or away from the viewer.
- **Swim cycle:** either a 2–4 frame sprite cycle, or a separate tail `Poster` rocking via a `rotation` interpolator around the tail joint. Tail speed scales with swim speed.
- **Gentle bob:** small looping vertical offset on an inner group.
- **Schools:** small schooling species (tetras, for example) follow a leader with offsets and a little lag.
- Fish swim across the **whole world**, not only the viewport, so the visible population changes as the camera pans.
- Target count is about 25–40 fish total across all depth bands, tuned per device tier.
- BrightScript only runs when a fish finishes a segment, which is every few seconds per fish. The CPU cost is very low.

### 4.3 Ambient life
- **Plants sway:** stems or fronds rotate gently around their base (`scaleRotateCenter`) with random phase and period.
- **Bubbles:** one or two bubblers emit bubbles that rise with slight wobble, recycled from a pool of Posters.
- **Light rays:** a few large, soft, semi-transparent shafts slowly drift and fade.
- **Caustics:** a tiling caustic texture at low opacity, slowly translated over the scene and gravel.
- **Water surface:** an optional faint shimmering band at the top that moves with the camera's vertical drift.
- **Optional extras:** a crab or snail crawling slowly along the gravel, or a sea anemone pulsing.

### 4.4 Slow brightness cycle
- The whole scene gets gradually brighter and dimmer, like a tank over a day. This also spreads wear across the screen over time, because pixel brightness changes.
- **Range:** about 100% down to about 75% brightness (final values tuned on a real OLED/TV). It never goes fully dark, so it stays pleasant as a screensaver.
- **Period:** about 20–40 minutes per full cycle, with a smooth sine-style ease so there is no visible step. The period is randomized slightly each cycle.
- **Implementation:** one full-screen black `Rectangle` at the top of the scene, with its `opacity` animated between 0.0 and about 0.25 by a looping `FloatFieldInterpolator`. This runs on the render thread, so it costs almost no script time.
- **Color shift (optional):** during the dim phase, add a faint blue-to-teal tint overlay, so it feels like evening light rather than just a darker picture.
- **Light rays and caustics** can fade with the cycle, so the "sun" dims along with the scene.
- **Settings (Phase 7):** on/off, dimming depth (subtle / medium / deep) and cycle length.
- **Note:** a black overlay on an LED/LCD TV doesn't save power the way it does on OLED, but it looks the same. On OLED it lowers the pixel brightness as intended.

## 5. OLED Safety Checklist

- [ ] No static UI: no logos, clocks or text. A future clock option would drift across the screen.
- [ ] Every layer, including the background gradient, moves (camera parallax plus vertical drift plus zoom breathing).
- [ ] Horizontal features (gravel line, surface) move **vertically** over time.
- [ ] Vertical features (plant stems, rock edges) move **horizontally** over time.
- [ ] Avoid large areas of pure white or max-brightness color. Highlights stay soft and moving.
- [ ] Slow global **brightness cycle** (§4.4): about 100% to 75% over a 20–40 minute period, via a top-level overlay.
- [ ] Verification: a debug mode that captures frames over time (or computes per-pixel variance offline from screenshots taken with the Roku developer screenshot utility) to confirm that no region stays static.

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
│   ├── Plant.xml/.brs          # swaying plant
│   ├── BubbleEmitter.xml/.brs  # pooled bubbles
│   ├── LightRays.xml/.brs      # light shafts + caustics
│   └── Settings*.xml/.brs      # screensaver settings UI
├── data/
│   ├── species.json            # species: art, size range, speed, depth band, palettes
│   └── tank_layout.json        # scenery placement per layer (or seeded random generation)
├── images/                     # build output: PNGs (FHD; optional HD set)
├── art/                        # source SVGs + generator scripts
└── tools/
    ├── build_assets.*          # rasterize SVG → PNG, generate gravel/caustics
    └── deploy.*                # zip + sideload to device (e.g. roku-deploy / Makefile + curl)
```

Key design choices:
- **Data-driven species and scenery** (JSON) so new fish or coral do not require code changes.
- **Seeded randomness:** scenery layout can be generated from a seed at startup, so each session looks a little different. A fixed seed is available for debugging.
- **Single device class:** because only Ultra 4660+ is supported, there is no tiering. We tune one profile against the 4660, the oldest target, and newer Ultras will have headroom. We may add a "high" setting for more fish on newer models later, but it is not needed for v1.

## 7. Phased Roadmap

| Phase | Deliverable | Exit criteria |
|---|---|---|
| **0. Spikes** | (a) Performance test: N animated Posters with interpolators on a Roku Ultra 4660 (or the closest we can test). (b) Confirm screensaver entry points and settings on current Roku OS. (c) Find the texture memory ceiling. (d) Check whether FHD art looks sharp enough on a 4K display, or whether the key layers need 4K art. | Known fish/layer budget for the 4660 and a decision on art resolution. |
| **1. Skeleton** | Manifest, `Main()` + `RunScreenSaver()`, empty full-screen Scene, build and deploy scripts. | Sideloads, runs as channel and as screensaver. |
| **2. World & camera** | Placeholder colored layers in the world, parallax groups, pan + vertical drift + zoom. | Smooth pan with no edges visible at any point in the cycle. |
| **3. Scenery art** | Back gradient, rocks, coral, plants, gravel tiles, asset pipeline. | Tank looks "full" and colorful at any camera position. |
| **4. Fish** | Species data, wander behavior, turning, tail animation, depth bands, schools. | 30+ fish swimming naturally at a solid frame rate. |
| **5. Ambient effects** | Plant sway, bubbles, light rays, caustics. | Scene feels alive. Still within performance budget. |
| **6. OLED hardening** | Checklist in §5, brightness cycle (§4.4), pixel-variance test. | No static region across a 30-minute capture. |
| **7. Settings & polish** | Settings screen (fish count, pan speed, effects on/off, day-night cycle). Icons and splash. | Settings persist via `roRegistrySection`. |
| **8. Packaging** | Signed package and, if desired, a channel store submission. | Installable package and docs. |

Optional **Phase 0.5:** a quick browser (HTML canvas) prototype to tune the motion "feel" (pan speed, wander, schooling) before porting the constants to BrightScript. It is cheap, but it duplicates logic, so it is only worth doing if tuning on device turns out slow.

## 8. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Performance on the oldest target (Ultra 4660) | Render-thread interpolators instead of per-frame script, pooled nodes, few large alpha-blended overlays. Test on a 4660 early. |
| Texture memory limits with a 3×-wide world | Tile large layers into ≤1920-px-wide chunks. Reuse tinted sprites. Use JPG for opaque backgrounds. |
| Distribution: Roku's store policies for screensavers may have changed | Sideloading always works for personal use. Check current certification and publishing rules before Phase 8. |
| Art quality / consistency | One style guide and one source format (SVG). Build the pipeline before mass-producing assets. |
| Visible looping or repetition | Randomized waypoints, non-harmonic camera periods, seeded layout variation per session. |

## 9. Open Questions

1. **Distribution:** personal use (sideload) only, or publish to the Roku Channel Store?
2. ~~Target devices~~ **Decided:** Roku Ultra 4660 and newer only. Remaining question: do you have a 4660 to test on, or which Ultra do you own? And is your TV 4K?
3. **Art source:** SVG authored in repo (recommended), commissioned art, or AI-generated?
4. **Style:** stylized/illustrated (recommended) or semi-realistic?
5. **Tank type:** saltwater reef (clownfish, tangs, coral) or freshwater planted tank (tetras, angelfish, plants), or a mix? A "colorful fish, coral and plants" brief suggests a stylized reef with some plants.
6. **Extras:** bubbler, crab or snail, treasure chest or decorations, optional drifting clock? (The brightness cycle is already in the plan.)
7. **Settings:** which user-adjustable options matter to you?
