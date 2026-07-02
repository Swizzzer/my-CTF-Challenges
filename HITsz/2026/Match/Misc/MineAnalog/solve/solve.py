from z3 import BitVec, Solver, sat, Extract
import re


def parse(filename):
  logic = {}
  with open(filename, "r") as f:
    for line in f:
      match = re.search(
        r"assign result_(\d+) = ~\(plaintext_\d+ \^ \(plaintext_0 ([&|]) ~plaintext_0\) \^ \(plaintext_0 ([&|]) ~plaintext_0\)\);",
        line,
      )
      if match:
        bit_idx = int(match.group(1))
        op1 = match.group(2)  # '&' or '|'
        op2 = match.group(3)  # '&' or '|'

        val1 = 0 if op1 == "&" else 1
        val2 = 0 if op2 == "&" else 1

        logic[bit_idx] = (val1, val2)

  return logic


def solve(logic):
  s = Solver()
  plaintext = BitVec("plaintext", 408)
  for bit_idx in range(408):
    if bit_idx in logic:
      val1, val2 = logic[bit_idx]
      expected_bit = val1 ^ val2
      bit_i = Extract(bit_idx, bit_idx, plaintext)
      s.add(bit_i == expected_bit)
  if s.check() == sat:
    model = s.model()
    plaintext_val = model[plaintext].as_long()
    return plaintext_val
  else:
    return None


def main():
  logic = parse("chall.v")
  plaintext = solve(logic)
  if plaintext is not None:
    num_bytes = (408 + 7) // 8
    plaintext_bytes = plaintext.to_bytes(num_bytes, byteorder="big")
    print(f"[+] FLAG: {plaintext_bytes.decode()}")
  else:
    print("[-] No solution found!")


if __name__ == "__main__":
  main()
