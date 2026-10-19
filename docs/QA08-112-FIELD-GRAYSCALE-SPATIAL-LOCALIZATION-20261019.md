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

Five ROM-free synthetic adversarial tests cover full-size channel/class semantics, lower/upper/edge cells, temporal overlap and count conservation, malformed input and fail-closed authentication. **Those local tests are not a replay of the genuine archives.** Authentic spatial counts and exact remaining pixel differences beyond the existing 890,205 benchmark require running against the two source-proven ZIPs. The independent release ledger stays unchanged at 0/12 and original-USA event acceptance at 0/45.
