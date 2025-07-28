from Crypto.Util.number import bytes_to_long, getPrime

flag = open("flag.txt", "rb").read().strip()
m = bytes_to_long(flag)
p = getPrime(256)
print(f"{p}")
print(f"{(m**30+405*m**2-4*m+1)%(p**3)}")
