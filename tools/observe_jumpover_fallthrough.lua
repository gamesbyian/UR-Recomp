-- Read-only per-frame observer for Jumpover fall-through movie replays in
-- historical Snes9x 1.51-rr (-autodemo <movie> -loadlua <this>).
-- It never writes game state or input. One line per emulated movie frame:
--   frame=<movie frame after emulation> <field>=<value> ...
-- Fields are the docs/SYMBOLS.md slots used by tools/extract_smv_freeze.py.
-- Numbers are formatted with string.format("%d"): tostring() on numbers is
-- unreliable in the locally built historical Lua bridge.
local log_path = os.getenv("UR_JO_LOG") or "jumpover-observe.txt"
local done_path = os.getenv("UR_JO_DONE") or "jumpover-observe.done"

snes9x.speedmode("maximum")

local function u16(a) return memory.readword(0x7E0000 + a) end
local function s16(a) return memory.readwordsigned(0x7E0000 + a) end
local function u8(a) return memory.readbyte(0x7E0000 + a) end

local FIELDS = {
    {"track_id", function() return u8(0x00CE) end},
    {"race_active", function() return u8(0x0313) end},
    {"p1_x", function() return u16(0x0411) end},
    {"p1_y", function() return u16(0x0415) end},
    {"p1_x_speed", function() return s16(0x04B7) end},
    {"p1_y_speed", function() return s16(0x04BB) end},
    {"p1_pitch", function() return u16(0x04C7) % 64 end},
    {"p1_air_time", function() return u16(0x0545) end},
    {"p1_stunt_air_latch", function() return u16(0x1361) end},
    {"p1_angular_velocity", function() return s16(0x0BAD) end},
    {"p1_z_rotation", function() return u16(0x0DFD) end},
    {"p1_roll_count", function() return u16(0x11F9) end},
    {"p1_flip_count", function() return u16(0x11FD) end},
    {"p1_contact_word_persisted", function() return u16(0x0E95) end},
    {"current_contact_word", function() return u16(0x0F09) end},
    {"p1_next_checkpoint", function() return u16(0x1199) end},
    {"p2_x", function() return u16(0x0413) end},
    {"p2_y", function() return u16(0x0417) end},
}

local out = assert(io.open(log_path, "w"))
local seen_active = false
local length = nil

local function finish(status)
    out:close()
    local f = assert(io.open(done_path, "w"))
    f:write("status=" .. status .. "\n")
    f:close()
    -- os.exit stops only the Lua thread on this frontend; the driver kills
    -- the emulator once the done file exists.
    os.exit(0)
end

while true do
    emu.frameadvance()
    if movie.active() then
        if not seen_active then
            seen_active = true
            length = movie.length()
            out:write(string.format("movie_length=%d\n", length))
        end
        local parts = {string.format("frame=%d", snes9x.framecount())}
        for _, f in ipairs(FIELDS) do
            parts[#parts + 1] = string.format("%s=%d", f[1], f[2]())
        end
        out:write(table.concat(parts, " ") .. "\n")
        if snes9x.framecount() >= length then
            finish("complete")
        end
    elseif seen_active then
        finish("movie-stopped-early")
    end
end
