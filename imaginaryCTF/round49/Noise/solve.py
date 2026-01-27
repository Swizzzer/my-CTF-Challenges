from Crypto.Util.number import *
from sage.all import *
import gmpy2


n = QQ(n)
e = QQ(e)
cf = continued_fraction(gift / n)
for i in range(1, 2000):
    k = cf.numerator(i)
    d = cf.denominator(i)
    if gcd(d, n) == d and d != n:
        print(d)
        break

p, q = d, n // d
phin = (p - 1) * (q - 1)
d = gmpy2.invert(int(e), int(phin))
print(long_to_bytes(pow(c, d, int(n))))
