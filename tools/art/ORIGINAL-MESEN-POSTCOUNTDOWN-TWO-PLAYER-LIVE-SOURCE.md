# Authenticated original MesenCE two-player post-countdown source frames, 1601–1605

The original USA-ROM race is **visibly underway** after the countdown in the actual live MesenCE replay: [original-source workflow #41585842911](https://github.com/gamesbyian/UR-Recomp/actions/runs/41585842911) passed. Its seven-day [artifact #13208166875](https://github.com/gamesbyian/UR-Recomp/actions/runs/41585842911/artifacts/13208166875), ZIP SHA-256 `d7d3e312528563bae0940ed97258024103085576c385334253458af501744ab7`, contains five original 256×239 screenshots (PPM), raw original SNES **OAM 544B, VRAM 65536B, CGRAM 512B** for each original tick, and **the exact MesenCE serialized PPU registers acquired in the same run**. Source-only producer `tools/art/capture_original_mesen_ppu_registers.py` now accepts `--include-held-framebuffer` without requiring a second ROM replay and leaves its old default unchanged. All five source files/tick, source original ROM and controller replay identities, no-frame-skip state, and PPU frame counter were independently checked against the actual artifact. Only the bounded diagnostic workflow was temporarily added to execute this proof and then removed.

The screenshot shows two actual racers after the giant countdown graphic has cleared. Source gameplay has a track, split-screen, score and text graphics, so source racer pixels can be obscured. Do not assert a completely unobscured racer. The actual authored input commands at original steps 1580–1603 were **P1 Right and P2 Left simultaneously**; the observed replay masks are P1=128/P2=64 on captured ticks 1601–1604, then zero at 1605. These inputs are **injected controls**, distinct from independently established engine acceleration or animation-bone velocities.

| Original Mesen bridge tick | Held blue OBJ slot96 X | Held red OBJ slot97 X | OAM bytes changed | VRAM bytes changed | CGRAM bytes changed | RGB pixels changed from previous frame |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1601 | 82 | 48 | baseline | baseline | baseline | baseline |
| 1602 | 83 | 48 | **1** | 117 | 18 | 19,903 |
| 1603 | 84 | 48 | **1** | 318 | 26 | 19,858 |
| 1604 | 85 | 48 | **1** | 124 | 17 | 20,613 |
| 1605 | 86 | 48 | **1** | 115 | 26 | 20,821 |

All held PPU states report `ppu.scanline=225`, `ppu.oamMode=4` (small16×16/large64×64), source OBJ tile base `0x6000` and second-table offset `0x1000` (both **VRAM word addresses**). Both source raster contents change during these frames even when a held OAM position remains unchanged. This directly demonstrates the danger of using only OAM-position deltas as an animation metric. The source 2D racers are recognisable in the original completed screen, but pixel content includes frame changes and HUD/track overlap.

The previously source-verified fully opaque **blue 323/323 and red 327/327 exact RGB matching** occurred at original countdown tick 1219. An independent exploratory pixel decoder applied to the new original live post-countdown raw arrays found only **281/316, 277/316, 281/320, 282/323, 281/317** best blue matches, and **132/311, 134/319, 134/316, 128/314, 132/318** best red matches at bounded translations. **These are observed partial overlaps, not failed source geometry.** The held PPU register snapshot may be at a different point in the original per-line drawing sequence than the completed screen. Pixel rejection or 3D geometry fitting from residuals is not authorized until source PPU OBJ writes, track/HUD priority and scanout origin are independently matched.

The exact per-frame screenshot and OAM hashes, original replay ROM/binary, source blue/red alpha counts and explicit negative gates are frozen in `analysis/data/racer-original-two-player-postcountdown-actual-frames-20261103.json`. Original Mesen source files can be regenerated via this one-pass command using pinned MesenCE and the archived no-frame-skip headless launcher:

```bash
MESEN_SNES_DISABLE_FRAME_SKIPPING=1 \
python3 -m tools.art.capture_original_mesen_ppu_registers \
  --rom reference/roms/retail/Uniracers_USA.sfc \
  --input-file tests/input/two-player-first-race.input \
  --mesen-for-ai-repo third_party/src/mesen-for-ai \
  --mesen-executable /path/to/pinned/Mesen \
  --advance-frames 1600 --capture-frames 5 --include-held-framebuffer \
  --out-dir /private/new/source-original-2p-frame-witness
```

**Next source discriminator:** collect time/scanline-indexed original OAM writes to PPU OBJ registers (or derive a source-verified finished-frame OAM buffer), then match one held source sprite raster to a particular **completed** original screen scanout for each of the two racer viewports. Preserve the exact already-verified original 2D 323/327 match as positive control. Only after source-to-screen temporal correspondence is stable should the existing part-addressable GLB (#2832), its pose viewer and the strict source-family withheld silhouettes be used to search source **3D** pose/camera hypotheses. The original 1994 mesh, rig pivots, skeleton, depth and shader remain unknown, as does owner likeness approval.

## Subsequent archived-data discriminator, no additional ROM run

[ART-4K diagnostic #3080](https://github.com/gamesbyian/UR-Recomp/pull/3080) reuses the real authenticated original source ZIP above without rebuilding Mesen or changing the game. The existing exact-colour 2D screen matcher inherited **countdown-only screen-origin bounds X=76..170**, excluding the red racer's post-countdown candidate. An explicit wide diagnostic X=0..192 preserves the original default for prior 1219 controls and changes no source video or model assets. All five held original frames yield:

| Mesen tick | Blue opaque matching | Red opaque matching, widened | Red with historical X76..170 |
| --- | ---: | ---: | ---: |
| 1601 | 281/316 | 132/311 | 0 |
| 1602 | 277/316 | 134/319 | 0 |
| 1603 | 281/320 | 134/316 | 0 |
| 1604 | 282/323 | 128/314 | 0 |
| 1605 | 281/317 | 132/318 | 0 |

The wide red source candidate is best at completed-screen **(34,48)**, while held OAM says **X48/Y48**. The blue best origin follows **X82..86/Y158**. Actual underlying raw PPU and P6 source SHA identities are unchanged; the numeric input and negative acceptance gates are frozen in [the authenticated source-only X-window receipt](../../analysis/data/racer-original-postcountdown-horizontal-window-real-20261103.json).

**Discriminative-colour control is essential:** blue's chromatic source pixels match **71/71,73/74,61/61,69/69,62/62**, but the red held source raster's strongly red pixels match **6/59,8/65,12/66,8/65,6/61**. The red 128..134 opaque matches are largely shared grays, while the opposite viewport also yields ~106..116 such grayscale-rich matches. This is insufficient evidence of correct original red source 2D pose registration. A separate ±8px bounded five-source × five-screen comparison finds that blue favors its corresponding original screen tick each time; red stays near 127..135 matches across target ticks, with no consistent uniform one-frame phase shift.

The original completed frames visibly contain text overlays and track graphics intersecting the racer crop. This **does not independently prove** which source pixels are occluded, absent at fetch time, altered by brightness/colour math, or overwritten by a higher-priority layer. The next real source experiment should therefore capture original **upper-viewport effective OBJ tile fetch and final BG/OBJ composition winner**, with original blue and 1219 exact 2D positives as controls; see [bounded source instrumentation issue #3078](https://github.com/gamesbyian/UR-Recomp/issues/3078). Do not use these partial 2D pixel residuals to refit the experimental GLB, certify the 1994 3D camera/skeleton, or award owner likeness approval.

## New exact source-2D explanation: mirror plus bounded red-channel compositing

The same authenticated 1601–1605 original-Mesen source archive has now been examined with a **controlled alternate 2D orientation** and a single, bounded RGB transformation. The reusable source-only producer is `tools/art/audit_original_postcountdown_obj_compositing.py`; the authentic five-frame numerical receipt is `analysis/data/racer-original-postcountdown-obj-flip-red-overlay-20261103.json`. No ROM replay, emulator patch, GLB retargeting or Windows build was required.

The held source red OAM slot 97 reports **x=48, y=48, H-flip bit OFF** on all five frames. The original displayed red sprite instead matches a **horizontally mirrored decoded 64×64 original sprite at the exact same x=48,y=48**. This is a diagnostic flip of the decoded pixels only, *not* a modification of source OAM. Blue slot 96 remains unflipped and registers at its observed completed-screen x=82..86, y=158, seven pixels below its held OAM y=151.

| Original tick | Blue source opaque pixels | Blue direct RGB | Blue red-channel addition | Red source opaque pixels | Mirrored red direct RGB | Red red-channel addition |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1601 | 316 | 281 | 35 | 311 | 290 | 21 |
| 1602 | 316 | 277 | 39 | 319 | 298 | 21 |
| 1603 | 320 | 281 | 39 | 316 | 295 | 21 |
| 1604 | 323 | 282 | 41 | 314 | 293 | 21 |
| 1605 | 317 | 281 | 36 | 318 | 297 | 21 |
| **Total** | **1,592** | **1,402** | **190** | **1,578** | **1,473** | **105** |

**Every one of 3,170 original opaque source-pixel observations is now accounted for at exact 8-bit Mesen P6 RGB:** 2,875 screen pixels equal their original source RGB, and the remaining 295 equal the source's **red-only five-bit channel +13, capped at 31 and expanded by the exact Mesen colour rule `(v<<3)|(v>>2)`**, with green and blue unchanged. In particular, **all distinctive red chromatic source pixels match**, 59/59, 65/65, 66/66, 65/65 and 61/61. The 21 red-channel-altered red-racer pixels occupy the same source-local coordinates over all five original frames and coincide visually with red HUD lettering. Blue's altered pixels move with the racer under screen lettering. That provides strong evidence of a consistent compositing operation; **the original active PPU colour-math registers, winning sprite priority and scanline OAM write site are not independently observed**.

The test explicitly rejects mistaken rival hypotheses. For red, applying the *held unflipped* raster at the correct origin leaves 297–304 unexplained pixels per frame; a one-pixel horizontal shift of the mirrored image leaves 228–237; an additive red constant of 12 rather than 13 leaves 21. For blue, flipping the raster leaves 292–305 unexplained; a one-pixel shift leaves 220–235; an additive red constant of 12 leaves 30–35. The claimed correspondence is a **source-derived 2D raster identity under an observed compositing rule**, not a captured causal OAM flip event or a fitted 1994 3D rig.

**Decision consequence:** The former partial raw colour disagreements do not justify new 3D geometry corrections or another generic source-frame capture. Accurate 2D source silhouettes and screen positions can now inform controlled, holdout-respecting experimental 3D pose comparisons while the narrower original PPU scanline writer / layer-ownership question remains open separately. No 1994 original source mesh, skeleton, camera, shader or shipping art was recovered, and no owner likeness approval or Windows release QA gate changes.
