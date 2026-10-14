# Independent QA: actual Windows existing-P1 selector witness (2026-10-14)

**Exact source:** merged Modern [#1513](https://github.com/gamesbyian/UR-Recomp/pull/1513), PR-head `737e3fd9954c3a9bdd14f22199187936f14c6a19`, green [Windows x64 workflow 38520109013](https://github.com/gamesbyian/UR-Recomp/actions/runs/38520109013), native Windows job `115707987452`. All its six exact-head workflow checks completed successfully. This is **not** a nominated final merged-main release build.

Independently downloaded actual Actions artifact **11873807418** `baldosa-win32-native-pause-evidence` (42,418 bytes); SHA-256 `9d5234047b4b68240d92420197ce6a95d99afab125c3e793d968e50931c0e202`. It contains a **single complete source-owned five-process group** under `UR Baldosa Win32 Pause Route/native_existing_p1_switch/`. The real-byte source files and their independent SHA-256 digests:

| Original archived file | SHA-256 |
| --- | --- |
| `report.json` | `ccabb780dbe47e2e650a240fff68059bfd12ac91c91c44627ad4643c3c04e481` |
| `first_creates_mike/log.txt` | `161233dad4cc169dd632d0a7ad1cb21b82d7e9df6b203cc4aceb5a028b580d03` |
| `named_mike_adds_andrew/log.txt` | `6dfccf9bbc709b6e6ca6b719049f3e7da68e17ad18fb9e42a100aa21c0d79ad5` |
| `mike_switches_to_andrew_next_boot/log.txt` | `e97ac0d3dd605cfe8beb46f58ce7e8a18b7546cc9ff49ab27fe4f3bb0216ec2a` |
| `andrew_switches_to_mike_next_boot/log.txt` | `a0dc3ef33bd4eaf6576e0a5577b214c3580901cfd16698c80e02dcc9874729f1` |
| `fresh_mike_reboot/log.txt` | `4e74d84e0d895ee4ce52820894feb2b0e8a9a238c50b4cc13811e52f7f1c07e5` |

**Source stages observed:** native anonymous first MIKE creation, fresh named MIKE creation of separate ANDREW; next native MIKE opens genuine Modern existing P1 selector, confirms switch MIKE→ANDREW and shows a **sticky stale-guest race-block**; fresh ANDREW now boots its own genuine 8-KiB SRAM, confirms selector ANDREW→MIKE and also blocks the stale guest; fifth real Windows game loads MIKE's original exact FNV-summarized SRAM and navigates ordinary read-only Records and stock 1P. A successful switch deliberately rejects an old process's save checkpoint with `PREFLIGHT_REJECTED status=3` after the switch: the rejection is an **expected isolation security property**, not an existing-profile selection failure. A next-process boot is mandatory to reactivate named gameplay.

The downloaded `report.json` confirms the source scope `native-p1-existing-profile-selector-real-controller-root-next-boot`, published root catalog SHA-256 `f42bf482f9cce61317fdf1d9c238fbdde65a5bd740466e95d40a48037a4fd131`, and explicitly **false** for guest hot swap, scored paired result, physical pads and release credit. Its raw P1/ANDREW profile catalog/selector/8-KiB SRAM bytes were not coarchived, so their producer-reported consistency **cannot** be independently rehashed or decoded from these logs. Every real Windows process reports **zero connected joysticks** and `audio=dummy`.

New read-only `tools/check_baldosa_win32_existing_profile_selector_qa.py` checks those exact five source logs, one absolute common non-traversing Windows user root, both source-ordered real root switch confirmations, the current named 8,192-byte SRAM boot fingerprints before switching, both post-switch race/preflight barriers, final original MIKE fingerprint restored, no original-native result/Records credit, and zero physical input credit. It rejects a stale switch guest that manages to enter stock racing, duplicate or forged markers, missing opposite identity, released guest save preflight after changing authority, wrong original guest boot on the next process, incomplete archives, and forged producer release fields. Example for the independently downloaded original ZIP:

```sh
python3 tools/check_baldosa_win32_existing_profile_selector_qa.py --evidence /path/to/real-artifact-11873807418.zip
```

ROM-free synthetic unit tests establish only the negative parser contract. This particular probe does not produce any **earned 2P Records**; the final actual Records page reports `paired=0`. Product [#1522](https://github.com/gamesbyian/UR-Recomp/pull/1522) is a **separate** in-flight integration lane intending to use the actual UI selection together with a genuine newly source-scored 2P result. Do not splice the #1513 existing-P1 switch into unrelated fixture-provisioned #1425 or source-settled #1510 evidence and call the combined journey independently accepted. The release ledger retains unverified physical two-pad/audio/display and first-user scored/Records L4 gates, no candidate source/inner ZIP nomination and strict original-USA **0/45 complete events**.
