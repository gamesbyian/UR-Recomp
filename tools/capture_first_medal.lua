-- Capture the first game-authored medal-matrix mutation from the verified historical movie.
-- This script only observes memory and writes evidence. It never writes game state.
local out = os.getenv("UR_MEDAL_SRAM_OUT") or "first-medal.srm"
local before_out = os.getenv("UR_MEDAL_BEFORE_OUT") or "before-runtime.srm"
local meta = os.getenv("UR_MEDAL_META_OUT") or "first-medal.txt"

-- Host throttling/rendering is irrelevant to the deterministic movie state.
snes9x.speedmode("maximum")

local MEDAL_BASE = 0x70069C
local MEDAL_ROWS = 9
local MEDAL_COLS = 16
local MEDAL_COUNT = MEDAL_ROWS * MEDAL_COLS

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

local function read_medals()
    local values = {}
    for i = 0, MEDAL_COUNT - 1 do
        values[i + 1] = memory.readbyte(MEDAL_BASE + i)
    end
    return values
end

local function legal_medals(values)
    for i = 1, #values do
        if values[i] > 3 then
            return false
        end
    end
    return true
end

local function first_medal_change(before, after)
    for i = 1, MEDAL_COUNT do
        if before[i] ~= after[i] then
            local index = i - 1
            return index, before[i], after[i]
        end
    end
    return nil, nil, nil
end

local function snapshot()
    return {
        frame = snes9x.framecount(),
        menu = memory.readbyte(0x7E009F),
        track = memory.readbyte(0x7E00CE),
        in_race = memory.readbyte(0x7E0313),
        rider = memory.readbyte(0x7E017D),
        tour = memory.readbyte(0x7E00D0),
        tier = memory.readbyte(0x7010D3 + (memory.readbyte(0x7E017D) % 16)),
        medals = read_medals(),
    }
end

local armed = false
local baseline = nil
local previous = snapshot()

while true do
    emu.frameadvance()
    local current = snapshot()

    if not armed then
        -- The reset movie's embedded SRAM bytes are not necessarily the game's
        -- initialized save image at Lua startup. Arm only once the game has
        -- authored a checksum-valid save whose medal matrix is legal.
        if legal_medals(current.medals) and checksum_valid() then
            armed = true
            baseline = current
            previous = current
            dump_sram(before_out)
        end
    else
        local index, before_value, after_value =
            first_medal_change(baseline.medals, current.medals)
        if index ~= nil then
            dump_sram(out)
            local row = math.floor(index / MEDAL_COLS)
            local rider_col = index % MEDAL_COLS
            local previous_value = previous.medals[index + 1]
            local f = assert(io.open(meta, "w"))
            f:write(string.format(
                "baseline_frame=%d\nframe=%d\nmedal_index=%d\ntour_row=%d\nrider_column=%d\n" ..
                "medal_before=%d\nmedal_previous=%d\nmedal_after=%d\n" ..
                "previous_frame=%d\nprevious_menu=%d\nprevious_track=%d\nprevious_in_race=%d\n" ..
                "previous_rider=%d\nprevious_tour=%d\nprevious_tier=%d\n" ..
                "current_menu=%d\ncurrent_track=%d\ncurrent_in_race=%d\n" ..
                "current_rider=%d\ncurrent_tour=%d\ncurrent_tier=%d\n",
                baseline.frame, current.frame, index, row, rider_col,
                before_value, previous_value, after_value,
                previous.frame, previous.menu, previous.track, previous.in_race,
                previous.rider, previous.tour, previous.tier,
                current.menu, current.track, current.in_race,
                current.rider, current.tour, current.tier
            ))
            f:close()
            os.exit(0)
        end
    end
    previous = current
end
