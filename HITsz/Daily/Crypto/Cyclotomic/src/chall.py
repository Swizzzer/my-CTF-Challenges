from Crypto.Util.number import *

p, q = getPrime(512), getPrime(512)
r = p**4 - p**3 + p**2 - p + 1
m = bytes_to_long(open("flag.txt","rb").read().strip())
print(m^p)
print(p*q*r)