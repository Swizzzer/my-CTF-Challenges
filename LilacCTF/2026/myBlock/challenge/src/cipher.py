POLY = 0x1002D
ROUNDS = 8


class myFeistel:
  def __init__(self, subkeys):
    assert len(subkeys) == ROUNDS
    self.subkeys = subkeys

  @staticmethod
  def add(a, b):
    return a ^ b

  @staticmethod
  def mul(a, b):
    res = 0
    for i in range(16):
      if (b >> i) & 1:
        res ^= a

      high_bit = (a >> 15) & 1
      a = (a << 1) & 0xFFFF
      if high_bit:
        a ^= POLY & 0xFFFF
    return res

  @staticmethod
  def cube(a):
    sq = myFeistel.mul(a, a)
    return myFeistel.mul(sq, a)

  def enc_block(self, L, R):
    for k in self.subkeys:
      T = self.cube(L ^ k)
      new_R = R ^ T
      new_L = L
      L, R = new_R, new_L

    return L, R

  def enc(self, data):
    return [self.enc_block(l, r) for l, r in data]  # noqa: E741
