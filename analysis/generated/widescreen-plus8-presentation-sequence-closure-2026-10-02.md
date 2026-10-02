# +8 presentation-sequence divergence closure — 2026-10-02

## Scope

This closes the first +8 presentation-state divergence under the deterministic Dragster tail while preserving the full renderer and semantic/event-relative anchors.

The clean runtime evidence is workflow run `36978866214` (PR #214). Earlier trace-enabled paused-host writer evidence remains rejected because it collapsed the retained 0/+8 divergence.

## Event-relative boundary

Through `object-tail-140`, control and +8 agree on:

- meaningful P2 race state;
- P2 presentation ID;
- explicit presentation override `$0F4F` and persistent backing `$0DEB` (both zero);
- ordinary selector state including `$0300`, `$0F77`, `$0F83`, `$0FD9`, facing, motion, angle and the sampled tabletop/override counters;
- P2 presentation-sequence selector `$136B = 0`;
- P2 sequence cursor `$11DD = 0`, identity `$11E1 = 0`, and initialized flag `$11E5 = 0`.

At `object-tail-141`:

- control initializes sequence selector/identity **1**;
- +8 initializes sequence selector/identity **3**;
- both initialize the same cursor **1** and flag **1**;
- control writes P2 persistent presentation override `$0DEB = 0x0A45`;
- +8 writes `$0DEB = 0x0A8D`;
- the normal P2 marshal copies `$0DEB -> $0F4F`;
- `83:EF06..EF0C` selects nonzero `$0F4F` into working presentation `$0F97`;
- `82:935A..935D` persists that selection into `$0FEB`.

VRAM remains equal at `141` and first differs at `object-tail-142`; OAM remains equal throughout the retained early gap.

## Hidden producer recovered

The apparent direct `$0F4F` producers at `82:961D` and `82:A45A` are not the source of `0x0A45/0x0A8D`.

The actual producer is the indexed presentation-sequence writer:

`83:EB57 -> 82:8952/8956 -> STA $0DE9,Y`

For P2, `Y=2`, so the final store is exactly `$0DEB`.

`82:8956`:

1. receives a small sequence selector in A;
2. selects a sequence pointer from the bank-`17` table rooted at `$C7C8`;
3. maintains per-player sequence cursor/identity/initialized state at `$11DB/$11DF/$11E3 + Y`;
4. reads the selected frame ID from the sequence;
5. stores it through `$0DE9,Y`.

The clean run shows a **different sequence identity with the same cursor**, so the divergence is sequence selection, not sequence-consumption rate.

## Selector source

P2 sequence setup around `83:EB20..EB57` initializes `$136B`. On the branch capable of producing the observed odd selectors, `83:EB3F..EB51` maps the low byte at `$7710B1` as:

- counter 0/1 -> sequence 1;
- counter 2/3 -> sequence 3;
- counter 4/5 -> sequence 5.

Bank-83 code bounds `$7710B1` to a six-state cycle:

- `83:C8EF..C8FB` clamps/reset values outside 0..5;
- `83:C9E2..C9F2` advances it modulo 6.

Therefore the observed selector split proves that, at the same semantic event, the control samples `$7710B1` in class **0/1** while +8 samples it in class **2/3**. The exact member within each two-value class is not directly dumped by the current WRAM-only harness, but that ambiguity cannot alter the selected sequence or causal conclusion.

This counter also participates in bank-83 presentation/frontend setup, including the `$770748/$770749` player-color selector family. It is not part of authoritative race simulation.

## Downstream upload chain

The already recovered presentation chain then explains the one-event VRAM lag:

1. sequence 1 vs 3 writes `0x0A45` vs `0x0A8D` to P2 `$0DEB`;
2. P2 update copies the value through `$0F4F -> $0F97 -> $0FEB` at `object-tail-141`;
3. `83:F0BB` consumes `$0FE9/$0FEB`;
4. `83:F296` resolves the selected frame through `20:8000 + frame_id*3`;
5. `83:F2BB` consumes the packed presentation record and stages `$15A1/$1645/$16E9` VRAM DMA descriptors;
6. NMI consumes those descriptors through `$2116` / DMA-to-`$2118`;
7. VRAM first differs at `object-tail-142`.

The contemporaneous `$0C75..$0C7F` difference is renderer staging scratch used by `83:F1D4..`, so it is downstream of the selected presentation rather than the selector input.

## Causal statement

> Same authoritative P2 race state -> +8 samples a different phase class of the six-state presentation/frontend counter `$7710B1` at `object-tail-141` -> `83:EB3F..EB51` initializes P2 sequence 3 instead of sequence 1 -> `82:8956` selects `0x0A8D` instead of `0x0A45` and stores it to P2 `$0DEB` -> `$0F4F -> $0F97 -> $0FEB` diverges at `141` -> `83:F0BB/F296/F2BB` resolves and stages different presentation data -> VRAM diverges at `object-tail-142`.

This is a presentation/frontend cadence-phase effect, not a gameplay-state divergence and not a VRAM-originating failure.

## Disposition

The first +8 presentation-state phase lane is closed sufficiently for the current Widescreen decision.

Do not patch gameplay activation, collision, course semantics, or the authentic-center x=255 composition symptom to compensate for this sequence choice.

The next Widescreen implementation experiment is now the deliberate **earlier/additional `$03xx` strip scheduling** against the already-closed camera-demand -> descriptor -> NMI-DMA chain, with authoritative simulation held invariant. The later x=255 composition issue remains a downstream renderer acceptance item after widened preparation is established.
