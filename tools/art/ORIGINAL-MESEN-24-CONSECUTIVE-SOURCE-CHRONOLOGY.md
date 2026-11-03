# ART-4K: authenticated contiguous original Mesen source-OBJ chronology (2026-11-03)

**Question resolved:** How often do the actual original game's 64×64 source OBJ racer alpha masks change over a narrowly bounded no-frame-skip 24-tick window? This is a 2D game-source *temporal observation*, not a recovered SNES 3D skeleton, original rendering camera, physical wheel rotation or owner-approved replacement.

## Original execution and evidence identity

Reuse the existing pinned [ART-4K original Mesen raw PPU workflow](https://github.com/gamesbyian/UR-Recomp/actions/workflows/art4k-live-original-mesen-ppu-raw.yml), not a new emulator harness. One manual dispatch, [run #41738370914](https://github.com/gamesbyian/UR-Recomp/actions/runs/41738370914), executed the source USA ROM SHA-256 `859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478` under MesenCE revision `a60e79feb4d6dcced5922d636f9211837d01e381`, with controller replay SHA-256 `28f2842fd262030e434b3aef88eb360f74de94fbf558f0eb0ba8edce645fb490` and explicit SNES frame-skipping disabled. Actual emulator bridge ticks **1601,1602,...,1624** executed consecutively. The run exported 24 mutually co-timed OAM 544-byte, VRAM 65,536-byte, CGRAM 512-byte and held 256×239 P6 screen snapshots. GitHub Actions artifact #13279512372 expires on **2026-11-10 at 23:21:45 UTC**.

To preserve verified bytes beyond the short artifact lifetime, archive `analysis/data/racer-original-mesen-consecutive-1601-1624-20261103.zip` stores the 97 deterministic canonical ZIP members: 24 × 4 actual regions plus `manifest.json`. All members were independently SHA-verified against the Actions manifest before preservation; ZIP CRC/extraction equality was rechecked. Canonical ZIP SHA-256 **`28dda3647fecb382fdbf824da7383a8116080df6ec8c98da0b3357a018986cf6`** (233,939 bytes), manifest SHA-256 **`35c04eb98be0facd1cc3bc81a3cc08db4a1ebba7f29a0962a9f7447d29c61fe3`**, 6,039,485 uncompressed bytes. This archive includes raw PPU captures, **not the ROM file**.

The new executable SHA-256 is `80ff379c31eedb8d5d7b9f5b1857ade463c584166de3d5e36192242ac2ed71ee`. The earlier independently authenticated sparse-run Mesen executable SHA-256 was **different**, `36778fa763211a72a444a7f343e7e251f07cc050d78ef88a1525a192e2a3644f`, despite the same source revision and replay identity. **Exact-byte provenance control:** independent download and manifest validation of the earlier artifact #13217381754, run #41605614082, confirms all bytes in **OAM, VRAM, CGRAM and P6** at overlapping ticks **1601, 1607, 1618** are exactly identical old versus new (12/12 region comparisons, plus controller masks). Distinct executable hashes are retained, not silently equated.

## What the observed original 2D source actually does

Decode genuine OAM slots 96 (blue) and 97 (red) using the previously authenticated SNES mode-4 OBSEL/VRAM 4bpp/OBJ palette configuration and source-local held OAM orientation. The retained frozen original sparse samples anchor these slot and register interpretations. Note that OBSEL itself was **not independently logged on every newly captured tick**, and independently matching newly captured source sprites to the *final completed screen* was **not repeated** for the 21 non-overlap ticks.

| Actual source 64×64 mask | Blue slot 96 | Red slot 97 |
|---|---:|---:|
| Executed frame observations | 24 | 24 |
| Genuine adjacent sprite-mask transitions | 23 | 23 |
| Adjacent source masks that change | **23** | **23** |
| Adjacent source masks that hold | **0** | **0** |
| Distinct alpha masks within 24 ticks | 19 | 23 |
| Changed alpha pixels per tick, minimum / median / maximum | 20 / **25** / 104 | 18 / **24** / 119 |

Blue held OAM X increases from 82 at tick 1601 to 105 at tick 1624; the red source held OAM X/Y remains at 48/48, but its original source alpha mask changes on every adjacent tick. Thus simple screen/object translation must be distinguished from local sprite shape changes. Both sprites also change their 4bpp index-plane and source RGBA pixels on all 23 actual adjacent transitions. The source has occasional large shape-change outliers (104 blue changed pixels, 119 red). Interpret these 2D facts as genuine sprite observations, not frame-by-frame joint rotations recovered from an inaccessible original 3D rig.

**Important discarded premise:** the earlier 1205–1220 P1/P2 "motion strip" is an **editorial sequence of ROM-composed source representations** (input manifest kind `ordered-evidence-backed-editorial-sprite-strip`). Its 21 held / 9 changed among 30 positions are valid comparisons *of that editorial strip* and **must never be treated as executed game animation cadence**. The prior 20 actually executed Mesen ticks 1601–2445 were sparse and likewise could not independently measure consecutive animation frames. This new 24-tick archive fills that very specific gap. The already inspected 24 frames are now diagnostics, **not prospective unobserved test data**.

## Cheap reproduction and immediate follow-up

Run from repo root with standard-library Python only and existing original 2D decoders:

```
python3 -m unittest tests.unit.test_audit_original_mesen_contiguous_24
python3 -m tools.art.audit_original_mesen_contiguous_24 \
  --archive analysis/data/racer-original-mesen-consecutive-1601-1624-20261103.zip \
  --out /private/new/verified-24-source-chronology.json
```

The exact-source re-audit verifies canonical ZIP/manifest, all 97 members and member SHA-256, original ROM/replay/Mesen binary hashes, the independent historical 3-tick overlap anchors, the original blue/red OAM hierarchy, decoded 4bpp source colour/index/alpha, all 46 authentic adjacent sprite edges and absence of invented 1994 rig/camera/art acceptance. The complete re-audited report is `analysis/data/racer-original-mesen-24-consecutive-source-chronology-20261103.json`, SHA-256 `96d5069e8b73d6a84319fc581ca59f81357682c272482046ced3212fb4409873`.

**Next cheapest discriminator:** use the *one* experimental five-parent GLB rig from #3101 under the frozen provisional 7:6 camera. Compare a predeclared zero-motion baseline against one or two **time-continuous direct-drive / bounded frame-tilt** hypotheses at these actual ticks, with one fixed image registration per player and no per-frame camera, geometry, translation, handedness or pose-class choices. Score real 2D changed-pixel spatial support/size, original colours/landmarks where identifiable, and static-fit costs separately. A model that reproduces changes every tick but misses their support or source appearance is a negative result, not a 3D recovery. Avoid re-running original Mesen; this archive supplies all evidence for this decision. Treat all 24 as exploratory because the current observation has already been examined.

No new recurring workflow, release/ART shipping gate, recovered camera, original SNES hardware observation, direct source part labelling or owner likeness approval is claimed.
