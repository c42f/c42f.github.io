#include <cassert>
#include <cstdint>
#include <iostream>

uint32_t hash(uint32_t key)
{
    uint32_t k0 = key;
    uint32_t k1 = k0 + ~(k0 << 15);  // k1 = (1-(1<<15))*k0 - 1 = ~(((1<<15) - 1) * k0)
    uint32_t k2 = k1 ^  (k1 >> 10);
    uint32_t k3 = k2 +  (k2 <<  3);  // k3 = 9*k2
    uint32_t k4 = k3 ^  (k3 >>  6);
    uint32_t k5 = k4 + ~(k4 << 11);  // k5 = (1-(1<<11))*k4 - 1 = ~(((1<<11) - 1) * k4)
    uint32_t k6 = k5 ^  (k5 >> 16);
    return k6;
}

uint32_t unhash(uint32_t hashval)
{
    uint32_t k6 = hashval;
    uint32_t k5 = k6 ^ (k6 >> 16);
    uint32_t k4 = 4290770943 * ~k5;
    uint32_t k3 = k4 ^ (k4 >> 6) ^ (k4 >> 12) ^ (k4 >> 18) ^ (k4 >> 24) ^ (k4 >> 30);
    uint32_t k2 = 954437177 * k3;
    uint32_t k1 = k2 ^ (k2 >> 10) ^ (k2 >> 20) ^ (k2 >> 30);
    uint32_t k0 = 3221192703 * ~k1;
    return k0;
    // Some slower alternative expressions for steps...
    // uint32_t k4 = 4196353 + k5 + (k5<<22) + (k5<<11);
    // uint32_t k0 = 1073774593 + k1 + (k1<<30) + (k1 << 15);
}

int main()
{
    // uint32_t i = 1234567891;
    // uint32_t j = unhash(hash(i));
    // std::cout << i-j << "\n";

    // Proof of inverse proof by exhaustive search
    for (uint64_t i = 0; i <= UINT32_MAX; ++i)
    {
        assert (unhash(hash(i)) == i);
        if (i % 100000000 == 0)
            std::cout << 100.0*i/UINT32_MAX << "%\n";
    }
    return 0;
}
