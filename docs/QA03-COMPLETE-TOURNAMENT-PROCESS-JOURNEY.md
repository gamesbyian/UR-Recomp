# QA-03: Complete saved tournament journeys across fresh processes

Status: **native process-test candidate in PR #1054**, pending CI and merge.
QA-03 remains **P0 / L4 in progress**. This is complete backend-persistence
coverage for two named event schedules, **not** a claim that the game UI drove
all guest races, that two physical controllers participated, or that a packaged
Windows release candidate passed.

## Reuse and actual authority

The existing `tests/native/qa02_fixture_hardkill_process.cpp` executable is
reused: `tests/unit/test_qa02_fixture_hardkill_process.py` compiles the
same real C++ product stores and invokes a **new OS process for each fixture**.
No new ledger, file format, scheduler, artificial award or alternate result
writer is introduced. Each fixture explicitly arms a persisted launch,
binds the scheduled entrants and course at the capture boundary, publishes a
checksum/course-bound ordinary-2P `.urrun` + `.urmatch` pair through
`append_multiplayer_match_pair`, commits the exact immutable fixture receipt,
and reconstructs standings from disk in the next process. The test's
`native-sim-v1` provenance uses a simulated stock 2P result observation;
it does not execute an original guest race.

## Completed-schedule targets

| Scenario | Schedule | Fresh-process sequence | Required result |
| --- | --- | --- | --- |
| Two-entrant duel | 3 legs, 2 entrants, 3 fixtures, alternating stock seat order | Create; arm+cancel once; separately arm/publish/commit fixture 0, 1, 2; independently verify twice; explicitly replace active event | Exactly 3 matching Records run+match pairs and 3 immutable receipts; each racer played 3; exactly 9 standing points; finished archive survives replacement |
| Odd-roster tournament | 3 entrants, 2 complete round-robin legs, 6 fixtures, one bye per entrant per leg | Create; arm+cancel; 6 new fixture writer processes; independently verify twice; explicitly replace active event | Exactly 6 saved Records pairs and 6 receipts; each racer played 4; exactly 18 points; completed archive remains accessible |
 
A third targeted crash variation runs the same 3-entrant two-leg event, credits
fixture 0, then kills the next writer with `std::_Exit(82)` after it
published its valid run+match pair **but before** fixture 1's receipt. The
fresh process must retain fixture 0, explicitly rearm fixture 1 with a
different token, finish fixtures 1–5 and produce six credited receipts.
Seven valid Records pairs must remain: six receipt-linked results plus the
dead owner's uncredited but legitimate ordinary Records pair. Replacement
must preserve the completed archive. This covers a *mid-series C14 process
exit* but not physical power loss or a guest-process Windows crash.

Both journeys must reject rearming a credited fixture, never award a cancelled
fixture, restore a full schedule from its immutable definition, preserve
historical completed standings after a new active event starts, and retain
each old Records pair unchanged by the replacement. A failed assertion aborts
the Python test and reports the exact transition. No separate tournament
harness was introduced.

Run the focused acceptance as:

```sh
python3 -m unittest discover -s tests/unit -p test_qa02_fixture_hardkill_process.py -v
```

## Remaining P0 release cuts

1. **Guest-raced, controller-driven QA-03 L4:** existing native
   `run_modern_local_tournament_legs_acceptance.sh` stops after *arming*
   leg 2 and deliberately ending the event. The existing packaged Windows
   `run_windows_local_tournament_package_acceptance.sh` completes only one
   fixture and restores History on relaunch. Neither provides real guest-raced
   full leg-2/leg-3 and 3+ entrant events. A UI/input owner must supply the
   narrow interactive continuation route; do not rewrite that subsystem here.
2. **QA-02 two live Windows game instances:** #1052 adds POSIX/Windows
   nonblocking OS lease, tested in two native processes, with hard-kill
   takeover, stale rearm refusal, exact owner credit and Busy feedback.
   Packaged-Windows J-07/J-08 and old-client (noncooperating) limits remain.
3. **Profile selector/SRAM C04, receipt cuts and storage C16/C17:** no atomic
   group transaction across host-state selector, profile mirror/framework
   SRAM, run/match/optional ghost, receipt/pending or schema migration.
   Target verified authority transitions and fail-closed recovery, not a
   file × error × OS Cartesian product. Exact candidate and Windows device
   evidence must be separately logged.

Neither native acceptance nor a green PR promotes the release ledger's L4
gate. Only a ZIP-hash-pinned, real guest-input Windows session reaching its
actual terminal result and independently reopened Records/Standings/History
can do that.
