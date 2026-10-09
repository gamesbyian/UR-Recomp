#pragma once

#include "modern_session_c_api.h"

namespace ur::product {

// One physical pause control (keyboard Escape or P1 pad Start). Preserve the
// owning press until key-up, including SDL keyboard repeat and rejected guest
// transitions. The Modern session owns policy; this tracks only edge capture.
// A failed native pause must NEVER fall through as guest Start on that frame.
class BaldosaPhysicalPauseInput {
public:
    bool on_button(int pressed, bool guest_racing,
                   UrModernSession* session) noexcept {
        if (!pressed) {
            const bool consumed = held_by_host_;
            held_by_host_ = false;
            return consumed;
        }
        if (held_by_host_) return true;
        if (!session ||
            (!guest_racing && !ur_modern_session_is_paused(session)))
            return false;
        held_by_host_ = true;
        last_result_ = ur_modern_session_handle_key(
            session, UR_MODERN_SESSION_KEY_ESCAPE);
        return true;
    }

    bool holding() const noexcept { return held_by_host_; }
    UrModernSessionResult last_result() const noexcept {
        return last_result_;
    }

private:
    bool held_by_host_ = false;
    UrModernSessionResult last_result_ = UR_MODERN_SESSION_NO_OP;
};

} // namespace ur::product
