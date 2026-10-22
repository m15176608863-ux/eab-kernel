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

class Rational;

class Int {
    using Backend = boost::multiprecision::number<
        boost::multiprecision::cpp_int_backend<>, boost::multiprecision::et_off>;
    Backend value_;
    explicit Int(Backend value) : value_(std::move(value)) {}
    friend class Rational;

public:
    Int(std::int64_t value = 0) : value_(value) {}
    static Int decimal(const std::string& digits) {
        if (digits.empty()) throw std::invalid_argument("empty integer");
        std::size_t at = digits[0] == '-' ? 1 : 0;
        if (at == digits.size()) throw std::invalid_argument("missing integer digits");
        Backend value = 0;
        for (; at < digits.size(); ++at) {
            if (digits[at] < '0' || digits[at] > '9')
                throw std::invalid_argument("invalid integer digit");
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
    friend Int operator+(const Int& a, const Int& b) { return Int(Backend(a.value_ + b.value_)); }
    friend Int operator-(const Int& a, const Int& b) { return Int(Backend(a.value_ - b.value_)); }
    friend Int operator*(const Int& a, const Int& b) { return Int(Backend(a.value_ * b.value_)); }
    friend Int operator/(const Int& a, const Int& b) { return Int(Backend(a.value_ / b.value_)); }
    friend Int operator%(const Int& a, const Int& b) { return Int(Backend(a.value_ % b.value_)); }
    friend Int operator-(const Int& a) { return Int(Backend(-a.value_)); }
    friend Int operator<<(const Int& a, std::size_t n) { return Int(Backend(a.value_ << n)); }
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
    explicit Rational(Backend value) : value_(std::move(value)) {}

public:
    Rational(std::int64_t value = 0) : value_(value) {}
    explicit Rational(const Int& value) : value_(value.value_) {}
    Rational(const Int& n, const Int& d) : value_(n.value_, d.value_) {}
    Int numerator() const { return Int(Int::Backend(boost::multiprecision::numerator(value_))); }
    Int denominator() const { return Int(Int::Backend(boost::multiprecision::denominator(value_))); }
    int sign() const { return value_ == 0 ? 0 : (value_ < 0 ? -1 : 1); }
    std::string canonical() const { return numerator().decimal() + "/" + denominator().decimal(); }
    friend Rational operator+(const Rational& a, const Rational& b) { return Rational(Backend(a.value_ + b.value_)); }
    friend Rational operator-(const Rational& a, const Rational& b) { return Rational(Backend(a.value_ - b.value_)); }
    friend Rational operator*(const Rational& a, const Rational& b) { return Rational(Backend(a.value_ * b.value_)); }
    friend Rational operator/(const Rational& a, const Rational& b) { return Rational(Backend(a.value_ / b.value_)); }
    friend Rational operator-(const Rational& a) { return Rational(Backend(-a.value_)); }
    friend bool operator==(const Rational& a, const Rational& b) { return a.value_ == b.value_; }
    friend bool operator!=(const Rational& a, const Rational& b) { return !(a == b); }
    friend bool operator<(const Rational& a, const Rational& b) { return a.value_ < b.value_; }
    friend bool operator>(const Rational& a, const Rational& b) { return b < a; }
    friend bool operator<=(const Rational& a, const Rational& b) { return !(b < a); }
    friend bool operator>=(const Rational& a, const Rational& b) { return !(a < b); }
};

inline Rational abs(const Rational& value) { return value.sign() < 0 ? -value : value; }

} // namespace eab2::exact
