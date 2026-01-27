from sage.all import GF, EllipticCurve, polygen, PolynomialRing, Zmod
from Crypto.Util.number import getPrime, isPrime, bytes_to_long
import random


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


def transform(secret: int):
  while True:
    try:
      p = getSafePrime(384)
      x = polygen(GF(p))
      F = GF(p**2, "i", modulus=x**2 + 1)
      j = F(secret)
      E = EllipticCurve(j=j)
      kerl = E(0).division_points(5)[1:]
      E2 = E.isogeny(random.choice(kerl)).codomain()
      return p, E2.j_invariant()
    except Exception as _:
      continue


if __name__ == "__main__":
  m = bytes_to_long(open("flag.txt", "rb").read().strip())
  p_m, (re, im) = transform(m)
  p = getSafePrime(512)
  pt = pow(int(re + im), -1, p**2)

  assert m.bit_length() < 384

  # fmt:off
  exps = [(getPrime(384) - 1) * p for _ in range(8)] + [getPrime(384) * (p - 1) for _ in range(8)]
  # fmt: on
  ct = encrypt(pt, p, exps)
  print(p_m)
  print(exps)
  print(ct)
