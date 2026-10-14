# QA-12: first genuinely frontend-created 2P scored Windows result with both Records, source-log admission

**2026-10-14 positive hosted-source witness, no release gate promotion.**

For the first time, **one connected original Windows-native test** created both racer profiles **through the actual modern game frontend**, then used those very profiles in a source-settled scored two-player Race, published one named pair, and reopened **both players' earned 2P Records in separate fresh native game processes**. This does *not* require stitching together prior fixture-provisioned 2P results and separately created players.

Independent QA directly downloaded and inspected the real exact [Modern #1510 Windows run 38522739830](https://github.com/gamesbyian/UR-Recomp/actions/runs/38522739830), job `115716339651`, PR exact source head `dddd8b5acf92502010f8b48436bf6c4595ea280f`. The native Windows test job and unit checks are green; the PR was **not** merged when observed. Exact independently computed hashes, process file digests, guest clock and package identities are preserved [in machine-readable evidence](../analysis/evidence/baldosa-win32-38522739830-created-mike-martin-source-scored-review.json).

The true downloaded **Windows source archive**, Actions artifact `11874846942`, contains 50,259 bytes, SHA-256 `fd7a2b6cbc7c4a40ffd0d6c552b3e441423d8b375c1d30d97b869996a21c8e78`. It includes **one report and all five distinct native game log files**, fully rehashed:

| Source evidence within `native_player_created_2p_records/` | SHA-256 |
| --- | --- |
| `report.json` | `e0d677a3afe8a5ea5d5ffc6bb77c48a780cfad958b8747ec566ccb52dcd92e88` |
| `first_P1_mike/log.txt` | `caaacb2137b137e54561b55a4a3d2614436872fee1539a39c986eb83277b6553` |
| `named_P1_adds_P2/log.txt` | `741e8411727a36f4d82e07094b72613a39c1305e61c44a9ed99a0ba266da9594` |
| `played_native_2p/log.txt` | `e449a80254b6b6417334b3778d9537e1730620d3eb7d3a86197e1f49aa6a57be` |
| `fresh_mike_records/log.txt` | `50dce1462da9bf939609d1482209811f2ee284c478b3d3c41e0a657bd8aa62a3` |
| `fresh_martin_records/log.txt` | `29123087a1e403b51c0dc08dcd65edeb64a05c71b4b47323e5ad5c9a63fb45a5` |

## Exact source event and participant consistency

1. Fresh anonymous native game used the actual X/A frontend to create **MIKE rider 0**. Next genuine native MIKE process booted 8,192-byte MIKE SRAM, opened the shared second-racer modal initially at **preset 1**, dispatched **Down** to `second_racer_preset=2`, and created isolated **MARTIN rider 2**, preserving MIKE as currently selected P1.
2. The third native process joined both seats using the actual shared host event path and reached untouched original stock `menu=3d`. The real guest script logged menu ready at **f248**, live race source condition `$0053==8610` at **f2002**, and original GO ticker `$0E1F` at **f2353**. Original guest Race settled on source host **f4378**, with rider bytes **0,2**, input **2231 frames / five source input runs**, published source result `winner=2`, **MIKE 27.61s**, **MARTIN 27.57s**. Exactly one source-paired `.urrun/.urmatch` archive was reported, associated with both real created identities.
3. A **fourth native game** explicitly selected MIKE and displayed `LAST 01 LOSS 00:27.61` on actual read-only 2P Records. The fifth booted MARTIN's separately stored 8,192-byte SRAM and displayed `LAST 01 WIN 00:27.57`. Both read-only pages report exactly one source-historical pair and zero unavailable items; no guest result or new match was invented during either viewer.

The independently downloaded report explicitly records the associated run/sidecar digests `346296f6...8a41` / `e1440b45...9c4` and claims same-pair preservation across both viewers. **Those are producer-reported strings.** The actual raw run and match bytes are **not contained in the downloaded Actions artifact**, so QA cannot independently rehash them, inspect FNV/checksum/format/source clock/controller spans or prove crash-atomic publication from this run. No original full user catalog/selector/SRAM bytes were archived either, so the positive log-level source and producer data-integrity observations must remain distinguishable.

## Verified product package bytes, not nominated release

The corresponding real Actions Windows candidate wrapper, artifact `11874831965`, SHA-256 `3f0bb5e20ec1dfeafd2d10e59fcecf7991f68ee3eb200dca69883f1d0d2ae96b`, contains the **inner portable ROM-free ZIP** SHA-256 `37054f58ceb7099845acd532a492246a92fb3a4c31d299ac2e1dc23e7b22c6cd` (5,946,733 bytes). QA independently rehashed every immutable manifest member, confirmed the Windows native **AMD64** PE executable SHA-256 `94209484e9d0ab4afc90267a06b208941ad74f94980a5642bcd62c6e69dd7acb`, confirmed the archived launcher script, and checked absence of bundled ROM, SRAM and run files. The manifest project revision `952d6a660cc9c5188b94bd2f3e85d8348ca667ae` is the pinned Baldosa AOT source, and required personal USA ROM SHA-256 is `859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478`. Neither manifest revision nor product PR head is an independently nominated merged-main release commit.

This evidence used **zero detected physical controllers**, SDL-semantic synthetic input, and **dummy audio**. Crucially, between MIKE's and MARTIN's fresh Records views, the active P1 selector was changed through a **verified test-only backend fixture**, not through the human-facing game frontend. Merged #1513 separately proves actual existing-P1 UI selection; product [#1522](https://github.com/gamesbyian/UR-Recomp/pull/1522) is now attempting the *stronger connected six-native-process integration* in which the same earned pair is opened after a real native MIKE→MARTIN UI selector step. The independent six-process QA consumer already exists with `--require-real-selector-ui` and will **not** substitute this older backend-fixture run.

## Release classification and exact next gates

**Credit:** independently source-log-consistent **hosted integrated first-user-created 2P result and both fresh player Records** on this exact pre-merge Windows candidate. **Zero** raw run/match archival byte signoff; **zero** physically plugged 2P pads, live sound device, real 4K Original/HD/Widescreen, packaged no-argument interactive first-person checkout, injected disk/crash/SAVE PENDING recovery or authoritative original/native 45-course complete-event equality. No formal L4/L5 release pass and **strict 0/45 complete original USA events unchanged**.

Modern owner should safely coarchive **only the test-owned throwaway `.urrun` and `.urmatch` bytes** under exact named bounded artifact paths for the already merged independent raw-byte decoder to inspect, not a ROM, original SRAM or personal user folders. Run the independent six-game source consumer on the **exact true Windows head** once #1522 is green. Do not dispatch general soak/campaign repetitions or increase account concurrency until these missing source/byte/hardware discriminators are resolved. A release ledger candidate remains **null** until a single final merged-main product ZIP is nominated and independently accepted.
