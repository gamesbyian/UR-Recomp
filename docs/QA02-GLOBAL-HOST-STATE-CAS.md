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

## Active racer switching: framework SRAM second phase (2026-10-09)

The profile selector previously committed the *global* active racer state,
switched to the target profile save root and restored its SRAM bytes to live
memory, but ignored the result of the framework `save.srm` writer. Thus it
reported `UR_PROFILE_SELECT APPLIED` even when the selected racer's new SRAM
was not written, leaving the just-published global pointer inconsistent with
the framework artifact. It also checked the SRAM pointer/size only after
publishing the global selector.

The activation path now verifies live SRAM preconditions before the global
commit, retains the previous global product state and exact 8192-byte live
SRAM, and checks the second-phase framework write. If the target state
fails to restore or the SRAM write fails, it compensates by calling the
production global CAS writer with the now-published target as its expected
baseline and the old product as the replacement. Only a successful exact
compensation switches the in-process root back and re-writes the old live
SRAM. If a second process has changed the global selector meanwhile,
the rollback fails closed and reports
`UR_PROFILE_SELECT ROLLBACK_CONFLICT_OR_IO` rather than destroying its
selection. The old SRAM rewrite may also fail; that outcome is independently
diagnosed and never reported as successful switching.

The real native host-state process fixture now exercises authorized
exact-state rollback and stale rollback refusal following an intervening
selection by another process; the source contract binds that to the
production active-profile path. This does not remove a crash window between
successful global selection and framework SRAM publication. Recovery after
abrupt termination remains unproven on a packaged Windows candidate and
QA-02 stays P0.
