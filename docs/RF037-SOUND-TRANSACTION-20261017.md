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
