# QA-08: Guarded native P1-only coverage in actual 2P racing

**Status: native bounded negative accepted** (AOT run `38084659523`,
artifact `11681821726`, exact head `da4c1ac`). All native, unit,
Modern and hygiene workflows passed. This experiment remains diagnostic,
enables no player option, and does not alter Original/Remastered gates.

## Why this is a meaningful candidate

Native #1211 captured actual 342-wide 2P running at guest frame 2208, well
after the scripted GO checkpoint at 1989, with both racers visible and
authentic expanded track/HUD pixels. However that frame, like all current
live 342-wide imagery, relies on Original fallback. Its reproducible source
artifact is native run 38083974528, artifact 11681865494. It is excellent
widescreen Original evidence, but does not show why a high-resolution art
reconstruction was undertaken.

The existing independent *production-guarded fixed-256* Baldosa 2P route
from native run 38083079741 or 38083974528 captures a more actionable
gap. Of 484 simulated guest frames after GO, **269** returned
\`p2-pair-gate\` despite valid P1 selection, while the other **215**
returned \`p1-selection-or-art\`; no post-GO guest frame displayed HD in the
measured stock configuration. These are guest-gate counts, not 484
desktop-present frames or proof that all 269 frames have visible approved
P1 artwork. The actual desktop presenter is sparse during scripted turbo.

## Native outcome: conservatism verified, no authorized 2P P1 artwork

The strict evidence `baldosa-evidence/guarded_p1_4x_coverage.json`
observed `status=guarded-p1-host-art-unproven`. After guest GO at **1989**,
there were **484** guest frames through 2473. With unsafe fixture flags
unset and the existing `UR_RACER_HD_P1_ONLY=1` enabled:

| Guarded post-GO guest outcomes | Count |
| --- | ---: |
| `p1-only-occlusion`: existing P1/P2 rectangle-source safety rejected | **269** |
| `p1-selection-or-art`: P1 register/asset unavailable | **215** |
| P1-only safe guest admissions | **0** |
| P1-only real HD host presents | **0** |
| Post-GO authored 4× screenshot witnesses | **0** |

Full native 2,473-frame guest CRC parity passed. No unsafe overlap bypass
was present, and the original 2P source rendering was retained. This
is a correct, actionable negative, **not** a playable Remastered visual
beta. It demonstrates the previous `p2-pair-gate` fallback (269
guest frames under normal guarded settings) cannot simply be bypassed by
painting P1 while keeping P2 Original; the built-in guard correctly
identifies potential stock P2 foreground occlusion.

**Next narrow approach:** independently identify original source-visible
P2-front interaction and exact final-colour ownership in a *moving
post-GO 2P frame* before replacing a rider. Only then consider a narrowly
admitted host P1-only presentation where the added authored silhouette
and P2 preservation can be checked against the actual PPU. Treat
identically coloured ownership as reference research unless a visible
rider would be broken. Evaluate safer 1P gameplay HD independently
before letting this 2P negative block the whole 4K Original beta.

## Controlled trial

\`racer_hd_presenter.cpp\` already implements an opt-in
\`UR_RACER_HD_P1_ONLY=1\` path that uses the **same first-party compositor**.
Its safety guard requires the supported 16/64 split-OBJ mode, forbids
priority rotation, checks stock P2 occlusion against both P1 source
rectangles and preserves the original stock P2 sprites. This experiment
tests the existing implementation, it neither relaxes those checks nor
creates artwork, source placement or another runner.

The pinned native job reuses its previously compiled fixed-width Baldosa
AOT host and existing 2,473-frame 2P event. Exactly one extra *guest
process* runs with that P1-only opt-in, 4x internal density and both unsafe
archival overlap flags **unset**. Guest WRAM CRC must remain byte-for-byte
identical to the independent stock route.

\`tools/check_baldosa_guarded_p1_coverage.py\` rejects missing native GO
provenance, missing guest/host gate evidence, inconsistent guest CRCs,
host HD without corresponding guest admission, use of the historical
unsafe fixture, incorrect dense-PAM geometry or unproven source images.
It reports:

- simulated post-GO guest gates for safely armed P1-only;
- real post-GO desktop *present* frames (distinct denominator);
- actual changed authored-vs-captured-underlay pixels, corroborated by
  a retained native 1024×896 PAM with exact frame identity/SHA256;
- detailed original fallback reasons for the remaining guest frames.

A positive result is **not** a reason to ship mixed Original/Remastered
riders. Source visibility and P2/foreground occlusion under the actual
original full composite require direct visual review and further
counterfactual oracle work. It also remains fixed-width 256×224 and
does not admit widened 342-column authored HD.

The observed blocker for 269 post-GO frames is the stock-P2
occlusion check, not the absence of approved P1 poses. A separate 215
frames also lack eligible P1 art/registration. Record both categories,
review visible races and source pixels, and target safe occlusion
admission before expanding art where it cannot yet be displayed.
The main product target remains coherent, visually polished
Windows 16:9/4K game presentation.
