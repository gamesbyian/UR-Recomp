#pragma once

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

struct SnesDesktopHostFrameStats;

void ur_uniracers_product_after_run_frame(
    const struct SnesDesktopHostFrameStats* stats);
int ur_uniracers_product_system_key_down(int key, int mod, int repeat);
int ur_uniracers_product_system_gamepad_button(int button, int pressed);
void ur_uniracers_product_system_overlay(
    uint8_t* dst,
    size_t pitch,
    int width,
    int height);

#ifdef __cplusplus
}
#endif
