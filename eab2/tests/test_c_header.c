#include "eab2/c_api.h"
#include <stdio.h>
#include <string.h>

int main(void) {
    eab2_abi_info info;
    eab2_context_options options;
    eab2_context context;
    memset(&info, 0, sizeof(info));
    info.struct_size = sizeof(info);
    info.abi_version = EAB2_ABI_VERSION;
    info.requested_capabilities = EAB2_CAP_CONTEXT;
    if (eab2_get_abi_info(&info) != EAB2_OK) return 1;
    if (info.context_size != sizeof(context) || info.binary64_bits != 64) return 2;
    if (info.supported_capabilities & EAB2_CAP_TEST_NUMERIC) return 3;
    if (eab2_self_test() != EAB2_OK) return 4;
    memset(&options, 0, sizeof(options));
    options.struct_size = sizeof(options);
    options.abi_version = EAB2_ABI_VERSION;
    if (eab2_context_create(&options, &context) != EAB2_OK) return 5;
    if (eab2_context_destroy(context) != EAB2_OK) return 6;
    if (eab2_context_destroy(context) != EAB2_INVALID_HANDLE) return 7;
#ifdef EAB2_STATIC
    puts("C_HEADER_STATIC checks=7 failures=0");
#else
    puts("C_HEADER_PRODUCTION_DLL checks=7 failures=0");
#endif
    return 0;
}
