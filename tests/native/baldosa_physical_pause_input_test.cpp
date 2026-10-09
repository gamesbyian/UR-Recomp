// The existing Modern session C ABI adjudicates native physical edges.
// This is a pure host-input policy test; actual SDL/native-guest execution is
// checked by the pinned Baldosa CI route and Windows build.
#include "baldosa_physical_pause_input.hpp"

#include <cassert>

namespace {
struct Guest {
    bool paused = false;
    bool refuse_pause = false;
    bool refuse_resume = false;
    unsigned pauses = 0;
    unsigned resumes = 0;
};
bool set_paused(void* context, int wanted) {
    auto& guest = *static_cast<Guest*>(context);
    if (wanted ? guest.refuse_pause : guest.refuse_resume) return false;
    guest.paused = wanted != 0;
    if (wanted) ++guest.pauses;
    else ++guest.resumes;
    return true;
}
} // namespace

int main() {
    using ur::product::BaldosaPhysicalPauseInput;
    Guest guest;
    const UrModernNativeSessionHooks hooks{
        &guest, &set_paused, nullptr, nullptr, nullptr};
    UrModernSession* session = ur_modern_session_create_native(1, &hooks);
    assert(session);

    BaldosaPhysicalPauseInput keyboard, p1_pad;
    // Menu navigation keeps stock Enter/Start until an actual guest race.
    assert(!keyboard.on_button(1, false, session));
    assert(!keyboard.on_button(0, false, session));
    assert(!p1_pad.on_button(1, false, session));
    assert(!p1_pad.on_button(0, false, session));
    assert(!guest.paused);

    // One rising edge dispatches to the existing Modern pause API.
    assert(keyboard.on_button(1, true, session));
    assert(keyboard.last_result() == UR_MODERN_SESSION_APPLIED);
    assert(keyboard.holding() && guest.paused && guest.pauses == 1);
    // Key repeat may not issue a second toggle and inadvertently resume.
    assert(keyboard.on_button(1, true, session));
    assert(guest.pauses == 1 && guest.resumes == 0 && guest.paused);
    assert(keyboard.on_button(0, true, session));
    assert(!keyboard.on_button(0, true, session));
    assert(!keyboard.holding());

    // P1 physical pad Start invokes the same Modern session, and resumes
    // even when guest frames are frozen (no new race-active observation).
    assert(p1_pad.on_button(1, false, session));
    assert(p1_pad.last_result() == UR_MODERN_SESSION_APPLIED);
    assert(!guest.paused && guest.resumes == 1);
    assert(p1_pad.on_button(0, false, session));

    // A refused native transition leaves the Modern phase unchanged and
    // cannot fall through as a stock Start press.
    guest.refuse_pause = true;
    assert(p1_pad.on_button(1, true, session));
    assert(p1_pad.last_result() == UR_MODERN_SESSION_REJECTED_BY_RUNTIME);
    assert(!guest.paused && !ur_modern_session_is_paused(session));
    assert(p1_pad.on_button(1, true, session));
    assert(guest.pauses == 1);
    assert(p1_pad.on_button(0, true, session));

    guest.refuse_pause = false;
    assert(p1_pad.on_button(1, true, session));
    assert(guest.paused);
    assert(p1_pad.on_button(0, true, session));
    guest.refuse_resume = true;
    assert(keyboard.on_button(1, false, session));
    assert(keyboard.last_result() == UR_MODERN_SESSION_REJECTED_BY_RUNTIME);
    assert(guest.paused && ur_modern_session_is_paused(session));
    assert(keyboard.on_button(0, false, session));
    guest.refuse_resume = false;
    assert(keyboard.on_button(1, false, session));
    assert(!guest.paused);
    assert(keyboard.on_button(0, false, session));
    ur_modern_session_destroy(session);
    return 0;
}
