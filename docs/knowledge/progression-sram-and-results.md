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

## In-tour progress

**Confirmed.** Battery SRAM `0x0230`, `0x0232` and `0x10A9` count won races in the current tour. They survive a power cycle, and the next win continues the count, so unfinished tour progress is not lost on power-off. The counter counts wins, not distinct tracks: re-winning an already-won track still advances it. **Unknown:** whether a resumed tour awards its medal, and whether a lost race changes the counter. (`analysis/generated/tour-progress-persistence.json`.)

## Result flow

**Confirmed (1P).** Race results `0x99`, circuit results `0xBC` (per-lap time graph) and stunt results (`0x2F` tally, then `0x18` with the QUALIFY threshold) all advance to TRACK_SELECT. POST_RESULT_DECISION is not on the 1P path.

**Confirmed (VS, snesref).** A VS race ends when a racer finishes or at the ~10-minute timeout and shows `0xF9`. A decided race continues to VS CHAMPIONS `0xD3` and then PICK CHALLENGER `0x3F`, which is driven by the loser's pad (the winner's input is inert). That leads to a track choice `0x5A` (NEXT TRACK / SAME TRACK / SELECT TRACK / SELECT TOUR / QUIT). A drawn race shows a REMATCH banner `0xB7` instead. (`analysis/generated/result-screens-probe.json`, `vs-challenger-probe.json`.)

## Controlled validation

**Confirmed.** A gameplay-authored Crawler bronze (`0→1`) with valid checksum and byte-exact fresh-process reload is accepted evidence (`analysis/generated/progression-sram-acceptance.json`, produced by the Snes9x 1.51-rr historical replay). Seeding a medal cell and recomputing the `0x073C` checksum before boot is a reliable black-box way to put the game into a chosen tier.

## Port requirement

Stock save/progression behavior is part of authoritative gameplay state.

Any modern save UX may wrap or expose it, but it must not silently reinterpret medal values, unlock conditions or result semantics.
