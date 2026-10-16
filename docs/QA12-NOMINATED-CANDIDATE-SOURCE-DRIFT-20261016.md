# QA-12: nominated Windows candidate vs current main, complete tracked-source drift audit

**2026-10-16 | Independent release QA | Exact nominated candidate retained, not renominated | No release-gate credit**

## Question and evidence authority

Has integration of independent QA, original/native event evidence and Windows storage-fault research changed the **tracked source and package-assembly inputs** underlying the one nominated Windows x64 candidate, or are the current advances evidence-only?

The authoritative candidate remains first manually nominated `gamesbyian/UR-Recomp@11501a15dea38fa912335cfc63103ce3a7208001`, inner portable ROM-free ZIP SHA256 `5605aaf2ab1773b35385601564ee320ef065ce9bde091117b1e8e5a4661ed1f7`, immutable original actual Windows game EXE SHA256 `0701f72481531ad4f2803caadc62bbb072f292abef69f039edda004b01c18ea9`. The owning source-bound manual Windows playtest and retained owner ZIP are documented in [QA-EXACT-MAIN-WINDOWS-OWNER-CANDIDATE-20261015.md](QA-EXACT-MAIN-WINDOWS-OWNER-CANDIDATE-20261015.md), with actual release state held only by [RELEASE-QUALITY-LEDGER.json](RELEASE-QUALITY-LEDGER.json).

Independent QA queried **the complete recursive Git GitHub Tree API for each of two immutable commits** and compared every tracked blob pathname, blob SHA and file mode, explicitly verifying neither tree was truncated. Compared base candidate `11501a15...` to `main@0eb1cd4b7fbda1ffee5428ffc5ec9169ae248260`. This is an **as-of** observation, not an evergreen assertion about any later branch head or requalification of a rebuilt executable.

The complete reproducible 75-entry old/new Git-blob SHA ledger, including all additions and modified test inputs, is [analysis/evidence/qa12-candidate-main-tracked-tree-delta-20261016.json](../analysis/evidence/qa12-candidate-main-tracked-tree-delta-20261016.json). It is independently derived from the two source commits, not PR prose or generator summaries.

## Exact result

| Source-tree category | Changed file paths |
| --- | ---: |
| Native game/runtime, graphics/media, imported original/upstream sources and vendored third-party trees | **0** |
| Explicitly checked original Windows manual-playtest and candidate assembler/binder/PE audit inputs | **0** |
| Other GitHub Actions workflow files | **3** |
| QA/event-analysis/harness/helper tool files | **14** |
| Unit and QA tests | **18** |
| Documentation | **21** |
| Analysis evidence and source/original QA data | **19** |
| **Total** | **75** |

The candidate tree contains **8,670** tracked blobs; the compared `main` tree contains **8,725**. Exactly **55 were added, 20 modified and 0 deleted**. The blob-count difference therefore reconciles arithmetically without hidden removals. The audited categories are explicit path-based classifications. Full blob SHA evidence is in the machine record.

**No tracked content difference whatsoever** was observed in `native/`, `reference/imported/`, `third_party/`, `media/`, conventional packaged source/assets directories, or root CMake/Make inputs. Eight specifically inspected original Windows-source/package inputs also remained identical between commits, including:

- `.github/workflows/manual-romfree-windows-playtest.yml`
- `tools/assemble_baldosa_windows_candidate.py`, `tools/bind_baldosa_candidate_receipt.py`, `tools/audit_baldosa_romless_candidate.py`, `tools/check_windows_portable_binary.py`
- `tools/baldosa_modern_profile_activation.cpp`, `tools/baldosa_native_modern_root.cpp`, `tools/baldosa_native_pause_lifecycle.cpp`

**Changes requiring explicit interpretation:** `.github/workflows/baldosa-windows-native-bridge.yml` did change. This is the Windows QA/experimental build bridge, now with source-pinned crash, storage and multi-process negative test steps. `.github/workflows/qa01-event-campaign.yml` also changed, and `.github/workflows/retain-nominated-owner-playtest.yml` was added to retain the historical immutable package, not to change its executable. The changed tools include the existing native Pause/Quit QA harness, cross-process verifier, `verify_baldosa_windows_extracted_launcher.py`, new PE-timestamp checker, retained-artifact verifiers and original event observers. These are material changes to **test/verification processes**, so a newly run bridge workflow does not silently inherit a historic passing CI verdict.

## What the result does and does not establish

**Supported finding:** At the fixed two Git commits, no changed tracked game/runtime/art/input files or original manual package assembly components were identified. The original nominated Windows ZIP and actual PE are still the **one immutable historically qualified source-bound candidate** for further independent QA. We have no source-tree basis to claim a new gameplay binary implementation landed after its nomination through that main checkpoint.

**Not supported:** A fresh Windows build from `main` is bitwise identical to the original ZIP or EXE. Git-tree parity does not verify compiler/toolchain version, dynamic remote fetches, build-time environment, PE timestamps, SDK, externally supplied ROM, upload/download integrity or actual binary output. Nor do green source-level QA tests approve physical Windows gamepads, audio output, 4K/rendering, human UI or power-loss resilience. There is **no new candidate nomination**, release packaging approval or inherited acceptance of Windows workflow results.

**Release blocker still live:** [P0 #1214](https://github.com/gamesbyian/UR-Recomp/issues/1214), independently source-pinned to the nominated original Windows executable, reproduces post-raw/pre-typed save divergence that prevents a damaged racer from loading and additionally prevents the existing canonical switch to a healthy alternate. See [QA02-ORIGINAL-WIN32-TWO-PROFILE-CRASH-BLAST-20261016.md](QA02-ORIGINAL-WIN32-TWO-PROFILE-CRASH-BLAST-20261016.md). No tracked Modern implementation or persistence-recovery repair has landed between the compared commits.

## Exact integration and QA handoff

1. Continue using only the ledger-pinned immutable owner ZIP for currently authorized **hosted** QA observations; do not infer a fresh candidate from advancement of `main`, and do not transfer evidence to QA-head executables.
2. On the first substantive Modern recovery, CPU/APU, game/rendering, authored art or actual package-assembly input merge, recompute the full tracked diff and have integration nominate and source-bind the actual new Windows executable/ZIP **before** qualifying fixed functionality. The present report is not an argument for indefinite reuse after such a merge.
3. Re-run the genuine Windows raw/typed fault acceptance from #1214, including healthy alternative-profile escape and deliberate old/new recovery, on that exact newly nominated artifact. Independent QA must check full raw/typed old/new bytes and repeated cold boots, not merely producer JSON or green unit suites.
4. Preserve current release-ledger status: QA-02 `in_progress`, QA-12 `unverified`, **0/12 full accepted gates**, **0/45 complete original/native USA events**, `physical_hardware_verified=false`, candidate release `not_assessed`.

**Three-project reuse preflight:** This audit reuses UR's existing first-party source blobs, source-bound candidate verifier and QA release ledger, existing pinned Baldosa guest inputs as part of the unchanged imported tree, and Malmazuke as advisory source only. No additional clone, unbounded Actions campaign, copied emulator, synthetic game result or new persistent storage implementation was created.
