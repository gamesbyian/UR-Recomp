# RF062 reusable independent same-native-binary ON/OFF examiner (19 October 2026)

This **read-only ROM-free consumer** is separate from temporary instrumented research PR #1941. The disposable branch runs the original and native 2014 Zoom Zoo **twice with exactly the same compiled native binary**: one run sets `UR_QA01_RF062_SOUND_DIRECT_PC=1`, the other unsets it; neither changes the RF018-corrected generated guest code between executions. Because the wrapper performs `cpu_read8_paced` in both conditions, this A/B can test **runtime logging/branch noninterference only**. It **cannot** prove that replacing Baldosa's original paced read site with that wrapper left gameplay or clock cycles unchanged. Comparisons against the separate archived RF054 old-source binary remain a distinct experiment.

Once a genuine source-authentic case artifact from #1941 exists, pin its actual Actions artifact ZIP SHA256 and run:

```sh
python3 tools/qa01_rf062_same_binary_ab.py \
  --archive /tmp/real-qa01-rf062-case-artifact.zip \
  --expect-sha256 REAL_64_DIGIT_SHA256 \
  --binary-artifact /tmp/real-qa01-campaign-reference-and-native-binaries.zip \
  --expect-binary-sha256 REAL_BINARY_ZIP_64_DIGIT_SHA256 \
  --output /tmp/rf062-independent-on-off.json
```

When the separate exact-head binary artifact is supplied, the examiner independently opens `native`, `snes9x_libretro.so`, `snesref` and `SHA256SUMS`, rehashes **all three actual executable files**, and checks the native and original-core hashes against the two case reports. Without `--binary-artifact`, the result explicitly leaves `independently_reopened_compiled_binaries=null`: matching producer-claimed hashes alone are not independent binary authentication. Similarly, source commit ancestry must be separately validated against the actual Actions checkout/plan; the case's `producer-report.json` itself doesn't contain a signed source commit ID. No automatic USA acceptance or factory admission follows a green A/B receipt.\n\nThe tool can also consume original on/off directories with `--off`, `--on` and `--output`. The ZIP path is preferred for independent archival reproducibility. It rejects unsafe/duplicate ZIP members, missing real guest logs, altered original/native replay-supplied controller files, source-ROM/movie/window, original core SHA, original replay script SHA, and native executable SHA. Source reports are always re-opened from disk, never copied from CI job conclusion. For **all ten observed RF062 native actual read returns**, it demands a unique genuinely instrumented RF054 CPU helper at the same native-local address, A, Y, D and master clock. Then it compares complete ordered RF054 populations (including DP registers) and exact CPU master values between observation ON and OFF; it records all insertion/deletion/replacement blocks, original log SHA values, sound-helper count, full Zoo mesh, terminal followthrough and next Bowl. The result never accepts any USA event and marks native-wrapper substitution equivalence **false** even when the logged ON/OFF result is positive.

**A hold or negative is meaningful:** a 655/655 match at identical native clocks would support bounded logging ON/OFF noninterference, not complete CPU or sound PCM fidelity. Counts or central clocks differing are retained as actual evidence, never masked. The independently merged [genuine 656-vs-655 census](QA01-RF062-GENUINE-EXECUTED-READ-RAW-20261019.md) compared **different source versions**, so it does not substitute for the new same-executable experiment.

The temporary execution PR must be closed unmerged after independent artifacts are consumed. This consumer alone neither triggers an Actions workflow nor authorizes QA01 research-factory scaling; the [source/native executed-event and raw-byte gate](QA01-RESEARCH-FACTORY-ADMISSION-20261019.md) remains separate. **0/45 independently accepted USA events.**
