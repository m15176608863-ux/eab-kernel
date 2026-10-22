#if defined(__AVX__)
#error eab2 controlled sources require the x64 SSE2 compilation target
#endif
#pragma once

// The only boundary that knows Boost types. All arithmetic returns owning values.
#ifndef BOOST_MP_STANDALONE
#define BOOST_MP_STANDALONE
#endif
#include <boost/multiprecision/cpp_int.hpp>
#include <cstdint>
#include <stdexcept>
#include <string>
#include <utility>

namespace eab2::exact {

struct ResourceLimit : std::runtime_error { using std::runtime_error::runtime_error; };
// Zero means unbounded only inside C0/private arithmetic, never in C1 config.
inline thread_local std::size_t integer_limit_bits = 0;
class IntegerLimitScope {
    std::size_t previous_;
public:
    explicit IntegerLimitScope(std::size_t limit) : previous_(integer_limit_bits) {
        integer_limit_bits = previous_ && (!limit || previous_ < limit) ? previous_ : limit;
    }
    ~IntegerLimitScope() { integer_limit_bits = previous_; }
    IntegerLimitScope(const IntegerLimitScope&) = delete;
    IntegerLimitScope& operator=(const IntegerLimitScope&) = delete;
};
inline void require_integer_bits(std::size_t bits) {
    if (integer_limit_bits && bits > integer_limit_bits)
        throw ResourceLimit("integer bit work limit exceeded");
}
inline void require_bit_sum(std::size_t first, std::size_t second, std::size_t extra = 0) {
    if (!integer_limit_bits) return;
    if (first > integer_limit_bits || second > integer_limit_bits - first ||
        extra > integer_limit_bits - first - second)
        throw ResourceLimit("integer operation conservative bit work limit exceeded");
}


class Rational;

class Int {
    using Backend = boost::multiprecision::number<
        boost::multiprecision::cpp_int_backend<>, boost::multiprecision::et_off>;
    Backend value_;
    explicit Int(Backend value) : value_(std::move(value)) { require_integer_bits(bit_length()); }
    friend class Rational;

public:
    Int(std::int64_t value = 0) : value_(value) { require_integer_bits(bit_length()); }
    static Int decimal(const std::string& digits) {
        if (digits.empty()) throw std::invalid_argument("empty integer");
        std::size_t at = digits[0] == '-' ? 1 : 0;
        if (at == digits.size()) throw std::invalid_argument("missing integer digits");
        Backend value = 0;
        for (; at < digits.size(); ++at) {
            if (digits[at] < '0' || digits[at] > '9')
                throw std::invalid_argument("invalid integer digit");
            if (integer_limit_bits) {
                const auto used = value == 0 ? 0 : static_cast<std::size_t>(boost::multiprecision::msb(value)) + 1;
                require_bit_sum(used, 4);
            }
            value *= 10;
            value += digits[at] - '0';
        }
        if (digits[0] == '-') value = -value;
        return Int(std::move(value));
    }
    std::string decimal() const { return value_.str(); }
    int sign() const { return value_ == 0 ? 0 : (value_ < 0 ? -1 : 1); }
    bool odd() const { return (value_ & 1) != 0; }
    std::size_t bit_length() const {
        // msb has no zero domain, and no negative domain on this backend.
        if (value_ == 0) return 0;
        const Backend magnitude = value_ < 0 ? -value_ : value_;
        return static_cast<std::size_t>(boost::multiprecision::msb(magnitude)) + 1;
    }
    std::uint64_t u64() const {
        if (value_ < 0 || bit_length() > 64) throw std::overflow_error("integer does not fit uint64");
        return value_.convert_to<std::uint64_t>();
    }
    friend Int operator+(const Int& a, const Int& b) {
        require_bit_sum(a.bit_length() > b.bit_length() ? a.bit_length() : b.bit_length(), 1);
        return Int(Backend(a.value_ + b.value_));
    }
    friend Int operator-(const Int& a, const Int& b) {
        require_bit_sum(a.bit_length() > b.bit_length() ? a.bit_length() : b.bit_length(), 1);
        return Int(Backend(a.value_ - b.value_));
    }
    friend Int operator*(const Int& a, const Int& b) {
        require_bit_sum(a.bit_length(), b.bit_length());
        return Int(Backend(a.value_ * b.value_));
    }
    friend Int operator/(const Int& a, const Int& b) { return Int(Backend(a.value_ / b.value_)); }
    friend Int operator%(const Int& a, const Int& b) { return Int(Backend(a.value_ % b.value_)); }
    friend Int operator-(const Int& a) { return Int(Backend(-a.value_)); }
    friend Int operator<<(const Int& a, std::size_t n) {
        require_bit_sum(a.bit_length(), n);
        return Int(Backend(a.value_ << n));
    }
    friend Int operator>>(const Int& a, std::size_t n) { return Int(Backend(a.value_ >> n)); }
    friend bool operator==(const Int& a, const Int& b) { return a.value_ == b.value_; }
    friend bool operator!=(const Int& a, const Int& b) { return !(a == b); }
    friend bool operator<(const Int& a, const Int& b) { return a.value_ < b.value_; }
    friend bool operator>(const Int& a, const Int& b) { return b < a; }
    friend bool operator<=(const Int& a, const Int& b) { return !(b < a); }
    friend bool operator>=(const Int& a, const Int& b) { return !(a < b); }
};

inline Int abs(const Int& value) { return value.sign() < 0 ? -value : value; }

// Newton integer square root, with a proved upper initial power of two.
inline Int isqrt(const Int& value) {
    if (value.sign() < 0) throw std::invalid_argument("negative integer square root");
    if (value == Int(0)) return Int(0);
    Int x = Int(1) << ((value.bit_length() + 1) / 2);
    for (;;) {
        const Int next = (x + value / x) >> 1;
        if (next >= x) return x;
        x = next;
    }
}

class Rational {
    using Backend = boost::multiprecision::number<
        boost::multiprecision::rational_adaptor<boost::multiprecision::cpp_int_backend<>>,
        boost::multiprecision::et_off>;
    Backend value_;
    void check() const {
        if (!integer_limit_bits) return;
        require_integer_bits(numerator().bit_length());
        require_integer_bits(denominator().bit_length());
    }
    static void sum_work(const Rational& a, const Rational& b) {
        if (!integer_limit_bits) return;
        require_bit_sum(a.numerator().bit_length(), b.denominator().bit_length(), 1);
        require_bit_sum(b.numerator().bit_length(), a.denominator().bit_length(), 1);
        require_bit_sum(a.denominator().bit_length(), b.denominator().bit_length());
    }
    explicit Rational(Backend value) : value_(std::move(value)) { check(); }

public:
    Rational(std::int64_t value = 0) : value_(value) { check(); }
    explicit Rational(const Int& value) : value_(value.value_) { check(); }
    Rational(const Int& n, const Int& d) : value_(n.value_, d.value_) { check(); }
    Int numerator() const { return Int(Int::Backend(boost::multiprecision::numerator(value_))); }
    Int denominator() const { return Int(Int::Backend(boost::multiprecision::denominator(value_))); }
    int sign() const { return value_ == 0 ? 0 : (value_ < 0 ? -1 : 1); }
    std::string canonical() const { return numerator().decimal() + "/" + denominator().decimal(); }
    friend Rational operator+(const Rational& a, const Rational& b) { sum_work(a, b); return Rational(Backend(a.value_ + b.value_)); }
    friend Rational operator-(const Rational& a, const Rational& b) { sum_work(a, b); return Rational(Backend(a.value_ - b.value_)); }
    friend Rational operator*(const Rational& a, const Rational& b) {
        if (integer_limit_bits) {
            require_bit_sum(a.numerator().bit_length(), b.numerator().bit_length());
            require_bit_sum(a.denominator().bit_length(), b.denominator().bit_length());
        }
        return Rational(Backend(a.value_ * b.value_));
    }
    friend Rational operator/(const Rational& a, const Rational& b) {
        if (integer_limit_bits) {
            require_bit_sum(a.numerator().bit_length(), b.denominator().bit_length());
            require_bit_sum(a.denominator().bit_length(), b.numerator().bit_length());
        }
        return Rational(Backend(a.value_ / b.value_));
    }
    friend Rational operator-(const Rational& a) { return Rational(Backend(-a.value_)); }
    friend bool operator==(const Rational& a, const Rational& b) { return a.value_ == b.value_; }
    friend bool operator!=(const Rational& a, const Rational& b) { return !(a == b); }
    friend bool operator<(const Rational& a, const Rational& b) {
        if (integer_limit_bits) {
            require_bit_sum(a.numerator().bit_length(), b.denominator().bit_length());
            require_bit_sum(b.numerator().bit_length(), a.denominator().bit_length());
        }
        return a.value_ < b.value_;
    }
    friend bool operator>(const Rational& a, const Rational& b) { return b < a; }
    friend bool operator<=(const Rational& a, const Rational& b) { return !(b < a); }
    friend bool operator>=(const Rational& a, const Rational& b) { return !(a < b); }
};

inline Rational abs(const Rational& value) { return value.sign() < 0 ? -value : value; }

} // namespace eab2::exact
