from sage.all import PolynomialRing, Zmod
from Crypto.Util.number import getPrime
from random import SystemRandom

random = SystemRandom()


def otp(bitlen: int) -> int:
  half_len = bitlen // 2
  left = ["0"] * (half_len - 1)
  right = ["1"] * (half_len + 1)
  bits = left + right
  random.shuffle(bits)
  return int("".join(bits), 2)


def get_exps(msg, nums):
  exps = []
  blen = len(msg) * 8
  m = int.from_bytes(msg, "big")
  for _ in range(nums):
    padding = otp(blen)
    exps.append(m ^ padding)
  return exps


if __name__ == "__main__":
  flag = open("flag.txt", "rb").read().strip()
  assert flag.startswith(b"LilacCTF{") and flag.endswith(b"}")
  flag = flag[9:-1]
  exps = get_exps(flag, 384)
  p = getPrime(384)
  R = PolynomialRing(Zmod(p**3), names="x,y")
  x, y = R.gens()
  I = R.ideal([x**3 + y**5 + 13 * x * y - 37, y**3 + x**5 + 37 * x - 13])  # noqa: E741
  S = R.quotient(I, names=("x,y"))
  g = S(x**2 + y**2 + 13 * x + 37 * y + 1337)
  print(p)
  for e in exps:
    print(g**e)
