# Baldosa native SRAM crash boundary: exact reproduction contract

Status (2026-10-10): **candidate diagnostic**, not an accepted fix, clean
recovery, fully atomic save transaction or beta-readiness credit. Issue
[#1214](https://github.com/gamesbyian/UR-Recomp/issues/1214) owns the
unresolved data-integrity boundary. The normal two-process selector/profile
conflict is already guarded by merged #1216.

## Source-owned boundary

The original pinned Baldosa host executes these operations in sequence,
inside the established selector/catalog/profile OS locks:

1. `ur_baldosa_modern_profile_before_native_save()` validates the catalog,
   named profile, selected root and unchanged raw/typed 8 KiB baseline.
2. The **original** `RtlWriteSram()` writes to the selected native root.
3. `ur_baldosa_modern_profile_finish_native_save(native_saved)` reconciles
   those new guest bytes into the typed Modern profile under the same locks.

Locks prevent cooperating second processes from interfering during step 2.
They **do not** turn steps 2 and 3 into a power-loss-atomic multi-file commit.
Process death between steps 2 and 3 may leave the newer raw save and the
last committed typed snapshot inconsistent. The existing launch policy
rejects such a mismatch; it does not silently promote the raw bytes or
repair the typed profile.

## Executable witness

`tools/baldosa_modern_profile_activation_spike.py` inserts an opt-in
`UR_BALDOSA_QA_CRASH_AFTER_NATIVE_SRAM_WRITE=1` fault only after a
successful actual `RtlWriteSram()`, before the typed checkpoint. It flushes
the diagnostic and terminates with code 86, bypassing normal teardown.

`tools/baldosa_windows_native_pause_route.py` proves the boundary with the
**real pinned Windows x64 executable**, existing Modern profile codec fixture
and **actual two-player SDL pause/Quit** at game frame 1952. The test uses a
fresh, isolated named profile and its previous actual 8 KiB source save; it
never touches a user data root. Acceptance requires:

- The guest entered a real active race, was paused and Quit through the
  original SDL event loop, and reached the unique post-raw/pre-typed marker.
- Original raw `save.srm` remains 8 KiB but **differs** from its previously
  verified typed baseline. A zero-delta save is inconclusive and must fail.
- Previously committed `host-profile.txt`, catalog and selector are
  byte-for-byte unchanged. No typed checkpoint or run completion is claimed.
- A **fresh native process**, with fault injection disabled, refuses the
  divergent selected profile with exit 7 **before** its first guest frame,
  and leaves both raw and typed files unchanged.
- No anonymous default save, `.urrun`, fake victory, tournament credit
  or silent repair appears.

Real run logs and file evidence remain in the owning Windows CI execution
workspace. Synthetic unit tests defend the callback order; they do not
satisfy the real two-process gate.

## Required follow-up after reproduction

Design and test explicit, consent-respecting recovery of a mismatched
selected profile without silently replacing the newer raw data or losing the
last-good typed state. Candidate policies must preserve both byte-for-byte
snapshots for forensic inspection and apply normal selector/catalog/profile
authority. Test failure during staging, native write, typed publication,
repeated fresh launch and two independent profiles. A persisted
transaction/checkpoint journal or an atomic shared publication design needs
its own code review, durability proof and rollback behavior.

**No repair policy is introduced by the fault-injection PR.**
