from shared.polynomial import fast_polynomial_gcd # https://github.com/jvdsn/crypto-attacks
from Crypto.Util.number import *
import itertools
from tqdm import tqdm
import ast
from sage.all import *
import multiprocessing

def process_chunk(args):
    chunk_ps, chunk_output, E, cs = args
    chunk_ans = []
    for p, out in tqdm(zip(chunk_ps, chunk_output),total=len(chunk_ps)):
        PR = PolynomialRing(GF(p), 'x')
        x = PR.gen()
        ff = 0
        for e, c in zip(E, cs):
            ff += c * x**e
        ff -= out
        RP = PR.quotient(ff)
        y = RP.gen()
        gg = y**(p-1) - 1
        g = gg.lift()
        h = fast_polynomial_gcd(ff, g)
        roots = tuple(int(r[0]) for r in h.roots())
        chunk_ans.append(roots)
    return chunk_ans

if __name__ == '__main__':
    with open("output.txt") as f:
        output = ast.literal_eval(f.readline())
        ps = ast.literal_eval(f.readline())
        cs = ast.literal_eval(f.readline())
        E = ast.literal_eval(f.readline())

    ncpus = 8
    n = len(ps)
    chunk_size = n // ncpus
    chunks = [
        (
            ps[i*chunk_size : (i+1)*chunk_size],
            output[i*chunk_size : (i+1)*chunk_size],
            E,
            cs
        )
        for i in range(ncpus)
    ]

    pool = multiprocessing.Pool(processes=ncpus)
    chunk_results = pool.map(process_chunk, chunks)
    pool.close()
    pool.join()

    ans = []
    for result in chunk_results:
        ans.extend(result)

    combs = itertools.product(*ans)  
    results = []
    for comb in tqdm(combs, total=prod(len(_) for _ in ans)):
        try:
            m = crt(list(comb), ps)
            results.append(m)
        except ValueError:
            pass

    for res in results:
        if long_to_bytes(res).isascii():
            print(long_to_bytes(res))
            # break