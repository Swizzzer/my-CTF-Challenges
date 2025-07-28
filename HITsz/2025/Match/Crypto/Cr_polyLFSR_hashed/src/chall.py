import secrets
from hashlib import shake_256

MASK1 = 0x77E3816DD9E3627340D7EE76204ED9F9
MASK2 = 0x512E5CEC93B9AE8D6E28E2AB78B8432B


class LFSR:
    def __init__(self, n: int, key: int, mask: int):
        self.n = n
        self.state = key & ((1 << n) - 1)
        self.mask = mask

    def __call__(self):
        b = bin(self.state & self.mask).count('1')
        output = self.state & 1
        self.state = (self.state >> 1) | ((b & 1) << self.n - 1)
        return output


class Cipher:
    def __init__(self, key_pair):
        self.lfsr1 = LFSR(128, key_pair[0], MASK1)
        self.lfsr2 = LFSR(128, key_pair[1], MASK2)
        self.lfsr3 = LFSR(128, key_pair[0] ^ key_pair[1], MASK2)

    def bit(self):
        x = self.lfsr1()
        y = self.lfsr2() ^ self.lfsr2()
        z = self.lfsr3() ^ self.lfsr3() ^ self.lfsr3()
        return shake_256(str(x + 2 * y + 3 * z + 624).encode()).digest(64)[0] & 1

    def stream(self):
        while True:
            b = 0
            for i in reversed(range(8)):
                b |= self.bit() << i
            yield b

    def encrypt(self, pt: bytes):
        return bytes([x ^ y for x, y in zip(pt, self.stream())])


flag = open("flag.txt", "rb").read().strip()
key_pair = [secrets.randbits(256), secrets.randbits(256)]
cipher = Cipher(key_pair)
gift = cipher.encrypt(b"\x00" * 96)
print(gift.hex())
ct = cipher.encrypt(flag)
print(ct.hex())