from Crypto.Util.number import getPrime, bytes_to_long, isPrime
from sage.all import PolynomialRing, Zmod


def getSafePrime(bits: int) -> int:
  while True:
    p = getPrime(bits - 1)
    q = 2 * p + 1
    if isPrime(q):
      return q


def encrypt(m: int, p: int, exponents: list[int]):
  modulus = p**3
  y = PolynomialRing(Zmod(modulus), "x").quotient("x**3 + x + 1", "y").gen()
  g = 13 * y + 37
  powers = [pow(m, e, modulus) for e in exponents]
  return [g**e for e in powers]


if __name__ == "__main__":
  with open("flag.txt", "rb") as f:
    m = bytes_to_long(f.read().strip())
  p = getSafePrime(512)
  assert p < m < p**2
  # fmt:off
  exps = [(getPrime(384) - 1) * p for _ in range(8)] + [getPrime(384) * (p - 1) for _ in range(8)]
  # fmt: on
  ct = encrypt(m, p, exps)
  print(exps)
  print(ct)
