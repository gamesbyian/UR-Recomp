# QA-01: executed Bowl tally WRAM offset evidence (2026-10-10)

**Status: original/native original-authentic scored Stunt *diagnostic*, not 45-course acceptance.** The [original/native Bowl paired workflow run 38025090532](https://github.com/gamesbyian/UR-Recomp/actions/runs/38025090532) and its artifact **11659973901** emitted the **actual offset-only report**, not a hypothetical source diff. The job's artifact ZIP SHA-256 was `5fc790a32137576f6b2d796f9fbfb68d417c910a11b0e51a83c1950f0d53d62b`. Preserve the exact source-observed eight-frame report at [`analysis/data/bowl-original-native-observed-tally-wram-offsets-20261010.json`](../analysis/data/bowl-original-native-observed-tally-wram-offsets-20261010.json) before the Actions retention period expires. It contains **addresses and counts only**, no ROM, SRAM, controller contents or guest memory byte values.

The previous [count-only original/native witness](../analysis/data/bowl-tally-full-guest-same-host-eight-frame-20261009.json) is an independent crosscheck. The archived 2014 original 45-second scored Bowl Stunt and the pinned Baldosa guest matched **28/28 sampled active semantic states** and both emitted the actual PPU **MIKE 764**, qualifier **68**. Both observe stable tally at **absolute host frame 4279**, terminal result at **4349**; relative to the separately measured course entry, the native result precedes the reference by **one frame**. This has **not** been attributed to an incorrect game rule, instruction PC, NMI phase, or controller latch.

## Actual eight-frame address result

| Tally-relative | Absolute host | WRAM diff bytes | VRAM | CGRAM | Selected discriminators |
|---:|---:|---:|---:|---:|---|
| +54 | 4333 | 6 | 0 | 0 | `7E:01DB/1DD/1DF/1E0/1E1/1E3` |
| +60 | 4339 | 6 | 0 | 0 | `7E:01E3/1E8/1E9/1EA/1EB/1EC` |
| +64 | 4343 | 50 | 2 | 0 | menu timers, animation frames, 17 OAM-shadow offsets, `7E:01D8–01F0` |
| +65 | 4344 | 14 | 0 | 0 | clustered `7E:01D8–01EA` |
| +66 | 4345 | 6 | 0 | 0 | `7E:01D8/1DA/1DD/1DF/1E2/1EE` |
| +67 | 4346 | 6 | 0 | 0 | exactly same six addresses as +66 |
| +68 | 4347 | 22 | 0 | 0 | `7E:0072/73` plus `01D8–01F0` |
| +69 | 4348 | 16 | 0 | 0 | `7E:0072` plus `01D8–01F3` |

There are **57 unique WRAM-offset addresses** across all eight frames, with **no offset common to every frame**. The first two six-byte sets share **only `7E:01E3`**. Thus the earlier count-only conjecture that a constant six-byte mismatch persists through the tally is **falsified**. The same six-byte set at +66/+67 *does* persist across those **two** sampled frames, and nothing more should be inferred.

Known source labels from [the pinned imported Baldosa WRAM catalogue](../reference/imported/reverse-engineering/baldosa-uniracers-recomp/decomp/ram.txt), with all ownership still tentative:

- `7E:0072–0073`: `wJoy1Held` is a **two-byte** source-map word. Its **high byte `7E:0073` differs already at tally +64 / absolute host 4343**; both bytes differ at +68 / host 4347, and only low byte `7E:0072` differs at +69 / host 4348. These are *captured WRAM offsets*, not read-out controller masks or proof of modified inputs. Never retime the controller movie to suppress them.
- `7E:0089` / `7E:008B`: `wMenuIdleTimer` / `wMenuAnimTimer` (at +64).
- `7E:0187–0193`: +64 contains all eight bytes of `wMenuAnimFrames` at `0187..018E`, separately named `wMenuAnimPhase` at `0191`, and **unattributed** `0192/0193`. The full 65C816 stack-page address range does not mean every resident byte is a stack push.
- `7E:01D8–01F3`: **25 distinct low-WRAM offsets** without a specific label in the pinned `ram.txt`. Their changing pattern is the dominant repeated cluster. Do **not** silently assign a specific sprite/physics register name.
- `7E:0B82–0BCA`: **17 OAM-shadow offsets**, all at +64 only; the source catalogue labels them `wOamBuf/wOamBuffer`. VRAM differs at only **`0x0245C` and `0x0249C`** on the same host frame. All CGRAM comparisons match.

**Interpretation:** the sampled evidence is compatible with animation/menu-transition staging or a narrow host observation phase mismatch. It provides **no confirmed scoring, lap, race finish or other guest gameplay semantics difference**. The exact result-menu transition (Bowl `0x2F` through host 4343, `0xD8` from 4344, final `0x18` at 4349) is shared by both engines. Do not patch an input offset or change Baldosa guest rules based on these addresses.

**Cheapest next independent discriminator:** obtain original and native **instruction-owner/phase** evidence for a *small selected subset* of the frequently varying `01D8..01F3` addresses across +54/+60/+64/+66/+68, while distinguishing `7E:0072` (input held), `7E:0089` (menu timer), and one OAM-shadow offset as negative controls. Tie original CPU-PC/NMI labels and native generated-function ownership to the same source frame/input on both engines, with exact original and native guest-relative and absolute host-frame anchors. Prefer one shared pinned guest build; do not launch another generic all-course harness. The result to seek is the **earliest genuine source-event divergence**, not more arbitrary postresult snapshots.

Use the existing mapper against the committed exact report (no emulator or copyrighted assets needed):

```bash
python3 tools/annotate_bowl_guest_memory_offsets.py \
  --report analysis/data/bowl-original-native-observed-tally-wram-offsets-20261010.json \
  --out /tmp/bowl-symbol-labels.json
python3 -m unittest discover -s tests/unit -p test_bowl_observed_tally_wram_offsets.py
```

**Release decision unchanged:** Zoo and Bowl remain completed *investigative candidates*, but official **0/45** USA course-complete independently admitted. The observed one-frame relative onset mismatch remains open. Source address labels are only annotations, not runtime causality, and the comparison includes no per-byte guest-state data.


## Reconciled latch-before-menu-handoff, existing witnesses only (2026-10-14)

An exact second-source read of the **independently executed** [offset evidence](../analysis/data/bowl-original-native-observed-tally-wram-offsets-20261010.json) and [count-only witness](../analysis/data/bowl-tally-full-guest-same-host-eight-frame-20261009.json) corrects the earlier text's `wJoy1Held` timing. The **first observed difference in either byte** of that 16-bit word is the **high byte at host 4343 (tally +64)**, **one sampled frame before both guests change menu `0x2F→0xD8` at 4344**, and six host frames before the shared `0x18` scored result at 4349. The first two selected snapshots, hosts 4333 and 4339, differ at only six `7E:01xx` addresses each, which are in the architectural stack page but have no executed original CPU push/read attribution for this Bowl event. At +64, the 50 WRAM offsets split into a high joypad-held word byte, two menu timing bytes, eight named animation frame bytes, one named colour-phase byte, two still-unattributed `0192/0193` bytes, nineteen other `01xx` page bytes and seventeen OAM-shadow bytes. VRAM differs in two offsets only at this host; CGRAM remains equal.

`tools/qa01_bowl_tally_latch_crosswalk.py` now **recomputes** this crosswalk entirely offline from those two archived independently executed runs, requiring unchanged exact run/artifact identities, tally/result host anchors, eight identical per-host memory-difference counts, complete sorted captured offsets, stage identity, zero raw-memory retention and zero release credit. Its tests independently pin the input-word high/low chronology and the symbolic names against the retained imported `decomp/ram.txt`, and reject altered hosts, invented acceptance, truncated profiles and substituted sources. This repair is a *classification of existing exact capture addresses*, not a newly executed native-vs-original trace or proof of differing button masks.

**Next bounded causal question for Bowl after the two-player writer replay:** on already selected host **4342–4344**, did the original/native controller interface supply and consume the same P1 mask, and did the actual original CPU NMI/input-latch writer update `7E:0073` before or after the snapshot? Capture the authentic source PC and guest beam/host phase and compare the native generated writer **without globally shifting any input**. The contemporaneous `0089/008B` menu timers are useful original-defined progression controls; the OAM/VRAM deltas alone are presentation evidence and belong to their own owner. If an original/native mask is proven unequal, correct the input-transport provenance first; if consumed masks are equal, isolate the smallest instruction/observation-phase difference before touching source gameplay. **Bowl remains an actual MIKE-764 result candidate, not an admitted USA event; ledger 0/45 unchanged.**


**Static source-region lead, not an executed Bowl PC:** The preserved Baldosa symbol catalogue identifies `80:D1DB Input_ReadPads`. The independent Nitrodon bank-80 annotated bytes at `80:D1DE AE 18 42 LDX $4218`, `80:D1E1 86 72 STX $72`, `80:D1E3 AE 1A 42 LDX $421A`, and `80:D1E6 86 74 STX $74` expose the direct original joypad hardware-to-`$72/$74` copy candidate. The routine begins `80:D1DB JSR $9318`, a separate existing OAM-upload call; the executed input X-register width, CPU frame, source PC, stack/caller and VBlank timing are **not yet proven** for Bowl +64. Bank 80 also has alternative direct reads of `$4218` at `80:85E4` and `80:87E9` into distinct `$030D` fields, so not every hardware joypad read updates `$72`. The new crosswalk carries this **static, explicitly unexecuted writer candidate** and pins its archive bytes/symbol in unit tests. This is a much narrower starting PC for an eventual original opcode observer than instrumenting all of SNES WRAM; no runtime or release verdict is made from it.

**Static potential read consumers:** The same archived bank-80 source has `80:B6BE Input_IsAnyButtonHeld` with `80:B6BF REP #$20; 80:B6CA LDA $72; 80:B6CC BIT #$FFF0`, and `80:B708 Input_IsConfirmHeld` with `80:B709 REP #$20; 80:B714 LDA $72; 80:B716 BIT #$9080`. Those original-source instructions test **16-bit** joypad-held masks, including bits in `7E:0073`. Therefore a high-byte difference is potentially relevant to result/menu decisions rather than an automatically disposable cosmetic residue. Their actual execution during Bowl host 4343 has **not** been established, and neither the differing bit values nor the intended/consumed P1 input masks are present in the old offset-only artifact. The offline crosswalk records both as candidates explicitly marked **not yet executed**. The next phase-relevant result is whether original/native reach one of these branch consumers with matching inputs and bitmasks in the authentic source timing window.
