#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include <string.h>

#define ARRAY_SIZE 35
#define P 131071 // 2^17 - 1

// Array to generate flag array.
long long to_mod[ARRAY_SIZE] = {124, 118, 121, 123, 127, 112, 141, 135, 142, 99, 115, 116, 125, 99, 119, 121, 125, 135, 121, 136, 99, 139, 113, 142, 114, 99, 135, 125, 123, 124, 121, 141, 118, 142, 133};
long long mod[ARRAY_SIZE] = {12026,106894,23495,3642,92453,81076,96744,16385,16514,79580,45876,29849,29790,79580,28988,23495,29790,16385,23495,50913,79580,125787,86936,16514,3973,79580,16385,29790,3642,12026,23495,96744,106894,16514,58872};


long long mod_exp(long long base, long long exp, long long mod) {
    long long result = 1;
    base = base % mod;
    while (exp > 0) {
        if (exp % 2 == 1)  
            result = (result * base) % mod;
        exp = exp >> 1;  
        base = (base * base) % mod;  
    }
    return result;
}

long long* divide_arrays(long long a[], long long b[], long long size) {
    long long* result = (long long*)malloc(size * sizeof(long long));
    if (result == NULL) {
        fprintf(stderr, "Memory allocation failed\n");
        return NULL;
    }
    
    for (int i = 0; i < size; i++) {
        if (b[i] == 0) {
            fprintf(stderr, "Division by zero at index %d\n", i);
            free(result);
            return NULL;
        }
        long long inv_b = mod_exp(b[i], P - 2, P);  // b[i]^-1 mod P
        result[i] = (a[i] * inv_b) % P;
    }
    
    return result;
}

// Signal handler
void signal_handler(int sig) {
    if (sig == SIGSEGV) {
        signal(SIGSEGV, signal_handler);
    }else{
        printf("Not correct.\n");
        exit(EXIT_FAILURE);
    }
    
}

void run() {
    char input[256];
    printf("Input your flag:");
    scanf("%35s", input);
    if(strlen(input)!=35){
        printf("Not correct.\n");
        exit(EXIT_FAILURE);
    }
    for (int i = 0; i < ARRAY_SIZE; i++) {
        long long size = sizeof(to_mod) / sizeof(to_mod[0]);
        long long* mod_result = divide_arrays(to_mod, mod, size);
        int result = input[i] ^ (int)(mod_result[i]);
        int tmp = (result>>6)&0xf;
        if(tmp==0){
            raise(result);  
        }else{
            printf("Not correct.\n");
            exit(EXIT_FAILURE);
        }
    }
    printf("You got it!\n");

}

int main() {
    for (int sig = 1; sig < NSIG; ++sig) {
        if (sig != SIGKILL && sig != SIGSTOP) {
            signal(sig, signal_handler);
        }
    }
    run();


    return 0;
}
