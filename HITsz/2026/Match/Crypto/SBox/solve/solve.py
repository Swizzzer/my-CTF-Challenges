#!/usr/bin/env python3

import os
from typing import Dict, List, Tuple

from pwn import context, remote, process


context.log_level = "error"

HOST = "10.249.14.223"
PORT = 32839


def chunk_blocks(data: bytes) -> List[bytes]:
  assert len(data) % 8 == 0
  return [data[i : i + 8] for i in range(0, len(data), 8)]


class Oracle:
  def __init__(self, host: str, port: int):
    # self.io = remote(host, port)
    self.io = process(["python3", "chall.py"])
    line = self.io.recvline().decode().strip()
    prefix = "Ciphertext: "
    if not line.startswith(prefix):
      raise ValueError(f"unexpected banner: {line!r}")
    self.flag_ct = bytes.fromhex(line[len(prefix) :])

  def query_blocks(self, blocks: List[bytes]) -> List[bytes]:
    payload = b"".join(blocks)
    self.io.recvuntil(b"> ")
    self.io.sendline(payload.hex().encode())
    line = self.io.recvline().decode().strip()
    prefix = "Result: "
    if not line.startswith(prefix):
      raise ValueError(f"unexpected result: {line!r}")
    ct = bytes.fromhex(line[len(prefix) :])
    out = chunk_blocks(ct)
    # PKCS#7 always adds one extra block.
    if len(out) != len(blocks) + 1:
      raise ValueError("oracle returned an unexpected number of blocks")
    return out[:-1]

  def close(self) -> None:
    self.io.close()


def family(oracle: Oracle, base: bytes, pos: int) -> List[bytes]:
  blocks = []
  for value in range(256):
    block = bytearray(base)
    block[pos] = value
    blocks.append(bytes(block))
  return oracle.query_blocks(blocks)


def build_norm(entries: List[Tuple[int, int]]) -> Dict[int, int]:
  table = {key: value for key, value in entries}
  if len(table) != 256:
    raise ValueError("expected a permutation-sized table")
  ref = min(table)
  ref_value = table[ref]
  return {key: table[key] ^ ref_value for key in range(256)}


def surrogates(ciphertext: bytes, maps: Dict[str, Dict[int, int]]) -> List[int]:
  s = [None] * 8
  s[7] = ciphertext[2]
  if "C7" in maps:
    s[6] = ciphertext[6] ^ maps["C7"][s[7]]
  if "B6" in maps and s[6] is not None:
    s[5] = ciphertext[0] ^ maps["B6"][s[6]]
  if "A7" in maps and "B5" in maps and s[5] is not None:
    s[4] = ciphertext[4] ^ maps["A7"][s[7]] ^ maps["B5"][s[5]]
  if "C6" in maps and "A4" in maps and s[4] is not None:
    s[3] = ciphertext[1] ^ maps["C6"][s[6]] ^ maps["A4"][s[4]]
  if "B7" in maps and "C5" in maps and "A3" in maps and s[3] is not None:
    s[2] = ciphertext[5] ^ maps["B7"][s[7]] ^ maps["C5"][s[5]] ^ maps["A3"][s[3]]
  if "A6" in maps and "C4" in maps and "B2" in maps and s[2] is not None:
    s[1] = ciphertext[3] ^ maps["A6"][s[6]] ^ maps["C4"][s[4]] ^ maps["B2"][s[2]]
  if (
    "D7" in maps and "A5" in maps and "C3" in maps and "B1" in maps and s[1] is not None
  ):
    s[0] = (
      ciphertext[7]
      ^ maps["D7"][s[7]]
      ^ maps["A5"][s[5]]
      ^ maps["C3"][s[3]]
      ^ maps["B1"][s[1]]
    )
  return s


def recover_maps(oracle: Oracle) -> Dict[str, Dict[int, int]]:
  maps: Dict[str, Dict[int, int]] = {}

  outs7 = family(oracle, os.urandom(8), 2)
  maps["A7"] = build_norm([(c[2], c[4]) for c in outs7])
  maps["B7"] = build_norm([(c[2], c[5]) for c in outs7])
  maps["C7"] = build_norm([(c[2], c[6]) for c in outs7])
  maps["D7"] = build_norm([(c[2], c[7]) for c in outs7])

  outs6 = family(oracle, os.urandom(8), 6)
  entries6 = [(surrogates(c, maps)[6], c) for c in outs6]
  maps["B6"] = build_norm([(key, c[0]) for key, c in entries6])
  maps["C6"] = build_norm([(key, c[1]) for key, c in entries6])
  maps["D6"] = build_norm([(key, c[2]) for key, c in entries6])
  maps["A6"] = build_norm([(key, c[3]) for key, c in entries6])

  outs5 = family(oracle, os.urandom(8), 0)
  entries5 = [(surrogates(c, maps)[5], c, surrogates(c, maps)) for c in outs5]
  maps["B5"] = build_norm([(key, c[4] ^ maps["A7"][s[7]]) for key, c, s in entries5])
  maps["C5"] = build_norm([(key, c[5] ^ maps["B7"][s[7]]) for key, c, s in entries5])
  maps["D5"] = build_norm([(key, s[6]) for key, _, s in entries5])
  maps["A5"] = build_norm([(key, c[7] ^ maps["D7"][s[7]]) for key, c, s in entries5])

  outs4 = family(oracle, os.urandom(8), 4)
  entries4 = [(surrogates(c, maps)[4], c, surrogates(c, maps)) for c in outs4]
  maps["A4"] = build_norm([(key, c[1] ^ maps["C6"][s[6]]) for key, c, s in entries4])
  maps["B4"] = build_norm([(key, s[7] ^ maps["D6"][s[6]]) for key, _, s in entries4])
  maps["C4"] = build_norm([(key, c[3] ^ maps["A6"][s[6]]) for key, c, s in entries4])
  maps["D4"] = build_norm([(key, s[5]) for key, _, s in entries4])

  outs3 = family(oracle, os.urandom(8), 1)
  entries3 = [(surrogates(c, maps)[3], c, surrogates(c, maps)) for c in outs3]
  maps["A3"] = build_norm(
    [(key, c[5] ^ maps["B7"][s[7]] ^ maps["C5"][s[5]]) for key, c, s in entries3]
  )
  maps["B3"] = build_norm([(key, s[6] ^ maps["D5"][s[5]]) for key, _, s in entries3])
  maps["C3"] = build_norm(
    [(key, c[7] ^ maps["D7"][s[7]] ^ maps["A5"][s[5]]) for key, c, s in entries3]
  )
  maps["D3"] = build_norm([(key, s[4]) for key, _, s in entries3])

  outs2 = family(oracle, os.urandom(8), 5)
  entries2 = [(surrogates(c, maps)[2], c, surrogates(c, maps)) for c in outs2]
  maps["A2"] = build_norm(
    [(key, s[7] ^ maps["B4"][s[4]] ^ maps["D6"][s[6]]) for key, _, s in entries2]
  )
  maps["B2"] = build_norm(
    [(key, c[3] ^ maps["A6"][s[6]] ^ maps["C4"][s[4]]) for key, c, s in entries2]
  )
  maps["C2"] = build_norm([(key, s[5] ^ maps["D4"][s[4]]) for key, _, s in entries2])
  maps["D2"] = build_norm([(key, s[3]) for key, _, s in entries2])

  outs1 = family(oracle, os.urandom(8), 3)
  entries1 = [(surrogates(c, maps)[1], c, surrogates(c, maps)) for c in outs1]
  maps["A1"] = build_norm(
    [(key, s[6] ^ maps["B3"][s[3]] ^ maps["D5"][s[5]]) for key, _, s in entries1]
  )
  maps["B1"] = build_norm(
    [
      (key, c[7] ^ maps["D7"][s[7]] ^ maps["A5"][s[5]] ^ maps["C3"][s[3]])
      for key, c, s in entries1
    ]
  )
  maps["C1"] = build_norm([(key, s[4] ^ maps["D3"][s[3]]) for key, _, s in entries1])
  maps["D1"] = build_norm([(key, s[2]) for key, _, s in entries1])

  outs0 = family(oracle, os.urandom(8), 7)
  entries0 = [(surrogates(c, maps)[0], c, surrogates(c, maps)) for c in outs0]
  maps["A0"] = build_norm(
    [(key, s[5] ^ maps["C2"][s[2]] ^ maps["D4"][s[4]]) for key, _, s in entries0]
  )
  maps["B0"] = build_norm([(key, s[3] ^ maps["D2"][s[2]]) for key, _, s in entries0])
  maps["C0"] = build_norm(
    [
      (key, s[7] ^ maps["A2"][s[2]] ^ maps["B4"][s[4]] ^ maps["D6"][s[6]])
      for key, _, s in entries0
    ]
  )
  maps["D0"] = build_norm([(key, s[1]) for key, _, s in entries0])

  return maps


def invert_surrogate(ciphertext: bytes, maps: Dict[str, Dict[int, int]]) -> bytes:
  s = surrogates(ciphertext, maps)
  x = [0] * 8
  x[7] = s[0]
  x[3] = s[1] ^ maps["D0"][s[0]]
  x[5] = s[2] ^ maps["D1"][s[1]]
  x[1] = s[3] ^ maps["B0"][s[0]] ^ maps["D2"][s[2]]
  x[4] = s[4] ^ maps["C1"][s[1]] ^ maps["D3"][s[3]]
  x[0] = s[5] ^ maps["A0"][s[0]] ^ maps["C2"][s[2]] ^ maps["D4"][s[4]]
  x[6] = s[6] ^ maps["A1"][s[1]] ^ maps["B3"][s[3]] ^ maps["D5"][s[5]]
  x[2] = (
    s[7] ^ maps["C0"][s[0]] ^ maps["A2"][s[2]] ^ maps["B4"][s[4]] ^ maps["D6"][s[6]]
  )
  return bytes(x)


def main() -> None:
  oracle = Oracle(HOST, PORT)
  try:
    maps = recover_maps(oracle)

    known_block = b"ABCDEFGH"
    known_ct = oracle.query_blocks([known_block])[0]
    calibration = bytes(
      a ^ b for a, b in zip(invert_surrogate(known_ct, maps), known_block)
    )

    recovered = b"".join(
      bytes(a ^ b for a, b in zip(invert_surrogate(block, maps), calibration))
      for block in chunk_blocks(oracle.flag_ct)
    )
    pad = recovered[-1]
    flag = recovered[:-pad]
    print(flag.decode())
  finally:
    oracle.close()


if __name__ == "__main__":
  main()
