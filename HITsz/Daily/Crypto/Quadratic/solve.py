from sage.all import *
from Crypto.Util.number import *
lines = open("output.txt").readlines()
p = int(eval(lines[0]))
F = GF(p)
out = list(eval(lines[1]))


def is_quadratic_residue(a, p):
    if kronecker(a, p) != 1:
        return False
    return True


flag = ""
for i in range(len(out)):
    if is_quadratic_residue(out[i], p):
        flag += "1"
    else:
        flag += "0"
print(f"{p = }")
print(flag)
print(long_to_bytes(int(flag, 2)))
