DCT

**Category:** Misc

**Difficulty:** Medium

**Description:** Oops, I can't see anything once the matrix is applied...

**Flag:** ictf{c0mPress3d_s3nsing_1s_s0_c00o0OL}


Solve idea/Writeup: 

```python
import numpy as np
from scipy.fftpack import idct
from sklearn.linear_model import OrthogonalMatchingPursuit
import matplotlib.pyplot as plt

A = np.load('A.npy')

features = np.load('output.npy')
image = np.zeros((368, 368))
reconstructed_image = np.zeros_like(image)
block_idx = 0
block_size = 8
blocks = [image[i:i+block_size, j:j+block_size].flatten() 
          for i in range(0, image.shape[0], block_size) 
          for j in range(0, image.shape[1], block_size)]
M = 64
N = 20

omp = OrthogonalMatchingPursuit(n_nonzero_coefs=10)
for i in range(0, image.shape[0], block_size):
    for j in range(0, image.shape[1], block_size):
        y = features[block_idx]
        omp.fit(A, y)
        sparse_coeff_recovered = omp.coef_
        block_recovered = idct(sparse_coeff_recovered, norm='ortho')
        block_recovered = block_recovered.reshape((block_size, block_size))
        reconstructed_image[i:i+block_size, j:j+block_size] = block_recovered
        block_idx += 1
plt.imshow(reconstructed_image, cmap='gray')
plt.show()
```