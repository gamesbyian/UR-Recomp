# QA08: authentic first medal pose-change field, 2014 Snes9x

18 October 2026. **Source timing discriminator; no guest/PPU/render fix or QA credit.**

The real original 2014 Snes9x painter experiment ([#1839](https://github.com/gamesbyian/UR-Recomp/pull/1839), actual artifact **12150037795**, SHA256 `8387c413d42cf8d2da2a61ba3ec67e8375394f938171dc4d73a3e4ba567920e4`) contains real renderer stages on original-internal fields **4028–4036** and **4172–4180**. Real unchanged 2014 original callback artifact **12075111053** (nested original ZIP SHA256 `72b7b152d08d8abb3636053bfd132db64926a5bf188f4dbba7e30b20d9583e9e`) and real compiled RF017 Windows 4bpp artifact **12134793278** (SHA256 `725ef03df3d43ff5d30b4bea944e32555974fb0b0e01af025da76ef88959b408`) were independently published. No ROM pixels are stored in this PR.

The **same-source 2014 original painter** maintains one stable five-point source signature for **4029–4031**, flips at **4032**, maintains that new signature for **4032–4034**, and flips again at **4035**. Exactly the same full after-transition five-point signature recurs at **4176–4178**, with independent stable before-state **4173–4175** and next flip at **4179**. Each signature includes genuine 2014 depth, RGB565 colour, actual source sprite-winner slot and original tile, not just apparent image colour.

| Original source coordinate | 4031 original painter | 4032 original painter | 4032 actual native winner |
| --- | --- | --- | --- |
| (207,91) | OBJ112, tile 15a2 | BG0, depth27 | background |
| (205,115) | OBJ113, tile 19a4 | OBJ113, tile 19a2 | OBJ113, tile suffix a2 |
| (205,139) | BG0, depth27 | OBJ114, tile 1da4 | OBJ114, tile suffix a4 |
| (225,96) | OBJ99, tile 15f6 | OBJ97, tile 15de | OBJ97, tile suffix de |
| (225,120) | OBJ98, tile 15f6 | OBJ96, tile 15de | OBJ96, tile suffix de |

The earlier 4175 original painter uses alternative source tile `15f2` at the x225 points; 4176 after-transition tile/state matches 4032 exactly. Source frame *images* may repeat without their internal tile index being identical, so the tool checks the actual source paint signature instead of guessing sprite identities from RGB alone.

Critically, an original 2014 **video callback labeled 4031** genuinely corresponds to original painter internal 4031 (and callback4175 to painter4175), **10/10 exact RGB samples**, already mechanically proven in merged [#1846](https://github.com/gamesbyian/UR-Recomp/pull/1846). The current native renderer at guest4032/4176 has the actual following source painter's winner/tile identity, **8/8 OBJ and 2/2 BG**, already proven in merged [#1880](https://github.com/gamesbyian/UR-Recomp/pull/1880). These two statements answer *different* time registration questions. At the **correctly paired original video callback** the native pixels still disagree and the broader [#1874](https://github.com/gamesbyian/UR-Recomp/pull/1874) census still shows 125/125 wrong pixels across 25 real result samples.

### Native brightness operand explains the two *remaining numerical shades*, not the medal timing

At genuine native guest4032 **and** guest4176, the physical PPU reports the actual winning source pixel at (205,115): **OBJ113, CGRAM word `0cd1`, pre-main RGB5 (17,6,3), postmath RGB5 (17,6,3), live INIDISP `0e`, final RGB8 (130,45,22)**. The original Snes9x **following internal painter stage** at the same numbered field is RGB565 `8183`, equivalent to RGB5 (16,6,3). After native brightness/host output the numerical difference is **(0,-1,-1)** RGB5, reproduced on both source fields. At the other four positions per field, native final RGB5 matches the following 2014 source stage. This directly narrows the *two otherwise unexplained one-step pixels* to a source-stage-versus-post-brightness arithmetic distinction; it neither proves the correct original 2014 final-video RGB nor licenses a global brightness adjustment, which would conflict with guest4016 blackout.

### Repeatable guard

The new stdlib script reuses the independent source SHA/consumed-input, Snes9x callback and physical native 4bpp verifiers rather than rebuilding another emulator or loosening their tests:

```sh
python3 tools/qa08_verify_true_original_medal_boundary.py \
  --original-outer /private/original-artifact-12075111053.zip \
  --original-painter /private/actual-source-artifact-12150037795.zip \
  --native-4bpp /private/native-fetch-artifact-12134793278.zip \
  --out /private/qa08-source-original-medal-transition.json
python3 -m unittest tests.unit.test_qa08_verify_true_original_medal_boundary
```

The verifier requires both original paint passes, exact source identities, the full 263 original callback provenance, ten true painter/callback pixels, each of the original three-field plateaus, ten true first-flip changes, later flips, 144-field recurrence, and the actual 8 sprite/2 background native writer evidence. It rejects changed source hash, missing/unstable pose, disappearance of first or second transition, reintroduced BG sprite, or native last-writer mismatch.

**Still unresolved:** exact original/native consumed button and CPU→PPU scanline/present-clock registration; original video output should not be shifted to the next painter field. No CPU/APU edits, naive ±1 video fix, invented tile replacement, medal recolour, #1807 brightness promotion, 342×224/7:6/4× modification, independent QA or release gate is authorized. For production, clean first-line HDMA/V0 [#1780](https://github.com/gamesbyian/UR-Recomp/pull/1780) and exact Modern integration [#1851](https://github.com/gamesbyian/UR-Recomp/pull/1851) remain separate, fully source-qualified but held.
