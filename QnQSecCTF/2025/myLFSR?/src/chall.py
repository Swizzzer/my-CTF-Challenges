from secrets import randbits
import os


def expand(n: int, base=3) -> list[int]:
  res = []
  while n:
    res.append(n % base)
    n //= base
  return res


class myLFSR:
  def __init__(self, key: list[int], mask: list[int]):
    assert all(0 <= x < 3 for x in key), "Key must be in range [0, 2]"
    assert all(0 <= x < 3 for x in mask), "Mask must be in range [0, 2]"
    assert len(key) == len(mask), "Key and mask must be of the same length"

    self.state = key
    self.mask = mask
    self.mod = 3

  def __call__(self) -> int:
    b = sum(s * m for s, m in zip(self.state, self.mask)) % self.mod
    output = self.state[0]
    self.state = self.state[1:] + [b]

    return output


class Cipher:
  def __init__(self, key: list[int], mask: list[int]):
    self.lfsr = myLFSR(key, mask)

  def encrypt(self, msg: bytes) -> bytes:
    pt = expand(int.from_bytes(msg, "big"))
    stream = [self.lfsr() for _ in range(len(pt))]
    ct = [a ^ b for a, b in zip(pt, stream)]
    return bytes(ct)


if __name__ == "__main__":
  flag = open("flag.txt", "rb").read().strip()
  KEY = expand(int.from_bytes(os.urandom(8), "big"))
  MASK = [randbits(256) % 3 for _ in range(len(KEY))]
  cipher = Cipher(KEY, MASK)
  gift = cipher.encrypt(b"\xff" * (len(KEY) // 3 + 3))
  ct = cipher.encrypt(flag)
  print(len(KEY))
  print(gift.hex())
  print(ct.hex())
