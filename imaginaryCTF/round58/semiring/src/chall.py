from copy import deepcopy
from Crypto.Util.number import bytes_to_long
from random import SystemRandom

random = SystemRandom()


class Matrix:
  def __init__(self, data):
    if not all(isinstance(row, list) for row in data):
      raise TypeError("Matrix must be initialized with a 2D list.")
    if len(set(len(row) for row in data)) != 1:
      raise ValueError("All rows must have the same length.")
    self.data = deepcopy(data)
    self.n = len(data)
    self.m = len(data[0])

  def __repr__(self):
    rows = ["[" + ", ".join(f"{x}" for x in row) + "]" for row in self.data]
    return "[\n  " + ",\n  ".join(rows) + "\n]"

  @staticmethod
  def t_add(a, b):
    if a == -1:
      return b
    if b == -1:
      return a
    return min(a, b)

  @staticmethod
  def t_mul(a, b):
    if a == -1 or b == -1:
      return -1
    return a + b

  def __add__(self, other):
    if (self.n, self.m) != (other.n, other.m):
      raise ValueError("Matrix dimensions must match for addition.")
    res = [
      [self.t_add(self.data[i][j], other.data[i][j]) for j in range(self.m)]
      for i in range(self.n)
    ]
    return Matrix(res)

  def __matmul__(self, other):
    if self.m != other.n:
      raise ValueError("Matrix dimensions must match for multiplication.")
    res = []
    for i in range(self.n):
      row = []
      for j in range(other.m):
        val = -1
        for k in range(self.m):
          val = self.t_add(val, self.t_mul(self.data[i][k], other.data[k][j]))
        row.append(val)
      res.append(row)
    return Matrix(res)

  def __pow__(self, power):
    if self.n != self.m:
      raise ValueError("Matrix power only defined for square matrices.")
    if power < 0:
      raise ValueError("Negative powers not supported.")
    result = Matrix(
      [[0 if i == j else -1 for j in range(self.n)] for i in range(self.n)]
    )
    base = deepcopy(self)
    p = power
    while p > 0:
      if p % 2 == 1:
        result = result @ base
      base = base @ base
      p //= 2
    return result


flag = bytes_to_long(open("flag.txt", "rb").read().strip())
res = []
flag_bits = [0] + list(
  reversed([1 if (flag >> i) & 1 else -1 for i in range(flag.bit_length())])
)
res.append(flag_bits)
for _ in range(flag.bit_length()):
  res.append([random.choice([1, 2]) for _ in range(flag.bit_length() + 1)])
for i in range(len(res)):
  res[i][i] = 0
M = Matrix(res)
print(M ** (flag.bit_length()))
