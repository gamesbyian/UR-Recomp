# First native Win32 2P source result → atomic paired Records → fresh game (independent QA review)

**2026-10-13 local / 2026-10-14 UTC.** Release-QA read-only evidence review, not a QA-01 emulator-original parity pass, consumer Windows L5 test or release-candidate nomination.

## The real advancement

After the previously archived red [run 38493490210](https://github.com/gamesbyian/UR-Recomp/actions/runs/38493490210), product [PR #1425](https://github.com/gamesbyian/UR-Recomp/pull/1425) corrected its **test-owned** P2 profile's rider to match actual stock source rider **2**. The exact local winner/result source never needed alteration, nor did the strict Modern match binder. The corrected [Windows native bridge run 38497178182](https://github.com/gamesbyian/UR-Recomp/actions/runs/38497178182) completed **green**. Independent QA downloaded and inspected the two original GitHub Actions wrappers.

From the **same actual Windows native game executable**, the source stock 2P racer picker reached gameplay with both joined seats; the game produced a settled ordinary `course:01` result at host frame **4377** with riders **0 and 2**, times **00:27.61 and 00:27.57** and original-source winner **rider 2**. The existing product publisher logged `UR_BALDOSA_NATIVE_MATCH CAPTURED=1` and a `published=1` receipt for the same result. Unlike the previous red experiment, the producer reports **one canonical saved `.urrun` and matching `.urrun.urmatch` sidecar**, checked before/after a genuine second game process opened the native Records page.

The second process's actual guest text reports `matches_readonly=1 paired=1 unavailable=0 selected=1` and `LAST 01 LOSS 00:27.61 source=historical_paired_archive`. That **LOSS** and P1's 27.61 correctly agree with the source winner (P2), rather than awarding P1 an invented win. It also reopens P1's named 8192-byte SRAM and checks P2's separate SRAM remains untouched. The stock game input script now completes at frame **5667** instead of **44047**, after source result had already occurred, removing an unnecessary roughly 38,380 frame tail.

## Exact original artifact identities

The successfully reviewed product PR head was `8d21e07d6e69c93c4dc27f7abbc63792c558b0e6`. The candidate manifest and executable were produced from synthetic pull-request checkout merge commit `821fc15a507680cf7e7a45c4879d7f91b0ec504e`, whose **second parent is the exact PR head** and first parent is `d20fa7b36d874e366d7c4294a7a0c9b68713d6ce`. This is **not** an independently nominated current-`main` release ZIP.

| Artifact | Independent SHA-256 |
| --- | --- |
| [Candidate Actions wrapper #11864698094](https://github.com/gamesbyian/UR-Recomp/actions/runs/38497178182/artifacts/11864698094) | `531a98bebbfcbaf2a02126090d99c4d6a6e0fde5448213b46b4960a5d19a3774` |
| **Inner actual ROM-free Windows ZIP** | `c417f5a297f40d2daba0f94463908b576c012d1597493e3913f5000a90af961d` |
| Inner Windows executable (PE32+ AMD64) | `36488d2de8587167f672913d7422ff5f6676ea571c93c9d80aab3b1489475ed2` |
| [Runtime Actions wrapper #11864648374](https://github.com/gamesbyian/UR-Recomp/actions/runs/38497178182/artifacts/11864648374) | `9906d288be1b7f1ab47e70a983b4a1ab49435b831aa06c96028f8e16d49f607a` |
| Played native 2P source-result log | `0a675155a7695fc6c3bfa46551e5813ec58d85e7da570765f4992cfef38368a4` |
| Fresh native game 2P Records log | `18f4d148ebf8985c50a4193b6b357d6636fa976ece3021b02b1311086a075e3d` |
| 2P result/provenance JSON report | `e8461584dea9eee8c305ad644ac96d23a56cc4351a72715e28be4109ab34d266` |

The two ZIP wrapper digests, inner ZIP, adjacent inner SHA-256 sidecar, exact four-file manifest payload hashes/sizes, executable AMD64 PE header and equality of runtime executable/launcher to the packaged bits were independently checked from downloaded bytes. **Do not use the Actions wrapper SHA as the Windows ZIP SHA.**

The two product-produced run artifact hashes are retained in the [compact source-bound evidence receipt](../analysis/evidence/baldosa-win32-38497178182-native-2p-fresh-records-review.json). They are **producer-reported**, not independent run-file byte digests, because the current Windows runtime upload omits the newly saved `.urrun` and `.urmatch` bytes. The producer's separate in-run before/after checks are valuable, but an external reviewer cannot currently reparse those absent files. No ROM, private raw SRAM or saved private user profile was uploaded.

## Reproduction via existing QA consumer

Use the current independent `tools/verify_baldosa_romless_candidate_qa.py` after the 2P evidence extension in [#1431](https://github.com/gamesbyian/UR-Recomp/pull/1431) merges. Download the exact **two original Actions wrappers** above (do not pre-extract them):

```bash
python3 tools/verify_baldosa_romless_candidate_qa.py \
  --actions-artifact candidate-actions-11864698094.zip \
  --runtime-evidence runtime-actions-11864648374.zip \
  --expected-actions-artifact-sha256 531a98bebbfcbaf2a02126090d99c4d6a6e0fde5448213b46b4960a5d19a3774 \
  --expected-runtime-evidence-sha256 9906d288be1b7f1ab47e70a983b4a1ab49435b831aa06c96028f8e16d49f607a \
  --expected-source 821fc15a507680cf7e7a45c4879d7f91b0ec504e \
  --expected-zip-sha256 c417f5a297f40d2daba0f94463908b576c012d1597493e3913f5000a90af961d
```

The **expected independent QA result is still `outcome=inconclusive` for release**. The narrow positive is a real played native Windows 2P result and log-grounded fresh-game paired Records, coarchived with verified candidate source/ZIP identity. The consumer must reject only-one-or-two-of-three 2P reports/logs, wrong riders/time/outcome, duplicate publications, missing fresh-game Records or independent-approval claims that no fixture supports.

## Independent fresh-Records visible-result binding (QA-12 follow-up)

The original hosted log admissibility required `records_last_2p=` plus `source=historical_paired_archive` but **did not verify the displayed line against the accepted source result**. Its earlier unit-positive fixture even contained P1 `WIN 00:27.57` while the test source reported rider-2 winning and P1 taking `00:27.61`. This is a **QA false-positive allowance**, not evidence of a production display error: the actual green 38497178182 Windows log correctly shows `LAST 01 LOSS 00:27.61`.

The QA consumer now checks that the fresh game shows the **selected P1's** original-source outcome (`WIN`, `LOSS`, or `DRAW`) and time in the native Records painter's genuine `MM:SS.hh` / `DNF` convention, including the correct `course:01` display label. It also requires the match writer's source `frames` count to agree with the settled input count, and the writer's `multiplayer-runs/<new-run>.urrun` filename to match the *same* `.urrun` stem whose exact pair of SHA-256 strings the product producer reported. Regression tests deliberately substitute opponent clocks, wrong winners, different course labels, unrelated run paths, mismatched basenames and mismatched frame counts; legitimate P1-win, draw and DNF values remain supported.

This establishes better **causal consistency of coarchived game logs and producer receipts**, still **not** independent verification of absent `.urrun`/`.urmatch` bytes. No new original-emulator or physical-hardware acceptance is inferred.

## Prepared raw CI pair byte admission (future producer handshake)

A separate **read-only** QA tool, `tools/check_baldosa_native_ci_pair_bytes_qa.py`, is prepared to consume the exact future **synthetic CI-profile** `.urrun` and `.urrun.urmatch` files together with the **same** source-result JSON, played-game transcript and fresh-game Records transcript. This tool does not create game saves, amend the product publisher, use a ROM, run a Windows game or claim strict original/native parity.

When the product owner opts to retain **only those test-created pair bytes** from a future real Windows bridge, without any personal ROM, raw SRAM, real player profile or user root, the independent QA command can inspect them outside the game:

```bash
python3 tools/check_baldosa_native_ci_pair_bytes_qa.py \
  --report report.json --played-log played_native_2p.log \
  --fresh-log fresh_game_2p_records.log \
  --run run-XXXXXXXXXXXXXXXX-XXXX.urrun \
  --match run-XXXXXXXXXXXXXXXX-XXXX.urrun.urmatch
```

The reader first requires the existing actual guest-result and second-process Records log acceptance, then independently recomputes **both raw-file SHA-256 digests**, the established run/match FNV-1a64 trailers, fixed `uniracers-usa` USA ROM/source-compat/course/mode provenance, exact native 2P input-span and source result timing, and the `p1=MIKE/rider0` + `p2=MARTIN/rider2` identities and result in the sidecar. Its tests use **synthetic bytes only**, exercising correct checksummed-but-wrong records and deliberately corrupt/truncated artifacts. A matching producer-supplied report alone is *never* enough.

**Do not retroactively mark this check passed for run 38497178182.** That run's Windows Actions artifacts contain the report and logs, but **not** the two saved files, so the independent digest/codec checks have not been possible. A future positive reading remains a **bounded hosted file-consistency finding**, not original-emulator parity, physical-controller certification or release eligibility.

## What is still actually missing

An **independently reviewable canonical new pair** means retaining those two **ROM-free synthetic CI-player saved artifacts**, bound to the exact existing digest and candidate, and independently parsing their real run/match codecs. This is a reasonable narrow next product/QA handshake, but cannot be achieved by retroactively inferring bytes from this artifact. Then complete one **packaged, human-controller-first native 1P/2P → Records** Windows journey and actual hardware gamepad/audio/display acceptance. A strictly accepted complete USA original-versus-native event and other **45/45** original-release coverage remain separately owned QA-01 work.

No release status or gate promotion follows this green product integration run. The current ledger retains **0/45 independently accepted original/native USA complete events, no nominated main-source+inner-ZIP consumer release candidate and no L5 physical acceptance**.
