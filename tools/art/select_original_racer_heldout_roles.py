#!/usr/bin/env python3
"""Predeclared first-family-fit / disjoint-family-heldout role selection.

Only source-shape connectivity is inspected. NEVER use model scores, artwork
acceptance, fitted camera, colour or manual silhouette appearance to decide
which source windows become withheld. The original 1205..1220 component is
always FIT; all other distinct binary-mask components become withheld_cand.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from tools.art.freeze_racer_source_family_splits import (
        CANONICAL_ROM_SHA, OUTPUT_SCHEMA, REQUEST_SCHEMA,
    )
    from tools.art.no_replace_report import publish_text_once
except ModuleNotFoundError:
    from freeze_racer_source_family_splits import (
        CANONICAL_ROM_SHA, OUTPUT_SCHEMA, REQUEST_SCHEMA,
    )
    from no_replace_report import publish_text_once

FIRST = "first-1205-1220"


def select_roles(diagnostics: dict) -> dict:
    if (not isinstance(diagnostics, dict) or
            diagnostics.get("schema") != OUTPUT_SCHEMA or
            diagnostics.get("source_rom_sha256") != CANONICAL_ROM_SHA or
            diagnostics.get("no_original_binary_silhouette_across_roles") is not True or
            diagnostics.get("source_family_split_is_frozen_by_exact_input_hashes") is not True or
            diagnostics.get("owner_likeness_approved") is not False or
            diagnostics.get("shipping_art_approved") is not False or
            diagnostics.get("withheld_candidate_is_an_independent_3d_camera") is not False):
        raise ValueError("unverified original-source diagnostic partition")
    connected = diagnostics.get("connected_window_components")
    if not isinstance(connected, list) or not connected:
        raise ValueError("no authenticated source components")
    roles = {}
    first_components = 0
    heldout_components = 0
    for component in connected:
        if not isinstance(component, dict) or component.get("role") != "diagnostic":
            raise ValueError("all source windows must initially be diagnostic")
        windows = component.get("windows")
        masks = component.get("source_binary_mask_shas")
        if (not isinstance(windows, list) or not windows or
                not isinstance(masks, list) or not masks or
                len(windows) != len(set(windows)) or
                len(masks) != len(set(masks)) or
                component.get("unique_source_binary_silhouette_count") != len(masks)):
            raise ValueError("malformed independent original-source component")
        is_first = FIRST in windows
        first_components += int(is_first)
        heldout_components += int(not is_first)
        for window in windows:
            if not isinstance(window, str) or not window or window in roles:
                raise ValueError("duplicate or invalid original source window")
            roles[window] = "fit" if is_first else "withheld_candidate"
    if (first_components != 1 or heldout_components < 1 or
            diagnostics.get("total_source_windows") != len(roles) or
            diagnostics.get("role_summary", {}).get("diagnostic", {}).get("window_count") != len(roles) or
            diagnostics.get("role_summary", {}).get("fit", {}).get("window_count") != 0 or
            diagnostics.get("role_summary", {}).get("withheld_candidate", {}).get("window_count") != 0):
        raise ValueError("no independently grouped other original source-family holdout")
    return {"schema": REQUEST_SCHEMA,
            "roles": {key: roles[key] for key in sorted(roles)}}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("diagnostic_report", type=Path)
    p.add_argument("--out", type=Path)
    args = p.parse_args()
    report = json.loads(args.diagnostic_report.read_text(encoding="utf-8"))
    payload = json.dumps(select_roles(report), indent=2, sort_keys=True) + "\n"
    if args.out:
        publish_text_once(args.out, payload)
    else:
        print(payload, end="")


if __name__ == "__main__":
    main()
