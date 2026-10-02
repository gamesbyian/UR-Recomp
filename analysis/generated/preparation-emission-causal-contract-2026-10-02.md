# Camera-window preparation → PPU emission causal contract

Date: 2026-10-02  
Scope: stock race presentation path only

## Result

The stock race preparation/update-list seam is now bounded at the byte-level
interfaces that a Widescreen implementation would have to extend.

Two mirrored update lists carry the contract:

| role | count | destination words | value selectors |
|---|---|---|---|
| list A | `$0DCD` | `$0D8D + 2*i` | `$0D6D + i` |
| list B | `$0DCF` | `$0DAD + 2*i` | `$0D7D + i` |

The bank-81 preparation path compacts the candidate lists and records their
counts. `81:AA40` then filters those entries against camera/window-edge bands.
The bank-82 consumer at `82:D37F..D3C7` iterates the same list representation
in reverse index order and emits each surviving entry directly to the PPU.

## List construction

The first list is compacted through `81:A7DB..A8FF`:

- eligibility bytes are read from `$0D6D,X`;
- active entries are compacted toward index Y;
- the corresponding 16-bit VRAM destination words are copied into
  `$0D8D + 2*Y`;
- `81:A8FF` stores the compacted count to `$0DCD`.

The mirrored second list is compacted through `81:A910..AA34`:

- eligibility bytes are read from `$0D7D,X`;
- destination words are compacted into `$0DAD + 2*Y`;
- `81:AA34` stores the compacted count to `$0DCF`.

The 16-entry permutation table at `81:A7B6` maps original candidate slots to
destination-word slots during both compaction passes.

## Camera/window filtering

`81:AA40..AB87` consumes the compacted counts and does not alter the
destination words. Instead it clears selector/eligibility bytes for entries that
match camera-window edge bands.

For list A, the filter derives horizontal and vertical edge classes from:

- `$0505`, masked by `$001F`;
- `$04F5` camera velocity sign, selecting +0x0F or +0x11 for the paired
  horizontal edge;
- `$050D`, masked by `$FFE0`;
- the paired vertical edge `($050D + $0200) & $03FF`.

Each destination word from `$0D8D` is split into those same low-5 and
`$03E0` components. Matching an edge clears the corresponding byte in
`$0D6D`.

List B is exactly mirrored with `$0507/$04F7/$050F`, destination words in
`$0DAD`, and selector bytes in `$0D7D`.

This makes the camera/window dependency explicit: the filter changes whether a
prepared destination emits, not the gameplay object plane.

## Hardware emission

`82:D37F..D3C7` is a direct consumer of the same representation.

For each list, from `count - 1` down to zero:

1. load destination word from `$0D8D + 2*i` or `$0DAD + 2*i`;
2. store it to `$2116` (VRAM address);
3. load selector byte from `$0D6D + i` or `$0D7D + i`;
4. double it and use it as an index into the 16-bit table rooted at
   `$7E2132`;
5. `XBA` the selected word;
6. store the 16-bit result at `$2118`, producing the VRAM data write pair.

There is no second interpretation layer between these arrays and the hardware
emitter. The list destination words are PPU destinations, and the selector
bytes choose the emitted data word.

## Widescreen implication

A main-line Widescreen implementation that needs earlier or broader background
preparation has a concrete seam to change: candidate/list production and/or the
camera-edge filter before `82:D37F`.

The consumer itself should remain a dumb authentic emitter. Widening the
presentation horizon must not alter the independently proven
`$0F09 -> 81:82E6 -> 7E:C000` gameplay-activation path.

## Remaining dynamic discriminator

The retained Dragster finish-tail evidence has zero `$0DCD/$0DCF` entries at
the exact finish-ingress sample, so it cannot by itself prove a live list entry
end-to-end. The cheapest follow-up is therefore a bounded stock-race capture
that stops on the first non-zero update-list count, retaining WRAM plus PPU
writes. One such sample is enough to check the static one-to-one emission
contract dynamically; do not broaden into generic PPU tracing.


## Runtime discriminator disposition

The bounded stock-race probe was repaired and rerun through guest-relative
samples `prep-emission-000` through `prep-emission-300`. Run
`36961500327` confirms the analyzer is reading the intended WRAM/PPU dump
family, but both compact list counts remain zero at every retained sample:

- list A `$0DCD = 0`;
- list B `$0DCF = 0`;
- therefore there are no predicted compact-list emissions and no matching
  D383-shaped `$2116/$2118` event sequence in this window.

This is useful negative evidence, but it does **not** dynamically close the
preparation-list → PPU-emission seam. The static representation and direct
consumer remain established; runtime closure still requires a deterministic
fixture or stopping condition that actually observes a non-zero compact list.

Retain `tools/analyze_preparation_emission_probe.py` and the workflow as the
bounded discriminator. The next attempt should stop on the first non-zero
`$0DCD/$0DCF` state rather than extending this zero-list sampling window
blindly.
