from sage.all import *
import math
import Crypto.Util.number as  cn
import ast

with open("output.txt") as f:
    r = ast.literal_eval(f.readline())
    ct = ast.literal_eval(f.readline())
 
x = int(GF(r)(-16).nth_root(3))
M = Matrix([[x,1],[r,0]])           
a, b = M.LLL()[0]
p = int(abs(a))
q = int(abs(b))
print(f"p = {a}")
print(f"q = {b}")
assert r == p**3+16*q**3
assert cn.isPrime(p) and cn.isPrime(q)
n = p*q*r
e = 65537
phi = (p-1) * (q-1) * (r-1)
d = cn.inverse(e, phi)
res = pow(ct, d, n)
print(cn.long_to_bytes(res))