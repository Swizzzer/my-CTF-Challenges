from Crypto.Util.number import bytes_to_long
from gmpy2 import next_prime
from secrets import randbits

p = next_prime(randbits(256))
q = next_prime(p)
r = next_prime(q)
n = int(p * q * r)
m = bytes_to_long(open("flag.txt", "rb").read().strip())
c = pow(m, 0x10001, n)

print(f"{c=}")
print(f"{n=}")
