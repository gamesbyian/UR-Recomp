# Checkpoint/finish resource family closeout — 2026-10-01

## Decision

Promote course resource ID `0x24` as the shipped **race/circuit checkpoint-finish resource family**.

## Corpus evidence

`tools/analyze_course_resource_lists.py` decoded the tail resource lists for all 45 course payloads in each preserved build.

For `0x24`:

| Build | Occurrences | Race A | Circuit A | Stunt | Race B | Circuit B |
|---|---:|---:|---:|---:|---:|---:|
| USA retail | 36 | 9 | 9 | 0 | 9 | 9 |
| Europe retail | 36 | 9 | 9 | 0 | 9 | 9 |
| Legacy beta | 36 | 9 | 9 | 0 | 9 | 9 |
| PAL prototype 1994-11-29 | 36 | 9 | 9 | 0 | 9 | 9 |

The usage fingerprint is identical in all four builds:
`06bdee2403829a8cbbaf9f2b1f4358eda34dec19810489f818b56c20706c2ed6`.

No cross-build remapping is needed for this resource: the numeric ID remains `0x24`.

## Independent semantic anchor

Dragster's exact materialization spans prove resource `0x24` owns C000 offsets 6..14 and contributes nine copies of runtime object code `0x14`.

Runtime object code `0x14` dispatches to `Race_HandleCheckpointFinish`.

Thus two independent relations converge:

1. **local behavior:** Dragster `0x24` materializes checkpoint/finish object cells;
2. **global incidence:** `0x24` is present in every Race/Circuit course and absent from every Stunt course.

That is sufficient for the family-level semantic promotion.

## Boundaries

This result does not claim that all `0x24` materialized content is byte-identical across courses or builds. The course loader selects a reusable resource/template family, and course-specific placement/topology may still come from other payload structures.

Do not spend a broad runtime campaign proving all 36 instances one by one. Revisit individual `0x24` materializations only if a concrete course parser/editor or fidelity discrepancy needs their exact placement semantics.

## Follow-on value

The 45-course manifest also establishes that the four preserved builds retain the same 38 numeric resource IDs and overwhelmingly identical usage structure. Europe retail changes resource-list length only on the already-known changed course payloads, making those courses the natural bounded targets for later resource-level regional analysis rather than a whole-corpus sweep.
