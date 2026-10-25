# Bounded controller replay reduction pilot

Status: opt-in engineering diagnostic; no release gate credit. See VALIDATION.md and AGENTS.md for source truth and evidence custody.

When a verified original/native mismatch needs thousands of controller frames, tools/reduce_controller_fixture.py tries removing unnecessary controller *rows*, preserving the original entry prefix and absolute timing. Input uses the existing canonical controller_input parser, including both player masks. Every row starting before --protected-before-frame is immutable even if it extends across the cutoff.

ROM-free contract test:

    python3 -m unittest tests.unit.test_reduce_controller_fixture

CLI (illustrative, using an actual paired original/native oracle supplied by the owner lane):

    python3 tools/reduce_controller_fixture.py \
      --input /private/source.script \
      --output /private/minimized.script \
      --report /private/minimized.json \
      --protected-before-frame 1700 \
      --max-calls 60 --repeats 2 --timeout 120 \
      --oracle python3 /private/qualified_original_native_adapter.py

The oracle receives --candidate PATH and --receipt PATH. It must actually execute the original reference engine and compiled native binary with equal legal input and return JSON containing:

- schema: ur-controller-reducer-oracle/1
- candidate_sha256: exact SHA-256 of candidate file
- source_sha: 40-character source commit
- original_rom_sha256 and native_binary_sha256: exact 64-character digests
- reference_engine, discrepancy_id, semantic_phase: nonempty, stable
- original_valid, native_valid: actual independent Boolean route validity
- result: reproduced, not_reproduced or invalid_route

Every candidate is replayed twice by default. The reducer refuses changed input digest, source provenance, emulator identity, semantic stage, missing or invalid receipts and unqualified paired behavior. Oracle subprocesses are bounded by time and call count; accepted results have source and reduced script hashes. Missing or non-reproducing candidates are rejected, with the last proven candidate retained.

There is deliberately no fake ROM fixture, generic automatic equivalence whitelist, generated oracle or independently accepted event count. The synthetic unit-test oracle tests the tool contract only. A genuine paired producer adapter must be qualified before running expensive experiments; outputs must still undergo independent QA acceptance. Do not include private ROMs or other licensed inputs in PR artifacts.
