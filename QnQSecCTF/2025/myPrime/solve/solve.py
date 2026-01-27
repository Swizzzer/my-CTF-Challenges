from sage.all import *
from Crypto.Cipher import AES
from Crypto.Util.number import *

with open("output.txt") as f:
  exec(f.read())

PR = PolynomialRing(GF(mod), "x")
F = PolynomialRing(ZZ, "y")
x = PR.gen()
y = F.gen()
# p + 1 ± (2*pp + 1)
gift_poly = x**2 + x + 3 + 1 + 2 * x + 1 - gift
p_y = y**2 + y + 3
print(gift_poly.roots())
for r in gift_poly.roots():
  for i in range(2):
    if isPrime(int(p_y(int(r[0]) + i * mod))):
      p = int(p_y(int(r[0]) + i * mod))
      print(f"p = {p}")
      break

cipher = AES.new(long_to_bytes(p)[:16], AES.MODE_CTR, nonce=nonce)
msg = cipher.decrypt(c)
print(msg)