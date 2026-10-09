# QA-02: Crash-released fixture ownership lease, proposed contract

Status: **implementation candidate** in this PR, pending exact-head native CI; **not** a packaged Windows release witness.
Owner: QA-02 persistence. Keep distinct from frontend, guest gameplay
and tournament rules. Current safety baseline: exact on-disk attempt
fence at receipt commit (#1042), with two-process adversarial coverage
in #1050. That fence prevents false awards but can still strand honest
in-flight work when a second game instance overwrites pending.urlaunch.

## Goal

Two actual game processes using the same user-data directory should not
be able to supersede each other's **live** tournament fixture attempts.
The system must also recover from an owner that died without cleanup,
without trusting a timestamp, PID file, uncommitted record, or arbitrary
artifact as proof of a win.

## Proposed protocol

1. Add a **separate, per-tournament, OS-handle-owned live-lease file**
   alongside pending.urlaunch, distinct from the existing short-lived
   pending.urlaunch.urmutex publication lock. Its fixed pathname belongs
   to the instance, not an attempt token or per-process random filename.
2. Acquire the live lease **nonblocking**, before writing a pending
   checkpoint or entering the guest race. Windows: LockFileEx with
   LOCKFILE_FAIL_IMMEDIATELY; POSIX: flock LOCK_EX|LOCK_NB. A healthy
   competing process receives Busy quickly, with no on-disk mutation.
   Do **not** spin, wait indefinitely, scavenge another process's lock,
   or delete a lock file because a PID/timestamp looks old.
3. Hold the live lease for the entire guest attempt, across result
   capture, saved run/match publication, receipt admission and exact
   pending retirement. Its OS handle must live in the game host state,
   not be reconstructed from a future program restart.
4. To change pending state, **while holding live ownership** acquire
   the existing short per-path publication mutex, read the canonical
   pending token, then save or retire through the current exact store
   contract. Global lock order: live lease, then pending file mutex.
   Never acquire in reverse order; duplicate handles within the same
   process must not be mistaken for recursive ownership.
5. On an ordinary confirmed commit, the receipt remains authoritative,
   and failure to retire pending is a diagnostic, not a rollback of
   points. Release the live lease on completion/cancel/clean exit. On
   abrupt process death Windows/POSIX releases the lock automatically.
6. On next launch, never auto-resume the previous pending guest race.
   If its live lease is free, offer explicit Retry/Discard to the
   player, preserving the old checkpoint for diagnostic inventory
   until the player chooses. Only the explicit new attempt may replace
   stale pending, with a fresh 32-hex token. A matching saved pair
   without a receipt remains ordinary Records evidence, never an award.
7. If the live-lease lock cannot be created/opened, fail closed without
   launching guest gameplay. Do not report a 'busy' conflict as an
   invalid roster or save corruption; distinguish Busy, IoError and
   stale pending awaiting explicit decision.

## Adversarial acceptance requirements

- Run **two packaged Windows game windows** simultaneously, same ZIP/hash,
  same user root and selected event. A arms a fixture and begins racing;
  B requests another arm and receives immediate Busy with no checkpoint
  overwrite. A finishes and gets exactly one receipt and three points.
- Kill A after arming; B subsequently acquires the **OS-released** live
  lease but cannot infer a win or resume A's guest attempt. B explicitly
  retries with a new token, and only B's actual saved result may credit.
- Inject kill after saved pair, after receipt and before pending retirement.
  Reopened B must reconstruct **only exact receipts**, never PB/points
  from an orphan sidecar or stale checkpoint. Test disk full at both
  lease acquisition and checkpoint write; do not clobber other files.
- Include host conflict paths on Windows Unicode/non-ASCII user roots,
  cancellation, exit-to-frontend and process shutdown, and two
  distinct fixture indices in one instance. Ensure the separate lease
  has no effect on Authentic execution or single-process input timing.
- Exercise exact nonblocking semantics with two independent processes
  at L2 first, then pin an immutable Windows ZIP and L4 witness.

## Why simply making pending create-only is wrong

The current restore path deliberately ignores a previous process's
pending attempt. Making all future launch publication create-only would
strand a profile after an ordinary power failure or OS-kill, because
its orphan checkpoint would remain present forever. Conversely always
replacing pending permits the stolen-attempt scenario from #1050.
A live OS handle plus explicit rearm semantics separates a *still-running*
owner from a *dead but durably pending* attempt, without relying on
unverifiable heartbeat age.

The coordinator and OS-lock primitive now implement the core live lease
as an unmerged candidate. Production arm acquires it nonblocking and
retains its handle in the coordinator through commit or cancellation.
Arm also rechecks the current active archive and receipt-derived fixture
completion to refuse stale in-memory rearm after another window finishes.
Native simultaneous processes and crash-released retry exercise its
fail-fast Busy and OS death semantics. This is still not a shipped menu
or permission to downgrade QA-02 P0 before L4.
