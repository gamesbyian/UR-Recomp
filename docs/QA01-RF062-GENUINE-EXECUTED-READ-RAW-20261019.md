# RF062 authentic opcode read and actual original/native full frame: independent QA intake

**19 October 2026. Outcome: a real bounded executed native ROM read has been independently corroborated and paired with original-side opcode evidence and genuine frame-relative raw memory. The *strict research control and full USA event* still fail. 0/45 accepted USA events, 0/12 Windows release QA.**

This review is based on four actual GitHub Actions ZIPs downloaded and rehashed outside their producing workflows. The bounded result, source/binary/frame digests and all explicit failure/unknown gates are pinned in [machine evidence](../analysis/data/qa01-rf062-genuine-opcode-raw-intake-20261019.json). Run the new read-only ROM-free `tools/qa01_rf062_real_read_raw_archive.py` to revalidate all four archives. **The RF062 source patches and experiment PRs remain disposable; do not merge them into the shipping build.**

## Actual performed observations

| Evidence | Actual qualified result |
| --- | --- |
| [Archived original RF054](https://github.com/gamesbyian/UR-Recomp/actions/runs/39161563837), artifact 12149640496 | Original 2014 Snes9x `QA01RF049LDA` at original host frame 6124, decoded `82:82F0`, `11:C774` actual read `D0` (A: `630D→63D0`); original CPU ports 3=`D0`, then 2=`63` |
| [RF062 real-native execution](https://github.com/gamesbyian/UR-Recomp/actions/runs/39308179192), case artifact 12214214743 | **Ten** native `QA01RF062NATIVE` actual returns at host frame 6124, `11:C770..C779`; `seq=5`: `82:82F0`, `11:C774→D0`, actual native CPU master **2188738232** |
| Same run, binary artifact 12215541266 | Real generated `Snd_UploadBlockList_82EF_M1X0` has exactly **one** instrumented CPU read site, actual native executable SHA256 `31790cd4…`. All binaries match their uploaded SHA256SUMS |
| [Separate RF062 raw-frame run](https://github.com/gamesbyian/UR-Recomp/actions/runs/39308189433), case artifact 12216270293 | Same verified native executable, same ROM/movie/controller window, same ten native returned bytes, and **three genuinely retained original/native script-dump frame pairs at +5105–+5107**; all **12 real 128KiB WRAM/8KiB SRAM images** rehashed and independently verified |
| Actual frame 6124 in the raw run | Both guests have verified race entry host frame **1017**; both frame-6124 dumps belong to relative **+5107**. Original/native entire WRAM/SRAM byte-equal at that post-script-dump instant |

Original source and native one-shot *do not share an independently demonstrated CPU instruction-cycle epoch*. The original RF049 execution came from the separately authenticated RF054 archive, not a reinstrumented original guest in the new raw run. However the ROM SHA256 `859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478`, original movie SHA256 `06dce29e9d36997fc2a1fac4bab72180ab6c8096366cfcf05780c1b2dea4b442` and authenticated normalized controller window SHA256 `7b03f40e3401d844c16c7c4e1cc7375e5419f33882793c8187dcebc88dbc8c93` are unchanged in both newer producer cases. The raw evidence's source SHA matches **its own** case-result source SHA, and both actual original/native entry origins are read from that case. Do not substitute origins observed in the earlier nine-frame capture where native entry was 1019.

### Independent evidence reproduction

```bash
python3 tools/qa01_rf062_real_read_raw_archive.py \
  --original-baseline /path/to/qa01-rf054-zoo-case.zip \
  --native-case /path/to/qa01-rf062-native-real-case-20261019.zip \
  --native-binaries /path/to/qa01-rf062-native-real-binaries-20261019.zip \
  --raw-case /path/to/qa01-rf062-raw-case-early-20261019.zip \
  --output /tmp/qa01-rf062-authentic-read-raw-independent.json
python3 -m unittest tests.unit.test_qa01_rf062_real_read_raw_archive -v
```

Actual archive ZIP SHA256 digests, in argument order:

- `3ccb209a92045e9e89113442e68af51b85a453a160a9b9efaf8ca0d59e79631c`
- `b8287234d2fe515ee32b19b3d2a9b0e1bb58104b437de3a5cbe2e32e3af093ff`
- `5d6ffbf1313d83961f496f3c7dc83021323d76fcd977dfc2662ef9afbf6c7b46`
- `85b8585539001210e4a9d2b22e5484034679fbda5d40808300d221e1ec583aed`

The observer separately compares **all ten** live native wrapper rows to the actual `QA01RF054NATIVEBUS` helper on exact `addr, master, A, Y, D` and verifies each has exactly one local match. This is evidence the returned values came through the actual CPU bus helper, not a guessed ROM lookup or address-only join. It does not re-execute a guest inside the independent consumer.

## Negative findings that must travel with the positive result

The native RF054 helper's **frame-6124** observation count changed from **656** in historical RF054 to **655** in the new RF062 replay. Its first sampled address changed from `11:C589` to `11:C58B`, last from `11:C818` to `11:C819`. At the actual `11:C774` read, helper ordinal changed **492→490** and native CPU master **2188739002→2188738232**. These are genuine frame-local trace-population and timing changes; without an independently controlled ON/OFF replay they must **not** be called either missing guest reads or benign probe overhead.

**Independent ordered helper-census alignment (19 October follow-up).** Reopening the two genuine native logs and aligning RF054 helper tuples `(physical ROM address, A, Y, D, dp63/64/65)` reveals **654 matching contiguous observations in the same order**. The historical frame-6124 window alone includes `11:C589` and `11:C58A` before that shared interval; the RF062-observed window alone includes `11:C819` after it. There are **no unmatched RF054 helper observations in the overlapping interior**. Independently recorded native-master clock differences across those matched rows range from **−860 to −688 cycles**, so clock epochs and offsets are not identical or a constant retime. New `compare_native_helper_windows` in `tools/qa01_rf062_real_read_raw_archive.py` regenerates this observation from the two actual archived log populations; adversarial tests deliberately omit a middle read or alter its registers and demand an explicit interior-negative classification. This does **not** prove the real CPU performed no other unobserved reads, that the frame-sampling edge was shifted benignly, or that swapping a native helper for an RF062 wrapper is nonperturbing. In particular, the original and modified builds are **not an exact same-binary A/B control**. A separate disposable A/B uses the *same native binary* with RF062 logging ON/OFF, also without claiming wrapper-replacement parity.

The baseline-vs-instrumented Zoo unmasked whole-memory checkpoint mesh and post-result memory samples **also differ**, although genuine result/onward Bowl progression remains observed. Existing `qa01_rf062_sound_pc_report.py` properly refuses to issue its stronger strict same-baseline-consumption verdict. **Do not alter that strict verifier, fill the missing count or backdate its master clock simply because the returned `D0` agrees.** This new separate intake reports the narrower authentic fact while marking noninterference, complete original/native causality, sound PCM equality and race acceptance as unproven.

The three consecutive raw WRAM and SRAM image pairs are **exactly equal** at the post-script-dump checkpoints, with SHA256 `67ba356b436d911804b24626e7e49f37a60064363d8a9846cd57289d1d07dcf5` for each frame-6124 WRAM and `97ea9642f49f5897f6e6a7d13e31652b025e6dad6580c8ce54128cfa5c167c8b` for each SRAM. No witness samples the WRAM at the **instant of the CPU operand read** or establishes original/native CPU instruction scheduling equivalence. Such equality cannot substitute for the independently accepted whole race.

The raw-run CI case step reported failure from **cold guest script SHA binding**, since the separate three-frame capture added dump commands to the source replay script. The actual producer/classifier still yielded a source-qualified `strict_candidate` with **zero release credit** and all retained original/native raw images; the independent raw audit completed. Do not waive cold guest disk persistence as a workaround. A separate unchanged-script cold run would be needed for that release gate.

## Next research move

The critical next question is no longer whether the native can return `D0` at an attributed `82:82F0` read. **It can, in a real execution.** Now perform an actual instrumented-on versus instrumented-off **same native binary family, identical input, frame-window and control replay** to identify whether the RF062 observation changes the CPU sound upload cadence, and if so, which earlier emitted operation or timing changes. In parallel, the original RF069 reader lane can work on the *late* `7E:01EE`/sound DP divergence with actual read-before-overwrite sequencing. Neither result qualifies ten-case factory expansion without the new QA01 executed-source/raw same-phase contract.

Related experimental PRs: [#1941](https://github.com/gamesbyian/UR-Recomp/pull/1941) and [#1945](https://github.com/gamesbyian/UR-Recomp/pull/1945) remain **DO NOT MERGE** research branches.
