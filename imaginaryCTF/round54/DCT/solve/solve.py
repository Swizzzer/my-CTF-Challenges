import numpy as np
from scipy.fftpack import idct
from sklearn.linear_model import OrthogonalMatchingPursuit
import matplotlib.pyplot as plt

A = np.load('A.npy')
out = np.load('output.npy')
num_blocks, _ = out.shape
block_size = 8

h_blocks = int(np.sqrt(num_blocks))
w_blocks = h_blocks if h_blocks**2 == num_blocks else num_blocks // h_blocks
Ha, Wa = h_blocks * block_size, w_blocks * block_size
image = np.zeros((Ha, Wa))

for k in range(num_blocks):
    y = out[k]
    omp = OrthogonalMatchingPursuit(n_nonzero_coefs=10)
    omp.fit(A, y)
    x_hat = omp.coef_
    block = idct(x_hat, norm='ortho').reshape((block_size, block_size))
    i, j = divmod(k, w_blocks)
    image[i*block_size:(i+1)*block_size, j*block_size:(j+1)*block_size] = block

plt.imshow(image, cmap='gray')
plt.axis('off')
plt.savefig('recovered_qr.png')
plt.show()