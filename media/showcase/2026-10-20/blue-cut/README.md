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
