## Final accepted source-verified action-film render

The new definitive playable review candidate is in [../blue-action-final](../blue-action-final/flagship-provenance.json). It supersedes the earlier blue-cut prototype, which is retained solely as an editing audit.

- [80-second 1080p source-faithful recruitment film](../blue-action-final/ur-recomp-blue-action-80s-1080p.mp4), SHA-256 `78ce2109ba1f2133657d665583ab66b94077b173e8dd6a4eb79c4dfec9cd4a0b`.
- [27-second vertical recruitment short](../blue-action-final/ur-recomp-blue-action-27s-vertical.mp4), SHA-256 `7ae46fca497c0a53e4bbc59b4ee2700844fcdc595edc0c63e27ce705fd5e2ded`.
- [Poster from the real upside-down Jumps rider](../blue-action-final/ur-recomp-blue-action-poster.png), SHA-256 `f3dd40d8c18bf88624d0ec3e41e705dd0e800561136ea16efcfeec46613762aa`.
- [Accepted exact source identities, three course cuts and 80-second timeline](../blue-action-final/flagship-provenance.json).
- [14 independently decoded output frame witnesses](../blue-action-final/blue-action-review.json).

The rendering stage passed in [Actions run 39381149305](https://github.com/gamesbyian/UR-Recomp/actions/runs/39381149305); the encoding result was rescued, source-audited, poster-generated and published without redundant re-encoding in [run 39381556246](https://github.com/gamesbyian/UR-Recomp/actions/runs/39381556246). No temporary editing workflows remain in the branch. Independent visual screening of the actual new cut sampled its authentic blue-framed reveal, course topography, separated players, Jumps inverted airborne rider, engineering/animation cards and final CTA. Full human play-through and media public redistribution rights are separate.

# Blue-box-art editorial overhaul, October 20

The three user-supplied references establish the visual brief: bright blue rather than grey/black cards, chunky yellow lettering with purple dimensional shadows, looping rainbow tubular track, gloss on the wheel/body, playful spots of confetti and a consistent Uniracers-inspired unicycle footer. This is an independently authored editorial treatment and **does not reproduce the game's official logo or claim the original designers authored these materials**.

The overhaul is implemented in `tools/showcase/blue_trailer_art_direction.py`, which generates all three static statement cards **and** the shared moving-graphics/technical-video presentation frames. `tools/showcase/build_flagship_recruitment_20261019.py` now imports that deterministic art renderer, so the widescreen reveal, code-to-C explanation, raster-xray, parity, sprite study and animation archaeology all use matching 1920×1080 blue storyboards rather than miscellaneous grey photographic holders.

The obsolete October 10 Modern prototype capture with its grey “SOON” menus is **removed**. The initial design draft was 75s/23s; it is now superseded by the actual 80s/27s action-footage edit. Both retain the same verified sources for actual gameplay. The storyline describes reconstruction concretely, with no “one game, bigger project”, “build the next version” or other catchphrase on the cards. The final contribution invitation names the actual disciplines needed.

**Outstanding:** The earlier flat original 2P footage is now replaced by separately verified three-course native footage. The broader capture research remains in [PR #2002](https://github.com/gamesbyian/UR-Recomp/pull/2002) is producing source-bound topology and asynchronous-player capture candidates. Neither jumping nor loops nor ramps are to be claimed or spliced into this film until independently decoded moving captures actually show them. The refreshed edit makes the art consistent first, then leaves the real race-footage improvement as a separate evidence gate.

Reproduction:
```sh
python3 tools/showcase/blue_trailer_art_direction.py --out /tmp/ur-blue-design
python3 tools/showcase/build_flagship_recruitment_20261019.py --outdir media/showcase/2026-10-20/blue-cut
```

Requires Pillow, FFmpeg and the already merged exact-source video SHA identities. The resulting frame hashes, source audit and render witnesses are required before any merge.

## Genuine newer course footage now integrated in the next render

New native capture assets merged to `main` since the initial design run: [MegaJump, Jumps and Looper source-verified action footage](../../2026-10-19/dynamic-native-2p/ACCEPTED-FOOTAGE.md) and [precise montage-source provenance](../../2026-10-19/dynamic-native-2p/dynamic-three-course-reel-provenance.json). The montage consists of three **different genuine running-game sessions** with 300 consecutive frames each and acknowledged hard editorial cuts. The updated film uses all 15 seconds of this independently qualified footage: MegaJump (steep hills/separated riders), Jumps (inverted airborne unicycle at verified Jumps source ordinal 570) and Looper (rolling slopes, **no fully closed loop claim**). The old flat, co-located 2P video is **fully removed** from the shot list.

The main film is now **80 seconds**, the social cut **27 seconds**, and the poster is derived from the real inverted airborne rider on Jumps rather than the original flat course. Video/visual acceptance must still confirm the new film exports. The 3840×2160 statistics remain expressly an editorial evidence graphic, not 4K gameplay footage.
