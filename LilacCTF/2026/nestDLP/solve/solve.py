from sage.all import prod, matrix, PolynomialRing, GF, Zmod
from tqdm import tqdm

from ortools.sat.python import cp_model


def projected_basis(I, p):  # noqa: E741
  R = I.ring()
  names = R.variable_names()
  Rfp = PolynomialRing(GF(p), names=names)
  Ifp = Rfp.ideal([Rfp(f) for f in I.gens()])
  basis_fp = Ifp.normal_basis()
  xs = R.gens()
  basis = []
  for m in basis_fp:
    exps = m.exponents()[0]
    mon = prod(x**e for x, e in zip(xs, exps))
    basis.append(mon)
  return basis


def padic_dlp(g: int, y: int, p: int, s: int):
  def theta(k, p, s):
    return (pow(k, (p - 1) * p ** (s - 1), p ** (2 * s - 1)) - 1) // (p**s)

  g, y, p, s = int(g), int(y), int(p), int(s)
  return pow(theta(g, p, s), -1, p ** (s - 1)) * theta(y, p, s) % (p ** (s - 1))


def get_matrix(element, quotient_ring, p):
  I = quotient_ring.defining_ideal()  # noqa: E741
  base_ring = quotient_ring.base_ring()
  basis = projected_basis(I, p)
  g_poly = element.lift()
  matrix_cols = []

  for b in basis:
    prod_poly = g_poly * b
    reduced_poly = quotient_ring(prod_poly).lift()
    coeffs = [reduced_poly.monomial_coefficient(mon) for mon in basis]
    matrix_cols.append(coeffs)

  M = matrix(base_ring, matrix_cols).transpose()
  return M


def solve(nums):
  max_bits = max(n.bit_length() for n in nums)
  bitlen = (max_bits + 7) // 8 * 8
  byte_len = bitlen // 8

  C_bits = []
  for c in nums:
    bits = f"{c:0{bitlen}b}"
    C_bits.append([int(b) for b in bits])

  model = cp_model.CpModel()
  m = [model.NewBoolVar(f"m_{j}") for j in range(bitlen)]
  B = [model.NewIntVar(0, 255, f"B_{i}") for i in range(byte_len)]
  for i in range(byte_len):
    model.Add(sum(((1 << (7 - k)) * m[i * 8 + k]) for k in range(8)) == B[i])

  for i in range(byte_len):
    model.Add(B[i] >= 32)
    model.Add(B[i] <= 126)

  W = (bitlen // 2) + 1

  for c_bits in C_bits:
    coeffs = []
    for j in range(bitlen):
      c = c_bits[j]
      a = 1 - 2 * c  # c=0 -> 1; c=1 -> -1
      coeffs.append(a)

    rhs = W - sum(c_bits)
    model.Add(sum(coeffs[j] * m[j] for j in range(bitlen)) == rhs)

  solver = cp_model.CpSolver()
  solver.parameters.num_search_workers = 8
  status = solver.Solve(model)

  if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    print("No solution found.")
    return

  bs = [solver.Value(bv) for bv in B]
  inner = bytes(bs).decode("ascii")
  flag = f"LilacCTF{{{inner}}}"
  print("FLAG:", flag)


if __name__ == "__main__":
  with open("output.txt") as f:
    p = int(f.readline().strip())
    datas = f.readlines()
  R = PolynomialRing(Zmod(p**3), names="x,y")
  x, y = R.gens()
  I = R.ideal([x**3 + y**5 + 13 * x * y - 37, y**3 + x**5 + 37 * x - 13])  # noqa: E741
  S = R.quotient(I, names=("x", "y"))
  g = S(x**2 + y**2 + 13 * x + 37 * y + 1337)
  exps = []
  for data in tqdm(datas, total=len(datas)):
    h = S(eval(data))
    det_g = get_matrix(g, S, p).det()
    det_h = get_matrix(h, S, p).det()
    log_det = padic_dlp(det_g, det_h, p, 3)
    exps.append(log_det)
  solve(exps)
