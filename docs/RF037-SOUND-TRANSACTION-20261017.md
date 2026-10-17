# RF037: original/native sound pointer to CPU/SPC transport

Source-qualified read-only genuine 2014 USA Zoo investigation. No CPU/APU
timing change, no controller input change, and no release credit (0/45).

RF035 proved that the original bank-82 sound upload instructions execute and
native sound-pointer readers advance from C773 to C774 at the first +5040
residual. The original 1024-opcode and native 4096-read logs then truncated
before a complete +5045 transaction could be observed. RF036 already rejected
two genuinely executed IPL CC publication-order changes: unmasked 128 KiB
WRAM exact-pair counts regressed 51/78 to 46/78 and 0/78.

The RF037 source observer is staged into independently pinned disposable
Snes9x and Baldosa research guests after RF030 through RF035. It captures:

- Original executed LDA indirect-pointer, STA 2143 payload, STA 2142
  sequence and CMP 2142 echo, preserving original CPU internal frame,
  program counter, accumulator, pointer and beam.
- Original CPU 2142/2143 real publication and SPC F6/F7 actual receiver
  reads on original, separate SPC-age and CPU beam axes.
- Native sound pointer/sequence live helper reads in the actual recomp
  function scope, plus CPU port schedule, apply and SPC recipient reads
  with queue target, SPC age and native host frame.

Instrumented clocks and frames remain separately attributed; the source
does not assume that original internal CPU frame 6072 equals native host 6057
without a measured registration. The source windows include both actual
+5040 and +5045 boundaries and neighboring frames. Every bounded recorder
provides a truncation sentinel; source reports must fail closed if either
target window is absent or truncated.

One source-pinned 2014 USA ROM/movie/SRAM/script replay must preserve all 78
unmasked original/native whole-WRAM paired checkpoints, all 13 adjacent
+5034 through +5046 sound samples, genuine Zoo +5163 result, next Bowl
+267, eleven full earned 8192-byte SRAM pairs and fresh guest cold record
reload. These are regression controls, not a route around exact full-event
CPU/SPC logic-tick parity or shipping Windows acceptance.

Decision-changing criterion: actual consumed pointer at both divergent
frames linked to the CPU port3 data value / port2 sequence and the SPC's
received port values. If absent, preserve the coverage gap instead of
guessing a scheduling correction. No timing patch until downstream liveness
and source-correct causal order are demonstrated; no masking or manual
phase shifts. Delete the temporary Actions trigger and restore the shared
campaign immediately after source execution queues.

## Actual first source-executed RF037 run: bounded positive and missing downstream witnesses

Immutable exact research source [run 39002336777](https://github.com/gamesbyian/UR-Recomp/actions/runs/39002336777), source `7a9fdb0c499964cc3cae90cd4cd683457e7a0e93`, 18-file case artifact **12089449113** ZIP SHA-256 `7756fd2194d75b591a98dc488034c27aeae30240042e55d9e667c04fd1ef20e7`. The genuine 2014 USA original movie, ROM and exact input passed source preflight. All plan/build/case/aggregate jobs **green**, and the final candidate did **not** relax strict acceptance. Original source ELF SHA-256 `983d54102abd4042e1f1a82a11cac6f3d2d89473b09c5385e0fd46c600cd377a`, native guest ELF `b90c6f167cf61912a5a2654c921601de8c6ae752d2fdf231cf3d1289813075a4`.

Exactly **51/78** original/native 128-KiB WRAM snapshots match. Sound DP +5039 and +5041 agree; +5040 `$63=73/74` and +5045 `$63=B3/B4` remain the sole sound-pointer leads; `$69` counter is equal at both. Next Bowl +266/+267/+280 have **4/0/4** residual WRAM byte counts. Authentic result +5163, next Bowl +267, all 11 full SRAM pairs and original/native cold 2510-centisecond record reload remain bounded positive controls, *not* a complete USA admission.

The original sound executable emitted **41,325** bounded opcode rows over internal frames 6072–6080. Of these, actual bank-82 sound-upload PCs `82F0/82F2/82F6` executed **4,687 each**, plus **27,264** `8301` echo polls. There are eight explicit per-frame `QA01RF037ORIGOP_TRUNCATED` sentinels (frames 6073–6080): per-frame opcode logging still lost late polls. The source original CPU port hook emitted **2** writes (ports 2/3 at SPC age 103322523/103322541), and source SPC port hook **3** reads, all in the early first-upload/IPL region. No synchronized later `+5045` original writer/recipient proof.

Native observed **20,010** executed sound-pointer helper reads over host frames 6055–6064, **without truncation**; at 6057 the first `Snd_UploadBlock_80D1_M1X0` read is `C774`, after `C773` at 6056; at 6062 the first is `D0B4`, after the previous `D0B3`. However the native APU queue/apply/SPC port observer emits only **346** records, **339** at host 6055 and **7** at 6056, and **zero** during either sound residual frame 6057 or 6062. Therefore the witness proves **live native consumers of each pointer lead**, but *does not* prove the pointer-to-CPU-port-to-SPC payload/echo transaction or justify a timing fix. An original opcode reaching STA does not alone prove the underlying APU port was published.

**Next executable coverage repair on the same draft, no timing patch:** identify whether native AOT byte/word CPU writes reach `cpu_write8/16`, `WriteReg`, `RtlApuWrite` before or after optional mod filters, or escape through a distinct direct B-bus path. Instrument all three source boundaries with per-host-frame limits, preserve a single filter invocation and all return paths, and capture original CPU `S9xAPUWritePort` using a broader, bounded **source-SPC-age bucket** rather than two original SPC-age islands; `ICPU.Frame` is file-local in the original APU translation unit. Reject empty later 2142/3 event windows as *unproven causality*, never as evidence of dead sound. No re-run is justified merely to reproduce the 51/78 baseline.


## Second source-executed run: upstream CPU-port coverage, not an equal-window count

The widened original source writer and native `cpu_write8/16` → `WriteReg` → `RtlApuWrite` probe passed the [complete real USA Zoo run 39006650922](https://github.com/gamesbyian/UR-Recomp/actions/runs/39006650922) at **immutable source `db6c3b2e2ffdb55ea232831626965b6e587f1d56`**. Its case artifact **12091825707**, ZIP SHA-256 **`2785bc65b8ce41bf2c4ddce39b90422a78a27a0f1a84f07a6b546c9095efeeec`** (18 files), and ELF artifact **12091223685**, ZIP SHA-256 **`c38148ebb6d66907ea0ca7bff77c213fa6b3a0e72f2c441c90b3df7fb322198c`**, were downloaded and examined independently. Original core SHA-256 **`78cf49a6771ec06420febc896b7bf0f8109567ce9f246723a029d04521115923`**; native ELF SHA-256 **`10d20b36c76f1a602b68335e8db4847db0d9e64c4cd731309a8693e27c801862`**. The full race mesh, dense +5040 and +5045 sound DP residual, result +5163, Bowl +267, earned 11/11 full SRAM and cold guest record controls remained unchanged. **51/78 unmasked paired WRAM checkpoints; 0/45 complete USA events accepted.**

**Original instrumentation:** 45,645 actual original `S9xAPUWritePort` calls addressed port 2/3, between SPC ages **103322523 and 104199985**; 41,325 printed executed opcode rows with eight opcode per-frame truncation markers (6073–6080), and three earlier SPC F6/F7 read rows. Source age buckets 19–55 each have roughly 1,200 port write rows. The original first two writes were port2=00 at SPC age **103322523** and port3=04 at **103322541**.

**Native instrumentation:** The *short, independent host window 6055–6064* emitted exactly two `cpu_write8` calls (2142=00, 2143=04) at native host 6056, and all six expected upstream stages: two `WriteReg`, two `RtlApuWrite` entries, two post-observer-filter entries; both native APU port writes actually scheduled and applied at target SPC ages **103322524 / 103322541**. Thus the **first two original/natively ordered port payloads agree**, including exact native target SPC age on port3 and a one-cycle port2 observation offset. Native observed 20,010 sound-pointer reads, including consumed +5040 **C774** and +5045 **D0B4**, but only its initial two port writes in the intentionally restricted native host range. No RF037 native writer/port record truncation.

**Critical comparison limitation:** **45,645 versus two is not a matched observation interval.** The original writer covers SPC age through 104199985, whereas the native writer was gated to only host 6055–6064, and its two observed APU port writes are near SPC age 1033225xx. Moreover the original bank-82 sound opcode observer captures original internal frames 6072–6080, not automatically native host 6055–6064. The source did **not** establish a missing native port write or identify a root-cause CPU/APU publication defect. The original `Memory.RAM[0x63]` in the opcode observer is not safely interpretable as the sampled DP pointer without its DP mapping; avoid treating `dp63=00` as a source pointer.

**Independent native ELF instruction evidence:** Disassembly of the exact downloaded native ELF finds `Snd_UploadBlock_80CE_M1X0.part.0` at ELF VA `0x69e390` (size `0x1644`), with compiled `cpu_write16_paced` at call site `0x69eb69` after materializing address `$2142` (`mov edx,0x2142` at `0x69eb5d`), and another `cpu_write8_paced` at `0x69f724` targeting `$2142`. Its `cpu_write8_paced` implementation tail-jumps to authoritative `cpu_write8` at `0x3dffa`; do not infer that either *instruction site actually executed* in the previously gated frames solely from its existence. The original source also contains bank-82 `STA $2143`/`STA $2142` executed opcodes, but matching the *time-aligned* source/native port publication remains unresolved.

**Next exact discriminator (RF037 continuation):** widen **only the native writer coverage** from 6055–6064 to host 6055–6115, preserving the current original SPC age-band and 78 WRAM controls, per-frame bounded recorder sentinels and full recorded port2/port3 values. Compare ordered CPU bus → `WriteReg` → `RtlApuWrite` and native SPC target-ages against the original age-bucket first/last rows; do not compare only gross event counts or pretend original internal frame equals native host frame. If the native source fails to emit at original counterpart ages, investigate `Snd_UploadBlock_80CE_M1X0` branch execution and actual emitted AOT source rather than writing a blind port timer. No global shift, no ROM/input state changes, no Windows QA-ledger update. The temporary workflow used for this source-executed run has already been removed and the shared QA workflow restored.


### Replay-independent writer-report utility

`python3 tools/qa01_rf037_port_writer_report.py path/to/qa01-campaign-case-zoom-zoo.zip --json-out rf037-writer-report.json` parses the immutable original/native replay logs, preserves original SPC-age buckets separately from native host frames/master clocks, reports per-native-frame write/register/APU publication coverage and recorder truncation, and computes *diagnostic only* nearest original same-port, same-value ages for genuine native APU `schedule` events. This does **not** establish paired causality by itself, cannot label a missing native write outside an observer gate, and deliberately sets release credit to zero. Synthetic negative/boundary unit tests live at `tests/unit/test_qa01_rf037_port_writer_report.py`. The extended native run [39010683041](https://github.com/gamesbyian/UR-Recomp/actions/runs/39010683041) is pinned to source `789dc8ba3adca300715cfa4cab76670dc052d9b4`; its case receipt must be separately downloaded and validated before making any claims about later ports. Its one-shot workflow was deleted immediately and the shared workflow restored to the main blob `5f5dda6b20aaa6bbde61f5420ef3bd6dd6977cdb`.
