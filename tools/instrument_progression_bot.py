#!/usr/bin/env python3
from __future__ import annotations
import argparse
from pathlib import Path

MONITOR = r'''
local UR_BASE = 0x70069C
local UR_COUNT = 144
local UR_BEFORE = os.getenv("UR_MEDAL_BEFORE_OUT") or "before-runtime.srm"
local UR_AFTER = os.getenv("UR_MEDAL_SRAM_OUT") or "first-medal.srm"
local UR_META = os.getenv("UR_MEDAL_META_OUT") or "first-medal.txt"
local UR_HEARTBEAT = os.getenv("UR_MEDAL_HEARTBEAT_OUT") or "medal-heartbeat.txt"
local ur_armed = false
local ur_baseline = nil
local ur_probe = 0
local ur_next_heartbeat = 10000

local function ur_u16(a)
    return memory.readbyte(a) + 256 * memory.readbyte(a + 1)
end

local function ur_checksum_valid()
    local sum = 0
    for a = 0x7005E8, 0x70073B, 2 do
        sum = (sum + ur_u16(a)) % 65536
    end
    return sum == ur_u16(0x70073C)
end

local function ur_dump(path)
    local f = assert(io.open(path, "wb"))
    for i = 0, 8191 do f:write(string.char(memory.readbyte(0x700000 + i))) end
    f:close()
end

local function ur_medals()
    local t = {}
    for i = 0, UR_COUNT - 1 do t[i + 1] = memory.readbyte(UR_BASE + i) end
    return t
end

local function ur_legal(t)
    for i = 1, #t do if t[i] > 3 then return false end end
    return true
end

local function ur_heartbeat(frame)
    local f = assert(io.open(UR_HEARTBEAT, "w"))
    f:write(string.format(
        "frame=%d\\nmenu=%d\\nselected_option=%d\\nselected_row=%d\\nselected_col=%d\\ntrack=%d\\nin_race=%d\\nrider=%d\\ntour=%d\\ncrawler_score=%d\\njumper_score=%d\\nshuffler_score=%d\\nbounder_score=%d\\nwalker_score=%d\\nrunner_score=%d\\nhopper_score=%d\\nsprinter_score=%d\\nhunter_score=%d\\nchecksum_valid=%s\\n",
        frame, memory.readbyte(0x7E009F), memory.readbyte(0x7E009B),
        memory.readbyte(0x7E000E), memory.readbyte(0x7E0C63),
        memory.readbyte(0x7E00CE), memory.readbyte(0x7E0313),
        memory.readbyte(0x7E017D), memory.readbyte(0x7E00D0),
        memory.readbyte(0x7E0A03), memory.readbyte(0x7E0A07),
        memory.readbyte(0x7E0A0B), memory.readbyte(0x7E0A0F),
        memory.readbyte(0x7E0A13), memory.readbyte(0x7E0A17),
        memory.readbyte(0x7E0A1B), memory.readbyte(0x7E0A1F),
        memory.readbyte(0x7E0A23), tostring(ur_checksum_valid())
    ))
    f:close()
end

function URProgressionMonitor()
    local frame = snes9x.framecount()
    if not ur_armed then
        if memory.readbyte(0x7E009F) == 0xD7 then
            local t = ur_medals()
            if ur_legal(t) and ur_checksum_valid() then
                ur_armed = true
                ur_baseline = t
                ur_dump(UR_BEFORE)
                ur_heartbeat(frame)
            end
        end
        return
    end

    if frame >= ur_next_heartbeat then
        ur_heartbeat(frame)
        ur_next_heartbeat = ur_next_heartbeat + 10000
    end

    local v = memory.readbyte(UR_BASE + ur_probe)
    if v ~= ur_baseline[ur_probe + 1] then
        local now = ur_medals()
        for i = 1, UR_COUNT do
            if now[i] ~= ur_baseline[i] then
                local idx = i - 1
                ur_dump(UR_AFTER)
                local f = assert(io.open(UR_META, "w"))
                f:write(string.format(
                    "frame=%d\nmedal_index=%d\ntour_row=%d\nrider_column=%d\nmedal_before=%d\nmedal_after=%d\nmenu=%d\ntrack=%d\nin_race=%d\nrider=%d\ntour=%d\n",
                    frame, idx, math.floor(idx / 16), idx % 16,
                    ur_baseline[i], now[i], memory.readbyte(0x7E009F),
                    memory.readbyte(0x7E00CE), memory.readbyte(0x7E0313),
                    memory.readbyte(0x7E017D), memory.readbyte(0x7E00D0)
                ))
                f:close()
                os.exit(0)
            end
        end
    end
    ur_probe = (ur_probe + 1) % UR_COUNT
end
'''

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("source", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()
    text = args.source.read_text(encoding="utf-8")

    old = "targetMedal = 21 -- 17 for bronze, 19 for silver, 21 for gold"
    if text.count(old) != 1:
        raise SystemExit("historical targetMedal declaration changed")
    text = text.replace(old, "targetMedal = 17 -- progression acceptance: bronze", 1)

    anchor = "needNewPlayer = false\n\t\nfunction Run()"
    if text.count(anchor) != 1:
        raise SystemExit("historical Run anchor changed")
    text = text.replace(anchor, "needNewPlayer = false\n\n" + MONITOR + "\nfunction Run()", 1)

    call = "            emu.frameadvance()"
    if text.count(call) != 2:
        raise SystemExit(f"expected 2 Run frameadvance sites, found {text.count(call)}")
    text = text.replace(call, call + "\n            URProgressionMonitor()")

    tail = "--snes9x.speedmode(\"nothrottle\")\nRun()"
    if text.count(tail) != 1:
        raise SystemExit("historical Run invocation changed")
    text = text.replace(
        tail,
        'snes9x.speedmode("nothrottle")\nRun()',
        1,
    )

    args.output.write_text(text, encoding="utf-8")
    print(args.output)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
