# MesenCE replay transition batching: bounded real-core A/B

This qualification extends the original exact-pinned MesenCE 2P workflow without changing its established per-frame run by default. A user can manually dispatch .github/workflows/mesence-two-player-reference.yml with benchmark_controller_batches=true. It runs original first, then the opt-in transition-batched route on the same 2P input, fixture script, verified retail ROM and cached pinned MesenCE executable. Both are fresh MesenCE processes with private output roots.

tools/compare_mesen_batch_replay.py compares **every byte of every named 131072-byte WRAM snapshot**, exact original guest frame milestone sequence and dump completeness; reports both binary/source SHA256, source ROM/input/script fingerprints, first differing byte if any, and the two measured *replay-only* process durations from GNU time. Any missing, malformed, altered or reordered checkpoint fails closed. A synthetic contract test cannot replace this original emulator A/B.

An initial one-shot trusted-PR qualification run was started from revision 14c8badc and the temporary PR trigger was removed immediately afterward to comply with the manual-only research workflow policy. The permanent workflow runs only with explicit manual dispatch. Do not apply batch mode to the default reference oracle until exact full-WRAM parity and timing are independently reviewed.

## First actual pinned-core result, October 25, 2026

**Decision: opt-in input-transition batching qualified for this one canonical two-player MesenCE research fixture; leave established default per-frame.**

Real [Actions run #40216541612](https://github.com/gamesbyian/UR-Recomp/actions/runs/40216541612) finished **success** on source checkout `14c8badc6fd0f370486a47ffc46c9216b52c1e2b` using pinned MesenCE revision `a60e79feb4d6dcced5922d636f9211837d01e381` and original input/script `tests/input/two-player-first-race.input` / `tests/input/two-player-first-race-observe.script`. Separate fresh original-core processes yielded legacy **15.28 s** and opt-in transition-batched **9.46 s**, a **38.1% reduction** in single-run replay-only elapsed time. **All 9 of 9 named full 131072-byte original MesenCE WRAM capture pairs were byte-identical**, with identical guest frame milestones through 1620. The existing MesenCE/Snes9x semantic expected-state assertions also passed on the legacy observer. The raw paired dumps, logs, per-case hashes, timing files and machine-readable A/B report are retained as Actions artifact `12607758450`, under the producer's seven-day retention policy.

This is a **single** two-player bounded fixture, not a fleet benchmark or proof of original-to-native parity; the paired captures come from the same MesenCE emulator core. The full workflow includes dependency installation and pinned MesenCE compilation, which are **not** covered by the 38.1% replay-only improvement. Repeating this experiment is unnecessary unless a new fixture/input seam or core build invalidates the existing outcome. No automatic research factory or release-gate promotion is authorized.

Even if all snapshots match, this demonstrates only behavioral equivalence between two stepping configurations **of the same pinned MesenCE core** at the checked checkpoints. It is not independent Snes9x agreement, a native recomp parity pass, complete original USA course acceptance, physical hardware evidence or a new release gate. Favor speed only if measured elapsed benefit is material; account for core startup and full toolchain setup separately.

ROM-free contract tests: python3 -m unittest tests.unit.test_compare_mesen_batch_replay
