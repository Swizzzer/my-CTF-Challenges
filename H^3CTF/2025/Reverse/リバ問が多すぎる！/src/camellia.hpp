#pragma once

#include <array>
#include <cstdint>
#include <vector>

class Camellia {
public:
  static constexpr size_t BlockSize = 16;
  explicit Camellia(const std::vector<uint8_t> &key);
  void EncryptBlock(uint8_t dst[BlockSize], const uint8_t src[BlockSize]) const;

private:
  uint64_t kw_[5]{};
  uint64_t k_[25]{};
  uint64_t ke_[7]{};
  int klen_ = 0;

  static uint64_t F(uint64_t fin, uint64_t ke);
  static uint64_t FL(uint64_t flin, uint64_t ke);
  static uint64_t FLInv(uint64_t flin, uint64_t ke);

  static void rotl128(const uint64_t in[2], unsigned rot, uint64_t &out_hi,
                      uint64_t &out_lo);
};

std::vector<uint8_t>
CamelliaStreamEncrypt(const std::vector<uint8_t> &key,
                      const std::vector<uint8_t> &iv,
                      const std::vector<uint8_t> &plaintext);

std::array<uint8_t, 4>
CamelliaHash(const std::vector<uint8_t> &data);

std::vector<std::array<uint8_t, 4>>
CamelliaHashVector(const std::vector<uint8_t> &data);
