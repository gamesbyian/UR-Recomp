# QA-08: authentic original split-screen racer multi-pose source atlas

**Art-reconstruction research input, NOT HD artwork approval.**

The accepted pinned original-native graphics AOT [run 38500872847](https://github.com/gamesbyian/UR-Recomp/actions/runs/38500872847), artifact **11865578533**, contains independent per-OAM-slot source PPU images and SHA256-backed source reports for **three physically rendered USA 2P guest frames: 1872, 1888 and 2208**. This is 12 actual historical pose/source captures. All four racer slots are present: top front98, top rear99, lower front96, lower rear97. The two earlier frames are in countdown; the last is post-GO.

The tool `tools/art/build_qa08_original_multipose_atlas.py` reads **only that already accepted archive** and produces a standalone HTML source contact atlas and machine-readable JSON provenance sidecar:

```sh
python3 tools/art/build_qa08_original_multipose_atlas.py \
  --artifact /path/to/baldosa-native-spike-evidence.zip \
  --out /tmp/qa08-authentic-multi-pose.html
```

It checks each of the **12 full 342×224 raw P7 source RGBA SHA256 hashes** against its specific independently accepted `ws342_obj_slot_<slot>_frame<frame>.json`, the exact 7 full Original shared native frame IDs, original source alpha counts and OAM bounding boxes. Empty or damaged sources cannot become invented art. No copyrighted raster is placed in Git: HTML embeds lossless cropped PNGs built from real source pixels. Only displayed width is adjusted for **SNES 7:6 pixel aspect**.

Both temporal transitions (1872→1888 and 1888→2208) for each of the four slots are given a completely reproducible source-alpha **Jaccard index after aligning the two original bounding-box top-left corners**. Also keep the actual screen displacement separately. The former quantifies exact pixel-mask changes after translation removal; it does **not** recover character yaw, 3D perspective, unseen wheel geometry, canonical anatomy, surface material or a priority winner. The latter is not itself pose change. Different source palettes or pose phase boundaries may matter more than this scalar; do not force shape identity across phases.

The atlas deliberately retains front and rear slots separately. Do not conflate 98/99 with a single composite or use pre-final isolated OAM alpha to overpaint BG3 foreground text. The exact post-GO text source equation is proven at two coordinates by [the native main/sub pixel report](QA08-ORIGINAL-PPU-MAIN-SUB-PIXEL-DISCRIMINATOR-20261013.md); the wider **26-text-pixel** acceptance is separately proposed in #1453. Neither constitutes validation of every original racer surface.

**Next design step:** compare these three authenticated projected poses and the original title-render reference (from `tools/art/build_qa08_original_contact_sheet.py`) in a human-reviewed character-model sheet, with genuinely independent period box/print material kept as additional references. A human must approve detailed character likeness; the historically owner-vetoed procedural HD racer remains unshippable. Preserve 256×224/7:6 original geometry, source-grounded world widescreen and byte-faithful Original 4× fallback.

## New exact original cross-viewport source aliases, three authentic phases

Independently rechecked **all twelve original source P7 RGBA files** from the
accepted run: after translating only to each source's own exact native
alpha bounding-box origin, the **full unscaled cropped RGBA bytes, including
transparent interior pixels**, are identical across the upper slot98 ↔
lower slot97 pair and the upper slot99 ↔ lower slot96 pair
at **each of frames1872,1888,2208**. This is six exact
cross-viewport source-image equalities, not merely similar silhouettes.

| Native guest | Upper98 → lower97 | Upper99 → lower96 |
| --- | --- | --- |
| 1872 countdown | exact RGBA; native translation **(0,+113)** | exact RGBA; **(0,+113)** |
| 1888 moving countdown | exact RGBA; **(0,+113)** | exact RGBA; **(0,+113)** |
| 2208 post-GO | exact RGBA; **(−13,+112)** | exact RGBA; **(−13,+112)** |

The new generator strictly rechecks all six by **comparing the
actual source bytes** and records a SHA256 of each common normalized
crop and exact native translation in its JSON. It refuses to draw
any conclusions or complete a report if one mirrored source unexpectedly
differs, even if both source files still have independently valid hashes.

This makes the split viewport's paired sprite **pose reuse** and its
different post-GO registration measurable without treating a top and
bottom screenshot as two independent animations or inventing another
original unicycle design. It does **not** establish original hardware
OBJ slot ownership at unrelated pixels, colour-window winners in the
finished PPU image or any authentic HD character likeness.
