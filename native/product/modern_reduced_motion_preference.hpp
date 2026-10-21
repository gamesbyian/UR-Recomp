#pragma once

// Reduced-motion preference resolution for Modern presentation. The player's
// explicit UR_REDUCED_MOTION override ("1" on, "0" off) always wins; when it
// is unset or unrecognised the operating-system "show animations" setting
// decides, so a player who disabled client-area animations in Windows gets
// reduced motion without discovering an environment variable. Presentation
// policy only: it never reads or writes guest state, and a failed OS query
// leaves motion at its previous (full) behaviour rather than guessing.

#include <cstring>

#if defined(_WIN32)
#  ifndef WIN32_LEAN_AND_MEAN
#    define WIN32_LEAN_AND_MEAN
#  endif
#  include <windows.h>
#endif

namespace ur::product {

// os_animations: 1 animations enabled, 0 disabled, -1 unknown/unavailable.
constexpr bool modern_reduced_motion_resolve(const char* env_value,
                                             int os_animations) noexcept {
    if (env_value) {
        if (env_value[0] == '1' && env_value[1] == '\0') return true;
        if (env_value[0] == '0' && env_value[1] == '\0') return false;
    }
    return os_animations == 0;
}

inline int modern_os_animations_enabled() noexcept {
#if defined(_WIN32) && defined(SPI_GETCLIENTAREAANIMATION)
    BOOL enabled = TRUE;
    if (SystemParametersInfoW(SPI_GETCLIENTAREAANIMATION, 0, &enabled, 0))
        return enabled ? 1 : 0;
#endif
    return -1;
}

inline bool modern_reduced_motion_preference(const char* env_value) noexcept {
    const bool explicit_override =
        env_value && (env_value[0] == '0' || env_value[0] == '1') &&
        env_value[1] == '\0';
    // The OS is only consulted when the player gave no explicit override.
    return modern_reduced_motion_resolve(
        env_value, explicit_override ? -1 : modern_os_animations_enabled());
}

}  // namespace ur::product
