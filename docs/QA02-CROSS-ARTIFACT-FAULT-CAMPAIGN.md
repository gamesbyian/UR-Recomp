# QA-02: Cross-artifact fault campaign and recovery oracle

Status: **unexecuted acceptance plan**, 2026-10-09. It does not upgrade
the QA-02 release gate or certify a packaged Windows candidate. Gate:
`RELEASE-QUALITY-LEDGER.json` (P0, L4); journeys: `QA-PLAYER-JOURNEYS.md`
J-02, J-07, J-08. This document separates proven store behaviour from
remaining multi-file fault hypotheses.

## Authorities, not just files

| Authority | Files / boundary | Current protective evidence | Remaining cross-artifact risk |
| --- | --- | --- | --- |
| Named racer | `profiles-v1.txt` and racer `host-profile.txt` | Typed bounded catalog and profile CAS (#996, #1003), conditional cleanup | Death after profile commit but before catalog membership: exact pristine-orphan explicit Create recovery (#1027/#1030), but progressed or unknown-data orphans remain preserved and unsupported |
| Global selection | `host-state-v1.txt` and selected racer root | Typed global state CAS (#1017), explicit per-profile isolation | Profile pointer may commit before new `save.srm`; profile switch compensation (#1019) handles reported failure, not sudden death |
| Progression | Selected racer `host-profile.txt` snapshot and framework `save.srm` | Staged file flush and conditional mirror rollback (#1005, #1016) | Power loss between files; damaged/torn framework write; no shared recovery journal |
| Multiplayer evidence | Paired `.urrun`, `.urmatch`, optional `.urghost` | No-replace pair publication, bounded rollback and fresh-process fixture (#993) | Crash after sidecar first claim; orphan match must remain invisible to run/PB admission; optional ghost fallback and group commit remain unverified |
| Tournament ownership | Archive `session.urtournament`, `active.urtournament` | Archive before active; exact-state active pointer CAS (#1009) | Death leaves valid inactive archive, and concurrent full coordinator creation needs process-level arbitration; no silent promotion |
| Fixture award | `pending.urlaunch`, run/match evidence, immutable fixture receipt | Pending written before guest route; receipt drives verified standings; retired pending not promoted on restart (#982/#984/#985) | Death between run publish and fixture receipt, or receipt and checkpoint retirement; never award twice |

## Fault-cut protocol

For each row below, run a **fresh process** at the exact write transition,
retain a bytewise inventory of both old and new artifacts, and restart
without changing the root. Repeat with a second process racing the same
logical owner. Separate these failure classes: graceful API failure, injected
process kill, OS hard termination, disk-full/read-only root, interrupted
upgrade, and physical power interruption. A process kill is **not** a
power-loss durability witness. Use the exact portable ZIP and its SHA-256 on
Windows for L4 and include an independent host/VM or physical machine.

| Cut | Intervention | Required oracle |
| --- | --- | --- |
| C01 | After new profile snapshot, before roster publication | No silent catalog row invention; old profiles safe; orphan preserved and explicitly recoverable only by verified policy |
| C02 | Two create/rename writers from identical roster | One CAS winner; losing writer cannot remove the other's newer profile; next explicit attempt can use fresh roster |
| C03 | After roster publication, before active profile/global selector save | Valid new racer remains discoverable; old active racer unaffected |
| C04 | After global active pointer publication, before target framework SRAM write | Restart never silently loads one racer's progression under another identity; explicit recovery or fail-closed diagnostic |
| C05 | Framework `save.srm` write fails after profile mirror commit | Mirror rollback only if exact intermediate version still current; competing profile writer preserved |
| C06 | Target SRAM write fails during profile selection | No `APPLIED` success; global selector rolled back only if no intervening winner; old SRAM restore diagnosed |
| C07 | Two processes change global selection and different settings | Exact-state winner, stale full-file writer loses instead of reverting selection or settings |
| C08 | Shutdown during profile reset or tour restart | No unreported new/old mix; existing valid SRAM and typed profile evidence retained; no false progression |
| C09 | After `.urmatch` public sidecar claim, before matching `.urrun` final-name claim (the production no-replace order) | Incomplete pair never appears as a completed match or PB; previous valid records retained |
| C10 | Pair published, before optional ghost | Match and run still valid; missing ghost follows documented fallback and never contaminates PB |
| C11 | Tournament instance archived, before active pointer CAS | Existing active event remains authoritative; inert archive cannot be silently auto-activated |
| C12 | Active tournament CAS races a different new event | Exactly one active winner; no overwritten valid pointer; abandoned archive discoverable for diagnosis |
| C13 | `pending.urlaunch` published, before guest result | Restart cannot infer victory from pending checkpoint; attempt identity fenced |
| C14 | Run/match result published, before immutable fixture receipt | No credit without validated receipt; replay/retry cannot duplicate run or fixture award |
| C15 | Receipt committed, before pending checkpoint retirement | Exactly one fixture credit on restore; stale pending not resurrected as live capture |
| C16 | Disk full on staged file flush, close, rename or post-rename directory sync | Precommit failure leaves old file; committed-uncertain state never disguised as uncommitted for unsafe compensation |
| C17 | Upgrade to newer schema or rollback to prior build with older root | Unsupported/corrupt future metadata read-only; no silent overwrite by defaults; versioned backup and explicit recovery |

## Evidence classification and stop conditions

**Observed store behaviour:** exact profile/catalog/global/active CAS, private
staging and prepublication data flush have focused native regressions.
Selected multi-process and crash-before-publish tests exercise real store
APIs. These do **not** make C01–C17 pass for the complete application.

**Known source-level defects corrected and merged:** #1016 compensates
a failed profile snapshot's second-phase framework SRAM write; #1017 fences
global active racer and settings to exact disk baseline; #1018 permits
explicit retry of lock-only failed-registration residue; #1019 compensates
failed target SRAM on profile switch; #1027/#1030 support explicit narrow
pristine-orphan claim across pre-catalog and post-rename staging-cleanup
process deaths; #1033/#1035 request OS data flush before publishing run,
match and ghost bytes; #1038/#1041 use create-only immutable archive
publication on create and legacy restore. #1042 verifies an exact still-live
durable pending launch under mutex through receipt admission, with native
in-process reconstruction at C14/C15. #1044 proposes fail-closed
downgrade handling for a valid future ghost schema, subject to CI and merge.
None of these equals a verified power-loss group transaction.

**Remaining risk hypotheses and unexecuted acceptance:** abrupt death
between a global profile selector and target framework SRAM (C04);
progressed/foreign orphan recovery beyond exact pristine initial snapshots;
simultaneous live fixture ownership; independent executable death between
saved run/match and receipt (C14) or between receipt and pending retirement
(C15); group metadata durability after canonical publication; and
future-schema downgrade/upgrade on a pinned portable ZIP (C17). Native
store/process fixtures and coordinator reloads establish narrower properties.
Do not count them as executed packaged Windows L4 evidence.

Pass criteria for *every* cut: no destruction of an unrelated valid
artifact; no incorrect racer attribution, false lap/award, duplicate fixture
or PB; bounded, deterministic fresh-process recovery or explicit rejection;
preserved original bytes for user-facing salvage; reproducible diagnostics;
and a preserved second-instance winner. Keep failures, unimplemented
cases, and cases merely passing process fixtures in distinct ledger fields.
A gate cannot advance to accepted until L4 evidence is attached to the
specific shipped artifact, not merely a green Actions workflow.


## Focused independent-process evidence, merged green 2026-10-09

The previously accepted store tests and in-process coordinator reconstructors
did not exhaust C09/C12/C14/C15. New native harnesses keep the **actual**
production C++ codec, store and coordinator code, start independent executable
processes, and retain one user-data directory throughout each trial.

- [#1046](https://github.com/gamesbyian/UR-Recomp/pull/1046) injects
  std::_Exit immediately after the real multiplayer sidecar no-replace
  claim (C09), after a complete saved pair but before the fixture
  receipt (C14), and after an authoritative receipt but before checkpoint
  retirement (C15). Reopened child processes verify no phantom PB/fixture
  credit, exactly one award after a receipt, and preservation of originals.
- [#1048](https://github.com/gamesbyian/UR-Recomp/pull/1048) races
  two full coordinator creations against the same root (C12),
  independently verifying one Created / one AlreadyExists and a
  single canonical active owner with no fake completed event.

Both PRs have passed exact-head project tooling and native heavy-router
checks and merged, establishing bounded L2 OS-process evidence for their
explicit fault cuts. They do not certify the pinned portable Windows
game or physical storage power-off L4 witness. A process
can die after a successful OS data flush while directory metadata still
has uncertain durability, and the framework SRAM/profile group
remains uncommitted as one transaction.
