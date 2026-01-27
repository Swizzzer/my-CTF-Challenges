from sage.all import *
from Crypto.Util.number import GCD, isPrime, long_to_bytes
import ast


# https://pypi.org/project/sageball/
def hensel_solve(f, p, r):
  """
  Solves polynomial roots in the ring Zmod(p**r) using Hensel's lifting method.

  Parameters:
  f (polynomial): The polynomial equation.
  p (int): A prime number.
  r (int): The exponent.

  Raises:
  ValueError: If p is not a prime number or if f has no roots.
  """
  if not is_prime(p):
    raise ValueError("p must be a prime")
  f = f.change_ring(Zp(p))
  F = f.change_ring(Zmod(pow(p, r)))
  P = Zp(p, max(30, r))
  Fd = derivative(F)
  origin_roots = f.roots()
  if not len(origin_roots):
    raise ValueError("f has no roots")
  ans = set()
  for x in origin_roots:
    x_k = ZZ(x[0])
    flag = 0
    for k in range(1, r):
      if Fd(x_k) == P(0):
        if Zmod(pow(p, r))(f(x_k)) == 0:
          continue
        else:
          flag = 1
          break
      else:
        x_k = Zmod(pow(p, r))(P(x_k) - P(F(x_k)) / P(Fd(x_k)))
    if not flag:
      ans.update({x_k})
  return list(ans)


def p_adic_dlp(g, y, p, e):
  R = Zp(p, prec=e)
  x = (R(y).log() / R(g).log()).lift()
  return x


def do_dlog(g, y, p, e, C_f):
  g_ = g.lift().substitute(x=C_f).det()
  y_ = y.lift().substitute(x=C_f).det()
  return p_adic_dlp(g_, y_, p, e)


p_m = eval(open("output.txt").readlines()[0])
exps = eval(open("output.txt").readlines()[1])

p = GCD(*exps[:8]) // 2
assert isPrime(p)
modulus = p**3
PR = PolynomialRing(Zmod(p**3), "x")
x = PR.gen()
f = x**3 + x + 1
y = PR.quotient(f, "y").gen()
ct = eval(open("output.txt").readlines()[-1])
g = 13 * y + 37
C_f = companion_matrix(f)
# replace "^" with "**" before solving
res = []
for y in ct:
  res.append(do_dlog(g, y, p, 3, C_f))
# print(res)
M = identity_matrix(len(res)).augment(vector(exps))
K = 2**128
M[:, -1:] *= K
L = M.LLL()
coeffs = []
for row in L:
  if abs(row[-1] // K) == 2:
    coeffs = row[:-1]
    # print(row)
    break
m = 1
for i in range(len(coeffs)):
  m *= pow(res[i], coeffs[i], p**2)
  m %= p**2
# print(m)

PR2 = PolynomialRing(Zmod(p**2), "z")
z = PR2.gen()
h = z**2 - m
ans = hensel_solve(h, p, 2)
print(ans)
mp5_def_str = """[0,0] 141359947154721358697753474691071362751004672000
[1,0] 53274330803424425450420160273356509151232000
[1,1] -264073457076620596259715790247978782949376
[2,0] 6692500042627997708487149415015068467200
[2,1] 36554736583949629295706472332656640000
[2,2] 5110941777552418083110765199360000
[3,0] 280244777828439527804321565297868800
[3,1] -192457934618928299655108231168000
[3,2] 26898488858380731577417728000
[3,3] -441206965512914835246100
[4,0] 1284733132841424456253440
[4,1] 128541798906828816384000
[4,2] 383083609779811215375
[4,3] 107878928185336800
[4,4] 1665999364600
[5,0] 1963211489280
[5,1] -246683410950
[5,2] 2028551200
[5,3] -4550940
[5,4] 3720
[5,5] -1
[6,0] 1"""
mp5_def = [
  [ast.literal_eval(x) for x in line.split(" ")] for line in mp5_def_str.split("\n")
]
mp_term = (
  lambda e, coef: lambda x, y: coef * x ** e[0] * y ** e[1]
  + coef * x ** e[1] * y ** e[0]
  if e[0] != e[1]
  else coef * x ** e[0] * y ** e[1]
)
mp = lambda mp_def: lambda x, y: sum([mp_term(*term)(x, y) for term in mp_def])
mp5 = mp(mp5_def)
x = var("x")
Fpm = GF(p_m)
Fpm2 = GF(p_m**2, "i", modulus=x**2 + 1)
i = Fpm2.gen()
aa, cc = Fpm2["aa, cc"].gens()
PR_Fpm = Fpm["aa, cc"]

# im = 0
# re + im = 14429765496353471453829343878729583280456154934347504974572768886654796949219268381988075960222490248804000928030775

f = mp5(aa + 0 * i, Fpm(ans[1]) + 0 * i)
f_real = PR_Fpm(f.map_coefficients(lambda c: c.polynomial()[0])).univariate_polynomial()
for res, _ in f_real.roots():
  if long_to_bytes(int(res)).startswith(b"H3CTF"):
    print(long_to_bytes(int(res)))
    break

