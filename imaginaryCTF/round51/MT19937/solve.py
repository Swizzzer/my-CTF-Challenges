from randcrack import RandCrack
from Crypto.Util.number import bytes_to_long, long_to_bytes

rc = RandCrack()
ct = open("ciphertext", "rb").read()
pt = open("msg.txt", "rb").read()
for i in range(624):
    rc.submit(
        bytes_to_long(pt[i * 4 : i * 4 + 4]) ^ bytes_to_long(ct[i * 4 : i * 4 + 4])
    )
for i in range(624, len(pt) // 4):
    rc.predict_getrandbits(32)
flag = b""
for i in range(len(pt) // 4, len(ct) // 4):
    flag += long_to_bytes(
        rc.predict_getrandbits(32) ^ bytes_to_long(ct[i * 4 : i * 4 + 4])
    )
print(flag)
