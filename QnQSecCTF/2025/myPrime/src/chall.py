from sage.all import EllipticCurve, GF
from secrets import randbits
from Crypto.Util.number import isPrime, long_to_bytes, getPrime
from Crypto.Cipher import AES


def genPrime(bits: int) -> int:
  while True:
    pp = randbits(bits // 2)
    p = pp**2 + pp + 3
    if isPrime(p):
      return p


p = genPrime(512)
mod = getPrime(256)
E = EllipticCurve(GF(p), [-3391094784, 77986137112576])
kerl = E(0).division_points(3)
phi = E.isogeny(kerl[-1])
E_ = phi.codomain()
gift = int(E_.order()) % mod
m = open("flag.txt", "rb").read().strip()
key = long_to_bytes(p)[:16]
cipher = AES.new(key, AES.MODE_CTR)
c = cipher.encrypt(m)
print(f"{gift = }")
print(f"{mod = }")
print(f"{c = }")
print(f"nonce = {cipher.nonce}")