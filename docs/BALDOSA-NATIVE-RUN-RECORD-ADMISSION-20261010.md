# Native Baldosa result-to-Records acceptance contract

Status (2026-10-10): implementation handoff, NOT a completed-event parity
witness, cross-backend replay certification or Windows beta release claim.
Original-emulator QA-01/07 and the release ledger retain independent authority.

## Existing pieces

Merged #1229 observes read-only genuine P1 line-crossing finishes and stock
ordinary 2P SRAM results after the actual native guest frames. Merged #1230
shows profile-scoped historical .urrun archives read-only in the Modern root,
but does NOT publish newly played events. #1238 (review at authoring) uses the
pinned runner's actual post-filter submitted P1/P2 controller words and
source-identified decoded USA Race courses, retaining the original Modern RLE
recorder. The pure native admission adapter in this branch validates a typed
result against selected-profile/participant authority and canonical
CompletedRunRecord, returning only an in-memory candidate. Nothing mints
medals, ghosts, tournament results, or a durable run yet.

## Required next integration and proof

1. Snapshot source-confirmed named Modern catalog/profile authorization at
   actual guest race entry, with exact stock SRAM and safe profile ID. A
   default anonymous save or Modern root preview is not enough.
2. Sample the original pinned host's **resolved controller word** exactly once
   per executed post-entry guest frame, excluding host-only paused redraws.
   Preserve human/script/debug merging before RtlRunFrame and the existing
   runner execution/run-ahead branches.
3. Require the stock P1 finish-line write with same-frame 60Hz sub-tick, or
   source-validated stock 2P 0xF9 result and participant binding, plus decoded
   original USA ordinary Race course. A results-looking menu or timer limit
   does not by itself authorize a record.
4. Re-authorize the selected profile at publication under existing selector,
   catalog and profile lock conventions, and require both 2P participants
   to match the original stock rider identities. Avoid profile crossover
   when a second process changes the selector.
5. Publish only through canonical immutable append_completed_run_record in
   runs/<safe-profile-id> and the canonical multiplayer-match paired store.
   The native build compatibility ID MUST differ from old SNESRecomp until
   exact cross-backend replay/input-latch equivalence has passed. Do not
   assert ghost, PB or tournament compatibility from codec readability.
6. Capture one uninterrupted **real** Windows 1P race from native Modern root
   through settled guest results, saved run, fresh-process Records readback
   and unchanged named SRAM. Repeat for real local 2P results with source
   rider/time identities and paired .urmatch. A seeded fixture or synthetic
   C++ observer alone cannot satisfy this acceptance condition.
7. Preserve fail-closed adversarial routes: paused Quit, pre-results Quit,
   stale root/player-count handoff, second-process profile switch, wrong
   course/mode, partial SRAM, duplicate run publication, truncated archive,
   crash during staging and fresh-process restart. Issue #1214 independently
   tracks raw SRAM and typed-profile cross-file crash recovery.

Do not call native Records complete or count a new course as QA-01 accepted
until the exact player-facing event and strict independent comparator pass.
The previous Modern core remains rollback until then.
