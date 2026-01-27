#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <time.h>
#include <string.h>
#include "rev.h"
#include "flag.h"
#define ll long long
int main()
{
	ll result[str_len];
	srand(19937);
	char str[str_len + 1];
	printf("Enter a flag of length %d: ", str_len);
	fgets(str, sizeof(str), stdin);

	for (int i = 0; i < str_len; i++)
	{
		ll tmp = (ll)str[i];
		result[i] = ((3 * tmp + 71) % 256) ^ (rand() % 256);
	}
	int is_correct = 1;
	for (int i = 0; i < str_len; i++)
	{
		if (result[i] != perm[i])
		{
			is_correct = 0;
			break;
		}
	}
	if (is_correct)
	{
		printf("Correct~My master of Reverse:)\n");
	}
	else
	{
		printf("Wrong...Try again?\n");
	}

	return 0;
}
