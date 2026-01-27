from sage.all import (
  is_prime,
  Zmod,
  Zp,
  ZZ,
  derivative,
  PolynomialRing,
  identity_matrix,
  companion_matrix,
  vector,
)
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


exps = ast.literal_eval(open("output.txt").readline())
p = GCD(*exps[:8]) // 2
assert isPrime(p)
modulus = p**3
PR = PolynomialRing(Zmod(p**3), "x")
x = PR.gen()
f = x**3 + x + 1
y = PR.quotient(f, "y").gen()
g = 13 * y + 37
C_f = companion_matrix(f)
# replace "^" with "**" before solving
ct = eval(open("output.txt").readlines()[-1])
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
for flag in ans:
  if b"QnQSec" in long_to_bytes(int(flag)):
    print(long_to_bytes(int(flag)))
    break
