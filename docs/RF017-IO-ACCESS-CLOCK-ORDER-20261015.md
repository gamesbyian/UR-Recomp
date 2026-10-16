# RF-017: register accesses see later instructions' fetch clocks (2026-10-15)

**Scope:** CPU/APU-lane causal adjudication of [RF-017](RESEARCH-FINDINGS-QUEUE.md#live-queue) on the pinned Baldosa product core (`gamesbyian/uniracers-recomp@10b864b`, framework `baldosa/snesrecomp@075fbe4`, still the tip of its `uniracers/native-handoff` branch; upstream `main` `ec8a3e7` has no related change), with the RF-015 refresh correction applied. It provides a staged correction, its deterministic regression and measured original/native impact. Compact evidence: [`analysis/data/rf017-io-access-clock-order-20261015.json`](../analysis/data/rf017-io-access-clock-order-20261015.json). **No release-gate or complete-event credit.** QA-01 alone decides event acceptance; official strict USA complete events stay **0/45**.

## Result

Baldosa's `paced_bus` code charges a whole basic block's opcode/operand fetches and internal cycles to `cpu->master_cycles` **at block entry**, then charges each data byte as it is transferred. A hardware register access inside the block therefore sees a clock that already includes the fetches of every *later* instruction in that block. On the 65816 the access happens after the instruction's own fetches and before anything that follows it.

The post-result VBlank wait `80:FAD2..FAD9` (`JSL 82:8035 / LDA $4212 / BPL`) makes this decisive. Block `80:FAD6` (`LDA $4212 / BPL $FAD2`) charges 5 fetch bytes (40 clocks, SlowROM) before the read, where hardware charges 3. The `$4212` read lands **16 master clocks late**. In the Zoom Zoo result field it lands 6 clocks after V=225 instead of 10 before it, so Baldosa sees VBlank one poll pass early. It leaves the wait before the NMI, where the original takes the NMI inside `82:8035`, finishes the call and polls once more. The following CPU-bound compute then starts **556 clocks** ahead and reaches the next wait before V=225, while Snes9x and bsnes arrive after it. From result +2 the `$C6` cursor wait runs one field early, and the follow-through reaches menu 246 at +16 where the original and the 2014 source movie are still on 188.

## How the cause was found

All runs are local, from current-`main` tools and exact binaries: canonical USA ROM `859ec99f…`; Snes9x and the patched bsnes core from `bootstrap_toolchain.py`; Baldosa's `snesref` for the 1P producer and UR's dual-controller `snesref` for 2P. The baseline native is the committed `src/gen` + QA scene shim + RF-015 patch. Its executable `cd5ba13f…` is **bit-identical** to the RF-015 corrected build in the [QA-01 RF-015 report](QA01-RF015-DRAM-REFRESH-BEAM-RATE-20261014.md).

1. **Both originals agree; native is the outlier.** bsnes can now take the 2014 movie's anchored SRAM: `bsnes-libretro-system-ram.patch` also exposes cartridge RAM as `RETRO_MEMORY_SAVE_RAM`, with no timing change. bsnes then reaches the Zoo result on the same host frame as Snes9x (6180). Dense per-frame dumps of `$0200–$1FFF` are **byte-identical between Snes9x and bsnes at every frame +0..+39**. Baldosa differs from +2 (`$C6` 07 vs 06), as RF-017 reported. This is not a reference knife-edge.
2. **The compute between the waits is faithful.** A disposable Snes9x per-instruction PC/V/H trace was compared against a disposable Baldosa block-entry clock observer (non-perturbing: dense WRAM identical to the unobserved build). The k-th execution of each block PC was aligned from the shared `80:FADB` anchor to the next `80:FAC9`. The spans are **712,980 (original) vs 712,926 (native) master clocks**, a 54-clock drift (0.008%). That rules out per-instruction costs, the refresh rate (RF-015) and SRAM/ROM region speeds in the `83:90F8 Sram_UpdateChecksums` loop that dominates the span.
3. **Poll-loop iterations are identical.** Per instruction, the `82:8035` empty path (212 + 122 + 180 clocks), `FAD6` (52) and `FAD2` (62) match Snes9x exactly. Iterations are 628 or 668 clocks (with a 40-clock refresh) in the same proportions on both engines.
4. **The difference is where V=225 lands in the loop.** In the field before the result onset, Snes9x's last pre-VBlank read is at −100 clocks (clear). Its next pass is inside `82:8035` when V=225 begins. The NMI is taken there, the call finishes and `FAD6` reads VBlank set at V=226. Baldosa's last `FAD6` block starts at −40; it charges 40 fetch clocks, reads at **+6** (set) and leaves the loop before its block-boundary NMI. Native passes `80:FADB` at field clock 2256, the original at 2812: 556 clocks.
5. **Decisive A/B.** In the generated `80:FACD` and `80:FAD6` blocks only, the `BPL/BMI` fetch charge was moved after the `$4212` read (same total). Result: dense `$0200–$1FFF` equals Snes9x at **every frame +0..+89**. All six source follow-through pairs (+8..+72) match by menu and track (+16: 188 = 188). The only remaining bytes are stale stack at `$01DB–$01F3` from different interrupt landing points. They were already different at +0 and are not simulation state (AGENTS rule 19).

## Correction

[`tools/baldosa_io_access_clock_order_patch.py`](../tools/baldosa_io_access_clock_order_patch.py) stages a narrow change to the pinned emitter (`recompiler/v2/emit_function.py`) in a disposable checkout:

- It acts only on blocks that contain a **statically addressed register access** (`$2100–$21FF`, `$4000–$43FF`). There, the static master clocks are added before each instruction instead of once at block entry. Every register access then sees exactly the bus cycles that precede it.
- Unchanged: block totals, the 65816 `cpu->cycles` counter, dynamic charges (D.l, page cross, branch taken), deadline/yield checks, and every other block. If a block's per-instruction split cannot reproduce the lumped total, it keeps the lump.
- `src/gen` must then be regenerated with `tools/regen.sh --cfg-roots`. Without the patch, that command reproduces the committed bank files byte-for-byte; only module digests and manifest metadata differ.
- `--verify-gen` then proves that the regenerated bank files differ from the committed ones **only in static charge lines with identical per-block totals**. On the pinned guest: 89 files, 1,432 blocks reordered, 15,484 in-order charge statements, 18,538 block totals checked.

Affected register traffic, by blocks containing it: PPU `$21xx` writes 1,483 and reads 123; DMA `$43xx` writes 1,053; CPU `$42xx` writes 498 and reads 24; APU `$2140–$2143` writes 168 and reads 114; `$4210–$4212` reads 18.

Remaining approximation: an instruction's own internal cycles are charged before its data access. That is exact for the loads, stores and branches that dominate register traffic. It is off by at most one internal cycle (6 clocks) for read-modify-write forms. NMI and IRQ are still taken at block boundaries.

## Deterministic regression

[`tests/unit/test_baldosa_io_access_clock_order_patch.py`](../tests/unit/test_baldosa_io_access_clock_order_patch.py):

- Stages the patch against verbatim pinned emitter regions and rejects anchor drift and marker tampering.
- Executes the staged helper on the measured `80:FAD6` block: a 3-fetch charge before the read and 2 after, at both live and constant SlowROM speed.
- Proves block totals are preserved with SRAM data bytes.
- Proves blocks without register access, and unreproducible splits, keep the lump.
- Checks the generated-code verifier's accept and reject paths.

## Validation

**1P strict producer** (`probe_original_event_complete.py --native-backend pinned-baldosa --source-followthrough`, Snes9x, unchanged comparator, classified by `qa01_event_campaign.py classify`). Base `cd5ba13f…` vs candidate `d337cbec…`, same sources except the staged emitter + regen:

| Case | Base | Candidate |
| --- | --- | --- |
| Zoom Zoo | `strict_candidate` +5163 = +5163; follow-through +16 **188 vs 246** | `strict_candidate` +5163 = +5163; **all six follow-through pairs equal** (+8..+72) |
| Bowl | `strict_candidate` +3365 = +3365; follow-through equal | unchanged |
| Switcher Race B | `strict_divergence` +4703 vs +4704, first disagreement +4664 | unchanged |
| Dragster Race A | `strict_divergence` +2080 vs +2081; +64 menu 22 vs 246 | unchanged |

**2P RF-015 seed population** (`qa_frontier_original_crosscheck.py paired --native-launcher baldosa`, UR dual-controller `snesref`, lag 0, frames to host 6400, or 9000 for 50024003; entry 1134 = 1134 in all 36 runs). Base `70a5055e…` and candidate `6b5ee7b5…` give **the same disposition, first divergent frame and differing-byte count in all 18 seed × reference pairs** (per-run receipts in the [evidence JSON](../analysis/data/rf017-io-access-clock-order-20261015.json)):

| Seeds | vs Snes9x | vs bsnes |
| --- | --- | --- |
| 50012000, 50012144, 50012215, 50036002, 50036005, 50024003 | exact, 0 bytes | exact, 0 bytes |
| 50036056 | exact | onset knife-edge (first difference 5236) |
| 50024004 | onset knife-edge (5123) | exact |
| 50048000 | one field early (5052): RF-016 | one field early (5052): RF-016 |

**No-input attract black-screen census** (`qa_blank_screen_census.py`, bsnes reference, five loads): base and candidate are identical. 248–276, 401–443 and 3632–3762 match bsnes exactly; the 941–1097 (bsnes 1098) and 1422 (1423) RF-016 residuals are unchanged.

## Hosted re-execution

Two single-case `qa01-event-campaign.yml` dispatches (`selected=zoom-zoo`, `source_followthrough`, `baldosa_refresh_beam_rate` and `baldosa_io_clock_order` all true) ran on clean `ubuntu-22.04` runners from this branch:

- [Run 38779527701](https://github.com/gamesbyian/UR-Recomp/actions/runs/38779527701) (head `3190cd7`): the runner staged both corrections, built the framework's Rust analyzer, regenerated `src/gen` and passed `--verify-gen` with the same counts as locally ("verified 89 generated files: 15484 in-order charge statements, every block total unchanged"). Zoom Zoo result onset +5163 = +5163.
- [Run 38781115852](https://github.com/gamesbyian/UR-Recomp/actions/runs/38781115852) (head `6f4498c`, which includes QA-01's #1650 SRAM consumer): onset +5163 = +5163, and the consumer reports **`Zoo live SRAM first sampled original/native disagreement: +None`**. All six fresh 8 KiB battery images (+8 to +72) now match. QA-01's only previous difference, SRAM `0x10A7` at +64/+72 (original 0x0C, native 0x0D; [QA-01 SRAM discriminator](QA01-ZOO-POSTRESULT-SRAM-ADDRESS-DISCRIMINATOR-20261015.md)), was the one-field return-phase offset this correction removes.

Both case artifacts carry the full producer and SRAM reports. This session could not download them (artifact storage is outside its network allowance), so they still need an independent read.

## Shipping boundary and what remains

- **Not yet staged into the Windows bridge.** It needs a `--cfg-roots` regen on the build host (Python + the framework's Rust analyzer). QA-01 adjudication of the hosted runs above should come before the product carries it.
- **RF-016 (SPC700 rate) remains** the cause of Switcher +4664, 2P seed 50048000 and the attract 941 load. Baldosa clocks the SPC700 at 17,088 cycles per field (`apu_frame_clock.h`, 534 samples × 32, i.e. exactly 60 fields per second). The references use 32,040 Hz × 32 = 17,059.9 per 357,368-clock field. The candidate leaves it untouched.
- **Dragster** keeps its +2080 vs +2081 terminal and +64 follow-through differences, and Switcher its two-frame-late race entry. Separate mechanisms.
