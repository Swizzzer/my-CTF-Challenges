from Crypto.Util.number import * 
import ast
from sage.all import *
with open("output.txt") as f:
    Primes = ast.literal_eval(f.readline())
    out = ast.literal_eval(f.readline())
res = ""
for i in out:
    M = Matrix(ZZ,33,33)
    for j in range(32):
        M[j,j] = 1
        M[j,-1] = Primes[j]
    M[32,-1] = i
    L = M.LLL()
    if all(int(c) == 0 or int(c) == -1 for c in L[0]):
        res += "1"
    else: 
        res += "0"
print(long_to_bytes(int(res,2)))

