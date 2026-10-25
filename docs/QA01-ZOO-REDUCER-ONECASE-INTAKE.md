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

Only after the authentic source preflight succeeds, start **one** bounded reduction:

    python3 tools/reduce_controller_fixture.py \
      --input /private/reducer/original.input \
      --output /private/reducer/minimal.input \
      --report /private/reducer/minimal.json \
      --protected-before-frame ORIGINAL_REFERENCE_ENTRY \
      --max-calls 12 --repeats 2 --timeout 120 \
      --oracle python3 tools/qa01_reducer_paired_oracle.py \
      --manifest /private/reducer/paired.json

Use the actual manifest guest_clocks.reference_entry_frame for ORIGINAL_REFERENCE_ENTRY. Historical entries 1017/1019 are *not defaults*. The manifest includes the exact source observer script, separate host frames and SRAM, SHA-pinned original/native binaries and native_xvfb=true. No ROM, SRAM, SMV, original input stream or private saves should be uploaded. Hash-only decisions still need actual CPU input-poll and causal writer/consumer verification. Synthetic test fixtures grant zero gameplay or Windows release credit.

ROM-free contract tests: python3 -m unittest tests.unit.test_prepare_qa01_zoo_reducer_pilot

If first discrepancy changes or the original source cannot be authenticated, stop and report the negative. No broad factory dispatch.
