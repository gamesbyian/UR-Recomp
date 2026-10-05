#include "modern_tour_entry_policy.hpp"

#include <cassert>

using namespace ur::product;

int main() {
    const ModernTourEntryContext valid{
        ExecutionMode::Modern,
        true,
        true,
        true,
    };

    const auto actions = modern_tour_entry_actions(valid);
    assert(actions.resume_available);
    assert(actions.restart_available);
    assert(actions.restart_requires_confirmation);

    const auto resume = resolve_modern_tour_entry(
        valid, ModernTourEntryIntent::Resume);
    assert(resume.intent == ModernTourEntryIntent::Resume);
    assert(resume.route_stock_frontend);
    assert(resume.restore_continuation_at_track_select);
    assert(!resume.retire_continuation_after_stock_wipe);

    // Restart is destructive only in the administrative sense: it discards
    // the pending host continuation after the stock rider-confirm path has
    // performed its own historical wipe. The product policy never authorizes
    // a direct SRAM-clear operation.
    const auto unconfirmed_restart = resolve_modern_tour_entry(
        valid, ModernTourEntryIntent::Restart, false);
    assert(unconfirmed_restart.intent == ModernTourEntryIntent::None);
    assert(!unconfirmed_restart.route_stock_frontend);
    assert(!unconfirmed_restart.restore_continuation_at_track_select);
    assert(!unconfirmed_restart.retire_continuation_after_stock_wipe);

    const auto restart = resolve_modern_tour_entry(
        valid, ModernTourEntryIntent::Restart, true);
    assert(restart.intent == ModernTourEntryIntent::Restart);
    assert(restart.route_stock_frontend);
    assert(!restart.restore_continuation_at_track_select);
    assert(restart.retire_continuation_after_stock_wipe);

    // Restart does not discard host continuation merely because the player
    // confirmed it. Retirement is allowed only after the stock route reaches
    // TRACK_SELECT and the stock qualification row is observed empty.
    assert(!modern_tour_entry_may_retire_continuation(
        restart, false, false));
    assert(!modern_tour_entry_may_retire_continuation(
        restart, true, false));
    assert(!modern_tour_entry_may_retire_continuation(
        restart, false, true));
    assert(modern_tour_entry_may_retire_continuation(
        restart, true, true));
    assert(!modern_tour_entry_may_retire_continuation(
        resume, true, true));

    ModernTourEntryContext authentic = valid;
    authentic.mode = ExecutionMode::Authentic;
    assert(!modern_tour_entry_actions(authentic).resume_available);
    assert(resolve_modern_tour_entry(
               authentic, ModernTourEntryIntent::Resume).intent ==
           ModernTourEntryIntent::None);
    assert(resolve_modern_tour_entry(
               authentic, ModernTourEntryIntent::Restart, true).intent ==
           ModernTourEntryIntent::None);

    ModernTourEntryContext no_profile = valid;
    no_profile.authoritative_profile = false;
    assert(!modern_tour_entry_actions(no_profile).restart_available);

    ModernTourEntryContext no_progress = valid;
    no_progress.unfinished_tour = false;
    assert(!modern_tour_entry_actions(no_progress).resume_available);

    ModernTourEntryContext stale = valid;
    stale.continuation_source_matches = false;
    assert(!modern_tour_entry_actions(stale).resume_available);
    assert(!modern_tour_entry_actions(stale).restart_available);

    return 0;
}
