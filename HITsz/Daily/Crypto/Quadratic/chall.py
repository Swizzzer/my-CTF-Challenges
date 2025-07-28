from sage.all import *
from random import SystemRandom
from Crypto.Util.number import *

rnd = SystemRandom()

p = 12863248358800754159071191498818956211257545331519984499403714771938500177987645713025771946209624419371350847486148516168726911506167238769202544818634601
rabbit = 2099115095612422634187926806804165900090922261548422887498250579740252262231499738954380920175419935784438802535206625589427448875763954989886848142679815
flag = open("flag.txt", "rb").read().strip()
flag_bin = bin(bytes_to_long(flag))[2:]
output = []
for c in flag_bin:
    e = rnd.randrange(2, p) | 1
    if c == "0":
        output.append(pow(rabbit, e, p))
    else:
        output.append(pow(rabbit, e-1, p))
print(p)
print(output)
