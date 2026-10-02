-- Capture the first game-authored Crawler medal mutation from the verified historical movie.
-- This script only observes memory and writes evidence. It never writes game state.
local out = os.getenv("UR_MEDAL_SRAM_OUT") or "first-medal.srm"
local before_out = os.getenv("UR_MEDAL_BEFORE_OUT") or "before-runtime.srm"
local meta = os.getenv("UR_MEDAL_META_OUT") or "first-medal.txt"

-- Host throttling/rendering is irrelevant to the deterministic movie state.
snes9x.speedmode("maximum")

local function dump_sram(path)
    local f = assert(io.open(path, "wb"))
    for i = 0, 8191 do
        f:write(string.char(memory.readbyte(0x700000 + i)))
    end
    f:close()
end

local function u16(addr)
    return memory.readbyte(addr) + 256 * memory.readbyte(addr + 1)
end

local function checksum_valid()
    local sum = 0
    for addr = 0x7005E8, 0x70073B, 2 do
        sum = (sum + u16(addr)) % 65536
    end
    return sum == u16(0x70073C)
end

local function snapshot()
    local flags = {}
    for i = 0, 4 do
        flags[#flags + 1] = memory.readbyte(0x701075 + i)
    end
    return {
        frame = snes9x.framecount(),
        menu = memory.readbyte(0x7E009F),
        track = memory.readbyte(0x7E00CE),
        in_race = memory.readbyte(0x7E0313),
        rider = memory.readbyte(0x7E017D),
        tour = memory.readbyte(0x7E00D0),
        medal = memory.readbyte(0x70069C),
        tier = memory.readbyte(0x7010D3),
        flags = flags,
    }
end

local function flags_text(flags)
    return table.concat(flags, ",")
end

local armed = false
local start_medal = nil
local baseline = nil
local previous = snapshot()

while true do
    emu.frameadvance()
    local current = snapshot()

    if not armed then
        -- The historical movie contains emulator SRAM bytes that are not yet the
        -- game's initialized save image at Lua startup. Arm only once the game
        -- has authored a checksum-valid SRAM state with a legal medal value.
        if current.medal <= 3 and checksum_valid() then
            armed = true
            start_medal = current.medal
            baseline = current
            previous = current
            dump_sram(before_out)
        end
    elseif current.medal ~= start_medal then
        dump_sram(out)
        local f = assert(io.open(meta, "w"))
        f:write(string.format(
            "baseline_frame=%d\nbaseline_medal=%d\n" ..
            "frame=%d\nmedal_before=%d\nmedal_after=%d\n" ..
            "previous_frame=%d\nprevious_menu=%d\nprevious_track=%d\nprevious_in_race=%d\n" ..
            "previous_rider=%d\nprevious_tour=%d\nprevious_tier=%d\nprevious_flags=%s\n" ..
            "current_menu=%d\ncurrent_track=%d\ncurrent_in_race=%d\n" ..
            "current_rider=%d\ncurrent_tour=%d\ncurrent_tier=%d\ncurrent_flags=%s\n",
            baseline.frame, baseline.medal,
            current.frame, start_medal, current.medal,
            previous.frame, previous.menu, previous.track, previous.in_race,
            previous.rider, previous.tour, previous.tier, flags_text(previous.flags),
            current.menu, current.track, current.in_race,
            current.rider, current.tour, current.tier, flags_text(current.flags)
        ))
        f:close()
        os.exit(0)
    end
    previous = current
end
