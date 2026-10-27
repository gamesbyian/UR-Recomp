# UR-Recomp Windows physical playtest: one-candidate results sheet

Copy this file into a **private working copy**, fill what you actually observed, and send a sanitized report or link to [QA-04 issue #970](https://github.com/gamesbyian/UR-Recomp/issues/970). Use **one sheet per Windows environment**, all testing the **same independently pinned playable ZIP and PE** where possible. The current [H01–H07 operator instructions](WINDOWS-PLAYTEST-INSTRUCTIONS.md) own the test procedure; this sheet owns observation capture, **not** QA acceptance.

**Tester privacy and safety:** Do not attach the USA ROM, saves/SRAM, personal profile databases, security tokens, machine serials, MACs, identifying folder names or unredacted user paths. Keep full raw logs and valuable saves private; conduct fault/corruption tests only on disposable copies. Notes, photographs and checkmarks are claims to be independently checked, not proof of a physical Windows setup on their own.

## Candidate identity (copy and independently verify)

| Field | Value |
| --- | --- |
| UTC test date/time | TODO |
| Producing [Actions workflow run](https://github.com/gamesbyian/UR-Recomp/actions/workflows/manual-romfree-windows-playtest.yml), artifact ID | TODO |
| Exact `main` source commit SHA (40 lowercase hex) | TODO |
| **Inner playable** `UR-Recomp-Baldosa-Windows-x64-ROMLESS.zip` SHA-256 (64 hex) | TODO |
| Actual extracted `UniracersSNESRecomp.exe` SHA-256 (64 hex) | TODO |
| ZIP SHA **before / after** gameplay, both match? | TODO / TODO / yes, no or not measured |
| EXE SHA **before / after** gameplay, both match? | TODO / TODO / yes, no or not measured |
| `PLAYTEST-PROVENANCE.json` ZIP and EXE checks independently matched local files? | yes / no / not checked |
| Local ROM validation by bundled launcher | passed / refused / not run (never attach ROM) |
| Package contents or executable altered for this test? | no / yes (describe and **do not** claim exact-candidate qualification) |

The GitHub Actions **outer transport artifact ZIP is different** from the **inner playable ZIP**. Never substitute its digest. Record original failed hash observations without silently replacing mismatches.

## Setup (anonymous, factual)

| Field | Value |
| --- | --- |
| Anonymous setup label (e.g. `PC-A`) | TODO |
| Physical PC / isolated clean VM / hosted runner | TODO |
| Genuine clean installation? If yes, why known? | TODO |
| Windows version/build | TODO |
| GPU family and driver version | TODO |
| Actual physical monitor resolution and refresh observed (not only configured resolution) | TODO |
| Connected P1 input device and connection | TODO |
| Connected P2 input device and connection | TODO |
| Actual audible output device / speakers-headphones | TODO |
| Keyboard used? Screen reader / reduced motion / display scaling relevant? | TODO |
| Launcher start: File Explorer, cmd.exe, PowerShell 5/7 or other | TODO |
| Disposable test data root used (describe anonymously, no private full path) | TODO |

## One human session: H01–H07

For each row choose **PASS / FAIL / BLOCKED / NOT RUN**. A **PASS** means actually performed on this machine and observed end to end. List the trace, redacted screenshot or short video filename privately if available. Mark script-only/virtual-pad observations as such; they cannot replace physical observations.

| ID | Test, success discriminator | Outcome | Actual observations / evidence labels |
| --- | --- | --- | --- |
| H01 | Fresh extraction; no-argument packaged CMD; first player; full quit and cold restart; absence/presence of runtime dependencies | TODO | TODO |
| H02 | True stock attract after idle; P1/keyboard/P2 wake ownership; **real P1 pad** visits Play, Practice, Multiplayer, Records, Options; Back/modal/return | TODO | TODO |
| H03 | **Real earned 1P race** to result; correct displayed outcome, Records, Next Event, full quit and persisted progression after cold reopen | TODO | TODO |
| H04 | **Two distinct physical pads**, independent seats through stock 2P GO, race completion, both Records; keyboard+pad and disconnect/seat churn where performed | TODO | TODO |
| H05 | Non-ASCII disposable user-data path, create/reopen named profile, Records/replay/Options cold reopen; damaged Options only on copied sacrificial data | TODO | TODO |
| H06 | Actually audible audio; visible fullscreen/window transitions, stock pixel aspect and 16:9; physical 3840×2160 measured if available | TODO | TODO |
| H07 | Clean quit/restart saves; interrupted-write/R/T/S/Q and NTFS fault recovery **only if implemented and using isolated disposable data**; second cold boot | TODO | TODO |

**Physical five-destination breakdown (H02):** Play: TODO; Practice: TODO; Multiplayer: TODO; Records: TODO; Options: TODO; Back/modal/return: TODO. **2P identity breakdown (H04):** P1: TODO; P2: TODO; whether wrong pad controlled other player: TODO.

**Candidate acceptance cautions:** A one-machine playtest does **not** satisfy QA-04's three-dissimilar-setup requirement, two of which must be physical PCs; a claimed clean install must be independently supportable. Hosted dummy audio, offscreen screenshots, simulated gamepads and virtual screen modes cannot prove physical peripherals. An actual 4K desktop resolution alone doesn't establish source/render/pixel-aspect correctness.

## Findings to integrate (repeat as needed)

| Field | Observation |
| --- | --- |
| Finding ID / Hxx case / severity (P0 player-data loss, control/result corruption/crash; P1; cosmetic) | TODO |
| Steps, from fresh disposable root | TODO |
| Expected behavior | TODO |
| Observed behavior | TODO |
| Reproducible? number of attempts | TODO |
| Did save/profile/Records bytes change unexpectedly? | TODO / not measured |
| Related screenshot/video/log label (scrub personal details) | TODO |
| Exact original source/ZIP/PE triple above still applies? | yes / no; explain |

### Independent QA handoff (for separate reviewer; tester does not self-approve)

- Distinct reviewing agent/person: **PENDING**
- Original bytes/logs and physical observations independently inspected: **PENDING**
- Full criteria supported, if any (e.g. `MENU-01`, `MENU-10`, `DATA-05`, `WIDE-06`): **NONE ADMITTED BY THIS SHEET**
- QA-04 private hardware packet crosswalk: [existing three-setup packet contract](QA04-PRIVATE-PHYSICAL-WINDOWS-WITNESS-PACKETS-20261019.md)
- Release ledger verdict: **UNCHANGED** unless an independent authorized reviewer updates [the release-quality ledger](RELEASE-QUALITY-LEDGER.json)
- Complete original/native USA event admissions: **unchanged** unless separately proven against the original-event authority

A failed or blocked result is useful evidence too. Record it truthfully instead of removing the row.
