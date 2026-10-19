# RF062: direct native emitted-opcode PC on real Zoom Zoo sound ROM consumption

**19 October 2026. Research instrument and ROM-free tests only. No new original/native replay executed, no runtime correction, no guest memory exemptions or event admission. USA complete original/native events remain 0/45.**

## Which actual causal ambiguity this closes when executed

The prior source-authentic RF054 archive proved 656 real native CPU helper reads in `Snd_UploadBlockList_82EF_M1X0`, including actual `11:C774` read ordinal492 at native CPU master2188739002, and original Snes9x executed `82:82F0 LDA [$63],Y` with *original* operand `11:C774`/A `630D→63D0`, followed by actual source CPU-to-APU port3 `D0` and port2 `63` publications. RF055's generated opcode marker missed the executing M1X0 variant; RF061 improves generated opcode markers but does not bind a marker to a specific real bus read. No original/native clock offsets are proven.

RF062 bypasses the uncertain 'last seen PC' association. In the pinned Baldosa v2 code generator's **actual `Read` IR emission**, its existing `_CURRENT_SOURCE_PC24` supplies the **decoded opcode itself**. For only `82:82F0`, width1 and `cpu_read8_paced`, the emitted C now calls `ur_rf062_cpu_read8_pc(cpu, bank, addr, 0x8282F0u)` in **every** emitted variant, including the independently known executing M1X0 upload. The opt-in wrapper directly calls the *single original* `cpu_read8_paced` and returns its actual byte, preserving the helper's master-clock accounting and bus effects; only afterward does it record ten bounded physical bank11 `C770..C779` observations in native host frame6124. No extra ROM peek, bus read, SPC tick, clock shift, controller modification or host-guest PC inference.

Source-staged code is `tools/qa01_rf062_direct_sound_bus_pc_patch.py`. The wrapper is entirely disposable research C and does not ship. Apply only to a pinned detached worktree (`--root baldosa`) **before regeneration**. RF015–RF028 historic correction staging and earlier original RF049/RF050, native RF054 provenance observers remain separately necessary. The **one real read** is required, so do not 'simplify' by fabricating a ROM data value from a pointer.

## The two independent mandatory qualification stages

**Static generated live-mode gate:** After regenerating native C, execute `python3 tools/qa01_rf062_verify_live_generated.py <actual-generated-C-root> --output <receipt.json>` and fail the build unless the body of the *actual* `Snd_UploadBlockList_82EF_M1X0` contains the direct `82:82F0` read wrapper. Merely seeing a formatted string or an M0X0 call in the ELF is rejected; the static gate is **necessary, not proof of execution**. The `<actual-generated-C-root>` must be the generated sources that really enter the nominated binary, not a fixture or stale checkout.

**Authentic game replay and real bus join:** Build the exact source-qualified 2014 USA Zoo movie, ROM, seed SRAM, expanded controller stream and pinned upstream revision; set `UR_QA01_RF062_SOUND_DIRECT_PC=1` only for the disposable native guest. Retain full original reference and native gameplay logs, binary SHA, source revision and unmasked actual WRAM/SRAM snapshots alongside the strict controls. Reopen new case ZIP and independently frozen actual RF054 baseline archive12149640496 (SHA256 `3ccb209a92045e9e89113442e68af51b85a453a160a9b9efaf8ca0d59e79631c`):

```bash
python3 tools/qa01_rf062_sound_pc_report.py <new-authentic-zoo-case.zip> \
  --baseline <original-authentic-rf054-case.zip> \
  --output <rf062-native-direct-pc-causal-report.json>
python3 -m unittest tests.unit.test_qa01_rf062_direct_sound_bus_pc_patch \
  tests.unit.test_qa01_rf062_verify_live_generated \
  tests.unit.test_qa01_rf062_sound_pc_report -v
```

The dynamic reporter requires **ten contiguous true RF062 read returns** at physical `11:C770..C779`, correct decoded PC `8282F0`, native-local CPU clock/Y/A/D/bank; all **656 authentic RF054 real CPU helper reads** with exact own ordinals and the *same native read clock, physical address, Y, A and D* for the ten joined entries; the original actual `RF049LDA` `11:C774` and `RF050ORIGAPU` `D0/63` publisher; unchanged complete source/native mesh, next Bowl, earned SRAM and input identities. It rejects missing/duplicated events, wrong PC or return byte, time mismatch, scope mismatch, and control drift. **The first jointly consumed candidate `11:C774` must return `D0` on both guests**, never inferred merely from equal numeric port payloads. The source original V/H and SPC local age are recorded independently; native master is never rebased or equated.

## Evidence limits and stop conditions

These code changes have **not yet been inserted into a live rebuilt source-authentic native guest**. No ten recorded RF062 events exist yet. Even if the eventual direct ROM read matches, it proves only a same physical byte at one truly executed guest opcode. It does **not** settle earlier `7E:0063` +5040/+5045 pointer divergence, source/native CPU/SPC global timing, first consumed *different* byte, generated vs interpreted RTI PC/PB treatment, full PCM, or 45 complete events. `qa01_causal_window.py` still requires shared original reader/writer/checkpoint ordinals, actual raw unmasked snapshot bytes, true executed PCs on *all relevant bus readers* and independent QA adjudication. Do not implement a timing or gameplay correction without a first proven consumed wrong state.
