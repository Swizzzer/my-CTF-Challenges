import gmpy2
from Crypto.Util.number import isPrime, bytes_to_long
from sympy.ntheory import sqrt_mod
from sympy.ntheory.modular import crt
from secret import p, q, r, pp
import os


def oracle(x):
  root_p = sqrt_mod(x, p)
  root_q = sqrt_mod(x, q)
  root_r = sqrt_mod(x, r)
  if root_p is None or root_q is None or root_r is None:
    return "🤐"
  ans, _ = crt([p, q, r], [root_p, root_q, root_r])
  return int(ans)


assert p == pp**2 + 3 * pp + 3 and q == pp**2 + 5 * pp + 7
assert isPrime(p) and isPrime(q) and isPrime(r)

m = bytes_to_long(os.getenv("FLAG", "LilacCTF{fake_flag}").encode().strip())
n = p * q * r
e = 65537
c = pow(m, e, n)

print(f"{n = }")
print(f"{c = }")

while True:
  x = int(input("🧭 > "))
  _, is_psq = gmpy2.iroot(x, 2)
  assert not is_psq, "👿"
  assert 80 < x < 100
  print(oracle(x))
