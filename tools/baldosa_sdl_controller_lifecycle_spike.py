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
* an unseated, already-open spare pad may take a vacant seat by pressing a
  button; that claiming press is consumed, never delivered to the guest;
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
    "      UrSeatClaim(SNESRECOMP_SDL_EVENT_BUTTON_DEVICE(*event));\n"
    "      return true;\n"
    "    }\n"
    "    if (gi) {\n"
)

RAW_REMOVED = (
    "  case SDL_JOYDEVICEREMOVED:\n"
    "    gi = GetGamepadInfo(event->jdevice.which);\n"
    "    if (gi && gi->raw_joystick) {\n"
)
RAW_REMOVED_NEW = RAW_REMOVED + "      UrSeatRelease(gi);  /* " + MARK + " */\n"

REASSIGN = "  g_pad_buttons = 0;\n  OpenAllGamepads();\n}\n"
REASSIGN_NEW = (
    "  g_pad_buttons = 0;\n"
    "  UrSeatReset();  /* " + MARK + ": the launcher re-seats from scratch */\n"
    "  OpenAllGamepads();\n}\n"
)

HELPERS_ANCHOR = "static bool HandleDeviceEvent(const SDL_Event *event) {\n"

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
        "static void UrSeatClaim(SDL_JoystickID id) {\n"
        "  if (SelftestPadExcludes(id)) return;\n"
        "  SDL_GameController *pad = SDL_GameControllerFromInstanceID(id);\n"
        "  if (!pad) return;\n"
        "  const int seat = UrSeatAssign(SDL_GameControllerGetJoystick(pad),\n"
        "                                SDL_GameControllerGetPlayerIndex(pad), -1, id, pad);\n"
        "  if (seat < 0) return;\n"
        "  GamepadInfo *gi = &g_gamepad[seat];\n"
        "  memset(gi, 0, sizeof(GamepadInfo));\n"
        "  gi->index = (uint8)seat;\n"
        "  gi->joystick_id = id;\n"
        "  printf(\"[Gamepad] UR_CONTROLLER_SEAT claim instance=%u seat=%d\\n\", (unsigned)id, seat);\n"
        "}\n"
        "static void UrSeatReset(void) {\n"
        "  for (int i = 0; i < UR_CONTROLLER_SEAT_COUNT; i++) {\n"
        "    if (g_ur_seat_pad[i]) SDL_GameControllerClose(g_ur_seat_pad[i]);\n"
        "    g_ur_seat_pad[i] = NULL;\n"
        "    g_ur_seat_key[i] = 0;\n"
        "  }\n"
        "  memset(g_ur_seats, 0, sizeof(g_ur_seats));\n"
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
enum { kUrAcceptPads = 4, kUrAcceptSettle = 6 };
static SDL_JoystickID g_ur_accept_id[kUrAcceptPads];
static SDL_Joystick *g_ur_accept_joy[kUrAcceptPads];
static int g_ur_accept_step, g_ur_accept_wait, g_ur_accept_failed, g_ur_accept_on = -1;
static int UrAcceptSeatOf(int pad) {
  if (!g_ur_accept_id[pad]) return -1;
  for (int i = 0; i < 2; i++)
    if (g_gamepad[i].joystick_id == g_ur_accept_id[pad]) return i;
  return -1;
}
static void UrAcceptAttach(int pad, Uint16 product, int player_index) {
  static const char *const kNames[kUrAcceptPads] = {
    "UR lifecycle pad A", "UR lifecycle pad B", "UR lifecycle pad C", "UR lifecycle pad D"};
  SDL_VirtualJoystickDesc desc;
  SDL_INIT_INTERFACE(&desc);
  desc.type = SDL_JOYSTICK_TYPE_GAMEPAD;
  desc.naxes = SDL_GAMEPAD_AXIS_COUNT;
  desc.nbuttons = SDL_GAMEPAD_BUTTON_COUNT;
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
static void UrAcceptExpect(const char *step, bool ok) {
  printf("UR_CONTROLLER_ACCEPT step=%s pass=%d seats=%u,%u pad_buttons=%08x\n", step,
         ok ? 1 : 0, (unsigned)g_gamepad[0].joystick_id, (unsigned)g_gamepad[1].joystick_id,
         (unsigned)g_pad_buttons);
  if (!ok) g_ur_accept_failed = 1;
}
static void UrControllerLifecycleAcceptanceTick(void) {
  if (g_ur_accept_on < 0) {
    const char *v = HostGetenv("UR_CONTROLLER_LIFECYCLE_ACCEPTANCE");
    /* "1" runs the scenario; "exit" also quits when it is done. */
    g_ur_accept_on = v && (atoi(v) || strcmp(v, "exit") == 0) ? 1 : 0;
  }
  if (!g_ur_accept_on || g_ur_accept_step < 0) return;
  if (g_ur_accept_wait > 0) { g_ur_accept_wait--; return; }
  g_ur_accept_wait = kUrAcceptSettle;
  switch (g_ur_accept_step++) {
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
    for (int i = 0; i < kUrAcceptPads; i++) UrAcceptDetach(i);
    break;
  default: {
    printf("UR_CONTROLLER_LIFECYCLE_ACCEPTANCE result=%s\n", g_ur_accept_failed ? "fail" : "pass");
    fflush(stdout);
    g_ur_accept_step = -1;
    const char *v = HostGetenv("UR_CONTROLLER_LIFECYCLE_ACCEPTANCE");
    if (v && strcmp(v, "exit") == 0) {
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
                   RAW_REMOVED, REASSIGN, HELPERS_ANCHOR, TICK_ANCHOR):
        if source.count(needle) != 1:
            raise ValueError(f"Pinned native Baldosa host diverged: {needle[:100]!r}")
    source = once(source, HELPERS_ANCHOR, helpers(policy) + HELPERS_ANCHOR)
    source = once(source, SELECTION, SELECTION_NEW)
    source = once(source, RAW_SELECTION, RAW_SELECTION_NEW)
    source = once(source, PAD_REMOVED, PAD_REMOVED_NEW)
    source = once(source, PAD_BUTTON, PAD_BUTTON_NEW)
    source = once(source, RAW_REMOVED, RAW_REMOVED_NEW)
    source = once(source, REASSIGN, REASSIGN_NEW)
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
