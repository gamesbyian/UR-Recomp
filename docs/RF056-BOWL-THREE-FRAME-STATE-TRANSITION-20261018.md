# RF056: independent USA Bowl transition-onset displacement, exact WRAM mutation identity

**October 18, 2026. Original/native CPU/gameplay-source research, not event admission. Complete USA events 0/45, release gates 0/12.** No ROM/input modification, guest code fix, CPU/APU cycle retime, input rephase, mask, graphics/Modern changes or QA ledger edit.

## Authenticated original evidence

Reuse the already genuinely executed [2014-USA Bowl three-guest case, Actions 39169304323](https://github.com/gamesbyian/UR-Recomp/actions/runs/39169304323). Exact source commit `d8fc9099ea2827c6a919ec01bd2c49472701803c`; immutable [78-file artifact 12151982503](https://github.com/gamesbyian/UR-Recomp/actions/runs/39169304323/artifacts/12151982503) was independently downloaded and SHA256-rehashed to `c2262b40e43b4e167cbdf291623b0e34207561187e103af39eca7a46fa4b0edc`. The retained actual 128KiB guest WRAM and 8KiB guest SRAM files include original Snes9x 2014 source-movie captures, separately replayed fresh Snes9x, and native Baldosa. ROM `859ec99f…`, movie `06dce29e…`, seed SRAM `a6af0ddf…` are separately verified from `bowl-report.json` and metadata. The source-movie-vs-fresh original is already **44 WRAM/71 SRAM bytes different at result +334**; never collapse those into a shared source state.

An archive-only [fail-closed full-image analysis script](../tools/qa01_rf056_bowl_temporal_byte_transition_audit.py) reads **all 24 untouched fresh guest full-WRAM captures, all 24 untouched full-SRAM captures, and eight historical original-movie WRAM/SRAM pairs**, with no excluded bytes. Reproduce:

```bash
python3 tools/qa01_rf056_bowl_temporal_byte_transition_audit.py \
  bowl-3guest-original-native-2014-source.zip --out rf056-temporal-audit.json
```

The input is the unchanged ZIP, not a new emulator run, generated/controller-shifted file or state reconstruction. It verifies provider artifact SHA, member count, source ROM/movie/SRAM identities, strict independent diagnostic status and raw full image sizes before calculating any result. [Rehashed evidence receipt](../analysis/data/rf056-bowl-independent-threeframe-full-wram-triples-20261018.json) fixes exact clock labels, source hashes, measured bytes and unresolved claims. [Unit negative fixtures](../tests/unit/test_qa01_rf056_bowl_temporal_byte_transition_audit.py) refuse incomplete snapshots, changed event artifacts and differences in actual byte-before/after values.

## New fully raw result: identical native state-construction *three sample frames later*

The *actual* fresh original and native pretransition WRAM is unchanged from result offsets +334 through +339 (original) and through +342 (native). Across these pretransition captures the only two original/native different bytes are the *persistent* `7E:00C6` original01/native00 and `7E:00C8` original05/native04. Their imported labels identify possible menu animation/timer roles but are **not actual executed writer/consumer provenance**.

Compare existing, separately observed guest images across offsets without changing the guests:

| Fresh original result offset | Native result offset | Different full 128KiB WRAM bytes |
| --- | --- | ---: |
| +340 | +343 | **2**, `00C6/00C8` only |
| +341 | +344 | **2**, `00C6/00C8` only |
| +342 | +345 | **6**, `00C6/00C8` plus four NMI stack bytes `01ED–01F0` |
| +343 | +346 | **2**, `00C6/00C8` only |

By comparison, the strict *same-result-offset* original/native whole WRAM differences remain +340 **33 bytes**, +341 **666**, +342 **688**, +343 **671**, +344 **289**. These are not observations to mask or waive. At +341 the fresh original Switcher is active, while native becomes active at +344. The original 2014 historical movie becomes active at its own +342. The result-relative labels are independent observed execution clocks; no original/native input alignment is inferred merely from the numbers.

Even more discriminating, comparing **every actual written-byte transition tuple (128KiB absolute address, byte before, byte after)** from genuine full snapshots, not just post-state equality:

- Original **+339→+340 writes 31 distinct WRAM byte transitions**. Native **+342→+343 writes the exact same 31 triples**, address-by-address and both old/new values, with **zero exceptions**.
- Original **+340→+341 writes 642 WRAM byte transitions**. Native **+343→+344 writes the exact same 642 triples**, again without a single exception.
- Following original **+341→+342** has 220 changes, native **+344→+345** has 219, with **216 identical triples**. The remaining limited differences belong to `01ED–01F0` stack phase; do not extrapolate full ongoing frame equivalence.
- The three *actual earned SRAM differences* persist independently at `0EF6` (01/00), `0F31` (01/00) and `0F33` (05/04). No sampled transition writes those SRAM bytes; do not imply ranked-record equality from the WRAM overlap.

This is unusually specific evidence: **the first 673 exact destination/before/after WRAM mutations reproduce identically but start three sampled guest frames later on native**. They include the result setup, NMI/stack/track/sound-queue bytes that previously appeared as an apparently broad 33/666-byte strict mismatch. The initial inability to align on the *same* result-relative frame remains a real strict failure. Exact shifted state is a causal clue, **not** parity certification and not an instruction-clock alignment proof.

## Exact retained host/controller observation boundary

The existing preserved **fresh Snes9x replay log** records `[input] frame=4687 mask=080`, `frame=4688 mask=040`, and `frame=4689 mask=080`; the next visible source input-change record is `frame=4696 mask=280`. In the **unchanged** 78-member archived source/fresh/native case, the fresh original's 31-byte transition occurs between actual snapshots **host4688→4689**; the native's *identical 31-byte triple set* occurs **host4691→4692**, while native+340/+341/+342 already observed its pretransition WRAM state. The exact 642-byte transition sets similarly occur original **host4689→4690** and native **host4692→4693**. These are true file clocks, **not a rephase**. The old archive's native log does not independently print consumed P1 controller masks, and no guest 65816 PC/branch read was sampled, so the original `[input]` records must not be mislabelled as an independently proven native controller-consumer event. Merged Bowl [#1856](https://github.com/gamesbyian/UR-Recomp/pull/1856) now retains actual source-bound replay controller files in a newer run; its independent input verification is a prerequisite to deciding whether this difference is an input-consumer, menu conditional or CPU master/beam scheduling effect.

## Concrete next original/native CPU intervention boundary

Investigate the **earliest actually executed branch/predicate and input/state read** preceding the original guest's first 31-byte mutation set at +339→+340, versus the native guest's identical set at +342→+343. Reuse the existing exact source movie, authentic fresh original/native controller input identity now retained by merged [#1856](https://github.com/gamesbyian/UR-Recomp/pull/1856), and the existing guest result recording. Require true executed 65816 PC, input sample, V/H or independent CPU master clock and writes that cause the first `7E:0057` NMI and race-transition state; identify whether `00C6/00C8` is actually *read* by a transition consumer before asserting causality.

Prefer a single adjacent-frame, read-only execution trace/conditional, with complete genuine source input fingerprints and the existing 131,072-byte raw equality controls. **Do not** immediately shift the game clock, controller movie, SPC queue or gate event acceptance because the two byte-transition sets match at shifted positions. The 2014 movie already differs from fresh original, and a genuine first reader/clock origin still has not been established. Inform QA/Bowl agents, but leave their event fixture, input pipeline and ledger unchanged.

## Three-project reuse preflight and ownership

The repository's strict original/native Zoo/Bowl comparator, existing independently proven original controller/source evidence and immutable source images are authoritative for this USA course. Pinned Baldosa supplies the native generated-CPU and helper interfaces; Malmazuke's reconstruction can suggest instruction and RAM labels only after a direct source-ROM check, never PAL→USA timing or acceptance. This PR owns only **offline, source-identity-bound CPU/gameplay event causality research**, and edits no shared workflow or acceptance authority.
