from Crypto.Util.number import * 
from secrets import randbits
def getRandSum():
    res = 0
    for _ in range(32):
        res += randbits(1)*randbits(256)
    return res
def getPrimeSum(Primes):
    res = 0
    for i in range(32):
        res += randbits(1)*Primes[i]
    return res


flag = open("flag.txt", "rb").read().strip()
m = bin(bytes_to_long(flag))[2:]
Primes = []
for _ in range(32):
    Primes.append(getPrime(256))
out = []
for c in m:
    if c == "0":
        out.append(getRandSum())
    else:
        out.append(getPrimeSum(Primes))

print(f"{Primes}")
print(f"{out}")
