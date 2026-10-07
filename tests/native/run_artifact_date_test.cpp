#include "run_artifact_date.hpp"

#include <cassert>
#include <string>

using namespace ur::product;

int main() {
    const auto canonical =
        run_artifact_date_text("run-0000000000000000-0001.urrun");
    assert(canonical.size() == 10);
    assert(canonical != "--");

    const auto nested = run_artifact_date_text(
        "some/profile/runs/run-0000000000000000-0042.urrun");
    assert(nested.size() == 10);
    assert(nested != "--");

    assert(run_artifact_date_text("run.urrun") == "--");
    assert(run_artifact_date_text(
               "bad-0000000000000000-0001.urrun") == "--");
    assert(run_artifact_date_text(
               "run-000000000000000-0001.urrun") == "--");
    assert(run_artifact_date_text(
               "run-000000000000000X-0001.urrun") == "--");
    assert(run_artifact_date_text(
               "run-0000000000000000_0001.urrun") == "--");

    return 0;
}
