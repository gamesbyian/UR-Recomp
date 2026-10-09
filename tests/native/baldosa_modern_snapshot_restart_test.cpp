// Native Modern pause acknowledgement + the EXISTING immutable race anchor.
// Fake rollback bytes stand in for actual Baldosa in-memory RtlRollback state;
// original/native execution and SRAM bytes still need the pinned-guest route.
#include "modern_session_c_api.h"

#include <array>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstring>

namespace {
struct Guest {
    std::array<std::uint8_t, 4> machine{{1, 2, 3, 4}};
    std::array<std::uint8_t, 4> sram{{20, 21, 22, 23}};
    bool paused = false;
    bool reject_load = false;
    unsigned saved = 0, loaded = 0, reconciled = 0;
};
Guest* g;
std::size_t save_snapshot(void* dst, std::size_t cap) {
    if (!g || cap < 8) return 0;
    ++g->saved;
    std::memcpy(dst, g->machine.data(), 4);
    std::memcpy(static_cast<std::uint8_t*>(dst) + 4, g->sram.data(), 4);
    return 8;
}
bool raw_load_snapshot(const void* src, std::size_t size) {
    if (!g || size != 8) return false;
    ++g->loaded;
    // Exercise SRAM restoration even after a rejected, partially applied load.
    const auto* bytes = static_cast<const std::uint8_t*>(src);
    std::memcpy(g->sram.data(), bytes + 4, 4);
    if (g->reject_load) return false;
    std::memcpy(g->machine.data(), bytes, 4);
    return true;
}
bool preserving_load(const void* src, std::size_t size) {
    return ur_modern_session_load_preserving_persistent_bytes(
        &raw_load_snapshot, src, size, g->sram.data(), g->sram.size());
}
bool pause(void* context, int wanted) {
    static_cast<Guest*>(context)->paused = wanted != 0;
    return true;
}
void reconcile() { ++g->reconciled; }
} // namespace

int main() {
    Guest guest;
    g = &guest;
    const UrModernNativeSessionHooks hooks{
        &guest, &pause, nullptr, nullptr, nullptr};
    UrModernSession* no_snapshot = ur_modern_session_create_native(1, &hooks);
    assert(no_snapshot);
    ur_modern_session_observe_race_active(no_snapshot, 1);
    assert(!ur_modern_session_restart_available(no_snapshot));
    ur_modern_session_destroy(no_snapshot);

    UrModernSession* modern = ur_modern_session_create_native_with_snapshot(
        1, &hooks, 8, &save_snapshot, &preserving_load, &reconcile);
    assert(modern);
    assert(!ur_modern_session_restart_available(modern));
    ur_modern_session_observe_race_active(modern, 1);
    assert(guest.saved == 1 && ur_modern_session_restart_available(modern));
    guest.machine = {{9, 9, 9, 9}};
    guest.sram = {{70, 71, 72, 73}};
    assert(ur_modern_session_pause(modern) == UR_MODERN_SESSION_APPLIED);
    assert(guest.paused && ur_modern_session_is_paused(modern));

    assert(ur_modern_session_restart_race(modern) == UR_MODERN_SESSION_APPLIED);
    assert((guest.machine == std::array<std::uint8_t, 4>{{1, 2, 3, 4}}));
    assert((guest.sram == std::array<std::uint8_t, 4>{{70, 71, 72, 73}}));
    assert(guest.paused && guest.reconciled == 1 && guest.loaded == 1);

    guest.machine = {{8, 8, 8, 8}};
    guest.sram = {{80, 81, 82, 83}};
    guest.reject_load = true;
    assert(ur_modern_session_restart_race(modern) ==
           UR_MODERN_SESSION_REJECTED_BY_RUNTIME);
    assert((guest.sram == std::array<std::uint8_t, 4>{{80, 81, 82, 83}}));
    assert(guest.paused && guest.reconciled == 1);

    guest.reject_load = false;
    assert(ur_modern_session_restart_race(modern) == UR_MODERN_SESSION_APPLIED);
    assert((guest.machine == std::array<std::uint8_t, 4>{{1, 2, 3, 4}}));
    assert((guest.sram == std::array<std::uint8_t, 4>{{80, 81, 82, 83}}));
    assert(guest.reconciled == 2 && guest.saved == 1);
    assert(ur_modern_session_resume(modern) == UR_MODERN_SESSION_APPLIED);
    assert(!guest.paused);
    ur_modern_session_retire_race_attempt(modern);
    assert(!ur_modern_session_restart_available(modern));
    assert(ur_modern_session_restart_race(modern) ==
           UR_MODERN_SESSION_REJECTED_BY_RUNTIME);
    ur_modern_session_destroy(modern);
    return 0;
}
