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

## Controlled validation

The recovered Dessyreqt workspace now supplies clean and all-silver 8 KiB SRAM images, so the historical model can be tested locally.

A clean-SRAM deterministic Dragster run showed that merely reaching the results screen does not yet mutate the medal matrix. The bounded follow-up advances the stock results UI and compares SRAM immediately before and after that transition. Once one game-authored medal change confirms the expected matrix cell plus checksum response, no broad SRAM reverse-engineering sweep is warranted for the current port plan.

## Port requirement

Stock save/progression behavior is part of authoritative gameplay state.

Any modern save UX may wrap or expose it, but it must not silently reinterpret medal values, unlock conditions or result semantics.
