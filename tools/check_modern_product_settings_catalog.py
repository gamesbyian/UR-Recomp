#!/usr/bin/env python3
"""Check machine-readable modern-setting metadata against the current C++ surface."""

from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
from typing import Any

def check_catalog(catalog: dict[str, Any], state_hpp: str, state_cpp: str, menu_h: str) -> list[str]:
    errors: list[str] = []
    match = re.search(r"schema_version\s*=\s*(\d+)", state_hpp)
    if not match:
        errors.append("could not locate HostProductState::schema_version")
    elif int(match.group(1)) != int(catalog["host_state_codec_version"]):
        errors.append("catalog host_state_codec_version does not match C++ schema_version")
    ids: set[str] = set()
    keys: set[str] = set()
    for setting in catalog.get("settings", []):
        sid = setting.get("id")
        key = setting.get("persisted_key")
        if not sid or sid in ids:
            errors.append(f"duplicate or empty setting id: {sid!r}")
        ids.add(sid)
        if not key or key in keys:
            errors.append(f"duplicate or empty persisted key: {key!r}")
        keys.add(key)
        if isinstance(key, str) and f'"{key}"' not in state_cpp:
            errors.append(f"persisted key not found in codec: {key}")
        symbol = setting.get("menu_symbol")
        if setting.get("menu_visible"):
            if not symbol:
                errors.append(f"menu-visible setting lacks menu_symbol: {sid}")
            elif symbol not in menu_h:
                errors.append(f"menu symbol missing from modern_options_menu.h: {symbol}")
        if setting.get("runtime_status") == "integrated" and not setting.get("menu_visible"):
            errors.append(f"integrated setting must have a visible Options row: {sid}")
        if setting.get("authentic_inert") is not True:
            errors.append(f"host setting must remain Authentic-inert: {sid}")
    return errors

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=Path, default=Path("analysis/modern-product-settings.json"))
    parser.add_argument("--state-hpp", type=Path, default=Path("native/product/host_product_state.hpp"))
    parser.add_argument("--state-cpp", type=Path, default=Path("native/product/host_product_state.cpp"))
    parser.add_argument("--menu-h", type=Path, default=Path("native/product/modern_options_menu.h"))
    args = parser.parse_args()
    catalog = json.loads(args.catalog.read_text())
    errors = check_catalog(catalog, args.state_hpp.read_text(), args.state_cpp.read_text(), args.menu_h.read_text())
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("MODERN_PRODUCT_SETTINGS_CATALOG_OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
