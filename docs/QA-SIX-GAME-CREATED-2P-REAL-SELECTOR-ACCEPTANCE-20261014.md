# QA-12: the six-process fully UI-created, UI-selected native 2P Records contract

**As of 2026-10-14 this is prospective, not an observed Windows pass.** Modern [#1510](https://github.com/gamesbyian/UR-Recomp/pull/1510) owns the actual frontend-created MIKE and MARTIN stock racer integration through a source-scored `0,2` two-player race, immutable run/match and fresh MIKE/MARTIN Records. Modern [#1522](https://github.com/gamesbyian/UR-Recomp/pull/1522), **stacked on #1510**, replaces the last privileged test-fixture next-boot selector with an actual native root controller X/A/B/A selection process. Both must pass their own exact source-head Windows execution; source-only unit success and merged #1513's independent selector smoke cannot be spliced together to fabricate a successful complete journey.

The QA-only `tools/check_baldosa_win32_created_pair_records_qa.py` now supports two **explicitly separate** source artifact contracts. Its default historical five-process mode retains the original hosted integration where the fifth profile's selector is a verified **test backend fixture**; it returns `martin_selection_via_backend_fixture_not_shipping_UI=true`. The new mode is opt-in with `--require-real-selector-ui` and requires **seven** bounded archive members: one source report plus **six genuine native Windows game process logs** under a common per-user Windows root:

1. Anonymous first native root X/A creates MIKE P1 (rider 0), no provisioned racer or source score.
2. Fresh MIKE explicitly opens second racer modal preset 1, moves to preset 2 via Down, and creates independent MARTIN P2 (rider 2), without mutating active MIKE.
3. Fresh game confirms distinct P1/P2 host seats, reaches original 2P GO, completes source-observed course `course:01` with real guest `race-2p` result, one source-published canonical `.urrun/.urmatch` pair, participant IDs `mike/martin` riders `0,2`.
4. Fresh native MIKE opens read-only 2P Records and sees his own exact source-clock and win/loss result.
5. A **separate actual native game process** starts under MIKE, receives the root's X/A/B/A controller-semantic input route (smoke mode 7), opens `existing_p1_opened=1 from=mike to=martin`, succeeds in saving the canonical selector, and blocks all stale guest racing, while preserving the existing earned pair.
6. A last fresh native MARTIN process boots his real rider-2 source SRAM and independently opens the **same** paired match on his own 2P Records page, with exactly the corresponding source time and complementary result.

The new parser refuses a six-process producer report unless its source scope is exactly `two-native-ui-created-players-played-source-2p-and-both-ui-selected-records`, explicitly states **no fixture selection** and **real P1 UI selector**, reports the original anonymous save preservation status, and still has `release_gate_credit=0`, `physical_pad_hardware_accepted=false`, `original_native_strict_event_accepted=false`. Its source log checker requires the extra native MIKE→MARTIN modal, **four** acknowledged synthetic gamepad-semantic edges, ordered CAS publication, a fresh MIKE boot before selection and stale-guest no-race/preflight barrier; the original scored source race and MIKE/MARTIN participant-relative Records checks from the five-process reader are reused without relaxing source rider, clock, published file or result requirements.

The actual file set is:

```text
native_player_created_2p_records/report.json
native_player_created_2p_records/first_P1_mike/log.txt
native_player_created_2p_records/named_P1_adds_P2/log.txt
native_player_created_2p_records/played_native_2p/log.txt
native_player_created_2p_records/fresh_mike_records/log.txt
native_player_created_2p_records/mike_ui_selects_martin/log.txt
native_player_created_2p_records/fresh_martin_records/log.txt
```

Run when the **owning Windows source group is actually coarchived**:

```bash
python3 tools/check_baldosa_win32_created_pair_records_qa.py \
  --evidence /path/to/real-Windows-source-evidence.zip \
  --require-real-selector-ui
```

**What this will and will not prove:** Once a future exact head passes with genuinely archived source logs, this supports a narrower *hosted native six-process controller-semantic, source-scored result and user-visible Records consistency* observation. It cannot independently certify raw player catalog/selector/SRAM source bytes, original/native completed USA event parity, absence of ROM-era runtime bugs, true two physical pads, real audio, no-argument packaged launcher, safe crash/disk failure recovery or Original/HD/wide raster parity. In particular the current product workflow coarchives the **JSON SHA report and logs**, but does **not** yet preserve the two test-generated canonical raw `.urrun/.urmatch` files; their checksum, participant identities and transaction atomicity cannot be independently decoded. This is an actionable safe source-artifact request to the Modern owner, **not** permission to upload a retail ROM, real user saves or whole profile tree.

The source-original USA complete scored course release ledger remains **0/45**. The Windows candidate commit and inner ROM-free consumer ZIP SHA remain **unset**; do not retroactively nominate a product PR build. Physical controller/presentation/audio and L4/L5 independent release certification stay unverified. Synthetic unit tests for the six-process parser are **solely adversarial input-contract guards**, not authentic native execution.
