from Crypto.Util.number import long_to_bytes
from ast import literal_eval

M = literal_eval(open("output.txt").read())
flag_bits = "".join(str((c - 1) ^ 1) for c in M[0][1:])
flag = int(flag_bits, 2)
print(long_to_bytes(flag))
