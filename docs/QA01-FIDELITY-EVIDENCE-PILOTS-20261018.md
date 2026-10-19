# QA01 fidelity-evidence pilots: causal window and continuous frame audit

**Status (18 October 2026): ROM-free tools and adversarial tests proposed for review. Not a new original/native experiment, course witness, emulator, product implementation, accepted observation contract or QA gate. Complete USA events remain 0/45; release QA 0/12.** Method intake: [issue #1900](https://github.com/gamesbyian/UR-Recomp/issues/1900). Source authority: [first USA acceptance review](QA01-INDEPENDENT-FIRST-USA-EVENT-ACCEPTANCE-20261018.md). Live priority: [work queue](WORK-QUEUE.md).

These pilots target two recurring costs: (1) uncertain first *consumed* Zoo stack/sound divergence despite extensive existing RF043/045/046/047/053/054 receipts; (2) sparse 78-checkpoint coverage and expired source archives missing raw WRAM/SRAM bytes.

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

## Pilot qualification and stop/go

1. **Local unit stage:** `python3 -m unittest tests.unit.test_qa01_fidelity_evidence_pilots -v`; positive and negative fixtures exercise no ROM/emulator. CI green here means only schema/comparison contract correctness.
2. **Bounded actual A/B:** use one previously qualified Zoo window (early +1 or late +5034..5045). Require instrumented-versus-unaltered original and native control invariance, exact authenticated artifacts, recorder coverage and two true executed readers, or report the precise absent witness. No repeated generic RF055 sound survey.
3. **Continuous capture benchmark:** measure wall time and data footprint for full +0..+5163 actual source and native with source-acknowledged frames; no synthetic claim of speedup. All 78 established checks and +5163 result/+267 handoff must still be observed.
4. **Independent reuse:** one exact immutable captured source/guest artifact bundle, at least two independently computed verifications, with missing/truncated/modified member negatives. Only after this consider tightening the full-event acceptance route.

**Decision:** keep a pilot only if it closes a named QA01 uncertainty or measurably reduces time/data cost without weakening source, clock, byte or Windows-product requirements. Otherwise retire the tool or return to the established specialized RF scripts. No auto workflows or acceptance ledger change.
