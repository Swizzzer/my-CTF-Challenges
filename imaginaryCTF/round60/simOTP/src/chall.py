from random import SystemRandom

random = SystemRandom()


def otp(bitlen):
  while True:
    half_len = bitlen // 2
    half = random.getrandbits(half_len)
    half_L = list(f"{half:0{half_len}b}")
    half_R = half_L[:]
    random.shuffle(half_R)
    otp_bin = half_L + half_R
    return int("".join(otp_bin), 2)


if __name__ == "__main__":
  flag = open("flag.txt", "rb").read().strip()
  assert flag.startswith(b"ictf{") and flag.endswith(b"}")
  flag = flag[5:-1]
  msg = int.from_bytes(flag, "big")
  blen = len(flag) * 8
  for _ in range(204):
    padding = otp(blen)
    print(msg ^ padding)
