from Crypto.Util.number import *
import ast
from sage.all import *
from tqdm import tqdm

with open("output.txt") as f:
    Primes = ast.literal_eval(f.readline())
    out = ast.literal_eval(f.readline())
res = ""
M = Matrix(ZZ, 65, 65)
for j in range(64):
    M[j, j] = 1
    M[j, -1] = Primes[j]
for i in tqdm(out, total=len(out)):
    M[64, -1] = i
    L = M.BKZ()
    if all(int(c) == 0 or int(c) == -1 for c in L[0]):
        res += "1"
    else:
        res += "0"
print(long_to_bytes(int(res, 2)))
