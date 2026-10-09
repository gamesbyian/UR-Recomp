# QA-02: Exact-snapshot compare-and-swap for host profiles

Status: implementation candidate. Profile/SRAM **cross-artifact** atomicity and packaged Windows verification remain open.

## Defect

The profile codec's `autosave_generation` increments only when a stock SRAM
snapshot is captured. In contrast, ghost selection and Recent Course re-save
the whole in-memory profile at an unchanged generation. Two open game processes
can each hold an old `HostProfileState` and replace the other's newer SRAM
with that old mirror, or silently undo a metadata change. A generation-only
guard is insufficient: two separately generated saves based on the same old
generation can produce the same new generation with different SRAM bytes.

Existing explicit rollback after a failed second-phase framework SRAM write
must also be permitted to restore an *older* generation. Rejecting every
decreasing generation would disable that recovery path.

## Store contract

`save_host_profile_state_file_if_current(mode, path, expected_current, next)`
takes a persistent OS-handle `.urmutex` lock on the canonical path, then
reads the current canonical disk profile, compares the complete typed
`HostProfileState` (identity, SRAM bytes, generation, continuation, ghost
preference and Recent Course), and performs the existing private same-directory
stage-and-replace **while still holding the lock**.

- `expected_current = nullopt` is create-only; it rejects an incumbent.
- A mismatch, unavailable/malformed incumbent or intervening mutation fails
  closed. An I/O error is never reinterpreted as an absent profile.
- The exact previous state authorizes any next valid generation, including
  rollback after an SRAM/roster persistence failure, but only if no independent
  writer changed the intermediate state.
- Normal production host saves use CAS; creating a profile uses create-only;
  explicit rename/reset/tour-restart rollback uses the exact intermediate
  state as its expectation.
- The original `save_host_profile_state_file` remains a low-level unconditional
  writer for migration/tests. It **does not acquire this lock**. All cooperating
  production profile mutations must use the conditional API.

## Verification

The production storage process-probe now forks two separate child processes.
Both decode the same existing profile before a disk-barrier releases them.
Exactly one CAS publication must succeed, the loser must get `Conflict`,
and fresh loading must recover the winning complete SRAM mirror. The test
also covers create-only collision, authorized exact rollback to an earlier
generation, and rejection of rollback after a third successful intervening
writer. All use the production store and OS lock, with no mock mutex.

## Explicit non-claims

This is a per-profile serialization and expected-state transaction only.
It does **not** make `save.srm` and `host-profile.txt` atomic as a pair.
There are still crash windows between host-state commit and the framework SRAM
write, and the reset/tour restart compensating rollback itself can fail on
disk-full or power loss. Cross-profile catalog create/rename, concurrent active
tournament sessions, launch checkpoints and fixture receipts have separate
authority rules. An OS-file lock is reliable for cooperating local writers
on supported Windows/POSIX filesystems, but is not an NFS lease or an fsync/
directory-sync durability guarantee.

QA-02 remains P0 until the exact packaged candidate completes Windows
two-game J-02/J-07/J-08, disk-full/power-failure, interrupted upgrade and
cross-artifact restore acceptance.

## Catalog/roster lost-update extension

The production profile catalog used a safe staged replacement but retained a
blind, last-writer-wins complete-roster write. During concurrent creation or
rename, two instances could each load the same old `profiles-v1.txt`, then
publish different lists. Whichever wrote last would discard the other's racer.
An intact `host-profile.txt` would no longer have an authorizing catalog row.

`save_host_profile_catalog_file_if_current(path, expected, next)` now acquires
the same OS-handle-owned per-path lock discipline as profile CAS, loads the
bounded previous roster from disk, compares the **whole typed roster** and
publishes only if it is unchanged. A missing catalog is the canonical empty
roster. Malformed/unavailable catalog data is never silently defaulted during
mutation. Profile create and rename supply their exact pre-edit roster. If
publication conflicts, creation abandons its newly written profile and rename
uses profile CAS to compensate the staged identity change, provided nobody
else has changed that intermediate profile.

A two-process fixture independently loads the same one-entry catalog, then
attempts two different additions after a barrier: exactly one succeeds and the
other reports conflict; a fresh process verifies the original row and exactly
one new row. A source contract guards against unprotected production catalog
mutations. This does not provide atomicity across the profile file and catalog
file, nor recovery from a hard kill between the two commits. Cross-artifact
transaction and orphan-profile restoration remain QA-02 P0 follow-ups.
