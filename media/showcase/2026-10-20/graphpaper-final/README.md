# Graph-paper illustrated recruitment: final editorial candidate

**October 20, 2026.** This is a reproducible **media-only** replacement for the October 20 blue action film. It does not change gameplay, the native executable, fidelity status, or the frontend. The final render and source references are on this branch.

## Films

| Deliverable | Details | SHA-256 |
| --- | --- | --- |
| [Flagship 80 seconds](ur-recomp-graphpaper-action-80s-1080p.mp4) | 1920×1080, 60 fps, 4,800 frames | `367375ef998ca951eca45a1383ffa33014d4975780eb21988d5a7a19f945888b` |
| [Portrait 27 seconds](ur-recomp-graphpaper-action-27s-vertical.mp4) | 1080×1920, 60 fps, 1,620 frames | `5d61045a5f4cf4fa1c305953003bbc7c893e3f304dc65bd5e89097d067a2e8e1` |
| [Real Jumps-frame poster](ur-recomp-graphpaper-action-poster.png) | Native three-course action source ordinal 570, editorial title bands | `37905919ac289e3db63895551272d09e7d4c1c15444ec83543799c1685ba6ac3` |

See [complete render/source manifest](flagship-provenance.json) for shot boundaries, exact source SHA identities, frame counts, and caveats. [CI 39393076502](https://github.com/gamesbyian/UR-Recomp/actions/runs/39393076502) completed successfully; it checked four decoded output samples, exact source and output hashes, the 12 source panels, and total film frame counts. Its deliverables are committed here. The one-shot workflow deleted itself after publication.

## Review frames

- [Moving widescreen reveal](qa-reveal-frame-0270.png) at film ordinal 270; the 7-second genuine 256→342 reveal remains.
- [Windows card](qa-windows-frame-1000.png) at film ordinal 1000; editorial explanation, not recorded Windows gameplay.
- [Native action](qa-action-frame-3820.png) at film ordinal 3820; native 2P MegaJump/Jumps/Looper footage survives.
- [Final contribution invitation](qa-cta-frame-4600.png) at film ordinal 4600; illustrated card.
- [12 individual source plates](cards/) include all documentary video holders, animations, raster and parity frames, alongside all three static cards.

## Graphic source and ethics

The two **unchanged, owner-supplied** black-pen drawings in [graphpaper-source](../graphpaper-source/) define the layout. All twelve 1920×1080 plates use a light cream graph-paper field, the genuine source logo in the header and the genuine track/rider at the foot, retaining pencil/ink cross-hatching and construction marks. The left footer joins into a newly drawn continuation; no regenerated alteration of source unicycle or source track geometry. The animated documentary plates overlay real, existing footage on an explicitly editorial cream frame.

The input film retains its authenticated native action montage, comprising **three separate 300-frame sessions**, MegaJump hills, Jumps with an actual airborne inverted racer, and rolling Looper terrain. This does not prove a complete Looper revolution, scored flip or Hill Climb. The original October 10 grey provisional menus are omitted. The technical, 4× art, pixel parity and 4K claims remain explicitly bounded as in the manifest. No sampled commercial soundtrack or synthesized gameplay frames.

## Reproduction

```sh
python3 tools/showcase/graph_paper_trailer_art_direction.py \
  --logo media/showcase/2026-10-20/graphpaper-source/uniracers_graphpaper_logo.jpg \
  --track media/showcase/2026-10-20/graphpaper-source/uniracers_track_unicycle.jpg \
  --out /tmp/ur-graphpaper-cards
python3 tools/showcase/build_graphpaper_recruitment_20261020.py \
  --outdir /tmp/ur-graphpaper-final
```

Requires Pillow, FFmpeg/ffprobe and all exact source videos already tracked by the repository. Full regeneration is source SHA checked and fails on a missing/changed input. Preserve the generated manifest alongside any published new revision.

## Remaining acceptance boundaries

Technical render/source validation passed. The panel-family art was visually inspected locally, but a **complete human screening of both entire films** and final aesthetic approval of the filmed compositions have not been recorded. Review all decoded shots and audio before promotional circulation. Redistribution/public-release rights for historical game artwork and captured source footage also require separate confirmation. The video is recruitment/editorial evidence, **not** a finished beta or complete original/native gameplay-parity announcement.
