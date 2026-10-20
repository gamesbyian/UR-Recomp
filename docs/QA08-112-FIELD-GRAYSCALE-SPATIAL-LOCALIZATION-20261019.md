# QA08: spatial discriminator for the authenticated 112-field grayscale-cycle frames

2026-10-19. **Read-only instrument, not an accepted original/native graphic repair.**

## Decision and provenance

Existing authentic 2014 Snes9x callbacks and the separate compiled Windows PPU source prove **890,205 wrong RGB5 positions on 263 full 256×224 pairs**. Of those, **318,775** are the four exact gray substitutions on thirteen samples at native guests 4064..5408, stride 112. The merged source verifier `tools/qa08_verify_112field_grey_pixel_budget.py` has already established both archive identities, 5,484 guest CRC, BGRX/P7 channel interpretations, pixel-level totals, and callback **f−1 ↔ native guest f** registration. Do not reassign this benchmark's guest source to a later clean production PE.

The narrow unknown tackled here is **spatial and temporal localization**, not a new claim about palette-ingestion causality. `tools/qa08_localize_112field_grayscale.py` reuses the exact archive verifier *first*, then classifies every uncropped source position into exact RGB5, one of the four measured gray transitions, another gray mismatch, or a non-gray mismatch. It reports per-frame counts, per-scanline counts, aggregate 8×8 source-cell counts, and the pixel-position union/intersection of the 13 cyclic-gray masks. No picture, colour raster or replacement assets are emitted.

```sh
python3 tools/qa08_localize_112field_grayscale.py \
  --original /private/original-2014-inner.zip \
  --native /private/integrated-ppu-artifact-12151839452.zip \
  --out /private/qa08-spatial.json
python3 -m unittest tests.unit.test_qa08_localize_112field_grayscale
```

The two immutable SHA256 identities are enforced by the inherited validator. The first path is the **nested** original ZIP in artifact 12075111053, not its outer download wrapper. The second path is the **outer** integrated native source ZIP in artifact 12151839452, which contains the nested P7 source frames. A separate source-verified long-retention archive for the older RF017+V0 epoch is *not* a substitute for the required integrated-source outer identity. If those exact bytes are unavailable, leave the report **not run**; never fabricate a heatmap from published totals.

## Interpretation and next discriminating capture

A small union/high intersection would establish a spatially persistent mismatch mask among these 13 fields; a large union/low intersection would identify moving or nonpersistent wrong pixels. Neither result identifies CGRAM port source, palette index, color math, HDMA ingestion, brightness, instruction clock or beam position. The scanline and cell summaries are intended to **select a narrow writer-to-raster observation**, not to support any pixel mask or output rewrite.

The independently archived current-RF017 late writer journal [QA08 gray-phase research](QA08-RESULT-GREY-PHASE-112-CYCLE-20261017.md) directly observes native CGRAM packet **5155** matching original packet **5157**, with all four palette words exact. Other native/original writer pairs 5162/5164, 5169/5171 and 5176/5178 agree. Same-PE guest CRC and same-clock equivalence are separate questions. A useful *new* source capture would bracket native guests **5154..5158** and the corresponding original callback and actual CPU/PPU register stages at consecutive fields, recording the first effective CGRAM index values at the first wrong source pixels, scanline/beam chronology, relevant color-math registers and $2100 forced-blank state. Do not assume that native/source H-counter units or host-field labels are directly comparable. The extra native writer phase observed in a separate executable also cannot by itself explain the distinct guest4016 premature unblank.

**Stop rule:** Run the spatial classifier once on exactly the pinned 13-image archive pair. Use its localization to narrow one source-consumed writer-to-pixel experiment only if source raster details would distinguish alternative register/ingestion causes. No 112-field video rephasing, guessed remap, full-raster mask, global brightness trial, CPU/APU clock fix, release gate award, Remastered likeness approval or pixel-count improvement is authorized.

## Verification boundary

Five ROM-free synthetic adversarial tests cover full-size channel/class semantics, lower/upper/edge cells, temporal overlap and count conservation, malformed input and fail-closed authentication. **Those local tests are not a replay of the genuine archives.** Authentic spatial findings from the two pinned source ZIPs are documented below; they remain a scientific observation rather than a correction. The independent release ledger stays unchanged at 0/12 and original-USA event acceptance at 0/45.

## Genuine archive replay on October 19

The original GitHub Actions artifact **12075111053** was downloaded (outer SHA256 `3475ee87b5b20768f9377d8d1c787927955c33ee6d4388dae008f5486a81370e`) and its real `original.zip` member extracted (SHA256 `72b7b152d08d8abb3636053bfd132db64926a5bf188f4dbba7e30b20d9583e9e`). The separate compiled integrated Windows PPU archive **12151839452** was downloaded and verified (SHA256 `832c08263e2d3013d5b15df82b2b0574fabfd3114194b7cbef9f6bb1b2959727`). All 13 members and the inherited full 263-frame guest/original identity and pixel census passed. The new tool itself was run on these files, not solely synthetic frames.

Across the **745,472** actual pixel positions in the 13 complete source pairs: **386,459 RGB5 exact**, **318,775 four-cycle gray wrong**, **23,311 other gray-to-gray wrong** and **16,927 non-grayscale wrong**, totalling precisely **359,013 wrong**. The cycling-gray positions have a union of **24,940 distinct source coordinates**, of which **24,096** are mismatched in **all 13** frames (96.6% of the union). The aggregate 8×8 logical grid has **448/896 affected cells**; **289 cells** have all 64 positions cycling-wrong on every one of the 13 samples, and **all 224 scanlines** contain at least one cycling-gray mismatch.

This is a **new, authentic spatial observation**: most cycling-gray errors occupy a remarkably stable part of the final output, making a shared source-value/presentation-phase discriminator preferable to speculative moving-OBJ image patches. It does **not** identify the consumed palette index, source writer instruction time or effective beam/HDMA ingestion stage. The mismatches persist; **zero source pixels were corrected**.

Compact per-frame/source-bound evidence is in [the October 19 spatial receipt](../analysis/data/qa08-authentic-grayscale-spatial-20261019.json). A private full per-scanline/per-cell JSON report was generated from the real archives (SHA256 `f07757a00888a720734fb99274c91111b9954e63f58a20c8a9adff3492676ba0`), but is not committed because it is regenerable from the exact archived images and would add bulk data. Direct script entrypoint, archive-authentication failure and synthetic raster invariants passed **6/6** local unit tests. The full repository tooling/hygiene suite and independent Windows executable/candidate tests have not been run here. **QA08/10 and 0/12 release gates remain HOLD.**

## Source-consumed CPU palette packet versus raster class algebra

Two additional genuine GitHub Actions source archives were downloaded and independently inspected, rather than relying on earlier prose alone:

- 2014 Snes9x original CPU-register journal in artifact **12013432991**, outer SHA256 `d725ee45db1b66d098e79499263dd089dba80a26de517c30db674f91e20f80a8`, journal member SHA256 `7e1f36a58fe52205011c9f34d4704c6311d929ac75caf11ea7e6958a6cc386c4`;
- Compiled RF017 Windows native CPU $2121/$2122 journal in artifact **12125295776**, outer SHA256 `a62f0c228e85c741a8f1da0b92a4444f9091681c065c93c8a678b4ee2bb6f2ef`, source JSON member SHA256 `33e27bc151c020e38beb40672fe67e2cc74bc43b8456bdbfd72af6f9c04dedda`.

Original field **5178** has source-written palette slot words `$6C=56B5, $6D=4A52, $6E=4631, $6F=4210`. Native writer field **5183** has `$6C=4A52, $6D=4631, $6E=4210, $6F=56B5`. Each word is neutral gray in RGB555. Under the **empirically observed candidate display mapping** `RGB5 channel = (RGB555 five-bit component)−1`, their exact per-slot original→native gray transitions are **20→17, 17→16, 16→15, 15→20**, respectively. These are *precisely all four* categories seen at **318,775 real pixel positions** in the 13 authenticated source rasters. The observation is recorded in [the four-color crossjoin receipt](../analysis/data/qa08-late-cgram-four-color-raster-crossjoin-20261019.json) with immutable source packet/journal identity and all negative proof flags.

**Interpretation:** A real source-packet phase permutation is algebraically consistent with every recurring final-raster mismatch *class*. This greatly narrows a useful follow-up, but is not yet a pixel-by-pixel causality proof. The native register-journal PE differs from the integrated Windows PPU-source PE; the original source callback and its CPU journal also have distinct observation-stage labels. No witness currently binds a wrong source pixel to its actual consumed CGRAM index, effective main/sub color-math operands, beam phase and executed source-instruction time at that exact field. The `minus one` display mapping is an observed numerical correspondence, not an independently proven renderer formula. Therefore the next producer should capture **effective CGRAM palette index and palette word at sampled stable-gray pixels before/after the original5178/native5183 transition**, alongside V/H and full source identity; keep the distinct forced-black4016 and medal masks out of a speculative palette correction.

No current original/native error total is lowered by this packet observation; output recolouring and frame shifting remain forbidden.


## Consecutive sampled-window controls: guest 5136..5232

After identifying the *intersection* of **24,096** four-cycle wrong coordinates across all thirteen source-authenticated 112-field pulse captures, the extended analyzer re-opened seven **distinct and SHA-verified** original callback f−1/native P7 guest f pairs. Unlike the 112-spaced pulse positions, the following fields are consecutive **16-field sampling ticks** around native guest 5184:

| Native guest | 24,096 shared coordinates RGB5-exact | Four-cycle wrong on those coordinates | Complete 256×224 frame wrong |
| --- | ---: | ---: | ---: |
| 5136 | 24,096 | 0 | 3,235 |
| 5152 | 24,096 | 0 | 2,989 |
| 5168 | 24,096 | 0 | 3,065 |
| **5184** | **0** | **24,096** | **27,569** |
| 5200 | 24,096 | 0 | 2,989 |
| 5216 | 24,096 | 0 | 3,066 |
| 5232 | 24,096 | 0 | 3,023 |

The genuine original and native *individual frame member* SHA256 hashes are preserved in [the seven-field machine receipt](../analysis/data/qa08-authentic-sevenfield-gray-pulse-bracket-20261019.json), as well as the persistent coordinate-set SHA256 `4646f2123c596b1e9bbca6813d92b1ae3b9a4a53e08e300c17bf2e5f2ebb7b95` (little-endian uint32 row-major source indexes). The live analyzer now validates all 14 control image members against the original independently captured source manifest and compiled Windows P7 report, then requires that *precise* one-sample pulse without any frame re-registration or pixel suppression. That protects the prior conclusion against accidental metadata substitution.

This localizes the *sampled* recurring gray disagreement: six surrounding measured 16-field ticks agree at every persistent gray-cycle source coordinate, whereas the 5184 tick differs at all 24,096. These are **sampled ticks, not continuous coverage of every intervening guest field**, so do not claim the actual write/ingestion edge first occurs at 5183/5184. Actual original/native CPU CGRAM packet and effective rendered palette index/timing still must be joined in one qualified source-clock observation, with separate PE epochs treated as separate experiments. The pending distinct guest4016 blackout and result-medal errors are not covered by this gray footprint result.

The full local JSON aggregate (including all scanline, cell, class and validated control hashes) was regenerated by running the expanded classifier on the exact historical archives; SHA256 `64f658331cefe7c4ee33003b3d5aae50c0dd98153c749e317022bead387e7427`. This bulk derived report is intentionally not checked into Git. **Ten** scoped local ROM-free Python tests cover morphology, immutable receipts, packet algebra, synthetic negative archive cases, direct CLI, and sampled-window controls. Neither source images nor binaries are committed. No pixels were corrected; QA-08/10 and release acceptance remain HOLD.

## Eight authentic source-coordinate anchors for the next effective-CGRAM probe

To prevent the next original/native producer from scanning an entire result raster to find a representative source pixel, the same SHA-bound source images were read at **eight selected logical source coordinates**, one in each upper/lower 112-line raster band for each of the four empirical gray mismatch classes at guest5184. Each chosen center was verified as a cycling-gray error in **all thirteen** 112-spaced source captures; at guest5184 each has a **3×3 neighborhood of the same RGB5 pair entirely inside that 13-frame error intersection**. The center pixel is RGB5-exact on every one of the six surrounding 16-field sampled controls, and wrong at guest5184. Numbers in the final column are correctly registered **original RGB5 → native RGB5**, *not* source palette-register IDs.

| Guest5184 source pixel (x,y) | Raster half | Authenticated original → native gray |
| --- | --- | --- |
| (70,58) | Upper | 20 → 17 |
| (202,182) | Lower | 20 → 17 |
| (84,77) | Upper | 15 → 20 |
| (175,145) | Lower | 15 → 20 |
| (53,41) | Upper | 16 → 15 |
| (187,160) | Lower | 16 → 15 |
| (65,52) | Upper | 17 → 16 |
| (190,161) | Lower | 17 → 16 |

These eight pixel samples are an **experiment selection**, not representative counts or an effective PPU palette-slot attribution. A tiny follow-up logger can instrument their *actual* guest/source pixel palette index, CGRAM word and main/sub-color operands at the relevant beam phase, including a background-region and sprite-region negative control if available. Retain the original 2014 callback f−1/native guest f video registration and original/native instrument PE/source epoch differences. No unverified OBJ or layer claim is attached to the coordinates. This additional coordinate reread changes no code, raw source images, acceptance or RGB5 totals.

## New per-coordinate four-class invariance on all thirteen original/native samples

The full original/native source images were independently re-opened to ask a stricter question than the combined 24,940-position footprint: **can a coordinate ever switch from one of the four actual grayscale substitutions to another?** Across all thirteen authentic 112-field source pairs, the answer is **zero observed cross-class switches**, including the 844 positions that are not wrong on *every* sampled field. A pixel can be exact on one sample and have its designated mismatch class on another, but no position maps to two different four-state grayscale transitions in these captures.

| Original → native RGB5 gray | Authenticated wrong-pixel occurrences | Distinct source coordinates | Positions wrong in all 13 | Upper / lower half of persistent positions |
| --- | ---: | ---: | ---: | --- |
| 15→20 | 53,658 | 4,181 | 4,088 | 1,958 / 2,130 |
| 16→15 | 107,868 | 8,380 | 8,236 | 4,163 / 4,073 |
| 17→16 | 52,716 | 4,131 | 3,969 | 1,999 / 1,970 |
| 20→17 | 104,533 | 8,248 | 7,803 | 3,827 / 3,976 |
| **Total** | **318,775** | **24,940** | **24,096** | **11,947 / 12,149** |

The read-only verifier now records and checks **four separate SHA256 hashes** of the sorted little-endian 32-bit *persistent source-position indexes* (without publishing masks or source artwork). Its fail-closed synthetic tests reject a coordinate that changes class between fields, impossible class identifiers, incomplete source sets or changed original/native pixel accounting. The observed source-authorized receipt is [qa08-authentic-fixed-gray-class-20261019.json](../analysis/data/qa08-authentic-fixed-gray-class-20261019.json).

This tightens the static four-phase color **correlation**: a persistent one-to-one spatial assignment of original/native gray substitutions across the 112-field *sampling alias*. It does **not** prove four CGRAM source indices at those pixels, their exact write/ingestion order, effective PPU priority or a continuously fixed visual mask during the intervening 111 frames. Four per-class spatial hashes, 0 cross-class switches and two new negative-control tests add **no release gate credit or corrected pixel positions**.

## Independent 2014 Snes9x full-CGRAM memory control versus native 5183 port packet

The originally archived 2014 Snes9x register evidence is supplemented by original artifact **12013432991** (outer SHA256 `d725ee45db1b66d098e79499263dd089dba80a26de517c30db674f91e20f80a8`). Its two **actual 512-byte** Snes9x CGRAM memory dumps at source-script frames **5183** and **5184** were independently extracted, hashed, compared byte-for-byte and decoded as little-endian RGB555 words. Both entire dumps have the identical SHA256 `431224685084e4a1ec62da7d7aaab96a7c36beb78aa8d257b0569be416737c12`, with `$6C..$6F = 56B5, 4A52, 4631, 4210`. Its original CPU port journal SHA `7e1f36a58fe52205011c9f34d4704c6311d929ac75caf11ea7e6958a6cc386c4` contains the preceding **5178** packet and no CPU CGRAM writes in the 5183-to-5184 observation interval.

The separately compiled current RF017 Win32 CPU-port journal artifact **12125295776** (SHA256 `a62f0c228e85c741a8f1da0b92a4444f9091681c065c93c8a678b4ee2bb6f2ef`) records twelve authentic $2121/$2122 port writes at native source field **5183**, submitting `$6C..$6F = 4A52, 4631, 4210, 56B5`. Those four *CPU-submitted* words form the observed one-slot permutation relative to the original *CGRAM memory readback*, and the genuinely captured native 5184 P7 image is exactly the unique 16-field sample pulse at all 24,096 stable cyclic-gray locations.

This is a qualified **cross-stage observation**, not a proven native effective-palette mismatch at the actual pixel beam. The original observations are retained full PPU CGRAM **readbacks** from the Snes9x source, whereas the native 5183 values are CPU input-port **transactions** from a different instrumented Windows PE than the raster archive. The next missing witness is an actual *native PPU-effective* palette read at the eight verified source pixel anchors, their main/sub color math/brightness, source stage and beam time, alongside equivalent original consumption. Do not infer exact instruction clocks, promote source-swapped colors to a correction, or treat existing 16-field P7 sampling as uninterrupted frame-by-frame coverage.

Machine-readable [original-CGRAM/full-state versus native-port source receipt](../analysis/data/qa08-original-full-cgram-stable-vs-native-port-20261019.json) preserves both exact ZIP identities, original dump SHA and four words, native guest CRC, stage distinctions and all negative gates.


## CI authority reconciliation before integration (October 19)

A previous exact-head tooling run on this evidence branch failed partly because the shared `tests.unit.test_document_authority` test expected the name `Baldosa` in `docs/WORK-QUEUE.md`. Agent 7's separate new synthetic regression helper typo was fixed in commit `166ce822c28397c3fffdbac485371c2c1d3ec09b`; the next full tooling run then reported only the shared document-authority failure. **Current main now contains the required Baldosa reference in the shared queue**, so this branch's subsequent PR merge-test must be requalified against current main, with no special-case test relaxation. Agent 7 does not own the queue or independent ledger, and leaves branch rebase/merge to Agent 8. A green head check would only qualify tools and documentation, not the original/native raster or physical release acceptance.



## Full 263-source RGB5 versus RGB8 comparison (independently measured October 19)

A separate complete byte-level census reopened the same SHA-pinned original 2014 Snes9x BGRX8888 **RGB565-derived** archive and compiled Windows P7 RGBA archive, on all 263 actual callback f−1/native guest f pairs. Every one of the 15,081,472 source pixel positions was checked both at **RGB5 component precision** and by full RGB8 components, without crop, shift or recolour:

| Pixel-level measure | Actual positions |
| --- | ---: |
| RGB5 incorrect (original authenticity benchmark) | 890,205 |
| RGB8 bytes differ | 13,293,424 |
| RGB5 exact but RGB8 differ | **12,403,219** |
| Full RGB8-exact positions | 1,788,048 |
| Entirely RGB5-exact frames | 132 of 263 |
| Entirely RGB8-exact frames | 18 of 263 |

All RGB5 errors are necessarily RGB8 errors. The large extra set shares the *same* top five RGB bits in each channel but differs in lower bits. This reflects the comparison of different captured **presentation pipelines** and is **not** an additional 12.4 million proven source-CGRAM/beam failures. It would be wrong to silently promote the more severe raw-RGB8 count into the accepted RGB5 graphical-fidelity budget. Byte-exact host presentation/DAC conversion should be studied independently, with a declared RGB565/Snes9x versus native RGBA colour-space contract and actual output surfaces.

Reproduction: `tools/qa08_authentic_rgb8_depth_census.py --original-inner /private/exact-original-inner.zip --native-outer /private/exact-Win32-outer.zip --out /private/bitdepth-census.json`. This qualifies the exact archive SHA, original/native 263-frame registration, source per-frame P7 hashes and the inherited original/native 890,205 RGB5 count; it reports both precision levels and refuses any source drift. Its ROM-free synthetic unit tests check full-source geometry, channel order, RGB5-exact-but-RGB8-different classification, alpha and negative release gates. The compact [numeric receipt](../analysis/data/qa08-authentic-rgb8-source-budget-20261019.json) contains the actual aggregate.

A second qualified observation explains the four recurring **RGB5 levels** previously described by an empirical component-minus-one mapping. Original 2014 Snes9x full display-register snapshots at original source fields **5183 and 5184** explicitly record `$2100 INIDISP=0E`, brightness **14/15**, forced blank off (per-source JSON SHA256 `8816b95e8e1832af2002b82c8a841a7d258f8d31390f31723a2f97cc86961a0f` and `960108750128708828579592469049fc38fd627b545143949f94147130c7af85`). The pinned native *legacy* renderer's 5→8 expansion/brightness math `(((c << 3) | (c >> 2)) * 14 // 15) >> 3` maps the actual equal-channel RGB555 palette values **21,18,17,16** to the observed RGB5 levels **20,17,16,15** exactly. Native post-brightness RGB8 values are **161,138,130,123**, respectively; the independently archived Snes9x original BGRX pixels may have different RGB8 low bits, e.g. the original RGB5=20 sample is `(165,166,165)`. So this derivation establishes the **RGB5 class correspondence**, not identical original 8-bit DAC output or an effective native PPU palette-index witness.

All output pixels remain unchanged; this source-only analysis authorizes no palette lookup rewrite, guessed fixed brightness, 216-line crop, frame shift, CPU clock repair, QA08/10 release acceptance or approval of procedural HD racer artwork.
