#define BOOST_MP_STANDALONE
#include <boost/multiprecision/cpp_int.hpp>
#include <iostream>
using Int = boost::multiprecision::number<boost::multiprecision::cpp_int_backend<>, boost::multiprecision::et_off>;
using Rational = boost::multiprecision::number<boost::multiprecision::rational_adaptor<boost::multiprecision::cpp_int_backend<>>, boost::multiprecision::et_off>;
int main() {
    Int n = 1; n <<= 200;
    Rational q(n, Int(3));
    Rational r = q * 3;
    if (r != Rational(n) || numerator(q) != n || denominator(q) != 3) return 1;
    std::cout << "BOOST_STANDALONE_OK cpp_int cpp_rational et_off\n";
}
