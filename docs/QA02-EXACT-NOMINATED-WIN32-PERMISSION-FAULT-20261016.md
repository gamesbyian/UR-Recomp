# QA-02: actual nominated Windows permission-fault source bytes

**2026-10-16 | Independent Windows release QA | bounded OS fault verified, overall P0 still open.** This is a negative-versus-positive discriminator on the **same immutable original nominated Windows executable**. It does not certify crash-recovery transactions or award any release gate.

## Immutable target and real Actions evidence

- Original merged-`main` source `11501a15dea38fa912335cfc63103ce3a7208001`, original ROM-free ZIP SHA256 `5605aaf2ab1773b35385601564ee320ef065ce9bde091117b1e8e5a4661ed1f7`, executed Windows x64 EXE SHA256 `0701f72481531ad4f2803caadc62bbb072f292abef69f039edda004b01c18ea9`.
- Same independently verified, preserved owner package from run [38828519791](https://github.com/gamesbyian/UR-Recomp/actions/runs/38828519791), original artifact 12016101293, was extracted and run both times. The source-compiled profile-fixture EXE is a **separately identified disposable fixture**, not a changed game candidate. USA reference ROM verified as SHA256 `859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478`.
- First Windows [run 38855216544](https://github.com/gamesbyian/UR-Recomp/actions/runs/38855216544), head `809901004b7a2d2d9d7173d652a3d34c6e565e04`, original retained 11-member artifact **12026798427**, SHA256 `6f24999b02db0cb27fb06056ff417e037abec7f063844057eda6247bdac77749`. CRC verified, full original raw and typed files independently rehashed and decoded.
- Second Windows [run 38856087185](https://github.com/gamesbyian/UR-Recomp/actions/runs/38856087185), QA head `80de6a93fcddd23a4664250cde1b56c6c957a951`, original retained 12-member artifact **12027625875**, SHA256 `9782cd4133e45e196dff2b94eb5106f9f2c262b7343bcf5b921f1827031fc2a8`. All ZIP CRCs verified. Exact file lengths, SHA256, code paths and exclusion flags are in [machine evidence](../analysis/evidence/qa02-original-win32-readonly-and-acl-denial-20261016.json). Disposable raw saves remain in Actions artifacts, not in the repository.

## Experiment A: Windows FILE_ATTRIBUTE_READONLY was an ineffective fault

The original Windows runner verified the named raw `save.srm` had the actual read-only file attribute, then ran the original SDL guest to frame **1952** and Quit. Contrary to the test's expectation, the original writer **successfully persisted** its change: process exit 0, `CHECKPOINT ... status=committed`, raw 8,192 bytes old SHA256 `bd9571f8...` to new SHA256 `2f3009bb...` (28 distinct changed bytes), typed `UR-HOST-PROFILE/5` generation **1 → 2**. Independent hex decoding proves both old and new typed `stock_sram` exactly equal their corresponding complete raw SRAM images. The selector, catalog and unearned run/match/ghost sidecars remained unchanged/absent.

**Disposition:** the file's `+R` attribute did not deny this writer's operation. The **test assumption** was false; source saved consistently. This is **not a data-loss bug, storage error witness, or permission-failure acceptance**. Preserve the negative result so the same incorrect injection is not repeated.

## Experiment B: genuine Win32 ACL denial preserves incumbent data

In a fresh, authentic full-length typed/raw named-profile root, the QA driver obtained the real Windows process SID and applied `icacls` deny ACEs for write/add/attribute/delete rights (`WD,AD,WEA,WA,DE,DC`) on that disposable profile directory and children. The **OS actually refused** a separate file creation inside the protected directory. This is a genuine Windows permission failure, not an exception simulated by the serializer.

The same unchanged original Windows EXE booted the valid named profile, entered the real existing 2P guest, reached SDL Pause/Quit at **frame 1952**, and attempted the original native save boundary. Source emitted:
- `UR_BALDOSA_NATIVE_PROFILE REJECTED reason=save_profile_lock_unavailable`
- `UR_BALDOSA_NATIVE_PROFILE native_save_preflight_failed`

Thus failure occurred at **profile-lock preflight**, **before actual raw publication**. The Windows native process returned **0** despite the stderr diagnostic. Four complete files are independently confirmed **byte-identical before/after**: raw 8,192 bytes SHA256 `bd9571f85e1b7ddfcf2b6913d5f3556c27ecadf65d353afbac29876e7d111c10`, typed 16,525 bytes generation 1 SHA256 `1f98e49d51691816a9cd544c6fe71a5f74c3447933a7db6a8cf4e659921775b0`, selector SHA256 `eb0d0bd6c37dfa57766faff9e70f57d1730cabca36426d2863553256bbe87956`, catalog SHA256 `75c0dcef43c3209a4f8793eae5ca035a535348412d3b8b807797fe7f176b1476`. There were **zero** unearned run/match/ghost artifacts.

After the QA driver removed the deny ACE, a **different real Windows game process** launched from the same user root, logged correct named `BOOT_SRAM bytes=8192`, exited zero after six genuine guest frames, and reported `CHECKPOINT ... status=unchanged`. All four SHA256 remained the same. This demonstrates **incumbent preservation and playable cold-start recovery after correcting this one ACL failure**. It does not show the UI communicated the original save failure; raw process exit code was still 0.

## Release and corrective ownership

The repaired-permission success is a **bounded J-08 preflight subset** only. It does not reach a mid-write interruption, actual disk full, source P0 post-`RtlWriteSram` / pre-typed divergence, or torn NTFS/power loss. It does not verify external taskkill, two simultaneous Windows games, duplicate earned fixture/receipt logic, original/native parity, physical controllers/audio/4K, or human-comprehensible error presentation.

Modern/persistence owner should inspect whether `save_profile_lock_unavailable` is surfaced to a real user and whether exit-zero on failed save is a misleading success. Require an actionable, user-visible failure without discarding older valid bytes. Independently retain the existing post-raw/pre-typed **P0 #1214** recovery request, with both old/new raw bytes and consent-safe policy. **No QA-owned Modern transaction edits or alternate runtime.**

QA-02 ledger stays `in_progress`, witness list empty. **0/12 accepted release gates**, **0/45** accepted original/native complete USA events, no physical hardware approval, release decision `not_assessed`; original nominated candidate unchanged.

Three-project reuse preflight: existing UR exact-owner ZIP verifier, unchanged native SDL/guest route, Baldosa original SRAM write authority and Modern typed-source fixture, Malmazuke references only. No second framework, new owner ZIP or ongoing fault factory.
