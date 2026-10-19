# QA01 research-factory upgrade: evidence first, volume second (19 October 2026)

**Disposition:** merged first-generation ROM-free readiness gate (#1909); independent raw-byte causal-checkpoint binding proposed in a separate follow-up. No new campaign, scheduler or runner dispatched, no changed ledger writer, no accepted original/native event. This is a supplement to [seven source-owned cumulative campaigns](QA-CUMULATIVE-RESEARCH.md), not an eighth campaign or release gate. Work queue and QA01 acceptance retain priority.

## First genuine producer result consumed (19 October)

The first source-authentic Zoo capture-on/off archival experiment has been independently rehashed and byte-reviewed, and the RF062 one-shot producer failure has been classified. See [actual run intake](QA01-AUTHENTIC-PRODUCER-RESULT-INTAKE-20261019.md) and [machine bytes](../analysis/data/qa01-authentic-producer-consumption-20261019.json). Result: **9 continuous paired script-dump frames, 13 unmasked WRAM differences at four concrete DP/stack addresses, 0 SRAM differences and a bounded noninterference A/B positive**. RF062's attempted genuine PC/read producer failed **before guest execution** on the v2 Read-IR source anchor. We have no same-checkpoint cross-guest ordered bus event payloads or CPU input-poll proof. Therefore **v2 factory admission is HOLD, no ten-case pilot or larger frontier batch is authorized, and QA01 remains 0/45**. The original/native source and guest controller files are independently hashed but *not byte-identical to each other*; matched controls are within each guest's on/off replay.

## Trigger and sequence

1. CPU/APU producer qualifies actually executed original RF045 + native RF047 read/write/checkpoint ordinals, real guest PC, complete fixed local observation window, original controller consumption, immutable original/movie/ROM/native hashes and noninterference. [RF061 producer staging](RF061-ZOO-EXECUTED-PC-CAUSAL-PRODUCER-20261019.md) identifies still-missing fields; do not fabricate them from stale IPC or interleaved stdout.
2. Continuous-frame owner qualifies exact same-phase **original and native** full 128KiB WRAM plus 8KiB SRAM across the requested bounded window, with no excluded bytes. Keep all decisive raw images and run `qa01_verify_frame_capture.py` separately. A full course still needs all original/native race frames and persistence/progression.
3. Independent QA supplies true/false attestations linked to exact original/native inputs and source artifacts. `tools/qa01_factory_preflight.py` combines the existing three merged diagnostic report schemas and an independent producer attestation. It returns a machine receipt with `hold` and exit 2 on incomplete/negative prerequisites. A fully positive result only returns `bounded_pilot_ready`, **maximum ten cases and no automatic dispatch**. These attestation booleans are a gate on already reviewed evidence, **not proof in themselves**; a dishonest `true` is not authenticated merely because the schema parsed.
4. Only then run one manual small original/native case population, not a new 10k frontier. Measure runner-minutes and retained bytes, exact new discrimination in source PC/read chains and actual state outcomes. Every experiment must record separate source/native clocks and independent original-checkpoint verification.
5. Consider 100 cases if a changed observer/producer yields a confirmed decision question; 1,000 only after a small observed cohort establishes a rare measurable feature or other named confidence threshold; 10,000 only on the existing fixed-cohort resumable mechanism after a 1,000-case result justifies it. [Measured escalation policy](QA-CUMULATIVE-RESEARCH.md#scientific-yield-escalation-and-stopping-2026-10-14) already forbids fingerprint-for-its-own-sake factories.

## New read-only admission check

Input attestation JSON requires `schema="ur-qa01-research-factory-preflight/2"` for positive readiness (legacy `/1` returns HOLD), immutable `source_sha`, `rom_sha256`, `movie_sha256`, `input_sha256`, and explicit boolean `checks` for source binary, native binary, controller reads, guest frame acknowledgments, phase qualification, no instrumentation perturbation, original clocks/unaltered input and unmasked retained memory. These claims must be independently backed by real signed/hashed source-owner evidence, not entered by guesswork.

```bash
python3 tools/qa01_factory_preflight.py \
  --attestation /tmp/qa01-independent-source-attestation.json \
  --causal-report /tmp/qa01-real-causal.json \
  --original-events /tmp/qa01-actual-original-bus-events.json \
  --native-events /tmp/qa01-actual-native-bus-events.json \
  --frame-report /tmp/qa01-real-frames.json \
  --independent-raw-report /tmp/qa01-independent-raw.json \
  --retained-raw /tmp/qa01-retained-original-native-raw \
  --output /tmp/qa01-factory-admission.json
```

Every provided report is parsed fail-closed for the named schema and source/input relationship, non-promoting event verdict, actual unmasked frame counts and independent raw-byte comparison. The output carries SHA256 hashes of all input JSON and missing/negative conditions. A report is a **read-only readiness aid, not proof that the signed producer is truly original**. Do not modify `research/qa-cumulative-ledger` from this tool, and never add a new scheduled factory merely because the tool reports readiness.

## Stronger three-consumer binding before admission

A review attestation with all `checks=true` is not by itself trustworthy. The revised `/2` contract additionally requires `evidence_sha256` mapping **exactly** `causal_report`, `frame_report`, and `independent_raw_report` to the SHA256 of each supplied JSON file. Those digests must be independently reviewed and recorded before the preflight runs. Swapped reports fail rather than silently inheriting somebody else's sign-off.

**For positive readiness, both `--original-events` and `--native-events` are also mandatory.** The preflight hashes each source/native event file from a single read, independently reruns `qa01_causal_window.assess` on those bytes and demands the entire recomputed causal report match exactly. A fabricated native executed PC, tampered event sequence or stale report fails rather than yielding a provisional green. This is read-only evidence recomputation, not an emulator run; independent original provenance and true guest-PC execution still require the explicit external attestation.

**For positive readiness, `--retained-raw` is mandatory.** The preflight reruns the project's independent `qa01_verify_frame_capture.verify` against the actual original/native raw image files and compares its counts against the independently supplied audit. It requires that the causal original and native windows share the frame fingerprint's **same declared observation phase**, and that the causal checkpoint falls inside the genuine continuous frame interval. For each causal physical `7E/7F` WRAM address, it independently opens the **same retained original/native frame** and verifies both source bytes, the differing-byte claim and the full-WRAM diff bound. Executed guest event SHA256 and complete/nonoverflow recorder flags are also required.

The raw-byte check does **not** independently establish CPU phase alignment or genuine emulator provenance; those are still distinct `checks` requiring externally verified executed source input and no capture perturbation. A forged self-attestation or a dishonest original emulator producer remains possible; this is a fail-closed integration contract, not a cryptographic authority oracle. A missing raw directory produces HOLD (exit 2), never a synthetic positive. No PR should introduce a factory runner from a mere tool-level `bounded_pilot_ready` without the human-reviewed independent evidence.

## Ownership and nonduplication

- **CPU/APU:** executed-PC, original shared ordinal, actual causal guest reads/writes; gameplay correction only from genuine consumption evidence.
- **Continuous memory owner:** streaming/fail-closed raw frame producer and measured storage/runtime/noninterference, currently tracked by [PR #1904](https://github.com/gamesbyian/UR-Recomp/pull/1904).
- **Independent QA:** source/input/PE/ZIP/cold persistence and evidence attestation; QA01 remains 0/45 until independent complete event admission.
- **Factory maintenance (this lane):** lightweight admission semantics, reusable source-bound transport receipt, cost/yield policy and bounded manual dispatch. Do not modify guest instruments, acceptance authority or the cumulative evidence branch.

Existing seven-lane auto rotation remains unchanged, preserving Tuesday/Friday cadence, single-writer semantics, seed reservation policy and 20-runner account ceiling. The `original-native` campaign's historical incomplete producer needs targeted recovery before heavy coordinator runs. Default **no 1,000/10,000-case dispatch**.
