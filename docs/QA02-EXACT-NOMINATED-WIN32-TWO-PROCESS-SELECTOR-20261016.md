# QA-02: nominated original Windows game vs independent Modern selector writer

**2026-10-16 | Bounded stale-selection concurrency pass | Original nominated candidate unchanged | No complete release-gate credit.**

## Exact candidate and original hosted evidence

The test executed the immutable first nominated Windows source `11501a15dea38fa912335cfc63103ce3a7208001`, original ROM-free ZIP SHA256 `5605aaf2ab1773b35385601564ee320ef065ce9bde091117b1e8e5a4661ed1f7`, and **actual original game executable** SHA256 `0701f72481531ad4f2803caadc62bbb072f292abef69f039edda004b01c18ea9`, recovered from the preserved nominated owner run `38828519791` artifact `12016101293`. The correct private source USA ROM SHA256 `859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478` was used on the runner, not included in any published game package or repository evidence.

One original Windows Actions [run 38867691561](https://github.com/gamesbyian/UR-Recomp/actions/runs/38867691561), exact tested QA-head `4d3058cd4b7a42cba8940860e0fa732e2e2c75f4`, completed the **specific source-exact selector-conflict test** successfully. The native Modern writer was the separately compiled, existing QA fixture SHA256 `4ee20da18d3ae7d374ba9d50de9c8ae429aa7fc65b40c398cf44c08ffeaecd82`, using the real canonical Modern CAS storage codecs, not a new game or a second synthetic serializer.

The actual archived 29-member Windows evidence artifact **12031753976**, whole ZIP SHA256 `c5b0e0722e21e3b879624282989e6ab29347170b6caee7799e8461fc63fc0e6f` (18,804 bytes), expires **2026-10-30 07:36:25 UTC**. Independent QA downloaded it, tested all ZIP CRCs, rehashed every one of the four-stage canonical file snapshots against the included receipts, compared complete bytes independently, decoded **both** actual `UR-HOST-PROFILE/5` generation-1 8192-byte `stock_sram` fields, and verified source game logs. The machine-authored independent audit is [here](../analysis/evidence/qa02-exact-nominated-win32-selector-conflict-20261016.json). Disposable named profile data stays only in short-lived Actions evidence, never in git.

## Actual three-process timeline

1. **Windows game process A:** Genuine unmodified nominated executable loads named first profile `native-ci-rider`, boots its authentic original guest SRAM, progresses through the existing stock two-player route, opens the actual SDL Modern Pause/Quit presentation at guest frame **1952**, and remains paused until a file handoff gate. The controller inputs are scripted SDL and **not physical pads**.
2. **Independent Windows writer process B:** The pre-existing native QA fixture starts as a separate process against the **same** Modern user root, legitimately registers `native-ci-second` with its own source-defined rider/8192-byte raw SRAM and typed state, and commits a canonical selector change from first to second with catalog append. It is **not a second running game**, a made-up fixture result, or an alternate store format. Before handing control back, QA records full current bytes of all six canonical files.
3. **Stale game A resumes Quit:** A detects `UR_BALDOSA_NATIVE_PROFILE PREFLIGHT_REJECTED status=3` and `UR_BALDOSA_NATIVE_PROFILE native_save_preflight_failed`. It does **not** call the original raw SRAM writer or publish a typed checkpoint. Independent QA compared *all complete bytes*: after B, the first raw and typed profile, second raw and typed profile, global selector and catalog are **byte-for-byte identical after A's attempted stale Quit**. A cannot steal B's selector or overwrite first-profile SRAM with speculative guest progress.
4. **Fresh Windows game process C:** A separate launch of the **same original game executable** against the same user root activates `native-ci-second`, reads its authentic full 8192-byte SRAM with source first-frame FNV32 `8d56d025`, runs six genuine guest frames and exits **0**, reporting `CHECKPOINT profile=native-ci-second status=unchanged`. All six canonical files again remain byte-identical. There are **zero** unearned `.urrun`, `.urmatch` or `.urghost` artifacts.

## Independent saved-byte ledger

| Canonical file | Before independent writer B | After B, after stale A and after cold B |
| --- | --- | --- |
| Global selector | 241 B, SHA256 `eb0d0bd6...` | 242 B, `9db71c0e...` |
| Profile catalog | 44 B, `75c0dcef...` | 70 B, `7793f9de...` |
| First raw SRAM | 8,192 B, `bd9571f8...` | **identical**, no guest overwrite |
| First typed profile | 16,525 B, `1f98e49d...` | **identical**, full typed SRAM matches first raw |
| Second raw SRAM | absent | 8,192 B, `c7db6830...` |
| Second typed profile | absent | 16,528 B, `3cf17ae3...`, full typed SRAM matches second raw |

The two separately named raw images differ at exactly byte offset **8191** (first 0x00, second 0x5a), from the already-established QA fixture's source-defined isolation discriminator, not synthetic race progress. Both original raw images exactly match their respective typed full SRAM images. The before/after files were independently hashed; their full SHA256 strings, process SHA identities, receipts and source-log hashes are in the machine evidence. This avoids relying on the producer's booleans as proof.

## Decision and limits

**Result:** an independently rehashed, original nominated Win32 **pre-write stale-selector conflict prevention** and genuine cold reentry of the newly selected profile. It removes an exact-owner evidence gap for this **bounded** J-02/J-08 concurrency slice. Neither a static lock unit test nor a relabelled PR-head game executable was substituted.

**This is not:** two simultaneously running Windows **game** instances competing for earned fixture receipts (full J-07), a real pad-controller conflict, human-visible save-error comprehension, a complete ordinary-USA original/native event, physical/audio/display qualification, Windows full disk, forced external process death, actual power-loss storage durability, or an accepted whole QA-02/12 release gate. Process B was a **fixture** calling real Modern stores. Source shutdown refusal happened **before** raw publication.

Most importantly the separately reproduced [Modern-owner P0 #1214](https://github.com/gamesbyian/UR-Recomp/issues/1214) is **not fixed**: when actual original `RtlWriteSram` *has already succeeded* and a real process dies before typed publication, the raw/typed generations diverge and the next game refuses the otherwise valid named racer. Selection locks correctly prevent a stale **pre-write** transaction but do not provide multi-file crash atomicity or a consent-safe recovery choice. The owner must implement and independently test that repair, including second-profile isolation and new/old generations, duplicate-earned-artifact exclusion and cold restarts.

The source-pinned release ledger retains **QA-02 `in_progress`**, **QA-12 `unverified`**, **0/12 complete accepted release gates**, **0/45 complete original/native USA events**, no physical QA, and original candidate decision `not_assessed`.

Three-project reuse preflight: existing UR exact nominated ZIP verifier and native two-process conflict observer, pinned Baldosa actual guest/Pause + canonical Modern writer, Malmazuke advisory only. No new emulator, store, framework, candidate or synthetic result.
