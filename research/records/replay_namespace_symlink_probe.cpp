#include <cassert>
#include <filesystem>
#include <iostream>
#include <system_error>
namespace fs = std::filesystem;
int main(int argc,char** argv) {
  assert(argc == 2);
  fs::path base(argv[1]);
  fs::path owner = base / "owner";
  fs::path foreign = base / "foreign";
  fs::create_directories(owner);
  fs::create_directories(foreign);
  std::error_code ec;
  fs::create_directory_symlink(foreign, owner / "replay", ec);
  if (ec) { std::cerr << "symlink unavailable: " << ec.message() << '\n'; return 2; }
  ec.clear();
  fs::create_directories(owner / "replay", ec);
  assert(!ec); // old code treats redirected parent as valid
  ec.clear();
  const auto status = fs::symlink_status(owner / "replay", ec);
  const bool allowed = !ec && fs::is_directory(status) && !fs::is_symlink(status);
  assert(!allowed); // corrected code must refuse the redirect
  assert(fs::is_empty(foreign));
  std::cout << "old create_directories admitted symlink; new direct-directory guard refused\n";
}
