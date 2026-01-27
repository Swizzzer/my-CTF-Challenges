from ast import literal_eval
from Crypto.Util.number import getPrime
import os
import time
from hashlib import sha3_512

FLAG1 = os.getenv("FLAG1", "H3CTF{dummy_flag1_for_testing}")
FLAG2 = os.getenv("FLAG2", "H3CTF{dummy_flag2_for_testing}")
FLAG3 = os.getenv("FLAG3", "H3CTF{dummy_flag3_for_testing}")
FLAG4 = os.getenv("FLAG4", "H3CTF{dummy_flag4_for_testing}")
FLAG5 = os.getenv("FLAG5", "H3CTF{dummy_flag5_for_testing}")


def level_1():
  res = input("🥱 You think you can read my mind? ")
  assert all(a == b for a, b in zip(res, FLAG1)), "👿"
  print(FLAG1)


def level_2():
  N = getPrime(512) * getPrime(512)
  print(f"{N = }")
  res = int(input("😏 Wanna break RSA? "))
  assert res != 1 and res != N and N % res == 0, "👿"
  print(FLAG2)


def level_3():
  res = input("🕐 Wondering the time? ")
  start = time.time()
  for i in range(min(len(res), len(FLAG3))):
    if res[i] != FLAG3[i]:
      time.sleep(0.001)
      break

  end = time.time()
  print(end - start)


def level_4():
  res = literal_eval(input("🫨 Why not flip some bits? "))
  assert (
    len(res) != 0
    and all(a == 0 for a in res)
    and all(res[i] == 1 for i in range(len(res)))
  ), "👿"
  print(FLAG4)


def level_5():
  a = "Swizzer!!"
  b = input("😵‍💫 Found some collisions? ")
  assert (
    sha3_512(a.encode()).hexdigest() == sha3_512(b.encode()).hexdigest() and a is not b
  ), "👿"
  print(FLAG5)


if __name__ == "__main__":
  print("🥰 Welcome to the impossible!")
  while True:
    choice = int(input("🔑 Choose a level to escape > "))
    match choice:
      case 1:
        level_1()
      case 2:
        level_2()
      case 3:
        level_3()
      case 4:
        level_4()
      case 5:
        level_5()
      case _:
        print("👿")
