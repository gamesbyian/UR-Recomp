# QA-02: Global host settings and active-profile selector CAS

Status: proposed storage and production integration; **not** full cross-artifact
atomicity, packaged Windows acceptance or release readiness.

## Confirmed lost-update path

The global host-state file stores both the active racer/profile pointer and
the Modern settings. It previously used a private staged replacement but no
cross-process expected-state comparison. Two game processes could load
profile A, one select profile B, and the other adjust a visual setting from its
stale in-memory host state. The settings writer's full-file replacement
silently selected profile A again. Conversely a profile switch could erase a
newer setting. Per-profile/profile-catalog CAS cannot protect this independent
global authority.

## Correction

`save_host_product_state_file_if_current(path, expected_current, next)`
owns the existing persistent per-path OS-handle `.urmutex` lock across the
canonical read, complete typed state comparison and staged publication.
A missing file is only authorized by create-only `expected_current = nullopt`.
Malformed, oversized, unsupported or inaccessible existing state is not
silently reset. A stale complete state returns `Conflict`, not success.

The production host retains `g_product_state_disk_baseline` separately from
the mutable live global state. This matters because the regional-presentation
path mutates the live global state before save. Only an actual successful
publication advances the expected-disk baseline. Every normal production
host-state save now uses conditional publication. On a conflict, the attempted
setting/profile change fails without modifying the newer file and emits
`UR_HOST_STATE SAVE_CONFLICT`.

## Acceptance and residual risks

The process probe uses separate child processes that read the same existing
global host state, block at a synchronization barrier, race two different
active-profile selections, then verifies exactly one succeeds and the other
returns `Conflict`. Additional coverage rejects create-only replacement of
a valid or corrupt incumbent. Existing private staging and data-sync tests
continue to apply.

Conflicting live sessions do not yet merge independently changed settings
or automatically reload the new disk baseline. Callers may need to restart
to adopt the other process's selection; regional live-presentation state may
already have changed in memory before a failed write. This is a fail-closed
integrity policy, not a complete multi-instance UI reconciliation contract.
The `save.srm`/host-profile/global-selector group still has power-loss
windows, and no exact candidate Windows two-process J-02/J-08 fault witness
is recorded. QA-02 stays P0 in progress.
