# QA-01 P0: original/native SRAM preload identity (2026-10-15)

**Owner:** original/native gameplay verification. **Status:** first real cold-load test negative; corrected QA-only native transport under real replay; pending executed corroboration. **No complete USA event credit.**

## First authoritative contradiction

[Run 38782417762](https://github.com/gamesbyian/UR-Recomp/actions/runs/38782417762), genuine original 2014 Crawler Zoom Zoo with RF-015 in the original/native shared build, produced source-qualified result onset +5163/+5163 and successfully classified the race, but the *new independent cold guest* from native's actual +72 post-result battery image failed at boot frame 300. Original Snes9x preserved the earned 2510-centisecond ranked record and all 150 score entries/holders; native boot produced different record bytes. The failure was enforced by `qa01_cold_result_record.py` (not a vague red GHA): `ColdProofError: native lost or rewrote original ranked-record bytes on cold start +300`. The job had successfully generated BOTH original/native boot images at frames 300 and 420. Case artifact 11996444518, GitHub ZIP digest `ea3750af896e4468db6a5a20f4a12b3f7fdf34b7e46ea9a4e1bb3bae3da48aab`. This is a negative test, not a passed cold-start record witness.

## Source-exact transport cause

The imported PINNED `baldosa/snesrecomp@075fbe4c8e0d97b0013be541795c39cb644a9709` desktop host `runner/src/desktop/host_main.c`, roughly lines 3011–3028, anchors cwd to the executable directory **only when no explicit `--config` is passed**. The pinned `runner/src/common_rtl.c` `RtlSramFilePath` at approximately line 2492 generates `saves/save.srm` relative to cwd, and `RtlReadSram` around 2523–2534 opens that path without consulting a separate executable-directory seed.

But the existing QA-only `tools/probe_original_event_complete.py::run_pinned_baldosa` always passes `--config $NATIVE_BIN_PARENT/config.ini` **and executes `subprocess.run(..., cwd=work)`**, while staging `$NATIVE_BIN_PARENT/saves/save.srm`. That image was not the file the native guest read. A previous apparent original/native agreement therefore did **not** independently establish that both engines began with the same archived 2014 battery image. The same wrapper is used by QA-01 Bowl, Switcher, Dragster and RF-017 Zoom Zoo campaign cases; all historical *source-anchored* 1P native comparisons require provenance review. The original Snes9x comparison remains an authentic original source run, and previously observed values are still useful diagnostics, but promotion to fully source-equivalent guest state is blocked until repaired replay.

## Narrow correction

The QA-only wrapper now uses `save_root = work / "saves"`, backs up any prior `work/saves`, stages the byte-for-byte input image there, passes the SAME `--config` and `cwd=work`, and restores the prior save directory after the process. The existing `test_probe_original_event_complete.py` and a new regression in `test_qa01_cold_result_record.py` assert at subprocess launch that the **actual guest cwd-relative SRAM** equals the source, while the executable-neighbor save remains untouched. No CPU/APU, shipping Windows save code, original controller input or acceptance rule changes.

**Crucial distinction:** this is a QA harness transport correction, *not* a game runtime or gameplay fix, and is not evidence of a native product persistence bug. The first experiment demonstrated the source image was not loaded from the expected place; only the corrected real run can determine subsequent replay parity. The independent executable digest, ROM, original movie, race-relative entry and terminal comparison remain distinct source dimensions.

## Next actual decision

Re-run the existing Zoom Zoo campaign against the fixed wrapper, retaining all source and binary SHA evidence and the exact original/native result and fresh cold-guest data. If original/native race-entry frame or result changes, classify the first true state difference from this new shared SRAM root; **do not quote earlier +5163/+5163 as a source-identical accepted witness**. For RF-017, do not generalize local in-order I/O fixes into validated 2014 SRAM equivalence until re-executed with the corrected seed. The CPU/APU/NMI implementation owner retains ownership of the RF-017 emitter fix.

Even if both cold reloads pass, that only proves **fresh guest reads of prepared images**, not durable Windows filesystem persistence, kill recovery, progression acceptance or complete strict frame equality. The ledger remains **0/45 USA complete events**.