# Genuine Windows title → Modern root final SDL evidence

Status: **bounded independent QA candidate** based directly on native title owner #2043, with no title/game host edits. This is not a release acceptance decision.

The title owner's exact Windows native/Original-source P7 frame evidence proves the pre-SDL host source composition and a semantic controller-first transition, but those two original P6/P7-source screens are **not** an independent actual SDL-renderer readback. The already merged QA runner can capture real `SDL_RenderReadPixels` from the same compiled native Windows AOT executable without fabricating another title or guest menu.

## Four actual native journeys in two output aspects

At **1280×720 (16:9)** and **1024×768 (4:3)**, build one Windows PE and independently launch four completely fresh original-Baldosa processes with the canonical USA retail ROM kept only on the runner:

| Route | Actual owner smoke | Reduced motion | Native behaviour |
| --- | --- | --- | --- |
| title-still | 15; suppress actions after guest frame 59 | Off | Render real title, never confirm |
| title-entered-root | 15; genuine semantic P1 A at guest frame 60 | Off | Leave real title, paint native root |
| title-reduced-still | 15; suppress actions after 59 | On | Hold real static reduced-motion title |
| title-reduced-entered-root | 15; genuine P1 A at frame 60 | On | Immediate reduced transition to native root |

Each process captures original final SDL **P7 draw ordinal 40**, not a guessed guest frame. The existing fixed capture driver independently requires correct process completion, original log, requested native SDL drawable size, exact source/PE, and one real SDL readback; it never calls a fake screenshot renderer. Original owner title/root log witnesses are required, and the static title routes fail if they accidentally proceed to root.

`tools/qa_modern_title_final_sdl_transition.py` additionally hashes actual P7/log bytes, requires all four to share the same exact original Windows PE and source head and drawable, rejects symlinks and bad P7 headers, and demands at least 300 changed **RGB** pixels in the centre safe area between title and root for normal and reduced motion independently. SDL readback alpha is not assumed to establish human-visible transparency. Unlike a timestamp/log-only transition claim, a pixel-identical or blank root fails. The 16:9 and 4:3 runs receive separate source-bound manifests. The original P7/PNG/log/receipt artifacts are preserved for independent art review; neither private ROM nor save roots are uploaded.

The proof qualifies at most genuine **final SDL title-versus-root presence and input-driven transition on one Windows PE**. It does **not** qualify source-logo exact RGB placement through SDL, actual natural 60Hz kinetics, early press edge ownership, 7:6 PAR calibration, original active racer likeness, human aesthetics, physical controllers or UHD, complete Authentic/guest CPU/APU parity, 342 logical output merely from 1280 display geometry, or any Windows/QA release gate. Those requirements remain with the independent owner and the combined integration draft #2053.

The change is a descendant PR against the title owner's branch, rather than a competing implementation of the native title/root. Once its genuine Windows artifacts are green, #2043/#2053 can consume the assertions and screenshots while preserving the exact compiled source lineage. No gameplay, title, modal, palette, art, input or runner implementation is changed.

Three-project reuse: the canonical UR source title and typed Modern root; Baldosa AOT/real input/SDL end-draw already installed; Malmazuke only source context. No second emulator or menu engine.
