from Crypto.Util.number import getPrime

m = open("flag.txt", "r").read().strip()
ps = [getPrime(512) for _ in range(len(m))]
ct = 0
for pt, p in zip(m, ps):
    ct += ord(pt) * p
print(f"{ps}")
print(f"{ct}")
