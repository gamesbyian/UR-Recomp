# RF081 independent raw-memory census and cross-epoch boundary (H19)

**Status: HOLD. Zero independently accepted complete USA events.** No release ledger or shared-queue edit.

## Authenticated source and method

RF081 original/native source-case ZIP SHA256:
`df35ddcd8e87bd6664e4e01fe6cbc91fabef6b45292d92564bdab92214bcff37`.

The independent ROM-free `tools/qa01_rf081_raw_memory_pairs.py` checks the exact archive's SHA256, ZIP CRC, duplicate names and paired `work/zoom-zoo/replay/ref` versus `native` members, validating 131072-byte WRAM and 8192-byte SRAM image sizes. It compares all bytes without normalization, masks or a guessed source-clock shift. Its detailed image-hash and offset census is preserved in the [Agent 2 H19 recovery bundle](https://drive.google.com/file/d/1qG2rpRjzz-Y4w1H5FJwA70CspdUywuAI/view) alongside `rf081-raw-pair-report.json`.

**RF081 observed:** 44 paired WRAM images; 27 byte-exact, 17 different, **82 differing-byte occurrences**. Every observed difference lies within `01DB..01F3`; `01F3` differs in one pair. No `0063` difference in **this** archive. All 44 sampled SRAM pairs are byte-exact.

**Keep populations separate:** the prior RF054 review had 78 pairs, 51 exact and 92 differing occurrences (including two `0063` sound-pointer differences). Do not mix the RF054 78-pair denominator with RF081's 44 pairs, or infer the sound path has been repaired. These are different execution epochs and artifact populations.

## RTS / event boundary

The H18 width-aware read analysis correctly found generic width-two reads beginning at `01F1` that touch `01F2`. This is not evidence that the native CPU executed a source-tagged RTS operand fetch. Likewise the sampled WRAM `01F3` difference is not a dynamically observed RTS read. The original/native return target, first causally consumed mismatch, separate clock alignment and complete USA event acceptance remain unproved.

Next smallest producer experiment: freeze one identical original/native Zoo source/build/input pair; capture actual original RTS fetched PC and stack operand bus accesses, native executed PC or compiled continuation plus source-tagged reads, pre/post stack pointer, first downstream read/write and distinct clocks. Reopen all evidence independently. Do not substitute another broad 45-course sweep.

## Independent boundaries

- The raw-byte census is research evidence, **not** continuous semantic gameplay equivalence or physical Windows storage acceptance.
- QA06 4K/342-wide geometry checks are analytical; no physical 4K or character-likeness approval follows.
- H19 video byte-witness and SQLite/Ed25519 checkpoint pilots are research, not shipping encoder, live multiplayer, independent anti-rollback anchor or release gating.
- UR owns the original/native source evidence and event census; Baldosa's trace instrumentation is a possible exact-source adapter, malmazuke's labels a provenance crosswalk. The full three-project CLI was not executed in H19.

**Release-gate credit: 0.** Full original source and reproduced evidence remain in Drive, linked above.
