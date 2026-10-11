# Native Baldosa 2P: source-bound canonical match publication

**Status:** implementation candidate, stacked atop the explicit two-seat
profile join PR #1326 and read-only native Records PR #1323. This does
**not** close full source-parity, human two-controller or fresh-process
Windows acceptance.

The native post-frame observer already samples a genuine stock ordinary-2P
Race settlement and resolved P1/P2 controller words. During the real
source-verified 2P handoff only, the existing Modern root can supply
two distinct profile entries separately confirmed by P1 and P2 gamepads.
No other guest/menu state can provide names to the result publisher.

`ur_baldosa_modern_publish_settled_two_player_match` consumes exactly
those two inputs. Before any persistent write it:

1. Requires verified process-selected P1, genuine ordinary-2P result,
   source-verified USA Race course, original input-frame count, and a
   self-consistent stock title result.
2. Calls the established `bind_local_multiplayer_match_context`, which
   rejects any mismatch between the source stock P1/P2 rider indices
   and the two explicitly selected racer identities. The canonical
   `assemble_baldosa_native_run_record` validates the same real source
   result and both captured gamepad lanes for a `race-2p` carrier.
3. Obtains the existing nonblocking selector, catalog and two named
   profile OS leases before publication. It rechecks launch selector,
   current typed P1/typed P2 states, real roster membership and their
   complete unmodified 8192-byte raw SRAM files. Conflicts reject;
   neither existing player save nor guest WRAM is modified.
4. Rejects substituted symlinked/dangling shared `multiplayer-runs`
   archive roots and delegates publication to the existing
   `append_multiplayer_match_pair`, which stages metadata and record
   together and makes the run visible last. Success is logged only
   after that exact canonical pair is committed. A repeated guest
   event in this process cannot publish twice.
5. Leaves anonymous, missing, stale, duplicate or unconfirmed two-player
   sessions **playable but unrecorded**. It grants no tournament fixture,
   unverified replay, new trophy or leaderboard authority.

The native regression exercises the *actual* profile catalog, SRAM,
source-to-run binder and paired archive codecs with synthetic typed
results, proves selector-lease contention cannot mint a half-pair,
checks two distinct identities, stock rider agreement, stable P1/P2
input lanes, rejection of changed opponent racer identity, and
duplicate-event refusal. Source fixtures are not evidence of an
actual played event.

Remaining acceptance: two real physical/virtual controllers confirm
distinct profiles, select the corresponding original stock riders, race
to a genuine title result, produce a newly canonical pair, and show the
selected winner/loser after a **fresh Windows process** loads the same
archive. This must be recorded in the independent release ledger.

## Bounded, named two-seat native Windows handoff route

The existing named Records Windows route now exercises a third fresh
process, after the canonical fixture registers a separate initialized
P2 profile and selects its real SRAM. A test-only semantic edge invokes
the **same production** root P1/P2 gamepad callbacks once for each seat
(mode `UR_BALDOSA_MODERN_ROOT_KEY_SMOKE=3`). The runner requires ordered
named-profile activation, explicit P1 and P2 confirmations, the already
owned stock request, and the **actual original guest** stock 0x3D
transition. Both historical run+match archives must remain byte-identical
after the process exits.

This narrow smoke only proves that the compiled host, verified profile
picker, acknowledged guest menu and paired-record nonpublication agree
on the route. It does not synthesize a finish, claim a live match result,
test a physical joystick device, or waive independent Windows
controller/stock-rider/fresh-process Records acceptance.

## Source-locked 2P match save retry (stacked follow-up)

The native result observer still owns the **only** initial genuine 2P
settlement. If its paired canonical append fails under temporary OS lease
contention, a process-local pending result may retry at most five more
times, 30 actual host gameplay frames apart, using the existing writer
and exact originally selected P1/P2 catalog entries. It does not duplicate
or synthesize the controller trace or accept anonymous stock 2P.

Every retry requires **all** of the same live conditions: original stock
two-player root handoff, original result menu `0xF9`, no new race,
the current game's independently sampled SRAM result words equal to the
original observed riders/times/outcome, and identical still-confirmed
Modern profile IDs and racer identities. On any departure, mismatch,
Restart, timeout or exhaustion, the pending result is discarded without
writing a match or awarding a win. Failure/success is logged as
`UR_BALDOSA_NATIVE_MATCH SAVE_PENDING / SAVE_RETRY / SAVE_ABANDONED`.
No 2P save badge is claimed until a separate explicit UI acceptance.

## 2P player-visible Records save acknowledgement

The already-shipping native one-player result save strip is reused on the
**original stock 2P result surface** (0xF9), without adding a separate
renderer or modifying guest memory. A true canonical run+sidecar append
causes `RECORD SAVED`. A transient denied pair append with a valid pending
source-bound retry shows `RECORD SAVE PENDING`, and a missing profile,
wrong original rider, exhausted retry or other refusal shows
`RECORD NOT SAVED`. These labels describe storage acknowledgement,
**not** medals, lap times, rankings or release acceptance.

The strip is cleared on any source menu change, restarted race, failed
root handoff, new setup or return to the Modern root. A retried 2P match
cannot display success unless the paired writer acknowledges its commit.
