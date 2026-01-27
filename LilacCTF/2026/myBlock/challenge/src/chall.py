from secrets import randbits
from cipher import myFeistel, ROUNDS
from hashlib import sha3_256
import signal


def handler(_signum, _frame):
  raise TimeoutError("⏰")


def oracle(nums, subkeys):
  cipher = myFeistel(subkeys)
  pts = [(randbits(16), randbits(16)) for _ in range(nums)]
  cts = cipher.enc(pts)
  print(pts)
  print(cts)


if __name__ == "__main__":
  signal.signal(signal.SIGALRM, handler)
  signal.alarm(512)
  flag = open("flag.txt", "rb").read().strip()
  subkeys = [randbits(16) for _ in range(ROUNDS)]
  nums = int(input("🎫 > "))
  assert nums < 675
  oracle(nums, subkeys)
  key = b"".join(subkeys[i].to_bytes(2, "big") for i in range(ROUNDS))
  print(sha3_256(key).digest().hex())
  guess = bytes.fromhex(input("🔑 > ").strip())
  assert guess == key, "💥"
  print(flag)
