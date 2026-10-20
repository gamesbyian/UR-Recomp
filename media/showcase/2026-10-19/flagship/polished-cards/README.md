# Flagship editorial card redesign

Three static cards in the October 19 flagship have been redesigned, with the original 1994 Uniracers palette and race-track contours used as visual references, and a **SHA-locked genuine original-race still** deliberately defocused as atmospheric background. The game image is never represented as new footage or a new course.

**Windows product journey:**

> A race you can come back to.

The native frontend can create racers, run a two-player event, and reopen earned records after a fresh launch.

Three concise labelled beats identify racer selection, completing the race, and reopening Records. The card describes verified scripted journeys and explicitly notes that a newly recorded complete Windows session remains pending.

**Original-mode UHD evidence:**

> 3840 × 2160
>
> Actual framebuffer. Pixel-checked.

The explanatory copy identifies the real SDL pixel readback, the genuine 342×224 world, 7:6 pixel aspect, and checked output pixel count. It explicitly says the evidence is a checked frame, *not* 4K recorded gameplay.

**Contribution request:**

> There's a running game.
>
> There's work to finish.

The card names the project’s specific missing disciplines: reverse engineering, C++/native platforms, character art/animation and independent testing. The GitHub URL gets a calm, high-contrast full-width treatment.

The design rejects motivational slogans, hypey word salads, invented game interfaces and exaggerated fidelity claims. It uses a restrained high-contrast geometric hierarchy, reference SNES rainbow accents, a source-blurred racing still and a deliberate recurring footer. The same 1920×1080 outputs are imported by `tools/showcase/build_flagship_recruitment_20261019.py` at the original editorial points, so no gameplay or track image is modified. The only change in the next video build is the three source-backed cards.

Build the standalones:

```bash
python3 tools/showcase/polished_editorial_cards.py \
  --poster media/showcase/2026-10-10/recruitment/definitive-film/ur-recomp-recruitment-final-poster.png \
  --outdir media/showcase/2026-10-19/flagship/polished-cards
```

The render checks source SHA, exact output dimensions and commits a new provenance manifest. An inspected trailer render must separately prove the 85-second and 27-second output identities. The already merged versions are retained unchanged until the new film is visually reviewed.
