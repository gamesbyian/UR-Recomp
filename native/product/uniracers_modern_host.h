#pragma once

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

struct SnesDesktopHostFrameStats;
struct SnesDisplayViewport;

void ur_uniracers_modern_after_config(void);
void ur_uniracers_modern_after_run_frame(
    const struct SnesDesktopHostFrameStats* stats);
int ur_uniracers_modern_system_key_down(int key, int mod, int repeat);
int ur_uniracers_modern_system_gamepad_button(int button, int pressed);
int ur_uniracers_modern_system_gamepad_source_button(
    int player_index, uint64_t source_id, int button, int pressed);
void ur_uniracers_modern_system_gamepad_source_connection(
    int player_index, uint64_t source_id, int connected);
/* Read-only Modern Local Tournament projection. Return 0 if unavailable
 * or Authentic. Does not create fixtures, infer Records matches or write SRAM.
 * Profile IDs are bounded storage identities; display names remain catalog-
 * owned. A fixture outcome is 0=unplayed, 1=first entrant, 2=second,
 * 3=draw, already oriented by its authoritative saved seat mapping. */
struct UrModernTournamentOverview {
    uint32_t entrants;
    uint32_t fixtures;
    uint32_t completed_fixtures;
    int complete;
};
struct UrModernTournamentFixtureInfo {
    uint32_t round;
    char first_profile_id[129];
    char second_profile_id[129];
    char course_id[16];
    int outcome;
};
struct UrModernTournamentStandingInfo {
    char profile_id[129];
    uint32_t rank;
    uint32_t played;
    uint32_t wins;
    uint32_t draws;
    uint32_t losses;
    uint32_t points;
};
int ur_uniracers_modern_local_tournament_overview(
    struct UrModernTournamentOverview* out);
int ur_uniracers_modern_local_tournament_fixture(
    size_t index, struct UrModernTournamentFixtureInfo* out);
int ur_uniracers_modern_local_tournament_standing(
    size_t sorted_index, struct UrModernTournamentStandingInfo* out);

int ur_uniracers_modern_controls_active(void);
/* Nonzero while a paused Modern subview (Options, Controls, Run Data or Quit
 * confirmation) owns the pause surface. */
int ur_uniracers_modern_subview_active(void);
/* Settled Modern main menu with no host modal/route: frontend Records may
 * open. While open, the Modern host owns human input and holds guest frames. */
int ur_uniracers_modern_frontend_records_admissible(void);
void ur_uniracers_modern_set_frontend_records_open(int open);
int ur_uniracers_modern_settled_main_menu(void);
int ur_uniracers_modern_system_gamepad_control(int control, int pressed);
uint32_t ur_uniracers_modern_filter_player_input(uint32_t inputs);
/* Final mapped P2 HUMAN word (unshifted). Distinct from input-file/debug masks. */
uint32_t ur_uniracers_modern_filter_second_player_input(uint32_t inputs);
void ur_uniracers_modern_system_overlay(
    uint8_t* dst,
    size_t pitch,
    int width,
    int height);
/* 0 keeps presentation locked to authoritative guest cadence; positive
 * values request only host-side re-presentation of captured frames. */
double ur_uniracers_modern_presentation_hz(double display_refresh);

/* Widescreen presentation callbacks. They are inert unless the accepted
 * authentic-16x9 selector is active; scene ownership stays title-side. */
int ur_uniracers_modern_native_widescreen_enabled(void);
void ur_uniracers_modern_prepare_frame(
    int drawable_width,
    int drawable_height,
    int* frame_width,
    int* frame_height);
void ur_uniracers_modern_begin_sim_frame(unsigned frame_number);
int ur_uniracers_modern_presentation_scale(void);
int ur_uniracers_modern_draw_frame(
    uint8_t* dst, size_t pitch, const uint8_t* field,
    int frame_width, int frame_height, double alpha);
void ur_uniracers_modern_compute_viewport(
    int frame_width,
    int frame_height,
    int drawable_width,
    int drawable_height,
    struct SnesDisplayViewport* viewport);

#ifdef __cplusplus
}
#endif
