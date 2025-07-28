from Crypto.Util.number import bytes_to_long, getPrime
from secrets import randbits
from random import SystemRandom
from uuid import uuid4
import signal


def handler(_signum, _frame):
    raise TimeoutError("⏰ Mamba out!")


def del0n1x(x: int, coff: list, exp: list, p: int) -> int:
    return sum([(c * pow(x, e, p)) for c, e in zip(coff, exp)]) % p


def getQuestion(p_bits, c_bits, len):
    upper = 20
    E = [randbits(upper) for _ in range(len)]
    cs = [randbits(c_bits) for _ in range(len)]
    ps = [getPrime(p_bits) for _ in range(len)]
    pk = list(uuid4().hex)
    SystemRandom().shuffle(pk)
    pk = "".join(pk)
    key = bytes_to_long(pk.encode())
    output = [del0n1x(key, cs, E, p) for p in ps]
    return output, ps, cs, E, pk


gift = getQuestion(64, 16, 8)
for i in range(4):
    print(f"🎁 {gift[i]}")

flag = open("flag.txt", "rb").read().strip()

signal.signal(signal.SIGALRM, handler)
signal.alarm(720)

input_key = input("🔑 ").strip()
assert input_key == gift[-1], "🔒"
print(f"🔐 {flag}")
