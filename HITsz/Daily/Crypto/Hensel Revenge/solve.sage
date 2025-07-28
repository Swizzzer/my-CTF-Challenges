from Crypto.Util.number import *
import ast


def hensel_solve(f, p, r):
    """
    Solves polynomial roots in the ring Zmod(p**r) using Hensel's lifting method.

    Parameters:
    f (polynomial): The polynomial equation.
    p (int): A prime number.
    r (int): The exponent.

    Raises:
    ValueError: If p is not a prime number or if f has no roots.
    """
    if not is_prime(p):
        raise ValueError("p must be a prime")
    f = f.change_ring(Zp(p))
    F = f.change_ring(Zmod(pow(p, r)))
    P = Zp(p, max(30, r))
    Fd = derivative(F)
    origin_roots = f.roots()
    if not len(origin_roots):
        raise ValueError("f has no roots")
    ans = set()
    for x in origin_roots:
        x_k = ZZ(x[0])
        flag = 0
        for k in range(1, r):
            if Fd(x_k) == P(0):
                if Zmod(pow(p, r))(f(x_k)) == 0:
                    continue
                else:
                    flag = 1
                    break
            else:
                x_k = Zmod(pow(p, r))(P(x_k) - P(F(x_k)) / P(Fd(x_k)))
        if not flag:
            ans.update({x_k})
    return list(ans)


with open("output.txt") as f:
    p = ast.literal_eval(f.readline())
    c = ast.literal_eval(f.readline())

PR.<x> = PolynomialRing(Zmod(p**3))
f = x^30+405*x**2-4*x+1-c
print(f.change_ring(Zmod(p)).roots())
print(hensel_solve(f, p, 3))
m = int(hensel_solve(f, p, 3)[0])
print(long_to_bytes(m))