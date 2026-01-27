import random
from Crypto.Util.number import long_to_bytes, bytes_to_long
from secret import seed, flag

msg = open("msg.txt", "rb").read()

stream1 = random.Random(seed)
stream2 = random.Random(flag)

msg += flag
c = b""

assert len(seed) == 32
assert len(msg) % 4 == 0

for i in range(len(msg) // 4):
    c += long_to_bytes(
        bytes_to_long(msg[i * 4 : i * 4 + 4])
        ^ stream1.getrandbits(32)
        ^ stream2.getrandbits(32)
    ).rjust(4, b"\x00")

open("ciphertext", "wb").write(c)
