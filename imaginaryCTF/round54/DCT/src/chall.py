import numpy as np
from scipy.fftpack import dct
import qrcode
from functools import reduce


def gen_qr(data):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    qr_image = qr.make_image(fill='black', back_color='white')
    return np.array(qr_image).astype(float)


def rs(image, size):
    H, W = image.shape
    Ha = H // size * size
    Wa = W // size * size
    print(Ha, Wa)
    return image[:Ha, :Wa]


def bs(image, size):
    return [image[i:i+size, j:j+size].flatten()
            for i in range(0, image.shape[0], size)
            for j in range(0, image.shape[1], size)]


def trans(blocks, size, len):
    mat = np.random.randn(size, len)
    return mat, [mat.dot(dct(block, norm='ortho')) for block in blocks]


def compose(*funcs):
    def compose_two(f, g):
        return lambda x: f(g(x))
    return reduce(compose_two, funcs)


def processor(block_size, rs_size):
    def rsp(img): return rs(img, block_size)
    def bsp(img): return bs(img, block_size)
    def transp(blocks): return trans(blocks, rs_size, block_size**2)

    return compose(transp, bsp, rsp, gen_qr)


flag = "ictf{REDACTED}"
BS = 8
RS = 20
A, out = processor(BS, RS)(flag)
np.save('A.npy', A)
np.save('output.npy', out)
