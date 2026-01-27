from Crypto.Util.number import getRandomNBitInteger, getPrime, bytes_to_long
import signal
import random


def handler(_signum, _frame):
  raise TimeoutError("⏰ Mamba out!")


def banner():
  print(r"""
        Welcome to
▄▄▄▄  ▄   ▄ ▗▖   ▗▄▄▄▖▗▄▄▖▗▄▄▖ 
█ █ █ █   █ ▐▌   ▐▌  ▐▌   ▐▌ ▐▌
█   █  ▀▀▀█ ▐▌   ▐▛▀▀▘▝▀▚▖▐▛▀▚▖
      ▄   █ ▐▙▄▄▖▐▌  ▗▄▄▞▘▐▌ ▐▌
       ▀▀▀                     
""")


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


class Cipher:
  def __init__(self, *lfsrs):
    self.lfsrs = lfsrs
    for _ in range(128):
      for lfsr in self.lfsrs:
        lfsr()

  def encrypt(self, msg):
    lfsr1, lfsr2, lfsr3 = self.lfsrs
    enc = []
    for m in msg:
      s = 0
      for _ in range(8):
        s = [(s << 1) | lfsr2(), (s << 1) | lfsr3()][lfsr1()]
      enc.append(s ^ m)
    return bytes(enc)


if __name__ == "__main__":
  signal.signal(signal.SIGALRM, handler)
  signal.alarm(384)
  banner()
  n = 64
  flag = open("flag.txt").read().strip()
  m = bytes_to_long(flag.encode())
  seed1, seed2, seed3, mask1, mask2, mask3 = [getRandomNBitInteger(n) for _ in "_" * 6]
  lfsr1 = LFSR(n, seed1, mask1)
  lfsr2 = LFSR(n, seed2, mask2)
  lfsr3 = LFSR(n, seed3, mask3)
  cipher = Cipher(lfsr1, lfsr2, lfsr3)
  while inp := input(
    "👉 Choose an option\n\033[34mmask\033[0m, \033[34mguess\033[0m, \033[34menc\033[0m or \033[34mexit\033[0m\n> "
  ):
    if inp == "mask":
      print(f"{mask1 = }\n{mask2 = }\n{mask3 = }")
    elif inp == "guess":
      if (
        input("seed1: ") == str(seed1)
        and input("seed2: ") == str(seed2)
        and input("seed3: ") == str(seed3)
      ):
        print("🎉🎉🎉")
        seed = int(input("Give me a seed and I'll give you a gift > "))
        prng = PRNG(seed)
        a = prng.round(random.SystemRandom().randrange(2**16))
        b = prng.round(random.SystemRandom().randrange(2**16))
        p = getPrime(512)
        print(f"[+] {p = }")
        print(f"[+] Here's your gift: {(a * m + b) % p}")
      else:
        print("❌❌❌ Wrong seeds!")
        exit(0)
    elif inp == "enc":
      print(cipher.encrypt(bytes.fromhex(input("msg: "))).hex())
    elif inp == "exit":
      exit()
