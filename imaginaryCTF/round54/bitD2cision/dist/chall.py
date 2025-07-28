from Crypto.Util.number import *
from random import SystemRandom
from sage.all import *

random = SystemRandom()
# BLS12-381 curve
p = 0x1a0111ea397fe69a4b1ba7b6434bacd764774b84f38512bf6730d2a0f6b0f6241eabfffeb153ffffb9feffffffffaaab
K = GF(p)
E = EllipticCurve(K, (0, 4))
flag = open("flag.txt", "rb").read().strip()
flag_bin = bin(bytes_to_long(flag))[2:].zfill(len(flag)*8)
assert flag.decode().startswith("ictf")
output = []
n = E.order()
sn = 52437899
s = n//sn**2
print(n)
for c in flag_bin:
    if c == "0":
        output.append(random.getrandbits(512) % p)
    else:
        P1 = s*E.random_element()
        P2 = s*E.random_element()
        output.append(P1.weil_pairing(P2, sn))

print(output)
