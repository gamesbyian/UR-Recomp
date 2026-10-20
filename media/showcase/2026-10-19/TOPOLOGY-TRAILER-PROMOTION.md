# Promote real visible topology, not scripts with attractive names

This media edit is deliberately blocked until draft PR [#2002](https://github.com/gamesbyian/UR-Recomp/pull/2002) has produced **genuine native footage** of three different 2P races, where a loop, ramp and hill have actually been seen and independently reviewed. No user-facing film is produced by this branch alone.

The editor `tools/showcase/promote_source_verified_topology_trailers.py` checks that:

- The Looper / MegaJump / Hill Climb or equally source-backed courses were played by the original native executable, with no geometry or guest-state edits.
- Three distinct source games passed their no-video versus recording full WRAM CRC comparison and 900 exact consecutive guest frames each.
- A reviewer recorded actual loop, ramp and hill sightings, real track movement, and source clip ordinals. The approved reel has 240+180+180 real frames, with source SHA and guest-position witnesses.
- The existing 85-second and 58-second horizontal films and their 27-second and 20-second portrait versions match their exact original manifests. Each soundtrack is preserved unchanged, and all original timelines retain their total frame counts.

The 85-second film replaces its original first four seconds of uninteresting side-by-side movement with **four seconds through a real loop**, then replaces the six-second reprise near the finale with **three seconds of actual ramp and three seconds of actual hill**. The 58-second film replaces its ten-second plain 2P passage with the same genuine three-course ten-second reel. The 27-second portrait replaces six seconds of old flat racing with 2s of each actual course; the 20-second portrait uses about 1.67 seconds per course. For portrait exports the full horizontal 2P source raster is fitted inside the existing 9:16 matte without cropping the P2 screen. Scene changes are honest editorial cuts between separate games.

The desired aesthetic is a kinetic **rider separation → loop → ramp takeoff → hill profile** demonstration, with authentic original racer movement and a mix of wide course topology. If the actual native recordings lack one of those features, the editor rejects the source instead of substituting fabricated track geometry or approving a feature inferred from a course name.

Typical invocation (requires both native source approval and existing media PRs as local files):

```sh
python3 tools/showcase/promote_source_verified_topology_trailers.py \
  --ledger /tmp/real-dynamic/dynamic-racing-provenance.json \
  --review /tmp/real-dynamic/accepted-topology-visual-review.json \
  --reel /tmp/real-dynamic/true-hill-loop-ramp-reel.mp4 \
  --reel-provenance /tmp/real-dynamic/true-hill-loop-ramp-reel.provenance.json \
  --original-flagship-provenance media/showcase/2026-10-19/flagship/flagship-provenance.json \
  --original-definitive-provenance media/showcase/2026-10-10/recruitment/definitive-film/definitive-trailer-provenance.json \
  --flagship-master media/showcase/2026-10-19/flagship/ur-recomp-flagship-85s-1080p.mp4 \
  --definitive-master media/showcase/2026-10-10/recruitment/definitive-film/ur-recomp-definitive-recruitment-58s-1080p.mp4 \
  --flagship-vertical media/showcase/2026-10-19/flagship/ur-recomp-flagship-27s-vertical.mp4 \
  --definitive-vertical media/showcase/2026-10-10/recruitment/definitive-film/ur-recomp-recruitment-vertical-20s-1080x1920.mp4 \
  --output-dir media/showcase/2026-10-19/flagship/topology-upgrade
```

This script does not process the additional portrait ambient variant until a matching new verified source SHA is provided to its generator. The old content remains intact as a comparison until all replacements are visually inspected. No successful actual native loop/jump film, finished-beta assertion or whole-game parity claim is made by this documentation.
