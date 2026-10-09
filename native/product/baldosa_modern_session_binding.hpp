#pragma once

#include "baldosa_execution_backend.hpp"
#include "modern_session_c_api.h"

namespace ur::product {

// Glue from the existing Baldosa execution contract to the existing Modern
// session C ABI. No extra menu, input router or persistence authority lives
// here. Native host callbacks must acknowledge real guest transitions.
inline bool baldosa_modern_set_paused(void* context, int paused) noexcept {
    auto& backend = *static_cast<BaldosaExecutionBackend*>(context);
    return (paused ? backend.pause() : backend.resume()) ==
        BaldosaBackendStatus::Applied;
}

inline bool baldosa_modern_restart(void* context) noexcept {
    return static_cast<BaldosaExecutionBackend*>(context)->restart() ==
        BaldosaBackendStatus::Applied;
}

inline bool baldosa_modern_exit(void* context) noexcept {
    return static_cast<BaldosaExecutionBackend*>(context)->exit_to_frontend() ==
        BaldosaBackendStatus::Applied;
}

inline bool baldosa_modern_can_restart(void* context) noexcept {
    const auto phase = static_cast<BaldosaExecutionBackend*>(context)->phase();
    return phase == BaldosaBackendPhase::Running ||
           phase == BaldosaBackendPhase::Paused ||
           phase == BaldosaBackendPhase::Finished;
}

inline UrModernNativeSessionHooks baldosa_modern_session_hooks(
    BaldosaExecutionBackend& backend) noexcept {
    return {&backend, &baldosa_modern_set_paused, &baldosa_modern_restart,
            &baldosa_modern_exit, &baldosa_modern_can_restart};
}

} // namespace ur::product
