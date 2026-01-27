**Noise**

**Category:** Crypto

**Difficulty:** Easy

**Description:** Can you find it amidst all this noise?

**Flag:** `ictf{recover_it_using_continued_fraction_b7b85f8e}`

**Solve idea/Writeup:** Similar to Wiener attack, notice that $\frac{noisy*p+noisier}{n}\approx \frac{noisy}{q}$ , then use continued fraction to recover $p$.

Copper Smith's method is also available.