# QA-01: Zoom Zoo post-result SRAM byte discriminator

**Owner:** independent gameplay verification, QA-01/07. **Status:** read-only address classifier; zero USA complete-event credit.

## Original experiment and specific missing evidence

The executed [corrected original/native Zoom Zoo run 38684825148](https://github.com/gamesbyian/UR-Recomp/actions/runs/38684825148) has the genuine 2014 original controller movie, independent race entry calibration, matching result onsets (+5163/+5163), positive Circuit results, and an 8 KiB fresh-original/native SRAM pair at result-relative +8, +16, +24, +32, +64 and +72. Hash-verification of artifact 11950385272 (ZIP SHA-256 69da3deb508ce0184fd2176283452d20fb3ed05624aee62c5965a40136d5b297) confirmed that the SRAM images agree through +32 and first disagree at the **sampled** +64 observation; the source-qualified Crawler course's three ranked record entries still agree. The original movie's in-tour SRAM is a third, distinct source, not a simultaneously sampled fresh SRAM image.

The exact +64 differing addresses remain unknown because that artifact contains SRAM fingerprints, not raw 8 KiB images. At +5171 the named contact values temporarily differ, at +5178 the reused race-state byte differs, and at +5179 native returns to menu F6 while original is still at BC; original follows at +5180. Those are observation times, not independently proven first CPU writers.

## Source-bound existing-workflow consumer

The opt-in tools/qa01_postresult_sram_diff.py independently reads the six already-produced original-follow-XX.sram.bin files from the existing original and native replay directories. It verifies **every 8 KiB file** against its matching producer SHA-256 and independently checks the USA ROM, archived source/result identity, both race-entry-relative host-frame axes, RF-015-corrected +5163/+5163 onset, decoded original SRAM course ranks and checksum. Missing files, altered bytes, changed clocks or producer contradictions abort the experiment rather than generating a pass.

The output groups actual byte addresses by the known original Track Records word table (0x0422..0x054D), checksum (0x054E..0x054F), holders (0x0550..0x05E5) and other cartridge RAM. Each of six rows contains exact full-image hashes, difference counts, at most 64 annotated byte differences, the SHA-256 of the complete address set, and observed changes since the previous sample in each guest. No ROM or complete SRAM contents are published. These region labels do **not** make every score-table byte a live gameplay effect.

The existing manual qa01-event-campaign.yml invokes the additional consumer only after an actual **successful corrected Zoom Zoo source-followthrough** producer/classifier. It uploads the compact report to the **same case artifact**, using the original immutable shared binaries and case workspace. No new recompiler, acceptance oracle, automatic workflow, CI matrix or candidate is created. Default campaign runs remain unchanged.

## Decision and stop

A single exact corrected Zoo rerun can determine which battery **addresses** first disagree at the sampled +64 point. If records/checksum/holders are equal, inspect the source-backed owner/reader of the other address before calling it a progression bug. A time-shifted result-lifecycle write remains a possibility; test only with independent CPU/beam evidence from Agent 5, never by shifting controller input or weakening strict frame comparison. Cold second-process persistence and actual Windows candidate provenance are separate required admission steps.

This consumer **cannot** prove which opcode first wrote a byte, whether the first divergence occurred at +33, source logic-tick equivalence, progression acceptance or file durability. The original strict comparator, 45 USA course denominator and independent QA release ledger remain untouched: **0/45 accepted events**.
