# QA-01: original 2014 Bowl SRAM-correlated WRAM crosswalk (18 October 2026)

**Decision: bounded, authentic, noncausal investigation only. USA events accepted: 0/45.** No byte is waived or masked and no original/native input, memory, CPU/APU or emulator timing was altered. This note builds on the independently executed and merged [original movie vs fresh guest experiment](QA01-BOWL-2014-MOVIE-THREE-GUEST-MEMORY-20261018.md); it is not another source replay.

## Exact independently inspected original files

I directly downloaded [original 2014 movie / fresh original / native run 39169304323](https://github.com/gamesbyian/UR-Recomp/actions/runs/39169304323), artifact [12151982503](https://github.com/gamesbyian/UR-Recomp/actions/runs/39169304323/artifacts/12151982503). The full original 78-member archive SHA-256 is `c2262b40e43b4e167cbdf291623b0e34207561187e103af39eca7a46fa4b0edc`, independently recomputed and matched against GitHub's report. Original source is `d8fc9099ea2827c6a919ec01bd2c49472701803c`. Original producer `bowl-report.json` SHA-256 is `e965cada128c4beb89aae8244bc11e9f3b68068158d1ee9baaab265b43cc2b15`.

All eight archived movie source frames (+334/+339/+340/+341/+342/+343/+344/+354), eight fresh-original guest frames and eight native guest frames each retain their real full 131072-byte WRAM and 8192-byte SRAM. I independently rehashed all **48** source/fresh/native WRAM and SRAM member bytes and recomputed all movie-to-original, movie-to-native and original-to-native full-memory difference counts from the bytes against the producer report. Captures are independently stamped in their own guest/movie host clocks; comparisons at the same result-relative index are not the same CPU-master-tick or a justified host-input phase shift.

## Newly discriminating byte structure

For each differing WRAM byte at low-bank address `7E:xxxx`, compare the original and guest values at SRAM `0x0E6B + xxxx`, **without deleting that WRAM difference from any denominator**. A match here requires **both original and compared guest values** to be identical to their corresponding SRAM bytes. The candidate displacement `0x0E6B` is a retrospective, measured static crosswalk; it is NOT an independently proven source-level SRAM copy, write instruction, direction of transfer, live hardware mapping or declaration that those bytes are semantically irrelevant.

At the earliest two common sampled points +334 and +339:

| Guest comparison | Full WRAM differences | Exact-value SRAM-offset-correlated WRAM differences | WRAM differences not explained by this value correspondence | Full SRAM differences |
|---|---:|---:|---:|---:|
| Original 2014 movie ↔ fresh Snes9x | 44 | **39** | **5** | 71 |
| Original 2014 movie ↔ Baldosa | 45 | **40** | **5** | 73 |
| Fresh Snes9x ↔ Baldosa | 2 | **2** | **0** | 3 |

All five original movie↔fresh-original **unmatched** WRAM difference addresses at +334/+339 are `7E:0069`, `7E:01F4`, `7E:01F5`, `7E:2049`, `7E:205B`. The same unmatched addresses appear for movie↔native. These are genuine source-history-associated differences between original Snes9x executions, not necessarily a defect in the recompiler. In particular `7E:0069` is already investigated elsewhere as a sound-transfer field. The existence of that common sound-byte residual in two Snes9x histories cannot by itself decide CPU↔SPC causality.

At +340 the original/native guest transition phases begin to separate:

| Offset | Movie↔fresh-original WRAM different | Movie↔native WRAM different | Fresh-original↔native WRAM different | Mapped movie↔fresh-original | Mapped movie↔native |
|---:|---:|---:|---:|---:|---:|
| +334 | 44 | 45 | 2 | 39 | 40 |
| +339 | 44 | 45 | 2 | 39 | 40 |
| +340 | 73 | 45 | 33 | 39 | 40 |
| +341 | 687 | 74 | 666 | 39 | 40 |
| +342 | 266 | 705 | 688 | 38 | 39 |
| +343 | 186 | 709 | 671 | 38 | 39 |
| +344 | 179 | 293 | 289 | 38 | 39 |
| +354 | 126 | 140 | 113 | 38 | 39 |

The static SRAM counts remain 71/73/3 across the archived offsets. The source archived next Switcher onset is Bowl-result +342, fresh original +341, native +344. The 2014 movie has prior completed tours and earned record history, while the two fresh guests were separately entered from the stock menu with historical embedded SRAM and event-relative controls. Their different persistent runtime/history bytes are observed, not a validated causal explanation for every discrepancy.

## Reproduce, never promote

Use `tools/qa01_bowl_movie_sram_crosswalk.py` on the **original** Actions ZIP without running either game:

```sh
python3 tools/qa01_bowl_movie_sram_crosswalk.py \
  --original-zip /path/to/github-actions-artifact-12151982503.zip \
  --expected-zip-sha256 c2262b40e43b4e167cbdf291623b0e34207561187e103af39eca7a46fa4b0edc \
  --out /tmp/bowl-movie-sram-crosswalk.json
```

The tool checks the original ZIP identity, original source event/frame clocks and guest report, all 48 raw images and each claimed image hash/count; it reports all observed unmasked differences, the exact-value SRAM crosswalk subset, and the **remaining addresses** separately. It **always returns 0 release admissions**, even if every offset-correlated byte is present. The ROM-free tests reject bad ZIP hashes, missing movie bytes, forged guest memory, forged comparison counts and falsified source clock registration.

**Next experiment decision:** Before another expensive original/native emulator campaign, compare the **true original movie and fresh original Snes9x writer history** for the five unmatched raw bytes and the `+339→+340` host/stack transition. Separately identify whether the correlated `+0x0E6B` values are ever *read* by gameplay consumers and whether any pre-existing source-history divergence affects event behavior. Do not globally retime, alter acceptance byte masks or claim source/gameplay equivalence from same-value SRAM alone. The CPU/APU agent owns native causal writer investigations, the source-event owner owns alternate-event captures, and independent QA owns eventual 45-event admission.
