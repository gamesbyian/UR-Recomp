# Modern original-racer hero: source clip inventory (2026-10-20)

**Status:** source-registration discrimination only, not a native hero shipment, original-emulator frame-timing qualification, ROM-raster acceptance or user art approval. Shipping Modern menu animation remains separately owned by [PR #2042](https://github.com/gamesbyian/UR-Recomp/pull/2042), and the combined native integration by [PR #2053](https://github.com/gamesbyian/UR-Recomp/pull/2053). The source-exact Windows drawable review belongs to [PR #2041](https://github.com/gamesbyian/UR-Recomp/pull/2041).

## Decision and stop rule

**Decision:** do we already have other genuine, contiguous *registered* racer composition windows that might be useful as bounded entry/reaction/hold sequences, without recycling the current eight-frame 1213–1220 clip into an unsupported endless idle loop?

**Cheapest discriminator:** inspect the current register `analysis/data/racer-hd-replacement-prototype.json` and the canonical USA original-ROM asset provenance `analysis/generated/racer-presentation-family.json`, not regenerated 4× art, a synthetic animation or a second gameplay renderer.

**Results:** `tools/audit_modern_hero_source_clips.py` emits a reproducible JSON-only source-registration receipt for three windows:

| Candidate | Registered guest frames | Length | Appropriate *potential* use |
| --- | --- | --- | --- |
| Root entry response | 1213–1220 | 8 | Existing #2042 bounded source-pose experiment |
| Settle / recover | 1230–1239 | 10 | A separately qualified reaction, with a genuine long registered composition hold |
| Long hold / recovery | 1244–1252 | 9 | A separately qualified hold-to-recovery reaction |

Source registration lists a *complete P1 composition representation ID*, not merely a primary semantic pose. Distinct registered representation IDs can still rasterize identically; independently compare source Original pixels before assigning expressive labels. Chronological registered native guest labels do not independently establish emulator/guest clock cadence. The report therefore explicitly refuses `may_reverse_or_loop` for **all** clips and records outstanding raster/native/visual approval. No pose pixels, manufactured "in-between" frames, ROM bytes, gameplay animation, procedural 4× model or hypothetical 3D rotation are generated or committed.

Run:

```sh
python3 tools/audit_modern_hero_source_clips.py --output /tmp/modern-hero-source-clips.json
python3 -m unittest tests.unit.test_audit_modern_hero_source_clips
```

The inventory tests inspect the repository's real source register and fail closed on wrong ROM identity, absent/reordered/duplicated frames, unaccepted status, changed P1 palette, composition-guard disagreement, ambiguous representation IDs and invented source windows. The output is intentionally ephemeral until a renderer consumer needs a pinned manifest.

## Private original-raster plate proof (additional deliverable)

A separately bounded, explicit-ROM opt-in producer `tools/build_modern_hero_reaction_plates.py` uses the **existing** `prototype_racer_hd_replacement.build_stock_rgba` Original 64×64 raster compositor to extract either *settle-and-recover* or *long-hold-recovery* in the accepted registered order. No new sprite decoder, original-content distributor, HD procedure or saved in-game asset is introduced. The producer validates the USA ROM SHA256 and exact 2,097,152 bytes, registered P1 semantic/palette and composition, per-pose stock contact/pivot, plausible occupied pixels, chronological frame count and identical pixels for repeated registration IDs. It refuses an entirely static candidate. It writes 64×64 original lossless PNG review plates and a SHA-bound JSON manifest **only into the explicitly requested private output folder**, never the git tree.

```sh
python3 tools/build_modern_hero_reaction_plates.py \
  --rom reference/roms/retail/Uniracers_USA.sfc \
  --clip settle-and-recover \
  --out-dir /tmp/modern-original-reaction-plates
python3 -m unittest tests.unit.test_build_modern_hero_reaction_plates
```

The unit tests generate synthetic images under a **synthetic non-retail ROM identity** and patch only the isolated test process. These are rejection-path tests, never the user's actual art or native screenshots. Real source raster generation must be performed privately with a verified canonical ROM and visually compared to the independently captured original/native game before promoting a new reaction animation. Source plates do not prove visible on-screen 342×224 or 256×224 behaviour. The currently integrated eight-pose hero clip and motion module in #2042 are untouched.


## Three-project reuse preflight and interfaces

Reused UR's registered original source raster composition and existing native Modern/Baldosa interface, as prescribed by the `modern-product` lane of `tools/select_three_project_reuse.py --lane modern-product --include-conditional`. Baldosa's native guest/host is authoritative for actual game execution; Malmazuke's independent PAL frontend and renderer remain architectural reference only and are **not** substituted for the USA stock P1 source. No new guest emulation, second animation scheduler, CI experiment, native hero artwork or sprite copies.

For #2042: if the current experimental original P1 pose provider is extended beyond eight frames, preserve exact source representation and guest-frame order, revalidate original ROM source rasters and palette/companion occupancy, and distinguish 60Hz guest cadence from injected host UI ticks. A 10-frame clip requires a separately bounded frame-count contract rather than silently modulo-wrapping the current eight-frame motion ordinal. Keep source art opt-in/labelled until reviewed, with immediate source-frame holds and selection interruptions tested. #2038/#2040/#2043 retain grammar, destination and title composition ownership, respectively.

For integration/QA: only a generated source-verified asset built into an exact native PE, captured **from that native process** in 256×224 and 342×224 at final SDL output with 4:3/16:9, 1×/4× comparison, reduced-motion, confirm/cancel/return, visible source character likeness and independent artistic approval can close final presentation. This source audit grants no QA01/QA08/Windows release credit. The October 10 procedural 4× likeness veto remains in force.

**Next relevant step:** let #2042's owner select a single suitable new clip after privately extracting original P1 rasters, compare exact consecutive rendered pixel frames, then submit one source-bound native opt-in capture through the existing #2041/#2053 acceptance machinery. If no clean registered transition proves a coherent reaction, retain the last verified still pose rather than manufacturing a loop.
