# QA-02: Win32 file-only ACLs are not valid native SRAM failure injections

**October 16, 2026 | Independent negative evidence, no release gate | Closed/unmerged [#1693](https://github.com/gamesbyian/UR-Recomp/pull/1693).**

## Why this experiment mattered

Merged [#1691](https://github.com/gamesbyian/UR-Recomp/pull/1691) already demonstrated an original-Windows `save_profile_lock_unavailable` *preflight* refusal, four byte-identical old save files, and successful cold-start after correcting the original directory-wide ACL. That is not a failed `RtlWriteSram` call; it is an earlier safe refusal. Independent QA attempted to isolate actual native raw-file publication failure **without altering Modern/Baldosa implementation**.

The game remained the **original candidate** (source `11501a15dea38fa912335cfc63103ce3a7208001`, retained ROM-free ZIP SHA256 `5605aaf2ab1773b35385601564ee320ef065ce9bde091117b1e8e5a4661ed1f7`, Windows EXE SHA256 `0701f72481531ad4f2803caadc62bbb072f292abef69f039edda004b01c18ea9`). It came from the original Actions run `38828519791`/artifact `12016101293`. A separate source-compiled test fixture created the disposable valid named profile; it was not a new game candidate. Tested only with a genuine original-USA ROM, never bundled into a public artifact.

## Actual Windows experiment A: deny direct writes to the existing SRAM

Run [38861260577](https://github.com/gamesbyian/UR-Recomp/actions/runs/38861260577), head `01f71c86846f1e1a735148516b3c18e936203a62`. Independently downloaded source artifact **12029890032**, outer ZIP SHA256 **`7d4a57d913b75d6f3a72ee194b8a651010f6c3fe9b6b008d2352fb9e65ea2547`**. All **11** archive members passed CRC validation. The exact byte comparisons and source-linked identity are retained in [machine evidence](../analysis/evidence/qa02-original-win32-raw-file-acl-negative-20261016.json).

An actual `icacls /deny *SID:(WD)` targeted the **existing raw 8192-byte SRAM file**. The current Windows process independently observed that `r+b` opening that specific file was permission-denied, while the profile parent remained writable. Nevertheless the **unchanged original Windows game executed**, reached real live-guest Pause/Quit at frame **1952**, returned process code **0** and emitted `CHECKPOINT profile=native-ci-rider status=committed`. Raw SRAM advanced by **28 genuine guest-changed bytes** from SHA256 `bd9571f85e1b7ddfcf2b6913d5f3556c27ecadf65d353afbac29876e7d111c10` to `2f3009bb2436e3862e045df7f12da4d37845b83ada491cbc80cbef3a098f80d8`.

The full typed `UR-HOST-PROFILE/5` changed generation **1→2**, new SHA256 `5b8960309ff9e34761a467072690e587790710b2686c557f6b4cb794cc9886e8`. **Independent decoding**, not just producer receipt, proved that each full 8192-byte embedded `stock_sram` exactly equals the corresponding original raw before/after. The selector/catalog were unchanged; no unearned `.urrun`, `.urmatch`, `.urghost` appeared.

**Disposition:** The original writer persisted a consistent raw/typed pair despite direct file write access being denied. This does **not** show the writer disregards a failed write; it shows the fault injection did not block actual publication. It is compatible with replacement-style storage semantics, but this experiment alone does not determine the exact filesystem system calls. There was **no native save failure to test**, and no data corruption.

## Actual Windows experiment B: deny file write and deletion, prove replacement

The second exact-head run [38862014937](https://github.com/gamesbyian/UR-Recomp/actions/runs/38862014937) executed a stronger OS prerequisite probe, with `icacls /deny *SID:(WD,DE)` **on a separate disposable target**, while leaving its parent directory writable. The probe attempted a same-directory `os.replace(staging, target)` under the actual Windows security principal. The replacement **succeeded** despite the target's file-only write/delete denies. Thus the intended destination-publication denial was **not established**.

The verifier deliberately raised `OS replacement denial ineffective: destination is still replaceable` **before launching the game**, and the Windows job failed. No saved-game before/after artifact was produced from this second probe; it was never a native save execution. The failure itself is auditable in the Windows job log at that run and exact head `d0973f2e93cf4f445cfd676c42d80166158605e8`. Do not invent a game execution, mutation, or pass based on this job.

The first focused unit run contained an independent QA mock error: a global `Path.open` mock also denied the initial expected read. The retrieved error log disclosed it. The later revision restricted the mock to `r+b`, added the disposable replacement guard, and the full focused tooling suite was green in run [38862014948](https://github.com/gamesbyian/UR-Recomp/actions/runs/38862014948). That green fixture oracle cannot turn an **ineffective real Windows ACL** into a verified native write failure.

## Decision for next owner / independent verifier

**Close [#1693](https://github.com/gamesbyian/UR-Recomp/pull/1693), unmerged.** Do not land a branch-scoped experiment that currently fails its own Windows OS fault prerequisite. Retain the actual working preflight proof from merged #1691 as a separate bounded J-08 subset.

A future true native failure would need a *source-pinned, verified* OS publication denial triggered **after** successful game profile-lock preflight yet **before** native raw replacement, with an independent before/after raw+typed+selector/catalog audit and clean cold reentry. Whether a test-only synchronization seam is worthwhile should be decided with the Modern/persistence owner, not implemented by QA inside product code. Another file-only permission variation without verifying the actual Windows publication operation is unlikely to add value.

The already verified [P0 #1214](https://github.com/gamesbyian/UR-Recomp/issues/1214), **successful raw write followed by abrupt `_Exit(86)` before typed publication and unplayable divergent cold reentry**, is a separate unrepaired product blocker. That defect and the Modern-owner need for explicit consent-safe recovery remain higher priority than speculative ACL experiments. A safe preflight refusal and an ineffective file ACL are not transaction recovery.

**No release admission**: QA-02 remains `in_progress`; QA-12 remains `unverified`; zero accepted gates and zero accepted full original/native USA events, no physical controllers/audio/4K, no exact hardware or power interruption, no completed 2P same-fixture conflict acceptance. Candidate identity and release decision remain unchanged. These are negative research receipts, not pass witnesses.

Three-project preflight: reuse existing UR exact nominated Windows candidate verifier, source-owned Baldosa original save/SDL Pause/Quit, and Malmazuke reference only. No second emulator, independent product writer or new Windows candidate.
