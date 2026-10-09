# Baldosa/UR-Recomp independent symbol crosswalk: first reviewed findings

**Date:** 2026-10-09. **Input provenance:** local `analysis/generated/symbols.json` from `docs/SYMBOLS.md`; external imported `baldosa/uniracers-recomp` commit `10b864b9d14a7b7416dd909eb7b054c88faef101`. Import verification: 18/18 original metadata/routes/comparison files and 16/16 subsequent AOT analyzer/tool files matched their upstream SHA/size pins. Run `python3 tools/build_baldosa_symbol_crosswalk.py --differences` to regenerate overlaps, and `--out analysis/generated/baldosa-symbol-crosswalk.json` for a full candidate register.

## Scope and measured overlap

Initial comparison of pinned external source and pre-correction local canonical JSON produced **1,300 distinct external address/kind keys**, **142 local address/kind keys**, **49 exact overlaps**, **1,251 external-only** keys and **93 local-only** keys, after normalizing `00..03:8000..FFFF` to their `80..83` LoROM mirrors. All 49 overlapping keys used different labels; **different spelling is not evidence of conflicting behavior**. Counts describe parsed symbol rows, not code coverage, named instruction percentage or verified runtime equivalence. This register is derived and should be recomputed after any canonical correction; the first counts deliberately identify the pre-correction comparison baseline.

## Concrete static correction: indexed result slots beginning at SRAM $77:0618

Our former `docs/SYMBOLS.md` RAM row labeled `77:0618` and `77:061A` fixed last-race P1/P2 values. Baldosa's `decomp/ram.txt` instead calls the 96-byte range beginning at `770618` `sLeaguePointTable`, and describes separate P1/P2 *race-result blocks* at `770755` and `7707BF`, with total time at their later offsets.

More decisively, the mechanically recompiled USA code in external `src/gen/bank80_part0f_v2.c`, routine `Scores_StoreResult_FastRom_M0X0` at **$80:F877**, shows: read 16-bit index `[DP+$CC]`; read a 16-bit value at `$770678+index`; compute `X = 8*index + 2*that_value`; write a word at `$770618+X`, and optionally a second at `$77061A+X`; then checksum. The **variable address calculation is proven in this source**, so treating the two fixed base words as global per-race P1/P2 storage is unsound. The project canonical row is consequently narrowed to `Save_IndexedResultWordTable`; its exact slot/league/person semantics are deliberately unresolved. Reference: [upstream generated function](https://github.com/baldosa/uniracers-recomp/blob/10b864b9d14a7b7416dd909eb7b054c88faef101/src/gen/bank80_part0f_v2.c).

**Impact audit required (QA-02/QA-03 and Records):** inspect existing host result capture, tournament fixture settlement, SRAM profile projection, guest-result provenance and derived stats for any *fixed* reads of `77:0618/061A`. Do not equate those with live P1/P2 race results without evidence. Prefer a fresh original/native trace of `80:F877` with $CC, `$770678+index`, computed X, writes to indexed `$770618+` and actual result screen fields; crosscheck true P1/P2 result blocks at `$770755+` and `$7707BF+`. If the former source row only affected documentation, no runtime fix is necessary. This static finding is **not** a reproduced player data-loss defect.

## Other high-value overlap probes

- **$82:E02E:** our `Race_LoadPresentationAssets` vs baldosa `League_LoadPodiumGraphics`. Distinguish contexts by instruction-time callers, asset IDs and PPU/OBJ output. Our existing graphics-family provenance supports a race asset load; external name may refer to another callsite or could be too narrow.
- **$81:8050:** our `Race_HandleCheckpointFinish` vs external `Uni_CheckLapLine`. Reuse existing original Zoom Zoo lap/contact evidence and determine which actions the routine actually accepts before changing either label.
- **$81:8B95:** our `Course_SampleRuntimeSurface` vs external `Uni_ProbeCollision`. These may describe successive portions of the same work; independently identify probe reads, output buffer, contact semantics.
- **$83:8AF7:** our cartridge-memory self-test vs external SRAM mirror check. Names likely describe the same SRAM-size check at different abstraction levels; low priority.
- **$83:F296/$83:F2BB:** independent rider frame-pointer/header decoders. Compare against our actual pose provenance as a potential graphics QA accelerant, without replacing the established shipped art source pipeline.

## Boundaries

Prioritize falsifiable implementation effects over renaming hundreds of symbols. Each fresh correction requires the USA-ROM identity, one relevant executed source instruction/trace or byte decode, competing explanations and a downstream regression where product behavior depends on it. Do **not** alter the 0/45 completed-course denominator, QA readiness gates or game physics based on a symbol-table comparison alone.
