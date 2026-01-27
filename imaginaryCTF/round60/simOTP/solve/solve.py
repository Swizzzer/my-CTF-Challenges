from ortools.sat.python import cp_model


def main():
  with open("output.txt", "r") as f:
    nums = [int(line.strip()) for line in f if line.strip()]

  max_bits = max(n.bit_length() for n in nums)
  bitlen = (max_bits + 7) // 8 * 8
  h = bitlen // 2
  byte_len = bitlen // 8

  C_bits = []
  for c in nums:
    bits = f"{c:0{bitlen}b}"
    C_bits.append([int(b) for b in bits])

  model = cp_model.CpModel()
  m = [model.NewBoolVar(f"m_{j}") for j in range(bitlen)]
  B = [model.NewIntVar(0, 255, f"B_{i}") for i in range(byte_len)]
  for i in range(byte_len):
    # B[i] = sum_{k=0..7} 2^(7-k) * m[i*8 + k]
    model.Add(sum(((1 << (7 - k)) * m[i * 8 + k]) for k in range(8)) == B[i])

  for i in range(byte_len):
    model.Add(B[i] >= 32)
    model.Add(B[i] <= 126)

  for c_bits in C_bits:
    coeffs = []
    for j in range(bitlen):
      c = c_bits[j]
      if j < h:
        a = 1 - 2 * c  # +1 if c=0, -1 if c=1
      else:
        a = -1 + 2 * c  # -1 if c=0, +1 if c=1
      coeffs.append(a)
    left_c = sum(c_bits[:h])
    right_c = sum(c_bits[h:])
    b_s = right_c - left_c
    model.Add(sum(coeffs[j] * m[j] for j in range(bitlen)) == b_s)

  model.AddDecisionStrategy(m, cp_model.CHOOSE_FIRST, cp_model.SELECT_MIN_VALUE)

  solver = cp_model.CpSolver()
  solver.parameters.num_search_workers = 8
  solver.parameters.log_search_progress = True
  status = solver.Solve(model)

  if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    print("No solution found.")
    return

  bs = [solver.Value(bv) for bv in B]
  try:
    inner = bytes(bs).decode("ascii")
  except Exception:
    inner = "".join(chr(b) if 32 <= b < 127 else "?" for b in bs)

  flag = f"ictf{{{inner}}}"
  print("FLAG:", flag)


if __name__ == "__main__":
  main()
