# copied from [tl2cents](https://blog.tanglee.top/2024/07/15/HITCON-CTF-2024-Qual-Crypto-Writeup.html#exploit-1)
import os
import ast
from sage.all import *
from tqdm import tqdm
import secrets
MASK1 = int(0x77E3816DD9E3627340D7EE76204ED9F9)
MASK2 = int(0x512E5CEC93B9AE8D6E28E2AB78B8432B)

with open("output.txt", "r") as f:
    gift = ast.literal_eval('"' + f.readline().strip() + '"')
    ct = ast.literal_eval('"' + f.readline().strip() + '"')
gift = bytes.fromhex(gift)
ct = bytes.fromhex(ct)

    
class LFSRSymbolic:
    def __init__(self, n, key, mask):
        assert len(key) == n, "Error: the key must be of exactly 128 bits."
        self.state = key
        self.mask = mask
        self.n = n
        self.mask_bits = [int(b) for b in bin(self.mask)[2:].zfill(n)]
        
    def update(self):
        s = sum([self.state[i] * self.mask_bits[i] for i in range(self.n)])
        self.state = [s] + self.state[:-1]
        
    def __call__(self):
        b = self.state[-1]
        self.update()
        return b  
class CipherSymbolic:
    def __init__(self, key: list):
        self.lfsr1 = LFSRSymbolic(128, key[-128:], MASK1)
        self.lfsr2 = LFSRSymbolic(128, key[-256:-128], MASK2)
        self.lfsr3 = LFSRSymbolic(128, [a - b for a, b in zip(key[-128:],key[-256:-128])], MASK2)
        
    def filter_polynomial(self, x0, x1, x2, x3):
        # x0*x1*x2 + x0*x2 + x1 + x2
        return x0*x1*x2 + x0*x2 + x1 + x2

    def bit(self):
        x,y,z = self.get_xyz()
        return self.filter_polynomial(x, y, z)
    
    def get_xyz(self):
        x = self.lfsr1()
        y = self.lfsr2() + self.lfsr2()
        z = self.lfsr3() + self.lfsr3() + self.lfsr3()
        return x,y,z
    
    def get_yz(self):
        y = self.lfsr2() + self.lfsr2()
        z = self.lfsr3() + self.lfsr3() + self.lfsr3()
        return y,z
    
    def stream(self, n):
        return [self.bit() for _ in range(n)]
            
    def xor(self, a, b):
        return [x + y for x, y in zip(a, b)]

    def encrypt(self, pt: bytes):
        pt_bits = [int(b) for b in bin(int.from_bytes(pt, 'big'))[2:].zfill(8 * len(pt))]
        key_stream = self.stream(8 * len(pt))
        return self.xor(pt_bits, key_stream)
    
key = secrets.randbits(256)
key_bits = [int(i) for i in bin(key)[2:].zfill(256)]
br256 = BooleanPolynomialRing(256, [f"x{i}" for i in range(256)])
key_sym = list(br256.gens())
print(len(key_sym))
# cipher = Cipher(key)
cipher_sym = CipherSymbolic(key_sym)

pt = b"\x00" * 128
ct_bits = [int(b) for b in bin(int.from_bytes(gift, 'big'))[2:].zfill(8 * len(gift))]
print(ct_bits.count(1))

# check if yz_list.obj exists
if os.path.exists("./yz_list.obj.sobj"):
    yz_list = load("./yz_list.obj.sobj")
else:
    yz_list = []
    for i in tqdm(range(len(pt) * 8)):
        yz_list.append(cipher_sym.get_yz())
    save(yz_list, "./yz_list.obj")



eqs = []
for i, bit in enumerate(ct_bits):
    if bit == 1:
        eqs.append(yz_list[i][0] + yz_list[i][1] + 1)

def all_monomials(x1s, x2s):
    d1_monos = x1s[:] + x2s[:]
    return [1] + d1_monos

def fast_coef_mat(monos, polys, br_ring):
    mono_to_index = {}
    for i, mono in enumerate(monos):
        mono_to_index[br_ring(mono)] = i
    # mat = matrix(GF(2), len(polys), len(monos))
    mat = [[0] * len(monos) for i in range(len(polys))]
    for i, f in tqdm(list(enumerate(polys))):
        for mono in f:
            # mat[i,mono_to_index[mono]] = 1
            mat[i][mono_to_index[mono]] = 1
    return mat
x2s = key_sym[128:256]
x1s = key_sym[:128]
monos = all_monomials(list(x1s), list(x2s))
print(f"[+] total equations {len(eqs)}")
print(f"[+] total monomials {len(monos)}")

mat = fast_coef_mat(monos, eqs, br256)
mat = matrix(GF(2), mat)
B = vector(GF(2),[1 for j in range(len(eqs))])
mat = mat[:, 1:]
print(f"[+] {mat.dimensions() = }, {mat.rank() = }")
try:
    sol = mat.solve_right(B)
    print(f"[+] solution found")
    print(f"[+] solution: {sol}")
    ker = mat.right_kernel()
    for v in ker.basis():
        print(f"[+] possible solution vector: {"".join(str(c) for c in v)[-128:]}")
        print(f"[+] possible solution vector: {"".join(str(c) for c in v)[:-128]}")
    # break
except:
    print(f"[+] no solution")