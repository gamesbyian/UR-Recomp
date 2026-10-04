#pragma once

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

struct SnesDesktopHostFrameStats;

void ur_uniracers_modern_after_run_frame(
    const struct SnesDesktopHostFrameStats* stats);
int ur_uniracers_modern_system_key_down(int key, int mod, int repeat);
int ur_uniracers_modern_system_gamepad_button(int button, int pressed);
void ur_uniracers_modern_system_overlay(
    uint8_t* dst,
    size_t pitch,
    int width,
    int height);
/* 0 keeps presentation locked to authoritative guest cadence; positive
 * values request only host-side re-presentation of captured frames. */
double ur_uniracers_modern_presentation_hz(double display_refresh);

/* Current evidence-backed Widescreen scene decision. This reports host
 * presentation policy only; it never mutates guest camera/simulation state. */
int ur_uniracers_modern_widescreen_world_expand(void);

#ifdef __cplusplus
}
#endif
