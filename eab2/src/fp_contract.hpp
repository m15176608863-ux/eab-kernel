#ifndef EAB2_FP_CONTRACT_HPP
#define EAB2_FP_CONTRACT_HPP

#if defined(_M_FP_FAST) || defined(__FAST_MATH__) || defined(_M_FP_CONTRACT)
#error eab2 rejects fast math and contraction compilation modes
#endif
#if !defined(_MSC_VER) || !defined(_M_X64)
#error eab2 C0 supports only MSVC x64
#endif

#include <cstdint>

namespace eab2::fp {
std::uint32_t self_test() noexcept;
}
#endif
