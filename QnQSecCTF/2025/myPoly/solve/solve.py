from shared.polynomial import (
  fast_polynomial_gcd,
)  # https://github.com/jvdsn/crypto-attacks
from sage.all import *
from multiprocessing import Pool
import itertools
from tqdm import tqdm
from Crypto.Util.number import long_to_bytes
from pwn import *
import time 
def my_factor(n):
  R = Zmod(n)["x"]
  while True:
    Q = R.quo(R.random_element(2))
    rr = gcd(ZZ(list(Q.random_element() ** (4 * n))[1]), n)
    if rr != 1:
      qq = (rr + 1) // 4
      pp = n // qq // rr
      assert pp * qq * rr == n
      return pp, qq, rr


def cal_roots(p, coffs, exps, ct):
  import os

  print(f"[+] Process {os.getpid()} starting to calculate roots for p={p}...")
  PR = PolynomialRing(GF(p), "x")
  x = PR.gen()
  f = 0
  for c, e in zip(coffs, exps):
    f += c * x**e
  f -= ct
  # g = x**(p-1) - 1
  g = pow(x, p - 1, f) - 1
  h = fast_polynomial_gcd(f, g)
  roots = tuple(int(res) for res, _ in h.roots())
  return roots


if __name__ == "__main__":
  context.log_level = "debug"
  # conn = process(["python", "chall.py"])
  conn = remote("127.0.0.1", 8000)
  exps = eval(conn.recvline())
  coffs = eval(conn.recvline())
  ct = eval(conn.recvline())
  n = eval(conn.recvline())
  start_time = time.time()

  ps = list(my_factor(n))
  tasks = [(p, coffs, exps, ct) for p in ps]
  with Pool() as pool:
    roots = pool.starmap(cal_roots, tasks)

  print("[+] roots calculated")

  combs = itertools.product(*roots)
  results = []
  for comb in tqdm(combs, total=prod(len(_) for _ in roots)):
    try:
      m = crt(list(comb), ps)
      results.append(m)
    except ValueError:
      pass
  for res in results:
    if long_to_bytes(res).isascii():
      print(long_to_bytes(res))
      break
  conn.sendlineafter(b"gimme your answer > ", long_to_bytes(res))
  end_time = time.time()
  print(f"[+] Time taken: {end_time - start_time:.2f} seconds")
  conn.interactive()
