// ROM-free contract for the reduced-motion preference resolver.
#include "native/product/modern_reduced_motion_preference.hpp"

#include <cstdio>
#include <cstdlib>

using namespace ur::product;

#define CHECK(c) do { if (!(c)) { std::fprintf(stderr, "FAIL %s:%d %s\n", \
    __FILE__, __LINE__, #c); std::exit(1); } } while (0)

// Explicit override beats the OS in both directions.
static_assert(modern_reduced_motion_resolve("1", 1));
static_assert(!modern_reduced_motion_resolve("0", 0));
// Unset or unrecognised falls back to the OS setting; unknown stays full motion.
static_assert(modern_reduced_motion_resolve(nullptr, 0));
static_assert(!modern_reduced_motion_resolve(nullptr, 1));
static_assert(!modern_reduced_motion_resolve(nullptr, -1));
static_assert(modern_reduced_motion_resolve("", 0));
static_assert(modern_reduced_motion_resolve("yes", 0));
static_assert(!modern_reduced_motion_resolve("11", 1));
static_assert(!modern_reduced_motion_resolve("10", -1));

int main() {
    // The host-facing entry point honours the same override without
    // consulting the OS, and never throws on any input.
    CHECK(modern_reduced_motion_preference("1"));
    CHECK(!modern_reduced_motion_preference("0"));
    const int os = modern_os_animations_enabled();
    CHECK(os >= -1 && os <= 1);
    CHECK(modern_reduced_motion_preference(nullptr) == (os == 0));
    std::puts("PASS: Modern reduced-motion preference");
    return 0;
}
