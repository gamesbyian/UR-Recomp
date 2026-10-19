# RF062 reusable independent same-native-binary ON/OFF examiner (19 October 2026)

This **read-only ROM-free consumer** is separate from temporary instrumented research PR #1941. The disposable branch runs the original and native 2014 Zoom Zoo **twice with exactly the same compiled native binary**: one run sets `UR_QA01_RF062_SOUND_DIRECT_PC=1`, the other unsets it; neither changes the RF018-corrected generated guest code between executions. Because the wrapper performs `cpu_read8_paced` in both conditions, this A/B can test **runtime logging/branch noninterference only**. It **cannot** prove that replacing Baldosa's original paced read site with that wrapper left gameplay or clock cycles unchanged. Comparisons against the separate archived RF054 old-source binary remain a distinct experiment.

## Genuine original/native replay: completed, independently consumed

The research experiment actually completed in [run 39315208102](https://github.com/gamesbyian/UR-Recomp/actions/runs/39315208102), source `c043964800ab35ff643d3fb81707e10cebedbd75`. The primary authentic case step and the original/native build both completed successfully. The final **aggregate** step failed because the extra A/B upload roots made the case member `qa01-case/case-result.json`, while the unchanged coordinator expected it at the artifact root. That is an **artifact transport failure after real replay**, not a CPU/SPC mismatch and not USA event acceptance. The immutable machine receipt is [here](../analysis/data/qa01-rf062-same-executable-on-off-20261019.json).

| Independent observation from actual ZIP | Result |
| --- | --- |
| Genuine case artifact 12219402017 | ZIP SHA256 `b94660b8ffb0cfb1cd35ec9fe3a3c1c8c6b44a46d865272b8cfdad2e62078cbd` |
| Genuine original/native binary artifact 12218451896 | ZIP SHA256 `83233faded8aa546025f59abe50c9ba29f109250f5bcafb2e20cdb5d7780bc37` |
| Original and native supplied input files ON/OFF | Exact same guest-local bytes, 4,264 original / 4,470 native |
| Real original Snes9x and native executable | Same exact SHA on/off, independently reopened from binary ZIP |
| RF054 actual native sound helper | **655 ON / 655 OFF, all 655 lines byte-for-byte equal**, including master clocks |
| RF062 native actual decoded-PC read | **10 ON / 0 OFF**, all ten actual returned bytes have distinct real helper joins; target `82:82F0`, `11:C774 → D0` |
| Complete unmasked Zoo mesh, source result followthrough and next Bowl | Identical between ON/OFF |
| Original source replay logs | 695 lines each; exactly **3** changed host-directory paths (ref.input, complete.script, anchored.srm), no other changed original line |
| Native replay logs after excluding the 10 RF062 diagnostic lines | 2,749 lines each; exactly **11** host elapsed wall-clock lines and **1** workdir script path differ; all other lines equal |

The first version of the producing job's `independent-same-binary-ab.json` marked runtime logging noninterference positive even though it merely reported raw original logs unequal. This **independent** consumer now validates the exact differences, permitting only those three original host-path lines and only elapsed host timestamps plus one native script path. Changed guest opcode, register/clock, CPU/APU publication, source input count or line order **fails**. Importantly, the host wall-time differences represent ordinary replay timing variation; guest-native master clocks in all 655 sampled helper records are identical. Thus this authentic A/B supports *bounded RF062 logging-branch noninterference* and narrows the historic 656/655 disagreement to changes between different compiled builds/source histories, **not to toggling the diagnostic log**.

It **still does not prove** that the research wrapper replacing `cpu_read8_paced` is nonperturbing relative to the **unmodified** native code generator, original/native synchronized opcode epochs, complete 2014 race equivalence, sound PCM parity, Windows product gates or admission of a 10-case research factory. Both guests genuinely race through the result and next Bowl but original/native unmasked state differences remain. **USA 0/45.**

For reproducibility, pin the authentic Actions artifact ZIP SHA256 and run:

```sh
python3 tools/qa01_rf062_same_binary_ab.py \
  --archive /tmp/qa01-rf062-ab-genuine-case.zip \
  --expect-sha256 b94660b8ffb0cfb1cd35ec9fe3a3c1c8c6b44a46d865272b8cfdad2e62078cbd \
  --binary-artifact /tmp/qa01-rf062-ab-genuine-binaries.zip \
  --expect-binary-sha256 83233faded8aa546025f59abe50c9ba29f109250f5bcafb2e20cdb5d7780bc37 \
  --output /tmp/rf062-independent-on-off.json
```

When the separate exact-head binary artifact is supplied, the examiner independently opens `native`, `snes9x_libretro.so`, `snesref` and `SHA256SUMS`, rehashes **all three actual executable files**, and checks the native and original-core hashes against the two case reports. Without `--binary-artifact`, the result explicitly leaves `independently_reopened_compiled_binaries=null`: matching producer-claimed hashes alone are not independent binary authentication. Similarly, source commit ancestry must be separately validated against the actual Actions checkout/plan; the case's `producer-report.json` itself doesn't contain a signed source commit ID. No automatic USA acceptance or factory admission follows a green A/B receipt.

The ZIP auditor also demands the genuine case's `case-result.json` source commit SHA and non-promoting disposition, and byte-matches its primary ON producer report against the separately retained ON copy. Only exact same-case evidence may be compared; old original/native observations are not substituted.

The tool can also consume original on/off directories with `--off`, `--on` and `--output`. The ZIP path is preferred for independent archival reproducibility. It rejects unsafe/duplicate ZIP members, missing real guest logs, altered original/native replay-supplied controller files, source-ROM/movie/window, original core SHA, original replay script SHA, and native executable SHA. Source reports are always re-opened from disk, never copied from CI job conclusion. For **all ten observed RF062 native actual read returns**, it demands a unique genuinely instrumented RF054 CPU helper at the same native-local address, A, Y, D and master clock. Then it compares complete ordered RF054 populations (including DP registers) and exact CPU master values between observation ON and OFF; it requires the full original-emulator replay logs to be byte-identical for a positive result and records all insertion/deletion/replacement blocks, original log SHA values, sound-helper count, full Zoo mesh, terminal followthrough and next Bowl. The result never accepts any USA event and marks native-wrapper substitution equivalence **false** even when the logged ON/OFF result is positive.

**A hold or negative is meaningful:** a 655/655 match at identical native clocks would support bounded logging ON/OFF noninterference, not complete CPU or sound PCM fidelity. Counts or central clocks differing are retained as actual evidence, never masked. The independently merged [genuine 656-vs-655 census](QA01-RF062-GENUINE-EXECUTED-READ-RAW-20261019.md) compared **different source versions**, so it does not substitute for the new same-executable experiment.

The temporary execution PR must be closed unmerged after independent artifacts are consumed. This consumer alone neither triggers an Actions workflow nor authorizes QA01 research-factory scaling; the [source/native executed-event and raw-byte gate](QA01-RESEARCH-FACTORY-ADMISSION-20261019.md) remains separate. **0/45 independently accepted USA events.**
