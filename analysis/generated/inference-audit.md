# Initial inference audit

Status: first pass complete  
Date: 2026-10-02

This audit consumes the normalized query surfaces in `analysis/data/` and applies the repository's derive-first/probe-second rule. Exact corpus relations are marked as derived invariants; extrapolations beyond directly sampled runtime evidence remain predictions.

## Highest-value findings

### IA-C02 — the course-tail cursor question closes statically

Across all 45 canonical USA course streams:

```
decoded_size - resource_cursor_initial = resource_count + 2
resource_terminator_offset = resource_cursor_initial + resource_count
```

Exactly one byte follows the terminator in every case.

This is an exact full-corpus relation, not a statistical tendency. The most economical interpretation is that the header/cursor value points at the first resource-list entry. The remaining post-terminator byte should stay separately unnamed until its consumer is identified. A second runtime course is no longer required to discover the cursor's role.

### IA-C01 / IA-C03 — the course corpus is a fixed-area reshape family

All 45 normalized dimension pairs multiply to 1024. Only six shapes ship:

| Header shape | Courses |
|---|---:|
| 256×4 | 4 |
| 128×8 | 3 |
| 64×16 | 22 |
| 32×32 | 11 |
| 16×64 | 4 |
| 4×256 | 1 |

Applying the already promoted presentation transform gives 16,384 coarse sectors and 67,108,864 square world units for every course. The four-shape presentation sample directly supports the transform; applying it to every unsampled course remains a strong prediction until a representative runtime/materialization check falsifies or confirms it.

This changes the validation problem from “45 unrelated courses” to “six geometric families sharing a fixed-area canvas.”

### IA-C04 / IA-C05 — resource lists contain stable scaffolds

The exact longest common prefixes by track kind are:

- race-a: `[1, 2]`
- circuit-a: `[1, 2, 3, 4, 5, 6, 7, 8]`
- race-b: `[1..11]`
- circuit-b: `[1..11]`
- stunt: `[1]`

Resources 1 and 2 occur somewhere in every course, and resource 1 is first in all 45. Downer is the sole exception to resource 2 being second: it uses `[1,18,2,...]`.

This supports a reusable base-resource scaffold model. It does not yet justify semantic names for individual resource IDs.

### IA-S01 — racer-state layout arithmetic survives regional relocation

For USA retail, the 1994 PAL prototype, and Europe retail alike:

- persistent X-speed → persistent Y-speed = **+4 bytes**;
- shared working X-speed → working Y-speed = **+2 bytes**;
- boost working slot → persistent boost slot = **+2 bytes**.

Those repeated deltas can be used as hard search constraints for adjacent unnamed racer-state projections across builds. Address spacing alone is not enough to assign semantics.

### IA-K01 — code-address mirror normalization was hiding valid joins

The consolidation tests exposed that `SYMBOLS.md` sometimes records ROM code in low mirror banks such as `01:` / `02:`, while the structural census uses CPU-space `81:` / `82:`. Canonicalizing low-bank ROM symbols to their high-bank mirrors recovers four direct named-function→structural-region joins and four named-function→cross-build correspondence joins.

All future cross-source code tooling should normalize this representation at ingestion.

### IA-P01 — racer presentation records have a fixed container boundary

All four recovered racer presentation frames satisfy:

```
record_length = 4 + 2 * packed_word_count
```

That gives the differential decoder a fixed four-byte header followed by 16-bit packed words. Future frame recovery can test the equation immediately before interpreting individual packed fields.

## First cross-shape stress corpus

A six-course set covers every shipped dimension family while preserving Dragster as the already instrumented baseline. For each other shape, choose the course with the highest resource count:

| Course | Stream | Shape | Resources |
|---|---:|---:|---:|
| Dragster | 1 | 256×4 | 6 |
| Flat Fun | 9 | 128×8 | 35 |
| Crock | 17 | 64×16 | 34 |
| Marathon | 27 | 32×32 | 30 |
| Vertical | 36 | 16×64 | 33 |
| Little Dipper | 38 | 4×256 | 19 |

Griller (stream 41) is a useful optional seventh case when maximum decoded-size/compression complexity matters: its decoded course payload is 65,354 bytes, the largest in the corpus.

This is a much cheaper first generalization matrix than 45-course runtime coverage.

## Negative result: size heuristics are not semantic classifiers

Stunt courses are more compressible on average, but the distributions overlap:

- stunt compression ratio: 0.0207–0.1040;
- non-stunt: 0.0109–0.2067;
- stunt resource count: 9–20;
- non-stunt: 6–35.

Dragster is more compressible than every stunt course. RNC size, compression ratio, decoded size, and resource count should therefore remain descriptive complexity features, not standalone track-type classifiers.

## Work deliberately not duplicated

The audit does not infer around active-agent evidence:

- PR #203 owns camera-driven preparation → VRAM/emission closure.
- PR #206 owns the +8 host-composition edge divergence.
- progression prediction can be added after the progression acceptance evidence is stable.

When those lanes land, their new evidence should be normalized and the relevant audit phases rerun.

## Immediate consequences

The course resource cursor can be promoted without another runtime trace. Cross-course geometry tests can use six representatives rather than 45. Resource archaeology can focus on the universal/scaffold IDs, and racer-state mining can use exact regional slot arithmetic as a constraint.

Future runtime experiments from this audit should exist only where two or more models remain compatible with these derived relations.
