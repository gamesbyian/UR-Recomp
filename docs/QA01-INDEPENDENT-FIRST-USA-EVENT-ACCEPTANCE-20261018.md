# QA-01/07: independent first-USA-event acceptance boundary (18 October 2026)

**Decision: HOLD, 0/45.** This is the independent acceptance review of genuine Zoo/Bowl evidence available on main at `e9a5cdca136ecc35fe25c74191cc995aada4f885`. It does not supersede [the 45-event census](ORIGINAL-COURSE-EVENT-CENSUS.md), [the release ledger](RELEASE-QUALITY-LEDGER.json) or the CPU/APU source owner's RF record. A research `strict_candidate` is valid *as a candidate* but is not independently accepted as a full USA event. No byte mask, assumed emulator clock shift, rephased controller input or new shipping CPU fix is approved here.

## Audited best available event: USA Zoom Zoo Circuit

The strongest single executed control is [RF054 real original/native USA 2014 Zoo run 39161563837](https://github.com/gamesbyian/UR-Recomp/actions/runs/39161563837), source `7334a568f52ea390ae5866d3ee132e392635a186`, [18-file case artifact 12149640496](https://github.com/gamesbyian/UR-Recomp/actions/runs/39161563837/artifacts/12149640496), reported archive SHA-256 `3ccb209a92045e9e89113442e68af51b85a453a160a9b9efaf8ca0d59e79631c`. [RF054's permanent machine receipt](../analysis/data/rf054-executed-native-11c774-port-receiver-witness-20261018.json) records the positive facts and their separate clock domains. This QA review **has not independently re-downloaded and recomputed the case ZIP**; artifact digest and paired-control assertions currently inherit that executed report's provenance. Those precise limitations matter for final acceptance.

Existing receipt-backed positives, with their *bounded* scopes:

- **Unchanged source:** same original USA ROM, 2014 movie, input and source SRAM identity across RF047/RF052/RF054 control producers. Independent fresh Snes9x and native Zoo result at race-relative **+5163**. Original movie and both guests observe next Crawler Bowl active **+267** after that result.
- **Real course/save outcomes:** 11/11 sampled 8192-byte original/native SRAM images match across the next-Bowl bracket; source-earned MIKE Zoo best lap **2510 centiseconds** survives the separately reported fresh *guest* original/native cold reload. That staging does not prove that the shipping Windows executable wrote and recovered the actual disk file.
- **Unmasked WRAM:** all 131,072 bytes were compared at each of **78** original/native checkpoints, with **51 exact pairs, 27 nonexact pairs and 92 differing-byte occurrences**. Earlier [address census](QA01-ZOO-STACK-RESIDUAL-CENSUS-20261017.md) localizes **90** occurrences to stack-page `7E:01ED..01F1` and **two** to sound pointer `7E:0063`. This is *not* an all-frame census; none of these residuals is waived.
- **NMI:** [RF047 source wait-loop crosswalk](RF047-ZOO-WAIT-LOOP-SOURCE-CONVERGENCE-20261018.md) identifies the extra taken original `82:D4F0 BPL` in four bounded interrupt windows and native compiled RTI's different PC/PB consumption contract. The CPU agent established a plausible convergent path after the original `BIT $57`, but did not independently prove the full post-wait consumer state/clock trajectory, nor authorize sampling normalization.
- **Sound:** [RF053](RF053-EXACT-SOURCE-NATIVE-SPC-RECEIVER-PARITY-20261018.md) finds a **unique 322/322 executed SPC PC+port+value ordered read alignment**, with only a **22- or 23-native-local-tick difference** between independently registered read sequences. [RF054](RF054-NATIVE-65816-SOUND-WRITER-20261018.md) further proves a real native `cpu_read8` at **11:C774**, then the same-scope native port3 D0/port2 63 writes, queue application and matching SPC reads. Original source also genuinely reads **11:C774** and publishes D0/63. The native source-instruction PC, CPU/master ↔ SPC clock registration, all intervening effects and final audible parity are not demonstrated. Matching receiver payload cannot license a global retime.

The research compiler/ELF, its source checkouts and the previously nominated Windows portable ZIP are **distinct build identities**. Main includes the RF017 Windows regeneration [#1744](https://github.com/gamesbyian/UR-Recomp/pull/1744); that does not transplant RF054 research-native execution proofs into an exact released Windows PE or prove the full guest route.

## Exactly why the first event remains unaccepted

| Requirement | Current best receipt | Acceptance verdict |
| --- | --- | --- |
| Authentic source course identity, input, entry, real result and next Bowl | Executed Zoo 2014 and RF054, bounded +5163/+267 | **Positive, bounded**; hashes/guest entry were recorded |
| Equal source-earned ranked result and 8KiB battery snapshots | 11/11 handoff pairs, cold *guest* ranked record | **Positive, bounded**; no Windows disk recovery claim |
| Unwaived full-course original/native semantics/consumer timing | 51/78 full-WRAM exact; +1 stack, +5040/+5045 pointer and differing NMI return/sound schedules | **Open**; actual differences or an independently justified phase-specific observation contract need resolution |
| Source/original/native entire course including unsampled frames | Sparse 78 samples, bounded early/late opcode windows | **Missing continuous qualification**; cannot infer every guest frame from sampled equality |
| Exact shipping Modern/Windows candidate route | RF054 research ELF, earlier #1744 shipping regeneration and separately hashed nominated older ZIP | **Missing common binary/source/consumed-input identity** |
| Actual shipping Windows save after quit/kill and fresh OS process | Research guests preloaded from authentic captured SRAM; Windows #1713 still separate | **Missing shipping disk-persistence witness** |
| Independent final adjudication against 45-event census | Existing manual classifier returns `strict_candidate`, credit 0 | **HOLD**; no unilateral ledger/census promotion |

**Acceptance-side stopping condition:** Do not spend another runner on the same +5163/+267/11-SRAM/322-receiver positive observations. The first worthwhile new run is one whose *new observable* closes a specific row in this table and preserves the already demonstrated controls. The CPU/APU agent owns live writer/reader, NMI/RTI and original/native clock causality, while independent QA owns verdict, source artifacts, release/product binding and eventual census entry. No QA implementation may alter guest timing to make this report green.

The cheapest next discriminators, in order: (1) CPU/APU owner reports exact original/native first consumed post-wait state and the actual compiled-segment instruction PC of the native sound read, or a controlled causal witness demonstrating these cannot affect game logic; (2) independent QA reviews the *same* case's genuine unmasked source and guest replay, frame/semantic coverage and any narrowly source-justified observation contract, without promoting differences by assumption; (3) when a real full-event comparison qualifies, bind an independently tested Windows PE/portable ZIP, player-driven input and real autosaved/cold-reloaded record to that very shipping source. Bowl scored Stunt and Switcher have weaker, separately qualified witnesses. Do not survey 45 events or reclassify them from Zoo.

## Existing-tool improvement

`tools/qa01_event_acceptance_readiness.py` reads the current **classified** `qa01_event_campaign.py` per-case `case-result.json`, without emulating a game or replacing the strict classifier:

```bash
python3 tools/qa01_event_acceptance_readiness.py path/to/qa01-campaign-case-zoom-zoo/case-result.json --output /tmp/qa01-readiness.json
```

It exposes positive bounded subclaims separately from negative observations and unproved course/product obligations, rejects invalid hash shape, fabricated promotion flags and contradictory strict/phase/handoff/WRAM metadata, and **always returns HOLD with accepted-event credit zero**. `producer_error` is never called a game divergence. It cannot recompute producer bytes from the classified report or attest to an archive it has not independently opened; the existing producer/aggregator retain that responsibility. The synthetic regression tests assert that even an imagined all-sampled-WRAM-exact handoff does not award any event. No automatic GHA workflow, emulator variant, census rewrite or competing ledger is introduced.

**Three-project reuse preflight:** `release-qa --include-conditional` found the existing candidate evidence envelope, route-input identity and first-divergence chain as P0 `now` reuses, with Malmazuke replay-manifest and Baldosa route/firstdiff as conditional methods. This change uses the existing UR classified case receipt and adds only an independent post-classification summary. It imports neither upstream code nor a second comparator.
