# One original/native Zoo +5040 replay-reduction intake

**Status:** private QA01 diagnostic intake, not a release acceptance gate. This tool consumes actual source-owned producer bytes and does not execute a ROM, generate source observations or award 1/45 course credit.

The existing manual QA01 workflow and probe_original_event_complete.py remain authoritative. For a single bounded source-qualified test, select zoom-zoo, enable zoo_race_mesh, zoo_dp_window, RF-015 (baldosa_refresh_beam_rate) and RF-017 (baldosa_io_clock_order). Disable RF-016/RF-018/RF-019 and other staged corrections. Preserve actual movie SRAM, original Snes9x, native, host clocks, source/ROM hashes and complete +5039/+5040 WRAM. Do not infer missing evidence from a sibling run.

Run this helper on the **same successful source checkout**, using the actual case and binary root:

    python3 tools/prepare_qa01_zoo_reducer_pilot.py \
      --producer /private/qa01-case/producer-report.json \
      --case /private/qa01-case/work/zoom-zoo \
      --binaries /private/qa01-binaries \
      --rom /private/Uniracers_USA.sfc \
      --movie /private/dessyreqt-4250-submission.smv \
      --source-sha "$(git rev-parse HEAD)" \
      --output-manifest /private/reducer/paired.json \
      --output-input /private/reducer/original.input \
      --output-receipt /private/reducer/intake.json

The intake refuses a wrong Zoo producer, ROM/SMV/SRAM identity mismatch, changed core/native/observer hashes, unqualified original/native race entry, mismatched supplied P1 input after source-earned two-host-clock shift, missing logs or wrong observed guest frame, nonidentical whole +5039 WRAM, any +5040 difference outside $0063/$0069, or wrong active Zoo track/race state. It validates all 131072 bytes per original/native image and derives the *current* target-byte values from this exact producer. Historic 0x73/0x4D values cannot be force-fitted.

**Per-candidate preservation check:** the generated private oracle now binds the full exact source +5039 WRAM SHA-256 (\`pre_target\` = \`scene-05039.wram.bin\`). Every candidate must independently capture this prior checkpoint from **both** guest subprocesses, each at its own authenticated +5039 host frame, and both 131072-byte buffers must have the exact source-qualified digest. Matching only the +5040 target byte and a few stage anchors cannot reproduce the original source circumstance. A candidate that changes earlier game state is rejected as \`invalid_route\`, even if the two +5040 bytes coincidentally match. This is intentionally conservative: a source-equivalent earlier state may prevent large reductions, and late +5040 equality does **not** itself prove the first instruction-level causal divergence.\n\n**Two-byte postcondition:** each reduced Zoo candidate must also reproduce the original +5040 *complete differing-byte set*: exactly `$0063` and `$0069`, with the source-qualified original and native values at both offsets. A candidate that preserves only the primary `$0063` byte, loses `$0069`, or develops any third WRAM difference is classified `not_reproduced`, even if its +5039 source state remains identical. This is a conservative, source-specific guard on the existing same-frame mismatch, not proof of the first opcode-level causal writer.\n\nOnly after the authentic source preflight succeeds, start **one** bounded reduction:

    python3 tools/reduce_controller_fixture.py \
      --input /private/reducer/original.input \
      --output /private/reducer/minimal.input \
      --report /private/reducer/minimal.json \
      --protected-before-frame ORIGINAL_REFERENCE_ENTRY \
      --max-calls 12 --repeats 2 --timeout 120 \
      --oracle python3 tools/qa01_reducer_paired_oracle.py \
      --manifest /private/reducer/paired.json

Use the actual manifest guest_clocks.reference_entry_frame for ORIGINAL_REFERENCE_ENTRY. Historical entries 1017/1019 are *not defaults*. The manifest includes the exact source observer script, separate host frames and SRAM, SHA-pinned original/native binaries and native_xvfb=true. No ROM, SRAM, SMV, original input stream or private saves should be uploaded. Hash-only decisions still need actual CPU input-poll and causal writer/consumer verification. Synthetic test fixtures grant zero gameplay or Windows release credit.

**Candidate route loss is an ordinary negative, not an experiment crash.** On an input-row removal, the authentic QA01 guest can fail its result-screen `until 009F == BC` condition and exit 3 with the exact script `TIMEOUT after ... (value=...)` record. The paired oracle classifies only this specifically identifiable guest-script gate timeout as `invalid_route`, allowing the bounded reducer to try other candidates. Missing/mismatched binaries, arbitrary nonzero subprocess returns, absent source receipts, unexpected emulator errors or false stage stamps are still hard failures. This treatment was driven by the actual baseline-successful, candidate-timeout result of [compute run #40225514533](https://github.com/gamesbyian/UR-Recomp/actions/runs/40225514533); the run did **not** produce an accepted reduced input.\n\nROM-free contract tests: python3 -m unittest tests.unit.test_prepare_qa01_zoo_reducer_pilot

If first discrepancy changes or the original source cannot be authenticated, stop and report the negative. No broad factory dispatch.


**2026-10-25 execution-path correction (post-run #40226399446):** The unchanged full source observer continues past `scene-05040` into an `until 009F == BC 9000` result-screen gate. The [earlier real run #40225514533](https://github.com/gamesbyian/UR-Recomp/actions/runs/40225514533) established baseline reproduction and the first reduced input's genuine scripted result timeout. The later [run #40226399446](https://github.com/gamesbyian/UR-Recomp/actions/runs/40226399446) ended after a native 120-second `xvfb-run` subprocess timeout, which does not establish a hang or a changed +5040 mismatch. For a +5040-only reducer, the intake now writes a **private, SHA-bound derived observer** containing the exact independently authenticated full-script prefix through `dump scene-05040`, immediately followed by `quit`. The manifest still separately pins the unaltered full producer script and its SHA; oracle validation recomputes the prefix byte-for-byte and rejects any shortened/mutated pre-checkpoint line or altered digest. The actual original/native commands both execute the same bounded script with their distinct source guest clocks. This avoids the irrelevant result-screen wait while preserving precheckpoint input/observation semantics; it cannot demonstrate a complete course or eliminate candidate-route failures before +5040. A single authentic bounded retry may evaluate whether this actually yields a smaller qualified counterexample. No release gate credit.


**2026-10-25 bounded ddmin efficiency follow-up (optional, no automatic research run):** The independently reopened original source fixture from producer run 40168208753 contains 354 P1 runs, **16 of which start strictly after the authenticated original +5040 observation at host frame 6057**. Generic left-to-right delta debugging with a twelve-call budget can expend its tests on unrelated earlier input blocks without ever reaching this suffix. The optional `--observation-frame` argument to `reduce_controller_fixture.py` uses the *authenticated original guest* observation frame (never a guessed native clock): after establishing a valid original baseline, it **spends a normal repeated, exact-original/native oracle check** on dropping only later-starting rows before ddmin. If that check is negative or invalid, all rows remain. Input runs crossing the observation boundary remain intact, output retains original source digest plus reported optional-frame, attempted-check and verified-tail-deletion counts, and the global oracle-call budget remains unchanged. This is test-plumbing efficiency, not a substitute original-game observation. Do not insert an extra authentic retry just to exercise this feature; the one 2026-10-25 real checkpoint-only retry was already dispatched separately.
