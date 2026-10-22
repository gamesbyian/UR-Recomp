#include "controller_seat_assignment_policy.h"

#include <cassert>
#include <cstdint>
#include <cstring>

namespace {

constexpr std::uint64_t kPadA = 0xa1u;
constexpr std::uint64_t kPadB = 0xb2u;
constexpr std::uint64_t kPadC = 0xc3u;

struct Table {
    UrControllerSeatSlot seats[UR_CONTROLLER_SEAT_COUNT];
    Table() {
        std::memset(seats, 0, sizeof(seats));
        seats[0].enabled = seats[1].enabled = 1;
    }
    int connect(std::uint64_t key, int player_index, int forced = -1) {
        const UrControllerSeatChoice choice =
            ur_controller_seat_choose(seats, key, player_index, forced);
        if (choice.seat >= 0) ur_controller_seat_taken(seats, choice.seat, key);
        return choice.seat;
    }
};

void first_two_pads_follow_player_index_or_first_free() {
    Table t;
    assert(t.connect(kPadA, 0) == 0);
    assert(t.connect(kPadB, 1) == 1);
    Table u;
    // No usable player index: P1 then P2.
    assert(u.connect(kPadA, -1) == 0);
    assert(u.connect(kPadB, 7) == 1);
}

void an_occupied_seat_is_never_stolen() {
    // The pinned host's defect: SDL hands a reconnecting XInput pad player
    // index 0 while another pad already owns seat 0.
    Table t;
    assert(t.connect(kPadA, 0) == 0);
    assert(t.connect(kPadB, 1) == 1);
    const UrControllerSeatChoice third =
        ur_controller_seat_choose(t.seats, kPadC, 0, -1);
    assert(third.seat == -1);
    assert(third.reason == UR_CONTROLLER_SEAT_NONE);
    // Seats unchanged.
    assert(t.seats[0].occupied && t.seats[1].occupied);
}

void a_reconnecting_pad_reclaims_its_own_seat() {
    Table t;
    assert(t.connect(kPadA, 0) == 0);
    assert(t.connect(kPadB, 1) == 1);
    ur_controller_seat_vacated(t.seats, 0, kPadA);
    assert(!t.seats[0].occupied);
    assert(t.seats[0].absent_owner_key == kPadA);
    // SDL may give the returning pad a different player index.
    const UrControllerSeatChoice back =
        ur_controller_seat_choose(t.seats, kPadA, 1, -1);
    assert(back.seat == 0);
    assert(back.reason == UR_CONTROLLER_SEAT_RECLAIMED);
    ur_controller_seat_taken(t.seats, back.seat, kPadA);
    assert(t.seats[0].absent_owner_key == 0);
}

void p2_leaving_does_not_swap_players_when_p2_returns() {
    Table t;
    assert(t.connect(kPadA, 0) == 0);
    assert(t.connect(kPadB, 1) == 1);
    ur_controller_seat_vacated(t.seats, 1, kPadB);
    ur_controller_seat_vacated(t.seats, 0, kPadA);
    // B returns first and is assigned player index 0 by SDL: it must still
    // go back to P2, not take P1 from the absent A.
    assert(t.connect(kPadB, 0) == 1);
    assert(t.connect(kPadA, 0) == 0);
}

void a_new_pad_prefers_a_seat_nobody_is_waiting_for() {
    Table t;
    assert(t.connect(kPadA, 0) == 0);
    ur_controller_seat_vacated(t.seats, 0, kPadA);
    // C has player index 0, but A is away from seat 0 and seat 1 is free.
    const UrControllerSeatChoice c =
        ur_controller_seat_choose(t.seats, kPadC, 0, -1);
    assert(c.seat == 1);
    assert(c.reason == UR_CONTROLLER_SEAT_FIRST_FREE);
    ur_controller_seat_taken(t.seats, c.seat, kPadC);
    // A still returns to P1.
    assert(t.connect(kPadA, 1) == 0);
}

void a_replacement_pad_can_take_an_absent_players_seat() {
    Table t;
    assert(t.connect(kPadA, 0) == 0);
    assert(t.connect(kPadB, 1) == 1);
    ur_controller_seat_vacated(t.seats, 0, kPadA);
    // A's battery died; C is the only way P1 can keep playing.
    const UrControllerSeatChoice c =
        ur_controller_seat_choose(t.seats, kPadC, 2, -1);
    assert(c.seat == 0);
    assert(c.reason == UR_CONTROLLER_SEAT_ABSENT_OWNER_SEAT);
    ur_controller_seat_taken(t.seats, 0, kPadC);
    assert(t.seats[0].absent_owner_key == 0);
    // When A comes back there is no seat left for it.
    assert(ur_controller_seat_choose(t.seats, kPadA, 0, -1).seat == -1);
}

void a_device_seated_elsewhere_is_no_longer_absent() {
    Table t;
    assert(t.connect(kPadA, 0) == 0);
    ur_controller_seat_vacated(t.seats, 0, kPadA);
    // A comes back while seat 0 is disabled, so it lands in seat 1 ...
    t.seats[0].enabled = 0;
    assert(t.connect(kPadA, 0) == 1);
    t.seats[0].enabled = 1;
    // ... and seat 0 is not held for a device that is present.
    assert(t.seats[0].absent_owner_key == 0);
    assert(t.connect(kPadC, -1) == 0);
}

void disabled_seats_are_never_used() {
    Table t;
    t.seats[1].enabled = 0;
    assert(t.connect(kPadA, 1) == 0);
    assert(t.connect(kPadB, 1) == -1);
}

void forced_seat_only_while_vacant() {
    Table t;
    assert(t.connect(kPadA, 1, 0) == 0);
    const UrControllerSeatChoice again =
        ur_controller_seat_choose(t.seats, kPadB, -1, 0);
    assert(again.seat == -1);
    assert(again.reason == UR_CONTROLLER_SEAT_NONE);
}

void unknown_device_key_never_matches_an_absent_owner() {
    Table t;
    assert(t.connect(0, 0) == 0);
    ur_controller_seat_vacated(t.seats, 0, 0);
    assert(t.seats[0].absent_owner_key == 0);
    assert(t.connect(kPadB, 0) == 0);
}

void device_key_is_stable_nonzero_and_serial_sensitive() {
    std::uint8_t guid[16] = {0x03, 0x00, 0x00, 0x00, 0x5e, 0x04, 0x00, 0x00,
                             0x8e, 0x02, 0x00, 0x00, 0x14, 0x01, 0x00, 0x00};
    const std::uint64_t none = ur_controller_device_key(guid, nullptr);
    assert(none != 0);
    assert(none == ur_controller_device_key(guid, nullptr));
    assert(ur_controller_device_key(guid, "") != none);
    assert(ur_controller_device_key(guid, "1234") !=
           ur_controller_device_key(guid, "1235"));
    std::uint8_t other[16];
    std::memcpy(other, guid, sizeof(other));
    other[8] ^= 1;
    assert(ur_controller_device_key(other, nullptr) != none);
}

void reason_names_are_stable_log_tokens() {
    assert(std::strcmp(ur_controller_seat_reason_name(
        UR_CONTROLLER_SEAT_RECLAIMED), "reclaimed") == 0);
    assert(std::strcmp(ur_controller_seat_reason_name(
        UR_CONTROLLER_SEAT_ABSENT_OWNER_SEAT), "absent_owner_seat") == 0);
    assert(std::strcmp(ur_controller_seat_reason_name(
        static_cast<UrControllerSeatReason>(99)), "none") == 0);
}

}  // namespace

int main() {
    first_two_pads_follow_player_index_or_first_free();
    an_occupied_seat_is_never_stolen();
    a_reconnecting_pad_reclaims_its_own_seat();
    p2_leaving_does_not_swap_players_when_p2_returns();
    a_new_pad_prefers_a_seat_nobody_is_waiting_for();
    a_replacement_pad_can_take_an_absent_players_seat();
    a_device_seated_elsewhere_is_no_longer_absent();
    disabled_seats_are_never_used();
    forced_seat_only_while_vacant();
    unknown_device_key_never_matches_an_absent_owner();
    device_key_is_stable_nonzero_and_serial_sensitive();
    reason_names_are_stable_log_tokens();
    return 0;
}
