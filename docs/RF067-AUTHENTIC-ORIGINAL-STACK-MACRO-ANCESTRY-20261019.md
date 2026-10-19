# RF067: original source stack macro writer-to-return ancestry

**Genuine historical original/native Zoom Zoo evidence.** The previous RF064 experiment exposed that 903 actual original stack pulls lacked an RF063 logged *getset read entry*. It did not mean the reads failed to occur. This independently examines **RF045's 1,806 actual source stack macro completions** on their own original-local ordered axis, without placing them at guessed native clock positions or manufacturing a missing RF044/RF063 read.

## What was directly observed

I reopened the exact authenticated [2014 USA Zoo run 39216237965](https://github.com/gamesbyian/UR-Recomp/actions/runs/39216237965), case artifact [12170321915](https://github.com/gamesbyian/UR-Recomp/actions/runs/39216237965/artifacts/12170321915) SHA-256 `7891a24124c67f414e9b00ed2bb1dbe2e59e4a2b6c50b558e920c25d885e63ea`, original log SHA-256 `0dfe14195cffc9fc2e044adb372f81c9440e94e4b0e5330671906934d475bfad`. All 1,806 `QA01RF045ORIGSTACK` local ordinals are contiguous: 903 genuine pushes and 903 genuine pulls.

The [RF067 consumer](../tools/qa01_rf067_original_macro_lineage.py) reconstructs the latest **actually logged source macro write**, individually for each physical byte of a byte or word pull. It does not initialize missing bytes or assume there were no other writers. **902/903 original pulls match every byte of their last observed earlier macro writer, with zero contradictory byte values.** The first observed word pull (`seq=1`, address `01F0`, returned `9141`) predates a writer in the bounded stream, so its ancestry remains **unknown**.

At source stack byte `01ED`, all nine host frames 1017..1025 contain two `0x81` pulls (source post-call context `81:8A7C`) preceded in the observed macro sequence by `0x81` pushes (`81:8A7D`), and one `0x26` pull (`80:B0EB`) preceded by a `0x26` push from the interrupted source PC context `82:D4F0` (4 times) or `82:D4EE` (5 times). These are **post-macro PC snapshots**, not automatically actual fetched opcode PCs. This local lineage adds substance to RF061's separately observed original/native real NMI status consumption of `0x26`, but does not align native and original clock phases or prove equality of saved PC/PB.

## Negative boundaries

These are **macro-level write→returned-value relationships**. RF045 recorded completions, not atomically ordered SNES bus micro-operations. A write performed elsewhere (DMA, another nonmacro CPU path, interrupts within getter), an unobserved earlier writer, or nonstack consumers may invalidate a universal last-writer assertion. Exactly matching the observed macro population is not a proof of all original or native bus accesses. RF064's *separate* original getset reader still observed zero qualifying read-entry events. The current full 78 × 128-KiB unmasked WRAM mesh remains 51 exact/27 differing with 92 byte-difference occurrences, original race +5163, next Bowl +267, independent 0/45 complete USA events and Windows release QA 0/12.

RF067 does not change emulated gameplay, source or native code, controller timing, stack bytes or masks. Its verifier preserves all unknown initial bytes, reports **raw mismatches** if any, validates real stack-pointer/width/physical-address semantics, forbids missing/duplicated RF045 ordinals and source truncation, and pins ZIP/log SHA-256 plus result/WRAM/SRAM control metadata. It is a historical source-side consumer, separate from RF066's **future** actual post-return shared-ordinal producer.

## Reproduce exactly

```bash
python3 tools/qa01_rf067_original_macro_lineage.py /path/to/qa01-campaign-case-zoom-zoo.zip --out /path/to/rf067-authentic-lineage.json
python3 -m unittest tests.unit.test_qa01_rf067_original_macro_lineage -v
```

For a new RF066 genuine producer output, do not paste or adapt this old RF064 receipt. Reopen the **new immutable archive**, validate that its source read-return events are complete, and independently retest lineage against the new exact binary/input/movie/ROM identity. The first *differing* byte's actual original/native reader before overwrite remains a separate QA01 causal-window gate. **0/45 USA, 0/12 release QA.**
