# SRAM medal/progression static model — 2026-10-01

This pass reconciles the recovered Dessyreqt SRAM snapshots with the canonical USA disassembly before interpreting the controlled runtime probe.

## Medal matrix

The results/progression helper at `83:9EB4` computes:

`X = 16 * (D0 & 0xFF) + CA`

and callers then access `77:069C,X`.

The surrounding frontend/results code establishes the axes:

- `D0`: tour row;
- `CA` / `$017D`: unicycle/rider column.

Therefore `77:069C+` is a 16-column medal matrix with 16-byte tour rows.

Historical row mapping remains consistent with the exact addressing:
- row 0 Crawler: `069C..06AB`;
- row 1 Jumper: `06AC..06BB`;
- row 2 Shuffler: `06BC..06CB`;
- row 3 Bounder: `06CC..06DB`;
- row 4 Walker: `06DC..06EB`;
- row 5 Runner: `06EC..06FB`;
- row 6 Hopper: `06FC..070B`;
- row 7 Sprinter: `070C..071B`;
- row 8 Hunter: `071C..072B`.

## Medal value encoding

The stock results path at `83:8823..8838` reads the active medal cell, increments it, and stores only while the new value is at most 3. Values therefore progress monotonically and saturate at 3.

Together with the recovered all-silver snapshot, which changes the first eight rows from `00` to `02`, the value meanings are mechanically supported as:

- `0`: no medal;
- `1`: bronze;
- `2`: silver;
- `3`: gold.

## First-eight-tour prerequisite scan

Immediately after updating the current medal, `83:885D..88C9` holds the selected unicycle column fixed and scans eight cells separated by `0x10` bytes, i.e. that rider's medal in rows 0..7.

It derives three thresholds:

- sum of eight medal values == `0x18` (8 × 3) → tier 3;
- count of medals >= 2 == 6 → tier 2;
- count of nonzero medals == 4 → tier 1.

The chosen tier is written through both `83:9F49` and `83:9F81`.

This is why the Hunter row is not part of the prerequisite scan: Hunter is row 8, while rows 0..7 drive the derived progression tier.

## Derived per-unicycle tier tables

`83:9F49` writes the tier to `77:10D3 + (CA & 0x0F)`.

`83:9F81` writes the same tier to `77:10FD + (CA & 0x0F)`.

`83:9F14` reads `77:10D3+CA` in single-player mode, or returns the maximum of all 16 entries in another mode.

The recovered snapshots therefore have a direct explanation:

- Clean → All Silvers / No Hunter: first eight medal rows become `02`, and `10D3..10E2` become `02`;
- All Silvers / No Hunter → With Hunter: the medal matrix is unchanged while `10D3..10E2` become `03`.

The latter snapshot is best described structurally as a tier-3 derived-unlock table. The user-facing meaning of tier 3 can be tied to Hunter only where the frontend/unlock path proves that presentation.

## Checksum covering the medal matrix

`83:90F4` recomputes several SRAM checksums. One loop sums 170 16-bit words from `77:05E8..073B` and stores the 16-bit result at `77:073C`.

The medal matrix `069C..072B` lies wholly inside this protected region. Any persistent medal edit must therefore be accompanied by the corresponding `073C` checksum change.

## Controlled-runtime discriminator

A clean-SRAM deterministic Dragster route was checked at three adjacent states:

1. settled race-results screen;
2. after advancing once from results;
3. after the documented back input.

None of those transitions changed the medal matrix at `069C..072B` or the derived tier table at `10D3..10E2`. The adjacent result-screen transitions changed only unrelated live/progression working state.

This falsifies the timing hypothesis that the medal write merely occurs after leaving the results screen. The static result gate at `83:879A` explains the negative: medal update is conditional on the mode-specific result/performance gate, and the project's simple deterministic Dragster fixture is a finish/reachability fixture rather than a proven medal-winning run.

That negative is sufficient for the current discriminator because the persistent layout itself is already mechanically resolved by direct shipped-code indexing, value saturation, threshold scans, recovered clean/all-silver snapshots, and checksum code. Replaying or optimizing a TAS solely to force one `0→1` cell would add little implementation value.

## Stopping condition

Do not broaden into generic SRAM archaeology. Revisit the medal award gate dynamically only when a stock-progression acceptance test needs an actual medal-winning fixture. The current port already has enough evidence to implement and validate the matrix shape, medal values, first-eight-tour unlock thresholds, derived tier tables, and checksum boundary.
