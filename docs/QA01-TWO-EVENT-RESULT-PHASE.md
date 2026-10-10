# QA-01: one-frame original/native result phase in two unrelated event families

Independent original Snes9x and pinned Baldosa executions now demonstrate a **matching scene-relative one-frame lead on native** in both the 2014 *Zoom Zoo* Circuit and the 2014 *Bowl* timed scored Stunt. [Machine-readable arithmetic](../analysis/data/two-event-original-native-result-phase-crosswalk-20261009.json) is checked by `python3 tools/check_two_event_result_phase.py`, with unit controls for inverted frame labels, missing independent event families and false course acceptance.

| Event | Original entry host | Native entry host | Original result host | Native result host | Result relative original/native |
|---|---:|---:|---:|---:|---:|
| Zoom Zoo, Circuit | 1604 | 1606 | 6767 | 6768 | 5163 / 5162 |
| Bowl, 45s scored Stunt | 984 | 985 | 4349 | 4349 | 3365 / 3364 |

The original/native **absolute result** host-frame difference is +1 for Zoo and 0 for Bowl, but the **calibrated entry host-frame** difference is +2 for Zoo and +1 for Bowl. Therefore in both cases `(native terminal − original terminal) − (native entry − original entry) = −1`.

This pattern in two event families weakens the hypothesis of a unique Zoo Circuit-specific finish defect. It is **not a causal timing verdict**. Both Snes9x `script_tick()` and Baldosa `TickScript()` inspect `until`/dump state before running the next simulation frame; their matching semantics do **not** prove the same guest CPU PC/NMI/VBlank phase. The native +5156 Zoo WRAM/VRAM/CGRAM exactly equals original +5157, and the original CPU write at `83:988A` is source-correlated with native `Sram_RestoreDirectPage_FastRom_M1X0`, but the original and native instrumented time stamps are different levels of precision.

Bowl's successful *executed* paired route has **28/28 matching gameplay semantic samples, identical original/native stunt tally PPU text, identical MIKE 764 / qualify 68 result rows and matching full sampled result semantic state**, with exact original movie/SRAM fingerprints. Its strict full-event parity predicate remains false solely because of the one-frame *scene-relative* terminal discrepancy. The fresh-groups claim is bounded to the tested original and native builds, input, and samples; it is neither a complete continuous-frame equality proof nor a demonstrated guest-instruction equivalence.

**Next narrow discriminator:** record guest CPU PC and NMI/VBlank timing at the course-entry predicate **and** result-restore/result-tally predicate in both engines, on the same source inputs. If the course entry host event is one frame phase-shifted, a host-owned zero-frame entry oracle may be responsible for both results. If CPU-frame-equivalent terminal writes occur at different instruction/scanline stages, investigate actual scheduling. Do not globally rebase controller input, do not modify physics/clock/scoring, and do not upgrade the **0/45 accepted USA complete courses** based on best-fit byte distances or matching score text alone.

Sources: Zoo [run 38018081196](https://github.com/gamesbyian/UR-Recomp/actions/runs/38018081196), [source-owner witness](../analysis/data/zoo-original-native-sram-restore-source-owner-20261009.json); Bowl [run 38021981513](https://github.com/gamesbyian/UR-Recomp/actions/runs/38021981513), [Bowl owning experiment](QA01-BOWL-2014-PAIRED-STUNT-PROBE.md). The associated archived CI artifacts are uniquely identified in the crosswalk.
