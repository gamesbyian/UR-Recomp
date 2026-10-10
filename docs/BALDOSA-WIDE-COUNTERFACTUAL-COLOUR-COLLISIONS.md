# QA-08: live slot-98 colour collisions and post-PPU attribution

Status: **measured native PPU evidence, not a shipping HD mask**.

The Baldosa AOT acceptance [run 38073654745](https://github.com/gamesbyian/UR-Recomp/actions/runs/38073654745)
from merged PR #1172 supplied a 342×224 original stock PPU PAM, a
read-only isolated slot-98 source PPU PAM, a **different native guest
process** removing only OAM slot 98 at guest frame 1856, and complete
matching guest-frame WRAM CRCs. All three images have exact same-frame
provenance. The native checker recorded 321 emitted slot-98 pixels,
307 final-PPU RGBA changes and **zero** changed pixels outside the
isolated slot's emitted-alpha footprint.

We reopened the retained machine artifact `baldosa-native-spike-evidence`
(artifact 11677962498) and compared this front slot with its actual
concurrent read-only rear slot **99**, not an assumed sprite shape:

| Original top-half classification | Exact native pixels |
| --- | ---: |
| Slot-98 emitted pixels | 321 |
| Changed after removing 98 | 307 |
| Changed, exposing slot-99 RGB | 143 |
| Changed, exposing a non-99 RGB | 164 |
| Unchanged despite slot-98 alpha | **14** |
| Of these, exact same-colour slot-99 overlap | **14/14** |
| Changed pixels outside slot-98 source | 0 |

The 14 unchanged pixels are precisely inside the 98/99 overlapping
OAM source rectangles and emit the **same three RGB channel values** in
both source planes. In the removal render the revealed RGB still
matches slot 99 at those same positions, so source-98 disappearance is
not visible in the resulting colour. This explains the discrepancy
without inventing a hidden sprite. It does **not** prove that colour
match always equals correct source ownership or establish a full
composite z-buffer winner mask.

The existing canonical `analyze_baldosa_wide_obj_overlap.py` now
accepts *optional*, **authenticated** counterfactual evidence using
`--removed-pam`, `--removed-report`, and `--removed-front-slot`.
It recomputes these classes from all source pixels and validates the
already-existing three-process native checksum/digest report before
attaching `verified_final_counterfactual`. No report can grant
`release_hd_admission`, even when every colour class is explained.

Example using the already captured original/source/removal evidence:

```sh
python3 tools/analyze_baldosa_wide_obj_overlap.py \
  --main-pam baldosa-ws342-captures/ur-baldosa-ws342-001856.pam \
  --slot-dir baldosa-ws342-obj-slots \
  --reports baldosa-evidence \
  --frame 1856 \
  --removed-pam baldosa-ws342-counterfactual-slot98/ur-baldosa-ws342-001856.pam \
  --removed-report baldosa-evidence/ws342_slot98_final_visibility_1856.json \
  --removed-front-slot 98 \
  --out baldosa-evidence/ws342_obj_overlap_with_slot98_counterfactual.json
```

**Shipping decision:** retain the Original 342-wide OAM renderer.
Differences between stock and removal prove a lower bound on final
pixel influence; source alpha and colour equality do not by themselves
prove the precise compositing owner, especially when same-coloured
front/rear art overlaps. Complete priority/z-order and BG/window
occlusion proof is still necessary before destructive removal and
authored 4× HD substitution.

Future native runs should repeat this with slot 96 in the bottom
viewport and a later moving frame. The present real result is not
original-emulator visual parity, full-event acceptance or physical 4K.
