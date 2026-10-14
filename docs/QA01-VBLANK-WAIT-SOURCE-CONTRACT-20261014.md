# QA-01: USA two-edge VBlank wait and RF-014 provenance (2026-10-14)

**Scope:** Independent gameplay/source interpretation of research PR #1537 (RF-014), using archived USA bank-80 opcode bytes, Baldosa's pinned USA RAM-symbol reference, and pinned upstream framework commits. No emulator was re-executed for this **static** investigation. It does not own #1537, the research queue, a production timing fix or the independent release ledger. Official complete USA event credit: **0/45**.

## Original source-backed mechanism

Verified verbatim by `tools/qa01_vblank_wait_source_contract.py` and fail-closed synthetic tests:

| Original USA PC | Executed operation in archived listing | Exact conditional meaning |
| --- | --- | --- |
| `80:FAC9` | Long call to `82:8035` | Before each first-edge poll |
| `80:FACD` / `80:FAD0` | `LDA $4212` / `BMI $FAC9` | Continue while HVBJOY bit 7 = 1; wait for VBlank **clear** |
| `80:FAD2` | Long call to `82:8035` | Before each second-edge poll |
| `80:FAD6` / `80:FAD9` | `LDA $4212` / `BPL $FAD2` | Continue while bit 7 = 0; wait for next VBlank **set** |
| `80:FADB` | `JSR $FADF` | Run continuation after both observed edges |
| `80:FAE2` / `80:FAE6..FAE8` | `DEC $C6`, reload `$1F` when negative | The 32-state cursor-animation counter |
| `80:FAF2..FAF9` | lookup indexed by `$C6 >> 1`, stores to `$0BDE/$0BFE` | Cursor-animation output, directly downstream of wait |

The imported Baldosa USA RAM map calls `7E:00C6` **`wCursorAnimTimer` (1 byte)**, not a universal game-frame clock. A `$C6` decrement is evidence consistent with executing this particular original wait's continuation. A host interval with fewer decrements is a meaningful *wait-throughput discrepancy*, especially in menus, but it cannot alone distinguish (a) source wait executing less often, (b) unrelated source writes to `$C6` (including the documented direct-page restore), (c) sampling the frame before versus after its write, and (d) true missing simulated gameplay updates. A modulo-32 census with fewer than 32 ticks per sampling interval does **not** detect other legitimate writes that happen to fall in the same modulo residue or change a value without exceeding the host span. The actual writer PC is the discriminator.

The static sequence also contains repeated calls to `82:8035`; whether translated code or tier-down/scheduler boundaries change their cost is an independent implementation question. The listing alone proves neither that those calls were executed in RF-014 nor what time they consume.

## Pinned cross-project reuse preflight

`AGENTS.md` instructs running `select_three_project_reuse.py --lane <lane> --include-conditional`. Its current lane catalog has **no `qa01-gameplay` selector**, so the scoped work uses the `all` registry and filters for the relevant proven entries, without pretending a nonexistent lane ran. Applicable decisions:

- `first-divergence` (P0, now, release-qa): reuse UR's `compare_wram_checkpoints` and `check_framedump_identity` before building another comparator, and consult Baldosa `tools/firstdiff.py` and Malmazuke replay evidence.
- `route-input-identity` (P0, now): preserve exact controller masks, observed consumption and race-entry phase. Original/native absolute frame equality does not imply equivalent race-relative input.
- `reference-multiple-oracles` and `full-event-acceptance` (P0): Snes9x **and** Beetle-bsnes with canonical USA ROM; no partial or source-only release credit.
- `framework-delta-porting` (P1, *conditional*): upstream changes can be selectively piloted **after** a measured runtime defect and before/after independent comparison, never as a global framework upgrade.

Source matrix: `analysis/data/three-project-apparatus-capability-matrix-20261010.json`; pinned Baldosa `baldosa/snesrecomp@075fbe4c8e0d97b0013be541795c39cb644a9709`; UR framework baseline `cd5875cbdaf19f5e324272b1f8051d671fce9215`; malmazuke `unirally-reconstruction@42d444594641d23f5d3c15da7b7c454bb5180e43`.

### Two particularly relevant post-pin Baldosa changes

1. **`96b7e9f50c81f193fddc9d45818790a99c6078d4`**: Clock-driven HVBJOY. The newer beam driver calls `snes_set_beam_clock_driven(true)` each frame. Under that explicit policy, `ReadRegOpenBus(0x4212)` synchronizes to `g_cpu.master_cycles`, while `snes_readReg(0x4212)` avoids the legacy `snes_advance_beam(64)` synthetic tick. Upstream reports its own title countdown previously ran at half speed. **That observation does not establish the present UR transition's smaller deficit or license a direct 64-clock removal**. The old UR pinned framework does not itself contain the later beam-driver source path, so this is **not** a safe three-line cherry-pick.
2. **`b7b4318fba3ad7695e4e37eaf103e9e5c41fc806`**: Opt-in `paced_bus` generated-code mode. Separates opcode/operand fetch clocks, paced guest data accesses and internal cycles, aligning AOT master-clock accounting with interpreter tier in that upstream configuration. Its tests are valuable, but it changes multiple generator/runtime surfaces; isolated beam-policy evidence should precede a broad recompilation experiment.

Existing UR authority already records both candidates: `docs/BALDOSA-FRAMEWORK-DELTA-20261009.md`. These are separate mechanism hypotheses, not two patches to apply simultaneously by default.

## RF-014 discriminating experiment, before any repair

**Decision:** Does native genuinely execute fewer completed `80:FADF` wait routines because of an incorrect beam/poll/scheduler implementation, or do the same guest steps land on different host/sample phases?

**Baselines and population:** Use the *same* exact USA ROM and controller stream for the original Snes9x, independent Beetle-bsnes and both generic / Modern native binaries, with executable and core hashes, source commit, build options, and input SHA. Preserve the original stock 2P host 426–446 transition, a stable menu 20-frame control window, delayed-prefix k=1/k=2 entry routes, and the no-input attract reproduction. The RF-014 773 vs 801/802 and 1311 vs 1326/1327 counts are research's **candidate observations**, not independently re-executed here.

**Minimum observer at the original/source CPU boundary:** Record actual hits at `80:FAC9`, `80:FACD`, `80:FAD0`, `80:FAD2`, `80:FAD6`, `80:FAD9`, `80:FADB` and `80:FAE2`, plus any *other* `7E:00C6` writer with opcode, effective address and DBR. Track `$4212` read values (especially bit 7), CPU PBR:PC, P, S, master cycles, SNES beam line/dot, original NMI entry count and timing, decoded race/scene state, WRAM sample phase, and host-frame entry/exit. Native instrumentation must identify original translated PC/tier-down/helper participation, not merely a C function name. Reuse existing source original opcode/WRAM observation and native trace infrastructure; do not introduce another automated factory. Scope tracing to host **426–446** before collecting large runs.

**Phase and attribution controls:** Original `ICPU.Frame`, native `snes_frame_counter`, guest `$C6`, and host-script `wait/dump` are different clocks. Align actual inputs at their consumed guest phase, record observer capture point relative to NMI and `80:FAE2`, and compare both clocks. A raw `$C6` match does not prove identical executed instruction histories. If any counter changes outside `80:FAE2/FAE8` or the original runtime window uses a different wait, classify it as **not adjudicated**, not "one missed game frame."

**Expected outcomes:**

- Same executed `FAE2` count and source-state progression across corresponding phases, shifted host observation => **observer/scheduler phase**; preserve simulator code.
- Fewer native `FAE2` hits, with original/native `$4212` read transitions or master-clock advancement demonstrably unequal at the **first** missing edge => candidate **beam/poll timing defect**, narrow A/B against the pinned upstream behavior and validate NMI/2P/attract/terminal regression before any port.
- Same `$4212` edges but native extra tier-down, instruction-cycle/host scheduling stalls and delayed continuation => **scheduler or AOT cost**; investigate call `82:8035` and paced bus timing before changing beam semantics.
- `$C6` value differs while actual `FAE2` counts do not, or a restore writes it => **counter aliasing**, not proved missing guest work.
- Results agree at race-relative gameplay checkpoints but terminal source state diverges => preserve specific terminal event oracle failure pending result caller.

**Stop:** Capture the earliest source-backed differential instruction/event and its consuming lifecycle impact. If unchanged source-bounded trace supports only a different host phase or source wait frequency, report that limit without patching or certifying full-event parity. A repair requires a pre-patch failing exact witness, post-patch corrected exact witness, and no regression across two independent original cores.

## Second priority: closest complete-event witness

**USA Zoom Zoo Circuit** is the best-documented complete-scored candidate, not an accepted event. Both original and native reach lap zero and the exact displayed MIKE/BRONSEN results; native reaches the intermediate restore and result transition roughly one guest-relative frame early, with transient post-result WRAM/PPU differences. Source `$009F` is the **two-byte `wTextPos` field**, so its raw values cannot independently define race phases (#1543). The executed original transition is localized around guest-relative +5155..+5163. Once the transition-frame cause is assessed, replay the **unchanged** Zoo input through genuine result, menu restoration and persistence, and have the independent QA owner certify or reject one exact candidate. Switcher Race B's real MIKE 1:08.81 result likewise still fails strict guest-relative terminal timing despite same-host text.

This source contract changes no native gameplay, Modern/graphics code, research scheduling, comparison thresholds, ROM, SRAM or release-quality ledger.
