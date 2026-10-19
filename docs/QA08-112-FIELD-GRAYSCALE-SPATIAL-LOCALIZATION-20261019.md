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
