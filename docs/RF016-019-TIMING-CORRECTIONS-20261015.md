# RF-016/018/019: SPC rate, `[dp],Y` pointer reads and HDMA stall (2026-10-15)

**Scope:** CPU/APU-lane follow-through after [RF-017](RF017-IO-ACCESS-CLOCK-ORDER-20261015.md) on the pinned Baldosa product core (`gamesbyian/uniracers-recomp@10b864b`, framework `baldosa/snesrecomp@075fbe4`). Each correction is staged by a disposable-checkout tool with a compiled regression test, applied on top of RF-015 + RF-017, and measured against Snes9x and the high-accuracy bsnes core. Compact evidence: [`analysis/data/rf016-019-timing-corrections-20261015.json`](../analysis/data/rf016-019-timing-corrections-20261015.json). **No release-gate or complete-event credit.** QA-01 alone decides event acceptance; official strict USA complete events stay **0/45**.

## Summary

| Finding | Cause in the pinned runtime | Stage tool | Effect |
| --- | --- | --- | --- |
| RF-016 | SPC700 clocked at 17,088 cycles per field (assumes 60.000 Hz) instead of the references' 15664/328125 per master clock (17,060 per field) | [`baldosa_spc_reference_rate_patch.py`](../tools/baldosa_spc_reference_rate_patch.py) | Attract load 941–1098 now equals both references (was 941–1097). **Falsified** as the cause of 2P seed 50048000 and Switcher +4664: both unchanged. |
| RF-018 | Every `[dp],Y` access reads and charges its 3-byte pointer twice (paced bus), 152 generated sites | [`baldosa_dp_indirect_long_pointer_once_patch.py`](../tools/baldosa_dp_indirect_long_pointer_once_patch.py) | The attract decompressor runs at reference speed; the second attract load ends on the reference frame. |
| RF-019 | HDMA's per-line CPU stall is never charged by the beam frame driver | [`baldosa_hdma_cpu_stall_patch.py`](../tools/baldosa_hdma_cpu_stall_patch.py) | Attract demo race no longer runs ~4% fast; all five attract loads and the demo race match bsnes. |

With all three corrections (executables: 1P scene shim `9fb998d2…`, 2P research shim `6c9cd0e9…`), no witness regressed:

- the 18 2P seed × reference pairs give the same dispositions, first-divergence frames and byte counts as the RF-017 build;
- Zoom Zoo keeps `strict_candidate` with all six source follow-through pairs and all six fresh SRAM images equal;
- Bowl, Switcher (+4703 vs +4704) and Dragster (+2080 vs +2081; +64 menu 22 vs 246) are unchanged.

## RF-016: SPC700 rate

Baldosa converts master clocks to SPC cycles at 17,088 per 357,368-clock field (`apu_frame_clock.h`), i.e. 534 DSP samples per field at exactly 60 fields per second. The NTSC field is 1/60.0988 s, so the SPC700 runs 0.165% fast relative to the CPU. Both references use 1,025,280 SPC cycles per second: Snes9x's `APU_NUMERATOR_NTSC / APU_DENOMINATOR_NTSC` = 15664/328125 SPC cycles per master clock, and bsnes's 32,040 × 768 Hz / 24. The stage tool keeps the guest timeline in master clocks and converts it at exactly that ratio. `RtlLastFramePeriods` still reports 1.0 for a normal field, so host pacing is unchanged, and the audio servo already absorbs ±0.5%.

**Result (attract census, bsnes reference).** The first attract load 941–1098 now matches both references exactly. The base build was 941–1097. That exposed a second, independent error in the second load (RF-018): with the rate fixed, native ended it at 1548 against bsnes 1547 and Snes9x 1546.

**Not the cause of:** 2P seed 50048000 (still one field early at 5052) and Switcher +4664 (unchanged). Those two witnesses, which the [findings queue](RESEARCH-FINDINGS-QUEUE.md) attributed to RF-016, are not SPC-rate effects.

## RF-018: `[dp],Y` pointer read twice

Over the second attract load, low WRAM `$0200–$1FFF` is identical between Snes9x and bsnes at every frame 1440–1560. Native lags: one-frame transients at 1457/1469/1482, and a sustained difference from 1523.

A Snes9x per-instruction PC/beam trace and a Baldosa block-entry clock observer were compared from the shared exit of the `82:E16D` clear loop to `81:B94F`. Native took **188,304 vs 176,554** master clocks. One block, `81:BB10 CMP [$88],Y`, accounts for 10,552 of the 11,692-clock deficit: **103.6 vs 80.1** clocks per execution, 448 executions.

The pinned emitter (`codegen.py::_segref_addr_expr`) returns the operand's bank and offset as two expressions, each of which re-reads the pointer. Its comment expects the C compiler to merge them. With the paced bus every `cpu_read*_paced` call charges master clocks, so the 3-byte pointer is charged twice. The doubled byte count also shrinks the static internal-cycle term, which partly hides it: the net error is +6 clocks per execution, or +24 where that term clamps at zero, as in `81:BB10`.

The stage tool emits the pointer read once, in hardware order (low word, then bank), into a temporary, adds Y with carry into the bank, and addresses the operand through it. After a `--cfg-roots` regen, `--verify-gen` confirms that 152 `[dp],Y` sites read their pointer once and none twice. The regression test executes the staged emitter and compiles its output: pointer `$DF:D537` + Y=`$2AC9` addresses `$E0:0000` with exactly 3 pointer bytes read, for both reads and writes.

**Result.** The second attract load ends at 1546, matching Snes9x; bsnes says 1547, a brightness knife-edge while both references agree byte-for-byte in WRAM. Low WRAM equals bsnes at every frame 1530–1700, with only small fade-table transients at 1452, 1520 and 1523–1529.

## RF-019: HDMA CPU stall

With RF-018 applied, native next diverged in the attract demo race. It matched until 2346, then reached the post-race wait-for-NMI `82:D4E9` (`STZ $57 / BIT $57 / BPL`) one field early at 2347. Per-frame busy time between NMI-wait exits and entries was **288,334 vs 300,406** clocks (native 4% fast), spread almost uniformly across blocks. The Snes9x trace shows why. Besides the 40-clock DRAM refresh near H≈508, every active line has a **66-clock stall at H≈1090**: HDMA. The game runs six HDMA channels (HDMAEN `$BE`) whose split-screen tables transfer only at a few lines, so on most lines the stall is 18 + 6 × 8 = 66 clocks.

The pinned beam frame driver performs HDMA only in the post-field render walk and charges the CPU nothing for it. `dma.c` still defines `dma_hdmaMasterEstimate`, added in framework `0b2bd83`, but nothing calls it. It would also charge every channel a transfer on every line: about 150+ clocks per line here, against the real 66.

The stage tool adds a cost-only HDMA walk. At V=0 it reads the live HDMAEN shadow and channel registers and walks each table, reading ROM/WRAM only. It prices initialization (18 + 8 per channel, +16 indirect) and each of lines 0–223: 18 overhead, plus 8 per live channel, 8 per transferred byte, and 8 (+16 indirect) per line-counter reload. The existing per-block/per-opcode refresh hook charges each line's stall as CPU time passes its H-blank (H=1104). Parked time passes those points without a charge, as refresh does. The guest-visible HDMA is untouched. The regression test compiles the staged module and checks the per-line formula (six live channels: 66 per line plus transfers) and that parked time is not charged.

**Result.** All five attract loads match: 248–276, 401–443 and 941–1098 equal both references; 1423–1546 equals Snes9x (bsnes 1547, as above); 3632–3762 equals both. Low WRAM equals bsnes at every frame of 2300–2400 and 3625–3770.

## Remaining 2P witness: seed 50048000

Both references agree on this seed, and native's result sequence is one frame early from the `0x84` onset (5014 vs 5015; race exit 5052 vs 5053) under every candidate. Dense WRAM pins the first difference to frame **5012**, the RF-015/RF-012 pattern:

- the `$7E:2000` sound-command queue has advanced further on native (read index 2 vs 1);
- at 5013 the `$C6` frame-wait counter decrements one frame early (30 vs 31; `$0BDE/$0BFE` follow);
- the onset follows at 5014.

The queue is serviced by `82:8035` inside the `80:FAC9/80:FAD2` waits, one command per SPC acknowledgement. Native's sound driver accepts its second queued command a frame sooner. The SPC rate (RF-016), `[dp],Y` reads (RF-018) and HDMA (RF-019) do not change it. The next experiment is an SPC-side port-handshake trace (`qa01_apu_phase_observers.py` style) over host 5008–5012 on Baldosa and bsnes. Earlier work found that this step is phase-sensitive even between correct cores (RF-015 seed 50036056), so a sub-field CPU/SPC phase difference, not a rate error, is the leading hypothesis.

## Hosted re-execution

[Run 38792581653](https://github.com/gamesbyian/UR-Recomp/actions/runs/38792581653) (head `65befa5`, Zoom Zoo, all five opt-in corrections) succeeded on a clean runner:

- the RF-015 and RF-017 corrections staged, and the first regen verified 15,484 in-order charges with every block total unchanged;
- the RF-016 and RF-018 corrections staged, and the second regen verified 152 `[dp],Y` pointers read once, none twice;
- RF-019 staged;
- Zoo onset +5163 = +5163, `Zoo live SRAM first sampled original/native disagreement: +None`.

### RF-020 traced to its root step

A trace over hosts 4700–5016 moves the cause earlier.

- **Race fields:** they match within about 90 clocks per NMI-to-wait span.
- **First SPC reset:** after the last NMI (host 4924) the NMI-disabled loader asks the SPC to reset (`82:8089 STA $2140=$FF`) and waits for the IPL signature `$BBAA` at `82:8097`. That first wait lasts **126,742** master clocks on Snes9x but **59,644** on native.
- **Everything else in the loader matches:** the two later resets match exactly (674/674 and 661/660 polls), and the IPL byte upload has identical per-byte poll histograms (41,499 vs 41,466 polls over 7,278 bytes).
- **The gap is one timer tick:** 67,098 clocks is one sound-driver timer tick to within poll granularity (25 timer-0 periods = 3,200 SPC cycles = 67,032 master clocks).
- **The chain that follows:** native leaves the loader about 49 lines early, its stream upload runs ~33 bytes ahead, it sends the first queued command ~53 lines early (host 5012), and the onset follows a frame early.

So the driver honours the reset at its next timer tick, and native's request lands one tick earlier relative to the SPC timer phase. This is a phase knife-edge, not a rate or code-cost error. The next step is an SPC-side timer-0 trace at host 4929–4931 on Baldosa and bsnes, then a bisection of earlier handshakes to find where the phase offset first appears.

## Shipping boundary

- None of RF-016/018/019 is staged into the Windows bridge.
- Each has an opt-in input in `qa01-event-campaign.yml` (`baldosa_spc_reference_rate`, `baldosa_dp_pointer_once`, `baldosa_hdma_cpu_stall`) for hosted re-execution. RF-018 regenerates `src/gen` a second time after RF-017 and verifies separately.
- QA-01 adjudication, and the Windows build host's regen, come before the product carries any of them.
- Known approximations:
  - RF-019 walks the tables once per field at V=0, so a mid-field HDMAEN or table rewrite is not repriced.
  - RF-017's register test matches the 16-bit address without its bank (e.g. `$7E:211E`). That only reorders static charges inside a block and leaves its total unchanged.
