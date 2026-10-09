#!/usr/bin/env python3
"""Add exactly one product input hook to the already proven Baldosa host.

Run after baldosa_guest_adapter_spike.py. Optional native HD presentation is
orthogonal. All changes stay in a disposable pinned Baldosa checkout.
"""
from __future__ import annotations

import argparse
from pathlib import Path

MARK = "UR_BALDOSA_PRODUCT_INPUT_SEAM"
FIELD = "    .num_players         = 2,\n"
OBSERVER = "UR_BALDOSA_GUEST_SNAPSHOT_BRIDGE"
PROTO = ("extern uint32_t ur_baldosa_product_filter_frame_inputs("
         "uint32_t word, unsigned frame);\n")
ANCHOR = "static const SnesDesktopHostGame kGameHost = {\n"


def patch_main(source: str) -> str:
    if MARK in source:
        return source
    if OBSERVER not in source:
        raise ValueError("First stage the verified Baldosa guest snapshot bridge")
    if source.count(ANCHOR) != 1 or source.count(FIELD) != 1:
        raise ValueError("Unrecognized Baldosa native host layout")
    # Baldosa's separate web build already has WebNetplayFilterInputs.
    # Do not replace its lockstep authority.
    replacement = (FIELD +
        "#ifndef __EMSCRIPTEN__\n"
        "    /* " + MARK + " */\n"
        "    .filter_frame_inputs = &ur_baldosa_product_filter_frame_inputs,\n"
        "#endif\n")
    return (source.replace(ANCHOR, PROTO + "\n" + ANCHOR, 1)
                  .replace(FIELD, replacement, 1))


def patch_cmake(source: str, root: Path) -> str:
    if MARK in source:
        return source
    if OBSERVER not in source:
        raise ValueError("First stage verified read-only observer sources")
    cpp = (root / "tools/baldosa_native_product_execution.cpp").resolve()
    inc = (root / "native/product").resolve()
    if not cpp.is_file() or not (inc / "baldosa_execution_backend.hpp").is_file():
        raise ValueError("Missing project-owned product C ABI bridge")
    return source.rstrip() + (
        "\n\n# " + MARK + ": native input hook, no second runtime\n"
        + f'set_source_files_properties("{cpp.as_posix()}" PROPERTIES '
          f'INCLUDE_DIRECTORIES "{inc.as_posix()}")\n'
        + f'target_sources(UniracersSNESRecomp PRIVATE "{cpp.as_posix()}")\n'
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", type=Path, required=True)
    ap.add_argument("--ur-root", type=Path, required=True)
    args = ap.parse_args()
    root, game = args.ur_root.resolve(), args.game.resolve()
    for path, apply in [
        (game / "src/main.c", patch_main),
        (game / "CMakeLists.txt", lambda text: patch_cmake(text, root))
    ]:
        before = path.read_text(encoding="utf-8")
        after = apply(before)
        if after != before:
            path.write_text(after, encoding="utf-8")
        print(f"{path}: {'already staged' if before == after else 'staged'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
