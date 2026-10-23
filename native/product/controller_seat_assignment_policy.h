#pragma once

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Which framework controller seat (P1 = 0, P2 = 1) a newly opened physical
 * gamepad takes.
 *
 * The pinned SNESRecomp desktop host seats pads itself. Its original rule
 * let a pad's SDL player index claim that seat even while another pad
 * occupied it. SDL3 reassigns player indices on reconnect (an XInput pad
 * returns to its XInput slot and bumps whichever pad held that index), so
 * re-plugging one controller during a two-player session could overwrite
 * the other player's seat. The orphaned pad's button releases then no
 * longer reached the shared pad word, leaving its held bits stuck.
 *
 * This policy is the replacement rule. It never steals an occupied seat,
 * lets a reconnecting device reclaim the seat it vacated, and keeps an
 * absent player's seat for them while another seat is free. It has no SDL
 * types, owns no state and never writes guest input; the host keeps the
 * seat table and feeds it here. Header-only C so the C host and the C++
 * product tests share one implementation. */

#define UR_CONTROLLER_SEAT_COUNT 2

typedef struct UrControllerSeatSlot {
    /* [General] EnableGamepadN for this seat. */
    int enabled;
    /* A pad currently owns this seat. */
    int occupied;
    /* While the seat is vacant: stable identity of the device that last
     * owned it, or 0. Cleared once the seat is taken again. */
    uint64_t absent_owner_key;
} UrControllerSeatSlot;

typedef enum UrControllerSeatReason {
    UR_CONTROLLER_SEAT_NONE = 0,
    /* The forced seat (the framework self-test pad) was vacant. */
    UR_CONTROLLER_SEAT_FORCED = 1,
    /* The device came back to the seat it last owned. */
    UR_CONTROLLER_SEAT_RECLAIMED = 2,
    /* The SDL player index named a vacant, unreserved seat. */
    UR_CONTROLLER_SEAT_PLAYER_INDEX = 3,
    /* First vacant seat nobody absent is waiting for. */
    UR_CONTROLLER_SEAT_FIRST_FREE = 4,
    /* Every vacant seat is held for an absent owner; take the first. */
    UR_CONTROLLER_SEAT_ABSENT_OWNER_SEAT = 5,
    /* More than one absent seat has this same unprovable device identity. */
    UR_CONTROLLER_SEAT_AMBIGUOUS_OWNER = 6,
} UrControllerSeatReason;

typedef struct UrControllerSeatChoice {
    int seat; /* -1: leave the pad unseated */
    UrControllerSeatReason reason;
} UrControllerSeatChoice;

static inline int ur_controller_seat_vacant(
    const UrControllerSeatSlot *seats, int seat) {
    return seat >= 0 && seat < UR_CONTROLLER_SEAT_COUNT &&
           seats[seat].enabled && !seats[seat].occupied;
}

/* device_key: stable identity (see ur_controller_device_key), 0 if unknown.
 * player_index: SDL's player index, any value outside 0..1 is ignored.
 * forced_seat: -1, or a seat the host requires (only taken while vacant). */
static inline UrControllerSeatChoice ur_controller_seat_choose(
    const UrControllerSeatSlot seats[UR_CONTROLLER_SEAT_COUNT],
    uint64_t device_key, int player_index, int forced_seat) {
    UrControllerSeatChoice choice;
    int i;
    choice.seat = -1;
    choice.reason = UR_CONTROLLER_SEAT_NONE;
    if (forced_seat >= 0) {
        if (ur_controller_seat_vacant(seats, forced_seat)) {
            choice.seat = forced_seat;
            choice.reason = UR_CONTROLLER_SEAT_FORCED;
        }
        return choice;
    }
    if (device_key != 0) {
        int matching_owner = -1;
        for (i = 0; i < UR_CONTROLLER_SEAT_COUNT; ++i) {
            /* Include disabled seats: a reservation there still makes the
             * returning hardware identity ambiguous. */
            if (seats[i].absent_owner_key != device_key) continue;
            if (matching_owner != -1) {
                /* Identical GUID-only pads are not independently identifiable.
                 * Never silently call the first return P1, clear both absent
                 * reservations, and swap the original players. A deliberate
                 * host seat reset or explicit forced assignment is required. */
                choice.reason = UR_CONTROLLER_SEAT_AMBIGUOUS_OWNER;
                return choice;
            }
            matching_owner = i;
        }
        if (ur_controller_seat_vacant(seats, matching_owner)) {
            choice.seat = matching_owner;
            choice.reason = UR_CONTROLLER_SEAT_RECLAIMED;
            return choice;
        }
    }
    if (ur_controller_seat_vacant(seats, player_index) &&
        seats[player_index].absent_owner_key == 0) {
        choice.seat = player_index;
        choice.reason = UR_CONTROLLER_SEAT_PLAYER_INDEX;
        return choice;
    }
    for (i = 0; i < UR_CONTROLLER_SEAT_COUNT; ++i) {
        if (ur_controller_seat_vacant(seats, i) &&
            seats[i].absent_owner_key == 0) {
            choice.seat = i;
            choice.reason = UR_CONTROLLER_SEAT_FIRST_FREE;
            return choice;
        }
    }
    /* Only seats held for absent players remain. A replacement pad must
     * still be able to play, so take one rather than leave it dead. */
    for (i = 0; i < UR_CONTROLLER_SEAT_COUNT; ++i) {
        if (ur_controller_seat_vacant(seats, i)) {
            choice.seat = i;
            choice.reason = UR_CONTROLLER_SEAT_ABSENT_OWNER_SEAT;
            return choice;
        }
    }
    return choice;
}

/* Record a seat being taken: it is no longer held for anybody, and the
 * device can no longer be "absent" from any other seat. */
static inline void ur_controller_seat_taken(
    UrControllerSeatSlot seats[UR_CONTROLLER_SEAT_COUNT], int seat,
    uint64_t device_key) {
    int i;
    if (seat < 0 || seat >= UR_CONTROLLER_SEAT_COUNT) return;
    for (i = 0; i < UR_CONTROLLER_SEAT_COUNT; ++i) {
        if (device_key != 0 && seats[i].absent_owner_key == device_key)
            seats[i].absent_owner_key = 0;
    }
    seats[seat].occupied = 1;
    seats[seat].absent_owner_key = 0;
}

/* Record the owner of a seat disconnecting. */
static inline void ur_controller_seat_vacated(
    UrControllerSeatSlot seats[UR_CONTROLLER_SEAT_COUNT], int seat,
    uint64_t device_key) {
    if (seat < 0 || seat >= UR_CONTROLLER_SEAT_COUNT) return;
    seats[seat].occupied = 0;
    seats[seat].absent_owner_key = device_key;
}

/* FNV-1a over the SDL GUID bytes and, when the driver reports one, the
 * serial. Two identical pads without serials share a key; if both are
 * absent, automatic seat reclamation is ambiguous and must be refused.
 * Never returns 0, so 0 can mean "unknown". */
static inline uint64_t ur_controller_device_key(
    const uint8_t guid[16], const char *serial) {
    uint64_t h = 1469598103934665603ull;
    int i;
    for (i = 0; i < 16; ++i) {
        h ^= guid[i];
        h *= 1099511628211ull;
    }
    if (serial) {
        h ^= 0xffu; /* separator: GUID-only and GUID+"" differ from GUID+serial */
        h *= 1099511628211ull;
        for (; *serial; ++serial) {
            h ^= (uint8_t)*serial;
            h *= 1099511628211ull;
        }
    }
    return h ? h : 1;
}

static inline const char *ur_controller_seat_reason_name(
    UrControllerSeatReason reason) {
    switch (reason) {
    case UR_CONTROLLER_SEAT_FORCED: return "forced";
    case UR_CONTROLLER_SEAT_RECLAIMED: return "reclaimed";
    case UR_CONTROLLER_SEAT_PLAYER_INDEX: return "player_index";
    case UR_CONTROLLER_SEAT_FIRST_FREE: return "first_free";
    case UR_CONTROLLER_SEAT_ABSENT_OWNER_SEAT: return "absent_owner_seat";
    case UR_CONTROLLER_SEAT_AMBIGUOUS_OWNER: return "ambiguous_owner";
    case UR_CONTROLLER_SEAT_NONE: break;
    }
    return "none";
}

#ifdef __cplusplus
}
#endif
