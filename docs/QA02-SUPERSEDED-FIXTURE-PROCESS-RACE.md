# QA-02: Two active fixture attempts, one durable checkpoint

Status: proposed native two-process adversarial acceptance, not a Windows
packaged game-UI witness or full race-preserving concurrency design.

## Why this test exists

A per-file CAS for the active tournament is not a long-lived lease on a
fixture. Two separate game windows can restore the same unfinished event.
The production arming path writes pending.urlaunch with a persistent
per-path OS mutex, but that mutex protects each write, not an entire
guest race. A later window can legitimately supersede an earlier
window's pending attempt. The earlier game may still finish a valid
stock 2P race and persist a checksum-bound run/match pair.

Before #1042, the earlier window could claim the immutable fixture
receipt using only its stale in-memory token. #1042 added exact disk
checkpoint validation and locked receipt admission. This harness
tests that behavior using **two simultaneously alive OS processes**, not
only an in-memory constructor or a source-contract assertion.

## Deterministic process interleaving

- Seed a real three-entrant tournament with its archive and global active
  pointer but no results. Old game A restores it, arms capture token A,
  publishes a valid stock-origin 2P record pair and waits.
- While A remains alive with its original launch state, game B starts in
  another executable process, restores the still-unplayed event, arms
  token B and publishes a *different* valid checksum-bound race pair.
  Its new durable pending checkpoint supersedes A.
- A resumes and attempts actual coordinator fixture commit. It must
  return EvidenceRejected, preserving its complete run and match but
  awarding no tournament credit. B then commits its own valid attempt.
- A newly launched verifier reconstructs **exactly one three-point win**
  from the single immutable fixture receipt, with two complete ordinary
  Records pairs, no resurrected pending guest race and no second fixture
  credit.

A filesystem barrier deliberately forces this challenging ordering,
rather than hoping the scheduler randomly reproduces it. Both contenders
use production C++ session, launch, record and receipt stores; no mocked
persistence or file copy is involved.

## Limitation and user-experience gap

This establishes a narrower safety property: a superseded window cannot
invent standings or overwrite the winner's receipt. It does not preserve
the older player's in-flight tournament attempt. The two game processes
are harness executables invoking the product's storage path, not two
actual Windows game windows with a live SDL/guest race. Two contenders
publishing *the same* pending token concurrently and physical power
interruption are separate scenarios.

The remaining design question is how an explicitly abandoned or dead
pending attempt is reclaimed without allowing an unrelated live window
to steal ownership. That requires a crash-safe lease or explicit
recovery/takeover contract, not simply changing last-writer-wins to
create-only (which would strand legitimate restarts). QA-02 stays P0
with J-07/J-08 packaged Windows L4 unverified.


## Proposed live-lease correction (2026-10-09, pending CI)

The original interleaving above remains a genuine reproducible
pre-lease counterexample and a reason #1042's fail-closed receipt fencing
was necessary. The live-lease candidate changes its *correct expected
outcome*: game B attempts a new arm while A still owns a nonblocking OS
fixture handle, receives Busy, and **never overwrites A's pending token**.
A then commits the original real saved pair. After A releases ownership,
B's stale in-memory roster/receipt snapshot is rejected instead of
rearming a fixture already credited by A.

A separate child exits abruptly while holding the live handle and leaving
a valid saved pair and pending checkpoint. A new process can explicitly
acquire the OS-released handle, retry with a new token and credit only its
own genuine saved result, preserving the dead owner's ordinary Records.

This new oracle supersedes the earlier expected A=EvidenceRejected,
B=Committed outcome *when both writers are cooperating new builds*.
The lower-level #1042 exact durable-token check remains essential against
older or noncooperating writers, corruption, and commit races. No packaged
Windows L4 evidence has been established.
