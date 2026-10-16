#!/usr/bin/env python3
"""QA-08: source-pinned cursor brightness/color-math order discriminator.

A mathematical explanation of ONE independently observed 2P menu-arrow pixel,
not a claim of original effective pixel-layer ownership, SNES hardware accuracy,
a raster fix, another native/emulator execution, or a graphics release gate.

Reference Snes9x: snes9xgit/snes9x@1bcc369e89f08243e0a462882fb1f3e42e51de3a,
ppu.cpp S9xFixColourBrightness() -> IPPU.ScreenColors before gfx.h
COLOR_ADD::fn1_2(). Native: baldosa/snesrecomp@075fbe4c8e0d97b0013be541795c39cb644a9709,
runner/src/snes/ppu_legacy.c ppu_render_pixel() halves raw channels before
applying master brightness. Both recipes use the pinned 2014 16x32 brightness
table formula (channel5 * brightness + 7) // 15.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL_CORE = "1bcc369e89f08243e0a462882fb1f3e42e51de3a"
NATIVE_PPU_CORE = "075fbe4c8e0d97b0013be541795c39cb644a9709"
ORIGINAL_SUB_CGRAM_INDEX = 0xDD
ORIGINAL_SUB_CGRAM_WORD = 0x1889
BRIGHTNESS = 14
RAW_MAIN_RGB5 = (15, 15, 15)
RAW_SUB_RGB5 = (9, 4, 6)
OBSERVED_ORIGINAL_RGB8 = (90, 74, 82)
OBSERVED_NATIVE_RGB8 = (90, 66, 74)


def brighten(channel5: int, brightness: int) -> int:
    if not 0 <= channel5 <= 31 or not 0 <= brightness <= 15:
        raise ValueError("outside SNES 5-bit colour / 4-bit brightness")
    return (channel5 * brightness + 7) // 15


def expand(channel5: int) -> int:
    if not 0 <= channel5 <= 31:
        raise ValueError("outside RGB5")
    return (channel5 << 3) | (channel5 >> 2)


def blend_before_brightness(main: tuple[int, ...],
                            sub: tuple[int, ...],
                            brightness: int) -> tuple[int, int, int]:
    """The pinned native legacy PPU's relevant add-half order."""
    if len(main) != 3 or len(sub) != 3:
        raise ValueError("expected exactly 3 RGB channels")
    return tuple(expand(brighten((a + b) // 2, brightness))
                 for a, b in zip(main, sub))


def brighten_before_blend(main: tuple[int, ...],
                          sub: tuple[int, ...],
                          brightness: int) -> tuple[int, int, int]:
    """The pinned 2014 Snes9x palette-first add-half colour order."""
    if len(main) != 3 or len(sub) != 3:
        raise ValueError("expected exactly 3 RGB channels")
    return tuple(expand((brighten(a, brightness) +
                         brighten(b, brightness)) // 2)
                 for a, b in zip(main, sub))


def analyze(early_cursor: dict, toolchain: dict) -> dict:
    tools = [t for t in toolchain["tools"] if t.get("id") == "snes9x-libretro"]
    if len(tools) != 1 or tools[0].get("revision") != ORIGINAL_CORE:
        raise ValueError("original Snes9x source pin changed")
    if (early_cursor.get("schema") !=
            "qa08-two-independent-original-native-early-menu-cursor-source-rgb5/1"
        or early_cursor.get("usa_rom_sha256") !=
            "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
        or early_cursor.get("original_color_conversion") !=
            "BGRX 2014 Snes9x green6_to5_only, native actual 256x224 P7 RGBA"
        or early_cursor.get("source_pairs_verified_per_mode") != 25
        or early_cursor.get("oneplayer", {}).get("first_divergent_native_guest") != 1280
        or early_cursor.get("twoplayer", {}).get("first_divergent_native_guest") != 1280):
        raise ValueError("unrecognized original/native real cursor source")
    observed = early_cursor.get("most_frequent_exact_original_to_native_color_substitution", {})
    if (observed.get("original_RGB5_expanded") != list(OBSERVED_ORIGINAL_RGB8)
        or observed.get("compiled_Windows_RGBA_rgb") != list(OBSERVED_NATIVE_RGB8)
        or observed.get("occurrences_1p") != 480
        or observed.get("occurrences_2p") != 3035):
        raise ValueError("authentic cursor image-colour witness changed")
    if (ORIGINAL_SUB_CGRAM_WORD & 31, (ORIGINAL_SUB_CGRAM_WORD >> 5) & 31,
        (ORIGINAL_SUB_CGRAM_WORD >> 10) & 31) != RAW_SUB_RGB5:
        raise ValueError("original source OBJ palette word inconsistent")
    source = brighten_before_blend(RAW_MAIN_RGB5, RAW_SUB_RGB5, BRIGHTNESS)
    native = blend_before_brightness(RAW_MAIN_RGB5, RAW_SUB_RGB5, BRIGHTNESS)
    if source != OBSERVED_ORIGINAL_RGB8 or native != OBSERVED_NATIVE_RGB8:
        raise ValueError("source-pinned register/colour order cannot explain exact pixels")
    return {
        "schema": "qa08-source-pinned-cursor-brightness-order-counterfactual/1",
        "scope": "one source-observed native 2P menu-arrow pixel x55,y65 at guest1280",
        "2014_original_Snes9x_pinned_revision": ORIGINAL_CORE,
        "native_Baldosa_PPU_pinned_revision": NATIVE_PPU_CORE,
        "original_USA_ROM_SHA256": early_cursor["usa_rom_sha256"],
        "native_cursor_guest": 1280,
        "original_video_callback": 1279,
        "source_original_subscreen_CGRAM_index": f"{ORIGINAL_SUB_CGRAM_INDEX:02x}",
        "source_original_subscreen_CGRAM_word": f"{ORIGINAL_SUB_CGRAM_WORD:04x}",
        "native_main_BG1_RGB5": list(RAW_MAIN_RGB5),
        "native_sub_OBJ_RGB5": list(RAW_SUB_RGB5),
        "native_effective_brightness": BRIGHTNESS,
        "native_math": "add-half with active subscreen OBJ",
        "pinned_Snes9x_palette_first_RGB8_counterfactual": list(source),
        "pinned_native_half_first_RGB8_counterfactual": list(native),
        "original_actual_RGB8": list(OBSERVED_ORIGINAL_RGB8),
        "actual_Windows_RGB8": list(OBSERVED_NATIVE_RGB8),
        "both_order_predictions_equal_actual_samples": True,
        "matched_1P_other_positions_with_same_colour_not_source_layer_proof": observed["occurrences_1p"],
        "matched_2P_other_positions_with_same_colour_not_source_layer_proof": observed["occurrences_2p"],
        "correctly_registered_original_original_effective_BG1_and_OBJ_pixel_layers_proven": False,
        "physical_SNES_color_math_order_proven": False,
        "all_cursor_pixels_explained": False,
        "all_transition_or_result_pixels_explained": False,
        "renderer_code_change_authorized": False,
        "QA08_QA10_HD_art_or_release_acceptance": False,
        "next_decision": "independently observe original Snes9x effective main BG1 and subscreen OBJ pixel layers at callback1279 x55,y65, then qualify hardware color-math brightness ordering before code changes",
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()
    witness = json.loads((ROOT / "analysis/data/qa08-early-cursor-crossmode-source-20261016.json").read_text())
    toolchain = json.loads((ROOT / "tools/toolchain.json").read_text())
    outcome = analyze(witness, toolchain)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(outcome, indent=2, sort_keys=True) + "\n")
    print("QA08_CURSOR_BRIGHTNESS_ORDER counterfactual_matches=2/2 original_layer_proven=0 native_fix_approved=0")


if __name__ == "__main__":
    main()
