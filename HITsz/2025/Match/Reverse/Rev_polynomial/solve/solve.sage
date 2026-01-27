from sage.all import *
ans = [1828,30029024,675933036,307266195,441725700,908486918,872572725,462684583,631964733,930026310,883382448,939457745,913070734,152279109,617088314,617509926,518595840,652243173]
FF = GF(998244353)
A = matrix(FF, 18, 18)
for i in range(1, 19):
    x = FF(1)
    for j in range(18):
        A[i-1, j] = x
        x *= i

b = vector(FF, ans)
print(bytes([int(x) for x in A.solve_right(b)]))