-- Capture the first game-authored medal-matrix mutation from the verified historical movie.
-- This script only observes memory and writes evidence. It never writes game state.
local out = os.getenv("UR_MEDAL_SRAM_OUT") or "first-medal.srm"
local before_out = os.getenv("UR_MEDAL_BEFORE_OUT") or "before-runtime.srm"
local meta = os.getenv("UR_MEDAL_META_OUT") or "first-medal.txt"
local heartbeat = os.getenv("UR_MEDAL_HEARTBEAT_OUT") or "medal-heartbeat.txt"

-- Host throttling/rendering is irrelevant to the deterministic movie state.
snes9x.speedmode("maximum")

local MEDAL_BASE = 0x70069C
local MEDAL_ROWS = 9
local MEDAL_COLS = 16
local MEDAL_COUNT = MEDAL_ROWS * MEDAL_COLS
local MAX_FRAME = 1200000
local STATUS_INTERVAL = 10000

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

local function state_snapshot()
    local rider = memory.readbyte(0x7E017D)
    return {
        frame = snes9x.framecount(),
        menu = memory.readbyte(0x7E009F),
        track = memory.readbyte(0x7E00CE),
        in_race = memory.readbyte(0x7E0313),
        rider = rider,
        tour = memory.readbyte(0x7E00D0),
        tier = memory.readbyte(0x7010D3 + (rider % 16)),
    }
end

local armed = false
local baseline = nil
local baseline_medals = nil
local previous = state_snapshot()
local next_status = STATUS_INTERVAL
local probe_index = 0
local race_entries = 0
local race_results_entries = 0
local track_changes = 0

local function write_heartbeat(current)
    local f = assert(io.open(heartbeat, "w"))
    f:write(string.format(
        "frame=%d\nmenu=%d\ntrack=%d\nin_race=%d\nrider=%d\ntour=%d\n" ..
        "race_entries=%d\nrace_results_entries=%d\ntrack_changes=%d\nchecksum_valid=%s\n",
        current.frame, current.menu, current.track, current.in_race,
        current.rider, current.tour, race_entries, race_results_entries,
        track_changes, tostring(checksum_valid())
    ))
    f:close()
end

while true do
    emu.frameadvance()
    local current = state_snapshot()

    if not armed then
        -- The reset movie's embedded SRAM bytes are not necessarily the game's
        -- initialized save image at Lua startup. Arm only at the verified
        -- stock main-menu state, once the game has authored a checksum-valid
        -- save whose medal matrix is legal. This excludes a zero-filled
        -- pre-initialization image whose zero checksum would otherwise pass.
        local medals = read_medals()
        if current.menu == 0xD7 and legal_medals(medals) and checksum_valid() then
            armed = true
            baseline = current
            baseline_medals = medals
            previous = current
            dump_sram(before_out)
        end
    else
        if previous.in_race ~= 1 and current.in_race == 1 then
            race_entries = race_entries + 1
        end
        if previous.menu ~= 0x99 and current.menu == 0x99 then
            race_results_entries = race_results_entries + 1
        end
        if current.track ~= previous.track then
            track_changes = track_changes + 1
        end

        if current.frame >= next_status then
            write_heartbeat(current)
            print(string.format(
                "progression-watch frame=%d menu=%d track=%d in_race=%d rider=%d tour=%d checksum_valid=%s",
                current.frame, current.menu, current.track, current.in_race,
                current.rider, current.tour, tostring(checksum_valid())
            ))
            next_status = next_status + STATUS_INTERVAL
        end
        if current.frame >= MAX_FRAME then
            local f = assert(io.open(meta, "w"))
            f:write(string.format(
                "status=no-medal-mutation\nbaseline_frame=%d\nlimit_frame=%d\n" ..
                "menu=%d\ntrack=%d\nin_race=%d\nrider=%d\ntour=%d\n" ..
                "race_entries=%d\nrace_results_entries=%d\ntrack_changes=%d\n",
                baseline.frame, current.frame, current.menu, current.track,
                current.in_race, current.rider, current.tour,
                race_entries, race_results_entries, track_changes
            ))
            f:close()
            -- On this historical frontend os.exit terminates the Lua thread,
            -- not the emulator process. The workflow watches the status file
            -- and terminates the bounded replay process immediately.
            os.exit(2)
        end

        -- Medal writes persist. Probe one cell per frame, cycling across all 144
        -- cells, instead of crossing the Lua memory bridge 144 times every frame.
        -- Any authentic mutation is therefore detected within at most 144 frames.
        local current_value = memory.readbyte(MEDAL_BASE + probe_index)
        if current_value ~= baseline_medals[probe_index + 1] then
            local current_medals = read_medals()
            local index, before_value, after_value =
                first_medal_change(baseline_medals, current_medals)
            if index ~= nil then
                dump_sram(out)
                local row = math.floor(index / MEDAL_COLS)
                local rider_col = index % MEDAL_COLS
                local f = assert(io.open(meta, "w"))
                f:write(string.format(
                    "status=medal-captured\nbaseline_frame=%d\nframe=%d\ndetection_lag_max_frames=%d\n" ..
                    "medal_index=%d\ntour_row=%d\nrider_column=%d\n" ..
                    "medal_before=%d\nmedal_after=%d\n" ..
                    "previous_frame=%d\nprevious_menu=%d\nprevious_track=%d\nprevious_in_race=%d\n" ..
                    "previous_rider=%d\nprevious_tour=%d\nprevious_tier=%d\n" ..
                    "current_menu=%d\ncurrent_track=%d\ncurrent_in_race=%d\n" ..
                    "current_rider=%d\ncurrent_tour=%d\ncurrent_tier=%d\n",
                    baseline.frame, current.frame, MEDAL_COUNT - 1,
                    index, row, rider_col, before_value, after_value,
                    previous.frame, previous.menu, previous.track, previous.in_race,
                    previous.rider, previous.tour, previous.tier,
                    current.menu, current.track, current.in_race,
                    current.rider, current.tour, current.tier
                ))
                f:close()
                os.exit(0)
            end
        end
        probe_index = (probe_index + 1) % MEDAL_COUNT
    end
    previous = current
end
