from pwn import *
from Crypto.Util.number import *

cipher = b"5A847152A394B6A7AD8165C6A5B2618D59B8EC381A8CF7E8488EA05AB069D0C161".lower()
print(b"c=", cipher)
flag = b""
while len(flag) < 33:
  for i in range(32, 127):
    r = process(["/build/camellia", "1"])
    r.recvuntil(b"Input the flag > ")
    tmp = flag + long_to_bytes(i)
    tmp = tmp.ljust(33, b"a")
    r.sendline(tmp)
    try:
      r.recvuntil(b"Wrong!\n")
    except:
      r.recvuntil(b"Correct!\n")
      print("flag is ", tmp)
      r.close()
      exit()
    r.recvuntil(b"Your ciphertext: ")
    res = r.recvuntil(b"\n")[:-1]
    # print(res)
    if res[: 2 * (len(flag) + 1)] == cipher[: 2 * (len(flag) + 1)]:
      flag = tmp[: len(flag) + 1]
      print(flag)
      r.close()
      break
    r.close()
