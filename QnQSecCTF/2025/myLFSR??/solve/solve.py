# ======== Written by adwa ========

from sage.all import *
from pwn import *
from tqdm import trange, tqdm

# r = process(["python", "chall.py"])
r = remote("8.140.204.2", 33142)


class LFSReq:
  def __init__(self, n, seed, mask):
    self.state = seed
    self.mask_bits = [int(b) for b in f"{mask:0{n}b}"]
    self.n = n

  def update(self):
    s = sum([self.state[i] * self.mask_bits[i] for i in range(self.n)])
    self.state = self.state[1:] + [s]

  def __call__(self):
    self.update()
    return self.state[-1]


n = 64
R = BooleanPolynomialRing(3 * n, [f"x{i}" for i in range(3 * n)])
seeds = list(R.gens())
seed1 = seeds[:n]
seed2 = seeds[n : 2 * n]
seed3 = seeds[2 * n :]

bits = 20000
r.sendlineafter(b"> ", b"mask")
mask1 = int(r.recvline().decode().split("= ")[-1])
mask2 = int(r.recvline().decode().split("= ")[-1])
mask3 = int(r.recvline().decode().split("= ")[-1])
r.sendlineafter(b"> ", b"enc")
r.sendlineafter(b"msg: ", b"00" * (bits // 8))
enc = r.recvline().decode().split("= ")[-1]

c = bin(int(enc, 16))[2:].zfill(bits)

lfsreq1 = LFSReq(n, seed1, mask1)
lfsreq2 = LFSReq(n, seed2, mask2)
lfsreq3 = LFSReq(n, seed3, mask3)
for _ in range(128):
  for lfsr in [lfsreq1, lfsreq2, lfsreq3]:
    lfsr()

eqs = [
  (1 - lfsreq1()) * lfsreq2() + lfsreq1() * lfsreq3() - int(c[i]) for i in trange(bits)
]


def all_monomials(x1s, x2s, x3s):
  d1_monos = x1s[:] + x2s[:] + x3s[:]
  d2_monos = []
  d3_monos = []
  for xi in x1s:
    for xj in x2s:
      d2_monos.append(xi * xj)
  for xi in x1s:
    for xj in x3s:
      d2_monos.append(xi * xj)
  return [1] + d1_monos + d2_monos + d3_monos


def fast_coef_mat(monos, polys, br_ring):
  mono_to_index = {}
  for i, mono in enumerate(monos):
    mono_to_index[br_ring(mono)] = i
  mat = [[0] * len(monos) for _ in range(len(polys))]
  for i, f in tqdm(list(enumerate(polys))):
    for mono in f:
      mat[i][mono_to_index[mono]] = 1
  return mat


def solve_lfsr(seed, eqs, R):
  mat = fast_coef_mat(seed, eqs, R)
  mat = matrix(GF(2), mat)
  B = vector(GF(2), [mat[j, 0] for j in range(len(eqs))])
  mat = mat[:, 1:]
  sol = mat.solve_right(B)
  return sol


mono = all_monomials(seed1, seed2, seed3)
sol = solve_lfsr(mono, eqs, R)
print(f"[+] {sol[:192] = }")
# Theoretically, all the seeds can be calculated, but s1 and s3 are actually all 0
# If not, we can have another try to solve it
s2 = sol[64:128]
s2 = int("".join(map(str, s2)), 2)
print(f"[+] {s2 = }")


class LFSR:
  def __init__(self, n, seed, mask):
    self.state = [int(b) for b in f"{seed:0{n}b}"]
    self.mask_bits = [int(b) for b in f"{mask:0{n}b}"]
    self.n = n

  def update(self):
    s = sum([self.state[i] * self.mask_bits[i] for i in range(self.n)]) & 1
    self.state = self.state[1:] + [s]

  def __call__(self):
    self.update()
    return self.state[-1]


lfsr2 = LFSR(n, s2, mask2)
for _ in range(128):
  lfsr2()
out1 = ["?" for _ in range(bits)]
out2 = [lfsr2() for _ in range(bits)]
out3 = ["?" for _ in range(bits)]
for i in range(bits):
  if int(c[i]) != out2[i]:
    out1[i] = 1
    out3[i] = int(c[i])

# print(f'[x] out1[:100]: {out1[:100]}')
# print(f'[x] out2[:100]: {out2[:100]}')
# print(f'[x] out3[:100]: {out3[:100]}')

lfsreq1 = LFSReq(n, seed1, mask1)
lfsreq3 = LFSReq(n, seed3, mask3)
for _ in range(128):
  for lfsr in [lfsreq1, lfsreq3]:
    lfsr()

eqs1, eqs3 = [], []
for i in range(bits):
  if out1[i] != "?":
    eqs1.append(lfsreq1() - out1[i])
  else:
    lfsreq1()
  if out3[i] != "?":
    eqs3.append(lfsreq3() - out3[i])
  else:
    lfsreq3()


s1 = solve_lfsr([1] + seed1, eqs1, R)
s3 = solve_lfsr([1] + seed3, eqs3, R)

s1 = int("".join(map(str, s1)), 2)
s3 = int("".join(map(str, s3)), 2)
print(f"s1 = {s1}")
print(f"s3 = {s3}")
r.sendlineafter(b"> ", b"guess")
r.sendlineafter(b"seed1: ", str(s1))
r.sendlineafter(b"seed2: ", str(s2))
r.sendlineafter(b"seed3: ", str(s3))
# Run find_seed_with_small_period.py to find a seed with small period
# We get this seed with 3-period
r.sendlineafter(b"> ", b"1137256")
r.interactive()
