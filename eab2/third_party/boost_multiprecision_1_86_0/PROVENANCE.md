# Boost.Multiprecision 1.86.0 provenance

- Source URL: https://codeload.github.com/boostorg/multiprecision/tar.gz/refs/tags/Boost_1_86_0
- Archive: `multiprecision-Boost_1_86_0.tar.gz`
- Archive SHA-256: `ef23b88cc3ae9c050d18887f7815aabb756c955ee8c64ca0b77690b79c316949`
- License: BSL-1.0, verbatim `LICENSE` alongside these headers.
- Mode: `BOOST_MP_STANDALONE`, MSVC 14.44.35207 x64, C++20.
- Selection: headers actually included by the `cpp_int` / `cpp_rational` et_off standalone probe (MSVC `/showIncludes`), plus LICENSE. Boost.Config is required by standalone_config.hpp. No downloads performed by this work order.
- All copied bytes were compared against BOTH the owner's extracted files and matching entries in the SHA-pinned archive. No third-party files were modified.
- Machine-readable inventory: [COPY_MANIFEST.json](COPY_MANIFEST.json).
- No copied individual file exceeds 1,000,000 bytes; no large-file exemption needed.
- This is a Windows/MSVC-only subset, not a general-purpose Boost distribution.

## Copied files

| Path | Bytes | SHA-256 |
|---|---:|---|
| `include/boost/config.hpp` | 2216 | `373206390d20aa5bb9e2628eb08543399d73b853af7bfc5f1d2bd9a00bc07593` |
| `include/boost/config/compiler/visualc.hpp` | 12785 | `1b607140adc4547e10b1203e779c9f0fa0a51173c2b9c750bec3e9daae04bb65` |
| `include/boost/config/detail/cxx_composite.hpp` | 9187 | `e1d48a1e474d7b3585f33b188aebc6d9a650155bc299122129896a7a1774841d` |
| `include/boost/config/detail/select_compiler_config.hpp` | 5356 | `73059f6ceb2952375b9cfb71ee609bd29c595d9f82014a01676fcc47c3a692d3` |
| `include/boost/config/detail/select_platform_config.hpp` | 4588 | `b24a891ef5cf8b032f1073c3e7d7416bba54657e58fec6f89e66c8ff9439665e` |
| `include/boost/config/detail/select_stdlib_config.hpp` | 4653 | `d26cb12104c9942b2031500c291ee13754dbb43b1d944fb30a7b98b119b83456` |
| `include/boost/config/detail/suffix.hpp` | 48075 | `f46a617b5bd44d2076c978ad7151b31f9921517d881f57ee927b26ae4c2383ec` |
| `include/boost/config/helper_macros.hpp` | 1120 | `ecf739b9b06545ebb0d691e8207cf7b70a5d42d7cb378d5d5502c0c96eefafc2` |
| `include/boost/config/platform/win32.hpp` | 2718 | `eaa82c93bc49969f4e91edd333e1068bb4aeeb97c9a3dcdf51c0f8dab05dc225` |
| `include/boost/config/pragma_message.hpp` | 1019 | `1951b59b8db3e8bf1e02c622605c7f45067dc3ce86eee8fba00f656099c64ab9` |
| `include/boost/config/stdlib/dinkumware.hpp` | 11403 | `6f8b6f608e92d92e18e436aefe1a56a157b2ad119ad1dec0122e057f1ad11a15` |
| `include/boost/config/user.hpp` | 5365 | `d24c2d771df2ee757c930466d69a0fac11cf721aaf89820f32c05c923a4ebca7` |
| `include/boost/config/workaround.hpp` | 8171 | `58a94045ef72552481b69a8b614a6c92e0d21ee19798677560ec4d59e10b0f99` |
| `include/boost/multiprecision/cpp_int.hpp` | 104250 | `4099045e8ac3e3507779c08980272b261a86498a23a4d0bb0786849f5424595a` |
| `include/boost/multiprecision/cpp_int/add.hpp` | 22328 | `3a6c9a403ee39f4ebb19fe1ebb7dc1a67368b0a441b419ebab733a9959cc1274` |
| `include/boost/multiprecision/cpp_int/add_unsigned.hpp` | 14128 | `9fd18ab658b9c20571c279f2d49df46fc713c1e0ffab1e025a98518fad30d2e0` |
| `include/boost/multiprecision/cpp_int/bitwise.hpp` | 42580 | `22bb953bd398773e7ea770c3bebcc051f10342cce10254b53da69f7061c22f50` |
| `include/boost/multiprecision/cpp_int/checked.hpp` | 5242 | `b33f0794085ffcd103c0dc576d9545af4d15a91d6dd254e87b3bea734572032d` |
| `include/boost/multiprecision/cpp_int/comparison.hpp` | 19208 | `506346c83b16e042f0f5cf90e0c669c50d1956dcc2dfc28e8c4a56fe6c565548` |
| `include/boost/multiprecision/cpp_int/cpp_int_config.hpp` | 6805 | `ca7cfa2c2fcc6f6c5e4c6daaec365d60b49dbd3f85e0a1c5cce0208a031204bf` |
| `include/boost/multiprecision/cpp_int/divide.hpp` | 29066 | `88c7ca149a95f70d06034ba80b40374a1ec7d40f2e8b93e0470cdd178fc569ef` |
| `include/boost/multiprecision/cpp_int/import_export.hpp` | 12507 | `6298449183554ab788f7b200f9f72cda46423439e9f5e19d02291b3f921d42e8` |
| `include/boost/multiprecision/cpp_int/intel_intrinsics.hpp` | 4280 | `0b989ebf7ea70be1a458fff8d6ec831b6f8bba59904a1a8448ee3ec392f5eda5` |
| `include/boost/multiprecision/cpp_int/limits.hpp` | 27106 | `e9ea155b8573e44f38e22a30e4fcdefd7a1807235300b71b77ea0f3056a3fb2d` |
| `include/boost/multiprecision/cpp_int/literals.hpp` | 12241 | `c271d461f00c5f7300faf758bee5d7bb96e2791f64d678eca2df02664d79a931` |
| `include/boost/multiprecision/cpp_int/misc.hpp` | 62949 | `8a95e268e6ce15d4e0dc48fc74d4ff970d7f156c7d1332077eca02356b8555c7` |
| `include/boost/multiprecision/cpp_int/multiply.hpp` | 45749 | `25413c62b71c24e9a4a42ea210ee206701c2a97b976960a2f9a39299905ab64c` |
| `include/boost/multiprecision/cpp_int/serialize.hpp` | 7244 | `bf671ec5be6b0c4fd80ffa5af353113e0cd7b559798782b97611b9a777a3b1b2` |
| `include/boost/multiprecision/cpp_int/value_pack.hpp` | 928 | `4d809c194298340d60ddcde5c5ce74b56a0df2567ca50cf239a0d87c938524ac` |
| `include/boost/multiprecision/detail/assert.hpp` | 810 | `f767e44bb2627a4686260ab9b715201a877532c2247da6b1ceeed3e0bc739aaa` |
| `include/boost/multiprecision/detail/bitscan.hpp` | 10587 | `9602b9df7fff54e2f330a9b06596525acbfa2c80808f7d7909445a56781963a5` |
| `include/boost/multiprecision/detail/check_cpp11_config.hpp` | 3737 | `c9cf1e182cf8024413362c8f0538fee6d29aa9c66ae0b3fde09168f43d615e23` |
| `include/boost/multiprecision/detail/constexpr.hpp` | 2139 | `2a04221b8778c2f7a26a650a9cbef7d0c440670c2a7e80a821dd66527f7eba5c` |
| `include/boost/multiprecision/detail/default_ops.hpp` | 240279 | `74d56bc6baa3e9a1bf6bcecbdaeb4bc2fa9f1edf1efc495d22face4956d4be12` |
| `include/boost/multiprecision/detail/digits.hpp` | 1343 | `c0e7666cac94a0f541cd572bb789a08a22a73a3748ffed905fa9c0a9e1d5d067` |
| `include/boost/multiprecision/detail/empty_value.hpp` | 2568 | `d4a56ae2e98882c4f7c1deeb2a1fc0555e33ad4723c42d1d65d082b2e1838606` |
| `include/boost/multiprecision/detail/endian.hpp` | 1360 | `1b712ae71c7021b6bcdd94f4ed6a660c88800ffc51be78d64c2b2c70de7294f7` |
| `include/boost/multiprecision/detail/et_ops.hpp` | 121893 | `976ae4aad4a0113f0681e0e5abba803b8ef31d2fa8c94d70893c754c8bf8d61d` |
| `include/boost/multiprecision/detail/float128_functions.hpp` | 2660 | `157fbb9d9378cd5f0ff8367b10573b8e72010165e5d6d2b3ea1b1d906c6c0127` |
| `include/boost/multiprecision/detail/fpclassify.hpp` | 3690 | `6d906b72713cae6c5dbaa52c8b7fcf2ebd03c1ead59912a4469732b43387f1b2` |
| `include/boost/multiprecision/detail/functions/constants.hpp` | 11774 | `58a28582e001a2abbedf4a6dcd1ed25068ae3a8dfc2778d14412a7badbd44220` |
| `include/boost/multiprecision/detail/functions/pow.hpp` | 27767 | `4912686750dae76e829a6912718fa3889dae425919059a91bac7e753b6f4aa64` |
| `include/boost/multiprecision/detail/functions/trig.hpp` | 32274 | `e802b586c80227149d36621e2752ea15f90d7b22bef92f5d17426ff521fc8845` |
| `include/boost/multiprecision/detail/functions/trunc.hpp` | 1979 | `d23ae08ead72273a57fc8fb401fcb32946def60febbc35a303e81e97b77993ed` |
| `include/boost/multiprecision/detail/generic_interconvert.hpp` | 26407 | `9ec3cca3e2488a185d17c2b4dba29e8b84c1eef39e0ad1bb523b4123c370f6c0` |
| `include/boost/multiprecision/detail/hash.hpp` | 1415 | `e1732d23c800b86062042a0f4d80395dc96f5ddcc696ac959b7a345ddc326ad6` |
| `include/boost/multiprecision/detail/integer_ops.hpp` | 18164 | `9ff2b7319b50085ceef269f92ee0d66d352ec8508b6fd1e7b8b133eb5678d918` |
| `include/boost/multiprecision/detail/min_max.hpp` | 4916 | `02c2587cd737cb15c91ee3640e57020b5c7355652c0e424c5d1f59c7a8736db0` |
| `include/boost/multiprecision/detail/no_et_ops.hpp` | 34948 | `1ae8ba856da812296a0ea1dff85ed0518e3a77e364c5ae2dfd6a0c4f28b8940f` |
| `include/boost/multiprecision/detail/no_exceptions_support.hpp` | 1869 | `9ccda2c4a2129244a656fed2c2081fcfe0c08964a37285066688fcd5d705a838` |
| `include/boost/multiprecision/detail/number_base.hpp` | 72928 | `b5f13b9f303d56216cb94bec90da5889e9529c01a1d85c8a51cbd2bd3b702a7c` |
| `include/boost/multiprecision/detail/number_compare.hpp` | 51232 | `e1d75991ad8e536ea9e850f2169979416b3823d1209b2305d3ff78af926e0e18` |
| `include/boost/multiprecision/detail/precision.hpp` | 13298 | `6a260661370a86ac273f3e31686a304fbc6bffa05fa726d3494181ddbd122549` |
| `include/boost/multiprecision/detail/rebind.hpp` | 730 | `2be7a28a74df4564ff6894ca4ba094e9affe9da69c17ac8d466909a16bbb6087` |
| `include/boost/multiprecision/detail/standalone_config.hpp` | 4625 | `ab479b39be1436d383d57cef60144831b784096b067eeadfa410ba9f447d04ec` |
| `include/boost/multiprecision/detail/ublas_interop.hpp` | 4325 | `b267977257ca6342b94345265c4d8efb382b2fef654961687e88df3d1a23fa56` |
| `include/boost/multiprecision/fwd.hpp` | 12594 | `da8f2d642828572587cf5dbac7552ba85a8a266734398bf71c596f339eadbc5e` |
| `include/boost/multiprecision/integer.hpp` | 12039 | `1a2d18d16098b528ce9dd13ac8fc440d543cdcb691c894255f442da7afd3734c` |
| `include/boost/multiprecision/number.hpp` | 120900 | `2549b437a6319ee9cbd2032560a0272611715dd89c2919dd85a4a3f9e9aed569` |
| `include/boost/multiprecision/rational_adaptor.hpp` | 39529 | `23757733a6f1111aab0af98bb0bf5105fde08ac412c2cbf18d51bbad42656012` |
| `include/boost/multiprecision/traits/explicit_conversion.hpp` | 2480 | `345bac71d2bc558ad299eb4b4eccb55e17aea6c0400a7247d3748a0ee00bc657` |
| `include/boost/multiprecision/traits/is_backend.hpp` | 2842 | `2259d4c191b10b2cdd8ed3d4fc47cd4e7a68f53cbb66548fa25d387cbcf2b50d` |
| `include/boost/multiprecision/traits/is_byte_container.hpp` | 1609 | `4219605c62b0af6b62918f9974e3f8f52c7f9a5a03d57e2a815557c2ef6fcc9b` |
| `include/boost/multiprecision/traits/is_complex.hpp` | 717 | `325bd1c8b4fad14f82e9028f353dfdd9512cdf0dff5011004880989c175444d3` |
| `include/boost/multiprecision/traits/is_convertible_arithmetic.hpp` | 1854 | `a3c604ed31afffda69f15e8bf473b10afe0d3361dfb8b73b1da2758d4cbe9efe` |
| `include/boost/multiprecision/traits/is_restricted_conversion.hpp` | 2533 | `d4d900efa2b34ceb4cd3975b23f85d46f090c1d54b2e28f63d028ac731061e4e` |
| `include/boost/multiprecision/traits/is_variable_precision.hpp` | 851 | `e8356c3d88d7de15a3081febb6c3a6258973c8c031b370bae2a139f2a2092500` |
| `include/boost/multiprecision/traits/max_digits10.hpp` | 2896 | `06859bbdc55e5ec7f329677fb9caae31a490c52327796657c7eb4d2b3f37d4cb` |
| `include/boost/multiprecision/traits/std_integer_traits.hpp` | 2563 | `65e01b9d8a1121d367a6b877464033cbec3a3f9fc765ad69ed5e5cdff539034d` |
| `include/boost/multiprecision/traits/transcendental_reduction_type.hpp` | 621 | `88cf0f2bbd93559dad052642721dbb2fb1db63f33a090eef3c79e4ff6b25a69a` |
| `LICENSE` | 1338 | `c9bff75738922193e67fa726fa225535870d2aa1059f91452c411736284ad566` |
