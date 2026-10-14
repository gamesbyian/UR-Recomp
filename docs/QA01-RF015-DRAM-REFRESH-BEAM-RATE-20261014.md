# QA-01 / RF-015: Baldosa's one-frame-short result phase is a DRAM refresh rate defect (2026-10-14)

**Scope:** Causal adjudication of [RF-015](RESEARCH-FINDINGS-QUEUE.md#product-core-baldosas-result-phase-is-one-frame-short-rf-015-handed-to-qa-01) on the pinned Baldosa product core (`gamesbyian/uniracers-recomp@10b864b`, framework `baldosa/snesrecomp@075fbe4`), plus the smallest faithful correction and its deterministic regression. Compact evidence: [`analysis/data/rf015-dram-refresh-beam-rate-20261014.json`](../analysis/data/rf015-dram-refresh-beam-rate-20261014.json). **No release-gate or complete-event credit.** Official strict USA complete events stay **0/45** until the QA-01 oracle accepts one with an exact candidate.

## Result

The 2P raw `7E:009F = 0x84` result phase is a CPU-bound, NMI-disabled VRAM upload followed by a two-edge VBlank wait. Pinned Baldosa gives the guest CPU about **1.14 extra master clocks per scanline (0.086%)** because `snes_refresh_charge()` charges the 40-clock DRAM refresh once per 1364 clocks of *execution* instead of once per 1364-clock *beam line*. Over the ~34-field upload that surplus (~9,300 clocks) moves the arrival at the wait from **V=230** (just after VBlank begins, as on Snes9x) to **V=224** (just before it). The original therefore waits one extra whole field and Baldosa does not: **34 vs 33 frames**.

With the one-line correction staged by [`tools/baldosa_dram_refresh_beam_rate_patch.py`](../tools/baldosa_dram_refresh_beam_rate_patch.py), Baldosa's semantic WRAM equals Snes9x at **every compared frame** of the RF-015 seed population, through the race, the 34-frame result phase and the restored menu (table below).

## How the earliest causal difference was found

All runs are local, from current `main` tools and exact binaries: canonical USA ROM `859ec99f…`; Snes9x core and patched bsnes core from `bootstrap_toolchain.py`; UR `snesref` with the dual-controller patch; Baldosa built with the research two-seat shim (`tools/research_baldosa_2p_input_patch.py`). The unpatched build is **bit-identical** to the research binary `279d053f…`, so the A/B differs by one framework line.

1. **The 5196 sound-queue difference is not a defect.** Snes9x and bsnes, both original references, differ from each other in exactly the pattern RF-015 attributed to Baldosa: the `7E:2000` queue step at 5196 vs 5197, the `$C6` decrement at 5197 vs 5198 and the `0x84` onset at 5198 vs 5199. Both still run the phase for 34 frames. It is a host-frame phase effect between correct implementations. Baldosa matches **Snes9x** byte-for-byte in semantic WRAM from 5192 through 5230, including those steps.
2. **The only Baldosa/Snes9x difference is the end of the phase.** `0BDE=00` lasts 2 frames on both originals before the `0x16` restore and 1 frame on Baldosa (restore 5231 vs 5232).
3. **The original's extra frame is a VBlank-wait miss.** A disposable Snes9x executed-PC trace (hosts 5195–5233; emulation unchanged, 0 differing bytes) shows no NMI from 5225 to 5231. The upload loop `82:B1F2..B202` (with callee `82:B293`) runs ~12,547 instructions per field, ends at 5230 V=200, and post-load code (`80:D29C…`, `83:99F6`) reaches `80:FAC9` at **V=230**. VBlank is already set, so `80:FAD0 BMI` spins until V=0 and `80:FAD9 BPL` until the next V=225. A read-only Baldosa observer (`$4212` reads, `$2100/$2116/$4200` writes, beam V/H, master clock; 0 differing bytes) shows Baldosa's first wait read at **V=224** with bit 7 clear, so both edges complete in the same field.
4. **The time difference accumulates uniformly.** From the matched forced-blank store `80:D205 STA $2100`, Baldosa reaches each of the six `82:B1DD STX $2116` upload checkpoints progressively earlier: −200, −1,908, −2,528, −3,028, −4,896 and −6,520 master clocks at 7.47M clocks (0.087%). This rules out a single event, APU servicing (NMI disabled, upload loop never touches the APU) and NMI scheduling.
5. **Per-instruction costs are identical.** Snes9x's executed costs for one two-byte iteration are `JSR` 46, `LDA abs,Y` 38, `INY` 14, `BEQ` 16, `CMP #` 16, `RTS` 42, `STA long $2118/9` 38 (SlowROM, MEMSEL=0), `DEX` 14 ×2 and `BNE` 22: 470 clocks, plus one 40-clock refresh on every one of the 262 lines. Baldosa's generated blocks (`Res_LoadToVram_M1X0`, `Res_ReadByte_FastRom_M1X0`) charge exactly 46/68/58/84/68/58/88 = 470 including paced bus accesses. The residual is per line, outside instructions.
6. **Refresh rate.** `runner/src/common_cpu_infra.c::snes_refresh_charge` accumulates execution clocks into `s_refresh_phase`, adds `40 * lines`, then sets `g_refresh_charged_upto = g_cpu.master_cycles`, *after* the stall. The stall never counts toward the next line, so one refresh lands per 1404 beam clocks. Predicted CPU surplus: 1364·1364/1404 − 1324 = 1.14 clocks per line, **0.086%**; measured 0.087%. Unchanged upstream at `baldosa/snesrecomp@ec8a3e7` (2026-10-14).

The APU port write-order contrast recorded in [the VBlank-wait source contract](QA01-VBLANK-WAIT-SOURCE-CONTRACT-20261014.md#rf-015-verified-data-bank-mapping-and-16-bit-apu-port-order-contrast) remains a real source difference. It is **not** the RF-015 cause: the correction never touches the APU path and closes the whole phase.

## Correction

Keep the watermark at the pre-stall clock (`g_refresh_charged_upto = m;`) so the next delta counts the stall toward the next line. The per-instruction cost model, park/exempt path, teleport guard, rollback accessors and both execution tiers' call sites (`WatchdogCheck`, interpreter) are unchanged. The script is idempotent, refuses any other framework revision and is meant for disposable pinned checkouts, in the same way as the other `tools/baldosa_*` stage scripts.

Remaining approximation: hardware refreshes at a fixed beam position (about H=538) in each line. Baldosa's accumulator places the stall at an execution-relative phase. The rate is now correct; the in-line phase can still differ by up to 40 clocks at a single instant.

## Deterministic regression

[`tests/unit/test_baldosa_dram_refresh_beam_rate_patch.py`](../tests/unit/test_baldosa_dram_refresh_beam_rate_patch.py) embeds the verbatim pinned function, applies the patch tool and **compiles and executes** both versions under the measured `82:B1D8` iteration (block entry charges as in generated code) for 34 fields. Corrected: 8,908 stalls for 8,908 lines (1,324 CPU clocks per line). Pinned: 8,654 stalls and a 10,182-clock surplus, reproducing the RF-015 mechanism. The patcher's anchor drift, duplicate and marker-tamper rejections are tested too.

The original/native regression is the existing paired tool on the RF-015 reproducer with the corrected binary:

```bash
python3 tools/qa_frontier_original_crosscheck.py paired --native-launcher baldosa \
  --native-exe <Baldosa 10b864b + research 2P shim + baldosa_dram_refresh_beam_rate_patch.py> \
  --seed 50036056 --arm rotation --lag 0 --finish-hold 4000 \
  --frames 1128-1140,1620-4800/60,4801-6400 --snesref <snesref> --core <snes9x|bsnes patched> \
  --ledger <ledger.json> --work W --out R
```

Expected: entry 1134 = 1134, `exact_field_agreement`, 0 differing semantic-WRAM bytes, `0x84` phase 34 = 34.

## Validation

**2P RF-015 population (paired race-relative tool, lag 0, frames to host 6400; entry 1134 = 1134 in every run).** Unpatched, the research reported 33 vs 34 in 9 of 9 seeds with this exact executable; seed 50036056 reproduces locally.

| Seed (arm) | Corrected vs Snes9x | Corrected vs bsnes | `0x84` frames native / original |
| --- | --- | --- | --- |
| 50012000 (balanced), 50012144 (p1-focus), 50012215 (p2-focus), 50036002 (p2-focus), 50036005 (alternating) | exact, 0 bytes | exact, 0 bytes | 34 / 34 |
| 50036056 (rotation) | exact, 0 bytes | onset 5198 vs 5199 | 34 / 34 |
| 50024004 (rotation) | onset 5085 vs 5086 | exact, 0 bytes | 34 / 34 |
| 50048000 (balanced) | onset 5014 vs 5015 | onset 5014 vs 5015 | 34 / 34 |
| 50024003 (alternating) | exact, 0 bytes (to host 9000) | exact, 0 bytes (to host 9000) | same onset 4740; no `0x16` restore inside the window |

Duration now matches on every completed pair: 7 of 9 seeds are byte-exact against Snes9x, 7 of 9 against bsnes, and 8 of 9 against at least one reference. Where Snes9x and bsnes disagree about the onset field (50036056, 50024004), the corrected core matches one of them exactly. **Seed 50048000 is the one remaining genuine residual**: both references agree on onset 5015 and the corrected core starts the whole phase one field early, the same sign as the Switcher +4664 onset below.

**No-input attract black-screen census (bsnes reference, host windows around the five loads).** Unpatched: `941–1097`, `1422–1547`, `3632–3761` against bsnes `941–1098`, `1423–1547`, `3632–3762`. Corrected: `3632–3762` now exact; `941–1097` and `1422` unchanged. That residual is a different mechanism, an SPC700 upload that ends ~54 lines early ([RF-016](RESEARCH-FINDINGS-QUEUE.md#live-queue)). All 46,414 port-2 writes align one-to-one by value; the lead builds during the IPL handshake (~19k clocks) and steadily over the ~71-field stream (~50k, 655 vs 653–654 bytes per field). Baldosa clocks the SPC700 at 17,088 cycles per field (~1.02696 MHz) against the references' 32,040 Hz × 32 (~1.02528 MHz). A disposable 17,060 A/B fixes the 941 load but moves two later boundaries one field late, so no rate change is adopted.

**QA-01 strict producer, unchanged (`probe_original_event_complete.py --native-backend pinned-baldosa`, Baldosa's `snesref`, Snes9x core, archived 2014 source movie), classified by `qa01_event_campaign.py classify`:**

| Case | Unpatched `c3471741…` | Corrected `cd5ba13f…` |
| --- | --- | --- |
| Zoom Zoo (course:02, circuit-a) | `strict_divergence`, terminal +5162 vs +5163 | **`strict_candidate`**, +5163 = +5163, no sampled disagreement |
| Switcher Race B | `strict_divergence`, terminal +4702 vs +4704 | `strict_divergence`, terminal **+4703** vs +4704; first disagreement still the `0x84` onset at +4664 |

Switcher's guest-relative axis is the oracle's. Its race matches guest-relatively through +4663; the `0x84` onset is one frame early at +4664 (open, same sign as 2P seed 50048000); and the result phase was one frame short and is now corrected (+4702 → +4703). The native race **entry** is two frames late (1081 vs 1079) in both builds, a separate mechanism this correction does not touch. The baseline's equal *absolute* result frame (5783 on both hosts, noted in the [census](ORIGINAL-COURSE-EVENT-CENSUS.md)) was therefore two errors cancelling; corrected, native presents the result at 5784.

`strict_candidate` is the comparator's own label for "not an independently adjudicated course pass" (`release_credit: 0`). The official census stays **0/45**; promotion needs independent re-execution, ideally hosted through the opt-in `baldosa_refresh_beam_rate` input added to `qa01-event-campaign.yml`, and independent QA adjudication of result, menu restoration and persistence.

## Shipping boundary and what remains

- **Product.** The pinned shipping Windows Baldosa build does not yet carry the correction. Staging it there changes the nominated executable, so it is a separate change with its own Windows acceptance run. Frame-indexed probes may legitimately move by a field where loads become faithful.
- **Legacy rollback (`cd5875c`).** It has the same `snes_refresh_charge` code but errs the other way (RF-012/RF-014), because its synthetic beam/`$4212` deficit dominates. This correction alone would not fix it, so it is not staged there. Per the [framework lineage check](QA01-VBLANK-WAIT-SOURCE-CONTRACT-20261014.md#actual-2026-10-14-windowsmodern-framework-identity-boundary), the portable `windows-native-smoke` ZIP and shared Modern acceptance still build on `cd5875c`. The RF-014 deficit therefore still affects those and the rollback, not the Baldosa journeys.
- **Open residual, one mechanism (RF-016):** the one-field-early `0x84` onset on 2P seed 50048000 comes from the result-screen song upload (`Snd_UploadBlockList`). The original finishes it at 5013 V=230 and reaches `80:FAC9` at V=232, seven lines into VBlank; the faster SPC handshake gets Baldosa there first. A disposable 17,060-cycle SPC build gives onset 5015 = 5015 (one transient 7-byte frame) but over-corrects two attract loads, so the remaining question is the unattributed IPL-handshake share, not a constant to tune. Switcher's +4664 onset is likely the same upload; testing that needs the bsnes SRAM accessor below.
- **Second original reference for the 1P producer.** Running the Switcher/Zoo producer with the patched bsnes core fails closed (`SNESREF_SRAM_IN: core exposes no SAVE_RAM`): the 2014 movie needs injected SRAM and the bsnes accessor patch exposes only work RAM. Extending it to cartridge SRAM is the cheap prerequisite for asking whether the Switcher +4664 onset is the same Snes9x/bsnes onset knife-edge seen on 2P seeds 50036056 and 50024004.
