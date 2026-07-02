from sage.all import *
from Crypto.Util.number import inverse, long_to_bytes

N = 
c = 
e = 65537
F = Zmod(N)
while True:
  x, y = (F**2).random_element()
  u, v, _ = EllipticCurve([0, y**2 - x**3])(x, y) * N
  if int(gcd([u])) > 1:
    break

p = int(gcd([u]))
q = N // p
phi = (p - 1) * (q - 1)
d = inverse(e, phi)
m = pow(c, d, N)
print(long_to_bytes(m).decode())
