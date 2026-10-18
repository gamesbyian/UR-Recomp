# RF055: genuine Zoo replay proved the generated instruction observer missed the executing mode

**October 18, 2026. Research/negative qualification only; original/native USA complete-event acceptance remains 0/45.** No production CPU/APU, guest game logic, sound queue, input, ROM, observer mask, graphics, Modern product, release package or independent QA ledger change.

## Authentic result and immutable inputs

RF054 [merged #1838](https://github.com/gamesbyian/UR-Recomp/pull/1838) had already matched the actual native CPU helper read of original-ROM operand `11:C774`, accumulator `630D`, and real port3 D0/port2 63 CPU publications, followed by the genuine matching original/native SPC700 receiver PC/port/byte triple. RF053 previously uniquely aligned **all 322 real source SPC receiver reads** inside 1,959 native reads. Neither result registered a common original/native CPU/SPC epoch or independently proved the generated executing 65816 instruction PC.

An RF055 probe was prepared to stamp decoded guest instruction sites `82:82F0/82F2/82F6` directly in pinned Baldosa v2 code generation, before each original instruction's existing IR. One bounded source-qualified original/native replay was attempted after the source fixture unit tests passed.

- **First attempted Actions 39165841295:** setup failed in the synthetic emitter test, prior to building a guest or executing the Zoo game. A nested Python→C quoting error was corrected. This failed setup earns no gameplay evidence.
- **Corrected authenticated Actions [39167048486](https://github.com/gamesbyian/UR-Recomp/actions/runs/39167048486):** exact source `3148dc522e03549823a8ed1305a996dc9bc3a02d`, all **four** jobs green, real original/native Zoo producer exit0 and actual 18-file case [artifact12151730258](https://github.com/gamesbyian/UR-Recomp/actions/runs/39167048486/artifacts/12151730258), SHA256 `18bfc0fd6c9efb4d0d849930aded4657f4d8079be065b0f0e294c08439dbb84a`. Native gameplay log SHA256 `3c8f2c7c47ae23c9c614a315243f6c9ccb1f2d8e6decf595547c01f8cd89ad69`.
- The independently reopened actual built binaries [artifact12151237301](https://github.com/gamesbyian/UR-Recomp/actions/runs/39167048486/artifacts/12151237301), ZIP SHA256 `2b47a6596362c68d39f1b7d1ca8e9491ab7fa7d4cfd87b99b880404681139dc2`, include the exact **16,587,264-byte native ELF** SHA256 `cac96d0ba41ce21eee5d310477ac1266c3fceea1490f7cb52ec98105db09db9e`. Its SHA is exactly the native binary identity independently declared in the game case-result evidence.

## Critical actual qualification: generated probe targeted the nonexecuting AOT mode

The case contains **656 genuine RF054 CPU ROM read-helper records** and **1,312 real port2/3 CPU writer records**, including helper #492 reading `11:C774` at native CPU master2188739002, A=`630D`, Y=`C774`, scope **`Snd_UploadBlockList_82EF_M1X0`**. Yet the native case has **zero** `QA01RF055NATIVEPC` emitted instruction-site records.

Inspecting the *actual linked native ELF* independently resolves the apparent contradiction: it contains precisely **three** RF055 formatted instruction-site strings, PCs `8282F0`, `8282F2`, `8282F6`, **all scoped to `Snd_UploadBlockList_M0X0`**. The ELF contains **no RF055 instruction marker scoped to the executing `Snd_UploadBlockList_82EF_M1X0`**, even though the other RF054 helpers are present and executed. Source staging, successful compilation and all-green Zoo gameplay **do not demonstrate that an instruction observer reached the live mode variant**.

This is a verified *instrumentation coverage failure*, not a proven guest instruction/operand mismatch, missing actual native sound write, or timing correction. It is **not appropriate to count the RF055 decoded-PC witness as proven**. [Machine receipt](../analysis/data/rf055-authentic-zoo-unexecuted-mode-instrumentation-20261018.json) contains all archive/binary hashes and the exact negative claims. Source original/native ROM, movie, seed SRAM and expanded input identities are identical to RF047/RF054. Entire producer objects `zoo_race_mesh`, `zoo_next_bowl_handoff`, `source_terminal_followthrough` agree with the independently preserved immutable RF047 baseline and RF054: **78 unmasked whole-128-KiB WRAM checkpoints, 51 byte-exact, all 92 differing-byte occurrences retained; original/native Zoo result +5163; authentic next Bowl +267; eleven earned entire SRAM pairs and cold ranked-record reload unchanged**. Classification remains `strict_candidate`, release credit0.

## Independent authentic local CPU timing constraint

The *earlier* authenticated RF054 case archive12149640496 (SHA256 `3ccb209a92045e9e89113442e68af51b85a453a160a9b9efaf8ca0d59e79631c`) holds 38 actual original CPU→APU publication rows and 1,312 actual native CPU publication rows. Taking adjacent port3→port2 rows at their **same-domain** CPU clocks shows **all 16/16 original and 656/656 native intervals are exactly 50 CPU master clocks**. Original beam conversion uses `(V₂−V₁)×1364+(H₂−H₁)`; native uses the difference of authentic `CpuState.master_cycles`. The original source SPC-local publication gaps in those 16 pairs are 2 ticks ×8 and 4 ticks ×8. The 656 native ROM helper addresses are contiguous `11:C589..11:C818`, and target `11:C774` is sequence #492. [Machine receipt](../analysis/data/rf055-original-native-cpu-local-writer-interval-census-20261018.json).

This narrowly supports matched *intra-CPU write pacing* in the observed intervals, **not** identical original/native CPU-SPC epochs, identical upload instruction lengths, SPC queue visibility, sound samples or 45 complete gameplay events.


## Real 656-transaction AOT executable and CPU bus correspondence (additional independently reproduced audit)

[Actual RF055 case12151730258](https://github.com/gamesbyian/UR-Recomp/actions/runs/39167048486/artifacts/12151730258) and [actual native binaries12151237301](https://github.com/gamesbyian/UR-Recomp/actions/runs/39167048486/artifacts/12151237301) were downloaded/rehashed again, with the full [immutable RF047 baseline12124654817](https://github.com/gamesbyian/UR-Recomp/actions/runs/39096831814/artifacts/12124654817) used as an independent comparator. These three original artifacts are all that the [new fail-closed offline auditor](../tools/qa01_rf055_native_elf_cpu_sound_path_audit.py) needs. It neither reads the local ROM nor launches an emulator. Reproduction on Linux with GNU binutils:

```bash
python3 tools/qa01_rf055_native_elf_cpu_sound_path_audit.py rf055-zoo-case.zip \
  --binary rf055-native-binaries.zip \
  --baseline rf047-zoo-baseline.zip \
  --out rf055-live-native-aot-audit.json
```

**Every one of the actual 656 native CPU ROM read-helper rows is within `Snd_UploadBlockList_82EF_M1X0`** at native host6124. Each effective 24-bit operand is strictly contiguous from `11:C589` to `11:C818`, equals `11:0000 + live Y`, and matches the following two same-scope *real* `RtlApuWrite` port publications at the same Y. **All 656/656 original native-ROM read→port3 gaps are exactly 30 *native CPU master clocks*, and 656/656 port3→port2 gaps are exactly 50; all 1,312/1,312 port bytes agree with the observed low accumulator byte.** The original 2014 Snes9x independently measures 16 genuine port3→port2 intervals of 50 source-local CPU master clocks, but their two source clock origins are not registered. Source-matched native `11:C774` remains actual read ordinal492, master2188739002, followed by port3 D0 at2188739032 and port2 63 at2188739082.

The independently reopened, exact **16,587,264-byte native x86-64 ELF** (SHA256 `cac96d0ba41ce21eee5d310477ac1266c3fceea1490f7cb52ec98105db09db9e`) contains a separate *actual live-mode* optimized function `Snd_UploadBlockList_82EF_M1X0.part.0` at virtual address **`0x6aea70`**. `nm -nC` and `objdump -d -M intel --disassemble=Snd_UploadBlockList_82EF_M1X0.part.0` independently show this ordered concrete CPU data/codepath:

| Native x86 VA | Statically compiled operation |
| --- | --- |
| `6aeb39` | `rol dx,0x8` (first accumulator exchange) |
| `6aeb96`, `6aebae` | `cpu_read16_paced`, `cpu_read8_paced` (DP pointer low word and bank) |
| `6aebc3`, `6aebcf` | `add esi,eax`, `cpu_read8_paced` (indexed 24-bit sound data) |
| `6aec3e`, `6aec4a` | `mov edx,0x2143`, `cpu_write8_paced` (CPU port3) |
| `6aec79` | `rol cx,0x8` (second exchange) |
| `6aecb5`, `6aecc4` | `mov edx,0x2142`, `cpu_write8_paced` (CPU port2) |

These correspond anatomically to the independently pinned generated `L_82EF_M1X0` ROM loop, but **multiple native `cpu_read8_paced` callsites occur elsewhere inside this function**, and the RF054 dynamic logger captures a function-scope name rather than a return address. Thus even this stronger *static executable plus genuine dynamic effect* bridge does **not** establish which particular native x86 callsite a given 656-read operation executed, nor produce the missing live `82:82F0` native instruction marker, nor reconcile absolute CPU/SPC clocks or sound PCM. No timing intervention follows. The exact executable/case hashes and all preserved controls are in [the machine receipt](../analysis/data/rf055-native-elf-live-upload-656-transaction-audit-20261018.json); negative unit fixtures test changed opcodes, compiled function scope, source-bank operands, port values and cycle deltas.

## Resolution, integration boundary and next causal question

The previously drafted RF055 codegen observer, companion reporter and unit fixtures were deliberately **retired from PR #1841**. They never provided an executed native PC marker and duplicate [independent research PR #1845](https://github.com/gamesbyian/UR-Recomp/pull/1845). This PR retains only unique source-authenticated negative provenance and interval evidence, and leaves the one live opcode investigation to #1845. The precise binary/mode finding was [communicated on #1845](https://github.com/gamesbyian/UR-Recomp/pull/1845#issuecomment-6255471413).

The next qualified narrow test must ensure the *actual generated, executing* `Snd_UploadBlockList_82EF_M1X0` branch contains a read-only source-stamped instruction-site marker and that the logger actually executes immediately before the genuine `11:C774` helper, then require source-original operand, real native CPU ports, receiver and unchanged unmasked RF047 controls. A build should **fail before running a case** if the executing AOT variant lacks the intended static observer. The other independently observed, earlier **Zoo +5040/+5045 live sound-pointer differences** still require original/native causal producer→consumer semantic registration before proposing *any* CPU/SPC timing correction.

Do not retry RF042's rejected equal-age retime, globally shift SNES clocks, invent SPC polls, mask WRAM bytes or claim a complete USA event from this research.
