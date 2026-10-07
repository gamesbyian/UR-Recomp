#pragma once

#include <string>

namespace ur::product {

/*
 * Canonical local-date presentation for append-only run artifact filenames:
 *
 *   run-<16 decimal milliseconds>-<suffix>.urrun
 *
 * The timestamp is host ordering metadata, not replay/timing authority.
 * Malformed/noncanonical filenames return "--".
 */
std::string run_artifact_date_text(const std::string& path);

}  // namespace ur::product
