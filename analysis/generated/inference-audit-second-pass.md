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
