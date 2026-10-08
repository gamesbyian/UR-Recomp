# Local Tournament instance and fixture-attempt IDs

Status: standalone OS-entropy utility with strict native C++17 acceptance. The player-facing tournament entry route is still outstanding.

The existing launch/receipt/standings contracts require a unique canonical 32-character lowercase hex tournament instance ID for every new event and an independently generated ID for each explicit fixture launch. Production callers should use `mint_local_tournament_token()` from `native/product/local_tournament_tokens.hpp` for both operations, and must refuse creation or launch if it returns no token.

The source is 128 bits of operating-system cryptographic entropy: Windows BCryptGenRandom (system-preferred RNG), Linux getrandom (including correct EINTR and short-read handling), or native arc4random_buf on supported BSD/macOS. There is no fallback to timestamps, saved-run filenames, predictable standard PRNG seeds or user identity; other OS platforms fail closed until their native entropy source is integrated. Windows MSVC/clang-cl links bcrypt through the compiler directive. No new persistent state or guest game authority is created.

The token is an unpredictable unique identifier for provenance and duplicate prevention. It is NOT a cryptographic signature or proof of who started a tournament. The pre-race fixture binding and exact saved pair/receipt remain authoritative for membership.

The C++ test checks canonical 32-hex output, repeated independent minting, and successful arming of the existing round-robin fixture with separately minted tournament/attempt IDs. This does not claim normal Windows player-facing event creation is yet wired to the token utility.
