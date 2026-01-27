from Crypto.Util.number import bytes_to_long, getPrime, isPrime
from secrets import randbits
from random import SystemRandom
import signal
import string


def handler(_signum, _frame):
  raise TimeoutError("⏰ Mamba out!")


def polyVal(x: int, coff: list, exp: list, p: int) -> int:
  return sum([(c * pow(x, e, p)) for c, e in zip(coff, exp)]) % p


def genKey(nbits):
  p = getPrime(nbits // 3)
  while True:
    q = getPrime(nbits // 3)
    r = 4 * q - 1
    if isPrime(r):
      return p * q * r


def genMsg(len: int):
  random = SystemRandom()
  alphabet = string.ascii_letters
  return "".join(random.sample(alphabet, len))


if __name__ == "__main__":
  flag = open("flag.txt", "rb").read().strip()
  msg = genMsg(50)
  exps = [randbits(16) for _ in range(8)]
  coffs = [randbits(16) for _ in range(8)]
  n = genKey(2048)
  ct = polyVal(bytes_to_long(msg.encode()), coffs, exps, n)
  print(f"{exps}")
  print(f"{coffs}")
  print(f"{ct}")
  print(f"{n}")

  signal.signal(signal.SIGALRM, handler)
  signal.alarm(150)

  res = input("gimme your answer > ").strip()

  if res == msg:
    print("🎉🎉🎉")
    print(flag)
  else:
    print("😭😭😭")
    exit(1)
