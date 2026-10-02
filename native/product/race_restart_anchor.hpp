#pragma once

#include <cstddef>
#include <cstdint>
#include <vector>

namespace ur::product {

struct SnapshotRuntimeHooks {
    std::size_t (*save_snapshot)(void* data, std::size_t capacity) = nullptr;
    bool (*load_snapshot)(const void* data, std::size_t size) = nullptr;
};

enum class RestartAnchorCaptureStatus : std::uint8_t {
    Captured = 0,
    AlreadyArmed = 1,
    MissingHook = 2,
    CaptureFailed = 3,
};

enum class RestartAnchorRestoreStatus : std::uint8_t {
    Restored = 0,
    NoAnchor = 1,
    MissingHook = 2,
    RestoreFailed = 3,
};

class RaceRestartAnchor {
public:
    static constexpr std::size_t default_capacity = 2u * 1024u * 1024u;

    explicit RaceRestartAnchor(
        SnapshotRuntimeHooks hooks,
        std::size_t capacity = default_capacity);

    RestartAnchorCaptureStatus capture();
    RestartAnchorRestoreStatus restart();

    void clear() noexcept;
    bool armed() const noexcept { return !snapshot_.empty(); }
    std::size_t snapshot_size() const noexcept { return snapshot_.size(); }

private:
    SnapshotRuntimeHooks hooks_;
    std::size_t capacity_;
    std::vector<std::uint8_t> snapshot_;
};

}  // namespace ur::product
