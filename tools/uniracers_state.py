#!/usr/bin/env python3
"""Canonical project-owned Uniracers WRAM state helpers.

Historical scripts are evidence, not APIs. Keep addresses used by project tooling
here once their semantics are sufficiently understood, and keep archaeological or
scratch addresses explicitly labelled instead of silently inheriting old names.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class Field:
    kind: str
    addr: int
    confidence: str
    note: str = ""


def s16(value: int) -> int:
    """Interpret an unsigned 16-bit value as signed two's-complement."""
    if not 0 <= value <= 0xFFFF:
        raise ValueError(f"value outside u16 range: {value}")
    return value - 0x10000 if value >= 0x8000 else value


def read_field(data: bytes, field: Field) -> int:
    width = 1 if field.kind == "u8" else 2
    if field.addr < 0 or field.addr + width > len(data):
        raise ValueError(
            f"field at 0x{field.addr:04X} ({field.kind}) outside {len(data)}-byte buffer"
        )
    if field.kind == "u8":
        return data[field.addr]
    raw = int.from_bytes(data[field.addr : field.addr + 2], "little", signed=False)
    if field.kind == "u16":
        return raw
    if field.kind == "s16":
        return s16(raw)
    raise ValueError(f"unsupported field kind: {field.kind}")


# Confirmed or operationally established project fields. Confidence is carried
# beside the address so an imported label cannot become "truth" merely because
# several tools copied the same constant.
PLAYER1_FIELDS: dict[str, Field] = {
    "in_race": Field("u8", 0x0313, "confirmed", "active-race state"),
    "track": Field("u8", 0x00CE, "confirmed", "current track id"),
    "x_pos": Field("u16", 0x0411, "confirmed", "player-1 X position"),
    "y_pos": Field("u16", 0x0415, "confirmed", "player-1 Y position"),
    "x_speed": Field("s16", 0x04B7, "confirmed", "player-1 signed X speed"),
    "y_speed": Field("s16", 0x04BB, "confirmed", "player-1 signed Y speed"),
    "pitch": Field(
        "u8",
        0x04C7,
        "confirmed",
        "persistent player-1 modulo-64 pitch/orientation angle",
    ),
    "air": Field("u8", 0x0545, "confirmed", "player-1 airborne state"),
    "faced_direction": Field(
        "u8", 0x0BA1, "historical", "recovered bot label; semantics not fully promoted"
    ),
    "countdown_timer": Field(
        "u16", 0x11BA, "confirmed", "race countdown/timer with observed 0x0100 cadence"
    ),
    "reverse_controls": Field(
        "u8", 0x132B, "historical", "recovered bot label; verify before fidelity use"
    ),
    "screen_x": Field(
        "u8", 0x1509, "historical", "recovered/display-oriented candidate"
    ),
}

PLAYER2_FIELDS: dict[str, Field] = {
    "x_pos": Field("u16", 0x0413, "paired", "player-2 X position slot"),
    "y_pos": Field("u16", 0x0417, "paired", "player-2 Y position slot"),
    "x_speed": Field("s16", 0x04B9, "paired", "player-2 signed X speed slot"),
    "y_speed": Field("s16", 0x04BD, "paired", "player-2 signed Y speed slot"),
    "pitch": Field("u8", 0x04C9, "paired", "player-2 pitch/orientation slot"),
    "air": Field("u8", 0x0547, "paired", "player-2 airborne state slot"),
    "faced_direction": Field("u8", 0x0BA3, "paired", "player-2 facing slot"),
}

# Values the 2014 Lua bot actually used because later duplicate table keys won.
# Keep these separate from the normalized project model. In particular 0x0F49
# is scratch/current-player pitch, not persistent player-1 pitch storage.
HISTORICAL_BOT_EFFECTIVE: dict[str, Field] = {
    "air": Field("u8", 0x0545, "historical-effective"),
    "pitch_scratch": Field("u8", 0x0F49, "historical-effective"),
    "showing_arrows": Field("u8", 0x0FCC, "historical-effective"),
    "arrow_direction": Field("u8", 0x0FCB, "historical-effective"),
    "tabletops": Field("u8", 0x042F, "historical-effective"),
}

HISTORICAL_BOT_OVERWRITTEN: dict[str, Field] = {
    "air": Field("u8", 0x0547, "overwritten", "later duplicate key replaced this"),
    "pitch": Field("u8", 0x04C9, "overwritten", "later duplicate key replaced this"),
    "showing_arrows": Field("u8", 0x0FCE, "overwritten"),
    "arrow_direction": Field("u8", 0x0FCD, "overwritten"),
    "tabletops": Field("u8", 0x0431, "overwritten"),
}


def read_state(data: bytes, fields: Mapping[str, Field] = PLAYER1_FIELDS) -> dict[str, int]:
    return {name: read_field(data, field) for name, field in fields.items()}
