# QA-12: exact Win32-created MIKE/ANDREW source-GO archive review (2026-10-14)

**Independent reviewer scope:** downloaded, directly opened and hashed **real GitHub Actions Windows archives** from [Modern merged #1490](https://github.com/gamesbyian/UR-Recomp/pull/1490), exact product PR source head `c078ddf9c48c951074d534f20ea40e28aeeaa248`, passing [Windows run 38518147298](https://github.com/gamesbyian/UR-Recomp/actions/runs/38518147298). The snapshot and every full SHA are recorded in [this machine-readable review](../analysis/evidence/baldosa-win32-38518147298-created-two-racer-go-review.json). No private ROM, guest SRAM, catalog or personal user data has been committed.

## Exact artifact identities actually downloaded

| Item | Full independently calculated SHA-256 |
| --- | --- |
| Runtime evidence ZIP, Actions artifact **11873505363**, 35,148 bytes | `a72b4cf147880c35c842d4c21e6a9a0aa02ff0d0b8eecbbf06c60e056a474b5c` |
| Candidate Actions wrapper ZIP, artifact **11873160951**, 5,934,305 bytes | `0c8f87a62bd5f3f87ecb920e01594fe659b1dbd8ba981a44ecb4729f0fd80243` |
| **Actual inner ROM-free portable ZIP**, 5,940,988 bytes | `f1cf69814a7cf2ab49c12f854fc114cbbdd1d499dec28fa5ac5e641ad85f7f25` |
| Embedded `UniracersSNESRecomp.exe` PE32+ AMD64, 19,736,576 bytes | `abd08e4d9d4227ccb36fa72b3ad19434e1677ee324ec26b35077954708c93b1c` |
| Embedded `run-baldosa-modern.cmd` | `aeec348f4c5980d61a7b1d00f3740de7df1656ed386bfbf72502cfeffb411a5c` |
| Embedded candidate manifest | `51769578d3f68b3f23cf71dfef03fa928af0162bead403646a6bf2a390a635a0` |

Unwrapped ZIP entries are **exactly** candidate manifest, README, executable and launcher. All three manifest-declared immutable file byte lengths and SHA-256 digests independently match their ZIP members. The PE has DOS `MZ`, `PE\0\0`, machine `0x8664` and PE32+ magic `0x20b`. No `.sfc`, `.smc`, `.srm`, `.urrun` or `.urmatch` is bundled. Launcher inspection confirms the published ROM-hash validation, absolute-root/reparse safety checks, missing/wrong-ROM gates and one-shot restart code paths **exist in the exact candidate bytes**. That static inspection is **not** an independent Windows no-argument GUI startup/run; the producer launcher report remains without its actual raw first-racer CMD restart log.

The embedded manifest's `project_revision=3e0c1d348a97fd3b641890726639c986a0017dd6` is the **synthetic pinned AOT checkout revision**, not the product PR head `c078ddf9...` and not a nominated merged-main source version. Do not represent a GitHub Actions wrapper digest as the inner consumer ZIP digest or retroactively nominate this PR smoke as an independently approved release candidate. The stated exact USA ROM dependency SHA is `859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478`; the original ROM bytes themselves are **not** supplied to QA.

## Original native source receipts, with no result inflation

The four-file group now **exists together**, rather than merely being prospective:

| File beneath `UR Baldosa Win32 Pause Route/native_real_second_racer/` | SHA-256 |
| --- | --- |
| `report.json` | `39d5d9a1c736b3fa1b803fefab464de3a1f02e279b23609c31e8004400ea8d52` |
| `first_P1_mike/log.txt` | `037c3574d5be52e1201b12ed39cad7e700bd342a0d7336c888fe5bd7b8c1038d` |
| `named_P1_adds_P2/log.txt` | `a572aefbdfadae28ab4d5139a3456fd102e4148b180967fa4e109cddd3c1565d` |
| `fresh_two_seat_source_go/log.txt` | `0a50b7da8abdc61f9f95e879643eb2f44b020f5fd8ef4c8474dee7aa4ff3c485` |

The **existing** independently merged #1498/#1507 source inspector's requirements were matched against the **actual native log lines**, not merely by report booleans: anonymous source MIKE creation; new named MIKE 8-KiB boot and distinct ANDREW preset-1 creation; separate new game with both host seats confirmed and stock `menu=3d` handoff, without hot-swap, source result or saved pair. P2's own typed/catalog/selector/SRAM bytes remain **unarchived** and therefore cannot be rehashed independently.

The accompanying original source-owned Win32 script is `native_modern_race_entry_script(2)`. After stock handoff, its separate conditions are title-ready `until16 0053 == F60C`, in-race source/NMI `until16 0053 == 8610`, and live guest GO ticker `until 0E1F != 00`. The **actual third-process log** has exactly two successful `until 00053` receipts at host frames **248** and **2002**, a successful `until 00E1F` at **2353**, `dump go ok` at **2353** and clean script quit at **2353**. The older independent #1498 source-line checker intentionally stopped at stock entry: it did not check these script receipts. New independent `tools/check_baldosa_win32_second_racer_go_script_qa.py` extends it with source-authorized, unique Win32 CRLF/LF wait and dump chronology, refusal of shadowed script receipts and synthetic adversarial tests. Usage on the original downloaded runtime ZIP:

```bash
python3 tools/check_baldosa_win32_second_racer_go_script_qa.py --runtime /path/to/baldosa-win32-native-pause-evidence.zip
```

**Exact claim boundary:** The logged original-native guest memory **wait-script** assertions were reached. The archived logs do **not** contain actual raw guest SRAM/WRAM bytes at GO, independent original Snes9x event parity or physical controller inputs. The source-go script witness is now more tightly evidenced than mere stock menu handoff, but it remains an **SDL synthetic input scripted native execution**, with zero physical pads (`SDL reports 0 joystick(s)`) and `audio=dummy`. The third process **quits at GO**. Producer explicitly reports `completed_two_player_result=false`, `reopened_paired_records=false` and `release_gate_credit=0`. **Do not splice** this MIKE/ANDREW 0/1 creation proof to the historical fixture-created MIKE/MARTIN 0/2 scored paired Records run.

## Exact next candidate and release boundaries

Modern [#1510](https://github.com/gamesbyian/UR-Recomp/pull/1510) is the owning **in-progress** five-native-process test of the missing joined MIKE/ANDREW `0/1` journey: both frontend-created, one original-native source-scored 2P result, one immutable run/match pair, fresh native MIKE read-only Records and separately fresh native ANDREW read-only Records. Its fifth process uses an **existing verified test fixture to set the P2 next-boot selector**; it does **not** demonstrate a shipped human-accessible profile-switch UI. Its eventual real Windows producer must be green at exact head before even claiming that bounded source-route result, and any coarchived CI-owned `.urrun/.urmatch` bytes must be separately validated; the old fixture 0/2 pair byte reader is participant-specific and must not be misapplied to new 0/1.

Only after a pinned **merged-main** Windows ZIP with safe no-argument launcher, human controller-only navigation, genuinely settled native result, both Records under **human-accessible selection**, authoritative original/native complete-course adjudication, fault cuts and physical pad/audio/presentation checks can corresponding L4/L5 gates be independently accepted. Independently review a real crash-before-receipt, unavailable catalog, redirected save root and SAVE PENDING recovery without manufacturing an award. The current release ledger has **no nominated candidate SHA/ZIP**, and official original-USA complete-event count remains **0/45**. No release ledger gate is promoted by this artifact review.
