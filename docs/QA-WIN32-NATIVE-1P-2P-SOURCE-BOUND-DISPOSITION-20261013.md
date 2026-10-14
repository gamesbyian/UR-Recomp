# Independent Win32 native product evidence: accepted 1P journey, refused 2P pairing

Dated 2026-10-13 local / 2026-10-14 UTC. Authority: **independent release QA evidence** only, not the Modern product writer, original emulator comparator or L5 physical certification.

## Reprocessed actual Windows artifacts, not unit fixtures

### Successful guest-played native 1P, run 38492514334

The product owner merged [#1416](https://github.com/gamesbyian/UR-Recomp/pull/1416) after [Windows run 38492514334](https://github.com/gamesbyian/UR-Recomp/actions/runs/38492514334) passed. Independent QA **downloaded both Actions artifacts** and separately recomputed the wrapper and inner ZIP identities, verified the exact four non-ROM candidate payloads against the embedded manifest, checked the AMD64 PE32+ executable header and matched the runtime executable digest to that immutable manifest.

- Product PR HEAD: `fd3ccdf5f67364a09b8d7b4b68d214598ee1afff`.
- **Synthetic Actions pull_request checkout/manifest source commit:** `5fd490beb905f111a296f46685efd4a3b19d0236`; its second commit parent is exactly that PR head, its first parent is `a62c370519e385b4a79457ad7c5d639dd9892876`. **Do not mistake the checkout merge for product HEAD or current `main`.**
- Candidate wrapper [artifact 11862436040](https://github.com/gamesbyian/UR-Recomp/actions/runs/38492514334/artifacts/11862436040), SHA-256 `9d38555daa39c6dcf4b5651ceef5730ff9ead34eeb1dd59ea6764e6865243f6d`.
- Actual **inner ROM-free ZIP**, SHA-256 `ab482697ab0cfca6a2c0db31520c11ba88eea872b3b9d3240b4f13c9bdf80739`; its sidecar matches independently calculated bytes. The executable SHA-256 is `e090e7eafdb8355acbd844f74aca0219fcb5d4d768dd481e48ffc2ce88b016f1`. Do not promote the *outer* wrapper digest as the candidate ZIP SHA.
- Runtime [artifact 11861599510](https://github.com/gamesbyian/UR-Recomp/actions/runs/38492514334/artifacts/11861599510), wrapper SHA-256 `1a00d912388e2c0bc0c07ce671f191e1a986372edfe4ef5486ef4ad203771f35`. Its launcher report independently names the same **inner ZIP** hash; its runtime report names the same immutable **executable** hash.

Actual game logs retain one stock native 1P `course:01` source result at host frame **4163** (race host 1910, 1,679 ticks at 60Hz, 2,253 captured input frames, five runs), with `UR_BALDOSA_NATIVE_RUN CAPTURED=1` and `published=1` under named profile `native-ci-rider`. A second **native executable process** reports the same named-profile SRAM boot and a validated/unavailable=0 Records read. The producer asserts exactly one newly saved `.urrun`, unchanged across both processes.

**Limit:** only the producer-reported SHA-256 `b73b9d8b2bfeb3379ff35e4a8db14d73a56eb7dce96fa481e1288f8ef6aca4a4` of that `.urrun` survives. The runtime artifact does **not** retain its raw bytes. Consequently this is source-driven native **product** result-to-fresh-Records **log evidence**, not independently rehashed record bytes, original/native course parity or actual packaged two-human-controller L5 acceptance. The machine-readable independent crosscheck is [the retained 1P receipt](../analysis/evidence/baldosa-win32-38492514334-native-1p-fresh-records-review.json).

Reproduce with the existing read-only `tools/verify_baldosa_romless_candidate_qa.py`, after downloading **exactly those two archives**:

```bash
python3 tools/verify_baldosa_romless_candidate_qa.py \
  --actions-artifact candidate-actions-11862436040.zip \
  --runtime-evidence runtime-actions-11861599510.zip \
  --expected-actions-artifact-sha256 9d38555daa39c6dcf4b5651ceef5730ff9ead34eeb1dd59ea6764e6865243f6d \
  --expected-runtime-evidence-sha256 1a00d912388e2c0bc0c07ce671f191e1a986372edfe4ef5486ef4ad203771f35 \
  --expected-source 5fd490beb905f111a296f46685efd4a3b19d0236 \
  --expected-zip-sha256 ab482697ab0cfca6a2c0db31520c11ba88eea872b3b9d3240b4f13c9bdf80739
```

This validator's response is always `outcome=inconclusive` for release QA. It can admit the hosted 1P product log milestone, never elevate original/native source parity or physical gamepad acceptance. It is a *prior PR-merge source artifact*, not a newly nominated `main` release candidate.

### Failed 2P pairing, run 38493490210

The product owner is developing [#1425](https://github.com/gamesbyian/UR-Recomp/pull/1425). Its [failed Windows run 38493490210](https://github.com/gamesbyian/UR-Recomp/actions/runs/38493490210), head `ccfbc8b8f947bf00c24c1efc839070b3e61ad511`, uploaded the actual played 2P log in [artifact 11862804037](https://github.com/gamesbyian/UR-Recomp/actions/runs/38493490210/artifacts/11862804037), outer SHA-256 `a7b8a4a2a08b62805afe8bddb97538d662ee31345661c7f2c58e64fe758de040`; the 2P log SHA-256 is `e3ca18a7dd99498f59cdf0c006c4dfd4298fb05a8585a4d29632497fb96fa985`.

The source stock 2P game reached GO at script frame 2352 and **really settled** at host result frame **4377**, with `riders=0,2`, `hundredths=2761,2757`, `winner=2`, `input_frames=2231`, `input_runs=5`, **`published=0`**. The two Modern join seats were separately confirmed, and the game process exited normally after scripted frame 44,047. The **acceptance step** then failed because no `UR_BALDOSA_NATIVE_MATCH CAPTURED=1` or persisted pair appeared. This is a useful precise **negative** finding; no 2P Records readback occurred.

The source `native/product/local_multiplayer_match_binding.cpp` correctly demands that each selected Modern catalog rider index equal the corresponding original-source result rider. The current experimental P2 fixture in #1425 uses `make_legacy_racer_identity(1)` while the observed P2 source racer is index **2**; a rider-binding mismatch is a **strong hypothesis**, not yet a proven unique cause. The owner must investigate real stock selection and correct the selected profile/fixture/source control route without weakening the exact binder or inventing a winner. The actual result arrived roughly **39,670 simulated frames before** the final script quit, so the current long waiting window is not the missing piece.

Independent detailed evidence is retained in [the negative 2P receipt](../analysis/evidence/baldosa-win32-38493490210-native-2p-rider-binding-failure.json). The PR owner was sent the exact observations and a bounded fix/discriminator, avoiding another expensive exploratory run without new evidence.

## Next QA decision and runner discipline

1. Reuse the already-merged independent [#1427](https://github.com/gamesbyian/UR-Recomp/pull/1427) 1P source/ZIP/log classifier for future source-bound artifacts. **Do not** count a 1P source-settled game result as a strictly original/native passed course, and do not invent absent run bytes.
2. Let the product owner resolve the 2P **rider identity → atomic pair publisher** disagreement and furnish a genuine newly created `.urrun/.urmatch` pair and separate native read-only consumer. Once available, independently verify its source rider IDs, outcomes, hash-bound records, participant identities and exact Windows candidate.
3. Reuse one existing Win32 bridge candidate. Avoid sweeping 10,000 physics probes, 30/60 trial Windows repeat soaks or a duplicate producer while the concrete publication mismatch is unresolved. Existing account-wide runner ceiling is 20 shared among four development lanes.
4. Only a later **nominated, merged-`main` consumer ZIP**, independent reference comparison and physical controller/audio/display acceptance can promote the corresponding release ledger gates.

Current `docs/RELEASE-QUALITY-LEDGER.json` status remains unmodified: no exact nominated consumer release candidate, no physical Windows L5 pass, and **USA strict original/native 0/45**.
