# Frontier 15-frame results and source-meaning adjudication (2026-10-13)

## Admitted evidence

[Run 38446393623](https://github.com/gamesbyian/UR-Recomp/actions/runs/38446393623) completed successfully on exact source `dd5632f0a612ee22cc46d9b1ce7a6005a5fa555f`. The authoritative [append-only research ledger](https://github.com/gamesbyian/UR-Recomp/blob/research/qa-cumulative-ledger/.github/qa-cumulative/ledger.json) accepted 100 real two-controller trajectories and 112 compiled-native processes, including four repeat/seat-ablation cases. The run contributed **200 previously unseen 96-bit normalized native WRAM fingerprints** to the exact census, growing **20,379 → 20,579**. Three-frame checkpoint fingerprint populations remain **1 / 100 / 100**, deliberately unchanged by the extra source-feature inspection.

The newly implemented observer examined 15 already-generated full WRAM checkpoints per case instead of the prior three. Counts are source-field *case incidence*, not distinct frame counts or original-SNES correctness:

| Native source-field predicate | Historical three frames | All fifteen | Cases newly detected by denser observation |
| --- | ---: | ---: | ---: |
| Both tracked air fields nonzero together | 1 | 1 | 0 |
| Both racer slots moving | 100 | 100 | 0 |
| Both tracked rotation values change | 95 | 100 | **5** |
| Both racer progress tuples change | 100 | 100 | 0 |
| Opposing X-velocity signs | 71 | 100 | **29** |
| Offscreen candidates `$121B/$121D` nonzero | 0 | 0 | 0 |
| Split-mode candidate `$0DDB` changes | 0 | 0 | 0 |
| Split-mode candidate `$0DDB` nonzero | 100 | 100 | 0 |

The five raw-register value populations across all **1,500 native source snapshots** were: `$0545 ∈ {0,1}`, `$0547 ∈ {0,1,2}`, `$121B = 0`, `$121D = 0` and `$0DDB = 1`. These values are exactly recorded source observations within this specific 100-case cohort. They do not establish that any field is invariant outside these frames, course, mode, input population, or the original emulator.

## Reproduce useful new witnesses

| Source question | Seed | Arm | Shard | First sampled frame |
| --- | ---: | --- | ---: | ---: |
| Two air candidates simultaneously nonzero | **50036056** | rotation | 2 | **2580** |
| Both rotation values change, missed by three-frame sampling | **50036005** | alternating | 0 | **1980** |
| Opposing X-speed signs, missed by three-frame sampling | **50036002** | P2-focus | 0 | **2820** |

The dual-air event was **already visible in the legacy frame 2580**; the additional twelve checkpoints did not newly reveal it. The two other witnesses do demonstrate how sparse sampling concealed source-state transitions. Reproduction requires the frozen plan, source SHA, pinned compiled native executable hash `28501fa3268f82d83672122cddbd2628ce5b2458e625f46d93766f50befbe515`, and source-verified USA ROM SHA-256 `859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478`. The archive does **not** distribute ROM bytes. The original and native versions have **not** yet been matched for these new input trajectories.

## Why the two zeros are not equivalent to game defects

**Split mode $0DDB:** [recovered bank-81 camera control](knowledge/rendering-camera-and-oam.md) conditions second-camera work on `$0DDB != 0`. A value continuously equal to 1 in a two-player race is consistent with that source structure, not an absence of split-screen function. The game's *visible* top/bottom split also relies on line-timed OAM mutation (scanlines 0 and 112, OAM high-table byte `$18`, racer sprite slots 96–99). This is a distinct mechanism. Do not use `split-register-changes = 0` as evidence of failed raster switching, or expand inputs in hopes that a normal active 2P race will disable its second camera.

**Offscreen candidates $121B/$121D:** their zero values cannot be interpreted as a complete visibility/culling census. Source recovery also identifies `82:D2D8..` producing OAMDATA from per-screen racer projection bytes `$1501..$1510`, using sentinel coordinates and visibility bits at `$1599`. Neither `$1599` nor the sentinel-coordinate fields is included in the current frontier offscreen predicate. The offsets $121B/$121D are names inherited from an earlier RAM watch and lack qualified semantic authority over all sprite visibility transitions. **Do not call a constant $121B/$121D a native culling failure.** Check source-backed writer paths, per-screen projection sentinels and original PPU output first. Graphics/QA-08 independently owns that work.

**Dual air:** `$0545` and `$0547` nonzero together at frame 2580 is a real native raw-slot observation. These registers alone cannot prove simultaneous visible airborne racers. Use the precise reproduction seed with synchronized original-USA emulator input and a source-qualified flight/pose or physics observer before asserting parity or a discrepancy. QA-01/07 owns strict gameplay acceptance.

## Highest-value next experiment

Do **not** launch another broad 10,000-case search for the two invariant candidate registers. Instead:

1. Reproduce seed **50036056**, arm `rotation`, frame **2580** under the original SNES emulator and the exact native build; verify controller input, race phase, $0545/$0547 semantics and frame alignment before interpreting an air or trick mechanic.
2. For QA-08/10, source-qualify `$1599` visibility and `$1501..$150E` sentinel coordinates at an already-observed split-racer transition, independently capturing OAM/PPU presentation. Compare original vs native on matching guest frames.
3. Distinguish the stable *2P camera-enable condition* `$0DDB` from actual scanline OAMDATA switching; use the project's existing original raster/OAM evidence rather than another single WRAM flag.
4. Revisit large frontier exploration only if a new source-backed observer or original oracle yields a discriminating causal question. Preserve the original three-frame fingerprint epoch and append-only exact census across such changes.

No release quality ledger, original-event oracle, graphics implementation, source ROM or gameplay code is modified by this research report. **Official complete original/native USA event acceptance remains 0/45 unless independently changed by its owning authority.**
