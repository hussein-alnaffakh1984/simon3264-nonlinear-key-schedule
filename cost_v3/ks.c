/* Key schedules std / v2 / v3 for Simon 32/64 (C99, branch-free, no tables, no libc). */
#include <stdint.h>
#define U16(v)    ((uint16_t)(v))
#define ROR(x,n)  U16((U16(x) >> (n)) | (U16(x) << (16 - (n))))
#define ROL(x,n)  ROR(x, 16 - (n))
#define Z0_28 UINT32_C(0x0386A45F)
static uint16_t nl(uint16_t w){ uint16_t n1 = U16((((w >> 15) & (w >> 7)) | (w >> 3)) & ((w >> 13) | (w >> 3)) & 1u); return U16(U16(w << 1) | n1); }
void ks_std(const uint16_t mk[4], uint16_t rk[32]){ uint32_t z = Z0_28; uint8_t i; uint16_t t;
    for (i = 0; i < 4; i++) rk[i] = mk[i];
    for (i = 4; i < 32; i++) { t = U16(ROR(rk[i-1], 3) ^ rk[i-3]); t = U16(t ^ ROR(t, 1)); rk[i] = U16(rk[i-4] ^ t ^ 0xFFFCu ^ (uint16_t)(z & 1u)); z >>= 1; } }
void ks_v2(const uint16_t mk[4], uint16_t rk[32]){ uint32_t z = Z0_28; uint8_t i; uint16_t t;
    for (i = 0; i < 4; i++) rk[i] = mk[i];
    for (i = 4; i < 32; i++) { t = U16(ROR(rk[i-1], 3) ^ nl(rk[i-3])); t = U16(t ^ ROR(t, 5)); rk[i] = U16(rk[i-4] ^ t ^ 0xFFFCu ^ (uint16_t)(z & 1u)); z >>= 1; } }
void ks_v3(const uint16_t mk[4], uint16_t rk[32]){ uint32_t z = Z0_28; uint8_t i; uint16_t t;
    for (i = 0; i < 4; i++) rk[i] = mk[i];
    for (i = 4; i < 32; i++) { t = U16(ROR(rk[i-1], 3) ^ rk[i-3] ^ (ROL(rk[i-1], 1) & ROL(rk[i-1], 8))); t = U16(t ^ ROR(t, 1)); rk[i] = U16(rk[i-4] ^ t ^ 0xFFFCu ^ (uint16_t)(z & 1u)); z >>= 1; } }
void ks_v3_inv(uint16_t rk[32]){ uint8_t i; uint16_t t;          /* rk[28..31] given -> fills rk[0..27] */
    for (i = 31; i >= 4; i--) { t = U16(ROR(rk[i-1], 3) ^ rk[i-3] ^ (ROL(rk[i-1], 1) & ROL(rk[i-1], 8))); t = U16(t ^ ROR(t, 1)); rk[i-4] = U16(rk[i] ^ t ^ 0xFFFCu ^ (uint16_t)((Z0_28 >> (i - 4)) & 1u)); } }
void ks_null(const uint16_t mk[4], uint16_t rk[32]){ uint8_t i; for (i = 0; i < 4; i++) rk[i] = mk[i]; }
