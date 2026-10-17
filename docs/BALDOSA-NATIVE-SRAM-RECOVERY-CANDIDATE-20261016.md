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


## Real Windows typed-publication/finalization cut (product producer)

The native Windows source producer also uses QA-only
`UR_BALDOSA_QA_CRASH_AFTER_TYPED_PROFILE_COMMIT=1` to stop the **actual**
guest process with `_Exit(87)` after original `RtlWriteSram` and
canonical typed CAS return `Committed`, but before the durable write-ahead
intent is retired. This must preserve exact new raw + new typed and the intact
pending old/new intent. Two fresh source guest processes must then archive
that intent **once**, retire it, load the same 8192 guest bytes and leave the
typed checkpoint generation and selector/catalog unchanged. The bounded
`native_typed_before_intent_recovery/fault-bytes/` artifact includes all
four before/crash/after canonical files, original intent/receipt and SHA
manifest. This test is a genuine Win32 *process abort* at a source-controlled
cut. It does not constitute an OS power-loss or partial-disk-write claim.


## Product-only partial raw recovery boundary (not disk-full evidence)

The Win32 original guest `_Exit(86)` case is copied **after the authentic
native raw writer and staged intent are observed**, into a separate disposable
root. The producer then *synthetically* truncates the copied raw SRAM to a
513-byte real-prefix image; it does **not** claim to force a real Windows
partial `RtlWriteSram`, ACL violation or disk-full. A real native Windows
process must refuse this unknown raw state before guest simulation. Its
one-shot explicit `typed` recovery must archive the entire 513-byte raw
prefix and exact pending intent before restoring the previously committed
typed SRAM as the canonical raw file. Two fresh genuine native boots must
preserve that restored image, typed generation, and archives unchanged. The
bounded producer retains a no-personal-data receipt and actual Windows
console logs for independent follow-up. This is product-layer policy testing
only; independent F4 physical I/O denial and durable OS error tests remain
unmet.


## Exact second-cold-boot canonical bytes for QA (product export)

Independent QA correctly noted that earlier positive source artifacts exported
four canonical before/crash/after files, but no independent **post-second-boot**
raw/typed/selector/catalog snapshots. Both genuine Windows recovery producers
now explicitly persist those actual second-process disk bytes in the bounded
source artifact (`*.second-cold.bin`) and SHA256/length receipts. The original
QA-owned strict 18-member flat `qa02-journaled-snapshot.zip` schema remains
unchanged; additional second-boot snapshots are **siblings in the original
Actions fault evidence**, not unreviewed extra members of the QA input.
The F3 typed-publication-cut snapshots likewise export distinct after-first
and after-second bytes. Product production and hash checks are not a
substitute for independent download, rehash, and release acceptance.


## Inspectable partial-raw archive bytes (product evidence, not QA credit)

The copied genuine Windows post-raw fault + **simulated** 513-byte partial
write test now retains 13 bounded CI-owned byte files under
`simulated_partial_raw_explicit_rollback/fault-bytes`. These include the
source-authentic raw 8192 image, synthetic truncated raw prefix, restored
8192 raw and second cold-boot raw, original/restored typed, selector and
roster before/after, exact genuine journal, immutable journal receipt, and
complete archived manual raw/typed snapshot, with a SHA256/length receipt
for each. The producer fails if the partial prefix is absent from the
archive, or if typed, selector, roster and intent diverge. Independent QA
may now recompute those comparisons directly, but this does **not**
establish an actual Win32 partial write, denied OS handle or device power
cut. The old candidate's P0 result remains negative and untouched.


## F5: real original Windows crashed B, intact alternate A

The previous healthy-alternate test used a fixture-changed source save.
The new bounded source producer first registers two distinct, individually
verified Modern racers, explicitly selects B using the actual original
Windows executable, then boots the real selected B SRAM. A source-backed
paused original **B** race at frame 1952 enters the unchanged native
`RtlWriteSram`, actually overwrites the complete B raw SRAM, and is killed
at the historical **unjournaled** `_Exit(86)` point before typed CAS.
A remains byte-exact intact. A new Windows process must refuse damaged B
without any guest frame. The actual original executable must then require
the **explicit** `healthy` action naming A, change only the canonical
selector, and permit **two** fresh source-authentic A boots. All B raw/typed
bytes from the genuine crash remain unchanged throughout. A, B, selector
and roster snapshots are retained in six times four canonical stages
(selected, B crash, after A selection and after second A boot), along with
actual native process logs and SHA-256 receipts. This does NOT replace a
physical packaged no-argument R/T/S/Q operator test or provide release
QA gate credit.


## Three registered profiles: independently corrupt C must not strand A→B

A separate hosted real-Windows product test uses only the canonical
Modern stores to provision distinct A/B/C racer identities and three
different 8192-byte SRAM images. The test deliberately damages the
unrelated **C typed file** and the currently selected **A raw SRAM** in
an isolated test root. The actual native game must first refuse A,
reject any attempt to select damaged C, then accept an **explicit** B
switch under the source/destination path locks despite unrelated C's
absence. Two original Windows cold processes must boot B with no
source/target mutation, no C reconstruction, no invented source result
and unchanged canonical roster. It retains seven canonical files at
four stages plus the archived original C typed file, with exact
SHA-256 receipts. Damage is QA-injected; this test does **not** claim
C was damaged by an original guest save, nor a physically operated
launcher recovery dialog. The distinct F5 B-crash/A rescue test
provides the genuine source-guest crash boundary separately.


## Exact QA-owned journaled reader handoff correction

Independent QA's updated read-only verifier
`tools/check_qa02_win32_fault_snapshots.py` expects a bounded **19-file**
flat F2 journaled ZIP: the 12 canonical before/crash/after files, the
canonical four-label `file-receipt.json`, two source process logs plus
second cold log, the two exact intent snapshots, and a separate
`intent-receipt.json` with the five canonical digest/retirement
assertions. An earlier product draft incorrectly emitted **18 members**
with intent metadata folded into an additional `file-receipt` key; the
independent QA owner correctly rejected that optional flat envelope.
The producer now copies the original already retained `intent-receipt.json`
as its own member, leaves the four-label file receipt unchanged, and
requires exactly 19 deterministic ZIP entries. The owning Windows Actions
run invokes the **QA-owned reader unchanged**, with the actual flat ZIP
SHA-256, to detect future schema drift on each exact source-head test.
This product-side compatibility preflight is NOT QA gate approval. The
separate original full Win32 evidence archive always retained the complete
correct 4+intent receipts.


## F1 before-raw process-death source boundary

The original Windows guest now has another narrowly isolated QA-only
process cut `UR_BALDOSA_QA_CRASH_AFTER_INTENT_BEFORE_RAW=1`: **after**
durable old/new typed write-ahead intent is prepared but **before**
the pinned native `RtlWriteSram` callback. The test guest reaches a
real source-backed frame-1952 shutdown and exits **84** with the
original raw/typed/selector/catalog bytes intact and the prewrite
intent outstanding. A new genuine Windows process must discard the
uncommitted old/old intent without changing typed generation or guest
SRAM; a second process must boot identically with no second replay.
The source-bound artifact retains **17 binary objects**: all four
canonical files at before/crash/first/second-cold plus the actual
durable intent and their SHA256/length receipts, as well as the three
actual Windows process logs. This is a controlled process-death
witness at a known point, not actual lost-power or partial filesystem
write evidence. No release gate credit.


## Two named profiles: original B journaled fault and untouched A

The product-owned Windows F5 route `native_journaled_b_crash_then_a`
now exercises the complementary **journaled** side of the real original B
source fault. Two individually valid canonical riders A/B are registered;
the original native game explicitly selects B, boots B's distinct 8192-byte
stock SRAM, reaches pause frame 1952, writes B raw via the original
`RtlWriteSram`, and is killed with QA-only `_Exit(86)` *before typed
CAS*. Only B raw and B's pending old/new typed intent may differ at crash.
Two genuine fresh B boots must reconcile its typed publication **exactly
once**, archive the original intent byte-for-byte, and preserve every
canonical A byte, global selector and roster. The same original Windows
executable then explicitly selects intact A and must boot A in two more
fresh processes, with all B's recovered raw/typed bytes and immutable
receipt unchanged. CI-owned fault evidence retains **32 exact binary
objects**: six canonical files over five stages plus the two intent
copies, with SHA256/length receipts and every actual Windows process log.
Source guest test, not actual power-cut/OS partial I/O, physical R/T/S/Q,
or independent release QA credit. The preceding unjournaled B→A witness
remains a separate, directly historical-comparable positive subtest.

## F4 actual Windows directory DACL denial before the raw writer

Unlike synthetic 513-byte input corruption, a separate product-only hosted
Windows test uses Windows `whoami /user` to select the **actual runner
security SID**, then `icacls /deny` on a disposable native profile folder
and its files. A fresh exclusive-create write attempt in this very process
**must fail with Win32 PermissionError** before the game starts. The
original named native executable then reaches a genuine frame-1952
paused save attempt while the directory is denied; the prewrite intent
cannot be staged and the raw writer must be refused. The harness
always removes the temporary denial in a `finally` block, retains
the complete canonical raw/typed/selector/roster bytes at before,
denied and second-cold stages (12 exact binaries + SHA receipts), and
requires two source guest cold boots after restoring access. This is
an **actual OS DACL-denied prewrite file operation**, not a denied
post-raw typed publication, disk-full or power-cut witness; it
does not assert a human-visible error dialog or release QA credit.

## Two live original Windows games sharing a named racer (product source route)

The bounded product Win32 producer now reuses the **independent QA's
existing byte-decoder/interleaving utilities without editing its evidence
or candidate identity**. Actual original process A pauses in a source
frame-1952 2P race and remains alive; actual original process B boots
the same named profile and authentically writes changed native SRAM and
typed metadata, while A waits behind the already-existing test-only
pause-menu gate. A's later original guest Quit must refuse a stale raw
write before it occurs. Four actual canonical files are snapshotted at
before A, after B, after A and after cold C, and independently decoded
raw/typed agreement and generation progression are required. C must
reload B's authentic SRAM in a third separate Windows game.

This is source-owned, real **overlapping game-process** coverage but
is not claimed as a simultaneous lock-acquisition collision at the
precise RtlWriteSram seam, NTFS disk-full, actual power loss, or
independent QA gate acceptance.

## Explicit-recovery restart bound

After a genuine startup refusal (exit 7), the no-argument packaged CMD
may offer R/T/S/Q only once. A successful one-shot R, T or S recovery
returns exit 89 before guest execution, clears its inherited action
variables and permits **one** new original Windows guest process. If that
new process also refuses startup, the launcher retains the rejection and
stops with exit 7; it does not re-open R/T/S/Q, repeatedly archive state or
enter an unbounded consent loop. Scripted launches never prompt. A source
unit assertion pins the recovery menu before choice and the retry guard
before a second potential entry. Human-operated package acceptance remains
independent and unverified.

## Real NTFS denial during cold reconciliation of a genuine F2 write

The native Windows product producer now clones the original **actual**
frame-1952 F2 raw-written/pretyped process-abort user root into a second
**disposable** test root, with the original entire raw SRAM, committed
typed sidecar, selector/catalog and pending exact old/new intent
**unchanged**. It applies an actual OS icacls deny to the current
Windows runner SID and confirms a real exclusive-create operation is
rejected by the kernel. A genuine original native cold process must
then reject the pending transaction before any guest frame, preserving
all four canonical files and the exact intent. In finally, the producer
removes the DACL; two subsequent original Win32 cold game processes must
reconcile exactly once, retain the immutable intent receipt, load
source-written 8192 SRAM and leave selector, roster, typed generation
and Records unchanged on repeat.

The source original post-raw write itself did **not** encounter the
OS-denied typed checkpoint. It was an authenticated process-abort F2;
the later OS denial is **real** but deliberately applied to an exact
copy during cold recovery. Consequently this is an actual post-raw-state
OS denied-reconciliation test, **not** an injected failure between the
live native RtlWriteSram and typed CAS, partial OS write, actual full
disk, or device power cut. These positive product-source observations
remain distinct from independent release QA; original 19-member flat
QA02 ZIP contract is completely unchanged.

## Live original Windows typed-publication denial after raw SRAM

**Candidate-bound, no gate credit until this exact head's Windows test passes.**
The original guest reaches an authenticated frame-1952 2P race, commits a
changed complete 8192-byte SRAM image through its actual `RtlWriteSram`,
and parks in a Windows-only QA hook while the original selector, roster and
profile interprocess leases remain acquired. Its exact old/new durable
write-ahead intent already exists and typed metadata is still old.

A separate Windows process first **proves** with disposable sibling files
that a Win32 `CreateFileW` handle allowing shared reads but **not**
`FILE_SHARE_DELETE` causes the actual kernel to reject an atomic
`os.replace` with access-denied or sharing-violation status. The runner
then acquires the same real Windows share-mode handle on the existing
canonical `host-profile.txt`, confirms the old typed bytes are still
readable, and releases the live game's gate. The original unchanged typed
CAS must read/verify its previous snapshot but fail the atomic
`MoveFileExW` replacement, preserving source-new raw bytes, typed-old,
selector, roster and pending intent **byte-for-byte**.

The runner holds the OS handle until the game's typed CAS finishes and
then closes it in a `finally` block. Two subsequent real original-game
cold boots must reconcile **once**, load exactly the original new 8192
guest bytes, preserve an immutable copy of the full previous/next intent,
and never create an earned run, match or ghost from this interrupted race.
Source-owned Windows evidence contains five four-file snapshots and two
exact intent snapshots (22 independently hashable binaries). The 19-member
flat QA02 consumer contract remains completely unchanged.

**Scope:** this is an actual Windows **sharing-denied destination
replacement during live typed publication**, not an ACL claim. Previous
source tests independently cover a real NTFS directory ACL denied
prewrite and denied cold reconciliation. A real disk-capacity exhaustion,
partial guest raw write, physical power cut, human-operated packaged
R/T/S/Q, and independent exact-package QA remain unverified.

## P0 #1751: report failed native save to the actual Windows player

Independent [#1751](https://github.com/gamesbyian/UR-Recomp/issues/1751)
reproduced an authentic frame-1952 original Windows paused Quit whose native
named-profile save was refused before raw publication by real NTFS permissions.
Canonical source SRAM, typed profile, catalog and selector remained unchanged,
but the **game exited 0** and the launcher therefore treated the session
as a clean save. Protecting bytes alone is insufficient when the player is
told nothing about potentially uncommitted progress.

The product-side follow-up replaces both ordinary failed save outcomes in
the existing pinned upstream shutdown wrapper with a **fail-closed exit 8**
and an explicit stderr `UR-BALDOSA-SAVE-FAILED` diagnostic. It preserves
the established start-before-guest refusal **7**, one-shot management
completion **89**, historical source crashes 84/86/87 and healthy ordinary
exit **0**. Both the pre-`RtlWriteSram` refusal and a real postraw typed
checkpoint error must return exit 8; a successful save continues to return
zero. No artificial SRAM writer, second journal authority, guest result,
rollback, or new live-retry semantics are introduced. OS process teardown
releases path locks on failed publication and the existing durable journal
is left for a safe cold start.

The existing packaged `run-baldosa-modern.cmd` now handles **8** separately:
it warns that the session could not finish saving, preserves the entire
user-data folder, keeps the interactive console visible for the player's
acknowledgement, and exits 8. Scripted invocations bypass interactive
holding and still return 8. It must **never** offer R/T/S/Q in this
save-on-quit failure path; those choices belong to a *subsequent*
explicit startup rejection (7), if any. An older/newer writer conflict
does not imply the player should replace a newer healthy save.

This is owning-product candidate implementation, **not validated Windows
source or human UI acceptance** until the new exact-head CI and independent
QA inspection. In particular, QA must re-run the real prewrite ACL denial,
the two concurrent original games A/B/C and the live denied typed-CAS
fault from one pinned Windows PE and extracted CMD package. True partial
disk writes, full-disk, power loss and manual physical controller acceptance
remain outside this evidence.


## #1751 player-authorized next-boot switch: save old rider FIRST

Two real source Win32 campaigns exposed a genuine bug in the first attempted
exit-8 user notification: native X/A selects an existing alternate P1 while
the **old** P1's cartridge is still running, immediately mutating canonical
`host-state-v1.txt`. At Quit, the original guest SRAM may legitimately have
changed during its 900 frames. The old-rider typed CAS must refuse that
already-mutated selector, so an automatic exit 8 is correct but an unfriendly
result of an otherwise legal player action. A second attempt to admit a
byte-identical no-write shutdown was demonstrably insufficient for those
authentic guests; it is not part of this candidate.

The product now uses the **existing selector authority** twice, each under
the original ordered OS selector / catalog / old/new typed locks. On a
verified X/A action, it performs the original complete existing-P1 selector
admission with `validate_only=true` and latches the explicit target **only
in the live process**. It never writes the new selector at that point or
hot-swaps the old guest. The Modern root marks it QUEUED; racing is latched
off. At ordinary Quit, the unmodified original `RtlWriteSram` and Modern
typed checkpoint execute under the original expected active selector and
write-ahead intent. A failed raw or typed write, conflicting external
selector, corrupt context, or missing journal still refuses exit 8 and
**never commits the requested switch**.

Only **after** the old rider's raw/typed checkpoint has fully succeeded,
the intent has been durably retired, and the three OS locks have been
explicitly released in reverse order does the same validated existing-P1
transaction recheck both identities, exact guest/typed/raw source state
and the still-old selector and commit the target for next process. This
avoids lock reentrancy and prevents a racing external writer from silently
authorizing a save. A failed second authorization leaves the completed
old-racer save intact but returns a non-success exit (no false success
or player-data deletion). The new source receipt is
`NEXT_BOOT_COMMITTED ... original_raw_typed_saved=1` and the tests reject
`UR-BALDOSA-SAVE-FAILED` in a normal controller switch.

The tests must demonstrate genuine Mike→Andrew→Mike original-game switches
and P1→P2 with retained earned Records, plus unchanged OS-denied prewrite/
postraw and two independently competing source games A/B/C. This remains
product candidate evidence, not clean-machine physical QA or a completed
release gate. #1214 and #1751 remain open pending source-exact validation.

## #1751 second-phase selector refusal: code 9, not a lost save

A real original guest may durably finish the old rider's `RtlWriteSram`,
typed checkpoint and intent retirement before the pending X/A next-boot
selector can be published. A separate process or Windows OS refusal can
legitimately win or block that SECOND phase. The saved old racer is
**not lost**, so treating that condition as exit 8 / a save-not-completed
message would misinform the player.

The native two-phase save bridge now returns **2** solely after the old
profile's save is durably complete but the independently verified next-boot
selector transaction is refused. The original native shutdown wrapper
translates this into OS **exit 9**, with a unique
`UR-BALDOSA-SWITCH-FAILED: Current racer save completed` source diagnostic.
The original ROMless `run-baldosa-modern.cmd` has a distinct exit-9
warning that explicitly confirms old progress was saved but the requested
next racer was not selected, and holds the double-click console for
acknowledgment; scripted invocations return 9 immediately. Exit 8
continues to mean prewrite or raw→typed save failure and must **never** be
used to describe a fully committed old save. Startup repair remains 7.

The adversarial original Windows test holds the still-running game after
its typed publication + journal retirement, releases its locks, and
invokes a separate **shipping canonical selector transaction** through
the already-compiled native profile fixture, updating Mike→Andrew first.
The original source game then resumes, must return **9**, and may not
overwrite this healthy external selector. Original 8 KiB Mike SRAM must
decode exactly against its typed checkpoint, Andrew raw and catalog
remain unchanged, no pending journal remains, and genuine source
`CHECKPOINT status=committed|unchanged` must precede the post-save
gate and `NEXT_BOOT_COMMIT_FAILED`. The original game and its external
actor are two distinct Win32 processes, not a fabricated result writer. A separate product-only
fault-byte artifact carries **24 actual canonical files**: the old and
alternate racers' raw/typed states, roster and global selector at
pre-save, source-save, external-selector and refused-original phases,
plus SHA-256 receipts. Each stage is source-read-only. An independently
replayed comparison must find the alternate racer and roster unchanged,
only the legitimate old raw/typed update before the actor, and **only**
the selector changed by the external winner; the refused original
may not mutate any file.
All evidence is product side and separate from independent release QA.

This extra negative control is a candidate, **not release acceptance**,
until the exact-commit Windows run and QA independently validate the
result. P0 #1214/#1751, manual human R/T/S/Q, full-disk/power cut and
physical gamepad acceptance remain open.

## Packaged CMD exact-PE fault acceptance (additional product witness)

The owning Windows source producer exercises real controller-originated
Modern **1P Play**, then holds the original guest in a source-authenticated
live race until frame **2200**, where it provokes the same true Win32
postraw typed-publication sharing denial through the extracted ROMless
ZIP's own `run-baldosa-modern.cmd`. The separately green direct original
2P source fault preserves the established frame-1952 witness.
It uses the exact tested PE, a temporary verified original USA ROM, an
original-native source SRAM seed and the production Modern profile fixture
in disposable user data outside the extracted package. The live source guest
must refuse typed CAS and **the actual CMD parent must return exit 8** with
its visible save-failure warning. When Windows sharing restrictions are
released, two further fresh CMD-launched original guest processes must
reconcile the exact new guest SRAM once and prove typed-generation
idempotence. The PE and immutable ROMless ZIP hashes must remain unchanged.
No ROM, private profile or synthetic earned result is packaged.

The separate packaged transcript/fault-byte evidence is retained **outside**
the strict 19-member QA02 ZIP under the additional Windows artifact
baldosa-win32-extracted-cmd-source-evidence. This is CI-scripted CMD
execution, not human R/T/S/Q or physical gamepad acceptance. No release
ledger credit is transferred; it is candidate coverage until the new
exact-head Windows process succeeds and independent QA reviews it.
