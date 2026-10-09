# QA-02: Exact on-disk fixture launch authorization

Status: native coordinator correction, not packaged Windows or power-loss
acceptance. C14/C15 use coordinator restoration from disk in the native
lifecycle fixture, not a full independent-process restart.

## Source-confirmed stale-attempt credit flaw

Fixture commit previously checked attempt identity against only the calling
process's memory, then admitted its saved run/match pair via the receipt
store. Another game instance could replace the same event's pending.urlaunch
with a newer attempt while the first instance was racing. The old memory
token would still pass validation and could claim irreversible fixture
credit although the durable launch authorization had changed.

The commit path now takes the exact pending.urlaunch.urmutex OS-handle lock
used by launch publication and retirement. Under that lock it reloads and
validates the on-disk pending fixture against the current unplayed schedule,
compares its complete canonical bytes to the live process's expected pending
attempt, and only then claims the immutable fixture receipt. Failed reads
return storage failure; absent, changed, invalid or superseded attempts
reject credit. The lock spans the receipt commit, so a cooperating writer
cannot change launch ownership between checking and awarding points.

After the durable receipt claims the fixture, the lock is released and
the existing exact-attempt retirement reacquires it. If a competing new
attempt appears, retirement refuses to unlink another process's checkpoint.
Receipt authority persists even if retirement fails.

## Focused regression and crash cuts

The native lifecycle fixture simulates a second window superseding an
already-armed durable checkpoint with a different valid attempt token while
the first has finished a real stored run/match pair. The old process must
not credit the fixture. Disk restoration must show zero credited results.
Restoring the authorized original pending allows the correct commit.

C14: publish real run and bound match with no fixture receipt, then restore
the coordinator; the match must not award points and the pending race must
not resume. C15: publish the production receipt but deliberately stop
before retiring the still-existing pending checkpoint; restore twice,
each time crediting exactly one fixture without reviving the pending
attempt, then retire the expected old checkpoint without losing points.

These native file-boundary tests do not yet kill and restart a separate
executable. They are not packaged Windows L4 witnesses or physical
power-interruption tests.

## Open boundary

A second live game can still use stale in-memory tournament standings to
arm a new pending checkpoint. The former owner now fails closed rather
than accepting an out-of-date credit, but its actual race work may be
stranded. Full cross-process fixture arming, explicit safe recovery of
abandoned pending attempts, and a group transaction across run, match,
receipt and pending remain unimplemented. A saved run without the exact
fixture receipt must never be promoted into a win. QA-02 stays P0.
