# Progression, SRAM and results

## Medal matrix and derived progression state

The historical nine-row layout is now supported directly by shipped code rather than only TAS notes.

`83:9EB4` computes the medal-cell index as `16 * tour + unicycle` before callers access `77:069C,X`. The resulting 16-byte rows are:

- Crawler: `0x069C-0x06AB`;
- Jumper: `0x06AC-0x06BB`;
- Shuffler: `0x06BC-0x06CB`;
- Bounder: `0x06CC-0x06DB`;
- Walker: `0x06DC-0x06EB`;
- Runner: `0x06EC-0x06FB`;
- Hopper: `0x06FC-0x070B`;
- Sprinter: `0x070C-0x071B`;
- Hunter: `0x071C-0x072B`.

The race-results path increments the active cell and saturates at 3. Combined with the recovered all-silver snapshot, the medal values are mechanically supported as:

- `00`: no medal;
- `01`: bronze;
- `02`: silver;
- `03`: gold.

After a medal update, the same results routine scans the selected unicycle through the first eight tour rows only. It derives progression tiers from three thresholds: all eight gold medals → tier 3; six-or-more silver-or-better medals → tier 2; four-or-more medals of any level → tier 1. The tier is written into 16-entry per-unicycle tables at `0x10D3-0x10E2` and `0x10FD-0x110C`.

This explains the recovered snapshots without assuming that `0x10D3` is itself a medal block: the first eight medal rows become `02` in the all-silver save, while the derived table becomes `02`; the “With Hunter” snapshot leaves the medal matrix unchanged and raises the derived table to `03`.

The medal matrix is checksum-protected. `83:90F4` sums 170 16-bit words covering `0x05E8-0x073B` and stores the checksum at `0x073C-0x073D`. Any persistent medal edit must therefore update that checksum as well.

RetroAchievements remains useful independent corroboration for the region and surrounding progression behavior, but the row/column geometry, value encoding, threshold scan, and checksum boundary no longer depend on it.

## Important ordering clue

The tour order above is not the same as some earlier provisional player-facing track ordering used during course-stream naming.

That means "tour order" is not yet one globally safe concept.

When linking:

- UI tour order;
- SRAM block order;
- runtime currentTrack IDs;
- RNC stream order;
- human course names;

record the exact mapping rather than assuming they all share one enumeration.

## Identity, opponents and tiers

**Confirmed.** Racer identity is a rider index. Indices 0–15 are the selectable racers (rider-select slot `2 * row + column`). The same index is the medal-matrix column, selects in-race palette asset `0x06 + index`, and selects the default name in the 16-byte player-name table at ROM `83:800C`. That table is copied to battery SRAM offset `0x000C` and is what the screens render. Indices 16–20 are `someone` (record-holder placeholder), `bronsen`, `silvia`, `goldwyn` and `anti-uni`. The silver opponent is **Silvia**; "Silverton" in older notes is wrong.

**Confirmed.** In 1P tour play the CPU opponent occupies the ordinary P2 racer slot (`$017F`) and palette path. On the main tours it is `17 + medal already held for that tour and rider`: none → Bronsen, bronze → Silvia, silver → Goldwyn, with TRACK_SELECT labelling the run BRONZE / SILVER / GOLD. This was checked on MIKE/Crawler and ANDREW/Shuffler. The Hunter tour fields Anti-Uni (20) under a GOLD label regardless of the Hunter medal. Once a rider's tier is 3, TOUR_SELECT becomes the two-column nine-tour page `0x10` that lists HUNTER. (`analysis/generated/legacy-cast-presets.json`, `tier-opponent-probe.json`.)

## Tour awards, ending and the splash cheat

**Confirmed (R-2026-10-04-UI-22).** When the fifth tour flag lands, the medal cell is incremented. Bronze and silver play the generic medal scene (`83:AEF6`). Reaching gold dispatches one of eight short per-tour vignettes (`83:88FD`), each a side-on track scene with a tour-specific prop that returns to TOUR_SELECT. Hunter's scene is the ending: two newspaper front pages, WHODUNNIT developer credits (`$9F` = 0x5B), then the title. The title-splash cheat **Up, Left, Up, R, A** (`80:F549`) sets every rider to tier 3 for the current power-on. It backs the real tiers up to `0x10E3`, sets `0x10D0` = 1 (which swaps the ending's front page for "CHEAT!"), and is undone on the next boot. (`analysis/generated/tour-award-ending-probe.json`.)

## Track records

**Confirmed.** Battery SRAM holds 150 record words at `0x0422 + 2*(50*rank + 5*tour_row + track)`, with a 16-bit sum checksum at `0x054E` and one holder rider-index byte per record at `0x0550 + index`. The three ranks are the GOLD/SILVER/BRONZE rows of the Track Records screen, meaning 1st/2nd/3rd best, not medal tiers. Each value is the race finish time or circuit best lap in 1/100 s (60000 = NO TIME) or the stunt score. Ten five-track groups follow the medal-matrix tour order. The tenth is probably unused padding: no decoded writer of the track index `$CE` reaches 45–49 (tour confirm clamps the row to ≤ 8 at `80:E69D`, the VS next-track cursor `0x067E,X` wraps at 44 at `80:AFF1`, and the attract demo counter `0x10C8` wraps at 40 at `80:949C`; static, bounded). (`analysis/generated/track-records-sram.json`.)

## Player stats and in-tour progress

**Confirmed.** Per-rider lifetime stats are 16 eight-byte records at SRAM `0x0230 + 8*rider`: PLAYED, WON, FAILED and SCORE as 16-bit words. FAILED counts did-not-finish results (time or best lap ≥ 60000), and SCORE accumulates stunt points. Player Scores derives LOST as PLAYED − WON and shows percentages of PLAYED. A P2 record is updated only when P2 is a human racer (rider index < 16). `0x10A9`/`0x10AB` are the VS session win tally and `0x10AD` is the play mode (1 tour, 2 VS). (`analysis/generated/progression-sram-semantics.json`, R-2026-10-04-UI-21.)

**Confirmed.** In-tour progress is one flag per track at SRAM `0x1075 + 5*tour_row + track` (50 bytes, outside the `0x073C` checksum). A qualifying 1P result sets the flag (`83:87F5`). When the tour row sums to 5, `83:881B` clears it and increments the medal cell. Confirming a rider zeroes all 50 flags (`80:BBC1`), so an unfinished tour does not survive a power cycle or a rider change, although the bytes themselves persist. Leaving TRACK_SELECT for TOUR_SELECT keeps the row unless the medal cell changed since the tour was confirmed (snapshot at SRAM `0x10D1`, `80:E6BF`; it also drives the BRONZE/SILVER/GOLD run label), so a tour can be left and resumed within a session (static decode). (`analysis/generated/tour-progress-persistence.json`, R-2026-10-04-UI-20.) The earlier "tour-win counter" was the PLAYED stat; `0x10A9` is a persisted wins counter.

## Result flow

**Confirmed (1P).** Race results `0x99`, circuit results `0xBC` (per-lap time graph) and stunt results (`0x2F` tally, then `0x18` with the QUALIFY threshold) all advance to TRACK_SELECT. POST_RESULT_DECISION is not on the 1P path.

**Confirmed (VS, snesref).** A VS race ends when a racer finishes or at the ~10-minute timeout and shows `0xF9`. A decided race continues to VS CHAMPIONS `0xD3` and then PICK CHALLENGER `0x3F`, which is driven by the loser's pad (the winner's input is inert). That leads to a track choice `0x5A` (NEXT TRACK / SAME TRACK / SELECT TRACK / SELECT TOUR / QUIT). A drawn race shows a REMATCH banner `0xB7` instead. (`analysis/generated/result-screens-probe.json`, `vs-challenger-probe.json`.)

## Controlled validation

**Confirmed.** A gameplay-authored Crawler bronze (`0→1`) with valid checksum and byte-exact fresh-process reload is accepted evidence (`analysis/generated/progression-sram-acceptance.json`, produced by the Snes9x 1.51-rr historical replay). Seeding a medal cell and recomputing the `0x073C` checksum before boot is a reliable black-box way to put the game into a chosen tier.

## Boot validation and malformed SRAM

**Confirmed (R-2026-10-08-SRAM-01).** On a cold boot the stock game validates only the 12-byte format signature. `80:8C4E` compares SRAM `0x0000-0x000B` with ROM `83:8000` (`ASJIver3.30` + `0xFF`). On any mismatch it reformats the whole cartridge to the fresh image, which is byte-identical to `Clean.srm`. Otherwise it keeps every byte. No checksum is checked at boot. The `0x073C` medal checksum, the `0x054E` records checksum and the other seven sums that `83:90F4` writes all survive a mismatch unchanged. Two compare routines (`83:89D9`, `83:8A59`) are never called (static). Out-of-range values are also kept: medal 7, record `0xFFFF`, holder `0xFF` and in-tour flag `0xFF`.

A boot that keeps the SRAM still rewrites a fixed set of bytes:

- `83:8AF7` (the mirroring probe) leaves `0x1FFF` = `0x56`;
- `83:8B23` zeroes `0x0400-0x041F`, the play mode `0x10AD` (so `0x7F` becomes 0) and the tier mirror `0x10FD-0x110C`.

The framework (`RtlReadSram`) reads up to 8 KiB over zeroed cart RAM and only logs `Error reading` on a short read. As a result:

- an empty file, or one too short to hold the signature, is reformatted;
- a longer truncated file keeps its prefix and silently gets a zero tail;
- an oversized file is cut to 8 KiB.

On exit the framework writes the live image back and keeps exactly one previous revision as `save.srm.bak`. A Modern profile root boots identically. Evidence: `analysis/generated/malformed-sram-containment.json`.

Consequence for host code: the guest is not a semantic validator. It will run on checksum-invalid or out-of-range bytes. Any host path that writes a profile mirror into live SRAM without a guest boot must apply the same signature check itself (see `docs/MODERN-PRODUCT-LAYER.md`).

## Port requirement

Stock save/progression behavior is part of authoritative gameplay state.

Any modern save UX may wrap or expose it, but it must not silently reinterpret medal values, unlock conditions or result semantics.
