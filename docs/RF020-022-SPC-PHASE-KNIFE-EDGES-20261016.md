# RF-020/021/022: SPC timer-phase knife-edges, SPC power-on, and witness fragility (2026-10-16)

**Scope:** CPU/APU-lane follow-through after [RF-016/018/019](RF016-019-TIMING-CORRECTIONS-20261015.md). The base is the full RF-015…019 candidate on the pinned Baldosa core (`gamesbyian/uniracers-recomp@10b864b`, framework `baldosa/snesrecomp@075fbe4`). Evidence comes from disposable SPC-side port/timer logs added to a Snes9x core and to a Baldosa observer build, plus PC-filtered CPU traces. Compact evidence: [`analysis/data/rf020-022-spc-phase-20261016.json`](../analysis/data/rf020-022-spc-phase-20261016.json). **No release-gate or complete-event credit.** QA-01 alone decides event acceptance; official strict USA complete events stay **0/45**.

## Summary

- **Dragster** (+2080 vs +2081) has the same root as 2P seed 50048000 (RF-020). Both Snes9x and bsnes agree byte-for-byte; native is the outlier. The post-race loader resets the SPC (`82:8089 STA $2140=$FF`, wait for `$BBAA` at `82:8097`). The sound driver honours the reset only after a fresh **timer-2 tick**. On the reference a stale tick is already pending, so it waits a whole timer period (~3,150 SPC cycles); on native it is not. Native then leaves the loader early and reaches the post-upload two-edge wait `80:FAC9` before VBlank (V=189) instead of just after it (V=228), so it skips a field.
- **RF-021:** native does not run the SPC until the CPU first writes an APU port (`portTimeValid` is set lazily in `apu_schedulePortWrite`). Hardware, Snes9x and bsnes run it from power-on. At the first SPC reset (host 35) the reference SPC has run 586,459 cycles; native's has run 6, so its IPL ROM is still clearing zero page. With the SPC anchored at power-on (2,446 guest cycles of offset), that first handshake matches **exactly**: 586,459 SPC cycles and a 10,004-clock latency on both. The later boot resets match within 2 lines.
- **RF-022 (method hazard):** running the SPC from power-on is the hardware-correct model, yet adopting it alone **flips several current matches**:
  - Zoom Zoo's +16 follow-through returns to menu 188 vs 246, and SRAM differs at +64/+72.
  - Three attract loads go one frame off: 941–1097, 1422–1545, 3631.
  - The 18 2P pairs, Bowl, Switcher and Dragster are unchanged.

  Those witnesses are decided by SPC-phase/CPU-time differences of roughly 100 SPC cycles (about 0.001% of a session). Under the lazy start they land on the reference's side partly through compensating errors. Current event matches on this core are therefore **knife-edges, not robust agreement**.

## Dragster root step

Dense dumps (+1940…+2100) show Snes9x and bsnes identical at every frame. Native first differs at +2040 (host 2985): the `$0BDD/$0BDE/$0BFE` transition counters start one field early. Its menu transitions follow a frame early, and it re-synchronizes by +2100.

The trace and SPC logs place the cause at the host-2902 SPC reset:

| | Snes9x | native (RF-015…019) | native + power-on anchor |
| --- | --- | --- | --- |
| Reset wait (`82:8082`→`82:809C`), master clocks | 123,394 | 75,242 | 119,790 |
| Driver reads `$FF`, SPC cycles after the write | 234 | 671 | 404 |
| Next timer-2 tick consumed | +257 (stale) and +3,406 | +1,113 | +3,240 |
| IPL ready (`rd0 00`) | +5,870 | +3,576 | +5,703 |
| Arrival at `80:FAC9` after the stream upload | V=228 | V=189 | V=222 |

With the power-on anchor native is only 6 lines early and still lands before VBlank, so the terminal stays one frame early. The remaining offset is the driver's timer-2 phase, which each driver restart re-anchors to CPU time. It traces back through the earlier resets: at hosts 46 and 849 native is 2 lines early, and the host-849 reset still differs by 36,112 clocks.

## RF-021 detail: whole-session SPC reset census

All eight `$FF`→`$BBAA` resets in the Dragster replay, with the power-on anchor, compared with Snes9x (positions are host frame and V; native frame labels run one behind):

| # | Snes9x position | Snes9x latency | native + power-on position | native latency |
| --- | --- | --- | --- | --- |
| 0 | 35 V98 | 10,004 | 34 V98 | 10,004 |
| 1 | 44 V209 | 50,868 | 43 V207 | 50,766 |
| 2 | 46 V71 | 50,802 | 45 V69 | 50,842 |
| 3 | 849 V88 | 125,344 | 848 V88 | 89,232 |
| 4 | 859 V22 | 50,808 | 858 V256 | 50,768 |
| 5 | 862 V155 | 50,812 | 861 V126 | 50,754 |
| 6 | 2902 V159 | 123,394 | 2901 V158 | 119,790 |
| 7–8 | 2912–2913 | ~50,800 | 2911–2912 | ~50,770 |

Without the anchor the boot reset differs by +40,524 clocks and reset #6 by −48,152.

## The remaining CPU residual

Race fields differ from Snes9x by tens of clocks per NMI-to-wait span. Seed 50048000's host-4800 field is 64 clocks short. General DMA is one contributor: native charges 12 clocks of CPU sync per `$420B` write, while Snes9x uses a fixed 18 (`Timings.DMACPUSync`). Changing native to 18 turns that field 50 clocks *long*, because it has about 19 DMA starts. So no single constant closes the residual. Hardware's 12–24-clock sync depends on clock alignment, and only a bus-exact model checked against bsnes, not Snes9x, can decide it.

## Recommendation

- **RF-021 (power-on SPC)** is correct hardware behaviour and should be part of any final timing model. It should not be shipped alone while the event matches above depend on the lazy start's offsetting error. Stage tool: [`tools/baldosa_spc_power_on_patch.py`](../tools/baldosa_spc_power_on_patch.py), with a unit test. It has no campaign input, deliberately.
- **QA-01:** treat Zoom Zoo's follow-through agreement and the attract matches as knife-edge witnesses. A small, correct timing change can flip them. Before accepting an event on such a witness, re-check it under every staged timing correction.
- **Next research step (low priority):** model general-DMA sync and the HDMA/DMA interaction bus-exactly against bsnes, then re-run the reset census. Until the CPU residual is far below ~100 SPC cycles at each driver restart, outcomes at SPC-reset knife-edges remain unstable.
