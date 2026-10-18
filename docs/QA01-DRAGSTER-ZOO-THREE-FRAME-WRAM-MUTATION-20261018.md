# QA-01: executed Dragster→Zoo three-frame WRAM mutation witness

**Genuine source evidence, not gameplay parity: HOLD, 0/45 USA events.** No guest, CPU/APU, controller, timing or acceptance change.

I independently downloaded the 69-member original archive from [Dragster run 39174631932](https://github.com/gamesbyian/UR-Recomp/actions/runs/39174631932), source `542205bd596306ef14a753dd005e391f60a8d413`, [artifact 12154480620](https://github.com/gamesbyian/UR-Recomp/actions/runs/39174631932/artifacts/12154480620), ZIP SHA256 `f036f80d72000b05a5c2edb42152eb433b89fa44c5fc36238ccc73bd143e2947` (independently matched provider). Original producer `dragster-report.json` SHA256 `be912d6dbcfe5d3f4c3c12ce6c00b44b649eb5d679b6ee07a4382872112d1936`. Rehashed all **56** true original/native full WRAM/SRAM images across 14 source-derived offsets; independently recalculated all unmasked differences. The source-owner [#1869](https://github.com/gamesbyian/UR-Recomp/pull/1869) still owns event fixtures, original scripts and fresh cold guest run.

## Exact observed mutations

The new read-only offline tool counts full-image **(byte address, old value, new value)** mutation triples within each true guest, then compares the two guests' *unchanged separately registered source clocks*.

| Fresh original result-relative transition | Fresh native transition | Source mutations | Native mutations | Exact mutation triples present in both |
|---|---|---:|---:|---:|
| +314→+315 | +317→+318 | 641 | 642 | **636** |
| +315→+316 | +318→+319 | 223 | 225 | **221** |
| +316→+317 | +319→+320 | 147 | 147 | **147** |
| +317→+318 | +320→+321 | 195 | 195 | **195** |

First pair has five original-only and six native-only triples; second has two original-only and four native-only. Last two changes agree **exactly** across all actual WRAM mutation addresses and values. No temporal shift, byte mask or tolerance is applied to either original/native *same-relative* comparison. The 3-frame-shifted **structural fingerprint** resembles the separately executed RF056 Bowl 31/31 and 642/642 mutation observations, but neither shared trigger nor legal clock correction has been proven.

True 2014 original movie Dragster result +2080, fresh Snes9x result +2081, Baldosa result +2079. Next active Zoo source +316, fresh original +315 and fresh native +318 **from their respective scored Dragster results**; actual host onset is original 3341 and native 3342, *not the same host frame*. These are genuine strict timing negatives despite visually matched decoded result and next-course payload.

## Persistent source-vs-native memory distinction

Across all fourteen full SRAM image pairs, **the same 13 bytes** differ with identical original/native values: offsets `0x0F31`, `0x0F33`, `0x0FF2..0x0FF9`, `0x0FFC..0x0FFE`. At every full WRAM pair those same thirteen different values appear at corresponding `7E:xxxx` under the *retrospectively observed* relation `SRAM offset = WRAM low address + 0x0E6B`. They are **not waived**: at +308/+312 all 13 original/native full-WRAM differences are value-correlated; at +304 the WRAM count is 17, at +314 it is 43, and +315 onwards the real transition expands to hundreds of unequal bytes.

Authentic Bowl SRAM has different actual values at two overlapping *positions* `0x0F31/0x0F33` and an additional `0x0EF6`, which Dragster does **not** share. Same-value correspondence across two authentic course families cannot establish a specific SRAM copy/write, first reader or non-gameplay relevance.

## Safest next discriminator

The CPU/APU owner should capture the original/native **first actually executed branch/input/state read** preceding the source +314→+315 versus native +317→+318 changes, preserving host, guest, CPU and SPC clocks separately. Compare that causal provenance to RF056 Bowl's +339→+340 vs +342→+343 transition; do not globally rephase controller masks or infer the fault from the matched later byte writes. Existing [RF056 #1864](https://github.com/gamesbyian/UR-Recomp/pull/1864) and [event #1869](https://github.com/gamesbyian/UR-Recomp/pull/1869) already have the precise handoff in PR comments.

For offline reproduction, run `python3 tools/qa01_dragster_zoo_transition_triples_audit.py --original-archive /path/to/github-actions-artifact-12154480620.zip --out /tmp/dragster-triples.json`. The original early ZIP **does not retain actual supplied controller input files**, so this is independent *raw memory* proof, not guest input-consumption proof, Windows shipping parity or complete-event admission. The original Actions artifact has limited retention. The compact [machine receipt](../analysis/data/qa01-dragster-zoo-threeframe-triples-20261018.json) cannot recreate its raw binary captures after expiry.

Three-project apparatus reuse: builds on established original source-event producer, qualified Baldosa/Snes9x route identities and read-only first-divergence crosswalk; no new emulator, sampled-byte mask, research factory or independent acceptance substitution.

