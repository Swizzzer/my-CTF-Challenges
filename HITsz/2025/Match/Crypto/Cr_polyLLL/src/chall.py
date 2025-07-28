from functools import reduce
from secrets import randbelow, choice
from Crypto.Util.number import getPrime
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from hashlib import sha3_256

flag = open("flag.txt", "rb").read().strip()
nn, n = 512, 256
p = getPrime(256)
points = [randbelow(p) for _ in range(n)]
coeffs = list(choice([-1, 1]) for _ in range(nn))
results = [reduce(lambda acc, c: (acc * k + c) % p, coeffs, 0) for k in points]
key = sha3_256("".join(str(c) for c in coeffs).encode()).digest()
aes = AES.new(key=key, mode=AES.MODE_ECB)
print(f"{p = }")
print(f"{points = }")
print(f"{results = }")
print(f"ct = {aes.encrypt(pad(flag, 16))}")
