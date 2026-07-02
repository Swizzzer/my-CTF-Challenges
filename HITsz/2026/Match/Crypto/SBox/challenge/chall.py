import os
from cipher import Kumiko


if __name__ == "__main__":
  cipher = Kumiko(os.urandom(16), rounds=8)
  flag = open("flag.txt", "rb").read().strip()
  ct = cipher.enc(flag)
  print(f"Ciphertext: {ct.hex()}")

  for _ in range(16):
    plaintext = bytes.fromhex(input("🎫 > "))
    ciphertext = cipher.enc(plaintext)
    print(f"Result: {ciphertext.hex()}")

  print("🤐")
