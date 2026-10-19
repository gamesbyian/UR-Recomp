# QA01 research-factory upgrade: evidence first, volume second (19 October 2026)

**Disposition:** bounded preflight candidate; no new campaign, no scheduler or runner dispatched, no changed ledger writer, no accepted original/native event. This is a supplement to [seven source-owned cumulative campaigns](QA-CUMULATIVE-RESEARCH.md), not an eighth campaign or release gate. Work queue and QA01 acceptance retain priority.

## Trigger and sequence

1. CPU/APU producer qualifies actually executed original RF045 + native RF047 read/write/checkpoint ordinals, real guest PC, complete fixed local observation window, original controller consumption, immutable original/movie/ROM/native hashes and noninterference. [RF061 producer staging](RF061-ZOO-EXECUTED-PC-CAUSAL-PRODUCER-20261019.md) identifies still-missing fields; do not fabricate them from stale IPC or interleaved stdout.
2. Continuous-frame owner qualifies exact same-phase **original and native** full 128KiB WRAM plus 8KiB SRAM across the requested bounded window, with no excluded bytes. Keep all decisive raw images and run `qa01_verify_frame_capture.py` separately. A full course still needs all original/native race frames and persistence/progression.
3. Independent QA supplies true/false attestations linked to exact original/native inputs and source artifacts. `tools/qa01_factory_preflight.py` combines the existing three merged diagnostic report schemas and an independent producer attestation. It returns a machine receipt with `hold` and exit 2 on incomplete/negative prerequisites. A fully positive result only returns `bounded_pilot_ready`, **maximum ten cases and no automatic dispatch**. These attestation booleans are a gate on already reviewed evidence, **not proof in themselves**; a dishonest `true` is not authenticated merely because the schema parsed.
4. Only then run one manual small original/native case population, not a new 10k frontier. Measure runner-minutes and retained bytes, exact new discrimination in source PC/read chains and actual state outcomes. Every experiment must record separate source/native clocks and independent original-checkpoint verification.
5. Consider 100 cases if a changed observer/producer yields a confirmed decision question; 1,000 only after a small observed cohort establishes a rare measurable feature or other named confidence threshold; 10,000 only on the existing fixed-cohort resumable mechanism after a 1,000-case result justifies it. [Measured escalation policy](QA-CUMULATIVE-RESEARCH.md#scientific-yield-escalation-and-stopping-2026-10-14) already forbids fingerprint-for-its-own-sake factories.

## New read-only admission check

Input attestation JSON requires `schema="ur-qa01-research-factory-preflight/1"`, immutable `source_sha`, `rom_sha256`, `movie_sha256`, `input_sha256`, and explicit boolean `checks` for source binary, native binary, controller reads, guest frame acknowledgments, phase qualification, no instrumentation perturbation, original clocks/unaltered input and unmasked retained memory. These claims must be independently backed by real signed/hashed source-owner evidence, not entered by guesswork.

```bash
python3 tools/qa01_factory_preflight.py \
  --attestation /tmp/qa01-independent-source-attestation.json \
  --causal-report /tmp/qa01-real-causal.json \
  --frame-report /tmp/qa01-real-frames.json \
  --independent-raw-report /tmp/qa01-independent-raw.json \
  --output /tmp/qa01-factory-admission.json
```

Every provided report is parsed fail-closed for the named schema and source/input relationship, non-promoting event verdict, actual unmasked frame counts and independent raw-byte comparison. The output carries SHA256 hashes of all input JSON and missing/negative conditions. A report is a **read-only readiness aid, not proof that the signed producer is truly original**. Do not modify `research/qa-cumulative-ledger` from this tool, and never add a new scheduled factory merely because the tool reports readiness.

## Ownership and nonduplication

- **CPU/APU:** executed-PC, original shared ordinal, actual causal guest reads/writes; gameplay correction only from genuine consumption evidence.
- **Continuous memory owner:** streaming/fail-closed raw frame producer and measured storage/runtime/noninterference, currently tracked by [PR #1904](https://github.com/gamesbyian/UR-Recomp/pull/1904).
- **Independent QA:** source/input/PE/ZIP/cold persistence and evidence attestation; QA01 remains 0/45 until independent complete event admission.
- **Factory maintenance (this lane):** lightweight admission semantics, reusable source-bound transport receipt, cost/yield policy and bounded manual dispatch. Do not modify guest instruments, acceptance authority or the cumulative evidence branch.

Existing seven-lane auto rotation remains unchanged, preserving Tuesday/Friday cadence, single-writer semantics, seed reservation policy and 20-runner account ceiling. The `original-native` campaign's historical incomplete producer needs targeted recovery before heavy coordinator runs. Default **no 1,000/10,000-case dispatch**.

## Independent QA provenance correction (October 19)

The initial preflight accepted independently shaped causal, frame and raw-verifier JSON reports from **distinct original/native experiments** whenever the top-level source code SHA matched. That was insufficient: the same Git commit can run different USA ROMs, 2014 input movies, actual supplied guest controllers, separate replay epochs or different capture windows and phases. The classifier previously allowed a synthetically forged "bounded_pilot_ready" for that mixed evidence.

The fixed CLI **re-opens** the actual original/native causal JSON event files through `qa01_causal_window.assess`, demands byte-for-byte equality of its result with the submitted causal report, and hashes both event files. The causal verdict now echoes the four **original/native previously validated** source/ROM/movie/input identifiers. A positive classification demands those match the attested inputs; matching source SHA alone is insufficient. Both actual guest checkpoint frames must belong to the submitted frame capture's range and declared phase. No cross-clock offset is inferred.

The CLI also requires `--retained-raw`, calls the merged independent `qa01_verify_frame_capture.verify` against the **actual full retained directory**, and demands the recomputed review equal its submitted JSON. A positive classification checks the canonical full fingerprint-report SHA256, original/native source identity, both host frame origins, complete relative interval, unmasked byte-occurrence totals, and retained raw manifest SHA256. This prevents an unrelated raw review from standing in for a missing frame report. Tests intentionally synthesize incompatible source-identical reports and assert refusal; direct `evaluate()` fixture green is not a real original/native execution or signed attestation.

For CLI use, add `--causal-original-events PATH --causal-native-events PATH --retained-raw DIR` alongside the existing four report inputs. Absence of these underlying sources is a **hard stop**, not a green based on a receipt claimed by its own producer. This enforces actual byte/manifest provenance *within the presented files*; it does **not** prove the collector observed every CPU bus event, a correct native executed guest PC, true joypad-poll consumption, external identity signatures, unretained equal-frame raw bytes, or a shipping Windows replay. The independent QA owner must qualify source executables/inputs and phase separately. Still only a maximum ten-case *manual research pilot*, never a USA release pass: **0/45 complete events, 0/12 QA gates**.
