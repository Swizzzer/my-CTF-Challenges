bitD2cision

**Category:** Crypto

**Difficulty:** Normal

**Description:** Make your decision bit by bit, again!

**Flag:** ictf{chEck_t0rsion_aft3r_pa1ring_3f1d7aec}

Solve idea/Writeup: 

```python
from Crypto.Util.number import *
import ast
with open("output.txt") as f:
    n = ast.literal_eval(f.readline())
    output = ast.literal_eval(f.readline())
p = 0x1a0111ea397fe69a4b1ba7b6434bacd764774b84f38512bf6730d2a0f6b0f6241eabfffeb153ffffb9feffffffffaaab
res = ""
for out in output:
    if pow(out, 52437899, p) == 1:
        res += "1"
    else:
        res += "0"
print(long_to_bytes(int(res, 2)))
```