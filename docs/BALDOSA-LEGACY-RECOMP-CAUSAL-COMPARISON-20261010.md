# Baldosa vs legacy UR-Recomp: bounded recompilation architecture comparison

Date: 2026-10-10. **Research only; no simulation, build, or release gate changes.** This report distinguishes directly inspected source from upstream assertions and causal hypotheses. Its purpose is to explain the apparent disparity in native completeness without delaying the Windows Modern integration.

## Source anchors

- `reference/imported/reverse-engineering/baldosa-uniracers-recomp/README.md`
- `reference/imported/reverse-engineering/baldosa-uniracers-recomp/recomp/README.md`
- `reference/imported/reverse-engineering/baldosa-uniracers-recomp/recomp/bank80.cfg` and `bank81.cfg`
- `reference/imported/reverse-engineering/baldosa-uniracers-recomp/tools/regen.sh`
- `tools/toolchain-entries/snesrecomp.json`
- `docs/BALDOSA-NATIVE-EXECUTION-EXPERIMENT-20261009.md`
- `docs/BALDOSA-UR-RECOMP-REUSE-AUDIT-20261009.md`
- `docs/RELEASE-QUALITY-LEDGER.json`

## Direct findings

1. **Same original USA ROM identity**, recorded SHA256 `859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478`; shared SNESRecomp lineage does **not** imply identical pinned compiler/framework revision, analysis roots, host scheduler, or tests.
2. **Baldosa has explicit, extensive analysis configuration.** Its `bank80.cfg` supplies `indirect_dispatch` targets for main-loop mode routing at `$80:88AB`, various pointer calls, explicit continuation/stack-frame semantics, and `exit_mx_variant` / `exit_mx_at` directives for processor register-width inference across tricky returns. `bank81.cfg` names original physics, lap, track, camera, HUD, DMA and stunt routines. These are real source-level inputs, not merely AI-generated feature-layer code.
3. **The upstream README makes strong, NOT independently reverified, coverage claims:** all code in banks 80–83 mapped (42.8k instructions), 674 named functions, 620 named RAM variables, byte-exact rebuilt disassembly, and seven interpreted reset-prologue instructions on its tested routes. These claims should be audited separately from official 0/45 complete-event release acceptance.
4. **A coverage-driven regeneration workflow is explicit.** `tools/regen.sh` verifies exact ROM identity, supports manually curated config roots and historical/current profile manifests, regenerates native C and synchronizes named functions. `recomp/README.md` distinguishes `emit=true` functions that are attempted AOT roots from `emit=false` labels left at LLE boundaries, and explains that generated `bank*_v2.c` coverage is not reflected simply by counting config declarations.
5. **Framework divergence is material.** Baldosa's README names upstream-branch-specific HVBJOY beam synchronization, native entry hand-off, variant roots, historical profile manifest support and paced-bus code generation. The legacy UR toolchain descriptor pins a different revision, `cd5875cbdaf19f5e324272b1f8051d671fce9215`, and enumerates 35 project-specific framework patches spanning title/input hooks, frame timing/restart, output, widescreen, persistence and audio. Patch count alone does not prove bugs; nor does this comparison establish which specific patch affects a course.
6. **Independent observed runtime:** the imported guest executed 5,447 native 1P frames and 2,473 native 2P frames; attaching UR's read-only guest observer preserved all 2,473 WRAM CRCs against untouched Baldosa. The original Zoo script initially timed out; later result comparisons still exposed frame-phase mismatches. Hence neither a zero-interpreter-hit upstream claim nor a passing native route certifies 45 courses or exact emulator equivalence.
7. **Legacy UR-Recomp owns much more product functionality.** Modern root, profile storage, SRAM transactions, Records, replay, ghosts, authored HD sprites and widened presentation are first-party value to preserve. The Baldosa guest was easier to transplant as a self-contained simulation, not a complete replacement for these systems.

## Causal hypotheses, ranked, not yet proven

- **H1: Analysis roots and dispatch/width annotations yield substantially more reliable native executable coverage.** Supported as a plausible mechanism by `bank80.cfg`; not proven as the cause of legacy differences until both configurations and generated AOT maps are compared.
- **H2: Runtime revision and scheduler/beam behavior explain some route/terminal phase differences.** Framework-specific timing features are explicit; actual same-host and guest-relative result differences exist. Attribution to any particular feature remains unproven.
- **H3: Development acceptance priorities changed what appeared finished.** Baldosa emphasized interpreter/native/original route checkpoints and named disassembly; UR invested in modern product/graphics/persistence and specific archaeological probes. This describes scope, not a measured superiority of either AI.
- **H4: 35 legacy patches increased integration surface.** Verified presence and categories, but no evidence establishes that accumulated patches *caused* the fidelity shortfall. Avoid treating patch count as defect count.

## Minimal decisive experiments, without new infrastructure

1. Compare the legacy **actual codegen inputs**, roots, pinned compiler/framework SHA and generated native-vs-LLE coverage against Baldosa under the same ROM. Record counts by bank and *executed* function variants, not just symbol totals. Reuse existing runners and logs; do not introduce another all-course system.
2. Select one observed divergent route (Switcher/Zoo) and compare first mismatch in: accepted guest input words, executed native/LLE dispatch target, CPU M/X width state, host-frame versus emulated-frame/NMI phase. Diagnose the first divergence rather than extrapolating from terminal memory.
3. Classify each legacy framework patch as host-only/product, guest scheduling, code generation, or hardware behavior. Only timing/codegen/hardware candidates deserve a focused controlled ablation, and only if they intersect an observed divergence.
4. Verify one upstream coverage assertion independently (on a pinned route, count executed interpreter instructions by category). Do not treat upstream README assertions as new release acceptance.

## Decision and stop rule

Do not pause Baldosa→Modern Windows player-journey work for this retrospective. Allocate at most **one focused 6-agent-hour hypothesis spike** to an immediately reusable differential witness. Stop when evidence fails to isolate a player-significant correctness, maintenance or build-risk decision. The product's critical path remains a working native profile→1P/2P race→result→Records/relaunch loop, with Original and stable widescreen presentation. Retain legacy backend as rollback until a candidate demonstrates product equivalence.
