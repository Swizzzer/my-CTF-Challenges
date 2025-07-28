from Crypto.Util.number import *
from os import urandom

def gen_keys():
    while True:
        a = getPrime(512)
        b = getPrime(512)
        p = a**3 + 16*b**3

        if isPrime(p):
            return a, b, p


def pad(msg: bytes) -> bytes:
    return msg + urandom(192)


p, q, r = gen_keys()
e = 65537
n = p*q*r

flag = pad(open("flag.txt", "rb").read().strip())

ct = pow(bytes_to_long(flag), e, n)
print(f"{r}")
print(f"{ct}")
