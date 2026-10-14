# QA-01: original/native Zoom Zoo exact pre-return guest memory and transient divergence

**Completed, genuinely executed evidence:** original pinned Snes9x USA and pinned Baldosa using the unchanged source 2014 controller movie, fresh independently measured scene entries (original host **1604**, native **1606**). This comparison rereads the independently green [workflow 38500427634](https://github.com/gamesbyian/UR-Recomp/actions/runs/38500427634), artifact [11866136501](https://github.com/gamesbyian/UR-Recomp/actions/runs/38500427634/artifacts/11866136501), pinned artifact ZIP SHA-256 `d5ec65c672736fa45f01214134db8598baa840f106729bd2c04ffb8949f1d039`. Every sample below has its own original/native `script f=N dump TAG ...` transcript receipt, not a reconstructed filename alone. The artifact contains full original/native 128-KiB WRAM, 64-KiB VRAM and 512-byte CGRAM at each tick.

| Actual original/native guest-relative frame | Different WRAM bytes (131,072) | Different VRAM bytes (65,536) | Different CGRAM bytes (512) |
| --- | ---: | ---: | ---: |
| Entry (1604/1606 absolute) | 4 | 0 | 0 |
| +4700 | 4 | 0 | 0 |
| **+4800** | **0** | **0** | **0** |
| +5000 | 4 | 0 | 0 |
| **+5100** | **0** | **0** | **0** |
| +5155 | 0 | 29 | 0 |
| +5156 | 69 | 0 | 0 |

Two complete **197,120-byte** guest samples (WRAM+VRAM+CGRAM combined) are byte-identical at the *same source-calibrated scene-relative position*, +4800 and +5100. They are not synthetic component tests, decoded fields or checksum estimates: all three independently dumped whole memories match. At +5100, both source PPU snapshots additionally register forced blank (`$2100=80`), consistent with the same pre-return loading stage, but this is not automatically the same CPU/beam phase.

The later **+5155 transient** is particularly instructive: full WRAM agrees while exactly 29 bytes of VRAM differ. At **+5156**, VRAM has rejoined to exact equality but 69 WRAM bytes differ; source opcode-scope tracing previously attributed all 69 to executing original code scopes in the later menu-stage transition. The mismatch switches *memory class* during that handoff. This is evidence of an original/native presentation/producer sampling phase relationship, **not a diagnostic of lap physics failure**, and is distinct from the separately proven one-frame result-state lead. Adjacent guest-relative memory cannot by itself determine NMI/beam-level causality; the two engines' absolute host clocks are still offset by two frames.

`tools/qa01_zoo_prereturn_bulk_parity.py` reconstructs every comparison from the immutable ZIP only, with strict digest identity, exact side-specific real emulator transcript grammar, exact guest relative frame ticks, complete lengths, no duplicate/symlink evidence members, and original/native per-image SHA-256. Unpinned synthetic fixtures are unit negative controls and never earn release credit. The compact [machine-readable digest ledger](../analysis/data/zoo-original-native-prereturn-full-memory-20261014.json) stores observed different-byte counts and representative original/native fingerprints. A later extended +5048..+5072 return/PPU original-PC trace is being investigated independently in [PR #1484](https://github.com/gamesbyian/UR-Recomp/pull/1484); it must not be called executed or green until its actual guest workflow passes.

**Next causal decision:** compare the original/native *actual* onset of `$2100` forced blank and the source-executed race-return PC immediately before the samples diverge; distinguish a rendering/return-phase offset from an upstream player-finish decision. Do not claim instruction equivalence, rewrite the original movie, shift all native controls or waive terminal frame equality. **0/45 strict complete USA events admitted.**
