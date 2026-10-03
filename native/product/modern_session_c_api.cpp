#include "modern_session_c_api.h"

#include "modern_session_runtime.hpp"

#include <cstring>
#include <new>
#include <vector>

using ur::product::ExecutionMode;
using ur::product::ModernSessionDispatchResult;
using ur::product::ModernSessionRuntime;
using ur::product::RaceRestartAnchor;
using ur::product::RaceRestartLifecycle;
using ur::product::RuntimeDispatchStatus;
using ur::product::SessionCommand;
using ur::product::SessionPhase;
using ur::product::SessionRequestStatus;
using ur::product::SessionRuntimeHooks;
using ur::product::SnapshotRuntimeHooks;

struct UrModernSession {
    RaceRestartAnchor anchor;
    RaceRestartLifecycle lifecycle;
    ModernSessionRuntime runtime;

    UrModernSession(
        ExecutionMode mode,
        std::size_t capacity,
        SnapshotRuntimeHooks snapshot_hooks,
        SessionRuntimeHooks runtime_hooks)
        : anchor(snapshot_hooks, capacity),
          lifecycle(anchor),
          runtime(mode, lifecycle, runtime_hooks) {}
};

namespace {

UrModernSessionResult map_result(const ModernSessionDispatchResult& result) {
    switch (result.request_status) {
    case SessionRequestStatus::RejectedByPolicy:
        return UR_MODERN_SESSION_REJECTED_BY_POLICY;
    case SessionRequestStatus::NoOp:
        return UR_MODERN_SESSION_NO_OP;
    case SessionRequestStatus::Busy:
        return UR_MODERN_SESSION_BUSY;
    case SessionRequestStatus::Accepted:
        break;
    }

    switch (result.dispatch_status) {
    case RuntimeDispatchStatus::Applied:
        return UR_MODERN_SESSION_APPLIED;
    case RuntimeDispatchStatus::MissingHook:
        return UR_MODERN_SESSION_MISSING_HOOK;
    case RuntimeDispatchStatus::RejectedByRuntime:
        return UR_MODERN_SESSION_REJECTED_BY_RUNTIME;
    case RuntimeDispatchStatus::UnsupportedAction:
        return UR_MODERN_SESSION_UNSUPPORTED;
    }

    return UR_MODERN_SESSION_UNSUPPORTED;
}

UrModernSessionResult request(
    UrModernSession* session,
    SessionCommand command) {
    if (!session) {
        return UR_MODERN_SESSION_REJECTED_BY_RUNTIME;
    }
    return map_result(session->runtime.request(command));
}

}  // namespace

extern "C" UrModernSession* ur_modern_session_create(
    int modern_mode,
    size_t snapshot_capacity,
    UrSaveSnapshotFn save_snapshot,
    UrLoadSnapshotFn load_snapshot,
    UrSetPausedFn set_paused,
    UrIsPausedFn is_paused,
    UrSetRewindAudioTimingLockFn set_rewind_audio_timing_lock,
    UrReconcileAfterRestartFn reconcile_after_restart) {
    const ExecutionMode mode =
        modern_mode ? ExecutionMode::Modern : ExecutionMode::Authentic;
    const SnapshotRuntimeHooks snapshot_hooks{
        save_snapshot,
        load_snapshot,
    };
    const SessionRuntimeHooks runtime_hooks{
        set_paused,
        is_paused,
        nullptr,
        set_rewind_audio_timing_lock,
        reconcile_after_restart,
    };

    return new (std::nothrow) UrModernSession(
        mode,
        snapshot_capacity,
        snapshot_hooks,
        runtime_hooks);
}

extern "C" void ur_modern_session_destroy(UrModernSession* session) {
    delete session;
}

extern "C" bool ur_modern_session_load_preserving_persistent_bytes(
    UrLoadSnapshotFn load_snapshot,
    const void* snapshot,
    size_t snapshot_size,
    void* persistent_bytes,
    size_t persistent_size) {
    if (!load_snapshot || (!persistent_bytes && persistent_size != 0)) {
        return false;
    }

    std::vector<unsigned char> preserved(persistent_size);
    if (persistent_size != 0) {
        std::memcpy(preserved.data(), persistent_bytes, persistent_size);
    }

    const bool loaded = load_snapshot(snapshot, snapshot_size);

    if (persistent_size != 0) {
        std::memcpy(persistent_bytes, preserved.data(), persistent_size);
    }
    return loaded;
}

extern "C" void ur_modern_session_observe_race_active(
    UrModernSession* session,
    int active) {
    if (session) {
        session->runtime.observe_race_active(active != 0);
    }
}

extern "C" void ur_modern_session_retire_race_attempt(
    UrModernSession* session) {
    if (session) {
        session->runtime.retire_race_attempt();
    }
}

extern "C" int ur_modern_session_restart_available(
    const UrModernSession* session) {
    return session && session->runtime.restart_available() ? 1 : 0;
}

extern "C" int ur_modern_session_is_paused(
    const UrModernSession* session) {
    return session && session->runtime.phase() == SessionPhase::Paused ? 1 : 0;
}

extern "C" UrModernSessionResult ur_modern_session_pause(
    UrModernSession* session) {
    return request(session, SessionCommand::Pause);
}

extern "C" UrModernSessionResult ur_modern_session_resume(
    UrModernSession* session) {
    return request(session, SessionCommand::Resume);
}

extern "C" UrModernSessionResult ur_modern_session_restart_race(
    UrModernSession* session) {
    return request(session, SessionCommand::RestartRace);
}
