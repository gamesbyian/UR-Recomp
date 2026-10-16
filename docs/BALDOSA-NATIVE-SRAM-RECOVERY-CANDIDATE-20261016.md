# Native Windows SRAM crash-recovery candidate (Modern product owner)

Status: **source candidate / not independent QA accepted / do not merge yet**.
Owning issue: [#1214](https://github.com/gamesbyian/UR-Recomp/issues/1214).
This describes the new transaction protocol, not a power-loss-atomicity claim.

## Actual native crash boundary

Original Baldosa `ur_baldosa_modern_profile_before_native_save` held
selector → catalog → typed profile OS locks, checked full typed/raw equality,
and let the actual `RtlWriteSram` mutate the canonical 8192-byte
`saves/profile-<id>/save.srm`. A successful native write preceded typed
`host-profile.txt` CAS. Accepted exact Windows guest evidence after
`_Exit(86)` demonstrates changed raw guest bytes, old typed bytes, and a
cold restart refusing the profile with exit 7. A second Windows reproducer
also demonstrates that the ordinary two-profile selector refuses an intact
alternate because it validates the broken *source* raw/typed pair.

Cross-file OS locks prevent cooperating writer races. They cannot prevent
a process abort or power failure between distinct file publications.

## Candidate protocol

1. Under the **same canonical three OS locks** and successful expected
   selector/catalog/typed CAS preflight, first compare the existing raw
   bytes to the committed typed snapshot. When the live guest bytes differ,
   construct the exact next typed state using
   `capture_stock_sram_for_profile`, and synchronously stage a **bounded,
   canonical, validated intent** in that profile directory. No intent is
   needed if the SRAM is byte-for-byte unchanged. An already-present
   pending intent always blocks further writes.
2. Only after successful journal durability request may the **original
   guest-owned** `RtlWriteSram` execute, unchanged. Successful native save
   and typed CAS still use the same checkpoint API. On successful finalization,
   remove only the matching intent; a cleanup error is not treated as a
   successful clean shutdown.
3. On fresh named-profile startup, before the first guest frame, reacquire
   selector → catalog → typed OS locks. Reject noncanonical, oversized,
   symlinked, malformed or unrelated intents, unauthorized roster identities,
   missing/corrupt typed states, and unknown raw bytes. Replay exactly:
   `old raw + old typed` means the native write never completed, so discard
   only the intent. `new raw + old typed` means the authorized source bytes
   landed, so archive exact old/new snapshots before typed CAS. `new raw +
   new typed` means the typed step completed, so archive and remove intent
   without publishing another generation. Every other combination refuses
   mutation. Repeated cold boots must be stable.
4. Archive filenames include the exact intent content digest, not just
generations: a later legitimate new attempt after a discarded or explicitly
rolled-back intent may reuse the same old/new generation numbers and must not
overwrite or be blocked by the prior receipt. The raw write interruption
with a valid pending intent can be explicitly rolled back to the committed
typed snapshot only after archiving the partial raw bytes *and* that intent;
automatic replay still refuses unknown or partial raw SRAM.

Archive files contain a read-only exact old/new typed receipt under the
   existing profile directory and are **never a load source**. Neither
   journal nor archive introduces a second save, progression oracle, or
   Records namespace. The active save remains the canonical `save.srm` plus
   `host-profile.txt`.
5. For an **unjournaled historical mismatch** (including the independently
   reproduced old `_Exit(86)`), remain fail-closed: no authorization of
   raw promotion can be inferred retroactively. The separate explicit
   `select_baldosa_healthy_profile_from_damaged_for_next_boot` operation
   can switch to a fully validated registered alternate while preserving
   the damaged current racer's bytes. It holds the same selector/catalog
   and sorted pair of typed locks and changes **only** the canonical next-boot
   selector. The canonical catalog may contain **three or more** profiles:
   only the explicitly selected source and destination typed/raw files are
   examined and locked (in sorted OS-path order), while the entire catalog
   is canonical-decoded and held under its original exclusive lock. Broken
   unrelated profiles never strand a healthy destination. No implicit
   profile choice or live guest hot-swap. The same pinned Windows executable exposes an explicit one-shot recovery
   command before its first guest frame, and the existing double-click CMD
   launcher prompts R/T/S/Q only after a native exit 7. Controller-accessible
   in-game recovery is still unavailable because the normal rejected guest
   never starts. Physical UI acceptance remains independent QA work.

## Historical, unjournaled save choices (explicit only)

A previously crashed Windows save can have the legitimate guest-written raw
bytes but no prewrite intent (because the installed executable predates this
protocol). Startup **continues to refuse** this unexplained mismatch.
`native/product/baldosa_native_manual_sram_recovery.hpp` provides exactly
two opt-in choices under existing selector/catalog/profile OS locks:

- **Keep guest-written raw:** Only for a complete 8192-byte raw image with a
  valid original save signature. Archive the exact old typed state and entire
  raw image first, then use canonical `capture_stock_sram_for_profile` and
  typed CAS. The original raw file is never overwritten by this choice.
- **Restore last committed typed:** Archive exact original raw bytes, even if
  short, and the full committed typed profile first, then atomically replace
  only canonical raw `save.srm` with its last committed 8192 bytes.

An existing valid pending intent additionally authorizes **only** explicit
restoration of the exact still-committed typed profile, never promotion of
partially written guest bytes. Both the entire interrupted raw and the
exact pending intent are archived before raw replacement; then the pending
intent can be retired under its original three OS locks.

Both require the expected currently selected catalogued racer, matching
racer identity and a separately explicit choice. Keep-raw requires NO pending
current-format intent. Restore-committed admits either no intent or a valid
intent naming the exact still-committed typed snapshot; other intents fail
closed. Never infer choice from an interrupted event,
auto-launch, profile name, or the presence of an old raw image. Archive files
are read-only receipts, not another recovery store, and remain in the
original profile directory. Both choices use stable archive identifiers,
reject symlink redirects and fail closed on lock, staging or CAS errors.

Recovery is available via the existing executable's
`ur_baldosa_modern_run_recovery_command()` pre-guest hook with one explicit
environment action (`raw`, `typed` or `healthy`, plus an exact target ID
for the last choice). The packaged `run-baldosa-modern.cmd` clears all
inherited recovery action variables, then after a genuine exit 7 and only
for an **interactive, no-argument launch** offers R/T/S/Q. S shows the canonical catalog (profile ID is the first
column) so the user need not guess a different registered racer. R or T or S
invokes that SAME game binary once, expects exit 89 before guest simulation,
clears recovery variables, and only then restarts. Q returns exit 7 without
any file writes. Scripted/CI launch remains non-interactive and fail closed.
QA fixture `--recover-keep-raw`, `--recover-keep-typed` and
`--recover-select-healthy` remain available for isolated tests but are not
distributed. This is a native Windows launcher recovery affordance, not an
in-game/controller modal or an independent QA acceptance claim.

## Fault-state matrix and preservation contract

| Exact state under locks at cold boot | Decision | User-data effect |
|---|---|---|
| No intent; raw equals typed | Ordinary boot | None |
| No intent; raw differs from typed | Automatic boot refuses; explicit archived raw/typed choice only | Preserve both until player decision |
| Valid intent; old raw + old typed | Retire abandoned intent | Keep old committed pair |
| Valid intent; new raw + old typed | Archive before/after, CAS next typed, retire intent | Preserve source-written 8 KiB raw and old/new typed receipt |
| Valid intent; new raw + new typed | Archive and retire intent | No duplicate generation |
| Valid intent; missing/short/foreign raw | Automatic replay refuses; explicit archived rollback to matching committed typed only | Keep full interrupted raw and intent receipts before repair |
| Malformed intent or missing/corrupt typed | Refuse | No reset/guess |
| Stale selector/catalog/profile or lock unavailable | Refuse | No write |
| Healthy alternate explicitly chosen while current is damaged | Validate destination fully, publish selector only | Damaged raw/typed/roster unchanged |
| Missing, corrupt, redirected or unauthorised alternate | Refuse | No selector or save change |
| Crash before intent visible | Previous raw/typed pair remains | Orphan staging not authoritative |
| Crash after intent visible but before original write | Old/old retry | No progress fabricated |
| Crash after native write but before typed | New/old retry | One source-bound typed checkpoint |
| Crash after typed but before intent retire | New/new retry | No duplicate checkpoint |

**Important limitations.** This is a process-crash-oriented protocol with
durability requests to the host OS. Device power-loss, directory sync on
Windows, and adversarial out-of-band simultaneous file mutation remain
outside proven atomicity. An intent is evidence of what the *authenticated
native process* intended to write, not proof of an earned course/result.
It grants zero `.urrun`, `.urghost` or `.urmatch` authority and must not
update `RELEASE-QUALITY-LEDGER.json`.

## Tests, gaps, and handoff

Source-focused native C++ test:
`tests/native/baldosa_native_existing_profile_next_boot_test.cpp`
(compiled by `tests/unit/test_baldosa_native_existing_profile_next_boot_cpp.py`)
covers old/old, new/old, new/new, repeated cold boot, foreign raw rejection,
healthy alternate, missing typed, explicit keep-raw and keep-typed with
unchanged archived source bytes, short raw, malformed intent, and wrong
profile authority. Product-owned Windows route
`tools/baldosa_windows_native_pause_route.py` runs genuine frame-1952
post-raw fault twice in disposable roots: the legacy unjournaled
`_Exit(86)` must reject cold boot before explicit archived raw promotion;
the journaled `_Exit(86)` must cold-replay exact SRAM on a second genuine
guest process. The producer also invokes the same source-built Windows game
binary's explicit `raw` rescue, verifies invalid actions cause no write,
and verifies an independently healthy second registered racer can be
explicitly selected despite corrupt raw bytes in the first one, with a fresh
native boot of the second SRAM and the first raw/typed pair untouched. These are **candidate-producer** evidence, not independent
QA or physical power-loss proof. The old
crash-negative witness is immutable historical evidence; it must not be
reinterpreted as success after this change.

**Independent QA handoff:** Pin new main/source SHA, actual packaged PE/ZIP
hash, frame-1952 paused original guest proof, a successful real
`RtlWriteSram` before `_Exit(86)`, old/new raw+typed+selector+catalog
SHA-256, new intent receipt, cold-boot source SRAM, no duplicate records,
second healthy profile (including 3+ profiles and an unrelated damaged
third) and separate damaged-source selector witness. The newer producer also
packages a bounded flat `qa02-journaled-snapshot.zip` with the exact
intent-aware hash receipt expected by the separately QA-owned read-only
verifier; product CI does not confer independent QA admission.
Independently exercise real Win32 ACL/partial-I/O cuts, restart repetition,
and old-version stores before closing #1214 or advancing the release ledger.
The nominated prior Windows ZIP remains immutable and unmodified.

Related issue triage: #1125's typed checkpoint and #983's
canonical path lock are already integrated in current source; #1532's
`file_exists` staging-collision retry is also integrated. Their older open
issue statuses should be reconciled with source-bound tests separately, not
treated as blockers requiring competing rewrites in this PR.
