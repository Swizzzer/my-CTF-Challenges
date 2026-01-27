def expand(n: int, base=3) -> list[int]:
  res = []
  while n:
    res.append(n % base)
    n //= base
  return res


class myLFSR:
  def __init__(self, key: list[int], mask: list[int]):
    assert all(0 <= x < 3 for x in key), "Key must be in range [0, 2]"
    assert all(0 <= x < 3 for x in mask), "Mask must be of the same length"
    assert len(key) == len(mask), "Key and mask must be of the same length"

    self.state = key
    self.mask = mask
    self.mod = 3

  def __call__(self) -> int:
    b = sum(s * m for s, m in zip(self.state, self.mask)) % self.mod
    output = self.state[0]
    self.state = self.state[1:] + [b]
    
    return output


def gf3_inv(a: int) -> int:
  if a == 0:
    raise ValueError("Cannot invert 0")
  return a


def gf3_mul(a: int, b: int) -> int:
  return (a * b) % 3


def gf3_add(a: int, b: int) -> int:
  return (a + b) % 3


# Berlekamp-Massey algorithm for GF(3)
# find the shortest LFSR that can generate a given sequence
def berlekamp_massey(s: list[int]) -> list[int]:
  n = len(s)
  C = [1]
  B = [1]
  L = 0
  m = 1
  b = 1

  for N_iter in range(n):
    d = s[N_iter]
    for i in range(1, L + 1):
      d = gf3_add(d, gf3_mul(C[i], s[N_iter - i]))

    if d == 0:
      m += 1
    else:
      T = C[:]
      d_mul_b_inv = gf3_mul(d, gf3_inv(b))
      C.extend([0] * (m + len(B) - len(C)))

      for i in range(len(B)):
        term = gf3_mul(d_mul_b_inv, B[i])
        C[m + i] = (C[m + i] - term + 3) % 3

      if 2 * L <= N_iter:
        L = N_iter + 1 - L
        B = T
        b = d
        m = 1
      else:
        m += 1

  while len(C) > 1 and C[-1] == 0:
    C.pop()

  return C


def unexpand(trits: list[int], base=3) -> int:
  n = 0
  for t in reversed(trits):
    n = n * base + t
  return n


def read_output(filename="output.txt"):
  with open(filename, "r") as f:
    lines = f.readlines()
    n_val = int(lines[0].strip())
    gift_hex_val = lines[1].strip()
    ct_hex_val = lines[2].strip()
  return n_val, gift_hex_val, ct_hex_val


def solve():
  try:
    LEN, gift_hex, ct_hex = read_output("output.txt")
  except Exception as e:
    print(f"[-] Error reading the output file: {e}")
    return
  LEN_KEY = LEN // 3 + 3
  gift = bytes.fromhex(gift_hex)
  ct_flag = bytes.fromhex(ct_hex)
  gift_bytes = b"\xff" * (LEN_KEY)
  gift_trits = expand(int.from_bytes(gift_bytes, "big"))
  gift_list = list(gift)

  len_gift_keyst = min(len(gift_trits), len(gift_list))
  keyst = [
    p ^ c for p, c in zip(gift_trits[:len_gift_keyst], gift_list[:len_gift_keyst])
  ]

  if not all(0 <= x < 3 for x in keyst):
    print("[-] Values are not in GF(3)")
    return

  conn_poly = berlekamp_massey(keyst)
  L = len(conn_poly) - 1

  if L != LEN:
    print(f"[?] Polynomial degree {L} does not match key length {LEN}.")
    return

  rec_mask = [(-conn_poly[L - i] + 3) % 3 for i in range(L)]
  init_key = keyst[:L]
  lfsr_sim = myLFSR(init_key, rec_mask)

  # Consume the gift keystream
  for _ in range(len_gift_keyst):
    lfsr_sim()

  # At this point, lfsr_sim.state is the key needed to decrypt the flag
  key_flag = lfsr_sim.state
  lfsr_flag = myLFSR(key_flag, rec_mask)

  ct_flag_list = list(ct_flag)
  st_flag = [lfsr_flag() for _ in range(len(ct_flag_list))]

  pt_flag_trits = [c ^ s for c, s in zip(ct_flag_list, st_flag)]
  flag_int = unexpand(pt_flag_trits)
  flag_bytes = flag_int.to_bytes((flag_int.bit_length() + 7) // 8, "big")
  assert b"QnQSec" in flag_bytes
  print(f"[+] FLAG: {flag_bytes}")


if __name__ == "__main__":
  solve()
