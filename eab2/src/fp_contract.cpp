#include "fp_contract.hpp"

#include <bit>
#include <cfenv>
#include <cstdint>
#include <limits>
#include <xmmintrin.h>

#pragma float_control(precise, on, push)
#pragma fp_contract(off)

namespace eab2::fp {
namespace {
__declspec(noinline) double add(double a, double b) { return a + b; }
__declspec(noinline) double multiply(double a, double b) { return a * b; }
__declspec(noinline) double negate(double a) { return -a; }
// No volatile intermediate product: this probes contraction of the expression.
__declspec(noinline) double contraction(double a, double b, double c) {
    return a * b + c;
}
double load(volatile std::uint64_t* source) {
    const std::uint64_t bits = *source;
    return std::bit_cast<double>(bits);
}
}

std::uint32_t self_test() noexcept {
    constexpr std::uint32_t failure = 6;
    static_assert(sizeof(double) == sizeof(std::uint64_t));
    const unsigned original = _mm_getcsr();
    // Check traps first: no potentially exceptional probe precedes this gate.
    if ((original & 0x1f80U) != 0x1f80U ||
        (original & (0x8000U | 0x0040U | 0x6000U)) != 0 ||
        std::fegetround() != FE_TONEAREST) {
        return failure;
    }
    if constexpr (!std::numeric_limits<double>::is_iec559 ||
        std::numeric_limits<double>::radix != 2 ||
        std::numeric_limits<double>::digits != 53 ||
        std::numeric_limits<double>::max_exponent != 1024) {
        return failure;
    }
    // Probes can set sticky inexact flags. Restore exactly those original bits;
    // never repair or change any caller control mode to make a bad mode pass.
    struct RestoreStatus {
        unsigned saved;
        ~RestoreStatus() { _mm_setcsr(saved); }
    } restore{original};
    volatile std::uint64_t raw[] = {
        UINT64_C(0x3ff0000000000000), UINT64_C(0x3ca0000000000000),
        UINT64_C(0x3cb8000000000000), UINT64_C(0x0000000000000000),
        UINT64_C(0x0010000000000000), UINT64_C(0x3fe0000000000000),
        UINT64_C(0x3ff0000002000000), UINT64_C(0x3feffffffc000000),
        UINT64_C(0xbff0000000000000)};
    if (std::bit_cast<std::uint64_t>(load(&raw[0])) != UINT64_C(0x3ff0000000000000) ||
        std::bit_cast<std::uint64_t>(add(load(&raw[0]), load(&raw[1]))) != UINT64_C(0x3ff0000000000000) ||
        std::bit_cast<std::uint64_t>(add(load(&raw[0]), load(&raw[2]))) != UINT64_C(0x3ff0000000000002) ||
        std::bit_cast<std::uint64_t>(negate(load(&raw[3]))) != UINT64_C(0x8000000000000000) ||
        std::bit_cast<std::uint64_t>(multiply(load(&raw[4]), load(&raw[5]))) != UINT64_C(0x0008000000000000) ||
        std::bit_cast<std::uint64_t>(contraction(load(&raw[6]), load(&raw[7]), load(&raw[8]))) != 0) {
        return failure;
    }
    return 0;
}
}
#pragma float_control(pop)
