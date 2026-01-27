from sage.all import *
from Crypto.Util.number import *
from secrets import randbits


class MRG:
    """My Random Generator!"""

    def __init__(self):
        self.p = 0xe2fbc223e2d1e203b2920c7f5fce8047
        self.a, self.b = 2, 3
        self.E = EllipticCurve(GF(self.p), [self.a, self.b])
        self.P = self.E(203571368239390431715773739259190151148, 234762980332835766486380874802032160962)
        self.Q = self.E(58920409573074533862107102872738014011, 115431365646495033422898143098214881751)
        self.s = 0
    def __repr__(self) -> str:
        return f"{self.E}\n{self.P} {self.Q}"

    def seed(self, srt):
        self.s = srt

    def randnum(self) -> int:
        out = (self.s*self.Q).x()
        self.s = (self.s*self.P).x()
        return out

rand = MRG()
rand.seed(randbits(64))
flag = open("flag.txt", "rb").read().strip()
m = bin(bytes_to_long(flag))[2:]
output = []
for bit in m:
    if bit == '0':
        output.append(randbits(128))
    else:
        output.append(rand.randnum())
print(rand)
print(output)


