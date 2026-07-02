from secrets import randbits, choice
from Crypto.Util.number import isPrime, getPrime, bytes_to_long
import string

def pad(m: bytes, alphabet: bytes):
  return m + bytes([choice(alphabet) for _ in range(64 - len(m))])


flag = open("flag.txt").read().strip().encode()
assert flag.startswith(b"HITCTF{") and flag.endswith(b"}")

e = 65537
bits = 1024
alphabet = (string.ascii_letters + string.digits).encode()
B = int(input("🎫 > "))
assert 1 < B < bits, "🤬"

while True:
  odd = randbits(bits - 1) | 1
  p = (B * odd**2 + 2) // 8
  if isPrime(p):
    break

q = getPrime(bits)
assert p != q, "🤬"
n = p * q

m = bytes_to_long(pad(flag, alphabet))
c = pow(m, e, n)

print(f"{n = }")
print(f"{e = }")
print(f"{c = }")
