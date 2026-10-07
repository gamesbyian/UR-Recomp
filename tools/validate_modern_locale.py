#!/usr/bin/env python3
"""Validate one UR-Recomp Modern UI locale pack."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

SCHEMA = "ur-recomp-modern-locale-v1"
LOCALE_RE = re.compile(r"^[a-z]{2,3}(?:-[A-Z]{2})?$")
KNOWN_KEYS = (
    "root.play",
    "root.practice",
    "root.multiplayer",
    "root.records",
    "root.options",
)
KNOWN_KEY_SET = set(KNOWN_KEYS)


class DuplicateKeyError(ValueError):
    pass


def _unique_object(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise DuplicateKeyError(f"duplicate JSON key: {key}")
        obj[key] = value
    return obj


def _bounded_text(value: object, name: str, maximum: int = 80) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{name}: must be a string")
    if not value:
        raise ValueError(f"{name}: must not be empty")
    if value != value.strip():
        raise ValueError(f"{name}: leading/trailing whitespace is not canonical")
    if len(value) > maximum:
        raise ValueError(f"{name}: exceeds {maximum} characters")
    if any(ord(ch) < 0x20 for ch in value):
        raise ValueError(f"{name}: contains control characters")
    return value


def validate_locale_pack(payload: object) -> dict:
    if not isinstance(payload, dict):
        raise ValueError("locale pack root must be an object")
    if set(payload) != {"schema", "locale", "entries"}:
        missing = sorted({"schema", "locale", "entries"} - set(payload))
        unknown = sorted(set(payload) - {"schema", "locale", "entries"})
        if missing:
            raise ValueError(f"locale pack missing fields: {', '.join(missing)}")
        raise ValueError(f"locale pack unknown fields: {', '.join(unknown)}")

    if payload["schema"] != SCHEMA:
        raise ValueError(f"locale pack schema must be {SCHEMA}")
    locale = _bounded_text(payload["locale"], "locale", maximum=12)
    if not LOCALE_RE.fullmatch(locale):
        raise ValueError("locale must be a canonical language or language-REGION tag")

    entries = payload["entries"]
    if not isinstance(entries, dict):
        raise ValueError("entries must be an object")
    keys = set(entries)
    missing = sorted(KNOWN_KEY_SET - keys)
    unknown = sorted(keys - KNOWN_KEY_SET)
    if missing:
        raise ValueError(f"entries missing required keys: {', '.join(missing)}")
    if unknown:
        raise ValueError(f"entries contain unknown keys: {', '.join(unknown)}")

    for key in KNOWN_KEYS:
        _bounded_text(entries[key], f"entries.{key}")

    return payload


def load_locale_pack(path: Path) -> dict:
    try:
        raw = path.read_text(encoding="utf-8")
        payload = json.loads(raw, object_pairs_hook=_unique_object)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, DuplicateKeyError) as exc:
        raise ValueError(f"cannot read locale pack: {exc}") from exc
    return validate_locale_pack(payload)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("locale_pack", type=Path)
    args = parser.parse_args()
    try:
        payload = load_locale_pack(args.locale_pack)
    except ValueError as exc:
        parser.error(str(exc))
    print(
        "MODERN_LOCALE_VALID "
        f"locale={payload['locale']} entries={len(payload['entries'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
