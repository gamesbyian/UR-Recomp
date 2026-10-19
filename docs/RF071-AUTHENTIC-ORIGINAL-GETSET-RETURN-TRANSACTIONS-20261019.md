# RF071: authentic original stack getter-to-return transaction joins

**October 19, 2026. Source-authentic original Snes9x evidence only.** This is a strengthened research witness, *not* proof of full original/native gameplay equivalence. The independent USA acceptance ledger remains **0/45**; Windows product QA remains **0/12**.

## Root-cause chain and real experiment

Historical RF064/RF066 original builds genuinely executed 903 original `PullB/PullW` getter returns but recorded **zero actual RF044/RF063 getset read-entry events** (only 903 writes). The original Snes9x libretro Makefile doesn't track `getset.h` in every object's dependencies. The [RF069 #1942](https://github.com/gamesbyian/UR-Recomp/pull/1942) clean rebuild plus RF070 SA-1-only compile isolation, and inspection of the compiled ELF's direct or LTO-outlined RF044/RF063 helper call paths, closed this **producer** flaw without adding a single emulated bus call.

The one-source authentic [RF069 Zoom Zoo experiment](https://github.com/gamesbyian/UR-Recomp/actions/runs/39307624432), ZIP artifact `12215281695` (SHA256 `90b03d7e035c7a1939b488211b98165615e3fc63226fe57ac718fc7e3e772763`), is complete. I independently reopened all 412 archive members and the raw original log (913,012 bytes, SHA256 `04989c5b60a92b9d393a66ad8e5a84e522f72d8f92bde2af83de5df2cd94bcb9`). The real original side now has **903 physically executed getset read entries**, **903 getset writes**, **903 separately observed actual PullB/W returned values**, and **one actual post-NMI-push five-byte checkpoint** on **2,710 contiguous source-local events**. Independently present RF044 getset rows number 1,806, RF045 actual stack macros 1,806, RF064 actual post-call values 903, RF066 source-ordered true returns 903.

The RF064 reporter qualified **903/903** *unique real getter intervals*; the RF066 reporter confirmed all 903 real returned values in matching source order and detected all 903 genuinely intervening source read events. For each, the sole RF063 read entry occurred strictly after the macro's captured `before` source ordinal and before its separately source-ordered `post_real_stack_getter_return` event; the physical bank/address and width, original host-frame, sampled 2014 memory byte/word, actual RF045 post-macro returned value and RF064/RF066 actual returned value match. This is actual **source-original bus getter-entry to getter-return attribution**, not just the same value appearing in nearby logs.

The 2014 main-CPU local V/H clock is *not guaranteed to be numerically identical* on both sides of a getter. **12/903** observed calls cross a video scanline and the H-cycle counter wraps; the verifier therefore checks lexicographic source-local `(V,H)` ordering inside a host frame rather than mistaking a negative raw H difference for time travel. The source getset entry PB:PC snapshot agrees with the post-call PB:PC snapshot only **183/903 times** and differs **720/903 times**. Those PC strings are actual live CPU state observations at different stages, **not independently decoded opcode-fetch PCs** and must not be used as such. No source/native absolute clock rebase is claimed.

## Independent true-witness consumer, not automatic QA admission

`tools/qa01_rf071_original_real_read_join.py` is designed to reopen **only this SHA256-pinned exact historical archive**. It requires the correct 2014 source, original and native binary SHA, original movie/ROM/input, 78 × 128KiB unmasked WRAM mesh, +5163 source Zoo result, +267 fresh source/native Bowl entry, same raw 92 differing-byte occurrences and independent QA **HOLD**. It reruns RF063, RF064, RF066 checks over the actual original log, verifies the **complete one-to-one RF044/RF063** getter/setter record streams including each real-PC context and physical byte/word, then validates every actual getset read against its enclosing true RF064/RF066 returned-value interval. It emits **all 903** observed transaction receipts, preserving source getset PC context and post-return PC context separately.

```bash
python3 tools/qa01_rf071_original_real_read_join.py \
  /path/to/exact-qa01-campaign-case-zoom-zoo.zip \
  --out /path/to/rf071-original-actual-transactions.json
python3 -m unittest tests.unit.test_qa01_rf071_original_real_read_join -v
```

Fail-closed tests cover missing/wrong RF044 mirror rows, missing RF063 read, duplicated/reordered ordinal, mismatched byte/word value, address, bank, width, true RF064 return, RF066 chronology, wrong local V/H clock and a valid source-internal scanline crossing. An apparently sensible source stack status byte still cannot substitute for a raw executed access.

## What remains before accepting any USA course

The source original's actual bounded `01ED..01F1` bus reads are now transactionally observable. The **native** side must independently tie original-vs-native *differing* bytes to actual consumed native reads at a truly matching semantic stage with qualified **executed instruction PC**, account for intervening WRAM writers including DMA, preserve original/native independently measured clock domains, and ultimately demonstrate continuous full-race gameplay equivalence. The frozen full-WRAM samples still contain **92 genuine unmasked byte differences in 27/78 pairs**, and strict full-frame coverage, independently accepted candidate semantics, exact Windows hardware/product and cold disk durability remain open.

This work neither modifies the actual original/native CPU execution nor authorizes a saved-PC or NMI-status waiver. Its standalone tool **always returns 0 accepted USA events**. It complements, but does not absorb or reinterpret, the active RF062 sound pointer read lane.
