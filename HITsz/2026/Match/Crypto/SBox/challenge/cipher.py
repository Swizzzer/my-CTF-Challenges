from random import SystemRandom

ROTS = (16, 16, 8, 8, 16, 16, 24, 24)


def xor(left, right):
  return bytes(a ^ b for a, b in zip(left, right))


def rotr32(word, bits):
  value = int.from_bytes(word, "big")
  value = ((value >> bits) | (value << (32 - bits))) & 0xFFFFFFFF
  return value.to_bytes(4, "big")


class Kumiko:
  def __init__(self, key, rounds=16):
    self.sboxes = [self._sbox() for _ in range(rounds // 8)]
    self.k0, self.k1 = key[:8], key[8:]

  @staticmethod
  def _sbox():
    rng = SystemRandom()
    cols = [rng.sample(range(256), 256) for _ in range(4)]
    return [bytes(cols[j][i] for j in range(4)) for i in range(256)]

  def enc_block(self, block):
    state = xor(block, self.k0)
    left, right = state[:4], state[4:]
    for sbox in self.sboxes:
      for bits in ROTS:
        left, right = rotr32(right, bits), xor(left, sbox[right[-1]])
    return xor(left + right, self.k1)

  def enc(self, plaintext):
    pad = 8 - len(plaintext) % 8
    plaintext += bytes([pad]) * pad
    return b"".join(
      self.enc_block(plaintext[i : i + 8]) for i in range(0, len(plaintext), 8)
    )
