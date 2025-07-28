from sage.all import *
import ast

with open("output.txt") as f:
    ps = ast.literal_eval(f.readline())
    ct = ast.literal_eval(f.readline())
n = len(ps)
M = Matrix(ZZ, n + 1, n + 1)
for i in range(n):
    M[i, i] = 1
    M[i, -1] = ps[i]
M[n, -1] = ct
L = M.LLL()
for c in L[0]:
    print(chr(abs(c)), end="")
print("\n")
