# QA-02: independent replay of the original failed hardkill-owner ELF

**Date:** October 14, 2026. **Evidence:** [bounded machine-readable receipt](../analysis/evidence/qa02-38519338884-exact-binary-local-negative-replay.json). This is an independent fault investigation, not a passing release gate, product repair or superseding original campaign verdict.

## Historical negative remains authoritative

The original [failed run 38519338884](https://github.com/gamesbyian/UR-Recomp/actions/runs/38519338884) executed its genuine production-host-store hardkill-owner scenario at repository source b9113d6e5951b22c81e9ca6875d2d014de1a9c2a. The accumulated fault receipt contained 4,495 accepted ten-case batches (44,950 real OS-process journeys) and then a failing batch **index 4495**, exact seed **5001200064495**. The saved wrapper exception only said **original production fault oracle rejected/incomplete trial population**. Its underlying child trial/assertion receipt was NOT retained, so it cannot identify a specific breached ownership or persistence invariant.

## New exact binary acquired and independently re-executed

Downloaded the ORIGINAL compiled Linux fault fixture from the SAME Actions run: archive artifact 11874481043 SHA256 **b91bbe2a835ae98f71b012a6203e41cacccfd23c363d9ba9d287c923a1fb16fc**, containing the original unmodified Linux x86-64 ELF binary SHA256 **ee17b8ae5fdae1ffbcceccbbb0b112130572fea58840d06f5eb7f423e7849b39**. The executable is an ordinary dynamically linked Linux ELF with historical source commit receipt. No reconstruction or recompilation of product implementation occurred.

Under the independent local Linux x86-64 container (kernel 6.18.44, glibc 2.41, Python 3.13.5), the existing source-owned hardkill-owner case sequence was replayed directly against that exact executable. Each iteration used a fresh isolated root: start a real owner-hold process, await the actual live barrier, sleep the seeded 0–8ms jitter, send a **real SIGKILL**, observe one persisted run, invoke a new owner-takeover process and verify two runs plus one original C15 fixture receipt through a separate verifier process. The first exact ten historical jitter values were **6, 3, 6, 0, 5, 4, 4, 2, 6, 5 milliseconds**.

**Result:** 10/10 original-seed cases completed successfully. Extending that seeded schedule to **500 fresh real-process journeys** yielded **500/500 successes**, zero failures, elapsed 10.466 seconds. Jitter histogram across 0 through 8ms was **[65, 52, 41, 55, 59, 52, 67, 49, 60]**.

This local replay used the original source fixture **binary** and equivalent source assertions; it did NOT import the complete historical Python run_suite wrapper, rebuild the historical GitHub runner, simulate 44,950 previous trials or recreate its CPU/process scheduling and resource accumulation. Consequently **the historical negative is not refuted**. Seed plus executable alone were insufficient to reproduce it in this external environment. A rare data race, runner artifact failure, synchronization stress or load-dependent effect remains possible.

## Owner handoff and next discriminator

The owning fault/CI agent should run just the **ten exact seed cases on the historical runner**, retain the **original per-trial** source assertion failure and actual owner/receipt file inventory, and distinguish storage authority invariants from scheduling and artifact publication. Only if this yields a minimal breach should gameplay/Modern/storage implementation owners be asked to repair specific behavior. No broad 60-minute campaign or extra automatic workflow is justified before this smaller receipt-producing discriminator.

This adds no Windows physical session, actual guest result, audio, power-loss simulation, original/native complete event or final package proof. **QA-02 stays in_progress**, all original USA complete-event acceptances remain **0/45**, and final candidate commit/ZIP remain unset.
