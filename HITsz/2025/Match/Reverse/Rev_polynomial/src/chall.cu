#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <cuda_runtime.h>

#define N (1 << 9)
#define P 998244353

typedef struct {
    int x;
} mint;

__constant__ mint c_w[N];
__constant__ mint c_inv[N];
__constant__ int c_secret1[18];

__host__ __device__ mint mint_create(int x) {
    mint m;
    m.x = x % P;
    if (m.x < 0) m.x += P;
    return m;
}

__host__ __device__ mint mint_add(mint a, mint b) {
    int res = a.x + b.x;
    return mint_create(res);
}

__host__ __device__ mint mint_mul(mint a, mint b) {
    long long product = (long long)a.x * b.x;
    return mint_create((int)(product % P));
}

__host__ __device__ mint mint_pow(mint a, int k) {
    if (k == 0) return mint_create(1);
    mint result = a;
    for (int i = 1; i < k; ++i) {
        result = mint_mul(result, a);
    }
    return result;
}

void init_host(mint* w, mint* inv) {
    // w初始化
    w[N/2] = mint_create(1);
    mint g_base = mint_create(3);
    int exponent = P / N;
    mint g = mint_create(1);
    for (int i = 0; i < exponent; ++i) {
        g = mint_mul(g, g_base);
    }

    for (int i = N/2 + 1; i < N; i++) {
        w[i] = mint_mul(w[i-1], g);
    }
    for (int i = N/2 - 1; i > 0; --i) {
        w[i] = w[i << 1];
    }

    // inv初始化
    inv[0] = mint_create(1);
    inv[1] = mint_create(1);
    for (int i = 2; i < N; i++) {
        mint temp = mint_create(P - P/i);
        inv[i] = mint_mul(inv[P % i], temp);
    }
}

__global__ void verify_flag_kernel(mint* d_a, int len, int* d_results) {
    int x = blockIdx.x * blockDim.x + threadIdx.x + 1;
    if (x > 18) return;

    mint ans = mint_create(0);
    mint tmp = mint_create(1);
    mint x_mint = mint_create(x);

    for (int i = 0; i < len; i++) {
        mint term = mint_mul(d_a[i], tmp);
        ans = mint_add(ans, term);
        tmp = mint_mul(tmp, x_mint);
    }

    d_results[x-1] = (ans.x == c_secret1[x-1]) ? 1 : 0;
}

int challenge() {
    char input[19];
    printf("Please input the flag: ");
    if (scanf("%18s", input) != 1) {
        printf("Invalid input!\n");
        return 1;
    }
    
    int len = strlen(input);
    if (len != 18) {
        printf("Failed: Incorrect length!\n");
        return 1;
    }

    // 主机数据
    mint* h_a = (mint*)malloc(len * sizeof(mint));
    for (int i = 0; i < len; i++) {
        h_a[i] = mint_create((int)input[i]);
    }

    mint* d_a;
    int* d_results;
    int* h_results = (int*)malloc(18 * sizeof(int));
    cudaMalloc(&d_a, len * sizeof(mint));
    cudaMalloc(&d_results, 18 * sizeof(int));

    // 数据拷贝到设备
    cudaMemcpy(d_a, h_a, len * sizeof(mint), cudaMemcpyHostToDevice);

    // 启动核函数
    dim3 block(32);
    dim3 grid((18 + block.x - 1) / block.x);
    verify_flag_kernel<<<grid, block>>>(d_a, len, d_results);

    // 回传
    cudaMemcpy(h_results, d_results, 18 * sizeof(int), cudaMemcpyDeviceToHost);
    for (int i = 0; i < 18; i++) {
        if (!h_results[i]) {
            printf("Failed at position %d!\n", i+1);
            free(h_a);
            free(h_results);
            cudaFree(d_a);
            cudaFree(d_results);
            return 1;
        }
    }

    printf("Congratulations! You got the flag! Remember to wrap it with HITCTF{}\n");

    // 清理资源
    free(h_a);
    free(h_results);
    cudaFree(d_a);
    cudaFree(d_results);
    return 0;
}

int main() {
    mint h_w[N], h_inv[N];
    init_host(h_w, h_inv);
    cudaMemcpyToSymbol(c_w, h_w, N * sizeof(mint));
    cudaMemcpyToSymbol(c_inv, h_inv, N * sizeof(mint));

    const int secret1[18] = {1828,30029024,675933036,307266195,441725700,908486918,872572725,462684583,631964733,930026310,883382448,939457745,913070734,152279109,617088314,617509926,518595840,652243173};
    cudaMemcpyToSymbol(c_secret1, secret1, 18 * sizeof(int));

    printf("Can you recover the secret of polynomial?\n");
    return challenge();
}
