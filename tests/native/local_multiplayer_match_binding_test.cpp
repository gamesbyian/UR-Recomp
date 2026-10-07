#include "local_multiplayer_match_binding.hpp"

#include <cassert>

using namespace ur::product;
using namespace ur::title;

namespace {

HostProfileCatalogEntry profile(
    const char* id,
    const char* name,
    std::uint8_t rider) {
    return {id, HostRacerIdentity{name, rider}};
}

OrdinaryTwoPlayerRaceResult result(
    std::uint8_t p1_rider = 2,
    std::uint8_t p2_rider = 7) {
    OrdinaryTwoPlayerRaceResult value;
    value.player1_rider = p1_rider;
    value.player2_rider = p2_rider;
    value.player1_hundredths = 1234;
    value.player2_hundredths = 1300;
    value.outcome = OrdinaryTwoPlayerRaceOutcome::Player1Win;
    return value;
}

}  // namespace

int main() {
    const auto p1 = profile("ian", "MIKE", 2);
    const auto p2 = profile("guest", "CHUCK", 7);

    const auto bound = bind_local_multiplayer_match(result(), p1, p2);
    assert(bound.bound());
    assert(bound.match.has_value());
    assert(bound.match->player1 == p1);
    assert(bound.match->player2 == p2);
    assert(bound.match->result.player1_rider == 2);
    assert(bound.match->result.player2_rider == 7);
    assert(bound.match->result.outcome ==
           OrdinaryTwoPlayerRaceOutcome::Player1Win);

    {
        auto missing = p1;
        missing.profile_id.clear();
        const auto rejected =
            bind_local_multiplayer_match(result(), missing, p2);
        assert(!rejected.bound());
        assert(rejected.status ==
               LocalMultiplayerMatchBindingStatus::MissingProfileIdentity);
    }

    {
        auto duplicate = p2;
        duplicate.profile_id = p1.profile_id;
        const auto rejected =
            bind_local_multiplayer_match(result(), p1, duplicate);
        assert(!rejected.bound());
        assert(rejected.status ==
               LocalMultiplayerMatchBindingStatus::DuplicateProfileIdentity);
    }

    {
        auto invalid = p2;
        invalid.identity.name.clear();
        const auto rejected =
            bind_local_multiplayer_match(result(), p1, invalid);
        assert(!rejected.bound());
        assert(rejected.status ==
               LocalMultiplayerMatchBindingStatus::InvalidRacerIdentity);
    }

    {
        auto wrong = p2;
        wrong.identity.rider_index = 6;
        const auto rejected =
            bind_local_multiplayer_match(result(), p1, wrong);
        assert(!rejected.bound());
        assert(rejected.status ==
               LocalMultiplayerMatchBindingStatus::RiderMismatch);
    }

    {
        const auto context = bind_local_multiplayer_match_context(
            result(), p1, p2, UrUniracersCourseIdentity{1, 45});
        assert(context.bound());
        assert(context.participant_status ==
               LocalMultiplayerMatchBindingStatus::Bound);
        assert(context.context->course_id == "course:45");
        assert(context.context->match.player1 == p1);
        assert(context.context->match.player2 == p2);
    }

    {
        const auto invalid = bind_local_multiplayer_match_context(
            result(), p1, p2, UrUniracersCourseIdentity{0, 12});
        assert(!invalid.bound());
        assert(invalid.status ==
               LocalMultiplayerMatchContextStatus::InvalidCourseIdentity);

        const auto out_of_range = bind_local_multiplayer_match_context(
            result(), p1, p2, UrUniracersCourseIdentity{1, 46});
        assert(!out_of_range.bound());
        assert(out_of_range.status ==
               LocalMultiplayerMatchContextStatus::InvalidCourseIdentity);
    }

    {
        auto wrong = p2;
        wrong.identity.rider_index = 6;
        const auto rejected = bind_local_multiplayer_match_context(
            result(), p1, wrong, UrUniracersCourseIdentity{1, 12});
        assert(!rejected.bound());
        assert(rejected.status ==
               LocalMultiplayerMatchContextStatus::ParticipantBindingRejected);
        assert(rejected.participant_status ==
               LocalMultiplayerMatchBindingStatus::RiderMismatch);
    }

    {
        // Outcome/timing are carried through from the title observer; the
        // identity binder neither recomputes nor ranks them.
        auto draw = result();
        draw.player1_hundredths = 60000;
        draw.player2_hundredths = 60000;
        draw.outcome = OrdinaryTwoPlayerRaceOutcome::Draw;
        const auto carried = bind_local_multiplayer_match(draw, p1, p2);
        assert(carried.bound());
        assert(carried.match->result.outcome ==
               OrdinaryTwoPlayerRaceOutcome::Draw);
        assert(!carried.match->result.player1_finished());
        assert(!carried.match->result.player2_finished());
    }

    return 0;
}
