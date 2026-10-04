#pragma once

#include <stdbool.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct UrModernSession UrModernSession;

typedef size_t (*UrSaveSnapshotFn)(void* data, size_t capacity);
typedef bool (*UrLoadSnapshotFn)(const void* data, size_t size);
typedef void (*UrSetPausedFn)(int paused);
typedef int (*UrIsPausedFn)(void);
typedef void (*UrSetRewindAudioTimingLockFn)(int active);
typedef void (*UrReconcileAfterRestartFn)(void);
typedef bool (*UrExitToFrontendFn)(void);

typedef enum UrModernSessionKey {
    UR_MODERN_SESSION_KEY_ESCAPE = 0,
    UR_MODERN_SESSION_KEY_ACCEPT = 1,
    UR_MODERN_SESSION_KEY_RESTART = 2,
} UrModernSessionKey;

typedef enum UrModernSessionResult {
    UR_MODERN_SESSION_APPLIED = 0,
    UR_MODERN_SESSION_REJECTED_BY_POLICY = 1,
    UR_MODERN_SESSION_NO_OP = 2,
    UR_MODERN_SESSION_BUSY = 3,
    UR_MODERN_SESSION_REJECTED_BY_RUNTIME = 4,
    UR_MODERN_SESSION_MISSING_HOOK = 5,
    UR_MODERN_SESSION_UNSUPPORTED = 6,
} UrModernSessionResult;

UrModernSession* ur_modern_session_create(
    int modern_mode,
    size_t snapshot_capacity,
    UrSaveSnapshotFn save_snapshot,
    UrLoadSnapshotFn load_snapshot,
    UrSetPausedFn set_paused,
    UrIsPausedFn is_paused,
    UrSetRewindAudioTimingLockFn set_rewind_audio_timing_lock,
    UrReconcileAfterRestartFn reconcile_after_restart,
    UrExitToFrontendFn exit_to_frontend);

void ur_modern_session_destroy(UrModernSession* session);

/* Load a restart snapshot while keeping the current persistent byte domain
 * (for Uniracers, cartridge SRAM) byte-identical across the restore. The
 * snapshot loader may transiently replace those bytes; this helper restores
 * the exact pre-call contents before returning, including on load failure. */
bool ur_modern_session_load_preserving_persistent_bytes(
    UrLoadSnapshotFn load_snapshot,
    const void* snapshot,
    size_t snapshot_size,
    void* persistent_bytes,
    size_t persistent_size);

void ur_modern_session_observe_race_active(
    UrModernSession* session,
    int active);

void ur_modern_session_retire_race_attempt(UrModernSession* session);

int ur_modern_session_restart_available(const UrModernSession* session);
int ur_modern_session_is_paused(const UrModernSession* session);

UrModernSessionResult ur_modern_session_pause(UrModernSession* session);
UrModernSessionResult ur_modern_session_resume(UrModernSession* session);
UrModernSessionResult ur_modern_session_restart_race(UrModernSession* session);
UrModernSessionResult ur_modern_session_exit_to_frontend(UrModernSession* session);

/* Minimal host-facing key policy. The platform host maps its own key codes to
 * these semantic keys; this layer remains SDL/platform independent.
 *
 * Escape toggles host pause. Accept resumes only when paused. Restart issues
 * Restart Race only when the validated anchor is available; it preserves the
 * current host pause state.
 */
UrModernSessionResult ur_modern_session_handle_key(
    UrModernSession* session,
    UrModernSessionKey key);

#ifdef __cplusplus
}
#endif
