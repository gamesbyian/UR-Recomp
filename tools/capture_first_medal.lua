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
local MAX_FRAME = 100000
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

local function tour_pass_flags(tour)
    local values = {}
    local base = 0x701075 + ((tour % 9) * 5)
    for i = 0, 4 do
        values[i + 1] = memory.readbyte(base + i)
    end
    return values
end

local function flags_csv(values)
    return string.format("%d,%d,%d,%d,%d", values[1], values[2], values[3], values[4], values[5])
end

local armed = false
local baseline = nil
local baseline_medals = nil
local previous = state_snapshot()
local next_status = STATUS_INTERVAL
local probe_index = 0
local race_entries = 0
local race_results_entries = 0
local circuit_results_entries = 0
local stunt_results_entries = 0
local track_changes = 0
local pending_award = nil
local MAX_SETTLE_FRAMES = 600

local function write_heartbeat(current)
    local f = assert(io.open(heartbeat, "w"))
    f:write(string.format(
        "frame=%d\nmenu=%d\ntrack=%d\nin_race=%d\nrider=%d\ntour=%d\n" ..
        "race_entries=%d\nrace_results_entries=%d\ncircuit_results_entries=%d\n" ..
        "stunt_results_entries=%d\ntrack_changes=%d\ntour_pass_flags=%s\nchecksum_valid=%s\n",
        current.frame, current.menu, current.track, current.in_race,
        current.rider, current.tour, race_entries, race_results_entries,
        circuit_results_entries, stunt_results_entries, track_changes,
        flags_csv(tour_pass_flags(current.tour)), tostring(checksum_valid())
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
        if previous.menu ~= 0xBC and current.menu == 0xBC then
            circuit_results_entries = circuit_results_entries + 1
        end
        if previous.menu ~= 0x18 and current.menu == 0x18 then
            stunt_results_entries = stunt_results_entries + 1
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
        if current.frame >= 10000 and race_entries > 0 and race_results_entries == 0 then
            local f = assert(io.open(meta, "w"))
            f:write(string.format(
                "status=replay-desync-no-first-results\nbaseline_frame=%d\nframe=%d\n" ..
                "menu=%d\ntrack=%d\nin_race=%d\nrider=%d\ntour=%d\n" ..
                "race_entries=%d\nrace_results_entries=%d\ncircuit_results_entries=%d\n" ..
                "stunt_results_entries=%d\ntrack_changes=%d\ntour_pass_flags=%s\n",
                baseline.frame, current.frame, current.menu, current.track,
                current.in_race, current.rider, current.tour,
                race_entries, race_results_entries, circuit_results_entries,
                stunt_results_entries, track_changes, flags_csv(tour_pass_flags(current.tour))
            ))
            f:close()
            os.exit(3)
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
        if pending_award == nil then
            local current_value = memory.readbyte(MEDAL_BASE + probe_index)
            if current_value ~= baseline_medals[probe_index + 1] then
                local current_medals = read_medals()
                local index, before_value, after_value =
                    first_medal_change(baseline_medals, current_medals)
                if index ~= nil then
                    pending_award = {
                        detected_frame = current.frame,
                        index = index,
                        before_value = before_value,
                        after_value = after_value,
                        previous = previous,
                        detected = current,
                    }
                end
            end
            probe_index = (probe_index + 1) % MEDAL_COUNT
        else
            local settled_medals = read_medals()
            local index = pending_award.index
            local expected_value = pending_award.after_value
            if settled_medals[index + 1] ~= expected_value then
                error("detected medal mutation did not persist while transaction settled")
            end

            if checksum_valid() then
                dump_sram(out)
                local row = math.floor(index / MEDAL_COLS)
                local rider_col = index % MEDAL_COLS
                local f = assert(io.open(meta, "w"))
                f:write(string.format(
                    "status=medal-captured-settled\nbaseline_frame=%d\ndetected_frame=%d\nsettled_frame=%d\n" ..
                    "settlement_frames=%d\ndetection_lag_max_frames=%d\n" ..
                    "medal_index=%d\ntour_row=%d\nrider_column=%d\n" ..
                    "medal_before=%d\nmedal_after=%d\n" ..
                    "detected_menu=%d\ndetected_track=%d\ndetected_in_race=%d\n" ..
                    "settled_menu=%d\nsettled_track=%d\nsettled_in_race=%d\n" ..
                    "settled_rider=%d\nsettled_tour=%d\nsettled_tier=%d\n" ..
                    "tour_pass_flags=%s\n",
                    baseline.frame, pending_award.detected_frame, current.frame,
                    current.frame - pending_award.detected_frame, MEDAL_COUNT - 1,
                    index, row, rider_col, pending_award.before_value, expected_value,
                    pending_award.detected.menu, pending_award.detected.track, pending_award.detected.in_race,
                    current.menu, current.track, current.in_race,
                    current.rider, current.tour, current.tier,
                    flags_csv(tour_pass_flags(current.tour))
                ))
                f:close()
                os.exit(0)
            end

            if current.frame - pending_award.detected_frame >= MAX_SETTLE_FRAMES then
                local f = assert(io.open(meta, "w"))
                f:write(string.format(
                    "status=medal-captured-checksum-did-not-settle\ndetected_frame=%d\nframe=%d\n" ..
                    "medal_index=%d\nmedal_before=%d\nmedal_after=%d\n",
                    pending_award.detected_frame, current.frame, index,
                    pending_award.before_value, expected_value
                ))
                f:close()
                os.exit(4)
            end
        end
    end
    previous = current
end
