from Crypto.Util.number import *
import random

p, q = getPrime(2048), getPrime(1024)
n = p * q
e = 0x10001

noisy, noisier = random.randint(1, 2**256), random.randint(1, 2**512)

with open("flag.txt", "rb") as f:
    flag = f.read().strip()

m = bytes_to_long(flag)
c = pow(m, e, n)

gift = noisy * p + noisier

print(f"{n=}")
print(f"{c=}")
print(f"{e=}")
print(f"{gift=}")
