# QA-01: independent Bowl→Switcher raw temporal census (18 October 2026)

**Status: authentic source-bound, sampled negative evidence; HOLD, 0/45 USA course admissions.** This work does not change any guest/emulator code, input clocks, source movie, official release ledger or acceptance threshold. The CPU/APU agent owns actual instruction-time writer/reader causality and the independent QA-01/07 event reviewer owns any future adjudication.

## Independently opened original artifact

- Genuine completed [original/native Bowl workflow #39168164480](https://github.com/gamesbyian/UR-Recomp/actions/runs/39168164480), tested PR source `9ee3b8cb876f630d259882dde62da07ba6217c8d`, original Actions job `117795412408`. The source movie and ROM remain original USA 2014, Bowl `course:03`. It executes real Snes9x + pinned Baldosa guests, not a simulation.
- Original [62-member artifact #12151357791](https://github.com/gamesbyian/UR-Recomp/actions/runs/39168164480/artifacts/12151357791), **398,053 bytes**, with 48 guest 128 KiB WRAM/8 KiB SRAM source images, exact producer JSON, cold-guest report/logs, original scan, original/native calibration and execution logs. Independently downloaded ZIP SHA-256 **`2924534f2700714c655647b43e2453c54d4e76f0e258566bcf500439d962ea79`**, identical to the GitHub artifact provider digest.
- Original producer-report SHA-256 **`55fd130ea2e52110ce89d7c3f33c6bfaf9182a4b2d1b82289a10845b0b1ca390`**, recomputed directly from the retained `bowl-report.json`. The producer's exact native executable SHA-256 is `439ac76fa8d90f141436dc25426e522561667cb3aa575d5c326a06afc6cb5ba8`. These are not an equivalence claim for the Windows shipping binary.
- The retained independent `bowl-independent-raw-audit.json` attests to all **12** paired raw memory offsets, **3,041** unmasked 128 KiB differing-byte occurrences and `accepted_event_credit: 0`. A *second independent local read* extracted every actual memory member and checked the 48 source-reported WRAM/SRAM member SHA-256 values and per-sample byte differences against the producer and independent audit. No ROM or game binaries were re-executed.

Reproduce the independent temporal audit using the already merged checker and the original archive, without building an emulator:

```sh
python3 tools/qa01_bowl_temporal_delta_census.py \
  --archive /path/to/github-actions-artifact-12151357791.zip \
  --expected-sha256 2924534f2700714c655647b43e2453c54d4e76f0e258566bcf500439d962ea79 \
  --out /tmp/qa01-bowl-temporal-census.json
```

## Exactly what the paired captures show

All rows are paired at the **same independently observed absolute host frame**. The offset is relative to each guest's *own* observed scored-Bowl result, never a newly shifted controller input. SRAM differences below include **every one of the 8,192 bytes** and WRAM counts compare **every one of 131,072 bytes** without masking.

| Offset after Bowl result | Absolute original/native host | Different WRAM bytes | Different SRAM bytes |
|---:|---:|---:|---:|
| +334 | 4683 | 2 | 3 |
| +338 | 4687 | 2 | 3 |
| +339 | 4688 | 2 | 3 |
| +340 | 4689 | 33 | 3 |
| +341 | 4690 | 666 | 3 |
| +342 | 4691 | 688 | 3 |
| +343 | 4692 | 671 | 3 |
| +344 | 4693 | 289 | 3 |
| +345 | 4694 | 214 | 3 |
| +346 | 4695 | 184 | 3 |
| +349 | 4698 | 177 | 3 |
| +354 | 4703 | 113 | 3 |

**Stable differences before the transition:** +334/+338/+339 WRAM is identical within each guest and has precisely two cross-guest differences, `7E:00C6` original 1/native 0 and `7E:00C8` original 5/native 4. There is no earlier paired full-WRAM observation in this archived series, so these are the *first observed sampled* residuals, not proof of the chronological first writer.

**SRAM static difference:** all 12 SRAM pairs differ at precisely the same three offsets and values, each unchanged within each guest across the sampled interval:

| SRAM offset | Snes9x original | Baldosa native |
|---|---:|---:|
| `0x0EF6` | 1 | 0 |
| `0x0F31` | 1 | 0 |
| `0x0F33` | 5 | 4 |

For every one of the 12 pairs, the two WRAM words/bytes `7E:00C6` and `7E:00C8` take the same respective guest values as SRAM `0x0EF6` (also `0x0F31`) and `0x0F33`. **This is a repeatedly observed value correlation only.** Neither a memory copy operation, a source-name mapping, the first write PC nor even a historical original/native *source* cause is established by snapshot equality.

**Transition boundary:** at +340 the first *observed expansion* adds 31 differences including `7E:01EC..01F5` stack/return-area bytes; at +341, when the fresh original guest enters Switcher and native is still in a different transition phase, the full-WRAM residual jumps to 666. The archived source enters Switcher at Bowl-result **+342**; fresh original at **+341**; native at **+344**. Both later reach actual canonical Switcher, but agreeing named fields at +344 does not erase unmatched original/native WRAM, the 3 static SRAM bytes or CPU/APU timing.

**Cold ranked records:** the same genuine ZIP contains a fresh original guest and a fresh native guest reloading the source-earned Bowl score **764**, the original 150 ranked words/holders and matching checksums at cold guest +300 and +420. The two complete SRAM image digests still differ. This does not prove shipping Windows disk publication, hard restart or power failure.

## Decisive next source work and stopping boundary

The smallest actionable CPU/APU/source archaeology target is the write/read chronology and ownership of `7E:00C6`, `7E:00C8`, `SRAM:0x0EF6`, `0x0F31` and `0x0F33` **before Bowl result +334**. Record separately the first original and native writer PC, source byte provenance and guest-frame/host timing without defaulting to a mirror assumption. Then investigate +339→+340 stack/NMI/transition scheduling and +340→+341 original Switcher onset on each guest's unmodified clock. Existing RF045/047/055 teams own shared CPU/SPC causes; this document is a QA evidence handoff and makes no speculative guest fix.

Unlike an accepted event, this original snapshot series **cannot prove any unsampled frame**, entire pre-Bowl play, full CPU/SPC execution, source-original controller consumption, or exact shipping Windows binary. It is never an additional 45-event certification or reason to waive a byte. No new workflows, recurring factories or emulator runs were started by this analysis.
