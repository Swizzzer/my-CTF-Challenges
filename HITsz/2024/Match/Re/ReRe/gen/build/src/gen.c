#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <time.h>
#include <string.h>
#define ll long long
int main()
{
    char knownStr[] = "FLAG_TEMPLATE"; // Dynamic flag
    int str_len = strlen(knownStr);
    ll result[str_len];
    srand(19937);
    printf("static int perm[] = {");

    for (int i = 0; i < str_len; i++)
    {
        ll tmp = (ll)knownStr[i];
        result[i] = ((3 * tmp + 71) % 256) ^ (rand() % 256);
        printf("%lld,",result[i]);
    }

    printf("};\n");
    printf("static int str_len = ");
    printf("%d",str_len);
    printf(";\n");

    return 0;
}
