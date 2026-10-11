/*
 * Explicit OPT-IN loopback-only direct UDP contact experiment.
 * This is NOT a player protocol, matchmaking, encryption, authentication,
 * NAT traversal, live guest input, or a permanent background service.
 * Neither mode contacts anything beyond IPv4 127.0.0.1.
 */
#include <array>
#include <cstdint>
#include <cerrno>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <string>
#include <string_view>

#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
#include <winsock2.h>
#include <ws2tcpip.h>
using Socket = SOCKET;
constexpr Socket kInvalid = INVALID_SOCKET;
#else
#include <arpa/inet.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <unistd.h>
using Socket = int;
constexpr Socket kInvalid = -1;
#endif

namespace {

void close_socket(Socket s) {
#ifdef _WIN32
    closesocket(s);
#else
    close(s);
#endif
}

struct Network {
#ifdef _WIN32
    WSADATA state{};
    bool started = false;
    Network() { started = WSAStartup(MAKEWORD(2, 2), &state) == 0; }
    ~Network() { if (started) WSACleanup(); }
#else
    bool started = true;
#endif
};

bool valid_hex(std::string_view value, std::size_t count) {
    if (value.size() != count) return false;
    bool nonzero = false;
    for (const char ch : value) {
        if (!((ch >= '0' && ch <= '9') ||
              (ch >= 'a' && ch <= 'f'))) return false;
        nonzero |= ch != '0';
    }
    return nonzero;
}

bool parse_port(std::string_view input, std::uint16_t& port) {
    if (input.empty() || input.size() > 5) return false;
    unsigned n = 0;
    for (char ch : input) {
        if (ch < '0' || ch > '9') return false;
        n = n * 10u + static_cast<unsigned>(ch - '0');
    }
    if (n == 0 || n > 65535) return false;
    port = static_cast<std::uint16_t>(n);
    return true;
}

sockaddr_in loopback(std::uint16_t port) {
    sockaddr_in addr{};
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    addr.sin_port = htons(port);
    return addr;
}

bool set_timeout(Socket socket) {
#ifdef _WIN32
    DWORD timeout = 2500;
    return setsockopt(socket, SOL_SOCKET, SO_RCVTIMEO,
        reinterpret_cast<const char*>(&timeout), sizeof(timeout)) == 0;
#else
    timeval timeout{};
    timeout.tv_sec = 2;
    timeout.tv_usec = 500000;
    return setsockopt(socket, SOL_SOCKET, SO_RCVTIMEO,
        &timeout, sizeof(timeout)) == 0;
#endif
}

int listen_once(std::string_view nonce, std::string_view sim) {
    const Socket fd = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    if (fd == kInvalid) return 3;
    const auto addr = loopback(0);
    if (bind(fd, reinterpret_cast<const sockaddr*>(&addr), sizeof(addr)) != 0 ||
        !set_timeout(fd)) { close_socket(fd); return 4; }
    sockaddr_in local{};
#ifdef _WIN32
    int local_len = sizeof(local);
#else
    socklen_t local_len = sizeof(local);
#endif
    if (getsockname(fd, reinterpret_cast<sockaddr*>(&local), &local_len) != 0) {
        close_socket(fd); return 5;
    }
    std::cout << "READY udp@127.0.0.1:" << ntohs(local.sin_port) << std::endl;
    std::array<char, 256> incoming{};
    sockaddr_in sender{};
#ifdef _WIN32
    int sender_len = sizeof(sender);
#else
    socklen_t sender_len = sizeof(sender);
#endif
    const int got = recvfrom(fd, incoming.data(), static_cast<int>(incoming.size()),
        0, reinterpret_cast<sockaddr*>(&sender), &sender_len);
    const std::string expected = "UR-LOOPBACK-HELLO-V0:" +
        std::string(nonce) + ":" + std::string(sim);
    if (got != static_cast<int>(expected.size()) ||
        std::memcmp(incoming.data(), expected.data(), expected.size()) != 0 ||
        sender.sin_addr.s_addr != htonl(INADDR_LOOPBACK)) {
        close_socket(fd); return 6;
    }
    const std::string reply = "UR-LOOPBACK-ACK-V0:" +
        std::string(nonce) + ":" + std::string(sim);
    const int sent = sendto(fd, reply.data(), static_cast<int>(reply.size()), 0,
        reinterpret_cast<const sockaddr*>(&sender), sender_len);
    close_socket(fd);
    if (sent != static_cast<int>(reply.size())) return 7;
    std::cout << "ACCEPTED local-direct-probe-only" << std::endl;
    return 0;
}

int dial_once(std::uint16_t port, std::string_view nonce,
              std::string_view sim) {
    const Socket fd = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    if (fd == kInvalid) return 3;
    if (!set_timeout(fd)) { close_socket(fd); return 4; }
    const auto addr = loopback(port);
    const std::string hello = "UR-LOOPBACK-HELLO-V0:" +
        std::string(nonce) + ":" + std::string(sim);
    const int sent = sendto(fd, hello.data(), static_cast<int>(hello.size()), 0,
        reinterpret_cast<const sockaddr*>(&addr), sizeof(addr));
    if (sent != static_cast<int>(hello.size())) { close_socket(fd); return 5; }
    std::array<char, 256> response{};
    sockaddr_in sender{};
#ifdef _WIN32
    int from_size = sizeof(sender);
#else
    socklen_t from_size = sizeof(sender);
#endif
    const int got = recvfrom(fd, response.data(), static_cast<int>(response.size()),
        0, reinterpret_cast<sockaddr*>(&sender), &from_size);
    close_socket(fd);
    const std::string expected = "UR-LOOPBACK-ACK-V0:" +
        std::string(nonce) + ":" + std::string(sim);
    if (got != static_cast<int>(expected.size()) ||
        std::memcmp(response.data(), expected.data(), expected.size()) != 0 ||
        sender.sin_addr.s_addr != htonl(INADDR_LOOPBACK) ||
        ntohs(sender.sin_port) != port) return 6;
    std::cout << "DIRECT local-two-process-probe-only" << std::endl;
    return 0;
}
} // namespace

int main(int argc, char** argv) {
    // Explicit action and scoped address are essential: no broadcast,
    // system default peers, remote route or automatic network activity.
    if ((argc != 5 && argc != 6) ||
        std::string_view(argv[1]) != "--allow-loopback-only" ||
        !valid_hex(argv[3], 32) || !valid_hex(argv[4], 64)) {
        std::cerr << "usage: lab --allow-loopback-only listen NONCE32 SIM32\n"
                  << "   or: lab --allow-loopback-only dial NONCE32 SIM32 PORT\n";
        return 2;
    }
    const Network network;
    if (!network.started) return 3;
    if (std::string_view(argv[2]) == "listen" && argc == 5)
        return listen_once(argv[3], argv[4]);
    std::uint16_t port = 0;
    if (std::string_view(argv[2]) == "dial" && argc == 6 &&
        parse_port(argv[5], port))
        return dial_once(port, argv[3], argv[4]);
    return 2;
}
