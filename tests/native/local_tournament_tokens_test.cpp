#include "local_tournament_tokens.hpp"
#include "local_tournament_fixture_launch.hpp"

#include <cstdio>
#include <cstdlib>
#include <set>
#include <string>

using namespace ur::product;

static void check(bool ok, const char* reason) {
    if (!ok) {
        std::fprintf(stderr, "FAIL: %s\n", reason);
        std::exit(1);
    }
}

int main() {
    const auto schedule =
        make_local_round_robin({"alpha", "beta"}, {"course:01"});
    check(bool(schedule), "actual canonical fixture schedule");
    std::set<std::string> tokens;
    for (int i = 0; i < 256; ++i) {
        const auto token = mint_local_tournament_token();
        check(token && local_tournament_valid_instance_token(*token),
              "OS entropy creates canonical lowercase 128-bit token");
        check(tokens.insert(*token).second,
              "repeated OS entropy requests produce distinct identities");
    }
    const auto tournament_id = mint_local_tournament_token();
    const auto attempt_id = mint_local_tournament_token();
    check(tournament_id && attempt_id &&
          *tournament_id != *attempt_id,
          "independent creation and launch tokens");
    LocalTournamentLaunchState state;
    check(local_tournament_arm_fixture(
            state, *schedule, *tournament_id, *attempt_id, 0) ==
            LocalTournamentLaunchStatus::Armed,
          "existing authoritative fixture launch accepts OS-minted IDs");
    check(state.pending &&
          state.pending->tournament_id == *tournament_id &&
          state.pending->attempt_id == *attempt_id,
          "live fixture keeps two separately minted identities");
    std::puts("local_tournament_tokens_test: ok");
    return 0;
}
