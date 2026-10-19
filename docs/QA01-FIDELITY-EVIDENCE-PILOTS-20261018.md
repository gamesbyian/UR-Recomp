# QA01 fidelity-evidence pilots: causal window and continuous frame audit

**Status (18 October 2026): ROM-free diagnostic tools and adversarial tests merged to main as [#1901](https://github.com/gamesbyian/UR-Recomp/pull/1901) at `a36a1dc77e86cb90e03cb628b0fbc886c07ccff5` after both required CI workflows passed. Source/native producer adapters, actual bounded causal witness, full-race capture, noninterference benchmark and independent product acceptance remain unqualified. Complete USA events remain 0/45; release QA 0/12.** Method intake: [issue #1900](https://github.com/gamesbyian/UR-Recomp/issues/1900). Source authority: [first USA acceptance review](QA01-INDEPENDENT-FIRST-USA-EVENT-ACCEPTANCE-20261018.md). Live priority: [work queue](WORK-QUEUE.md).

These pilots target two recurring costs: (1) uncertain first *consumed* Zoo stack/sound divergence despite extensive existing RF043/045/046/047/053/054 receipts; (2) sparse 78-checkpoint coverage and expired source archives missing raw WRAM/SRAM bytes.

## RF061 executable-PC and local ordinal producer staging (19 October)

[RF061 producer qualification](RF061-ZOO-EXECUTED-PC-CAUSAL-PRODUCER-20261019.md) extends source-pinned RF045 with its own original macro ordinals and RF047 with opt-in native *actually emitted* decoded-opcode PCs across compiled M/X variants and interpreter fetches, including the previously missed live sound-upload M1X0 variant. A raw-log readiness auditor binds actual ZIP/log hashes and identifies gaps before the `qa01_causal_window.py` consumer; **it does not submit invented normalized rows**. The original source RF044 bus writer/checkpoint records still lack one shared event ordinal, and native helper-read PCs remain unbound to their actual bus instruction lifetime. There is no newly qualified source-authentic replay, raw checkpoint capture, gameplay fix or USA event promotion in this staging PR. **0/45 USA, 0/12 release QA.**

## Pilot A: ordered actual-bus causal consumer

`tools/qa01_causal_window.py` takes **separate** original and native JSON payloads. Each is strictly bound to a 40-digit source commit, 64-digit canonical USA ROM, movie and controller-input digests. The `window` declares relative frame start/checkpoint/end, the exact sampled observation phase, complete/nonoverflow recorder status and unmasked physical addresses. `observed` maps each address to its actual byte at that checkpoint. `events` contains individually executed, guest-local sequential bus `read`/`write` records with physical address, byte, guest opcode PC, local clock domain and clock, plus exactly one `checkpoint` event. The tool rejects gaps/duplicates, invalid bytes/PCs, cross-input identity, phase disagreement, missing completeness or inconsistent first reads. It never equates a source CPU clock to a native master/SPC/host clock.

For each address it reports a *last observed* writer before the checkpoint, first actual read **before the next write**, and first overwrite. Identical first-reader PCs with different actual values are an **investigation candidate**, not automatically the same logical instruction execution or a confirmed gameplay defect. A missing reader in a bounded window never proves that bytes are unused over a complete race. Report and input SHA-256 digests can be reviewed without substituting a claim for the actual original producer bytes.

The inputs are **a normalized consumer contract, not a claim that existing RF047/RF045 logs already contain all necessary source/native bus events**. Before the first authentic pilot the CPU/APU owner must qualify minimal read-only adapters for executed Snes9x stack macro accesses and Baldosa helper/bus accesses, preserving unique local recorder ordinals, actual PC and nontruncation. Existing RF047 native sequence reports and RF045 original NMI witnesses should be reused. Do not use interleaved stdout/stderr line order as native execution order.

## Pilot B: complete frame capture fingerprint / decisive-byte preservation

`tools/qa01_frame_fingerprint.py` takes two *existing* full-memory dump roots and a source identity JSON. Example:

```bash
python3 tools/qa01_frame_fingerprint.py \
  --identity /tmp/zoo-identity.json \
  --original-root /tmp/original-frames \
  --native-root /tmp/native-frames \
  --start 0 --end 5163 \
  --retain-raw /tmp/zoo-decisions \
  --max-retained 5200 \
  --output /tmp/zoo-frame-report.json
```

The identity file requires `source_sha`, `rom_sha256`, `movie_sha256`, `input_sha256`, `observation_phase`, distinct integer `original_frame_origin` and `native_frame_origin`, and both `masked_wram_bytes=0` and `masked_sram_bytes=0`. Input files must exist at each guest's real `frame_NNNNNN_wram.bin` (131072 bytes) and `frame_NNNNNN_sram.bin` (8192 bytes). Separate host origins are used without shifting the guest's input or implying CPU-instruction synchronization.

Every frame is required with no gaps. Each full raw image is SHA-256 hashed and raw bytes compared without masking; the report includes both real guest frame IDs, every input hash, first differing relative frame, per-frame and total unequal byte counts and a digest-chain checksum. When `--retain-raw` is provided, **every differing pair and the start/end pairs** is copied, independently rehashed and included in a raw evidence manifest. A cap is fail-closed, never silent sample loss. The tool never declares the source identity, binary, guest input consumption or Windows disk persistence independently authenticated merely because someone supplied a hash.

**Important limitation:** this is an offline auditor. It does not itself generate lighter per-frame hashes inside Snes9x/Baldosa, pause/replay efficiently or make full-frame dump capture cheaper. The next source owner must first measure production overhead and qualify identical observation phases with no guest-timing perturbation. Only then consider a streaming digest recorder with bounded mismatch ring buffers; retain enough original bytes for independent verification. Until then the tool works on existing compatible genuine files and ROM-free tests, **not** on the RF054 18-member archive lacking raw memory images.

## Pilot C: capture once, independently verify many

`tools/qa01_verify_frame_capture.py` independently reopens the retained full-WRAM/SRAM images instead of trusting the producer's JSON. It requires every differing relative frame plus boundary frames, all four source/native WRAM/SRAM members per retained frame, exact filename/frame mapping, file length, SHA256, digest-chain agreement and **recomputed unequal byte counts**. Missing, malformed, shifted, tampered or extra raw files fail the audit. Example: `python3 tools/qa01_verify_frame_capture.py --report /tmp/zoo-frame-report.json --retained-raw /tmp/zoo-decisions --output /tmp/zoo-independent-review.json`. The verdict explicitly leaves actual guest input/host acknowledgments, instruction parity, Windows persistence and 0/45 unchanged.

The pilot B JSON plus retained raw evidence can serve CPU, memory and QA consumers after source provenance checks. Do not commit bulk binary frames to Git or proclaim SHA lists as independently verified original evidence. The eventual producer/consumer flow should reuse `tools/evidence_contract.py` and the current source archive identity, not add a second release ledger, input translator, emulator, or Windows backend. Retain actual source binary/PE, original SMV, ROM fingerprint, true guest controller reads and raw archive SHA, with an independent reader recomputing relevant bytes. Source evidence already indicates [Bowl historical movie vs fresh original divergence](ORIGINAL-COURSE-EVENT-CENSUS.md); keep all three histories and clocks separate.

## First real archive inspection (RF054, 18 October)

Independently obtained [RF054 actual Zoo case archive](https://github.com/gamesbyian/UR-Recomp/actions/runs/39161563837/artifacts/12149640496) and recomputed its ZIP SHA256 `3ccb209a92045e9e89113442e68af51b85a453a160a9b9efaf8ca0d59e79631c`, plus the actual case, producer, original and native replay member digests. Machine-read-only inventory: [RF054 archive readiness report](../analysis/data/qa01-rf054-evidence-pilot-archive-readiness-20261018.json). Actual source replay has **1,806 RF045 original stack operations, 903 original bus write observations and nine NMI records** over hosts 1017..1025. Native replay has **2,741 exact-contiguous RF047 event ordinals**, including **2,705 executed helper reads, nine each of NMI entry/push/compiled RTI/return**. These are authentic, useful records, not synthetic logs.

**Precise blocker found:** the original RF045 macros have executed guest PCs but no shared event sequence number across all buses/checkpoint markers. All **2,705 native RF047 read records lack an actual guest opcode PC**; other `IPC` hints in the archive are historically stale, and some stderr/stdout fragments interleave. Neither side preserves a complete single-ordinal last-writer/first-reader/checkpoint timeline. Accordingly the new causal consumer must **not** fabricate normalized witness rows from this archive or declare the stack difference harmless. The next source-pinned probe is much smaller: add those missing fields to the *existing* RF045/RF047 instrumentation for the known nine-frame window, preserving original clocks, controls and raw bytes. No second emulator or wholesale trace rewrite is needed.

## Second authentic archive calibration: Bowl result→Switcher

Independently downloaded and SHA-256 checked the actual [Bowl run 39168164480 artifact 12151357791](https://github.com/gamesbyian/UR-Recomp/actions/runs/39168164480/artifacts/12151357791), ZIP `2924534f2700714c655647b43e2453c54d4e76f0e258566bcf500439d962ea79`. Reopened the actual **12 original + 12 native full 128KiB WRAM and 8KiB SRAM images** for result-relative offsets `334,338,339,340,341,342,343,344,345,346,349,354`. Compared every raw byte again: **3,041 observed differing WRAM byte occurrences and 36 SRAM byte occurrences** (three differing SRAM bytes per sampled offset), matching the established independent Bowl witness. [Small machine-readable calibration receipt](../analysis/data/qa01-bowl-genuine-sparse-raw-calibration-20261018.json).

This source archive is genuinely raw and independently checkable, but **not continuous**: offsets 335–337, 347–348 and 350–353 do not appear. Therefore the new full-frame auditor correctly cannot be given a pretend 334..354 complete input. This is a reusable real-archive calibration for raw comparison and missing-population guard design, **not a passing end-to-end continuous-capture test or source/guest behavioral fix**. A full-contiguous source producer and real replay benchmarking remain outstanding.

## Genuine eight-frame contiguous Bowl calibration (19 October)

The 12-offset Bowl archive contains one useful continuous interval: result-relative **+339 through +346 inclusive**, eight consecutive original/native raw WRAM+SRAM pairs. Independently reopened each of all **32 authentic files** (two guests × two memories × eight frames) and compared every raw byte: **2,747 WRAM and 24 SRAM differing-byte occurrences**. The source archive is independently verified by SHA256; the digest-of-per-file-digests for the eight-frame sequence is `e7629d3bd6f99a919ee6db53dd7f802778bcd05683ef39e03408d6b21eec729d`. [Machine eight-frame calibration](../analysis/data/qa01-bowl-authentic-eight-frame-calibration-20261019.json) retains each relative offset and actual unequal-byte count. This supplies **real contiguous source data** for a bounded pilot compatibility check, without replaying the game. It does not establish the same emulator observation phase beyond the archive's existing witness, verify source instruction/button-consumption equivalence, qualify either course in full, or turn Bowl's strict progression failure into a pass. A complete genuine full-race capture remains outstanding.

## Integration qualification and CI repair (19 October)

The earlier branch CI unit run [39200843454](https://github.com/gamesbyian/UR-Recomp/actions/runs/39200843454) failed **only** the two existing document-bound tests: `docs/WORK-QUEUE.md` measured 17,268 characters against the under-16,000 policy. All three other unit shards passed, and the failing shard reported 940 tests with those two failures. The work queue has now been condensed to **15,439 characters**, retaining live gate priorities and relocating historical details to [#1899](https://github.com/gamesbyian/UR-Recomp/issues/1899). **Resolved:** the subsequent head `4ad22654031e6fe49ec6fbca1cdf9ec00dcd5a73` passed both Repository hygiene and Project tooling unit tests, and was squash merged as #1901. The pilot's ROM-free test coverage remains a separate qualification from the genuine evidence-producer demonstration.

## Pilot qualification and stop/go

1. **Local unit stage:** `python3 -m unittest tests.unit.test_qa01_fidelity_evidence_pilots -v`; positive and negative fixtures exercise no ROM/emulator. CI green here means only schema/comparison contract correctness.
2. **Bounded actual A/B:** use one previously qualified Zoo window (early +1 or late +5034..5045). Require instrumented-versus-unaltered original and native control invariance, exact authenticated artifacts, recorder coverage and two true executed readers, or report the precise absent witness. No repeated generic RF055 sound survey.
3. **Continuous capture benchmark:** measure wall time and data footprint for full +0..+5163 actual source and native with source-acknowledged frames; no synthetic claim of speedup. All 78 established checks and +5163 result/+267 handoff must still be observed.
4. **Independent reuse:** one exact immutable captured source/guest artifact bundle, at least two independently computed verifications, with missing/truncated/modified member negatives. Only after this consider tightening the full-event acceptance route.

**Decision:** keep a pilot only if it closes a named QA01 uncertainty or measurably reduces time/data cost without weakening source, clock, byte or Windows-product requirements. Otherwise retire the tool or return to the established specialized RF scripts. No auto workflows or acceptance ledger change.

## QA-only causal pilot consistency tightening (19 October)

The `qa01_causal_window.py` **offline executed-bus consumer** now refuses an internally impossible last-writer history in a `window.complete=true` event stream. Previously it verified only reads *after* its checkpoint until overwrite. A forged trace could claim the last observed source write to `7E:01ED` was `25`, raw checkpoint `26`, and next read `26`, and the consumer would accept an apparently complete writer→checkpoint→reader chain. Given complete physical-address observation within that bounded timeline, the last write must equal the actual checkpoint byte unless another writer was omitted. That failure is a producer coverage/observation-phase defect, **not an original/native fidelity verdict**.

The checker now maintains a per-address shadow of actually witnessed bus writes, seeds unknown initial bytes **only at the declared raw checkpoint**, enforces all later reads against the latest write/checkpoint (including reads after a subsequent overwrite), and rejects host-frame regressions across a guest-local ordered event stream. It keeps independent per-clock-domain monotonicity and never aligns original/native clock axes. Unknown writers outside the bounded start remain unknown, not fabricated evidence. Negative ROM-free tests exercise a wrong precheckpoint last writer, an invented precheckpoint read, a stale read after an overwrite, a backwards host frame, and the valid unknown-initial-writer control.

**Scope and acceptance:** consistency of a claimed complete event sequence is necessary but insufficient. The consumer cannot attest that original RF045 and native RF047 instrumentation really captured every physical bus writer/reader or actual native executed guest PC; it cannot reopen omitted raw checkpoint WRAM or verify source CPU controller reads. CPU/APU owner must still supply the authentic single-ordinal original events and real native executed PC fields identified in the RF054 archive readiness receipt. Do not use synthetic validator green as a substitute for executing that authentic bounded experiment. Zoo result +5163, next Bowl +267, 78 original/native WRAM controls, source clocks, full SRAM and Windows product acceptance remain unchanged. **0/45 events, 0/12 release gates**, no gameplay/timing/byte-mask change or recurring workflow.

## Independent raw-verdict provenance binding (October 19, QA reviewer)

An independently re-opened raw-frame receipt now carries `fingerprint_report_canonical_sha256`, a full copy of the **exact** `frame_source_identity`, `verified_relative_frame_window` (start/end/count, phase, original/native independent host origins) and `retained_raw_manifest_canonical_sha256`. Each digest uses deterministic sorted-key compact ASCII JSON, not a digest of pretty-print whitespace. The producer's report has already passed full-row/retained-raw consistency tests; the retained manifest's claimed hashes were independently recomputed from the actual raw images before the receipt was emitted.

**Downstream rule:** An acceptance/factory preflight must independently canonical-hash the **specific supplied frame fingerprint report** and compare it against the receipt field, verify all immutable original/native inputs and observation phase/coverage, and preferably call `qa01_verify_frame_capture.py` itself against the actual raw directory. Matching `source_sha` alone is insufficient: two real original/native runs of the same code may contain different ROM/movie/inputs or nonoverlapping capture windows. A producer's JSON and purported auditor JSON are not signatures; an attacker able to fabricate the raw data and reports could fabricate these hashes too. No extra certificate of original actual pad polls, source-executed clocks, unretained interior memory equality, Windows cold storage or complete-USA event was created. Cross-binding `qa01_causal_window.py` also requires genuine original/native event-file identity, not merely matching source SHA. **0/45 USA; 0/12 release QA.**

## Opt-in source-acknowledged per-frame producer bridge (19 October)

**Engineering scope:** `tools/probe_original_event_complete.py` now accepts `--qa01-frame-start N --qa01-frame-end M --qa01-frame-max-retained K` on the existing genuine original Snes9x / pinned Baldosa same-controller replay. The CLI adds one `dump qa01-frame-NNNNNN` at *every* requested race-relative frame, preserving existing scene/result checkpoints, actual guest input and frame clocks; when the capture extends beyond the last sparse scene checkpoint, its added **explicit** frame waits replace frames formerly advanced implicitly by the result `until` predicate. The sum of literal `wait` commands therefore changes for a full race and is not a valid noninterference criterion. No ROM, SRAM, CPU opcode, byte mask or controller-input edit is introduced. The bridge `tools/qa01_frame_capture_replay.py` refuses missing/duplicate/out-of-phase acknowledged host frame labels, absent/truncated memory images or mismatched source/native relative clocks. It hardlinks temporary input names, runs **the merged pilot's actual** full unmasked comparison and copy-on-difference/boundary retention, then invokes its independent byte-level raw verifier. Each side's observed race-entry host frame is kept distinct; record/log/binary/source/movie/script digests are retained in the normal per-case report plus `replay/qa01-frame-evidence/`. The pilot `input_sha256` is bound to the archived **actual 2014 movie controller-window digest**, while the replay command script and the two actual supplied per-guest input files receive **separate** SHA-256 fields; none asserts real CPU joypad-poll equivalence. Only already-acknowledged script dumps count. Reusing the same ROM/SMV/controller stream does **not** prove what the CPU actually polled.

**Reproducible real-data qualification:** `tools/qa01_qualify_authentic_bowl_frames.py --archive /path/to/genuine-Bowl-12151357791.zip --output /new/bowl-qualification`. It first pins SHA-256 `2924534f2700714c655647b43e2453c54d4e76f0e258566bcf500439d962ea79`, then reopens 32 real original/native unmasked memory images, *and* the two actual dump-acknowledgment logs. The requested interval is result-relative +339..+346 (eight consecutive points); **extra legitimate +334/+338/+349/+354 archive observations are allowed**, but missing any interior member or host frame is rejected. Original/native result onset was each actual host frame **4349**, so +339..+346 are hosts 4688..4695; this is **not** the race-entry clock. Expected 2,747 WRAM and 24 SRAM differing-byte occurrences, and digest chain `e7629d3bd6f99a919ee6db53dd7f802778bcd05683ef39e03408d6b21eec729d`. Real ZIP independent byte census was separately recomputed; the new reproducible script/CI invocation is the explicit integration contract and must be executed and its receipt reviewed before claiming end-to-end pilot qualification. Pinning the archived ZIP does not reopen the absent archived emulator binaries.

**Storage baseline:** both full memories = **278,528 bytes per paired frame** (2 guests × [131,072-byte WRAM + 8,192-byte SRAM]). Eight real paired frames = **2,228,224 uncompressed bytes** across 32 source images, compared byte-for-byte. The archived complete 62-member ZIP was **398,053 bytes**, but that compression ratio is scene/data-specific and must not be extrapolated. A fully inclusive race-relative **0..5163** Zoom Zoo window holds **5,164 paired frames** and requires at least **1,438,318,592 bytes (1.340 GiB)** for WRAM/SRAM images *alone*, before scene VRAM, CGRAM, logs and retained decision bytes. The local **eight-frame** Python archive read/hash/diff baseline was approximately **0.045 s**, excluding emulator, archive download, ZIP extraction and any new producer runtime; a separate local bridge dry-run against those authentic images (using compatible ROM-free local pilot stand-ins) staged, hashed, retained and checked in about **0.095 s**. These timings are **not** claims of the actual merged pilot runtime or of an instrumented/uninstrumented replay speedup. Real per-guest wall timers now exist in the producer's evidence report when opt-in capture runs; compare with an identical source-bound capture-off replay before declaring acceptable overhead.

**Full-race next bounded execution:** once cost-qualified, the complete Zoo race-relative interval `0..5163` (source-authentic result onset +5163) can be requested explicitly, with a sufficiently high fail-closed cap such as `--qa01-frame-max-retained 5164`. At frame 0 the new tag is sampled directly after the stock `race-entered` dump; at +5163 it is sampled directly after the actual guest `result-onset` predicate without waiting an assumed result clock. A guest that arrives at the result early/late therefore **fails** the expected host-frame acknowledgment rather than being silently rephased. The next Bowl +267 remains existing separate handoff evidence when enabled; **continuity across every post-result/handoff frame, actual pad CPU reads, emulator opcode equivalence and same-phase semantics are not yet demonstrated**. A mismatching frame is never masked or silently omitted merely to stay below the retention cap. Run a nine-frame genuine Zoo +5034..5042 captured-on/off A/B first; do not dispatch a 1.34-GiB replay based on these offline measurements alone. No automatic CI research workflow, guest behavioral edit, 45-event census promotion or Windows shipping claim follows from this change.


**Ack hardening (October 19):** source Snes9x must provide `fb=WIDTHxHEIGHT FORMAT sram=8192 ppuw=N`, while native Baldosa must provide `ok`; a stray, failed or duplicated tag alone never counts. These distinct log formats were independently checked against all 12 original and native checkpoint acknowledgments in the pinned Bowl ZIP. The true +339..+346 interval is the eight-frame calibration, not a complete race.


## Bounded capture-off/on noninterference control (19 October, PR #1904)

Before invoking any multi-gigabyte race dump, run one **genuine** source-bound Zoom Zoo original/native pair with capture off and a second replay at exactly `--qa01-frame-start 5034 --qa01-frame-end 5042 --qa01-frame-max-retained 9`; both replays must use the **same** branch commit, original retail USA ROM SHA, 2014 source SMV/controller window, source SRAM, reference Snes9x core binary, pinned native ELF and preexisting source-derived input events. Repeat only if a strict observed clock/source-input gate fails for a diagnosable reason, not to search for an advantageous phase alignment. The `--qa01-frame-start/--qa01-frame-end` settings apply to race-relative frames, never the 2014 movie absolute frame.

The producer now emits `qa01_capture_ab_control` on **both** ordinary and captured runs, independently identifying exact Git source commit, original movie controller-window hash, both **actual supplied guest input-file** hashes and lengths, both guest-log hashes, reference/native script hashes, capture-on marker, and separately timed guest replay wall seconds. Merely matching the per-guest command scripts would be insufficient (their dump directives intentionally differ). The original source event, both guest semantic checkpoints, native/retail identity, scored result, and optional same-input onward progression must all remain exactly comparable.

After capturing and independently retaining the raw memory, use:

```bash
python3 tools/qa01_verify_capture_ab.py \
  --baseline /real/capture-off/zoom-zoo-report.json \
  --captured /real/capture-on/zoom-zoo-report.json \
  --fingerprints /real/capture-on/replay/qa01-frame-evidence/fingerprints.json \
  --retained-raw /real/capture-on/replay/qa01-frame-evidence/retained \
  --baseline-original-log /real/capture-off/replay/reference.log \
  --baseline-native-log /real/capture-off/replay/native.log \
  --captured-original-log /real/capture-on/replay/reference.log \
  --captured-native-log /real/capture-on/replay/native.log \
  --output /new/qa01-zoo-capture-ab-review.json
```

This separate **read-only** reviewer fails on altered source/ROM/SMV/SRAM/native/core IDs, any changed original/native *supplied* controller file SHA/length, moved result/guest checkpoint/earnings/progression, wrong source frame origins, gap/duplicate frame population, any unretained differing raw frame, mismatched forensic digest, or a self-awarded course pass. It independently calls the existing raw-frame verifier and reports **separate** observed wall-time overhead for original and native. It does not attempt to compute missing actual CPU controller reads from the supplied file, retime CPU/SPC clocks, or promote an event. The accompanying synthetic unit tests are negative contract fixtures, **not** evidence of a source-authentic replay.

The separate `.github/workflows/qa01-authentic-frame-qualification.yml` is a deliberately lightweight **archive-only** test: it fetches the exact historic Bowl artifact `12151357791`, rechecks ZIP SHA-256, reopens all 32 genuine full memory images and original/native successful dump log acknowledgments over the eight consecutive result-relative frames +339..+346, invokes the merged fingerprint/independent verifier pipeline, uploads only compact reviews, and gives **zero** event credit. It does not run game binaries or launch a long research factory. Keep the workflow's pin, immutable case hash and source log format strict. After the 7-day source-artifact expiration, it must fail closed or be replaced with a properly archived verified immutable source ZIP rather than silently substituting fixture data.

**Promotion gate:** require passing **real** archive workflow, real identical-producer nine-frame capture-off/on timing/semantic invariance and independently verified unmasked retained bytes before authorizing the larger full-race memory producer experiment. A bounded capture whose result is a legitimate mismatch is a diagnostic, never an acceptance pass. The existing stricter all-frame, full-game, true pad-poll, CPU/APU causality, Windows PE, cold persisted record and QA01 acceptance requirements remain unchanged at **0/45**, release **0/12**.


### Authenticated archive-pilot promotion receipt

The *exact* code on archive-pilot PR commit `d00101e611b24dee31b1a9066f64d87fa3c1f476` passed [Actions run 39210769847](https://github.com/gamesbyian/UR-Recomp/actions/runs/39210769847) on **19 October** (workflow artifact `12167164045`, 3 compact JSON files). Independent reinspection of that completed workflow artifact confirmed the original 62-member ZIP hash `2924534f2700714c655647b43e2453c54d4e76f0e258566bcf500439d962ea79`, 8/8 source and native host ACKs, all 32 genuine unmasked raw WRAM/SRAM members reopened, 2,747 WRAM and 24 SRAM unequal-byte occurrences, full digest chain `e7629d3bd6f99a919ee6db53dd7f802778bcd05683ef39e03408d6b21eec729d`, and **0** omitted digest-only interior equal frames within this eight-frame interval. The original/native guest result-onset host frame was **4349** in both logs; the eight compared result-relative hosts were 4688..4695. The independent verifier deliberately reports `actual_guest_frame_acknowledgments_verified=false` because its *own* scope is reopened raw images; the separate producer bridge verifies both real log ACK syntaxes. The archive verifier never claims actual CPU pad-poll or full-course instruction parity.

The measured **offline consumer overhead only** was 0.0019 s to stage existing captures by hardlink, 0.066393 s to fingerprint/compare/retain, and 0.060596 s to independently rehash retained images for the eight-frame sample (128.889 ms total excluding ZIP extraction and game execution). Retained 2,228,224 bytes uncompressed; compression and observed storage ratios remain scene-dependent. The separate producer on/off runtime measurement and full-course frame coverage are **still unproven**.

The single bounded `qa01-zoo-frame-ab-once.yml` workflow is a 9-frame source/native Zoom Zoo producer **experiment**, not an autonomous factory. Its bounded 5034..5042 capture-off/on runs must preserve the 2014 controller movie, two supplied guest input files, core/ELF pins, 78 prior Zoo mesh checkpoints, scored result +5163, source next-Bowl +267, source-local clock axes, and full raw unmatched bytes. It blocks game builds if the genuine archived Bowl qualification or ROM-free A/B gates fail. Its output is never USA-event credit.


### Source-authentic Zoom Zoo nine-frame capture A/B: actual qualification (19 October)

At exact PR merge-source commit `a238df6edfff6893e6986e4ebb43af949069b620`, [Actions run 39211385737](https://github.com/gamesbyian/UR-Recomp/actions/runs/39211385737) **succeeded** on the one-shot live original Snes9x vs pinned native Baldosa capture-OFF/ON test. The immutable diagnostic artifact is `12167633197`, downloaded ZIP SHA-256 `be72834ac617da8dfb96c591e06efaa18adbfe7d872cc64f6a306d3db8db0765`; the on-run report SHA-256 is `2ce7c4bb092f616868273ca52876386a1b3a8fc380e0b6159bedfd8233d9712b`; the on-run fingerprint report SHA-256 is `12932551b24cc7542d8dba105e98bae4c8efa5cf626cc3ea504f482c570400f7`.

The separate original and native source-guest origin clocks were +1017 and +1019, respectively. All nine guest frame-success ACKs at race-relative +5034..+5042 map to **original actual host 6051..6059** and **native actual host 6053..6061**. The bounded verifier passed with `existing_semantic_observations_unchanged=true`, `same_source_controller_and_binaries=true`, `same_supplied_original_native_input_bytes_digest=true`, and 0 credit. The exact source movie controller input SHA and both supplied controller-file hashes were identical between ON/OFF. All standard 78 Zoo samples, result/menu and requested next-Bowl passage retained their previously observed state; paired-event criteria still fail. The two producer exit codes were **1** in both treatment arms, indicating ongoing strict original/native parity failure, not capture instrumentation failure.

Actual single-run per-guest replay wall times, captured minus baseline:

| Guest | OFF | ON | Difference | Relative difference |
|---|---:|---:|---:|---:|
| Original Snes9x | 4.837964 s | 4.863855 s | +0.025891 s | +0.535% |
| Native Baldosa | 109.049805 s | 109.079837 s | +0.030032 s | +0.028% |

These **single unpaired sequential runtime measurements** establish feasibility at this small sample, not statistical confidence, stability under repeated runs or the overhead of ~5,164 full-race snapshots. Frame evidence staging 0.002085 s, full image hash/compare/retention 0.049081 s and second-party revalidation 0.048190 s, separate from guest replay. Captured 9×2×(131072+8192) = **2,506,752 full input memory bytes**, retained **2,228,224 bytes** (8 differing/boundary full pairs). The nine-fingerprint chain is `759c24c1cc87072c8abb188fb210879e4ff600c4e0461907162e5dc13d457a5c`, with **13 WRAM** unequal-byte occurrences and **0 SRAM** unequal-byte occurrences. No byte masks.

The first-ever source-authentic contiguous original/native 9-frame memory census for this interval found these exact per-frame *memory* differences:

| Race-relative frame | Unmasked differing original/native WRAM byte values |
|---:|---|
| +5034 | `7E:01EE F0 / EE` |
| +5035 | `7E:01EE F0 / EE` |
| +5036 | `7E:01EE F0 / EE`; `7E:01F1 F4 / FB` |
| +5037 | `7E:01EE F0 / EE`; `7E:01F1 F4 / FB` |
| +5038 | `7E:01EE F0 / EE` |
| +5039 | equal original/native full-memory SHA-256 (interior raw images not retained in original artifact) |
| +5040 | `7E:0063 73 / 77`; `7E:0069 BE / C1` |
| +5041 | `7E:0063 4D / 51`; `7E:0069 97 / 9C` |
| +5042 | `7E:0063 27 / 2C`; `7E:0069 71 / 76` |

Totals by physical address: `7E:01EE` 5, `7E:01F1` 2, `7E:0063` 3 and `7E:0069` 3. The first two join the historical Zoo DP/stack residual census; **`7E:0069` is a new observed lead** in this window, and `7E:0063` now has a companion with a changing paired value. The equal observation at +5039 does not prove opcode-level reconvergence. Nothing here establishes which mismatch the gameplay subsequently *consumed*; RF045/047/061/063 must source-authentically capture writer/read ordinals and executed native guest PCs on the relevant physical bus, without frame-axis shifting.

**Independent raw caveat and upgrade:** The original passing archive independently reopens all eight differing/boundary source/native raw frame pairs; +5039 is a genuine original/native equal **digest-only** pair, not two independently archived raw images. This is not an acceptable basis for claiming a *fully independently re-openable nine-frame archive*. The branch has therefore been hardened to opt into **all-frame retention** whenever a continuous window fits `max_retained`, and the separate independent verifier now requires every raw image of that scope, with an adversarial altered-equal-middle-frame negative test. The archived old nine-frame result is immutable and is **not retroactively upgraded**. A future actual source capture with revised code is required to validate the stronger all-nine raw scope; do not pretend the old receipt met it. For 5,164-frame captures the explicitly limited old rule still retains all differing and boundary frames, with honest separately reported digest-only equals. The 9-frame A/B only promotes the *bounded capture-on/off noninterference and feasibility technique*, **not** all-frame course equivalence or a release gate.

Because the one-shot native build and replay already succeeded and was costly relative to the small memory payload, `.github/workflows/qa01-zoo-frame-ab-once.yml` is now **manual-only**; it will not rerun on every PR change or bootstrap/toolchain update. A newer heavy campaign should require a named hypothesis and explicit scope, not run just to improve this project's green CI percentage. **Acceptance remains 0/45 events and 0/12 QA gates**.


### Guest-log archival provenance tightening (19 October, after first A/B)

The one-shot A/B artifact `12167633197` preserves the raw frame images, fingerprints, producer A/B controls and verdict, but **does not include the four original/native replay guest-log files**. Thus the historic independent A/B JSON's 9 successful ACK count relies on the producer bridge having checked the logs at execution time; a third-party auditor reopening *only that ZIP* cannot independently repeat the log-ACK check. The old passing artifact is **not retrospectively promoted** to independently archived guest ACK proof.

The hardened `qa01_verify_capture_ab.py` now accepts and, in its CLI, **requires** four real guest log files, two for baseline and two for captured, rehashes each against the corresponding actual producer control, checks the captured-side additional recorded log hashes, parses every original Snes9x `fb=... sram=8192 ppuw=N` and native Baldosa `ok` success, and verifies every exactly positioned frame relative to the independently declared *separate* guest origin clocks. It rejects missing, shifted, forged-success or edited guest logs even when the edited logs' own new hashes were substituted into the producer JSON. The one-shot manual workflow is updated to preserve these four logs in any future archive, along with **all original/native full raw WRAM and SRAM frame images** for a window within its retention budget. Existing A/B reports without raw guest logs can still be inspected programmatically, but the new verdict explicitly marks `captured_successful_guest_acknowledgment_logs_independently_reopened=false` and cannot be used as fully independently re-openable archive evidence. Independent source CPU pad polls and between-frame guest opcode causality remain unproven.


## Independent source-bound temporal delta atlas (19 October follow-up)

The merged source-authentic pilot #1904 left a low-cost next question: which *actual raw* original/native bytes changed at a named frame, and which guest changed them since the prior raw-observed frame? The new ROM-free `tools/qa01_frame_delta_atlas.py` consumer accepts the already-authenticated `frame-fingerprints.json` and retained original/native images; it first invokes the existing independent raw verifier, then emits an address-level cross-guest census and per-guest previous-frame change counts. It accepts up to 200 scoped frames by design and uses a fail-closed explicit `--max-deltas-per-frame` rather than truncating source differences.

```bash
python3 tools/qa01_frame_delta_atlas.py \
  --fingerprints /real/original-native/fingerprints.json \
  --retained-raw /real/original-native/retained \
  --output /new/qa01-raw-delta-atlas.json
```

**Never invent equal-frame source memory from a digest.** The original Zoo +5034..+5042 artifact `12167633197` retained eight differing/boundary raw pairs and only the fingerprint digest for equal +5039. The atlas must therefore report that interval as `equal_by_digest_only_source_pair_not_reopened`, with null per-byte and intra-guest transitions. It must not bridge transitions across this interval or claim independently reopened data where none was archived. The newer all-frame-small-window retention added by merged #1904 allows a future genuine nine-frame artifact to include +5039; that should yield a complete atlas with all nine rows independently reopened. Both modes preserve separate original/native actual host frame origin IDs; no cross-clock alignment.

The output names each observed physical address (`7E`/`7F` WRAM, `SRAM` offset), exact original and native byte values at each retained pair, source-provenance fingerprint canonical SHA-256, total WRAM/SRAM byte-difference occurrences and the number/identity of equal digest-only unarchived frames. It distinguishes an observed differing frame from the **first genuinely consumed** CPU/SPC divergence, which cannot be inferred from snapshots alone. The source RF061/062/063/064 writer/reader owner must provide real guest executed PCs and original event ordinals to establish cause. This is an analytical accelerator, not new full-course coverage, proof of intervening opcodes, event admission, a research factory, or a release gate. **0/45 events; 0/12 QA release gates**.


### Real original Zoom Zoo ZIP integration: source-bound delta atlas (19 October)

The atlas has a separate **exact immutable original/native archive** entry point which first independently re-opens the complete A/B primary evidence with `qa01_independent_zoo_capture_ab_archive.verify` (already on main), checks pinned SHA256 `be72834ac617da8dfb96c591e06efaa18adbfe7d872cc64f6a306d3db8db0765`, source/game states, true input-file identity and all 32 retained raw images, then re-derives the temporal atlas. Run:

```bash
python3 tools/qa01_zoo_archived_frame_atlas.py \
  --archive /verified/actions-39211385737-artifact-12167633197.zip \
  --output /new/zoo-source-authentic-frame-atlas.json
```

[Actions run 39218213121](https://github.com/gamesbyian/UR-Recomp/actions/runs/39218213121) independently passed **both genuine Bowl and original Zoo A/B archive** source re-openings on the same code. It retained the readable `independent-atlas.json` as artifact `12170068734`; this is *not* a new emulator execution. The strict original Zoo output confirms 9 frame positions (+5034..+5042), **8 raw reopened pairs, 1 unarchived digest-only equal pair at +5039**, 13 unmasked WRAM occurrences at exactly four physical addresses, and zero SRAM differences:

| Address | Occurrences; frames | Actual original/native bytes |
|---|---|---|
| `7E:01EE` | 5; +5034..+5038 | F0 / EE throughout |
| `7E:01F1` | 2; +5036..+5037 | F4 / FB |
| `7E:0063` | 3; +5040..+5042 | 73/77, 4D/51, 27/2C |
| `7E:0069` | 3; +5040..+5042 | BE/C1, 97/9C, 71/76 |

The new **same-guest raw transition census**, compared against the prior *retained* full-frame images, demonstrates **zero** WRAM/SRAM changes inside either guest from +5034 to +5035 or from +5036 to +5037; at +5036 only native WRAM changes by one byte, and at +5038 native WRAM changes by one byte. The old archive's +5039 source/native raw images were **not retained**, so a real transition into +5040 cannot be computed: both guest change fields are `null`. At +5041 and +5042, **both** original and native WRAM each change at three byte positions per adjacent observed frame (SRAM unchanged), even though original-vs-native differences at each of those frames involve only two addresses. This distinction is factual byte observation, not a causal inference.

The experimental original and native guest-local host origins remain **1017/1019**; never cross-align them. No actual original/native guest execution log bytes, original CPU joypad bus reads, opcode writer/read ordinals, or shipping Windows persistent-record witness can be reconstructed from the old archive. In particular, the zero-byte within-guest changes at two sampled boundaries do **not** establish absence of transient or between-dump CPU/APU state changes. This atlas exists to focus RF061/062/063/064 physical-bus investigations on witnessed changing bytes rather than create game code or acceptance credit: **0/45 events; 0/12 QA gates**.


## Actual supplied original/native controller stream re-opening (October 19)

Merged authentic Zoo capture A/B #1904 established that ON and OFF replays supplied identical *per-guest* input file hashes/lengths, but original and native input files intentionally differ as raw text. The original Snes9x transport writes `START:DURATION:MASK_HEX`; the pinned native Baldosa transport writes `(START + native_entry - original_entry):DURATION:MASK_HEX_3_DIGITS`. The native non-pinned transport may include a fourth `:0` field. Raw SHA equality **across different guests** is therefore not an appropriate acceptance criterion; the actual source-relative mask, onset, and duration tuples must match instead. These input files encode *supplied* controller events only, never the executed CPU joypad read trace.

The new ROM-free `tools/qa01_verify_supplied_controller_streams.py` independently opens all four real ON/OFF guest input files (not just stored SHA fields), enforces canonical ASCII/line structure, nonzero SNES masks, ordered nonoverlapping intervals, real individual guest race-entry origins, exact producer-reported file sizes and SHA-256, and byte-identical original OFF/ON plus native OFF/ON file contents. It then independently subtracts each guest's **own observed race-entry host frame** and compares the resulting event tuples (relative onset, duration, hexadecimal mask) between original and native. It fails closed on modified mask, shifted/relabelled start, wrong endpoint, symlink/missing input, improper native transport syntax or any attempted CPU-input-consumption claim. No source ROM, gameplay code, save file, emulator, frame clock, actual input events, artifact factory or release gate is modified.

Example using future **real** persisted guest files (these were *not* retained by the historical successful archive `12167633197`):

```bash
python3 tools/qa01_verify_supplied_controller_streams.py \
  --baseline /real/zoo/capture-off/producer-report.json \
  --captured /real/zoo/capture-on/producer-report.json \
  --off-original-input /real/zoo/capture-off/replay/ref.input \
  --off-native-input /real/zoo/capture-off/replay/pinned-baldosa.input \
  --on-original-input /real/zoo/capture-on/replay/ref.input \
  --on-native-input /real/zoo/capture-on/replay/pinned-baldosa.input \
  --output /new/qa01-independent-supplied-input-streams.json
```

The receipt also retains **every** independently normalized source-relative start/duration/mask segment plus a canonical SHA-256 for direct future comparison against witnessed CPU joypad read ordinals; it never invents zero-mask events in between nonzero segments. The already manual-only `.github/workflows/qa01-zoo-frame-ab-once.yml` now retains these four small actual input-file artifacts and runs this independent check before publishing a verdict. The original successful 19 October archive does **not** contain them and can never retrospectively qualify independent reopening. Reproducing the source-2014 SMV controller window from the full movie and tracing actual executed original/native joypad polls remain separate uncompleted evidence gates. This verifier upgrades supply-path reproducibility only; it cannot prove guests *consumed* those masks, game-state equivalence, a complete race, true causal divergence, 45-event admission or Windows shipping persistence. **0/45 original USA events and 0/12 release QA gates.**
