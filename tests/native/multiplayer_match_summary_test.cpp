#include "multiplayer_match_summary.hpp"

#include <cstdio>
#include <cstdlib>
#include <string>
#include <vector>

using namespace ur::product;
using namespace ur::title;

namespace {

void check(bool ok, const char* what) {
    if (!ok) {
        std::fprintf(stderr, "FAIL: %s\n", what);
        std::exit(1);
    }
}

StoredMultiplayerMatch match(
    const char* path,
    const char* p1,
    const char* p1_name,
    const char* p2,
    const char* p2_name,
    OrdinaryTwoPlayerRaceOutcome outcome) {
    StoredMultiplayerMatch stored;
    stored.run_path = path;
    stored.run.provenance.mode = "race-2p";
    stored.match.run_artifact_checksum = "0123456789abcdef";
    stored.match.context.course_id = "course:01";
    stored.match.context.match.player1 = {p1, HostRacerIdentity{p1_name, 0}};
    stored.match.context.match.player2 = {p2, HostRacerIdentity{p2_name, 1}};
    stored.match.context.match.result.player1_rider = 0;
    stored.match.context.match.result.player2_rider = 1;
    stored.match.context.match.result.player1_hundredths = 2876;
    stored.match.context.match.result.player2_hundredths = 3000;
    stored.match.context.match.result.outcome = outcome;
    return stored;
}

constexpr auto kP1 = OrdinaryTwoPlayerRaceOutcome::Player1Win;
constexpr auto kP2 = OrdinaryTwoPlayerRaceOutcome::Player2Win;
constexpr auto kDraw = OrdinaryTwoPlayerRaceOutcome::Draw;

}  // namespace

int main() {
    // No admitted pairs: an explicit empty history, never invented rows.
    {
        const auto summary = summarize_multiplayer_matches({});
        check(summary.matches == 0 && summary.ignored_matches == 0,
              "empty history");
        check(summary.profiles.empty() && summary.head_to_head.empty(),
              "empty history has no rows");
    }

    const std::vector<StoredMultiplayerMatch> matches = {
        match("001.urrun", "sonic", "SONIC", "tails", "TAILS", kP1),
        // Seats swap: tails is P1 here and wins.
        match("002.urrun", "tails", "TAILS", "sonic", "SONIC", kP1),
        match("003.urrun", "sonic", "SONIC", "tails", "TAILS", kDraw),
        // Windows-equivalent spelling of one profile must not split history;
        // the newest spelling/name is presented.
        match("004.urrun", "SONIC", "SUPER", "knux", "KNUX", kP2),
        match("005.urrun", "sonic", "SONIC", "tails", "TAILS", kP1),
        // A same-identity pair is never aggregated.
        match("006.urrun", "amy", "AMY", "AMY", "AMY", kP1),
    };
    const auto summary = summarize_multiplayer_matches(matches);
    check(summary.matches == 5, "five admitted matches aggregated");
    check(summary.ignored_matches == 1, "same-identity pair ignored");
    check(summary.profiles.size() == 3, "three distinct profiles");

    // Profile-identity order, not a ranking.
    check(summary.profiles[0].profile_id == "knux", "order: knux");
    check(summary.profiles[1].profile_id == "sonic", "order: sonic");
    check(summary.profiles[2].profile_id == "tails", "order: tails");

    const auto* sonic = find_multiplayer_profile_record(summary, "Sonic");
    check(sonic != nullptr, "case-insensitive profile lookup");
    check(sonic->played == 5, "sonic played 5");
    check(sonic->wins == 2 && sonic->losses == 2 && sonic->draws == 1,
          "sonic 2W 2L 1D");
    check(sonic->racer_name == "SONIC", "latest racer name presented");
    const auto* tails = find_multiplayer_profile_record(summary, "tails");
    check(tails && tails->played == 4 && tails->wins == 1 &&
              tails->losses == 2 && tails->draws == 1,
          "tails 1W 2L 1D");
    const auto* knux = find_multiplayer_profile_record(summary, "knux");
    check(knux && knux->played == 1 && knux->wins == 1, "knux 1W");
    check(find_multiplayer_profile_record(summary, "amy") == nullptr,
          "ignored pair contributes no profile");

    check(summary.head_to_head.size() == 2, "two rivalries");
    const auto& knux_sonic = summary.head_to_head[0];
    check(knux_sonic.played == 1 && knux_sonic.first_wins == 1 &&
              knux_sonic.second_wins == 0,
          "knux vs sonic: knux 1");
    const auto& sonic_tails = summary.head_to_head[1];
    check(sonic_tails.played == 4 && sonic_tails.first_wins == 2 &&
              sonic_tails.second_wins == 1 && sonic_tails.draws == 1,
          "sonic vs tails: 2-1-1");

    // Oriented to each stored match's seats.
    {
        const auto h2h = multiplayer_head_to_head_for_match(summary, matches[0]);
        check(h2h && h2h->played == 4 && h2h->player1_wins == 2 &&
                  h2h->player2_wins == 1 && h2h->draws == 1,
              "match 1 oriented sonic-first");
        check(format_multiplayer_head_to_head(*h2h) == "P1 2  P2 1  DRAW 1",
              "head-to-head text");
    }
    {
        const auto h2h = multiplayer_head_to_head_for_match(summary, matches[1]);
        check(h2h && h2h->player1_wins == 1 && h2h->player2_wins == 2,
              "swapped seats flip orientation");
    }
    check(!multiplayer_head_to_head_for_match(summary, matches[5]),
          "ignored pair has no head-to-head");
    check(!multiplayer_head_to_head_for_match(
              summary,
              match("x.urrun", "rouge", "ROUGE", "shadow", "SHADOW", kP1)),
          "unknown pairing has no head-to-head");

    std::puts("multiplayer_match_summary_test: ok");
    return 0;
}
