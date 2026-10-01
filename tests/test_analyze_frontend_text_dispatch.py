#!/usr/bin/env python3
from tools.analyze_frontend_text_dispatch import TABLE_OFFSET, VALID_COMMANDS, decode_table

data = bytearray(TABLE_OFFSET + (len(VALID_COMMANDS) + 1) * 2)
targets = [
    0xC440, 0xC481, 0xC445, 0xC4A7, 0xC3AF, 0xC534, 0xC546, 0xC5C2,
    0xC617, 0xC66C, 0xC5BA, 0xC60F, 0xC664, 0xC4EF, 0xC6AA, 0xC463, 0xC6C4,
]
for i, target in enumerate(targets):
    data[TABLE_OFFSET + 2*i] = target & 0xFF
    data[TABLE_OFFSET + 2*i + 1] = target >> 8

# Bytes immediately after the table are executable code, producing 0x20E2 for EE.
i = len(targets)
data[TABLE_OFFSET + 2*i] = 0xE2
data[TABLE_OFFSET + 2*i + 1] = 0x20

r = decode_table(bytes(data))
assert [e["command"] for e in r["entries"]] == [f"0x{x:02X}" for x in VALID_COMMANDS]
assert [e["target_word"] for e in r["entries"]] == [f"0x{x:04X}" for x in targets]
assert all(e["rom_code_target"] for e in r["entries"])
assert r["ee_fallthrough_word"] == "0x20E2"
assert r["ee_rom_code_target"] is False
print("PASS: frontend text command dispatch")
