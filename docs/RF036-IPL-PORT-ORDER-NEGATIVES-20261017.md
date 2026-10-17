# RF-036: reject IPL-special-case CPU/SPC port publication

**2026-10-17. Reproduced actual source-guest experiments. Rejected implementation. No USA full-event credit (0/45).**

RF-034 established a genuine first IPL CC publication discrepancy: original Snes9x completes the live SPC `CMP #$CC,$F4` before CPU `$2140=$CC` becomes visible; source-pinned Baldosa's queue publishes before the live comparator's read. This warrants a *testable* hypothesis, not an assumption that all CPU/SPC handshake timing can be fixed by moving a queued port publication.

## Authentic A/B, exact source and log intervention

Both experiments run the unchanged original USA ROM, archived 2014 SMV and unchanged exact controller script with separately sourced Snes9x and Baldosa research guests. Both use the RF-015..028 research composite (not the production Windows bridge), true Zoo result **+5163**, authentic next Bowl entry **+267**, real full 8192-byte earned SRAM and original/native guest cold ranked-record restart. Both finished plan/build/case/aggregate green; a green research run classifies a bounded *candidate*, never grants full-event fidelity.

| Discriminator | RF-034 untouched source control | A: last bus cycle only | B: in-flight CMP completion |
| --- | ---: | ---: | ---: |
| Source / run | [38981131474](https://github.com/gamesbyian/UR-Recomp/actions/runs/38981131474) | [38998740919](https://github.com/gamesbyian/UR-Recomp/actions/runs/38998740919) | [38999611814](https://github.com/gamesbyian/UR-Recomp/actions/runs/38999611814) |
| True native post-CMP CC publications observed in replay | Not intervened | **2** | **6** |
| Whole 128-KiB WRAM exact sample pairs | **51/78** | **46/78** | **0/78** |
| First unmasked WRAM disagreement | Zoo +1, low stack | Zoo +1, `7E:01ED` | Zoo **+0**, `7E:01D6` |
| Zoo +5040 pointer `$63`, original/native (hex) | `73/74` | `73/75` | `73/74` |
| Zoo +5040 counter `$69`, original/native (hex) | `BE/BE` | `BE/BF` | `BE/BE` |
| Zoo +5045 pointer `$63`, original/native (hex) | `B3/B4` | `B3/B5` | `B3/B4` |
| Zoo +5045 counter `$69`, original/native (hex) | `FE/FE` | `FE/FF` | `FE/FF` |
| Bowl result +266, +267, +280 unmasked WRAM differing bytes | Previously 4/0/4 | **4/0/4** | **5/1/5** |
| Zoo terminal, Bowl start, 11 earned SRAM pairs, cold guest ranked record | Positive bounded evidence | Positive bounded evidence | Positive bounded evidence |
| Full USA event admitted | **No** | **No** | **No** |

Both interventions are **real**, not just fixture-compiled. A's guest replay log contains two complete `QA01RF035 pre/post` comparator-order interventions at actual native SPC ages 15928720 and 108520844. B has six `post` publications and eleven `pre` trace rows, including two-tick wait-through cases; no cycle count, guest input or queue target was artificially advanced. Historical trace prefixes `RF035` were emitted before merged [#1746](https://github.com/gamesbyian/UR-Recomp/pull/1746) reserved RF-035 for the *sound consumer-liveness observer*. The separate IPL hypothesis is indexed **RF-036** here, but do not rewrite immutable source-run identifiers.

Original/native post-result positive SRAM agreement and fresh-process guest record reloading do not waive **any** unmasked gameplay/stack/sound differences. A adds transfer counter errors and loses five exact checkpoints; B loses all exact checkpoints and pollutes the first race frame and Bowl entry. Both are conclusively worse than the untouched research baseline; they are **falsified as shipping corrections**. The speculative draft [#1747](https://github.com/gamesbyian/UR-Recomp/pull/1747) was closed *unmerged*; all temporary one-shot push triggers have been removed, and the shared QA workflow was restored byte-for-byte. No patch landed in Windows source, Modern, graphics or the independent release ledger.

## Next justified RF-037 causal experiment, not another global phase tweak

The live RF-035 sound observer, source run [38999341435](https://github.com/gamesbyian/UR-Recomp/actions/runs/38999341435) and ongoing source-only [#1749](https://github.com/gamesbyian/UR-Recomp/pull/1749), directly witnesses real original `82:82F0/82F2/82F6/8301` upload instructions and native `Snd_IncDataPtr_M1X0` / `Snd_UploadBlock_80D1_M1X0` readers. Its 51/78 sampled full-WRAM equality and +5040/+5045 one-byte pointer residual are unchanged. However its first 1,024 original opcode records are all exhausted inside one core frame, and native 4,096 helper records truncate by host 6058, preventing a full +5045 bus-transaction conclusion.

The smallest decision-changing next probe is source-clock-qualified, **per-frame/per-instruction** counter-limited observation of the real `$63/$64/$65/$69` native CPU read, the corresponding original CPU sound pointer read, downstream CPU `$2142/$2143` writer, SPC input-port consumer and echo *at the exact divergent +5040 and +5045 host windows*. Bind original/native host-clock axes independently; capture last true writer and consumed byte before changing scheduling. Reuse existing producer and original 2014 controller script, and keep the 78 WRAM / 13 DP / 11 SRAM, full result/Bowl/cold checks and negative 2P/attract controls. Do not rerun IPL literal special cases or reinterpret CPU echo liveness as sound-transfer causality.

[Canonical machine receipt](../analysis/data/rf036-executed-ipl-boundary-negative-20261017.json) retains exact run heads, guest hashes and artifact ZIP SHA256. All proof is from **research Linux guests**; authentic **shipping Windows source** USA event, all-frame logic parity and OS disk-hardkill durability remain unproven. **0/45**.
