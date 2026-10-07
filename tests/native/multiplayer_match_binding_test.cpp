#include "multiplayer_match_binding.hpp"

#include <cassert>
#include <optional>
#include <string>

using namespace ur::product;
using namespace ur::title;

namespace {

OrdinaryTwoPlayerRaceResult result() {
    OrdinaryTwoPlayerRaceResult value;
    value.player1_rider = 0;
    value.player2_rider = 1;
    value.player1_hundredths = 2876;
    value.player2_hundredths = kOrdinaryTwoPlayerNoTimeHundredths;
    value.outcome = OrdinaryTwoPlayerRaceOutcome::Player1Win;
    return value;
}

HostProfileCatalogEntry profile(
    std::string id,
    std::string name,
    std::uint8_t rider) {
    return {std::move(id), {std::move(name), rider}};
}

}  // namespace

int main() {
    const auto p1 = profile("ian", "IAN", 0);
    const auto bound = bind_ordinary_two_player_race_match(
        result(), "course:01", p1, std::nullopt);
    assert(bound);
    assert(bound->course_id == "course:01");
    assert(bound->player1.profile_id);
    assert(*bound->player1.profile_id == "ian");
    assert(bound->player1.racer.name == "IAN");
    assert(bound->player1.racer.rider_index == 0);
    assert(!bound->player2.profile_id);
    assert(bound->player2.racer.rider_index == 1);
    assert(bound->player2.racer.name == "ANDREW");

    const auto p2 = profile("friend", "RIVAL", 1);
    const auto both_profiled = bind_ordinary_two_player_race_match(
        result(), "course:01", p1, p2);
    assert(both_profiled);
    assert(both_profiled->player2.profile_id);
    assert(*both_profiled->player2.profile_id == "friend");
    assert(both_profiled->player2.racer.name == "RIVAL");

    const auto wrong_rider = profile("wrong", "WRONG", 2);
    assert(!bind_ordinary_two_player_race_match(
        result(), "course:01", p1, wrong_rider));

    const auto duplicate = profile("ian", "ALSOIAN", 1);
    assert(!bind_ordinary_two_player_race_match(
        result(), "course:01", p1, duplicate));

    assert(!bind_ordinary_two_player_race_match(
        result(), "", p1, std::nullopt));

    return 0;
}
