# RF037 follow-up: CPU-port writer-clock projection (research-only)

Date: 2026-10-17. **No guest/runtime fix, receiver equivalence, release QA or event admission. USA remains 0/45.**

## Immutable source and verification

Re-examined the *genuine USA Zoo* original/native [RF037 V5 run](https://github.com/gamesbyian/UR-Recomp/actions/runs/39010683041), case artifact 12093176984, SHA-256 `f2f9cf77efedd371dbcf7c61b3a54431e79a6fb5f951884ca66f53d9dfb7941a`, source `789dc8ba3adca300715cfa4cab76670dc052d9b4`. Independent ZIP rehash matched. Original `QA01RF037ORIGCPU2` captured 45,645 port2/port3 calls with source SPC ages; native `QA01RF037NATIVEUP kind=rtl-apu-enter` captured 56,041 calls with live native CPU master clocks and host frames. Across the canonicalized prefix, **45,645/45,645 port/value pairs match** after only the three previously documented same-original-SPC-age order ties. No native writer capture truncation. This is the already-merged RF037 writer-equivalence witness, not a new game pass.

## An intentionally limited independent clock projection

The new small, read-only artifact analyzer `tools/qa01_rf037_port_clock_crosswalk.py` reuses the **existing** RF037 ZIP parser, same-age normalization and exact source/native port values rather than adding a second trace producer. Anchoring the first actual matched CPU writer pair at original source SPC age `103322523` and native CPU master `2164382860`, it calculates

`residual = (original_SPC_age - 103322523) - (native_master - 2164382860) * (15664/328125)`

where 15664/328125 is the nominal native SPC-per-master ratio. Values are *relative source-age minus projected-native-master differences*, **not** measured SPC receive delays. Original source age is sampled at `S9xAPUWritePort` (after its APU execution boundary); native master is sampled at `RtlApuWrite` entry (before queuing). These are different call sites. Original same-SPC-age tie order and quantization can additionally distort individual samples; this is strictly an exploratory clock-axis crosswalk.

Selected actual source-matched native host frames (median residual in **nominal SPC cycles**):

| Native host frame | Matched writes | Median |
| --- | ---: | ---: |
| 6056 | 2 | +0.550 |
| 6073 | 1,312 | +16.249 |
| 6090 | 1,312 | +13.948 |
| 6091 | 1,289 | +16.096 |
| 6092 | 1,281 | +21.310 |
| 6093 | 1,310 | +21.332 |
| 6108 | 38 | +18.795 |

A localized **change in the distribution** occurs *inside native host 6091*, around original matched port stream indices **24,385–24,395** (source SPC age about `103919200–103919600`). Shortly before this region, projected residual medians cluster near +14; afterward they cluster near +21. Both ports change, not just a port2/port3 composition artefact. The full per-frame and per-port medians, bounds, and counts can be regenerated from the unmodified case ZIP via

`python3 tools/qa01_rf037_port_clock_crosswalk.py qa01-campaign-case-zoom-zoo.zip --json-out rf037-clock-crosswalk.json`

**This is not yet a demonstrated cycle error or an identified writer.** A CPU code-path change, original APU execution debt, source-age quantization, native host timing, and actual SPC recipient timing remain competing explanations. Do **not** insert a seven-cycle shift, reschedule the queue, or infer that an SPC instruction reads the same value solely from matched CPU publications.

## Decision-changing next measurement

At the matched source port ordinal ~24,390 (native host 6091, source age ~103919300), collect **real original SPC F6/F7 read opcodes** and **native queue schedule/apply plus F6/F7 real reads** on their separately labelled clocks. Compare values and source recipient PCs and bracket the apparent distribution change; include the earlier +5040/+5045 sound-pointer epochs as distinct windows without pretending that host frames directly equal original ICPU frames. Fail closed on missing/truncated records, preserve the authentic Zoo +5163 and Bowl +267 and all existing unmasked checkpoint/SRAM/cold controls, and leave independent QA to its lane. Continue the separate 01ED–01F1 last-writer/next-reader stack investigation. No production CPU/APU timing change is justified by this artifact.

The three-project reuse preflight selects the **current UR first-difference/checkpoint and RF037 writer analyzers**, with source-pinned Baldosa CPU timing as the implementation context. Malmazuke effective-address access-mode reuse remains conditional on a genuinely missing stack decode and requisite source registers. No parallel emulator, release gate or new workflow is introduced.
