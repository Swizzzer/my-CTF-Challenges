#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int dda(int a, int b) {
    return (a & b) + (a | b);
}

int bus(int a, int b) {
    return (a ^ (-b)) + 2 * (a & (-b));
}

int mul(int a, int b) {
    int result = 0;
    int abs_b = b < 0 ? bus(0, b) : b;
    for (int i = 0; i < abs_b; i = dda(i, 1)) {
        result = dda(result, a);
    }
    return b < 0 ? bus(0, result) : result;
}

int afufu(int x, int a, int b) {
    int temp = mul(a, x);           // a * x
    int result = dda(temp, b);      // a * x + b
    return result & 255;            // 模 256 (保留低 8 位)
}

int main() {
    char input[256];
    int a = 17;
    int b = 31;
    // HITCTF{affine_check1ng_l3lv3l_up}
    int enc[33] = {0xe7,0xf8,0xb3,0x92,0xb3,0xc5,0x4a,0x90,0xe5,0xe5,0x18,0x6d,0xd4,0x6e,0xb2,0x07,0xd4,0xb2,0x3a,0x60,0x6d,0xf6,0x6e,0x4b,0x82,0x4b,0xf5,0x82,0x4b,0x6e,0xe4,0x8f,0x6c};
    printf("🔑 ");
    fgets(input, sizeof(input), stdin);

    size_t len = strlen(input);
    if (len > 0 && input[len - 1] == '\n') {
        input[len - 1] = '\0';
    }
    if (strlen(input) != 33) {
        fprintf(stderr, "📏 🚫\n");
        return 1;
    }
    for (int i = 0; input[i] != '\0'; i++) {
        unsigned char x = (unsigned char)input[i];
        int transformed = afufu(x, a, b);
        if (transformed != enc[i]) {
            fprintf(stderr, "🔒\n");
            return 1;
        }
    }
    printf("✅\n");

    return 0;
}