#!/usr/bin/env python3
"""Width-aware generic SNES read footprint for RF081 evidence review.

A logged read starting at 00:01F1 with width=2 touches 01F2; that alone
does not identify an actual RTS stack operand or prove causality.
"""


def footprint(row):
    if row.get("stage") != "read":
        raise ValueError("not a native read")
    bank, addr, width = row.get("bank"), row.get("addr"), row.get("width")
    if (bank != "00" or type(addr) is not str or len(addr) != 4
            or any(char not in "0123456789ABCDEF" for char in addr)):
        raise ValueError("unqualified native bank/address")
    if width not in ("1", "2"):
        raise ValueError("unqualified native read width")
    start, n = int(addr, 16), int(width)
    if start + n > 0x10000:
        raise ValueError("read crosses bank boundary")
    return tuple(f"{x:04X}" for x in range(start, start+n))


def bounded_read_summary(rows):
    """Summarize already source-qualified rows; never infer RTS identity."""
    if len(rows) != 3:
        raise ValueError("exactly three source-local reads required")
    spans = [footprint(row) for row in rows]
    return {
        "starts_at_01F2": any(row["addr"] == "01F2" for row in rows),
        "touches_01F2": any("01F2" in span for span in spans),
        "touches_01F3": any("01F3" in span for span in spans),
        "observed_byte_footprints": [list(span) for span in spans],
        "dynamic_RTS_operand_identity_proven": False,
        "accepted_USA_events": 0,
    }
