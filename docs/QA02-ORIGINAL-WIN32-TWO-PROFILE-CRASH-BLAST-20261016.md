# QA-02: original nominated Windows crash also blocks canonical access to a healthy other racer

**October 16, 2026 | P0 #1214 independent negative | No release gate or product change**

## Question and source authority

The earlier independent original Win32 [raw/typed crash witness](QA02-EXACT-NOMINATED-WIN32-CRASH-BYTE-WITNESS-20261016.md) proved a genuine game at paused original guest frame 1952 can complete the real `RtlWriteSram`, die with `_Exit(86)` before typed checkpoint, and refuse its next launch because its selected named raw SRAM disagrees with the typed baseline. That established a blocked racer B, but not whether a separately registered *healthy* racer A could still be selected.

Source review identified an important limitation in `native/product/baldosa_native_existing_profile_next_boot.hpp`: the canonical `select_baldosa_existing_profile_for_next_boot` acquires shared selector/catalog/profile locks, then requires full typed/raw SRAM agreement for **each catalog entry** before permitting even a switch *away* from the broken selected entry. That policy is conservative about authority, but could strand otherwise intact profiles until a recovery path has resolved the currently selected mismatch.

## Exact original Windows execution and independent evidence

Source-pinned genuine original Windows [Actions run 38872238234](https://github.com/gamesbyian/UR-Recomp/actions/runs/38872238234), QA trial [PR #1700](https://github.com/gamesbyian/UR-Recomp/pull/1700) tested the **unchanged first nominated Windows PE** SHA256 `0701f72481531ad4f2803caadc62bbb072f292abef69f039edda004b01c18ea9`, extracted by existing source-bound verifier from immutable original ROM-free ZIP SHA256 `5605aaf2ab1773b35385601564ee320ef065ce9bde091117b1e8e5a4661ed1f7`, source `11501a15dea38fa912335cfc63103ce3a7208001`, old owner artifact `12016101293`. Source-verified private USA ROM SHA256 `859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478`, never committed with evidence.

The specific native Windows second-racer crash/selection probe and archive upload steps **passed as a *negative bug reproducer***. QA independently downloaded retained 33-member artifact **12034140741**, full ZIP SHA256 **`c61aaa3466a4faf75191b1c4ca84c27b9063fa08a08c272e5e428af8c7efaf6d`**, size **19,798 B**. Every CRC passed. QA rehashed complete saved files at **four stages**, decoded both real typed profile's entire 8,192-byte `stock_sram` values, checked all producer manifests against bytes, and read independent game/codec/switch logs.

The machine evidence is `analysis/evidence/qa02-original-two-profile-crash-blast-20261016.json`. Source records are **disposable Windows Actions artifacts**, not player data or committed ROM/profile bytes. The source-only test fixture is the genuine Modern codec/selector writer SHA256 `606464f330babe21aeb55668c55b3fa2d808b79a91adefd4b82be251077b7a20`, not an invented profile format or a substitute game executable.

## Actual observed timeline

1. In one disposable Modern user root, the existing real storage fixture registered **A = `native-ci-rider`** and **B = `native-ci-second`**, each with a distinct 8,192-byte raw SRAM and fully matching generation-1 typed snapshot. The *actual canonical selector* successfully switched **B → A → B** while both were still healthy. This healthy control was **enforced by source return codes/stdout predicates during the Windows run**, but its stdout was not independently retained in the uploaded archive, a deliberate evidence boundary.
2. The **actual nominated Windows game**, now selected B, reached real original two-player guest frame **1952**, showed scripted SDL Pause/Quit, saved B's **real** source guest raw 8,192-byte SRAM, and abruptly terminated with source `QA_CRASH_AFTER_RAW_WRITE exit=86 typed_checkpoint=0`, before publishing B's typed checkpoint. This is a process-local abrupt `_Exit(86)`, **not** external Taskkill, NTFS tear, or power cut.
3. B raw changed **28** actual bytes, from SHA256 `c7db68306d7c44253263b1957cfae71f89888e813f140c0c91f32a802063fef9` to `2f3009bb2436e3862e045df7f12da4d37845b83ada491cbc80cbef3a098f80d8`. B typed remained generation 1 SHA256 `3cf17ae30fb6be8bca5301f76331929ea610bddd792153805cc01ffc79e66213`, so its embedded SRAM **did not** match the actual new raw save. Neither selector nor catalog changed.
4. **Healthy A survived intact.** Its raw 8,192-byte file SHA256 `bd9571f85e1b7ddfcf2b6913d5f3556c27ecadf65d353afbac29876e7d111c10` and typed generation-1 file SHA256 `1f98e49d51691816a9cd544c6fe71a5f74c3447933a7db6a8cf4e659921775b0` remained *byte-identical*, with full typed/raw SRAM equality. Source codec verification passed A, **exit 0**. Source codec verification of B correctly failed, **exit 46**.
5. A fresh **same original nominated Win32 game**, still selected B, returned **exit 7** *before guest execution* with `UR-BALDOSA-SAVE-MISMATCH`. All six canonical files were unchanged by this failure.
6. Invoking the **same canonical existing-profile selector** to change **B → healthy A** then returned **exit 85**, after having passed that very request in the healthy pre-crash control. Again **all six full canonical files were byte-for-byte unchanged**, preserving the intact A and both old/new B save evidence. The selector correctly refused rather than corrupting state, but this leaves A inaccessible *through this source-backed canonical path* until B's mismatch is safely handled.

## Independent four-stage full-file SHA256 receipt

| File | Before B crash | After B crash, cold B rejection and B→A rejection |
| --- | --- | --- |
| A raw SRAM, 8192 B | `bd9571f8…` | **Identical**, typed matches all bytes |
| A typed profile, 16525 B | `1f98e49d…` | **Identical**, generation 1 |
| B raw SRAM, 8192 B | `c7db6830…` | `2f3009bb…` (**28 changed bytes**) |
| B typed profile, 16528 B | `3cf17ae3…` | **Identical**, generation 1; now mismatched |
| Global selector, 242 B | `9db71c0e…` | **Identical**, B remains selected |
| Profile catalog, 70 B | `7793f9de…` | **Identical**, two registered racers |

The table abbreviates hashes for legibility. Every **full** hash, process identity, file length, archive digest and source-log digest is present in the machine evidence. Four-stage all-byte comparisons, not producer report claims, prove that neither failed operation altered either racer or the selector/catalog. The original crash source log shows the actual guest and _Exit marker. The original cold boot log shows an error before guest. The B→A native fixture log shows **exit 85**; the fixture maps failed selection to that code without explaining the enum cause, while source policy independently identifies the full-roster SRAM-integrity prerequisite.

## Defect classification and acceptance contract

This expands the practical blast radius of **existing Modern persistence P0 [#1214](https://github.com/gamesbyian/UR-Recomp/issues/1214)**. It is not a second implementation-owner assignment and not proof every conceivable UI/manual recovery path is unavailable. The verified failure is the existing **canonical next-boot profile selection path**, with one independently healthy alternative inaccessible through it.

Modern ownership should provide **both**: (a) a consent-respecting recover-old/recover-new B policy, preserving the last-good typed generation and the new raw source bytes without silent overwrites; and (b) a safe escape from an unrecoverable currently selected B to an independently validated healthy A, without bypassing the existing selector/catalog locks, treating unknown raw as authentic results or modifying B's old/new evidence. On a repaired source-pinned original Windows candidate, repeat healthy B→A→B baseline; actual B post-raw/pre-typed crash; A raw/typed independent exact equality; explicit safe A selection and cold reentry; later deliberate recovery of B; repeated fresh processes; no duplicate `.urrun`/`.urmatch`/`.urghost`, PB, fixture awards, or unrelated profile mutations. Preserve denial behavior when the target A itself is corrupt.

**Release status is unchanged:** QA-02 `in_progress`, QA-12 `unverified`, **zero** fully accepted release witnesses, **0/45** accepted complete original/native USA events, first nominated candidate `not_assessed`. No physical gamepad, display/4K, audible SFX, power loss, human UI or complete game result was accepted here. The QA harness may be reused for negative/regression checking, but a green negative-reproducer workflow is **not** a passing release gate.

Three-project reuse check: UR retained exact-original owner package verifier, existing Baldosa original Windows guest and genuine Pause/Quit/crash seam, existing canonical Modern fixture for A/B and switch; Malmazuke only advisory. No new emulator, game product code, package candidate, persistent format or separate storage backend.
