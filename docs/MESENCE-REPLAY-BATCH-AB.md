# MesenCE replay transition batching: bounded real-core A/B

This qualification extends the original exact-pinned MesenCE 2P workflow without changing its established per-frame run by default. A user can manually dispatch .github/workflows/mesence-two-player-reference.yml with benchmark_controller_batches=true. It runs original first, then the opt-in transition-batched route on the same 2P input, fixture script, verified retail ROM and cached pinned MesenCE executable. Both are fresh MesenCE processes with private output roots.

tools/compare_mesen_batch_replay.py compares **every byte of every named 131072-byte WRAM snapshot**, exact original guest frame milestone sequence and dump completeness; reports both binary/source SHA256, source ROM/input/script fingerprints, first differing byte if any, and the two measured *replay-only* process durations from GNU time. Any missing, malformed, altered or reordered checkpoint fails closed. A synthetic contract test cannot replace this original emulator A/B.

A one-time, trusted same-repository PR ready_for_review trigger on exactly branch ci/mesen-batching-qualification-20261025 is for testing when direct manual dispatch is unavailable. **Remove that pull_request trigger before merging**; keep the permanent manual boolean opt-in only if real-core A/B produces useful data. Do not apply batch mode to the default reference oracle until exact full-WRAM parity and timing are independently reviewed.

Even if all snapshots match, this demonstrates only behavioral equivalence between two stepping configurations **of the same pinned MesenCE core** at the checked checkpoints. It is not independent Snes9x agreement, a native recomp parity pass, complete original USA course acceptance, physical hardware evidence or a new release gate. Favor speed only if measured elapsed benefit is material; account for core startup and full toolchain setup separately.

ROM-free contract tests: python3 -m unittest tests.unit.test_compare_mesen_batch_replay
