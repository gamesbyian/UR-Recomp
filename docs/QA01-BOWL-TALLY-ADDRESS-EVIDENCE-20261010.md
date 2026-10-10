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

- `7E:0072–0073`: `wJoy1Held` (at +68/+69 only); **not** proof of an altered human input stream or a one-frame controller rebase.
- `7E:0089` / `7E:008B`: `wMenuIdleTimer` / `wMenuAnimTimer` (at +64).
- `7E:0187–0193`: some bytes within `wMenuAnimFrames` and adjacent menu-animation state (at +64). The catalogue's named `wMenuAnimFrames` span is `7E:0187..018E`, so later offsets must not inherit that name.
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
