#!/usr/bin/env python3
"""Stage SDL controller seat ownership hardening into the pinned Baldosa host.

The pinned SNESRecomp desktop host (``host_main.c``) owns device discovery,
seat assignment and polling. Its seat rule had a lifecycle defect: a newly
added pad's SDL player index could claim a seat *already occupied* by
another pad (``k == 0 ||`` skipped the vacancy check). SDL3 hands an XInput
pad its XInput slot back on reconnect and bumps whichever pad held that
player index, so re-plugging one controller in a two-player session could
overwrite the other player's seat. The orphaned pad's later button releases
were then dropped, leaving its bits held in the shared pad word.

This disposable-checkout patch replaces only the seat *choice* with the
project-owned ``native/product/controller_seat_assignment_policy.h`` and adds:

* reconnect ownership: a returning device (same SDL GUID + serial) reclaims
  the seat it vacated, and a new pad prefers a seat nobody is away from;
* an unseated, already-open spare pad (mapped or raw) may take a vacant
  seat by pressing a button; that claiming press is consumed, never
  delivered to the guest. The host holds exactly one handle per spare and
  closes it on removal or re-seat;
* on removal, defensive release of any bits the pad still holds (SDL3
  already recentres before ``REMOVED``; this keeps both backends safe) and
  closing the gamepad handle the host opened;
* ``SNESRECOMP_UR_CONTROLLER_LIFECYCLE_ACCEPTANCE=1`` (SDL3 only): a
  virtual-gamepad hotplug scenario with fail-closed ``UR_CONTROLLER_ACCEPT``
  log lines. Inert unless that variable is set.

No guest, simulation, binding, mapping or keyboard code is touched; the
keyboard keeps feeding both players exactly as before. The patch is
guarded, atomic across files and idempotent.
"""
from __future__ import annotations

import argparse
from pathlib import Path

MARK = "UR_BALDOSA_SDL_CONTROLLER_LIFECYCLE"
POLICY = "native/product/controller_seat_assignment_policy.h"

SELECTION = (
    "  uint8 scan_order[3] = { SDL_GameControllerGetPlayerIndex(controller), 0, 1 };\n"
    "  /* The self-test pad must be player 1: the overlay gestures read seat 0. */\n"
    "  if (g_selftest_pad && SDL_JoystickInstanceID(g_selftest_pad) == joystick_id)\n"
    "    scan_order[0] = 0;\n"
    "\n"
    "  int found_idx = -1;\n"
    "  for (int k = 0; k < 3; k++) {\n"
    "    uint8 j = scan_order[k];\n"
    "    if (j < 2 && g_config.enable_gamepad[j] && (k == 0 || g_gamepad[j].joystick_id == -1)) {\n"
    "      found_idx = j;\n"
    "      break;\n"
    "    }\n"
    "  }\n"
)
SELECTION_NEW = (
    "  /* " + MARK + ": never steal an occupied seat. */\n"
    "  /* The self-test pad must be player 1: the overlay gestures read seat 0. */\n"
    "  const int forced_seat =\n"
    "      g_selftest_pad && SDL_JoystickInstanceID(g_selftest_pad) == joystick_id ? 0 : -1;\n"
    "  int found_idx = UrSeatAssign(SDL_GameControllerGetJoystick(controller),\n"
    "                               SDL_GameControllerGetPlayerIndex(controller),\n"
    "                               forced_seat, joystick_id, controller);\n"
)

RAW_SELECTION = (
    "  int slot = -1;\n"
    "  for (int j = 0; j < 2; ++j) {\n"
    "    if (g_config.enable_gamepad[j] && g_gamepad[j].joystick_id == -1) {\n"
    "      slot = j; break;\n"
    "    }\n"
    "  }\n"
)
RAW_SELECTION_NEW = (
    "  /* " + MARK + ": raw sticks follow the same seat ownership rule. */\n"
    "  int slot = UrSeatAssign(joystick, SDL_JoystickGetPlayerIndex(joystick),\n"
    "                          -1, id, NULL);\n"
)

PAD_REMOVED = (
    "  case SDL_CONTROLLERDEVICEREMOVED:\n"
    "    gi = GetGamepadInfo(SNESRECOMP_SDL_EVENT_DEVICE(*event));\n"
    "    if (gi) {\n"
    "      memset(gi, 0, sizeof(GamepadInfo));\n"
)
PAD_REMOVED_NEW = (
    "  case SDL_CONTROLLERDEVICEREMOVED:\n"
    "    gi = GetGamepadInfo(SNESRECOMP_SDL_EVENT_DEVICE(*event));\n"
    "    /* " + MARK + ": an unseated spare pad was opened but never closed. */\n"
    "    if (!gi) UrSpareRemoved(SNESRECOMP_SDL_EVENT_DEVICE(*event));\n"
    "    if (gi) {\n"
    "      UrSeatRelease(gi);  /* " + MARK + " */\n"
    "      memset(gi, 0, sizeof(GamepadInfo));\n"
)

PAD_BUTTON = (
    "  case SDL_CONTROLLERBUTTONDOWN:\n"
    "  case SDL_CONTROLLERBUTTONUP:\n"
    "    gi = GetGamepadInfo(SNESRECOMP_SDL_EVENT_BUTTON_DEVICE(*event));\n"
    "    if (gi) {\n"
)
PAD_BUTTON_NEW = (
    "  case SDL_CONTROLLERBUTTONDOWN:\n"
    "  case SDL_CONTROLLERBUTTONUP:\n"
    "    gi = GetGamepadInfo(SNESRECOMP_SDL_EVENT_BUTTON_DEVICE(*event));\n"
    "    /* " + MARK + ": an open spare pad's press may take a vacant seat;\n"
    "     * the claiming press itself never reaches the guest. */\n"
    "    if (!gi && event->type == SDL_CONTROLLERBUTTONDOWN) {\n"
    "      UrSeatClaim(SNESRECOMP_SDL_EVENT_BUTTON_DEVICE(*event), false);\n"
    "      return true;\n"
    "    }\n"
    "    if (gi) {\n"
)

# OpenOneGamepad leaves an unseated pad open; the host now owns that handle.
PAD_FOUND = (
    "  printf(\"Found controller '%s' assigning to player %d\\n\", "
    "SDL_GameControllerName(controller), found_idx + 1);\n"
)
PAD_FOUND_NEW = (
    "  if (found_idx < 0) UrSpareKeep(joystick_id, controller, NULL);  /* " + MARK + " */\n"
    + PAD_FOUND
)

# A raw stick with no free seat used to be closed, so unlike a mapped pad it
# could never take a seat that frees up later.
RAW_UNSEATED = "  if (slot < 0) { SDL_JoystickClose(joystick); return; }\n"
RAW_UNSEATED_NEW = (
    "  /* " + MARK + ": kept open as a spare, like an unseated mapped pad. */\n"
    "  if (slot < 0) { UrSpareKeep(id, NULL, joystick); return; }\n"
)

RAW_BUTTON = (
    "  case SDL_JOYBUTTONDOWN:\n"
    "  case SDL_JOYBUTTONUP:\n"
    "    gi = GetGamepadInfo(event->jbutton.which);\n"
)
RAW_BUTTON_NEW = RAW_BUTTON + (
    "    /* " + MARK + ": a raw spare's press may take a vacant seat; the\n"
    "     * claiming press never reaches the guest. */\n"
    "    if (!gi && event->type == SDL_JOYBUTTONDOWN &&\n"
    "        UrSeatClaim(event->jbutton.which, true))\n"
    "      return true;\n"
)

RAW_REMOVED = (
    "  case SDL_JOYDEVICEREMOVED:\n"
    "    gi = GetGamepadInfo(event->jdevice.which);\n"
    "    if (gi && gi->raw_joystick) {\n"
)
RAW_REMOVED_NEW = (
    "  case SDL_JOYDEVICEREMOVED:\n"
    "    gi = GetGamepadInfo(event->jdevice.which);\n"
    "    if (!gi) UrSpareRemoved(event->jdevice.which);  /* " + MARK + " */\n"
    "    if (gi && gi->raw_joystick) {\n"
    "      UrSeatRelease(gi);  /* " + MARK + " */\n"
)

REASSIGN = "  g_pad_buttons = 0;\n  OpenAllGamepads();\n}\n"
REASSIGN_NEW = (
    "  g_pad_buttons = 0;\n"
    "  UrSeatReset();  /* " + MARK + ": the launcher re-seats from scratch */\n"
    "  OpenAllGamepads();\n}\n"
)

HELPERS_ANCHOR = "static bool HandleDeviceEvent(const SDL_Event *event) {\n"

# Keyboard fallback. Any launcher commit writes SourceP1 = 2 (gamepad) once a
# config predates the Source keys -- with no pad attached at all -- and a
# gamepad-sourced player ignores the keyboard, so one Ctrl+L round trip left a
# keyboard-only player with no control at all.
KEYBOARD_P1 = (
    "  uint32 p1 = g_config.player_src[0] == 1 ? keybinds_read_player_runner(keys, 1) : 0;\n"
)
KEYBOARD_P1_NEW = (
    "  uint32 p1 = UrKeyboardDrives(0) ? keybinds_read_player_runner(keys, 1) : 0;"
    "  /* " + MARK + " */\n"
)
ACTIVE_P1 = "                (g_config.player_src[0] == 1 ? 1u : 0u) |\n"
ACTIVE_P1_NEW = "                (UrKeyboardDrives(0) ? 1u : 0u) |  /* " + MARK + " */\n"

# The in-game launcher runs its own event loop over the same SDL queue, so
# pads added or removed while it is open never reach HandleDeviceEvent.
LAUNCHER_RETURN = "  SDL_FlushEvent(SDL_QUIT);\n"
LAUNCHER_RETURN_NEW = LAUNCHER_RETURN + (
    "  UrSeatReconcile(\"launcher_returned\");  /* " + MARK + " */\n"
)

# OpenAllGamepads seats every pad present at start-up in SDL's enumeration
# order; sort it so the XInput slot order (ring lights) decides P1/P2.
ENUMERATE = "  SDL_JoystickID *joysticks = SDL_GetJoysticks(&njs);\n#else\n"
ENUMERATE_NEW = (
    "  SDL_JoystickID *joysticks = SDL_GetJoysticks(&njs);\n"
    "  UrSortByPlayerIndex(joysticks, njs);  /* " + MARK + " */\n#else\n"
)

# The pinned host let pads drive the game while another window had focus.
# Overlays navigated with the same pad (the Xbox Game Bar the Guide button
# opens, Steam's, Discord's) then also moved the game's menus behind them
# and resumed a focus-paused race (#2334). SDL still delivers releases and
# re-centring while unfocused, so nothing stays held.
BACKGROUND = '  SDL_SetHint(SDL_HINT_JOYSTICK_ALLOW_BACKGROUND_EVENTS, "1");\n'
BACKGROUND_NEW = (
    "  /* " + MARK + ": pads drive the game only while its window has focus.\n"
    "   * Hosted test runs may not get focus; they opt back in. */\n"
    "  {\n"
    '    const char *bg = HostGetenv("UR_BACKGROUND_PAD_INPUT");  /* test only */\n'
    '    SDL_SetHint(SDL_HINT_JOYSTICK_ALLOW_BACKGROUND_EVENTS, bg && atoi(bg) ? "1" : "0");\n'
    "  }\n"
)

TICK_ANCHOR = "    OverlaySelftestPadMainTick(frameCtr);\n"
TICK_NEW = TICK_ANCHOR + "    UrControllerLifecycleAcceptanceTick();  /* " + MARK + " */\n"


def helpers(policy: Path) -> str:
    return (
        "/* " + MARK + ": seat ownership over the existing g_gamepad table.\n"
        " * The choice itself lives in the project-owned policy header. */\n"
        f'#include "{policy.as_posix()}"\n'
        "static bool SelftestPadExcludes(SDL_JoystickID id);\n"
        "static UrControllerSeatSlot g_ur_seats[UR_CONTROLLER_SEAT_COUNT];\n"
        "static uint64_t g_ur_seat_key[UR_CONTROLLER_SEAT_COUNT];\n"
        "static SDL_GameController *g_ur_seat_pad[UR_CONTROLLER_SEAT_COUNT];\n"
        "static uint64_t UrDeviceKey(SDL_Joystick *joystick) {\n"
        "  if (!joystick) return 0;\n"
        "  SDL_JoystickGUID guid = SDL_JoystickGetGUID(joystick);\n"
        "  return ur_controller_device_key(guid.data, SDL_JoystickGetSerial(joystick));\n"
        "}\n"
        "/* The player number SDL keeps per device drives DualSense and Switch\n"
        " * lights. SDL hands a new device the lowest free number and bumps any\n"
        " * device already holding a number given to another, so after every seat\n"
        " * decision each seated pad is told its seat again. */\n"
        "static void UrSeatShowPlayerIndex(void) {\n"
        "  for (int i = 0; i < UR_CONTROLLER_SEAT_COUNT; i++) {\n"
        "    SDL_Joystick *j = g_gamepad[i].joystick_id == -1 ? NULL\n"
        "        : g_gamepad[i].raw_joystick ? g_gamepad[i].joystick\n"
        "        : g_ur_seat_pad[i] ? SDL_GameControllerGetJoystick(g_ur_seat_pad[i]) : NULL;\n"
        "    if (j && SDL_JoystickGetPlayerIndex(j) != i) SDL_JoystickSetPlayerIndex(j, i);\n"
        "  }\n"
        "}\n"
        "/* Choose and record a seat; -1 leaves the pad unseated (but open). */\n"
        "static int UrSeatAssign(SDL_Joystick *joystick, int player_index,\n"
        "                        int forced_seat, SDL_JoystickID id,\n"
        "                        SDL_GameController *pad) {\n"
        "  const uint64_t key = UrDeviceKey(joystick);\n"
        "  for (int i = 0; i < UR_CONTROLLER_SEAT_COUNT; i++) {\n"
        "    g_ur_seats[i].enabled = g_config.enable_gamepad[i] != 0;\n"
        "    g_ur_seats[i].occupied = g_gamepad[i].joystick_id != -1;\n"
        "  }\n"
        "  const UrControllerSeatChoice choice =\n"
        "      ur_controller_seat_choose(g_ur_seats, key, player_index, forced_seat);\n"
        "  printf(\"[Gamepad] UR_CONTROLLER_SEAT assign instance=%u seat=%d reason=%s \"\n"
        "         \"player_index=%d key=%016llx\\n\", (unsigned)id, choice.seat,\n"
        "         ur_controller_seat_reason_name(choice.reason), player_index,\n"
        "         (unsigned long long)key);\n"
        "  /* The pad's own player number shows its seat; an unseated spare shows\n"
        "   * none, and any seated pad it bumped is told its seat again. */\n"
        "  if (joystick) SDL_JoystickSetPlayerIndex(joystick, choice.seat);\n"
        "  UrSeatShowPlayerIndex();\n"
        "  if (choice.seat < 0) return -1;\n"
        "  ur_controller_seat_taken(g_ur_seats, choice.seat, key);\n"
        "  g_ur_seat_key[choice.seat] = key;\n"
        "  g_ur_seat_pad[choice.seat] = pad;\n"
        "  return choice.seat;\n"
        "}\n"
        "/* A seated pad is going away: let go of everything it still holds and\n"
        " * remember who owned the seat. The caller then clears the slot. */\n"
        "static void UrSeatRelease(GamepadInfo *gi) {\n"
        "  const int seat = gi->index;\n"
        "  for (int b = 0; b < kGamepadBtn_Count; b++) {\n"
        "    if (gi->modifiers & (1u << b)) HandleGamepadInput(gi, b, false);\n"
        "  }\n"
        "  gi->axis_buttons = 0;\n"
        "  if (seat < 0 || seat >= UR_CONTROLLER_SEAT_COUNT) return;\n"
        "  printf(\"[Gamepad] UR_CONTROLLER_SEAT vacate instance=%u seat=%d key=%016llx\\n\",\n"
        "         (unsigned)gi->joystick_id, seat, (unsigned long long)g_ur_seat_key[seat]);\n"
        "  ur_controller_seat_vacated(g_ur_seats, seat, g_ur_seat_key[seat]);\n"
        "  if (g_ur_seat_pad[seat]) SDL_GameControllerClose(g_ur_seat_pad[seat]);\n"
        "  g_ur_seat_pad[seat] = NULL;\n"
        "  g_ur_seat_key[seat] = 0;\n"
        "}\n"
        "/* Spares: open but unseated pads, so a press can take a seat that\n"
        " * frees up. The host owns exactly one handle per spare. */\n"
        "enum { kUrSpareMax = 8 };\n"
        "static struct { SDL_JoystickID id; SDL_GameController *pad; SDL_Joystick *raw; }\n"
        "    g_ur_spare[kUrSpareMax];\n"
        "static int UrSpareFind(SDL_JoystickID id) {\n"
        "  for (int i = 0; i < kUrSpareMax; i++)\n"
        "    if ((g_ur_spare[i].pad || g_ur_spare[i].raw) && g_ur_spare[i].id == id) return i;\n"
        "  return -1;\n"
        "}\n"
        "static void UrSpareClose(int i) {\n"
        "  if (g_ur_spare[i].pad) SDL_GameControllerClose(g_ur_spare[i].pad);\n"
        "  if (g_ur_spare[i].raw) SDL_JoystickClose(g_ur_spare[i].raw);\n"
        "  memset(&g_ur_spare[i], 0, sizeof(g_ur_spare[i]));\n"
        "}\n"
        "static void UrSpareKeep(SDL_JoystickID id, SDL_GameController *pad, SDL_Joystick *raw) {\n"
        "  int free_slot = -1;\n"
        "  for (int i = 0; i < kUrSpareMax; i++) {\n"
        "    if ((g_ur_spare[i].pad || g_ur_spare[i].raw) && g_ur_spare[i].id == id) free_slot = -2;\n"
        "    else if (free_slot == -1 && !g_ur_spare[i].pad && !g_ur_spare[i].raw) free_slot = i;\n"
        "  }\n"
        "  if (free_slot < 0) {  /* already held, or no room: drop this extra handle */\n"
        "    if (pad) SDL_GameControllerClose(pad);\n"
        "    if (raw) SDL_JoystickClose(raw);\n"
        "    return;\n"
        "  }\n"
        "  g_ur_spare[free_slot].id = id;\n"
        "  g_ur_spare[free_slot].pad = pad;\n"
        "  g_ur_spare[free_slot].raw = raw;\n"
        "  printf(\"[Gamepad] UR_CONTROLLER_SEAT spare_kept instance=%u raw=%d\\n\",\n"
        "         (unsigned)id, raw ? 1 : 0);\n"
        "}\n"
        "/* A spare is going away: close the handle the host holds for it. */\n"
        "static void UrSpareRemoved(SDL_JoystickID id) {\n"
        "  const int i = UrSpareFind(id);\n"
        "  if (i < 0) return;\n"
        "  printf(\"[Gamepad] UR_CONTROLLER_SEAT spare_closed instance=%u\\n\", (unsigned)id);\n"
        "  UrSpareClose(i);\n"
        "}\n"
        "/* A spare's press: take a vacant seat. Returns 1 when the press was a\n"
        " * claim (taken or not), so the caller consumes it. */\n"
        "static int UrSeatClaim(SDL_JoystickID id, bool raw) {\n"
        "  const int i = UrSpareFind(id);\n"
        "  if (i < 0 || SelftestPadExcludes(id) || (raw ? !g_ur_spare[i].raw : !g_ur_spare[i].pad))\n"
        "    return 0;\n"
        "  SDL_GameController *pad = g_ur_spare[i].pad;\n"
        "  SDL_Joystick *joystick = pad ? SDL_GameControllerGetJoystick(pad) : g_ur_spare[i].raw;\n"
        "  const int seat = UrSeatAssign(joystick, SDL_JoystickGetPlayerIndex(joystick), -1, id, pad);\n"
        "  if (seat < 0) return 1;\n"
        "  GamepadInfo *gi = &g_gamepad[seat];\n"
        "  memset(gi, 0, sizeof(GamepadInfo));\n"
        "  gi->index = (uint8)seat;\n"
        "  gi->joystick_id = id;\n"
        "  if (!pad) {\n"
        "    gi->joystick = joystick;\n"
        "    gi->raw_joystick = true;\n"
        "  }\n"
        "  memset(&g_ur_spare[i], 0, sizeof(g_ur_spare[i]));  /* the seat owns it now */\n"
        "  printf(\"[Gamepad] UR_CONTROLLER_SEAT claim instance=%u seat=%d\\n\", (unsigned)id, seat);\n"
        "  return 1;\n"
        "}\n"
        "static void UrSeatReset(void) {\n"
        "  for (int i = 0; i < UR_CONTROLLER_SEAT_COUNT; i++) {\n"
        "    if (g_ur_seat_pad[i]) SDL_GameControllerClose(g_ur_seat_pad[i]);\n"
        "    g_ur_seat_pad[i] = NULL;\n"
        "    g_ur_seat_key[i] = 0;\n"
        "  }\n"
        "  memset(g_ur_seats, 0, sizeof(g_ur_seats));\n"
        "  /* OpenAllGamepads reopens every device, spares included. */\n"
        "  for (int i = 0; i < kUrSpareMax; i++) UrSpareClose(i);\n"
        "}\n"
        "#if SNESRECOMP_SDL3\n"
        "/* Seat devices found together (start-up, a reconcile) gamepads first, so\n"
        " * an unmapped stick (a wheel, a flight stick, a peripheral's joystick\n"
        " * interface) never takes P1 from a real pad, then in SDL player index\n"
        " * order, so the pad whose XInput slot (ring light) says 1 is P1 and the\n"
        " * one saying 2 is P2. A device without an index goes after those with\n"
        " * one; SDL's own order breaks ties. */\n"
        "static uint64_t UrSeatingRank(SDL_JoystickID id) {\n"
        "  return ((uint64_t)(SDL_IsGamepad(id) ? 0u : 1u) << 32) |\n"
        "         (uint32_t)SDL_GetJoystickPlayerIndexForID(id);\n"
        "}\n"
        "static void UrSortByPlayerIndex(SDL_JoystickID *ids, int count) {\n"
        "  for (int i = 1; ids && i < count; i++) {\n"
        "    const SDL_JoystickID id = ids[i];\n"
        "    const uint64_t rank = UrSeatingRank(id);\n"
        "    int j = i;\n"
        "    while (j > 0 && UrSeatingRank(ids[j - 1]) > rank) {\n"
        "      ids[j] = ids[j - 1];\n"
        "      j--;\n"
        "    }\n"
        "    ids[j] = id;\n"
        "  }\n"
        "}\n"
        "#endif\n"
        "/* Catch up on hotplug another event loop consumed: release seats and\n"
        " * spares whose device is gone, then open devices the host never saw.\n"
        " * Seat memory is kept, so a pad that returned still reclaims its seat. */\n"
        "static unsigned g_ur_reconcile_gone, g_ur_reconcile_new;\n"
        "static void UrSeatReconcile(const char *why) {\n"
        "  for (int i = 0; i < UR_CONTROLLER_SEAT_COUNT; i++) {\n"
        "    GamepadInfo *gi = &g_gamepad[i];\n"
        "    if (gi->joystick_id == -1) continue;\n"
        "    const bool attached = gi->raw_joystick\n"
        "        ? gi->joystick && SDL_JoystickGetAttached(gi->joystick)\n"
        "        : g_ur_seat_pad[i] && SDL_GameControllerGetAttached(g_ur_seat_pad[i]);\n"
        "    if (attached) continue;\n"
        "    printf(\"[Gamepad] UR_CONTROLLER_SEAT reconcile reason=%s gone instance=%u seat=%d\\n\",\n"
        "           why, (unsigned)gi->joystick_id, i);\n"
        "    ++g_ur_reconcile_gone;\n"
        "    const bool raw = gi->raw_joystick;\n"
        "    SDL_Joystick *raw_handle = gi->joystick;\n"
        "    UrSeatRelease(gi);\n"
        "    if (raw && raw_handle) SDL_JoystickClose(raw_handle);\n"
        "    memset(gi, 0, sizeof(GamepadInfo));\n"
        "    gi->joystick_id = -1;\n"
        "  }\n"
        "  for (int i = 0; i < kUrSpareMax; i++) {\n"
        "    const bool attached = g_ur_spare[i].pad\n"
        "        ? SDL_GameControllerGetAttached(g_ur_spare[i].pad)\n"
        "        : g_ur_spare[i].raw && SDL_JoystickGetAttached(g_ur_spare[i].raw);\n"
        "    if ((g_ur_spare[i].pad || g_ur_spare[i].raw) && !attached) UrSpareRemoved(g_ur_spare[i].id);\n"
        "  }\n"
        "#if SNESRECOMP_SDL3\n"
        "  int count = 0;\n"
        "  SDL_JoystickID *ids = SDL_GetJoysticks(&count);\n"
        "  UrSortByPlayerIndex(ids, count);\n"
        "  for (int i = 0; ids && i < count; i++) {\n"
        "    const SDL_JoystickID id = ids[i];\n"
        "    const int open_arg = (int)id;\n"
        "#else\n"
        "  const int count = SDL_NumJoysticks();\n"
        "  for (int i = 0; i < count; i++) {\n"
        "    const SDL_JoystickID id = SDL_JoystickGetDeviceInstanceID(i);\n"
        "    const int open_arg = i;\n"
        "#endif\n"
        "    if (GetGamepadInfo(id) || UrSpareFind(id) >= 0 || SelftestPadExcludes(id)) continue;\n"
        "    printf(\"[Gamepad] UR_CONTROLLER_SEAT reconcile reason=%s new instance=%u\\n\",\n"
        "           why, (unsigned)id);\n"
        "    ++g_ur_reconcile_new;\n"
        "    OpenOneGamepad(open_arg);\n"
        "  }\n"
        "#if SNESRECOMP_SDL3\n"
        "  SDL_free(ids);\n"
        "#endif\n"
        "}\n"
        "/* Whether the keyboard drives a player. Keyboard-sourced players, as\n"
        " * before; and P1 when set to Gamepad with no pad in its seat (none\n"
        " * plugged in, or it was unplugged), unless P2 already uses the keyboard\n"
        " * (both players default to the same keys). A seated pad keeps P1's\n"
        " * input to itself, exactly as before. */\n"
        "static bool UrKeyboardDrives(int player) {\n"
        "  const int src = g_config.player_src[player];\n"
        "  if (src == 1) return true;\n"
        "  return player == 0 && src == 2 && g_gamepad[0].joystick_id == -1 &&\n"
        "         g_config.player_src[1] != 1;\n"
        "}\n"
        "static uint32 GetActiveControllers(void);\n"
        "/* Product-facing: move the pad seated in `from` to the empty, enabled seat\n"
        " * `to` (keyboard + one pad joining 2P as P2). Held bits are released on the\n"
        " * old seat first; `from` is left free for anyone, and a replug of the moved\n"
        " * pad reclaims `to`. Returns 1 when moved, 0 when refused. */\n"
        "int snesrecomp_desktop_product_seat_move(int from, int to) {\n"
        "  if (from < 0 || from >= UR_CONTROLLER_SEAT_COUNT || to < 0 ||\n"
        "      to >= UR_CONTROLLER_SEAT_COUNT || from == to) return 0;\n"
        "  GamepadInfo *src = &g_gamepad[from], *dst = &g_gamepad[to];\n"
        "  if (src->joystick_id == -1 || dst->joystick_id != -1 ||\n"
        "      !g_config.enable_gamepad[to]) return 0;\n"
        "  const SDL_JoystickID id = src->joystick_id;\n"
        "  const bool raw = src->raw_joystick;\n"
        "  SDL_Joystick *raw_handle = src->joystick;\n"
        "  SDL_GameController *pad = g_ur_seat_pad[from];\n"
        "  const uint64_t key = g_ur_seat_key[from];\n"
        "  for (int b = 0; b < kGamepadBtn_Count; b++) {\n"
        "    if (src->modifiers & (1u << b)) HandleGamepadInput(src, b, false);\n"
        "  }\n"
        "  src->axis_buttons = 0;\n"
        "  memset(src, 0, sizeof(GamepadInfo));\n"
        "  src->joystick_id = -1;\n"
        "  g_ur_seat_pad[from] = NULL;\n"
        "  g_ur_seat_key[from] = 0;\n"
        "  g_ur_seats[from].occupied = 0;\n"
        "  g_ur_seats[from].absent_owner_key = 0;  /* nobody is away from it */\n"
        "  memset(dst, 0, sizeof(GamepadInfo));\n"
        "  dst->index = (uint8)to;\n"
        "  dst->joystick_id = id;\n"
        "  if (raw) {\n"
        "    dst->joystick = raw_handle;\n"
        "    dst->raw_joystick = true;\n"
        "  }\n"
        "  ur_controller_seat_taken(g_ur_seats, to, key);\n"
        "  g_ur_seat_key[to] = key;\n"
        "  g_ur_seat_pad[to] = pad;\n"
        "  SDL_Joystick *moved = raw ? raw_handle : pad ? SDL_GameControllerGetJoystick(pad) : NULL;\n"
        "  if (moved) SDL_JoystickSetPlayerIndex(moved, to);  /* its lights follow */\n"
        "  printf(\"[Gamepad] UR_CONTROLLER_SEAT move instance=%u from=%d to=%d\\n\",\n"
        "         (unsigned)id, from, to);\n"
        "  return 1;\n"
        "}\n"
        "/* Product-facing, read-only: the SDL instance occupying a seat, or -1.\n"
        " * Modern polls this at the completed-frame boundary to notice a seat\n"
        " * owner leaving; it never chooses or changes a seat. */\n"
        "long long snesrecomp_desktop_product_seat_source(int seat) {\n"
        "  if (seat < 0 || seat >= UR_CONTROLLER_SEAT_COUNT) return -1;\n"
        "  return g_gamepad[seat].joystick_id != -1\n"
        "      ? (long long)g_gamepad[seat].joystick_id : -1;\n"
        "}\n"
        "/* Product-facing, read-only: input comes from a --script, so no player\n"
        " * is present to resume a pause the host did not ask for. */\n"
        "int snesrecomp_desktop_product_input_scripted(void) {\n"
        "  return g_script_count > 0;\n"
        "}\n"
        + ACCEPTANCE + "\n"
    )


# Fail-closed virtual-device scenario. Each step waits a few host frames so
# the ordinary main-loop SDL_PollEvent/HandleDeviceEvent path delivers the
# device events; nothing here calls the seat helpers directly.
ACCEPTANCE = r'''#if SNESRECOMP_SDL3
enum { kUrAcceptPads = 6, kUrAcceptRaw = 5, kUrAcceptSettle = 6 };
static SDL_JoystickID g_ur_accept_spare_id;
static int g_ur_accept_b_seat = -1;
static SDL_JoystickID g_ur_accept_id[kUrAcceptPads];
static SDL_Joystick *g_ur_accept_joy[kUrAcceptPads];
static int g_ur_accept_step, g_ur_accept_wait, g_ur_accept_failed, g_ur_accept_on = -1;
static int UrAcceptSeatOf(int pad) {
  if (!g_ur_accept_id[pad]) return -1;
  for (int i = 0; i < 2; i++)
    if (g_gamepad[i].joystick_id == g_ur_accept_id[pad]) return i;
  return -1;
}
/* The player number SDL (and the pad's lights) currently show, -2 if absent. */
static int UrAcceptIndexOf(int pad) {
  return g_ur_accept_joy[pad] ? SDL_GetJoystickPlayerIndex(g_ur_accept_joy[pad]) : -2;
}
static void UrAcceptAttach(int pad, Uint16 product, int player_index) {
  static const char *const kNames[kUrAcceptPads] = {
    "UR lifecycle pad A", "UR lifecycle pad B", "UR lifecycle pad C", "UR lifecycle pad D",
    "UR lifecycle pad E", "UR lifecycle raw stick F"};
  SDL_VirtualJoystickDesc desc;
  SDL_INIT_INTERFACE(&desc);
  /* F is a generic stick SDL has no gamepad mapping for. */
  desc.type = pad == kUrAcceptRaw ? SDL_JOYSTICK_TYPE_UNKNOWN : SDL_JOYSTICK_TYPE_GAMEPAD;
  desc.naxes = pad == kUrAcceptRaw ? 2 : SDL_GAMEPAD_AXIS_COUNT;
  desc.nbuttons = pad == kUrAcceptRaw ? 8 : SDL_GAMEPAD_BUTTON_COUNT;
  desc.vendor_id = 0x1209;
  desc.product_id = product;
  desc.name = kNames[pad];
  g_ur_accept_id[pad] = SDL_AttachVirtualJoystick(&desc);
  g_ur_accept_joy[pad] = g_ur_accept_id[pad] ? SDL_OpenJoystick(g_ur_accept_id[pad]) : NULL;
  /* Mimic SDL handing a returning XInput pad a player index someone else
   * holds: SDL bumps that pad and the new one arrives with this index. */
  if (g_ur_accept_joy[pad] && player_index >= 0)
    SDL_SetJoystickPlayerIndex(g_ur_accept_joy[pad], player_index);
  if (!g_ur_accept_joy[pad]) g_ur_accept_failed = 1;
}
static void UrAcceptDetach(int pad) {
  if (g_ur_accept_joy[pad]) SDL_CloseJoystick(g_ur_accept_joy[pad]);
  if (g_ur_accept_id[pad]) SDL_DetachVirtualJoystick(g_ur_accept_id[pad]);
  g_ur_accept_joy[pad] = NULL;
  g_ur_accept_id[pad] = 0;
}
static void UrAcceptButton(int pad, bool down) {
  if (g_ur_accept_joy[pad])
    SDL_SetJoystickVirtualButton(g_ur_accept_joy[pad], SDL_GAMEPAD_BUTTON_SOUTH, down);
}
/* Stand in for another event loop (the in-game launcher) draining the
 * queue: the host never sees these device events. */
static void UrAcceptDrainDeviceEvents(void) {
  SDL_PumpEvents();
  SDL_FlushEvents(SDL_EVENT_JOYSTICK_AXIS_MOTION, SDL_EVENT_GAMEPAD_STEAM_HANDLE_UPDATED);
}
/* Fired from SDL's timer thread while the in-game launcher's own loop owns
 * the queue (the joystick API is locked internally). */
static Uint32 SDLCALL UrAcceptUnplugA(void *userdata, SDL_TimerID id, Uint32 interval) {
  (void)userdata; (void)id; (void)interval;
  UrAcceptDetach(0);
  return 0;
}
static Uint32 SDLCALL UrAcceptPlugB(void *userdata, SDL_TimerID id, Uint32 interval) {
  (void)userdata; (void)id; (void)interval;
  UrAcceptAttach(1, 0x5502, -1);
  return 0;
}
/* Every key down, read through the host's own keyboard poll; the real state
 * is restored by the main loop's poll before the next guest frame. */
static int g_ur_accept_src[2];
static uint32 g_ur_accept_held;
static uint32 UrAcceptKeyboardWord(void) {
  static uint8_t all_down[SDL_SCANCODE_COUNT];
  memset(all_down, 1, sizeof(all_down));
  PollKeyboardControls(all_down);
  const uint32 word = g_input_state;
  PollKeyboardControls(snesrecomp_sdl_get_keyboard_state());
  return word;
}
static void UrAcceptExpect(const char *step, bool ok) {
  printf("UR_CONTROLLER_ACCEPT step=%s pass=%d seats=%u,%u pad_buttons=%08x\n", step,
         ok ? 1 : 0, (unsigned)g_gamepad[0].joystick_id, (unsigned)g_gamepad[1].joystick_id,
         (unsigned)g_pad_buttons);
  if (!ok) g_ur_accept_failed = 1;
}
static void UrControllerLifecycleAcceptanceTick(void) {
  if (g_ur_accept_on < 0) {
    const char *v = HostGetenv("UR_CONTROLLER_LIFECYCLE_ACCEPTANCE");
    /* "1" runs the scenario; "exit" also quits when it is done; "launcher"
     * runs the real in-game launcher over hotplug instead, then quits;
     * "focus" checks that a pad is ignored while the window is unfocused. */
    g_ur_accept_on = !v ? 0 : strcmp(v, "launcher") == 0 ? 2
                   : strcmp(v, "focus") == 0 ? 3
                   : (atoi(v) || strcmp(v, "exit") == 0) ? 1 : 0;
  }
  if (!g_ur_accept_on || g_ur_accept_step < 0) return;
  if (g_ur_accept_wait > 0) { g_ur_accept_wait--; return; }
  g_ur_accept_wait = kUrAcceptSettle;
  if (g_ur_accept_on == 2) {
    /* Each unplug/plug fires on a timer while the launcher is open, so the
     * launcher's own loop drains the device event. */
    switch (g_ur_accept_step++) {
    case 0: UrAcceptAttach(0, 0x5501, -1); return;
    case 1:
      UrAcceptExpect("launcher_pad_seated", UrAcceptSeatOf(0) == 0);
      g_ur_accept_spare_id = g_ur_accept_id[0];
      SDL_AddTimer(400, UrAcceptUnplugA, NULL);
      g_open_launcher_hotkey = 1;
      return;
    case 2:
      UrAcceptExpect("launcher_removal_reconciled", g_gamepad[0].joystick_id == -1 &&
                     g_ur_reconcile_gone == 1 && g_pad_buttons == 0);
      SDL_AddTimer(400, UrAcceptPlugB, NULL);
      g_open_launcher_hotkey = 1;
      return;
    case 3:
      UrAcceptExpect("launcher_add_reconciled", UrAcceptSeatOf(1) >= 0 &&
                     g_ur_reconcile_new == 1);
      for (int i = 0; i < kUrAcceptPads; i++) UrAcceptDetach(i);
      return;
    default: break;
    }
    g_ur_accept_step = 1000;  /* fall into the shared result/quit below */
  }
  if (g_ur_accept_on == 3) {
    /* The product default: no background pad input. A desktop that never
     * takes focus away (or never gives it back) records not_exercised. */
    switch (g_ur_accept_step++) {
    case 0: UrAcceptAttach(0, 0x5501, -1); return;
    case 1:
      UrAcceptExpect("focus_pad_seated", UrAcceptSeatOf(0) == 0);
      SDL_MinimizeWindow(g_window);
      return;
    case 2:
      if (SDL_GetKeyboardFocus() != NULL) {
        printf("UR_CONTROLLER_ACCEPT step=unfocused_press_ignored not_exercised=1\n");
        g_ur_accept_step = 4;
        return;
      }
      UrAcceptButton(0, true);
      return;
    case 3:
      UrAcceptExpect("unfocused_press_ignored", (g_pad_buttons & 0xffffffu) == 0);
      UrAcceptButton(0, false);
      return;
    case 4:
      SDL_RestoreWindow(g_window);
      SDL_RaiseWindow(g_window);
      g_ur_accept_wait = 30;
      return;
    case 5:
      if (SDL_GetKeyboardFocus() != g_window) {
        printf("UR_CONTROLLER_ACCEPT step=focused_press_drives not_exercised=1\n");
        g_ur_accept_step = 7;
        return;
      }
      UrAcceptButton(0, true);
      return;
    case 6:
      UrAcceptExpect("focused_press_drives", (g_pad_buttons & 0xfffu) != 0);
      UrAcceptButton(0, false);
      return;
    case 7:
      for (int i = 0; i < kUrAcceptPads; i++) UrAcceptDetach(i);
      return;
    default: break;
    }
    g_ur_accept_step = 1000;
  }
  switch (g_ur_accept_on >= 2 ? 1000 : g_ur_accept_step++) {
  case 0: UrAcceptAttach(0, 0x5501, -1); break;
  case 1: UrAcceptAttach(1, 0x5502, -1); break;
  case 2:
    UrAcceptExpect("two_pads_seated", UrAcceptSeatOf(0) == 0 && UrAcceptSeatOf(1) == 1);
    /* C arrives claiming P1's player index while P1 and P2 are seated. */
    UrAcceptAttach(2, 0x5503, 0);
    break;
  case 3:
    UrAcceptExpect("no_steal", UrAcceptSeatOf(0) == 0 && UrAcceptSeatOf(1) == 1 &&
                   UrAcceptSeatOf(2) == -1);
    UrAcceptExpect("spare_shows_no_player_index", UrAcceptIndexOf(0) == 0 &&
                   UrAcceptIndexOf(1) == 1 && UrAcceptIndexOf(2) == -1);
    UrAcceptButton(2, true);  /* both seats full: no claim */
    break;
  case 4:
    UrAcceptButton(2, false);
    break;
  case 5:
    UrAcceptExpect("full_no_claim", UrAcceptSeatOf(2) == -1 && UrAcceptSeatOf(0) == 0 &&
                   g_pad_buttons == 0);
    UrAcceptDetach(0);
    break;
  case 6:
    UrAcceptExpect("p1_vacated", g_gamepad[0].joystick_id == -1 && UrAcceptSeatOf(1) == 1);
    /* A returns (same identity) and SDL gives it P2's player index. */
    UrAcceptAttach(0, 0x5501, 1);
    break;
  case 7:
    UrAcceptExpect("p1_reclaimed", UrAcceptSeatOf(0) == 0 && UrAcceptSeatOf(1) == 1 &&
                   UrAcceptSeatOf(2) == -1);
    /* A came back holding P2's number; it shows P1 again, B keeps P2. */
    UrAcceptExpect("reclaimed_pad_shows_its_seat", UrAcceptIndexOf(0) == 0 &&
                   UrAcceptIndexOf(1) == 1 && UrAcceptIndexOf(2) == -1);
    UrAcceptDetach(1);
    break;
  case 8:
    UrAcceptButton(2, true);  /* the spare pad takes the vacant P2 seat */
    break;
  case 9:
    UrAcceptButton(2, false);
    break;
  case 10:
    /* The claiming press was consumed: nothing reached P2's pad bits. */
    UrAcceptExpect("spare_claimed_p2", UrAcceptSeatOf(2) == 1 && UrAcceptSeatOf(0) == 0 &&
                   (g_pad_buttons & 0xfff000u) == 0);
    UrAcceptButton(2, true);
    break;
  case 11:
    UrAcceptDetach(2);  /* removed while held */
    break;
  case 12:
    UrAcceptExpect("held_released_on_remove", g_gamepad[1].joystick_id == -1 &&
                   (g_pad_buttons & 0xfff000u) == 0 && g_gamepad[1].axis_buttons == 0);
    /* D replaces C: the only vacancy is held for the absent C. */
    UrAcceptAttach(3, 0x5504, 1);
    break;
  case 13:
    UrAcceptExpect("replacement_takes_absent_seat", UrAcceptSeatOf(3) == 1 &&
                   UrAcceptSeatOf(0) == 0);
    UrAcceptDetach(3);
    UrAcceptDetach(0);
    break;
  case 14:
    /* Both players away. P2's pad returns first, holding player index 0. */
    UrAcceptAttach(3, 0x5504, 0);
    break;
  case 15:
    UrAcceptAttach(0, 0x5501, 0);
    break;
  case 16:
    UrAcceptExpect("returning_players_not_swapped", UrAcceptSeatOf(3) == 1 &&
                   UrAcceptSeatOf(0) == 0);
    /* Both seats stay full: E arrives as an unseated spare. */
    UrAcceptAttach(4, 0x5505, -1);
    break;
  case 17:
    g_ur_accept_spare_id = g_ur_accept_id[4];
    UrAcceptExpect("spare_unseated", UrAcceptSeatOf(4) == -1 &&
                   SDL_GetGamepadFromID(g_ur_accept_spare_id) != NULL);
    UrAcceptDetach(4);
    break;
  case 18:
    /* The host's own handle for the spare must be gone, not leaked. */
    UrAcceptExpect("spare_closed_on_remove",
                   SDL_GetGamepadFromID(g_ur_accept_spare_id) == NULL);
    /* Seats still full: unmapped stick F arrives. */
    UrAcceptAttach(kUrAcceptRaw, 0x5506, -1);
    break;
  case 19: {
    const SDL_JoystickID f = g_ur_accept_id[kUrAcceptRaw];
    const int kept = f ? UrSpareFind(f) : -1;
    UrAcceptExpect("raw_spare_kept", f && !SDL_IsGamepad(f) &&
                   UrAcceptSeatOf(kUrAcceptRaw) == -1 && kept >= 0 && g_ur_spare[kept].raw);
    OpenOneJoystick(f);  /* the host enumerating F again must not stack a handle */
    break;
  }
  case 20: {
    int held = 0;
    for (int i = 0; i < kUrSpareMax; i++)
      held += (g_ur_spare[i].pad || g_ur_spare[i].raw) &&
              g_ur_spare[i].id == g_ur_accept_id[kUrAcceptRaw];
    UrAcceptExpect("raw_spare_reopen_not_duplicated",
                   held == 1 && UrAcceptSeatOf(kUrAcceptRaw) == -1);
    UrAcceptDetach(3);  /* P2 leaves */
    break;
  }
  case 21:
    UrAcceptButton(kUrAcceptRaw, true);  /* F takes the vacant P2 seat */
    break;
  case 22:
    UrAcceptButton(kUrAcceptRaw, false);
    break;
  case 23:
    UrAcceptExpect("raw_spare_claimed_p2", UrAcceptSeatOf(kUrAcceptRaw) == 1 &&
                   g_gamepad[1].raw_joystick && UrAcceptSeatOf(0) == 0 &&
                   UrSpareFind(g_ur_accept_id[kUrAcceptRaw]) < 0 &&
                   (g_pad_buttons & 0xfff000u) == 0);
    UrAcceptDetach(kUrAcceptRaw);
    break;
  case 24:
    UrAcceptExpect("raw_seat_released_on_remove", g_gamepad[1].joystick_id == -1 &&
                   UrAcceptSeatOf(0) == 0 && (g_pad_buttons & 0xfff000u) == 0);
    for (int i = 0; i < kUrAcceptPads; i++) UrAcceptDetach(i);
    break;
  case 25:
    /* B is plugged in while another loop owns the queue. */
    UrAcceptAttach(1, 0x5502, -1);
    UrAcceptDrainDeviceEvents();
    break;
  case 26:
    UrAcceptExpect("drained_add_unseen", UrAcceptSeatOf(1) == -1 &&
                   g_gamepad[0].joystick_id == -1 && g_gamepad[1].joystick_id == -1);
    UrSeatReconcile("acceptance");
    break;
  case 27:
    g_ur_accept_b_seat = UrAcceptSeatOf(1);
    UrAcceptExpect("reconcile_seats_new_pad", g_ur_accept_b_seat >= 0);
    g_ur_accept_spare_id = g_ur_accept_id[1];  /* remember B's instance */
    UrAcceptDetach(1);  /* and unplugged unseen */
    UrAcceptDrainDeviceEvents();
    break;
  case 28:
    UrAcceptExpect("drained_removal_unseen", g_ur_accept_b_seat >= 0 &&
                   g_gamepad[g_ur_accept_b_seat].joystick_id == g_ur_accept_spare_id);
    UrSeatReconcile("acceptance");
    break;
  case 29:
    UrAcceptExpect("reconcile_releases_gone_pad", g_ur_accept_b_seat >= 0 &&
                   g_gamepad[g_ur_accept_b_seat].joystick_id == -1 && g_pad_buttons == 0);
    UrAcceptAttach(1, 0x5502, 1 - g_ur_accept_b_seat);  /* B returns with the other index */
    break;
  case 30:
    UrAcceptExpect("returning_pad_reclaims_after_reconcile",
                   g_ur_accept_b_seat >= 0 && UrAcceptSeatOf(1) == g_ur_accept_b_seat);
    for (int i = 0; i < kUrAcceptPads; i++) UrAcceptDetach(i);
    break;
  case 31: {
    /* Both players on Gamepad (what a launcher commit writes), no pads. */
    g_ur_accept_src[0] = g_config.player_src[0];
    g_ur_accept_src[1] = g_config.player_src[1];
    g_config.player_src[0] = g_config.player_src[1] = 2;
    const uint32 in = UrAcceptKeyboardWord();
    UrAcceptExpect("keyboard_fallback_drives_p1",
                   g_gamepad[0].joystick_id == -1 && (in & 0xfffu) != 0 &&
                   ((in >> 12) & 0xfffu) == 0 && (GetActiveControllers() & (1u << 30)));
    UrAcceptAttach(0, 0x5501, 0);
    break;
  }
  case 32:
    UrAcceptExpect("seated_pad_keeps_p1_exclusive",
                   UrAcceptSeatOf(0) == 0 && (UrAcceptKeyboardWord() & 0xffffffu) == 0);
    g_config.player_src[1] = 1;  /* P2 moves to the keyboard */
    UrAcceptDetach(0);
    break;
  case 33: {
    const uint32 in = UrAcceptKeyboardWord();
    UrAcceptExpect("no_fallback_when_p2_on_keyboard", g_gamepad[0].joystick_id == -1 &&
                   (in & 0xfffu) == 0 && ((in >> 12) & 0xfffu) != 0);
    g_config.player_src[0] = g_ur_accept_src[0];
    g_config.player_src[1] = g_ur_accept_src[1];
    PollKeyboardControls(snesrecomp_sdl_get_keyboard_state());
    /* Keyboard + one pad: A is seated P1 and holds a button. */
    UrAcceptAttach(0, 0x5501, 0);
    break;
  }
  case 34:
    UrAcceptButton(0, true);
    break;
  case 35:
    g_ur_accept_held = g_pad_buttons & 0xfffu;  /* A's held P1 bits */
    UrAcceptExpect("seat_move_refused_when_target_bad",
                   UrAcceptSeatOf(0) == 0 && !snesrecomp_desktop_product_seat_move(0, 0) &&
                   !snesrecomp_desktop_product_seat_move(1, 0) &&
                   !snesrecomp_desktop_product_seat_move(0, 2));
    UrAcceptExpect("seat_move_p1_pad_to_p2",
                   g_ur_accept_held != 0 && snesrecomp_desktop_product_seat_move(0, 1) &&
                   UrAcceptSeatOf(0) == 1 && g_gamepad[0].joystick_id == -1 &&
                   (g_pad_buttons & 0xfffu) == 0);
    UrAcceptButton(0, false);
    break;
  case 36:
    UrAcceptButton(0, true);  /* the moved pad now drives P2 */
    break;
  case 37:
    UrAcceptExpect("moved_pad_drives_p2", (g_pad_buttons & 0xfffu) == 0 &&
                   (g_pad_buttons & 0xfff000u) != 0);
    UrAcceptExpect("moved_pad_shows_p2", UrAcceptIndexOf(0) == 1);
    UrAcceptButton(0, false);
    break;
  case 38:
    UrAcceptDetach(0);
    break;
  case 39:
    UrAcceptAttach(0, 0x5501, 0);  /* replug, SDL player index 0 again */
    break;
  case 40:
    UrAcceptExpect("moved_pad_reclaims_p2_after_replug", UrAcceptSeatOf(0) == 1 &&
                   g_gamepad[0].joystick_id == -1);
    for (int i = 0; i < kUrAcceptPads; i++) UrAcceptDetach(i);
    break;
  case 41:
    /* A fresh session: nobody is away from a seat. A lone pad arrives
     * holding player index 1 (an XInput pad Windows left in slot 2). */
    UrSeatReset();
    UrAcceptAttach(4, 0x5505, 1);
    break;
  case 42:
    UrAcceptExpect("lone_pad_with_p2_index_takes_p1", UrAcceptSeatOf(4) == 0 &&
                   g_gamepad[1].joystick_id == -1 && UrAcceptIndexOf(4) == 0);
    for (int i = 0; i < kUrAcceptPads; i++) UrAcceptDetach(i);
    break;
  case 43:
    /* Two pads present together, found in the opposite order to their
     * player indices: A (index 1) then B (index 0), unseen until a reconcile
     * enumerates both, as at start-up. */
    UrSeatReset();
    UrAcceptAttach(0, 0x5501, 1);
    UrAcceptAttach(1, 0x5502, 0);
    UrAcceptDrainDeviceEvents();
    break;
  case 44:
    UrSeatReconcile("acceptance");
    break;
  case 45:
    UrAcceptExpect("enumeration_follows_player_index", UrAcceptSeatOf(1) == 0 &&
                   UrAcceptSeatOf(0) == 1);
    for (int i = 0; i < kUrAcceptPads; i++) UrAcceptDetach(i);
    break;
  case 46:
    /* An unmapped stick holding index 0 and a gamepad holding index 1 are
     * found together: the gamepad is P1, the stick only gets what is left. */
    UrSeatReset();
    UrAcceptAttach(kUrAcceptRaw, 0x5506, 0);
    UrAcceptAttach(0, 0x5501, 1);
    UrAcceptDrainDeviceEvents();
    break;
  case 47:
    UrSeatReconcile("acceptance");
    break;
  case 48:
    UrAcceptExpect("gamepad_seated_before_raw_stick", UrAcceptSeatOf(0) == 0 &&
                   UrAcceptSeatOf(kUrAcceptRaw) == 1);
    for (int i = 0; i < kUrAcceptPads; i++) UrAcceptDetach(i);
    break;
  default: {
    printf("UR_CONTROLLER_LIFECYCLE_ACCEPTANCE result=%s\n", g_ur_accept_failed ? "fail" : "pass");
    fflush(stdout);
    g_ur_accept_step = -1;
    const char *v = HostGetenv("UR_CONTROLLER_LIFECYCLE_ACCEPTANCE");
    if (v && (strcmp(v, "exit") == 0 || strcmp(v, "launcher") == 0 ||
              strcmp(v, "focus") == 0)) {
      SDL_Event quit;
      memset(&quit, 0, sizeof(quit));
      quit.type = SDL_QUIT;
      SDL_PushEvent(&quit);
    }
    break;
  }
  }
  fflush(stdout);
}
#else
static void UrControllerLifecycleAcceptanceTick(void) {}
#endif
'''


def once(source: str, needle: str, replacement: str) -> str:
    if source.count(needle) != 1:
        raise ValueError(f"Pinned native Baldosa host diverged: {needle[:100]!r}")
    return source.replace(needle, replacement, 1)


def patch_host_main(source: str, policy: Path) -> str:
    if MARK in source:
        return source
    for needle in (SELECTION, RAW_SELECTION, PAD_REMOVED, PAD_BUTTON,
                   RAW_REMOVED, REASSIGN, HELPERS_ANCHOR, TICK_ANCHOR,
                   PAD_FOUND, RAW_UNSEATED, RAW_BUTTON, LAUNCHER_RETURN,
                   KEYBOARD_P1, ACTIVE_P1, ENUMERATE, BACKGROUND):
        if source.count(needle) != 1:
            raise ValueError(f"Pinned native Baldosa host diverged: {needle[:100]!r}")
    source = once(source, HELPERS_ANCHOR, helpers(policy) + HELPERS_ANCHOR)
    source = once(source, SELECTION, SELECTION_NEW)
    source = once(source, RAW_SELECTION, RAW_SELECTION_NEW)
    source = once(source, PAD_REMOVED, PAD_REMOVED_NEW)
    source = once(source, PAD_BUTTON, PAD_BUTTON_NEW)
    source = once(source, RAW_REMOVED, RAW_REMOVED_NEW)
    source = once(source, REASSIGN, REASSIGN_NEW)
    source = once(source, PAD_FOUND, PAD_FOUND_NEW)
    source = once(source, RAW_UNSEATED, RAW_UNSEATED_NEW)
    source = once(source, RAW_BUTTON, RAW_BUTTON_NEW)
    source = once(source, LAUNCHER_RETURN, LAUNCHER_RETURN_NEW)
    source = once(source, KEYBOARD_P1, KEYBOARD_P1_NEW)
    source = once(source, ACTIVE_P1, ACTIVE_P1_NEW)
    source = once(source, ENUMERATE, ENUMERATE_NEW)
    source = once(source, BACKGROUND, BACKGROUND_NEW)
    return once(source, TICK_ANCHOR, TICK_NEW)


def plan(game: Path, root: Path):
    policy = (root / POLICY).resolve()
    if not policy.is_file():
        raise ValueError(f"Missing project-owned seat policy: {policy}")
    path = game / "snesrecomp/runner/src/desktop/host_main.c"
    before = path.read_text(encoding="utf-8")
    return [(path, before, patch_host_main(before, policy))]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--ur-root", type=Path,
                        default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    for path, before, after in plan(args.game.resolve(), args.ur_root.resolve()):
        if before != after:
            path.write_text(after, encoding="utf-8")
        print(f"{path}: {'already staged' if before == after else 'staged'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
