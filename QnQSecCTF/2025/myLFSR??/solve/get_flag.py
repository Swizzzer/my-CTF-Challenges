# ======== Written by Swizzer ========

import random
from itertools import product
from Crypto.Util.number import long_to_bytes


class PRNG:
  def __init__(self, seed):
    self.a = 1337137
    self.b = 13371337
    random.seed(seed)

  def next(self):
    x = random.randint(self.a, self.b)
    random.seed(x**2 + x + 1)
    return x

  def round(self, k):
    for _ in range(k):
      x = self.next()
    return x


prng = PRNG(1137256)
res = set()
for _ in range(128):
  res.add(prng.next())

# res should be a set of 3 elements
print(res)
# paste the data we get after running solve.py
p = 12880949572959162796936930535230806183729258371972341651341625517976560400956785472908715460387961666064494497770066388163215400887968347917486444369843587
gift = 7011798377833911440101706718970154349479397026858490045733407634714531923182075075014400800234235932252778533147452087564804861889953970777095727825692

for a, b in product(list(res), repeat=2):
  try:
    m = pow(a, -1, p)
    x = (gift - b) * m % p
    ans = long_to_bytes(x)
    if ans.startswith(b"QnQSec{") and ans.endswith(b"}"):
      print(f"Found: {ans}")
      break
  except:
    continue
