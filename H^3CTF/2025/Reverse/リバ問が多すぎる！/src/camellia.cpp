#include "camellia.hpp"

#include <algorithm>
#include <array>
#include <cstring>
#include <stdexcept>

namespace {

static constexpr uint64_t sigma1 = 0xA09E667F3BCC908BULL;
static constexpr uint64_t sigma2 = 0xB67AE8584CAA73B2ULL;
static constexpr uint64_t sigma3 = 0xC6EF372FE94F82BEULL;
static constexpr uint64_t sigma4 = 0x54FF53A5F1D36F1CULL;
static constexpr uint64_t sigma5 = 0x10E527FADE682D1DULL;
static constexpr uint64_t sigma6 = 0xB05688C2B3E6C1FDULL;

static constexpr uint8_t SBOX1[256] = {
    0x70, 0x82, 0x2c, 0xec, 0xb3, 0x27, 0xc0, 0xe5, 0xe4, 0x85, 0x57, 0x35,
    0xea, 0x0c, 0xae, 0x41, 0x23, 0xef, 0x6b, 0x93, 0x45, 0x19, 0xa5, 0x21,
    0xed, 0x0e, 0x4f, 0x4e, 0x1d, 0x65, 0x92, 0xbd, 0x86, 0xb8, 0xaf, 0x8f,
    0x7c, 0xeb, 0x1f, 0xce, 0x3e, 0x30, 0xdc, 0x5f, 0x5e, 0xc5, 0x0b, 0x1a,
    0xa6, 0xe1, 0x39, 0xca, 0xd5, 0x47, 0x5d, 0x3d, 0xd9, 0x01, 0x5a, 0xd6,
    0x51, 0x56, 0x6c, 0x4d, 0x8b, 0x0d, 0x9a, 0x66, 0xfb, 0xcc, 0xb0, 0x2d,
    0x74, 0x12, 0x2b, 0x20, 0xf0, 0xb1, 0x84, 0x99, 0xdf, 0x4c, 0xcb, 0xc2,
    0x34, 0x7e, 0x76, 0x05, 0x6d, 0xb7, 0xa9, 0x31, 0xd1, 0x17, 0x04, 0xd7,
    0x14, 0x58, 0x3a, 0x61, 0xde, 0x1b, 0x11, 0x1c, 0x32, 0x0f, 0x9c, 0x16,
    0x53, 0x18, 0xf2, 0x22, 0xfe, 0x44, 0xcf, 0xb2, 0xc3, 0xb5, 0x7a, 0x91,
    0x24, 0x08, 0xe8, 0xa8, 0x60, 0xfc, 0x69, 0x50, 0xaa, 0xd0, 0xa0, 0x7d,
    0xa1, 0x89, 0x62, 0x97, 0x54, 0x5b, 0x1e, 0x95, 0xe0, 0xff, 0x64, 0xd2,
    0x10, 0xc4, 0x00, 0x48, 0xa3, 0xf7, 0x75, 0xdb, 0x8a, 0x03, 0xe6, 0xda,
    0x09, 0x3f, 0xdd, 0x94, 0x87, 0x5c, 0x83, 0x02, 0xcd, 0x4a, 0x90, 0x33,
    0x73, 0x67, 0xf6, 0xf3, 0x9d, 0x7f, 0xbf, 0xe2, 0x52, 0x9b, 0xd8, 0x26,
    0xc8, 0x37, 0xc6, 0x3b, 0x81, 0x96, 0x6f, 0x4b, 0x13, 0xbe, 0x63, 0x2e,
    0xe9, 0x79, 0xa7, 0x8c, 0x9f, 0x6e, 0xbc, 0x8e, 0x29, 0xf5, 0xf9, 0xb6,
    0x2f, 0xfd, 0xb4, 0x59, 0x78, 0x98, 0x06, 0x6a, 0xe7, 0x46, 0x71, 0xba,
    0xd4, 0x25, 0xab, 0x42, 0x88, 0xa2, 0x8d, 0xfa, 0x72, 0x07, 0xb9, 0x55,
    0xf8, 0xee, 0xac, 0x0a, 0x36, 0x49, 0x2a, 0x68, 0x3c, 0x38, 0xf1, 0xa4,
    0x40, 0x28, 0xd3, 0x7b, 0xbb, 0xc9, 0x43, 0xc1, 0x15, 0xe3, 0xad, 0xf4,
    0x77, 0xc7, 0x80, 0x9e,
};

static uint8_t SBOX2[256];
static uint8_t SBOX3[256];
static uint8_t SBOX4[256];

inline uint8_t rotl8(uint8_t x, unsigned r) {
  r &= 7u;
  return static_cast<uint8_t>((x << r) | (x >> (8 - r)));
}

void init_sboxes_once() {
  static bool inited = false;
  if (inited)
    return;
  for (int i = 0; i < 256; ++i) {
    uint8_t v = SBOX1[i];
    SBOX2[i] = rotl8(v, 1);
    SBOX3[i] = rotl8(v, 7);
    SBOX4[i] = SBOX1[rotl8(static_cast<uint8_t>(i), 1)];
  }
  inited = true;
}

inline uint64_t be64_load(const uint8_t *p) {
  return (static_cast<uint64_t>(p[0]) << 56) |
         (static_cast<uint64_t>(p[1]) << 48) |
         (static_cast<uint64_t>(p[2]) << 40) |
         (static_cast<uint64_t>(p[3]) << 32) |
         (static_cast<uint64_t>(p[4]) << 24) |
         (static_cast<uint64_t>(p[5]) << 16) |
         (static_cast<uint64_t>(p[6]) << 8) | static_cast<uint64_t>(p[7]);
}

inline void be64_store(uint8_t *p, uint64_t v) {
  p[0] = static_cast<uint8_t>(v >> 56);
  p[1] = static_cast<uint8_t>(v >> 48);
  p[2] = static_cast<uint8_t>(v >> 40);
  p[3] = static_cast<uint8_t>(v >> 32);
  p[4] = static_cast<uint8_t>(v >> 24);
  p[5] = static_cast<uint8_t>(v >> 16);
  p[6] = static_cast<uint8_t>(v >> 8);
  p[7] = static_cast<uint8_t>(v);
}

inline uint32_t rotl32(uint32_t x, unsigned r) {
  r &= 31u;
  return (x << r) | (x >> (32 - r));
}

}

Camellia::Camellia(const std::vector<uint8_t> &key) {
  init_sboxes_once();

  klen_ = static_cast<int>(key.size());
  if (!(klen_ == 16 || klen_ == 24 || klen_ == 32)) {
    throw std::invalid_argument("camellia: invalid key size");
  }

  uint64_t kl[2] = {0, 0};
  uint64_t kr[2] = {0, 0};
  uint64_t ka[2] = {0, 0};
  uint64_t kb[2] = {0, 0};

  kl[0] = be64_load(&key[0]);
  kl[1] = be64_load(&key[8]);

  if (klen_ == 24) {
    kr[0] = be64_load(&key[16]);
    kr[1] = ~kr[0];
  } else if (klen_ == 32) {
    kr[0] = be64_load(&key[16]);
    kr[1] = be64_load(&key[24]);
  }

  uint64_t d1 = (kl[0] ^ kr[0]);
  uint64_t d2 = (kl[1] ^ kr[1]);

  d2 ^= F(d1, sigma1);
  d1 ^= F(d2, sigma2);

  d1 ^= kl[0];
  d2 ^= kl[1];
  d2 ^= F(d1, sigma3);
  d1 ^= F(d2, sigma4);
  ka[0] = d1;
  ka[1] = d2;
  d1 = (ka[0] ^ kr[0]);
  d2 = (ka[1] ^ kr[1]);
  d2 ^= F(d1, sigma5);
  d1 ^= F(d2, sigma6);
  kb[0] = d1;
  kb[1] = d2;

  auto R = [](const uint64_t a[2], unsigned rot, uint64_t &hi, uint64_t &lo) {
    Camellia::rotl128(a, rot, hi, lo);
  };

  if (klen_ == 16) {
    R(kl, 0, kw_[1], kw_[2]);

    R(ka, 0, k_[1], k_[2]);
    R(kl, 15, k_[3], k_[4]);
    R(ka, 15, k_[5], k_[6]);

    R(ka, 30, ke_[1], ke_[2]);

    R(kl, 45, k_[7], k_[8]);
    {
      uint64_t hi, lo;
      R(ka, 45, hi, lo);
      k_[9] = hi;
      (void)lo;
    }
    {
      uint64_t hi, lo;
      R(kl, 60, hi, lo);
      k_[10] = lo;
      (void)hi;
    }
    R(ka, 60, k_[11], k_[12]);

    R(kl, 77, ke_[3], ke_[4]);

    R(kl, 94, k_[13], k_[14]);
    R(ka, 94, k_[15], k_[16]);
    R(kl, 111, k_[17], k_[18]);

    R(ka, 111, kw_[3], kw_[4]);
  } else {
    R(kl, 0, kw_[1], kw_[2]);

    R(kb, 0, k_[1], k_[2]);
    R(kr, 15, k_[3], k_[4]);
    R(ka, 15, k_[5], k_[6]);

    R(kr, 30, ke_[1], ke_[2]);

    R(kb, 30, k_[7], k_[8]);
    R(kl, 45, k_[9], k_[10]);
    R(ka, 45, k_[11], k_[12]);

    R(kl, 60, ke_[3], ke_[4]);

    R(kr, 60, k_[13], k_[14]);
    R(kb, 60, k_[15], k_[16]);
    R(kl, 77, k_[17], k_[18]);

    R(ka, 77, ke_[5], ke_[6]);

    R(kr, 94, k_[19], k_[20]);
    R(ka, 94, k_[21], k_[22]);
    R(kl, 111, k_[23], k_[24]);

    R(kb, 111, kw_[3], kw_[4]);
  }
}

void __attribute((__annotate__(
    ("indirectcall,flattening,aliasaccess,boguscfg,substitution"))))
Camellia::EncryptBlock(uint8_t dst[BlockSize],
                       const uint8_t src[BlockSize]) const {
  uint64_t d1 = be64_load(src);
  uint64_t d2 = be64_load(src + 8);

  d1 ^= kw_[1];
  d2 ^= kw_[2];

  d2 ^= F(d1, k_[1]);
  d1 ^= F(d2, k_[2]);
  d2 ^= F(d1, k_[3]);
  d1 ^= F(d2, k_[4]);
  d2 ^= F(d1, k_[5]);
  d1 ^= F(d2, k_[6]);

  d1 = FL(d1, ke_[1]);
  d2 = FLInv(d2, ke_[2]);

  d2 ^= F(d1, k_[7]);
  d1 ^= F(d2, k_[8]);
  d2 ^= F(d1, k_[9]);
  d1 ^= F(d2, k_[10]);
  d2 ^= F(d1, k_[11]);
  d1 ^= F(d2, k_[12]);

  d1 = FL(d1, ke_[3]);
  d2 = FLInv(d2, ke_[4]);

  d2 ^= F(d1, k_[13]);
  d1 ^= F(d2, k_[14]);
  d2 ^= F(d1, k_[15]);
  d1 ^= F(d2, k_[16]);
  d2 ^= F(d1, k_[17]);
  d1 ^= F(d2, k_[18]);
  asm("backend-obfu");
  if (klen_ > 16) {
    d1 = FL(d1, ke_[5]);
    d2 = FLInv(d2, ke_[6]);

    d2 ^= F(d1, k_[19]);
    d1 ^= F(d2, k_[20]);
    d2 ^= F(d1, k_[21]);
    d1 ^= F(d2, k_[22]);
    d2 ^= F(d1, k_[23]);
    d1 ^= F(d2, k_[24]);
  }

  d2 ^= kw_[3];
  d1 ^= kw_[4];

  be64_store(dst, d2);
  be64_store(dst + 8, d1);
}

uint64_t __attribute((
    __annotate__(("indirectcall,indirectbr,aliasaccess,boguscfg,flattening"))))
Camellia::F(uint64_t fin, uint64_t ke) {
  uint64_t x = fin ^ ke;
  uint8_t t1 = SBOX1[static_cast<uint8_t>(x >> 56)];
  uint8_t t2 = SBOX2[static_cast<uint8_t>(x >> 48)];
  uint8_t t3 = SBOX3[static_cast<uint8_t>(x >> 40)];
  uint8_t t4 = SBOX4[static_cast<uint8_t>(x >> 32)];
  uint8_t t5 = SBOX2[static_cast<uint8_t>(x >> 24)];
  uint8_t t6 = SBOX3[static_cast<uint8_t>(x >> 16)];
  uint8_t t7 = SBOX4[static_cast<uint8_t>(x >> 8)];
  uint8_t t8 = SBOX1[static_cast<uint8_t>(x)];
  uint8_t y1 = t1 ^ t3 ^ t4 ^ t6 ^ t7 ^ t8;
  uint8_t y2 = t1 ^ t2 ^ t4 ^ t5 ^ t7 ^ t8;
  uint8_t y3 = t1 ^ t2 ^ t3 ^ t5 ^ t6 ^ t8;
  uint8_t y4 = t2 ^ t3 ^ t4 ^ t5 ^ t6 ^ t7;
  uint8_t y5 = t1 ^ t2 ^ t6 ^ t7 ^ t8;
  uint8_t y6 = t2 ^ t3 ^ t5 ^ t7 ^ t8;
  uint8_t y7 = t3 ^ t4 ^ t5 ^ t6 ^ t8;
  uint8_t y8 = t1 ^ t4 ^ t5 ^ t6 ^ t7;
  return (static_cast<uint64_t>(y1) << 56) | (static_cast<uint64_t>(y2) << 48) |
         (static_cast<uint64_t>(y3) << 40) | (static_cast<uint64_t>(y4) << 32) |
         (static_cast<uint64_t>(y5) << 24) | (static_cast<uint64_t>(y6) << 16) |
         (static_cast<uint64_t>(y7) << 8) | static_cast<uint64_t>(y8);
}

uint64_t Camellia::FL(uint64_t flin, uint64_t ke) {
  uint32_t x1 = static_cast<uint32_t>(flin >> 32);
  uint32_t x2 = static_cast<uint32_t>(flin & 0xffffffffu);
  uint32_t k1 = static_cast<uint32_t>(ke >> 32);
  uint32_t k2 = static_cast<uint32_t>(ke & 0xffffffffu);
  x2 ^= rotl32(x1 & k1, 1);
  x1 ^= (x2 | k2);
  return (static_cast<uint64_t>(x1) << 32) | static_cast<uint64_t>(x2);
}

uint64_t Camellia::FLInv(uint64_t flin, uint64_t ke) {
  uint32_t y1 = static_cast<uint32_t>(flin >> 32);
  uint32_t y2 = static_cast<uint32_t>(flin & 0xffffffffu);
  uint32_t k1 = static_cast<uint32_t>(ke >> 32);
  uint32_t k2 = static_cast<uint32_t>(ke & 0xffffffffu);
  y1 ^= (y2 | k2);
  y2 ^= rotl32(y1 & k1, 1);
  return (static_cast<uint64_t>(y1) << 32) | static_cast<uint64_t>(y2);
}

void Camellia::rotl128(const uint64_t in[2], unsigned rot, uint64_t &out_hi,
                       uint64_t &out_lo) {
  rot %= 128u;
  uint64_t hi = in[0];
  uint64_t lo = in[1];
  if (rot == 0) {
    out_hi = hi;
    out_lo = lo;
    return;
  }
  if (rot == 64) {
    out_hi = lo;
    out_lo = hi;
    return;
  }
  if (rot < 64) {
    out_hi = (hi << rot) | (lo >> (64 - rot));
    out_lo = (lo << rot) | (hi >> (64 - rot));
    return;
  }
  unsigned r = rot - 64;
  out_hi = (lo << r) | (hi >> (64 - r));
  out_lo = (hi << r) | (lo >> (64 - r));
}

std::vector<uint8_t> __attribute((
    __annotate__(("indirectcall,indirectbr,aliasaccess,boguscfg,linearmba"))))
CamelliaStreamEncrypt(const std::vector<uint8_t> &key,
                      const std::vector<uint8_t> &iv,
                      const std::vector<uint8_t> &plaintext) {

  if (!(key.size() == 16 || key.size() == 24 || key.size() == 32)) {
    throw std::invalid_argument("CamelliaStreamEncrypt: invalid key size");
  }
  if (iv.size() != Camellia::BlockSize) {
    throw std::invalid_argument("CamelliaStreamEncrypt: IV must be 16 bytes");
  }

  Camellia cam(key);
  std::vector<uint8_t> ciphertext(plaintext.size());
  if (plaintext.empty()) {
    return ciphertext;
  }

  std::array<uint8_t, Camellia::BlockSize> counter{};
  std::memcpy(counter.data(), iv.data(), Camellia::BlockSize);

  std::array<uint8_t, Camellia::BlockSize> keystream{};
  size_t offset = 0;

  while (offset < plaintext.size()) {
    cam.EncryptBlock(keystream.data(), counter.data());
    size_t chunk = std::min(Camellia::BlockSize, plaintext.size() - offset);
    for (size_t i = 0; i < chunk; ++i) {
      ciphertext[offset + i] = plaintext[offset + i] ^ keystream[i];
    }

    for (int idx = static_cast<int>(Camellia::BlockSize) - 1; idx >= 0; --idx) {
      if (++counter[idx] != 0) {
        break;
      }
    }

    offset += chunk;
  }

  return ciphertext;
}

std::array<uint8_t, 4> __attribute((
    __annotate__(("indirectcall,aliasaccess,boguscfg,linearmba"))))
CamelliaHash(const std::vector<uint8_t> &data) {
  static const std::vector<uint8_t> kHashKey = {
      0x00, 0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77,
      0x88, 0x99, 0xaa, 0xbb, 0xcc, 0xdd, 0xee, 0xff};
  static const std::vector<uint8_t> kHashIv = {
      0xfe, 0xdc, 0xba, 0x98, 0x76, 0x54, 0x32, 0x10,
      0x01, 0x23, 0x45, 0x67, 0x89, 0xab, 0xcd, 0xef};

  std::vector<uint8_t> message;
  message.reserve(data.size() + sizeof(uint32_t));
  message.insert(message.end(), data.begin(), data.end());

  uint32_t len = static_cast<uint32_t>(data.size());
  for (int shift = 0; shift < 32; shift += 8) {
    message.push_back(static_cast<uint8_t>((len >> shift) & 0xffu));
  }

  auto encrypted = CamelliaStreamEncrypt(kHashKey, kHashIv, message);

  std::array<uint8_t, 4> digest{0xA3, 0x1F, 0x5B, 0xC7};
  uint8_t carry = 0;
  for (size_t i = 0; i < encrypted.size(); ++i) {
    uint8_t mixed =
        static_cast<uint8_t>(encrypted[i] ^ carry ^ static_cast<uint8_t>(i));
    size_t idx = i % digest.size();
    digest[idx] ^= mixed;
    digest[(idx + 1) % digest.size()] =
        static_cast<uint8_t>(digest[(idx + 1) % digest.size()] + mixed);
    carry = static_cast<uint8_t>(carry + encrypted[i] + mixed);
  }

  return digest;
}

std::vector<std::array<uint8_t, 4>>
CamelliaHashVector(const std::vector<uint8_t> &data) {
  std::vector<std::array<uint8_t, 4>> hashes;
  hashes.reserve(data.size());

  std::vector<uint8_t> prefix;
  prefix.reserve(data.size());

  for (uint8_t byte : data) {
    prefix.push_back(byte);
    hashes.push_back(CamelliaHash(prefix));
  }

  return hashes;
}
