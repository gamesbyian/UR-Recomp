# QA-01: exact frontier dual-air input and latest cumulative original/native triage (2026-10-13)

**Status:** the exact legal original/native input has now **executed in both real guests** (run 38502953689), but the first paired classifier failed on a **source transcript grammar bug before examining raw paired WRAM**. No valid paired dual-air verdict exists; source-field labels remain hypotheses. This evidence is distinct from complete-event qualification and does not alter the strict comparator, the canonical original source, the ROM, the release ledger or **0/45 accepted USA events**.

## The executed frontier discovery

The append-only cumulative research ledger (branch `research/qa-cumulative-ledger`) confirms [frontier run 38446393623](https://github.com/gamesbyian/UR-Recomp/actions/runs/38446393623), source commit `dd5632f0a612ee22cc46d9b1ce7a6005a5fa555f`, 100 legal real-native input experiments. A **single** `both-air-raw` case was observed: **seed 50036056**, **rotation arm**, **shard 2**, first sampled at **absolute host frame 2580**. This is an evaluation of nonzero source-register candidates `7E:0545` (P1) and `7E:0547` (P2), from the native 15-frame (120-frame-spaced) WRAM observer. No original Snes9x execution for this input was part of the frontier producer.

Relevant retained identities:

| Item | Identity |
| --- | --- |
| Exact original-USA ROM SHA-256 | `859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478` |
| Frontier native executable SHA-256 | `28501fa3268f82d83672122cddbd2628ce5b2458e625f46d93766f50befbe515` |
| Original neutral 2P input fixture SHA-256 | `28f2842fd262030e434b3aef88eb360f74de94fbf558f0eb0ba8edce645fb490` |
| Original 2P observation-script SHA-256 | `ebac1a3505281e9793c8197006081c5d88f6ab3383df48f23ba2475159e9e6e3` |

The actual generator is pinned source in `tools/qa_adaptive_frontier.py::actions_for(50036056, "rotation")`, which consumes the established `tools/qa02_native_2p_seeded_endurance.py` input planner, preserves the already source-validated 2P navigation prefix, and injects both P1/P2 legal controls after first-race entry. A random new controller movie or hand-edited button state would not reproduce the cited observation.

## Cheapest valid original/native discriminator

New **opt-in** manual workflow input `qa01_dual_air_50036056` on the existing `.github/workflows/two-player-reference.yml` reuses its original Snes9x and ordinary 2P build for the existing regression, but downloads the **exact immutable Modern frontier native binary** from workflow run 38446393623 for the separate seed-specific comparison. Its executable SHA-256 is checked before launch; a rebuilt unrelated native target is not substituted. The normal workflow is unchanged when the boolean is false.

1. `python3 tools/qa01_dual_air_paired.py prepare --out-dir PATH` regenerates the original-source exact seed/arm neutral `case.input` and the existing 15-checkpoint `case.script`, validates the source fixture hashes and refuses overwritten results.
2. Original Snes9x and native execute the same frozen input, ROM and absolute-host dump schedule in separate guests. Each independently dumps a complete 128-KiB WRAM image at the source pre-intervention `1620`, each original `1740..3420` sample, and **two additional adjacent host frames 2579 and 2581** around the first frontier dual-air sighting. Those two `dump` commands do not add or retime input or change the host-frame index of frame 2580. The original frontier producer's `qa02_native_2p_seeded_endurance.execute` supplies a fresh isolated user-data root, authentic execution mode, unpaced config and identical controller-stream/dump transports.
3. The analyzer independently regenerates the exact inputs from the pinned planner, checks run identity, 2P source entry and both actual 128-KiB dump sets, and reports **both** raw air bytes, position, velocity, race progress, hash equality and native executable identity at each frame, including the three-frame **2579/2580/2581** raw-air window. The run fails closed unless the executable is byte-identical to the cited frontier witness.
4. The analyzer now **also requires independently emitted actual `script f=N dump LABEL …` receipts from both real emulators** for all 18 pinned frame labels. The original transcript is retained separately; the exact Modern frontier native execution writes its internally captured host transcript into `native.log` without changing the ordinary endurance producer. A missing, repeated, reordered or off-by-one receipt rejects the run even when a plausible 128-KiB WRAM file exists under the expected name. The report preserves each actual label/frame pair and the separate transcript SHA-256. These host-tick attestations do not equate emulator CPU/NMI instruction phase or constitute event parity.
5. Inspect whether the original *also* shows both provisional raw air bytes nonzero at host 2580, whether original/native guest source states diverge in adjacent sampled frames, and whether frame-alignment needs a fresh independently measured course-entry anchor. Current comparison is **same absolute host label only**, with two nearest-neighbor samples available for diagnosing a possible ±1 host sampling disparity, never a normalized guest-relative gameplay proof.

## First genuine paired original/native attempt, failure and correction (2026-10-14)

Manual [workflow run 38502953689](https://github.com/gamesbyian/UR-Recomp/actions/runs/38502953689) launched the exact pinned frontier executable and original Snes9x from the verified stock USA ROM and exact seed **50036056** input. The ordinary 2P regression and all source 2P non-air stages passed. The dedicated QA-01 step independently ran **both** 3420-frame guests, and their retained actual log files from artifact **11865834830** (ZIP SHA-256 `5c64ee354b3fc0c2e7507a2d97b6d9a8d3f8ab9e499514f5aa2c98d7bd4e9f9b`) prove **all 18 scripted sample frame receipts, including 2579/2580/2581**, exist in both original and native logs. The completed runtime transcripts are independently hashed: original `91c61fb998efac3547a44e057f243614b748f6a81f9c3a12effb2a58279e607e`, native `1c9d0435564e0277eb09ee9dc813b6f55e1cb59ae6ffa6618acd2afd8eb37f0b`.

The actual **original** Snes9x script writes `script f=2580 dump endurance-2580 fb=256x224 RGB565 sram=8192 ppuw=1063`; actual **native** writes `script f=2580 dump endurance-2580 ok`. The classifier introduced in #1428 mistakenly demanded literal `ok` from **both** and thus observed **zero** original valid receipts, failing at `frame_receipts(original_log)` **before** checking paired original/native WRAM air values. The original and native games did **not** fail here, and the failed classifier supplies **no raw-air parity result**. The first-run artifact retains the exact reproducible input, original/native transcript, and ELF dependency log; **it does not retain the 128-KiB dumps**, so no retrospective code fix can honestly recover the missing paired air readout.

The correction now requires each engine's **exact documented host-native receipt grammar**, validates all expected ordered frame labels and ticks, refuses duplicated/mistimed/malformed output, and retains the original-versus-native log SHA-256. A unit test replicates the genuine `fb=… sram=… ppuw=…` source format and rejects synthetic source `ok` or native `partial` as a false receipt. Another fresh paired run on a SHA including the fix is needed for the 2580 raw-register verdict. No input offset, source game, runtime physics, release QA comparator or strict USA 0/45 event acceptance is altered.

Verified dump script ticks address one concrete provenance risk, **but the original and native CPU/guest-relative entry phases remain uncalibrated**. This observation **cannot alone establish that either racer physically becomes airborne**; `air_effective` and `air` are provisional decoded RAM semantics, and a simultaneous nonzero-byte predicate is neither original physics correctness nor visual OAM proof. The original 120-frame survey could have missed entry, jump and landing transitions; the new 2579/2580/2581 burst narrows the observation window around this one lead without claiming continuous coverage. In particular, `7E:0DDB=1` means second-camera enabled in active 2P and is *not* a failed visual split.

**Acceptance boundary:** this diagnostic always emits `release_gate_credit: 0` and `strict_complete_event_accepted: false`. Next decision, if original/native registers differ, is a *small* original and native writer/input-edge trace around the first observed difference, not adjusting comparator thresholds. If both have raw air, trace source authorship/vertical integration and camera conditions before claiming real airborne motion. A full event still requires independently calibrated entry, all required source semantics and accepted terminal/progression behaviour.

## Diagnose the latest incomplete cumulative original-native producer before another campaign

The separate ledger's **most recent original-native coordinator entry**, run [38446280858](https://github.com/gamesbyian/UR-Recomp/actions/runs/38446280858) at source `dd5632...`, is **`incomplete_or_failed`** with the reason `original workflow or aggregate unavailable`, not `strict_divergence`. GitHub's REST API currently returns **404** for the run, its jobs and artifacts; a recent run listing also omits it. Consequently **the actual first failed step cannot be recovered from presently accessible run data**. Do not turn that absence into a claimed emulator fault, guest regression or exact known cause.

The relevant existing orchestrator source is precise:

- `.github/workflows/qa-cumulative-research.yml` routes `original-native` to reusable `.github/workflows/qa01-event-campaign.yml` with `selected: all` and `zoo_terminal_phase: false`.
- The child job must build the original and pinned native once, attempt the three historical source-qualified Zoo/Bowl/Switcher events, retain per-case `case-result.json` and bounded producer logs, and publish `qa01-campaign-aggregate/campaign-result.json`.
- In `tools/qa01_event_campaign.py`, a genuine strict-negative case is **scientifically complete** and exits the case-classifier with code 0; only a `producer_error` makes that case job red. Three negatives with authentic case receipts should yield `transport_complete: true` and `counts.strict_divergence: 3`, not an absent aggregate.
- In `tools/qa_cumulative_ledger.py::outcome`, the text `original workflow or aggregate unavailable` is the **combined fallback** for either a nonsuccess reusable job result **or** absent aggregate. It alone does not tell whether a source producer, build, artifact transfer, reusable workflow or coordinator failed.

**Triage condition:** before any rerun, recover the 404 run's logs/artifacts by a valid exact URL or document their unavailability; then inspect *first failure* in source workflow `plan → build → cases → aggregate`. If artifact unavailable persists, a **single selected source case** via existing manual `qa01-event-campaign.yml` is the cheapest infrastructure discriminator; do not order another cumulative 10k/long experiment to try to fix an unseen producer. The failure's seed reservation remains consumed in the immutable cumulative ledger.

## More direct Switcher fidelity priority

Merge #1370 (generated C newline repair), #1376 (f5782 following-frame saved-A 4004 read candidates), #1383 (Zoo fixed-host boundary evidence) before running new evidence: all three were merged on 2026-10-13. The next **specific and already implemented** original/native Switcher experiment is the manually dispatched `.github/workflows/qa01-switcher-original-2014.yml` with `source_horizon=22000`, `fresh_paired_nmi_probe=true`, `stack_writer_probe=false`. It instruments genuine original NMI saved-A/pull/RTI and native interpreter PLA and WRAM reads, produces source-authenticated separate crosswalks, and does not alter gameplay.

Its required decision is *which actual source guest instruction/restore boundary differs and whether a result/progression-critical consumer observes it*. A native `01DD=4004` word/byte read callback alone is **not** a proved 16-bit PLA, and matching settled MIKE result at host 5783 does not erase the strict original +4704/native +4702 guest-relative mismatch. If the run's first step fails, fix the minimal instrumentation/transport defect and retain reproducible negative evidence before source-runtime edits.

No repeat original/native evidence has been produced by this documentation or by merging these PRs. No long cumulative campaign is recommended until a specific first-failure reason is available.

### Preserve the actual guest states even on a classifier crash

The *first* paired original/native opt-in run [38502953689](https://github.com/gamesbyian/UR-Recomp/actions/runs/38502953689) genuinely executed all eighteen original/native checkpoint dumps but then failed before raw-air comparison on the original Snes9x receipt grammar. Its `always()` QA-01 artifact contained transcripts, input and manifest, **not the generated 128-KiB WRAM files**. That prevented a retrospective adjudication without a full repeat run. The parser itself was corrected and merged in #1464.

The existing opt-in artifact now **also** retains all original `original/*.wram.bin` and native `native-run/dumps/*.wram.bin` snapshots in the **same** 14-day artifact, including failures. The existing independently emitted real guest transcript `original.log`/`native.log`, manifest, input and exact binary SHA gate remain mandatory for accepting a comparison; a correctly named saved image alone does **not** attest its real capture frame or guest identity. This is preservation and forensic reproducibility only, not an additional emitter, extra guest simulation, invented register semantics or permission to attribute airborne physics from a nonzero raw byte. The workflow remains manual opt-in and strict 0/45 original/native release-event credit remains unchanged.


## Successfully executed paired 2P discriminator (2026-10-14)

**The original/native comparison is now executed and classified**, superseding the earlier no-verdict transport failure. [Actual successful workflow 38509912672](https://github.com/gamesbyian/UR-Recomp/actions/runs/38509912672), artifact **11869806880**, retains manifest, source/native actual runtime transcripts and `paired-report.json` with **18 verified 128-KiB WRAM snapshots per guest**, true frame-label receipts and the frozen **seed 50036056 / rotation / frame 2580**. The native executable SHA-256 matches the original frontier `28501fa3268f82d83672122cddbd2628ce5b2458e625f46d93766f50befbe515`, and the stock-USA ROM/input fixture fingerprints match their manifest. **No controller input timing was rebased.**

| Exact shared host label | Original source `7E:0545/0547` | Native `7E:0545/0547` | Original P1 Y / P2 Y | Native P1 Y / P2 Y |
| --- | --- | --- | --- | --- |
| 2579 | `00/01` | `00/01` | `857/860` | `857/860` |
| 2580 | **`00/02`** | **`01/02`** | `857/863` | `858/862` |
| 2581 | `00/00` | `00/00` | `857/864` | `858/864` |

At host 2580, the genuine **native alone** satisfies the provisional simultaneous nonzero P1/P2 raw-air predicate. Original and native are both in a real active 2P race and have equal **horizontal** P1/P2 coordinates (5054, 4505) at that sample, yet their vertical coordinates and the P1 provisional raw-air byte differ. Source P1 Y 857 remains steady across 2579–2581; native P1 Y 857→858→858. Source P2 Y 860→863→864; native P2 Y 860→862→864. Full original/native 128-KiB WRAM is **not byte-identical** at any of those checkpoints. The comparison covers only the named samples, not every intervening source instruction.

This is a **real original/native provisional state divergence**, not a complete-event failure verdict or proof either racer was physically airborne. It might reflect the vertical-update/landing or observational frame phase, a P1 local state transition, or incorrect attribution of those RAM bytes to effective physics. The **next smallest genuine cause-discriminator** is independently source-visible P1 `7E:0545` writer/consumer and vertical-position (P1 Y) trace with P1 input edges across **2578–2582**, plus native source helper writes at the same real host ticks. Retain original/runtime CPU clock axes and check effective jump/landing semantics before changing any physics. Avoid expanding the 120-frame census, retriggering a large factory, adjusting controller inputs, or treating `7E:0DDB=1` as a broken 2P visual split.

**Admission:** `raw_both_air_at_2580={"original":false,"native":true}`, `paired_guest_relative_entry_offset_calibrated=false`, `strict_complete_event_accepted=false`, `release_gate_credit=0`. This is research evidence, **not 1 of 45 USA strict accepted events**.

## Completed actual original/native dual-air comparison (2026-10-14)

**The requested paired experiment has now succeeded**, [Actions run 38509912672](https://github.com/gamesbyian/UR-Recomp/actions/runs/38509912672), [retained original/native paired artifact 11869806880](https://github.com/gamesbyian/UR-Recomp/actions/runs/38509912672/artifacts/11869806880). The full original Snes9x and exact frontier native binary ran the **same pinned legal input seed 50036056**, and the corrected parser verified **all 18 independent original and native zero-frame script receipts**. The artifact ZIP SHA-256 is `7bc085861183e7667620ad66fb0c7a18f8be7a870afe8c2e4752eb6229cd6c2a`, and its independently executed `paired-report.json` SHA-256 is `de521d7597b274031ba8768aa8f67e2d65938178f2e0e43fa93a1cb7d9497a6a`. The retained classifier reports **strict release gate credit = 0**.

| Exact sampled absolute host | Original P1/P2 `7E:0545/0547` | Native P1/P2 | Original P1 Y / vertical velocity | Native P1 Y / vertical velocity |
| --- | --- | --- | --- | --- |
| 2579 | `00/01` | `00/01` | `857 / 0` | `857 / 0` |
| **2580** | **`00/02`** | **`01/02`** | **`857 / 0`** | **`858 / 19`** |
| 2581 | `00/00` | `00/00` | `857 / 0` | `858 / 0` |

Both actual guests remain `7E:0313=1` (active race), have P1/P2 laps remaining 1 and checkpoint 1, and keep the independently logged source course state. At frame 2580, **P2 matches while P1 has a single-byte raw-air disagreement and a related vertical-motion/position difference**. At 2579 neither engine has both raw-air bytes nonzero, at 2580 only native does, and at 2581 neither does. Full same-host WRAM equality is false at all three, as recorded in the executed report. This is **not** a fabricated one-frame shifted comparison, and the 18 checkpoints do not provide continuous intervening memory samples.

Interpret this narrowly. `7E:0545/0547` are **provisional** air-state labels; they do not alone prove authentic world collision/contact, visible 2P OAM split, a source physical airborne event, or the offending instruction. The only fact established here is the exact original/native **raw guest-state and vertical-motion discrepancy at same absolute host frame 2580**, with independently attested original/native scripts and the exact pinned native executable. This does **not** prove source/native guest-relative entry or CPU/NMI phase equivalence; resampling neighboring ticks or globally retiming controller inputs would not repair the demonstrated same-host discrepancy. The original and native source input and ROM remain unchanged; **strict USA accepted events: 0/45**.

`tools/qa01_dual_air_executed_result.py --artifact ORIGINAL-ZIP --out REPORT` independently rechecks archive/report hashes, engine-specific real guest receipt formats, all 18 frames, pinned native identity and the three sampled raw-air/vertical-motion observations. No new emulator run or CI runner is required to reproduce the classification. **Next experiment, if worthwhile:** bound the first divergence with a small original/native **P1 0545 and vertical integration writer/CPU input-edge trace**, or a few additional host WRAM samples around 2580, only after separately qualifying the exact 2P guest entry phase. Avoid treating the ephemeral single-frame nonzero byte as gameplay-event acceptance.


## Original source 2P air/vertical producer search, next instruction experiment

A static pass through the retained Nitrodon annotated SNES bank 81 disassembly locates a high-priority **P1/P2 local-state round trip**, rather than a generic shared "air flag":

- P1 `81:8DAE` loads 16-bit `$0545`, stores it in shared `$0F29`; after P1 movement/pose/collision calls `81:8DD6 JSR $9E2A`, `81:8DD9 JSR $8B95`, `81:8DDC JSR $8FB8`, `81:8E23` loads `$0F29` and **`81:8E26 STA $0545`** writes it back.
- P2 takes the analogous path `81:8F08 LDA $0547`, `81:8F0B STA $0F29`, `81:8F2A JSR $9E2A`, `81:8F2D JSR $8B95`, `81:8F30 JSR $8FB8`, `81:8F77 LDA $0F29`, **`81:8F7A STA $0547`**.
- The same functions save Y coordinate/vertical velocity to the per-player fields: P1 `81:8E3C STY $0415`, `81:8E48 STY $04BB`; P2 `81:8F8E STY $0417`, `81:8F9C STY $04BD`. The CPU's scratch `$0FA1` and `$A7` are **shared sequentially across player updates**.

This is **an archived disassembly hypothesis, not yet confirmed executing USA original/native PCs**. It suggests a sharper discriminator than a blind same-host byte compare: instrument the actual original opcode scopes (with PPU scanline and absolute host receipts) around the source-equivalent `81:8E26`/`81:8F7A`, and compare the **pre- and post-update** original/native `$0F29`, `$0FA1`, `$A7`, `$0545/$0547`, `$0415/$0417` and `$04BB/$04BD` near host **2578..2582**. Confirm the USA ROM instruction identities dynamically before assigning those addresses; capture both players to distinguish differing P1 vs P2 update order from true differing shared movement rule. An immediate native P1 +19 vertical velocity at 2580 and surviving +1 Y offset at 2581 are real witnessed consequences, while the native P2 -1 Y difference at 2580 **resolves** by 2581. None of these alone establishes jump/collision causality, guest entry parity or original event credit. Do not patch gameplay based on historical bank labels.
