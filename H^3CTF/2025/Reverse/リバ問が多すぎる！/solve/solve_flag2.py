import subprocess
import re
import string
from tqdm import trange


def extract_instructions(perf_output: str) -> int:
  match = re.search(r"(\d+)::instructions:([a-zA-Z]):(\d+):([\d.]+)::", perf_output)
  if not match:
    raise ValueError("Failed to extract instructions count")
  return int(match.group(1))


def run_perf(binary: str, input_str: str) -> int:
  cmd = ["perf", "stat", "-x:", "-e", "instructions:u", binary]
  proc = subprocess.Popen(
    cmd,
    stdin=subprocess.PIPE,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.PIPE,
    text=True,
  )
  _, stderr = proc.communicate(input=input_str)
  return extract_instructions(stderr)


PRINTABLE_CHARSET = "".join(
  ch
  for ch in (string.ascii_letters + string.digits + string.punctuation + " ")
  if ch not in "{}"
)


def search(binary: str) -> str:
  TOTAL_LEN = 26
  PREFIX = "H3CTF{"
  SUFFIX = "}"

  placeholder = "?"
  correct = [placeholder] * TOTAL_LEN
  correct[: len(PREFIX)] = list(PREFIX)
  correct[-1] = SUFFIX

  start = len(PREFIX)
  end = TOTAL_LEN - 1
  for position in trange(start, end):
    max_instr = -1
    best_char = placeholder

    for ch in PRINTABLE_CHARSET:
      original = correct[position]
      correct[position] = ch
      test_input = "".join(correct)

      try:
        instr = run_perf(binary, test_input)
      except Exception:
        correct[position] = original
        continue

      if instr > max_instr:
        max_instr = instr
        best_char = ch

      correct[position] = original

    correct[position] = best_char
    print(f"Current string: {''.join(correct)}")

  return "".join(correct)


if __name__ == "__main__":
  target_binary = "../handout/camellia"
  result = search(target_binary)
  print(f"The possible input is: {result}")
