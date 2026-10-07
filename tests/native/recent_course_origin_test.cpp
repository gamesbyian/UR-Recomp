#include "recent_course_origin.hpp"

#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <initializer_list>

namespace {

using ur::product::RecentCourseOriginState;
using ur::product::observe_recent_course_origin;
using ur::product::recent_course_origin_admits;

struct Hold {
    std::uint8_t race;
    std::uint8_t menu;
    int frames;
};

RecentCourseOriginState play(RecentCourseOriginState state,
                             std::initializer_list<Hold> holds) {
    for (const Hold& hold : holds) {
        for (int i = 0; i < hold.frames; ++i) {
            state = observe_recent_course_origin(state, hold.race, hold.menu);
        }
    }
    return state;
}

void expect(bool ok, const char* what) {
    if (!ok) {
        std::fprintf(stderr, "FAILED: %s\n", what);
        std::exit(1);
    }
}

}  // namespace

int main() {
    // Boot: blank, title, then main menu. The boot title must not taint a
    // race the player then starts.
    const auto booted = play({}, {{0, 0x00, 247}, {0, 0x84, 195}, {0, 0xD7, 63}});
    expect(recent_course_origin_admits(booted), "boot reaches main menu clean");

    // Native trace of an ordinary 1P race: main menu, rider select, tours,
    // tracks, NOW_PLAYING, course load, race.
    const auto player = play(booted, {
        {0x3C, 0x3C, 70}, {0x3C, 0x6D, 62}, {0, 0xF6, 66}, {0, 0x16, 130},
        {0, 0x00, 135}, {1, 0x00, 2249},
    });
    expect(recent_course_origin_admits(player), "player race is admitted");

    // Post-finish fade shows 0x84 while $0313 is still 1: not a title origin.
    const auto finished = play(player, {{1, 0x84, 36}, {1, 0x16, 4}});
    expect(recent_course_origin_admits(finished), "post-race fade keeps origin");

    // Native trace of the idle attract cycle: main menu, title, course load
    // with per-frame scratch, then the demo race.
    auto demo = play(booted, {{0, 0xD7, 506}, {0, 0x84, 489}, {0, 0x00, 31}});
    // Scratch: single frames that happen to read main menu / NOW_PLAYING.
    for (std::uint8_t scratch : {0xD7, 0x16, 0x1E, 0xD7, 0xCC, 0x3C, 0x84}) {
        demo = observe_recent_course_origin(demo, 0, scratch);
    }
    demo = play(demo, {{0, 0x11, 3}, {0, 0x00, 9}, {1, 0x00, 2189}});
    expect(!recent_course_origin_admits(demo), "attract demo race is rejected");

    // Demo returns through the title to the main menu; the next player race
    // is admitted again.
    const auto after_demo = play(demo, {
        {1, 0x84, 39}, {0, 0xD7, 507}, {0x3C, 0x3C, 70}, {0, 0xF6, 66},
        {0, 0x16, 130}, {1, 0x00, 60},
    });
    expect(recent_course_origin_admits(after_demo), "player race after demo");

    // Start exits the demo through the title to the main menu.
    const auto exited = play(demo, {{0, 0x84, 95}, {0, 0xD7, 37}});
    expect(recent_course_origin_admits(exited), "start-exit clears origin");

    // Seven frames of a stable title are not yet stable enough.
    const auto brief = play(booted, {{0, 0x84, 7}, {1, 0x00, 10}});
    expect(recent_course_origin_admits(brief), "sub-threshold title ignored");

    std::puts("recent_course_origin_test: ok");
    return 0;
}
