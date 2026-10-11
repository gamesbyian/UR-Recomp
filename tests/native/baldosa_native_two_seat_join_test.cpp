#include "baldosa_native_two_seat_join.hpp"

#include <cassert>
#include <cstdio>
#include <string>
#include <vector>

using namespace ur::product;

namespace {
std::vector<HostProfileCatalogEntry> valid() {
    return {{"alpha", {"MIKE", 0}}, {"beta", {"ANDREW", 1}},
            {"gamma", {"MELISSA", 3}}};
}
} // namespace

int main() {
    BaldosaNativeTwoSeatJoin join;
    assert(!join.begin({}, "alpha"));
    assert(!join.open() && !join.ready());
    assert(!join.begin(valid(), "not-present"));
    assert(!join.begin(valid(), "../alpha"));
    assert(join.begin(valid(), "alpha"));
    assert(join.open() && !join.ready());
    assert(join.candidate(0)->profile_id == "alpha");
    assert(join.candidate(1)->profile_id == "beta");
    assert(!join.confirmed(0) && !join.confirmed(1));
    assert(join.confirm(1)); // physical P2 confirms a distinct profile
    assert(join.confirmed(1) && !join.ready());
    assert(join.move(0, 1));
    assert(!join.confirm(0)); // P1 cannot replace selected SRAM mid-session
    assert(join.move(0, -1));
    assert(join.confirm(0));
    assert(join.ready());
    assert(join.participant(0)->profile_id == "alpha");
    assert(join.participant(1)->profile_id == "beta");
    assert(!join.move(2, 1));
    assert(!join.confirm(2));

    // Any cursor change revokes the previous human confirmation; no
    // implicit opponent selected by gamepad seat or cursor highlight.
    assert(join.move(1, 1));
    assert(!join.ready() && !join.confirmed(1));
    assert(join.candidate(1)->profile_id == "gamma");
    assert(join.confirm(1) && join.ready());
    assert(join.move(1, 1)); // gamma -> alpha collides with P1
    assert(!join.confirm(1) && !join.ready());
    assert(join.clear(0));
    assert(!join.ready());
    assert(join.confirm(1));
    assert(join.move(1, 1)); // alpha -> beta
    assert(join.confirm(1));
    assert(join.confirm(0) && join.ready());

    join.cancel();
    assert(!join.open() && !join.ready());
    assert(!join.participant(0) && !join.participant(1));
    assert(!join.confirm(1));
    assert(join.begin(valid(), "ALPHA")); // Windows storage identity
    assert(!join.ready());
    join.cancel();

    auto duplicate = valid();
    duplicate[1].profile_id = "ALPHA";
    assert(!join.begin(duplicate, "alpha"));
    auto invalid = valid();
    invalid[2].profile_id = "../traversal";
    assert(!join.begin(invalid, "alpha"));
    invalid = valid();
    invalid[2].identity.name = "";
    assert(!join.begin(invalid, "alpha"));
    invalid = valid();
    invalid.resize(129, invalid.front());
    assert(!join.begin(invalid, "alpha"));

    std::puts("PASS: native two-seat join requires independent human profile confirmations");
}
