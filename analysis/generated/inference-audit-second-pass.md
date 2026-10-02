# Second-pass inference audit

Date: 2026-10-02

This pass deliberately searched for things the first consolidation and audit did not normalize or join. It found one material correction to the course corpus and several new cross-source deductions.

## 1. The first course-name mapping was wrong after stream 5

The first consolidation inherited the manual/player-facing tour order and assigned it directly to RNC stream groups. Joining decoded header coordinates against Dessyreqt's complete 45-track landmark table falsifies that assumption.

The canonical five-stream RNC groups are:

1. Crawler
2. Jumper
3. Shuffler
4. Bounder
5. Walker
6. Runner
7. Hopper
8. Sprinter
9. Hunter

That is exactly the recovered SRAM medal-matrix row order.

So a useful new identity falls out:

```
progression_tour_row = floor((course_stream_index - 1) / 5)
```

The corrected order is now in `analysis/data/course-corpus.json`, and the historical note that previously encouraged the bad mapping has been amended.

## 2. Header landmark A.x is very likely the start/spawn X coordinate

After correcting stream identity, **43 of 45** historical course start-X coordinates equal:

```
header.spawn_or_landmark_a.x * 16
```

exactly.

The only exceptions are Zoom Zoo and Jumps. Those should be treated as special cases to investigate, not as enough evidence to discard a 43/45 exact relation.

This is substantially stronger evidence for the header field's semantics than the first pass recorded. The Y component and the A/B distinction remain less fully resolved.

## 3. Stunt identity has three independent signatures

All nine stunt courses simultaneously satisfy:

- they are slot 3 in their five-course group;
- decoded byte 2 / `stunt_time_or_mode` is 45;
- historical start X equals historical finish X.

None of the 36 non-stunt courses has start X equal to finish X in the recovered landmark set.

That gives the course corpus a robust semantic consistency check independent of any single reference.

## 4. Persistent racer state is more regular than the first audit captured

The first audit noticed regional spacing for three marshal fields. The recovered Dessyreqt corpus makes the larger pattern explicit: P2 persistent fields sit exactly **+2 bytes** from P1 for at least eleven useful pairs, including X/Y position, X/Y speed, facing, tabletop duration, Z-flips, rolls, flips, next checkpoint, and camera X speed.

This is a much better mining rule for the persistent racer struct:

1. take a known or candidate P1 word;
2. inspect +2 for its P2 sibling;
3. require shared marshal/read/write behavior before semantic promotion.

## 5. Regional WRAM relocation is not globally arithmetic

The WRAM motion atlas contains Europe-vs-USA clusters with several distinct deltas, including +10, +4, 0 and +6 among high-value state.

That rules out a tempting future shortcut: there is no single “Europe WRAM = USA + N” transformation. Regional state mapping needs cluster/anchor-specific evidence.

## 6. Progression was under-consolidated

The first pass left the medal/tier/checksum model mostly in prose. It is now normalized as `analysis/data/progression-model.json`.

That gives inference tooling direct access to:

- the 9×16 medal matrix;
- row order;
- medal value encoding;
- first-eight-row tier thresholds;
- primary and mirrored tier tables;
- checksum coverage;
- what runtime persistence is already proven and what medal-changing acceptance remains open.

The next progression experiment can therefore be judged against an exact expected logical SRAM transformation instead of “did some bytes change?”

## 7. One extra presentation constraint

Across the four recovered racer frame records, the stored `mask` value equals the first header byte exactly:

- 0540: 70
- 0542: 38
- 0544: 38
- 057E: 70

Combined with the first pass's fixed `4 + 2*N` record container, byte 0 is now a particularly strong candidate control/mask field for differential decoding. It should be tested against OAM piece eligibility before spending effort on the packed word payload.

## Consolidation changes

This pass corrected course identities, attached all 45 historical landmarks to course records, added the normalized progression model, enriched the state schema with paired-racer and regional-motion evidence, and corrected the historical course-order note.

The active preparation/emission and +8 composition PRs remain deliberately outside this audit until their evidence lands.


## 8. Historical numeric track IDs bridge directly to RNC streams

After correcting the canonical stream order, Dessyreqt's historical numeric IDs satisfy:

```
track_id = stream_index - 1
```

for all 45 courses.

This is a useful interoperability result because many recovered bot/map scripts identify courses numerically without carrying the modern stream index or canonical name. Those artifacts can now be joined without a hand-maintained lookup table.

## 9. The two header coordinate pairs are strongly constrained as racer spawns

Existing dense loader evidence already proves that Dragster's header pairs `(68,50)`, `(68,50)` become the two racer slots at `(1088,800)`, `(1088,800)` during initialization, exactly at ×16 scale.

The full corrected corpus strengthens that model:

- all 36 non-stunt courses have identical A/B X coordinates;
- their A/B Y coordinates are usually identical and otherwise differ by small lane-like offsets;
- four stunt courses use distinct A/B X coordinates as well.

This is much more consistent with paired racer spawn positions than with start/finish metadata. A single runtime initialization on a course with unequal A/B coordinates should be enough to separate P1 from P2 and close the assignment.

## 10. Course resources contain exact ordered bundles

Two particularly strong resource groups emerge from the full 45-course lists:

- `0x03..0x08` occur together in 43 courses and are consecutive, ascending and adjacent in every carrier;
- `0x09..0x0B` occur together in 42 courses and are likewise consecutive, ascending and adjacent in every carrier.

All nine stunt-course resource lists are duplicate-free, while several race/circuit lists intentionally repeat resource IDs.

These are structural facts, not semantic labels. The right next move is to inspect descriptor/content relationships for each bundle rather than naming them from incidence alone.

The already-promoted `0x24` checkpoint/finish family is now represented in the normalized resource catalog as a semantic anchor for that work.

## 11. Medal checksum behavior can be predicted before the next acceptance run

The medal matrix begins at even address `77:069C`, uses a 16-byte row stride, and the checksum sums little-endian 16-bit words.

Therefore, for a non-saturating one-step medal increment:

- even rider column → medal cell contributes `+1` to checksum `77:073C`;
- odd rider column → medal cell contributes `+0x0100`;
- arithmetic is modulo `0x10000`.

That is only the medal-cell contribution, because a real award transaction may mutate other protected fields too. Still, it gives the next progression acceptance fixture an exact checksum expectation rather than a vague “checksum should change.”

## 12. Racer presentation header is a 32-bit occupancy mask candidate

The strongest new presentation pattern is:

```
popcount(4-byte record header) = packed_word_count
```

for all four recovered racer frames.

Examples:

| Frame | Header | Header popcount | Packed words |
|---|---|---:|---:|
| 0540 | 70 C3 1E 30 | 13 | 13 |
| 0542 | 38 C3 1C 70 | 13 | 13 |
| 0544 | 38 E7 1C 70 | 15 | 15 |
| 057E | 70 C3 0E 38 | 13 | 13 |

Combined with `record_length = 4 + 2*N`, this strongly indicates a 32-bit occupancy/piece mask followed by one 16-bit packed word for each set bit.

The next decoder step should map set-bit positions to packed-word order and compare bit changes against OAM piece changes. That is a finite correspondence problem, not an open-ended format search.


## 13. Resource bundles survive all preserved builds

The ordered resource patterns are conserved in USA retail, Europe retail, the legacy beta, and the 1994-11-29 PAL prototype with the same carrier counts:

- `0x03..0x08`: 43 courses;
- `0x09..0x0B`: 42;
- `0x01/0x02`: 45;
- `0x16/0x18`: 39;
- checkpoint/finish resource `0x24`: 36.

That makes the first two groups especially strong structural resource bundles rather than one-build coincidences.

The seven Europe-retail course payloads known to differ from USA also separate cleanly:

- streams 16, 20, 27 and 35 retain dimensions, spawn pairs and identical resource lists;
- stream 4 (Switcher) retains dimensions/resource selection but changes spawn-A Y from 26 to 22;
- stream 26 (Down+Up) and stream 36 (Vertical) retain dimensions/spawns but append resource `0x22`.

So only two of the seven known PAL course changes alter the high-level resource list. Most regional course differences should be sought in course-local spatial/content data first.
